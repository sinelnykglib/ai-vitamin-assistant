import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Імпортуємо логер
from utils.logger import get_logger

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логування всіх HTTP запитів"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Логуємо вхідний запит
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Обробляємо запит
        try:
            response = await call_next(request)
            
            # Логуємо час виконання
            process_time = time.time() - start_time
            logger.info(
                f"Response: {response.status_code} - "
                f"{process_time:.3f}s - {request.method} {request.url.path}"
            )
            
            # Додаємо заголовок з часом виконання
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error processing {request.method} {request.url.path}: {str(e)} "
                f"(time: {process_time:.3f}s)"
            )
            raise