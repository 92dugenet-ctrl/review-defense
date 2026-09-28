from pathlib import Path
import os
import psycopg
ROOT=Path(__file__).resolve().parents[1]
def main():
    dsn=os.environ.get("DATABASE_URL")
    if not dsn: raise SystemExit("DATABASE_URL is required")
    with psycopg.connect(dsn) as conn:
        for path in sorted((ROOT/"migrations").glob("*.sql")): conn.execute(path.read_text(encoding="utf-8"))
        conn.commit()
if __name__=="__main__": main()
