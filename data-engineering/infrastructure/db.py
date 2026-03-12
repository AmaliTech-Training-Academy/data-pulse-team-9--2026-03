from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from config import settings

_source_engine = None
_target_engine = None

AnalyticsBase = declarative_base()


def _get_database_url(setting_key: str, env_var: str) -> str:
    url = settings["database"].get(setting_key, "")
    if not url:
        raise RuntimeError(f"Missing database setting '{setting_key}'. Set {env_var} in your .env or environment.")
    return url


def get_source_engine():
    global _source_engine
    if _source_engine is None:
        _source_engine = create_engine(_get_database_url("source_url", "DATABASE_URL"))
    return _source_engine


def get_target_engine():
    global _target_engine
    if _target_engine is None:
        target_url = _get_database_url("target_url", "TARGET_DB_URL")
        source_url = _get_database_url("source_url", "DATABASE_URL")
        if target_url == source_url or target_url == "${database.source_url}":
            _target_engine = get_source_engine()
        else:
            _target_engine = create_engine(target_url)
    return _target_engine


def reset_engines():
    global _source_engine, _target_engine
    if _source_engine:
        _source_engine.dispose()
        _source_engine = None
    if _target_engine and _target_engine != _source_engine:
        _target_engine.dispose()
        _target_engine = None
