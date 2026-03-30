from fastapi import HTTPException, status
from typing import List, Optional
from models.schemas import UserRequest, HealthProfile

def validate_user_request(request: UserRequest) -> None:
    """
    Validate user request data
    
    Raises:
        HTTPException: If validation fails
    """
    # Validate user_id
    if not request.user_id or len(request.user_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id: must be between 1 and 100 characters"
        )
    
    # Validate message
    if not request.message or len(request.message) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message: must be between 1 and 2000 characters"
        )
    
    # Validate conversation history limit
    if len(request.conversation_history) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many messages in conversation history (max 100)"
        )
    
    # Validate language
    supported_languages = ["uk", "en", "ru"]
    if request.language not in supported_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: {request.language}. Supported: {supported_languages}"
        )

def validate_health_profile(profile: HealthProfile) -> None:
    """
    Validate health profile data
    
    Raises:
        HTTPException: If validation fails
    """
    # Validate age
    if profile.age is not None and (profile.age < 0 or profile.age > 120):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid age: must be between 0 and 120"
        )
    
    # Validate allergies (max 50 items)
    if len(profile.allergies) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many allergies (max 50)"
        )
    
    # Validate current supplements (max 50 items)
    if len(profile.current_supplements) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many supplements (max 50)"
        )
    
    # Validate health goals (max 20 items)
    if len(profile.health_goals) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many health goals (max 20)"
        )

def validate_vitamin_name(name: str) -> bool:
    """Validate vitamin name format"""
    if not name or len(name) > 100:
        return False
    # Basic validation - allow letters, numbers, spaces, hyphens
    import re
    return bool(re.match(r'^[a-zA-Z0-9\s\-]+$', name))