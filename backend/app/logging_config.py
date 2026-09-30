import logging
import time
from pathlib import Path
from logging.handlers import RotatingFileHandler


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "world_001.log"

BASE_LOGGER_NAME = "world_001"


def setup_logging():
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    logger = logging.getLogger(
        BASE_LOGGER_NAME
    )

    # Evita handlers duplicados em reloads do Uvicorn.
    if logger.handlers:
        return

    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)sZ | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )

    # Horário UTC nos logs.
    formatter.converter = time.gmtime

    console_handler = logging.StreamHandler()

    console_handler.setFormatter(
        formatter
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )

    logger.addHandler(
        file_handler
    )


def get_logger(category: str):
    setup_logging()

    return logging.getLogger(
        f"{BASE_LOGGER_NAME}.{category}"
    )