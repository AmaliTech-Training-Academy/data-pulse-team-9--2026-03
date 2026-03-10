from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from config import settings

_source_engine = None
_target_engine = None

AnalyticsBase = declarative_base()


def get_source_engine():
    global _source_engine
    if _source_engine is None:
        _source_engine = create_engine(settings["database"]["source_url"])
    return _source_engine


def get_target_engine():
    global _target_engine
    if _target_engine is None:
        target_url = settings["database"]["target_url"]
        source_url = settings["database"]["source_url"]
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
