"""V6.1 persistent application repository.

The repository is the persistence boundary used by the production API adapter.
Every public operation opens a transaction and sets the tenant context with
SET LOCAL. No external/Google mutation is performed here.
"""
from __future__ import annotations
import json
from contextlib import contextmanager
from dataclasses import asdict
from typing import Any, Mapping
from .postgres_repository import RepositoryError, PostgresRepository

class PostgresAPIRepository(PostgresRepository):
    def _row(self, cur, sql, params=()):
        cur.execute(sql, params); return cur.fetchone()

    def create_user(self, organization_id: str, email: str, password_hash: str, role: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO users(email,password_hash) VALUES(%s,%s) RETURNING id,email,password_hash""", (email.lower(), password_hash))
                uid, em, ph = cur.fetchone()
                cur.execute("INSERT INTO memberships(organization_id,user_id,role) VALUES(%s,%s,%s)", (organization_id, uid, role))
                return str(uid), str(em), ph, role

    def get_user_by_email(self, organization_id: str, email: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT u.id,u.email,u.password_hash,m.role FROM users u JOIN memberships m ON m.user_id=u.id WHERE m.organization_id=%s AND u.email=%s""", (organization_id,email.lower()))
                return cur.fetchone()

    def get_invitation_by_token(self, organization_id: str, token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT invitation_id,organization_id,email,role,token_hash,expires_at,invited_by,accepted_at,revoked_at FROM organization_invitations WHERE organization_id=%s AND token_hash=%s""", (organization_id,token_hash))
                return cur.fetchone()

    def mark_invitation_accepted(self, organization_id: str, invitation_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE organization_invitations SET accepted_at=now(),updated_at=now() WHERE organization_id=%s AND invitation_id=%s AND accepted_at IS NULL AND revoked_at IS NULL", (organization_id,invitation_id))
                return cur.rowcount == 1

    def list_members(self, organization_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT u.id,u.email,m.role FROM users u JOIN memberships m ON m.user_id=u.id WHERE m.organization_id=%s ORDER BY u.email", (organization_id,))
                return cur.fetchall()

    def put_session(self, organization_id: str, token_hash: str, user_id: str, role: str, expires_at: str, user_agent: str | None = None, ip_hash: str | None = None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO api_sessions(token_hash,user_id,organization_id,role,expires_at,user_agent,ip_hash,last_seen_at) VALUES(%s,%s,%s,%s,%s,%s,%s,now())", (token_hash,user_id,organization_id,role,expires_at,user_agent,ip_hash))

    def touch_session(self, organization_id: str, token_hash: str, user_agent: str | None = None, ip_hash: str | None = None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE api_sessions SET last_seen_at=now(), user_agent=COALESCE(%s,user_agent), ip_hash=COALESCE(%s,ip_hash) WHERE token_hash=%s", (user_agent, ip_hash, token_hash))

    def revoke_all_sessions(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE api_sessions SET revoked_at=now() WHERE organization_id=%s AND user_id=%s AND revoked_at IS NULL", (organization_id,user_id))

    def security_event(self, organization_id: str, actor_user_id: str | None, event_type: str, target_user_id: str | None = None, metadata: dict | None = None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO security_events(organization_id,actor_user_id,event_type,target_user_id,metadata) VALUES(%s,%s,%s,%s,%s::jsonb)", (organization_id,actor_user_id,event_type,target_user_id,json.dumps(metadata or {})))

    def get_session(self, organization_id: str, token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT token_hash,user_id,organization_id,role,expires_at,revoked_at FROM api_sessions WHERE token_hash=%s", (token_hash,))
                return cur.fetchone()

    def revoke_session(self, organization_id: str, token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("UPDATE api_sessions SET revoked_at=now() WHERE token_hash=%s", (token_hash,))

    def upsert_review(self, organization_id: str, review: Mapping[str,Any]):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO api_reviews(organization_id,review_id,location_id,author_display_name,rating,review_text,published_at,updated_at,language,source,review_url)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(organization_id,review_id) DO UPDATE SET location_id=excluded.location_id,author_display_name=excluded.author_display_name,rating=excluded.rating,review_text=excluded.review_text,published_at=excluded.published_at,updated_at=excluded.updated_at,language=excluded.language,source=excluded.source,review_url=excluded.review_url""",
                (organization_id,review['review_id'],review.get('location_id',''),review.get('author_display_name'),review['rating'],review['text'],review.get('published_at',''),review.get('updated_at'),review.get('language'),review.get('source','GOOGLE'),review.get('review_url')))

    def get_review(self, organization_id: str, review_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT review_id,organization_id,location_id,author_display_name,rating,review_text,published_at,updated_at,language,source,review_url FROM api_reviews WHERE review_id=%s", (review_id,)); return cur.fetchone()

    def list_reviews(self, organization_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT review_id,organization_id,location_id,author_display_name,rating,review_text,published_at,updated_at,language,source,review_url FROM api_reviews ORDER BY published_at DESC NULLS LAST"); return cur.fetchall()

    def create_case_persistent(self, organization_id: str, case_id: str, review_id: str, status: str, actor_user_id: str|None=None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                # The legacy cases table is the FK parent of case_events. Keep the
                # event/audit graph consistent with the API persistence mirror.
                cur.execute(
                    "INSERT INTO cases(id,organization_id,review_id,state) VALUES(%s,%s,%s,%s) "
                    "ON CONFLICT (id) DO NOTHING",
                    (case_id, organization_id, review_id, status),
                )
                cur.execute("INSERT INTO api_cases(organization_id,case_id,review_id,status) VALUES(%s,%s,%s,%s) RETURNING case_id,organization_id,review_id,status,decision_id,snapshot_sha256,created_at,updated_at", (organization_id,case_id,review_id,status)); row=cur.fetchone()
                cur.execute("INSERT INTO case_events(organization_id,case_id,event_type,actor_user_id,payload) VALUES(%s,%s,%s,%s,%s::jsonb)", (organization_id,case_id,'CASE_CREATED',actor_user_id,'{}'))
                return row

    def list_cases(self, organization_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT case_id,organization_id,review_id,status,decision_id,snapshot_sha256,created_at,updated_at "
                    "FROM api_cases WHERE organization_id=%s ORDER BY created_at DESC NULLS LAST",
                    (organization_id,),
                )
                return cur.fetchall()

    def get_case_persistent(self, organization_id: str, case_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT case_id,organization_id,review_id,status,decision_id,snapshot_sha256,created_at,updated_at FROM api_cases WHERE case_id=%s", (case_id,)); return cur.fetchone()

    def update_case(self, organization_id: str, case_id: str, *, status=None, decision_id=None, snapshot_sha256=None):
        fields=[]; vals=[]
        for name,val in [('status',status),('decision_id',decision_id),('snapshot_sha256',snapshot_sha256)]:
            if val is not None: fields.append(f'{name}=%s'); vals.append(val)
        if not fields: return
        vals.extend([organization_id,case_id])
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute(f"UPDATE api_cases SET {', '.join(fields)},updated_at=now() WHERE organization_id=%s AND case_id=%s", tuple(vals))

    def update_case_sla(self, organization_id: str, case_id: str, *, paused_at, paused_seconds: float, pause_reason):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE api_cases SET sla_paused_at=%s, sla_paused_seconds=%s, sla_pause_reason=%s, updated_at=now() WHERE organization_id=%s AND case_id=%s", (paused_at, paused_seconds, pause_reason, organization_id, case_id))

    def put_decision(self, organization_id: str, d: Mapping[str,Any]):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO api_decisions(organization_id,decision_id,case_id,status,kind,rationale,snapshot_sha256,created_by,created_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(organization_id,decision_id) DO UPDATE SET status=excluded.status,snapshot_sha256=excluded.snapshot_sha256""", (organization_id,d['decision_id'],d['case_id'],d['status'],d['kind'],d['rationale'],d.get('snapshot_sha256'),d.get('created_by'),d['created_at']))

    def put_snapshot(self, organization_id: str, case_id: str, sha256: str, payload: Mapping[str,Any], frozen_by: str, frozen_at: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("INSERT INTO api_dossier_snapshots(organization_id,case_id,sha256,payload,frozen_by,frozen_at) VALUES(%s,%s,%s,%s::jsonb,%s,%s) ON CONFLICT(organization_id,case_id) DO UPDATE SET sha256=excluded.sha256,payload=excluded.payload,frozen_by=excluded.frozen_by,frozen_at=excluded.frozen_at", (organization_id,case_id,sha256,json.dumps(payload,sort_keys=True),frozen_by,frozen_at))

    def put_approval(self, organization_id: str, a: Mapping[str,Any]):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("INSERT INTO api_approvals(organization_id,approval_id,case_id,decision_id,actor_id,actor_role,snapshot_sha256,approved_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", (organization_id,a['approval_id'],a['case_id'],a['decision_id'],a['actor_id'],a['actor_role'],a['snapshot_sha256'],a['approved_at']))

    def put_submission(self, organization_id: str, s: Mapping[str,Any]):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("INSERT INTO api_submissions(organization_id,submission_id,case_id,status,external_call) VALUES(%s,%s,%s,%s,%s)", (organization_id,s['submission_id'],s['case_id'],s['status'],False))

    def put_idempotency(self, organization_id: str, key: str, fingerprint: str, response: Any):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO api_idempotency(organization_id,idempotency_key,payload_fingerprint,response_json) VALUES(%s,%s,%s,%s::jsonb) ON CONFLICT(organization_id,idempotency_key) DO NOTHING RETURNING idempotency_key", (organization_id,key,fingerprint,json.dumps(response,sort_keys=True)))
                return cur.fetchone()

    def put_evidence_fact(self, organization_id: str, fact: Mapping[str,Any]):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO evidence_facts(organization_id,fact_id,evidence_id,case_id,key,kind,value,source_location,verified,verified_by,verified_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(fact_id) DO UPDATE SET key=excluded.key,kind=excluded.kind,value=excluded.value,source_location=excluded.source_location,verified=excluded.verified,verified_by=excluded.verified_by,verified_at=excluded.verified_at""",
                (organization_id,fact['fact_id'],fact['evidence_id'],fact['case_id'],fact['key'],fact['kind'],fact['value'],fact.get('source_location',''),fact.get('verified',False),fact.get('verified_by'),fact.get('verified_at')))

    def list_evidence_facts(self, organization_id: str, case_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT fact_id,evidence_id,case_id,key,kind,value,source_location,verified,verified_by,verified_at FROM evidence_facts WHERE organization_id=%s AND case_id=%s ORDER BY created_at", (organization_id,case_id))
                return cur.fetchall()

    def put_fact_suggestion(self, organization_id: str, suggestion: Mapping[str,Any]):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO evidence_fact_suggestions(organization_id,suggestion_id,evidence_id,case_id,key,kind,value,source_location,confidence)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(organization_id,suggestion_id) DO UPDATE SET value=excluded.value,source_location=excluded.source_location,confidence=excluded.confidence""",
                (organization_id,suggestion['suggestion_id'],suggestion['evidence_id'],suggestion['case_id'],suggestion['key'],suggestion['kind'],suggestion['value'],suggestion.get('source_location',''),suggestion['confidence']))

    def put_contradiction(self, organization_id: str, finding: Mapping[str,Any]):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO contradiction_findings(organization_id,contradiction_id,case_id,claim_id,key,kind,claim_value,evidence_ids,evidence_values,description,confidence,requires_human_review)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s)
                ON CONFLICT(organization_id,contradiction_id) DO UPDATE SET evidence_ids=excluded.evidence_ids,evidence_values=excluded.evidence_values,description=excluded.description,confidence=excluded.confidence,requires_human_review=excluded.requires_human_review""",
                (organization_id,finding['contradiction_id'],finding['case_id'],finding['claim_id'],finding['key'],finding['kind'],finding['claim_value'],json.dumps(finding['evidence_ids']),json.dumps(finding['evidence_values']),finding['description'],finding['confidence'],finding.get('requires_human_review',True)))

    def assign_case(self, organization_id: str, case_id: str, user_id: str | None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE api_cases SET assigned_to=%s, updated_at=now() WHERE organization_id=%s AND case_id=%s", (user_id, organization_id, case_id))

    def upsert_sla_calendar(self, organization_id: str, calendar):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO organization_sla_calendars(organization_id,timezone,workdays,start_hour,end_hour,holidays,updated_at)
                VALUES(%s,%s,%s::jsonb,%s,%s,%s::jsonb,now())
                ON CONFLICT(organization_id) DO UPDATE SET timezone=excluded.timezone,workdays=excluded.workdays,start_hour=excluded.start_hour,end_hour=excluded.end_hour,holidays=excluded.holidays,updated_at=now()""",
                (organization_id,calendar['timezone'],json.dumps(calendar['workdays']),calendar['start_hour'],calendar['end_hour'],json.dumps(calendar['holidays'])))

    def upsert_escalation(self, organization_id: str, e):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO case_escalations(organization_id,case_id,level,reason,status,acknowledged_by,acknowledged_at,resolved_by,resolved_at,updated_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,now())
                ON CONFLICT(organization_id,case_id,level) DO UPDATE SET reason=excluded.reason,status=excluded.status,acknowledged_by=excluded.acknowledged_by,acknowledged_at=excluded.acknowledged_at,resolved_by=excluded.resolved_by,resolved_at=excluded.resolved_at,updated_at=now()""",
                (organization_id,e['case_id'],e['level'],e['reason'],e['status'],e.get('acknowledged_by'),e.get('acknowledged_at'),e.get('resolved_by'),e.get('resolved_at')))

    def get_sla_calendar(self, organization_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT timezone,workdays,start_hour,end_hour,holidays FROM organization_sla_calendars WHERE organization_id=%s", (organization_id,))
                row=cur.fetchone()
                if not row: return None
                return {"timezone":row[0],"workdays":row[1],"start_hour":row[2],"end_hour":row[3],"holidays":row[4]}

    def create_notification(self, organization_id: str, n):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO notification_outbox(organization_id,notification_id,case_id,escalation_level,channel,target,subject,body,status,created_by,created_at,dedupe_key,delivery_attempts,max_attempts)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s) ON CONFLICT(organization_id,dedupe_key) DO NOTHING""",
                (organization_id,n['notification_id'],n['case_id'],n['escalation_level'],n['channel'],n['target'],n['subject'],n['body'],n['status'],n.get('created_by'),n.get('created_at'),n['dedupe_key'],n.get('max_attempts',3)))

    def get_notification_policy(self, organization_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT enabled,levels,channels,quiet_start,quiet_end,allow_external FROM organization_notification_policies WHERE organization_id=%s", (organization_id,))
                row=cur.fetchone()
                if not row: return None
                return {"enabled":row[0],"levels":list(row[1] or []),"channels":list(row[2] or []),"quiet_start":str(row[3]) if row[3] is not None else None,"quiet_end":str(row[4]) if row[4] is not None else None,"allow_external":row[5]}

    def upsert_notification_policy(self, organization_id: str, policy):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO organization_notification_policies(organization_id,enabled,levels,channels,quiet_start,quiet_end,allow_external) VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(organization_id) DO UPDATE SET enabled=EXCLUDED.enabled,levels=EXCLUDED.levels,channels=EXCLUDED.channels,quiet_start=EXCLUDED.quiet_start,quiet_end=EXCLUDED.quiet_end,allow_external=EXCLUDED.allow_external,updated_at=NOW()""", (organization_id,policy["enabled"],policy["levels"],policy["channels"],policy.get("quiet_start"),policy.get("quiet_end"),policy["allow_external"]))

    def get_notification(self, organization_id: str, notification_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""SELECT notification_id,organization_id,case_id,escalation_level,channel,target,subject,body,status,created_by,created_at,sent_by,sent_at,cancelled_by,cancelled_at,dedupe_key,delivery_attempts,last_attempt_at,delivery_error,max_attempts,next_attempt_at,dead_lettered_at FROM notification_outbox WHERE organization_id=%s AND notification_id=%s""", (organization_id,notification_id))
                row=cur.fetchone()
                if not row: return None
                names=("notification_id","organization_id","case_id","escalation_level","channel","target","subject","body","status","created_by","created_at","sent_by","sent_at","cancelled_by","cancelled_at","dedupe_key","delivery_attempts","last_attempt_at","delivery_error","max_attempts","next_attempt_at","dead_lettered_at")
                d=dict(zip(names,row))
                for k in ("notification_id","organization_id","case_id","created_by","sent_by","cancelled_by"):
                    if d.get(k) is not None: d[k]=str(d[k])
                for k in ("created_at","sent_at","cancelled_at","last_attempt_at","next_attempt_at","dead_lettered_at"):
                    if d.get(k) is not None: d[k]=d[k].isoformat() if hasattr(d[k],"isoformat") else str(d[k])
                return d

    def list_notifications(self, organization_id: str, status=None):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                if status:
                    cur.execute("""SELECT notification_id,organization_id,case_id,escalation_level,channel,target,subject,body,status,created_by,created_at,sent_by,sent_at,cancelled_by,cancelled_at,dedupe_key,delivery_attempts,last_attempt_at,delivery_error,max_attempts,next_attempt_at,dead_lettered_at FROM notification_outbox WHERE organization_id=%s AND status=%s ORDER BY created_at DESC""", (organization_id,status))
                else:
                    cur.execute("""SELECT notification_id,organization_id,case_id,escalation_level,channel,target,subject,body,status,created_by,created_at,sent_by,sent_at,cancelled_by,cancelled_at,dedupe_key,delivery_attempts,last_attempt_at,delivery_error,max_attempts,next_attempt_at,dead_lettered_at FROM notification_outbox WHERE organization_id=%s ORDER BY created_at DESC""", (organization_id,))
                rows=[]
                for row in cur.fetchall():
                    names=("notification_id","organization_id","case_id","escalation_level","channel","target","subject","body","status","created_by","created_at","sent_by","sent_at","cancelled_by","cancelled_at","dedupe_key","delivery_attempts","last_attempt_at","delivery_error","max_attempts","next_attempt_at","dead_lettered_at")
                    d=dict(zip(names,row))
                    for k in ("notification_id","organization_id","case_id","created_by","sent_by","cancelled_by"):
                        if d.get(k) is not None: d[k]=str(d[k])
                    for k in ("created_at","sent_at","cancelled_at","last_attempt_at","next_attempt_at","dead_lettered_at"):
                        if d.get(k) is not None: d[k]=d[k].isoformat() if hasattr(d[k],"isoformat") else str(d[k])
                    rows.append(d)
                return rows

    def update_notification(self, organization_id: str, n):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""UPDATE notification_outbox SET status=%s,sent_by=%s,sent_at=%s,cancelled_by=%s,cancelled_at=%s,delivery_attempts=%s,last_attempt_at=%s,delivery_error=%s,max_attempts=%s,next_attempt_at=%s,dead_lettered_at=%s WHERE organization_id=%s AND notification_id=%s""",
                (n['status'],n.get('sent_by'),n.get('sent_at'),n.get('cancelled_by'),n.get('cancelled_at'),n.get('delivery_attempts',0),n.get('last_attempt_at'),n.get('delivery_error'),n.get('max_attempts',3),n.get('next_attempt_at'),n.get('dead_lettered_at'),organization_id,n['notification_id']))

    def record_notification_attempt(self, organization_id: str, n):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE notification_outbox SET delivery_attempts=%s,last_attempt_at=%s,delivery_error=%s,max_attempts=%s,next_attempt_at=%s,dead_lettered_at=%s WHERE organization_id=%s AND notification_id=%s", (n.get("delivery_attempts",0), n.get("last_attempt_at"), n.get("delivery_error"), n.get("max_attempts",3), n.get("next_attempt_at"), n.get("dead_lettered_at"), organization_id, n["notification_id"]))

    def get_escalation(self, organization_id: str, case_id: str, level: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT case_id,level,reason,status,acknowledged_by,acknowledged_at,resolved_by,resolved_at FROM case_escalations WHERE organization_id=%s AND case_id=%s AND level=%s", (organization_id,case_id,level))
                row=cur.fetchone()
                if not row: return None
                return {"case_id":str(row[0]),"level":row[1],"reason":row[2],"status":row[3],"acknowledged_by":str(row[4]) if row[4] else None,"acknowledged_at":row[5].isoformat() if row[5] else None,"resolved_by":str(row[6]) if row[6] else None,"resolved_at":row[7].isoformat() if row[7] else None}

    def upsert_contradiction_disposition(self, organization_id: str, disposition: Mapping[str,Any]):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO contradiction_dispositions(disposition_id,organization_id,case_id,contradiction_id,status,rationale,actor_id,created_at,requires_human_review)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(organization_id,contradiction_id) DO UPDATE SET status=EXCLUDED.status,rationale=EXCLUDED.rationale,actor_id=EXCLUDED.actor_id,created_at=EXCLUDED.created_at,requires_human_review=TRUE""",
                (disposition['disposition_id'],organization_id,disposition['case_id'],disposition['contradiction_id'],disposition['status'],disposition['rationale'],disposition['actor_id'],disposition['created_at'],True))

    def append_contradiction_disposition_history(self, organization_id: str, history: Mapping[str,Any]):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO contradiction_disposition_history(history_id,organization_id,case_id,contradiction_id,disposition_id,status,rationale,actor_id,created_at,requires_human_review) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(history_id) DO NOTHING""", (history['history_id'],organization_id,history['case_id'],history['contradiction_id'],history['disposition_id'],history['status'],history['rationale'],history['actor_id'],history['created_at'],True))

    def list_contradiction_disposition_history(self, organization_id: str, contradiction_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT history_id,organization_id,case_id,contradiction_id,disposition_id,status,rationale,actor_id,created_at,requires_human_review FROM contradiction_disposition_history WHERE organization_id=%s AND contradiction_id=%s ORDER BY created_at ASC", (organization_id, contradiction_id))
                names=("history_id","organization_id","case_id","contradiction_id","disposition_id","status","rationale","actor_id","created_at","requires_human_review")
                rows=[]
                for row in cur.fetchall():
                    d=dict(zip(names,row)); d["created_at"]=d["created_at"].isoformat() if hasattr(d["created_at"],"isoformat") else str(d["created_at"]); d["organization_id"]=str(d["organization_id"]); d["case_id"]=str(d["case_id"]); d["actor_id"]=str(d["actor_id"]); rows.append(d)
                return rows

    def get_contradiction_disposition(self, organization_id: str, contradiction_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT disposition_id,organization_id,case_id,contradiction_id,status,rationale,actor_id,created_at,requires_human_review FROM contradiction_dispositions WHERE organization_id=%s AND contradiction_id=%s", (organization_id, contradiction_id))
                row=cur.fetchone()
                if not row: return None
                names=("disposition_id","organization_id","case_id","contradiction_id","status","rationale","actor_id","created_at","requires_human_review")
                d=dict(zip(names,row)); d["created_at"]=d["created_at"].isoformat() if hasattr(d["created_at"],"isoformat") else str(d["created_at"])
                return d

    def get_mfa_state(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT mfa_enabled,mfa_secret_enc FROM users WHERE id=%s", (user_id,)); return cur.fetchone()

    def set_mfa_secret(self, organization_id: str, user_id: str, secret_enc: str, enabled: bool):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("UPDATE users SET mfa_secret_enc=%s,mfa_enabled=%s,mfa_enabled_at=CASE WHEN %s THEN now() ELSE NULL END WHERE id=%s", (secret_enc,enabled,enabled,user_id))

    def disable_mfa(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("UPDATE users SET mfa_enabled=false,mfa_secret_enc=NULL,mfa_enabled_at=NULL WHERE id=%s", (user_id,))

    def create_recovery_token(self, organization_id: str, user_id: str, token_hash: str, expires_at: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("INSERT INTO password_recovery_tokens(organization_id,user_id,token_hash,expires_at) VALUES(%s,%s,%s,%s)", (organization_id,user_id,token_hash,expires_at))

    def get_recovery_token(self, organization_id: str, token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("SELECT recovery_id,organization_id,user_id,expires_at,used_at FROM password_recovery_tokens WHERE organization_id=%s AND token_hash=%s", (organization_id,token_hash)); return cur.fetchone()

    def consume_recovery_token(self, organization_id: str, token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("UPDATE password_recovery_tokens SET used_at=now() WHERE organization_id=%s AND token_hash=%s AND used_at IS NULL", (organization_id,token_hash)); return cur.rowcount == 1


    def get_email_verified(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT email_verified_at IS NOT NULL FROM users WHERE id=%s", (user_id,))
                row = cur.fetchone()
                return bool(row[0]) if row else False

    def mark_email_verified(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET email_verified_at=COALESCE(email_verified_at, now()) WHERE id=%s", (user_id,))

    def set_email_unverified(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET email_verified_at=NULL WHERE id=%s", (user_id,))

    def create_email_verification_token(self, organization_id: str, user_id: str, token_hash: str, expires_at: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO email_verification_tokens(organization_id,user_id,token_hash,expires_at) VALUES(%s,%s,%s,%s)", (organization_id,user_id,token_hash,expires_at))

    def get_email_verification_token(self, organization_id: str, token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT verification_id,organization_id,user_id,expires_at,used_at FROM email_verification_tokens WHERE organization_id=%s AND token_hash=%s", (organization_id,token_hash)); return cur.fetchone()

    def consume_email_verification_token(self, organization_id: str, token_hash: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE email_verification_tokens SET used_at=now() WHERE organization_id=%s AND token_hash=%s AND used_at IS NULL", (organization_id,token_hash)); return cur.rowcount == 1

    def get_user_by_id(self, organization_id: str, user_id: str):
        with self.transaction(organization_id) as conn:
            with conn.cursor() as cur: cur.execute("SELECT u.id,u.email,u.password_hash,m.role FROM users u JOIN memberships m ON m.user_id=u.id WHERE m.organization_id=%s AND u.id=%s", (organization_id,user_id)); return cur.fetchone()
