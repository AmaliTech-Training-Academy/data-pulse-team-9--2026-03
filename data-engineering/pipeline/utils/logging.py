import logging
from pathlib import Path

from config import settings

_log_dir = Path(__file__).parent.parent.parent / settings["logging"]["directory"]
_log_dir.mkdir(exist_ok=True)

LOG_FILE = _log_dir / "etl.log"
ERROR_LOG_FILE = _log_dir / "etl_errors.log"

_formatter = logging.Formatter(
    settings["logging"]["format"],
    datefmt=settings["logging"]["date_format"],
)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, settings["logging"]["level"]))
    logger.propagate = False

    all_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    all_handler.setLevel(logging.INFO)
    all_handler.setFormatter(_formatter)
    logger.addHandler(all_handler)

    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(_formatter)
    logger.addHandler(error_handler)

    return logger
