import sys
from loguru import logger
from config.settings import LOGS_DIR

logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | {message}")
logger.add(
    str(LOGS_DIR / "trading_{time:YYYY-MM-DD}.log"),
    rotation="1 day",
    retention="30 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<7} | {module}:{function}:{line} | {message}",
)
