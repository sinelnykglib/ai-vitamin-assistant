from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import time
import uuid
from datetime import datetime

from models.schemas import (
    UserRequest, 
    AIResponse, 
    VitaminRecommendation,
    HealthProfile,
    SessionHistory,
    APIResponse,
    ErrorResponse
)
from services.preprocess import preprocess_request
from services.n8n_client import N8NClient
from services.postprocess import postprocess_recommendations
from services.response_builder import build_response
from database.memory import SessionMemory, UserProfileMemory
from utils.validators import validate_user_request, validate_health_profile
from utils.config import get_settings
from utils.logger import setup_logger

router = APIRouter(prefix="/api/v1", tags=["vitamin-assistant"])
logger = setup_logger(__name__)
settings = get_settings()

# Ініціалізація сервісів
session_memory = SessionMemory()
user_profile_memory = UserProfileMemory()
n8n_client = N8NClient(settings.N8N_WEBHOOK_URL)

# ==================== ЕНДПОІНТИ ====================

@router.post(
    "/recommend", 
    response_model=APIResponse,
    summary="Отримати рекомендації з вітамінів",
    description="Аналізує запит користувача та повертає персоналізовані рекомендації"
)
async def get_recommendations(request: UserRequest):
    """
    Основний ендпоінт для отримання рекомендацій
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # 1. Валідація вхідних даних
        validate_user_request(request)
        
        # 2. Логування запиту
        logger.info(f"Request {request_id} from user {request.user_id}: {request.message[:100]}")
        
        # 3. Отримуємо або створюємо сесію
        session = session_memory.get_or_create_session(
            request.user_id, 
            request.session_id
        )
        
        # 4. Отримуємо профіль користувача
        user_profile = user_profile_memory.get_profile(request.user_id)
        if request.user_profile:
            # Оновлюємо профіль, якщо надано
            user_profile = user_profile_memory.update_profile(
                request.user_id, 
                request.user_profile
            )
        
        # 5. Preprocessing - підготовка даних для AI
        preprocessed = preprocess_request(
            message=request.message,
            user_profile=user_profile,
            conversation_history=session.history[-10:],  # останні 10 повідомлень
            context={
                "session_id": session.session_id,
                "request_id": request_id,
                "platform": request.platform
            }
        )
        
        # 6. Виклик n8n workflow
        n8n_response = await n8n_client.send_request(
            preprocessed=preprocessed,
            user_profile=user_profile,
            session_history=session.history
        )
        
        # 7. Postprocessing - застосування правил
        processed_recommendations = postprocess_recommendations(
            n8n_response.get("recommendations", []),
            user_profile=user_profile
        )
        
        # 8. Формування відповіді
        response_data = build_response(
            recommendations=processed_recommendations,
            ai_message=n8n_response.get("message", ""),
            user_profile=user_profile
        )
        
        # 9. Створення структурованої відповіді
        ai_response = AIResponse(
            request_id=request_id,
            user_id=request.user_id,
            session_id=session.session_id,
            reply_message=response_data["message"],
            recommendations=[
                VitaminRecommendation(**rec) for rec in processed_recommendations
            ],
            schedule=response_data["schedule"],
            timestamp=datetime.now(),
            processing_time_ms=int((time.time() - start_time) * 1000),
            confidence_score=n8n_response.get("confidence", 0.85)
        )
        
        # 10. Збереження в історію
        session.add_interaction(
            user_message=request.message,
            assistant_message=ai_response.reply_message,
            recommendations=processed_recommendations
        )
        
        # 11. Логування успіху
        logger.info(f"Request {request_id} completed in {ai_response.processing_time_ms}ms")
        
        return APIResponse(
            success=True,
            data=ai_response,
            meta={
                "request_id": request_id,
                "processing_time_ms": ai_response.processing_time_ms,
                "api_version": "v1"
            }
        )
        
    except HTTPException as he:
        logger.warning(f"Request {request_id} failed: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Request {request_id} error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get(
    "/history/{user_id}",
    response_model=APIResponse,
    summary="Отримати історію рекомендацій"
)
async def get_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Отримує історію взаємодій користувача
    """
    try:
        if session_id:
            history = session_memory.get_session_history(session_id)
        else:
            history = session_memory.get_user_history(user_id, limit, offset)
        
        return APIResponse(
            success=True,
            data={
                "user_id": user_id,
                "total": len(history),
                "history": history,
                "pagination": {
                    "limit": limit,
                    "offset": offset
                }
            }
        )
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve history"
        )


@router.put(
    "/profile/{user_id}",
    response_model=APIResponse,
    summary="Оновити профіль користувача"
)
async def update_profile(user_id: str, profile: HealthProfile):
    """
    Оновлює профіль користувача для персоналізації
    """
    try:
        validate_health_profile(profile)
        updated_profile = user_profile_memory.update_profile(user_id, profile)
        
        return APIResponse(
            success=True,
            data=updated_profile,
            message="Profile updated successfully"
        )
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update profile"
        )


@router.get(
    "/profile/{user_id}",
    response_model=APIResponse,
    summary="Отримати профіль користувача"
)
async def get_profile(user_id: str):
    """
    Отримує поточний профіль користувача
    """
    profile = user_profile_memory.get_profile(user_id)
    
    return APIResponse(
        success=True,
        data=profile or {},
        message="Profile retrieved" if profile else "No profile found"
    )


@router.delete(
    "/history/{user_id}",
    response_model=APIResponse,
    summary="Очистити історію користувача"
)
async def clear_history(user_id: str):
    """
    Очищає всю історію взаємодій користувача
    """
    session_memory.clear_user_history(user_id)
    
    return APIResponse(
        success=True,
        message="History cleared successfully"
    )


@router.get(
    "/health",
    response_model=APIResponse,
    summary="Health check endpoint"
)
async def health_check():
    """
    Перевірка стану сервісу
    """
    return APIResponse(
        success=True,
        data={
            "status": "healthy",
            "services": {
                "n8n": await n8n_client.health_check(),
                "database": session_memory.health_check(),
                "memory": "ok"
            }
        }
    )