from __future__ import annotations
import os
from dataclasses import dataclass
@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("REVIEW_DEFENSE_ENV","development")
    host: str = os.getenv("HOST","0.0.0.0")
    port: int = int(os.getenv("PORT","8080"))
    database_url: str = os.getenv("DATABASE_URL","")
    secure_headers: bool = os.getenv("SECURE_HEADERS","true").lower() in {"1","true","yes","on"}
def get_settings() -> Settings:
    return Settings()
