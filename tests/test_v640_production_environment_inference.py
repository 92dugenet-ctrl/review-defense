import os

from src.production_config import ProductionConfig


def test_https_public_base_url_implies_production_when_environment_is_unset(monkeypatch):
    monkeypatch.delenv("REVIEW_DEFENSE_ENV", raising=False)
    monkeypatch.setenv("REVIEW_DEFENSE_PUBLIC_BASE_URL", "https://trustera-intelligence.ecloudserv.fr")
    config = ProductionConfig.from_env()
    assert config.environment == "production"
    assert config.production


def test_explicit_environment_still_wins(monkeypatch):
    monkeypatch.setenv("REVIEW_DEFENSE_ENV", "development")
    monkeypatch.setenv("REVIEW_DEFENSE_PUBLIC_BASE_URL", "https://trustera-intelligence.ecloudserv.fr")
    config = ProductionConfig.from_env()
    assert config.environment == "development"
    assert not config.production


def test_local_http_default_remains_development(monkeypatch):
    monkeypatch.delenv("REVIEW_DEFENSE_ENV", raising=False)
    monkeypatch.delenv("REVIEW_DEFENSE_PUBLIC_BASE_URL", raising=False)
    config = ProductionConfig.from_env()
    assert config.environment == "development"
    assert not config.production
