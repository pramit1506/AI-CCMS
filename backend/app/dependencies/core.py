from app.core.config import settings, Settings
from loguru import logger

def get_settings() -> Settings:
    return settings

def get_logger():
    return logger
