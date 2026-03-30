from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

from api.routes import router as api_router
from middleware import LoggingMiddleware
from rate_limiter import RateLimiter
from utils.config import get_settings
from utils.logger import setup_logger

# Налаштування
settings = get_settings()
logger = setup_logger(__name__)

# Створення додатку
app = FastAPI(
    title="AI Vitamin Assistant API",
    description="API for personalized vitamin recommendations",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS налаштування для Docker
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Додаємо middleware
app.add_middleware(LoggingMiddleware)

# Підключаємо роути
app.include_router(api_router)

# Rate limiter (можна додати як dependency)
rate_limiter = RateLimiter(requests_per_minute=settings.RATE_LIMIT_REQUESTS)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.on_event("startup")
async def startup_event():
    """Дії при запуску"""
    logger.info(f"Starting AI Vitamin Assistant API v{app.version}")
    logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    logger.info(f"Allowed origins: {settings.ALLOWED_ORIGINS}")

@app.on_event("shutdown")
async def shutdown_event():
    """Дії при зупинці"""
    logger.info("Shutting down AI Vitamin Assistant API")

@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "AI Vitamin Assistant API",
        "version": app.version,
        "status": "running",
        "docs": "/api/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )