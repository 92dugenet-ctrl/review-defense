#!/usr/bin/env python3
"""Bounded hourly commercial-site maintenance for Review Defense."""
from pathlib import Path
import json, re, subprocess

ROOT=Path(__file__).resolve().parents[1]
landing=ROOT/"frontend/landing.html"
home_css=ROOT/"frontend/assets/home.css"
report=ROOT/"artifacts/hourly-premium-maintenance.json"

changes=[]
html=landing.read_text(encoding="utf-8")
original=html
html=re.sub(r'\s*<link[^>]+(?:fonts\.googleapis\.com|fonts\.gstatic\.com)[^>]*>', '', html, flags=re.I)
if 'class="hero rd-home-hero"' not in html and 'class="rd-home-hero hero"' not in html:
    html=html.replace('<section class="hero"', '<section class="hero rd-home-hero"', 1)
if 'id="public-login"' not in html:
    html=html.replace('class="btn-secondary" href="/app"', 'id="public-login" class="btn-secondary" href="/app"', 1)
if html!=original:
    landing.write_text(html,encoding="utf-8")
    changes.append("landing compatibility/external-font guardrails")

css=home_css.read_text(encoding="utf-8")
guard='.rd-home a:focus-visible,.rd-home button:focus-visible'
if guard not in css:
    css += '\n/* Premium accessibility guardrail. */\n.rd-home a:focus-visible,.rd-home button:focus-visible{outline:3px solid rgba(20,108,240,.35);outline-offset:3px}\n'
    home_css.write_text(css,encoding="utf-8")
    changes.append("homepage focus-visible guardrail")

report.parent.mkdir(parents=True,exist_ok=True)
report.write_text(json.dumps({"version":"6.40","changes":changes,"status":"CHANGED" if changes else "NO_CHANGE"},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
if changes:
    subprocess.run(["git","add","frontend/landing.html","frontend/assets/home.css"],cwd=ROOT,check=True)
    subprocess.run(["git","config","user.name","review-defense-bot"],cwd=ROOT,check=True)
    subprocess.run(["git","config","user.email","review-defense-bot@users.noreply.github.com"],cwd=ROOT,check=True)
    subprocess.run(["git","commit","-m","chore: hourly bounded premium maintenance"],cwd=ROOT,check=True)
print(json.dumps({"status":"CHANGED" if changes else "NO_CHANGE","changes":changes}))
