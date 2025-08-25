"""Logging configuration for the ETL pipeline."""
from __future__ import annotations

import logging.config
from pathlib import Path
from logging.handlers import RotatingFileHandler  # noqa: F401  # ensure import for config

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs" / "pipeline.log"


def setup_logging(log_path: Path = LOG_PATH) -> None:
    """Configure root logger with console and rotating file handlers."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": str(log_path),
                "maxBytes": 1_000_000,
                "backupCount": 5,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
    }
    logging.config.dictConfig(config)
