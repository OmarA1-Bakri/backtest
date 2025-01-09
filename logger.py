"""Logger module."""

import logging
from core.config.settings import settings

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)

# Create handlers
file_handler = logging.FileHandler(settings.LOG_FILE)
console_handler = logging.StreamHandler()

# Create formatters and add it to handlers
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)8s] %(message)s (%(filename)s:%(lineno)s)"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
