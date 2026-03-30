from collections import defaultdict
import time
from typing import Dict, List
from fastapi import HTTPException, status

class RateLimiter:
    """
    Простий rate limiter на основі пам'яті
    Обмежує кількість запитів від одного користувача за хвилину
    """
    
    def __init__(self, requests_per_minute: int = 30):
        """
        Args:
            requests_per_minute: Максимальна кількість запитів за хвилину
        """
        self.requests_per_minute = requests_per_minute
        self.user_requests: Dict[str, List[float]] = defaultdict(list)
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """
        Перевіряє чи не перевищено ліміт запитів для користувача
        
        Args:
            user_id: Ідентифікатор користувача
            
        Returns:
            True якщо ліміт не перевищено
            
        Raises:
            HTTPException: Якщо ліміт перевищено
        """
        now = time.time()
        minute_ago = now - 60
        
        # Очищаємо старі запити (старші за хвилину)
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > minute_ago
        ]
        
        # Перевіряємо чи не перевищено ліміт
        if len(self.user_requests[user_id]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Maximum {self.requests_per_minute} requests per minute.",
                    "retry_after": 60
                }
            )
        
        # Додаємо поточний запит
        self.user_requests[user_id].append(now)
        return True
    
    def get_remaining_requests(self, user_id: str) -> int:
        """
        Повертає кількість залишених запитів для користувача
        """
        now = time.time()
        minute_ago = now - 60
        
        # Очищаємо старі запити
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > minute_ago
        ]
        
        return max(0, self.requests_per_minute - len(self.user_requests[user_id]))
    
    def reset_user(self, user_id: str) -> None:
        """
        Скидає лічильник запитів для користувача
        """
        if user_id in self.user_requests:
            self.user_requests[user_id] = []