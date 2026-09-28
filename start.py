"""Minimal local/server launcher for Review Defense."""
import os,subprocess,sys
if __name__=="__main__":
    port=os.environ.get("SERVER_PORT",os.environ.get("PORT","8080"))
    raise SystemExit(subprocess.call([sys.executable,"-m","gunicorn","--bind",f"0.0.0.0:{port}","--workers","2","--threads","4","--timeout","60","wsgi:app"]))
