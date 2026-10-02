from __future__ import annotations
import hashlib,json,sqlite3,threading,time,uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any,Callable,Mapping

class ProcessingStatus(str,Enum):
    PENDING="pending"; PROCESSING="processing"; COMPLETED="completed"; FAILED="failed"
class ProcessingJobNotFound(KeyError): pass
class ProcessingIdempotencyConflict(RuntimeError): pass
@dataclass(frozen=True)
class ProcessingJob:
    job_id:str; organization_id:str; kind:str; payload:Mapping[str,Any]; status:ProcessingStatus
    attempt:int; max_attempts:int; next_attempt_at:float; idempotency_key:str|None
    payload_fingerprint:str; worker_id:str|None; leased_until:float|None
    request_id:str|None; correlation_id:str|None; last_error:str|None; created_at:float; updated_at:float
@dataclass(frozen=True)
class ProcessingEvent:
    event_id:str; job_id:str; organization_id:str; event_type:str
    from_status:ProcessingStatus|None; to_status:ProcessingStatus; attempt:int
    worker_id:str|None; request_id:str|None; correlation_id:str|None; details:Mapping[str,Any]; created_at:float

class SQLiteProcessingQueue:
    def __init__(self,path=":memory:",*,clock:Callable[[],float]=time.time):
        self.clock=clock; self._lock=threading.RLock(); self._db=sqlite3.connect(path,check_same_thread=False); self._db.row_factory=sqlite3.Row
        self._db.executescript("""CREATE TABLE IF NOT EXISTS processing_jobs(
        job_id TEXT PRIMARY KEY,organization_id TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN('pending','processing','completed','failed')),attempt INTEGER NOT NULL DEFAULT 0,
        max_attempts INTEGER NOT NULL,next_attempt_at REAL NOT NULL,idempotency_key TEXT,payload_fingerprint TEXT NOT NULL,
        worker_id TEXT,leased_until REAL,request_id TEXT,correlation_id TEXT,last_error TEXT,created_at REAL NOT NULL,updated_at REAL NOT NULL,
        UNIQUE(organization_id,idempotency_key));
        CREATE INDEX IF NOT EXISTS idx_processing_ready ON processing_jobs(status,next_attempt_at,created_at);
        CREATE INDEX IF NOT EXISTS idx_processing_lease ON processing_jobs(status,leased_until);
        CREATE TABLE IF NOT EXISTS processing_job_events(
        event_id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES processing_jobs(job_id) ON DELETE CASCADE,organization_id TEXT NOT NULL,
        event_type TEXT NOT NULL,from_status TEXT,to_status TEXT NOT NULL,attempt INTEGER NOT NULL,worker_id TEXT,
        request_id TEXT,correlation_id TEXT,details TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE INDEX IF NOT EXISTS idx_processing_events ON processing_job_events(job_id,created_at);"""); self._db.commit()
    @staticmethod
    def fingerprint(payload):
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    def enqueue(self,*,organization_id,kind,payload,max_attempts=3,next_attempt_at=None,idempotency_key=None,request_id=None,correlation_id=None):
        if not organization_id or not kind: raise ValueError("organization_id and kind are required")
        if max_attempts<1: raise ValueError("max_attempts must be positive")
        now=self.clock(); fp=self.fingerprint(payload)
        with self._lock:
            if idempotency_key is not None:
                row=self._db.execute("SELECT * FROM processing_jobs WHERE organization_id=? AND idempotency_key=?",(organization_id,idempotency_key)).fetchone()
                if row:
                    if row["payload_fingerprint"]!=fp: raise ProcessingIdempotencyConflict("idempotency key reused with different payload")
                    return self._row(row)
            jid=str(uuid.uuid4()); self._db.execute("""INSERT INTO processing_jobs
            (job_id,organization_id,kind,payload,status,attempt,max_attempts,next_attempt_at,idempotency_key,payload_fingerprint,request_id,correlation_id,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(jid,organization_id,kind,json.dumps(payload,sort_keys=True),ProcessingStatus.PENDING.value,0,max_attempts,now if next_attempt_at is None else next_attempt_at,idempotency_key,fp,request_id,correlation_id,now,now))
            self._event(jid,organization_id,"enqueued",None,ProcessingStatus.PENDING,0,None,request_id,correlation_id,{"kind":kind},now); self._db.commit(); return self.get(jid)
    def get(self,job_id,*,organization_id=None):
        row=self._db.execute("SELECT * FROM processing_jobs WHERE job_id=?",(job_id,)).fetchone()
        if row is None or (organization_id is not None and row["organization_id"]!=organization_id): raise ProcessingJobNotFound(job_id)
        return self._row(row)
    def claim(self,*,worker_id,lease_seconds=30):
        if not worker_id or lease_seconds<=0: raise ValueError("worker_id and positive lease_seconds are required")
        now=self.clock()
        with self._lock:
            self._recover(now); self._db.execute("BEGIN IMMEDIATE")
            row=self._db.execute("SELECT * FROM processing_jobs WHERE status=? AND next_attempt_at<=? ORDER BY next_attempt_at,created_at LIMIT 1",(ProcessingStatus.PENDING.value,now)).fetchone()
            if row is None: self._db.commit(); return None
            attempt=row["attempt"]+1; self._db.execute("UPDATE processing_jobs SET status=?,attempt=?,worker_id=?,leased_until=?,updated_at=? WHERE job_id=? AND status=?",(ProcessingStatus.PROCESSING.value,attempt,worker_id,now+lease_seconds,now,row["job_id"],ProcessingStatus.PENDING.value))
            self._event(row["job_id"],row["organization_id"],"claimed",ProcessingStatus.PENDING,ProcessingStatus.PROCESSING,attempt,worker_id,row["request_id"],row["correlation_id"],{},now); self._db.commit(); return self.get(row["job_id"])
    def complete(self,job_id,*,worker_id): return self._finish(job_id,worker_id,ProcessingStatus.COMPLETED,"completed",{})
    def fail(self,job_id,*,worker_id,error,retry_delay=1):
        with self._lock:
            row=self._owned(job_id,worker_id); now=self.clock(); terminal=row["attempt"]>=row["max_attempts"]; target=ProcessingStatus.FAILED if terminal else ProcessingStatus.PENDING; nxt=now if terminal else now+retry_delay
            self._db.execute("UPDATE processing_jobs SET status=?,next_attempt_at=?,worker_id=NULL,leased_until=NULL,last_error=?,updated_at=? WHERE job_id=?",(target.value,nxt,str(error)[:4000],now,job_id))
            self._event(job_id,row["organization_id"],"failed" if terminal else "retry_scheduled",ProcessingStatus.PROCESSING,target,row["attempt"],worker_id,row["request_id"],row["correlation_id"],{"error":str(error)[:4000],"retry":not terminal},now); self._db.commit(); return self.get(job_id)
    def recover_expired_leases(self):
        with self._lock:
            now=self.clock(); self._db.execute("BEGIN IMMEDIATE"); n=self._recover(now); self._db.commit(); return n
    def events(self,job_id,*,organization_id=None):
        self.get(job_id,organization_id=organization_id); rows=self._db.execute("SELECT * FROM processing_job_events WHERE job_id=? ORDER BY created_at,event_id",(job_id,)).fetchall()
        return [ProcessingEvent(r["event_id"],r["job_id"],r["organization_id"],r["event_type"],ProcessingStatus(r["from_status"]) if r["from_status"] else None,ProcessingStatus(r["to_status"]),r["attempt"],r["worker_id"],r["request_id"],r["correlation_id"],json.loads(r["details"]),r["created_at"]) for r in rows]
    def _finish(self,jid,w,target,event,details):
        with self._lock:
            row=self._owned(jid,w); now=self.clock(); self._db.execute("UPDATE processing_jobs SET status=?,worker_id=NULL,leased_until=NULL,updated_at=? WHERE job_id=?",(target.value,now,jid))
            self._event(jid,row["organization_id"],event,ProcessingStatus.PROCESSING,target,row["attempt"],w,row["request_id"],row["correlation_id"],details,now); self._db.commit(); return self.get(jid)
    def _owned(self,jid,w):
        row=self._db.execute("SELECT * FROM processing_jobs WHERE job_id=?",(jid,)).fetchone()
        if row is None: raise ProcessingJobNotFound(jid)
        if row["status"]!="processing" or row["worker_id"]!=w: raise RuntimeError("job lease is not owned by worker")
        return row
    def _recover(self,now):
        rows=self._db.execute("SELECT * FROM processing_jobs WHERE status='processing' AND leased_until IS NOT NULL AND leased_until<=?",(now,)).fetchall()
        for r in rows:
            self._db.execute("UPDATE processing_jobs SET status='pending',worker_id=NULL,leased_until=NULL,next_attempt_at=?,updated_at=? WHERE job_id=?",(now,now,r["job_id"]))
            self._event(r["job_id"],r["organization_id"],"lease_expired",ProcessingStatus.PROCESSING,ProcessingStatus.PENDING,r["attempt"],r["worker_id"],r["request_id"],r["correlation_id"],{},now)
        return len(rows)
    def _event(self,jid,org,event,frm,to,attempt,w,req,corr,details,now):
        self._db.execute("INSERT INTO processing_job_events(event_id,job_id,organization_id,event_type,from_status,to_status,attempt,worker_id,request_id,correlation_id,details,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),jid,org,event,frm.value if frm else None,to.value,attempt,w,req,corr,json.dumps(details,sort_keys=True),now))
    @staticmethod
    def _row(r):
        return ProcessingJob(r["job_id"],r["organization_id"],r["kind"],json.loads(r["payload"]),ProcessingStatus(r["status"]),r["attempt"],r["max_attempts"],r["next_attempt_at"],r["idempotency_key"],r["payload_fingerprint"],r["worker_id"],r["leased_until"],r["request_id"],r["correlation_id"],r["last_error"],r["created_at"],r["updated_at"])

class ProcessingWorker:
    def __init__(self,queue,handlers,*,worker_id,lease_seconds=30,retry_delay=1): self.queue=queue; self.handlers=dict(handlers); self.worker_id=worker_id; self.lease_seconds=lease_seconds; self.retry_delay=retry_delay
    def run_once(self):
        job=self.queue.claim(worker_id=self.worker_id,lease_seconds=self.lease_seconds)
        if job is None:return None
        handler=self.handlers.get(job.kind)
        if handler is None:return self.queue.fail(job.job_id,worker_id=self.worker_id,error=f"no handler for {job.kind}",retry_delay=self.retry_delay)
        try: handler(job.payload)
        except Exception as exc:return self.queue.fail(job.job_id,worker_id=self.worker_id,error=f"{type(exc).__name__}: {exc}",retry_delay=self.retry_delay)
        return self.queue.complete(job.job_id,worker_id=self.worker_id)
