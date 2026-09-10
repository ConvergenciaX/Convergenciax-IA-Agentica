"""DocChat RAG — Logging configuration (file + stdout with rotation)."""
from loguru import logger
import sys
from config.settings import settings
from pathlib import Path

# Remove default handler
logger.remove()

# File logging with rotation
log_path = Path(settings.LOG_DIR) / settings.LOG_FILE
logger.add(
    str(log_path),
    rotation=f"{settings.LOG_MAX_SIZE_MB} MB",
    retention=f"{settings.LOG_BACKUP_COUNT * 10} days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    level=settings.LOG_LEVEL
)

# Stdout logging (console)
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | {message}",
    level=settings.LOG_LEVEL
)

logger.info(f"Logging initialized (level={settings.LOG_LEVEL}, file={log_path})")
