"""
Nueva Compare Tool - Logger Utility
Production-grade logging with file and console handlers.
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_DIR = Path.home() / ".nueva_compare" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"nueva_compare_{datetime.now().strftime('%Y%m%d')}.log"

_loggers = {}


def get_logger(name: str) -> logging.Logger:
    """Get or create a named logger with file and console handlers."""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        _loggers[name] = logger
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-25s | L%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler — 5 MB per file, keep 7 backups
    fh = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=7, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Console handler — INFO and above
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.propagate = False

    _loggers[name] = logger
    return logger


def log_exception(logger: logging.Logger, exc: Exception, context: str = "") -> str:
    """Log a full exception with traceback. Returns formatted message."""
    tb = traceback.format_exc()
    msg = f"{context} | {type(exc).__name__}: {exc}" if context else f"{type(exc).__name__}: {exc}"
    logger.error(msg)
    logger.debug("Full traceback:\n%s", tb)
    return msg


ROOT_LOGGER = get_logger("nueva_compare")
ROOT_LOGGER.info("Nueva Compare Tool logger initialised. Log file: %s", LOG_FILE)
