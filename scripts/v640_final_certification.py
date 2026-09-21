#!/usr/bin/env python3
"""V6.40 final deterministic certification gate.

Non-destructive: validates the complete V6.40 console contract, runs the full
regression suite and compile checks, and writes an auditable report. It never
deploys, calls Google, changes production data, or bypasses human approval.
The gate itself never deploys. It performs no deployment, makes no Google API call, and requires
the human approval boundary to remain explicit before any controlled submission.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VERSION="6.40"
REQUIRED_FILES=[
 "frontend/assets/app.js","frontend/assets/app.css",
 "tests/test_v640_console_interface.py","scripts/release_candidate_gate.py",
 "scripts/staging_certification.py",".github/workflows/review-defense-staging.yml",
]

def run(cmd:list[str],timeout:int=900):
 p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 return p.returncode,p.stdout

def contracts():
 js=(ROOT/"frontend/assets/app.js").read_text()
 css=(ROOT/"frontend/assets/app.css").read_text()
 wf=(ROOT/".github/workflows/review-defense-staging.yml").read_text()
 checks={f"file:{p}":(ROOT/p).is_file() for p in REQUIRED_FILES}
 checks.update({
  "version:api":'"6.40"' in (ROOT/"src/api_server.py").read_text(),
  "version:release_gate":'VERSION = "6.40"' in (ROOT/"scripts/release_candidate_gate.py").read_text(),
  "version:staging_cert":'VERSION = "6.40"' in (ROOT/"scripts/staging_certification.py").read_text(),
  "workflow:archive":"review-defense-v6.40" in wf,
  "workflow:certification":"v6.40-staging-certification.json" in wf,
  "ui:block11":"alert-overview" in js and "Observabilité uniquement" in js,
  "ui:block12":"org-overview" in js and "Isolation organisationnelle" in js,
  "ui:block13":"auth-shell-premium" in js and "mfa_code" in js,
  "ui:responsive":"@media(max-width:600px)" in css,
  "human:approval":"Confirmer l’approbation humaine" in js,
  "human:submission":"Aucune exécution externe" in js,
  "google:frontend":not any(x in js for x in ["googleapis.com","google.com"]),
  "google:autonomous":not any(x in (ROOT/"src/api_server.py").read_text().lower() for x in ["delete review","report review","reply review"]),
 })
 checks["all"]=all(checks.values())
 return checks

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--output",type=Path,default=Path("artifacts/v6.40-final-certification.json"))
 ap.add_argument("--skip-tests",action="store_true")
 a=ap.parse_args(); out=a.output if a.output.is_absolute() else ROOT/a.output; out.parent.mkdir(parents=True,exist_ok=True)
 report={"version":VERSION,"started_at":datetime.now(timezone.utc).isoformat(),"status":"NO-GO","contracts":contracts()}
 if not report["contracts"]["all"]:
  report["error"]="one or more final contracts failed"
 elif a.skip_tests:
  report["status"]="CONTRACT-PASS-NOT-FULLY-CERTIFIED"
  report["limitation"]="regression and compile checks were intentionally skipped"
 else:
  rc,test=run([sys.executable,"-m","pytest","-q"])
  report["pytest"]={"returncode":rc,"tail":test[-16000:]}
  rc2,comp=run([sys.executable,"-m","compileall","-q","src","scripts","tests","wsgi.py"])
  report["compileall"]={"returncode":rc2,"output":comp[-4000:]}
  if rc==0 and rc2==0:
   report["status"]="PASS"
  else:
   report["error"]="regression or compile check failed"
 report["completed_at"]=datetime.now(timezone.utc).isoformat()
 raw=json.dumps(report,indent=2,sort_keys=True)+"\n"; out.write_text(raw,encoding="utf-8")
 report["sha256"]=hashlib.sha256(raw.encode()).hexdigest()
 print(json.dumps(report,indent=2,sort_keys=True))
 return 0 if report["status"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
