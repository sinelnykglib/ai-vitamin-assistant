import logging
import sys
from datetime import datetime
from typing import Optional

from utils.config import get_settings

settings = get_settings()

def setup_logger(name: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
    """
    Налаштовує логер для додатку
    
    Args:
        name: Ім'я логера (зазвичай __name__)
        level: Рівень логування
    
    Returns:
        Налаштований логер
    """
    logger = logging.getLogger(name or __name__)
    
    # Встановлюємо рівень логування
    log_level = level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Якщо вже є handlers, не додаємо нові
    if logger.handlers:
        return logger
    
    # Форматування логів
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler для виводу в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler для запису в файл (якщо вказано)
    if settings.LOG_FILE:
        try:
            file_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")
    
    return logger

# Для зворотньої сумісності
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Аліас для setup_logger"""
    return setup_logger(name)