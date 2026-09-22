#!/usr/bin/env python3
"""V6.40 live HTTPS/auth/MFA/browser certification for a dedicated staging account."""
from __future__ import annotations
import argparse, json, os, sys, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def api_login(base: str, email: str, org: str, password: str, mfa_code: str | None = None):
    body = {"email": email, "organization_id": org, "password": password}
    if mfa_code: body["mfa_code"] = mfa_code
    req = urllib.request.Request(base.rstrip('/') + '/v1/auth/login', data=json.dumps(body).encode(), headers={"Content-Type":"application/json","Accept":"application/json"}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors='replace')
        try: payload=json.loads(raw)
        except json.JSONDecodeError: payload={"raw":raw[:1000]}
        return e.code,payload

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--base-url', default=os.getenv('STAGING_BASE_URL',''))
    ap.add_argument('--output', type=Path, default=ROOT/'artifacts/v6.40-live-e2e.json')
    args=ap.parse_args()
    base=args.base_url.rstrip('/')
    required=['E2E_EMAIL','E2E_PASSWORD','E2E_ORGANIZATION_ID']
    missing=[x for x in required if not os.getenv(x)]
    report={'version':'6.40','started_at':datetime.now(timezone.utc).isoformat(),'status':'NO-GO','base_url':base}
    if not base.startswith('https://'):
        report['error']='STAGING_BASE_URL must use HTTPS'
    elif missing:
        report['error']='missing required E2E secrets: '+', '.join(missing)
    else:
        email=os.environ['E2E_EMAIL']; password=os.environ['E2E_PASSWORD']; org=os.environ['E2E_ORGANIZATION_ID']; mfa_secret=os.getenv('E2E_MFA_SECRET','')
        if mfa_secret:
            status,payload=api_login(base,email,org,password)
            report['mfa_enforcement_without_code']={'status':status,'error':payload.get('error')}
            if status != 401:
                report['error']='MFA-enabled staging account accepted password-only login'
            else:
                from src.mfa import totp_code
                code=totp_code(mfa_secret)
                status,payload=api_login(base,email,org,password,code)
                report['mfa_login']={'status':status}
                if status != 200 or not payload.get('access_token'):
                    report['error']='MFA login failed'
        else:
            status,payload=api_login(base,email,org,password)
            report['password_login']={'status':status}
            if status != 200 or not payload.get('access_token'):
                report['error']='staging password login failed'
        if 'error' not in report:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
                    page=browser.new_page()
                    page.goto(base+'/app',wait_until='networkidle')
                    page.locator('input[name="email"]').fill(email)
                    page.locator('input[name="organization_id"]').fill(org)
                    page.locator('input[name="password"]').fill(password)
                    page.locator('#login button[type="submit"]').click()
                    if mfa_secret:
                        page.wait_for_selector('input[name="mfa_code"]',timeout=10000)
                        from src.mfa import totp_code
                        page.locator('input[name="mfa_code"]').fill(totp_code(mfa_secret))
                        page.locator('#login button[type="submit"]').click()
                    page.wait_for_selector('.sidebar',timeout=10000)
                    title=page.locator('#title').inner_text()
                    resources=page.evaluate("performance.getEntriesByType('resource').map(x => x.name)")
                    forbidden=[u for u in resources if 'googleapis.com' in u or 'google.com' in u]
                    report['browser']={'login':'PASS','dashboard':'Dashboard' in title,'no_external_google':not forbidden}
                    if not report['browser']['dashboard'] or forbidden:
                        report['error']='browser security/auth contract failed'
                    browser.close()
            except Exception as exc:
                report['error']=f'browser E2E failed: {exc}'
        if 'error' not in report:
            report['status']='CERTIFIED'
    report['completed_at']=datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,sort_keys=True))
    return 0 if report['status']=='CERTIFIED' else 1
if __name__=='__main__': raise SystemExit(main())
