"""Minimal eCloudServ-compatible entrypoint."""
import os
import sys
def build_gunicorn_command(port=None):
    selected=port or os.environ.get("PORT") or "8080"
    return [sys.executable,"-m","gunicorn","--bind",f"0.0.0.0:{selected}","--workers","2","--threads","4","--timeout","60","wsgi:app"]
if __name__=="__main__":
    os.execv(sys.executable,build_gunicorn_command())
