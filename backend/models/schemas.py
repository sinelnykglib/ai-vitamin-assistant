from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

# ==================== ENUMS ====================

class TimeOfDay(str, Enum):
    MORNING = "morning"
    DINNER = "dinner"
    EVENING = "evening"

class Platform(str, Enum):
    WEB = "web"
    IOS = "ios"
    ANDROID = "android"
    TELEGRAM = "telegram"
    API = "api"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

# ==================== REQUEST MODELS ====================

class HealthProfile(BaseModel):
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[Gender] = None
    allergies: List[str] = []
    current_supplements: List[str] = []
    health_goals: List[str] = []
    medical_conditions: List[str] = []
    medications: List[str] = []
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 120):
            raise ValueError('Age must be between 0 and 120')
        return v

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('content')
    def validate_content(cls, v):
        if len(v) > 5000:
            raise ValueError('Message too long (max 5000 chars)')
        return v

class UserRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: List[Message] = []
    user_profile: Optional[HealthProfile] = None
    platform: Platform = Platform.WEB
    language: str = "uk"
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('user_id must contain only alphanumeric characters and underscores')
        return v

# ==================== RESPONSE MODELS ====================

class VitaminRecommendation(BaseModel):
    vitamin: str
    time: TimeOfDay
    dosage: Optional[str] = None
    notes: Optional[str] = None
    priority: Literal["high", "medium", "low"] = "medium"
    reason: Optional[str] = None

class AIResponse(BaseModel):
    request_id: str
    user_id: str
    session_id: str
    reply_message: str
    recommendations: List[VitaminRecommendation] = []
    schedule: dict = {
        "morning": [],
        "dinner": [],
        "evening": []
    }
    timestamp: datetime
    processing_time_ms: int
    confidence_score: Optional[float] = Field(None, ge=0, le=1)

class APIResponse(BaseModel):
    success: bool
    data: Optional[AIResponse | dict] = None
    error: Optional[str] = None
    message: Optional[str] = None
    meta: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None