from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import json

from models.schemas import HealthProfile, Message

class SessionMemory:
    """In-memory storage for user sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)
    
    def get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> Dict:
        """Get existing session or create new one"""
        
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        
        # Create new session
        new_session_id = session_id or f"session_{datetime.now().timestamp()}_{user_id}"
        session = {
            "session_id": new_session_id,
            "user_id": user_id,
            "created_at": datetime.now(),
            "history": [],
            "recommendations": []
        }
        
        self.sessions[new_session_id] = session
        self.user_sessions[user_id].append(new_session_id)
        
        return session
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get history for specific session"""
        session = self.sessions.get(session_id)
        return session.get("history", []) if session else []
    
    def get_user_history(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all history for user across sessions"""
        all_history = []
        for session_id in self.user_sessions.get(user_id, []):
            session = self.sessions.get(session_id, {})
            all_history.extend(session.get("history", []))
        
        # Sort by timestamp and apply pagination
        all_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_history[offset:offset + limit]
    
    def add_interaction(self, session_id: str, user_message: str, assistant_message: str, recommendations: List) -> None:
        """Add interaction to session history"""
        session = self.sessions.get(session_id)
        if session:
            session["history"].append({
                "timestamp": datetime.now().isoformat(),
                "user": user_message,
                "assistant": assistant_message,
                "recommendations": recommendations
            })
            session["recommendations"].extend(recommendations)
    
    def clear_user_history(self, user_id: str) -> None:
        """Clear all history for user"""
        for session_id in self.user_sessions.get(user_id, []):
            if session_id in self.sessions:
                del self.sessions[session_id]
        self.user_sessions[user_id] = []
    
    def health_check(self) -> Dict:
        """Health check for memory storage"""
        return {
            "status": "healthy",
            "total_sessions": len(self.sessions),
            "total_users": len(self.user_sessions)
        }


class UserProfileMemory:
    """In-memory storage for user profiles"""
    
    def __init__(self):
        self.profiles: Dict[str, HealthProfile] = {}
    
    def get_profile(self, user_id: str) -> Optional[HealthProfile]:
        """Get user profile"""
        return self.profiles.get(user_id)
    
    def update_profile(self, user_id: str, profile: HealthProfile) -> HealthProfile:
        """Update user profile"""
        # If profile exists, merge with existing
        existing = self.profiles.get(user_id)
        if existing:
            # Merge logic (new data overrides old)
            for key, value in profile.dict().items():
                if value is not None and value != []:
                    setattr(existing, key, value)
            self.profiles[user_id] = existing
        else:
            self.profiles[user_id] = profile
        
        return self.profiles[user_id]
    
    def delete_profile(self, user_id: str) -> bool:
        """Delete user profile"""
        if user_id in self.profiles:
            del self.profiles[user_id]
            return True
        return False