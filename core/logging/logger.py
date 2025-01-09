# backtest/logger.py

import logging
from logging.handlers import RotatingFileHandler
from core import config


def setup_logger():
    logger = logging.getLogger("backtest")
    if not logger.hasHandlers():
        logger.setLevel(getattr(logging, config.logging.log_level, logging.INFO))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            getattr(logging, config.logging.log_level, logging.INFO)
        )
        console_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)

        # File handler
        file_handler = RotatingFileHandler(
            config.logging.log_file, maxBytes=5 * 1024 * 1024, backupCount=5  # 5MB
        )
        file_handler.setLevel(getattr(logging, config.logging.log_level, logging.INFO))
        file_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        # Add handlers to the logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


logger = setup_logger()
