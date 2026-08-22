"""Rate limiting service to prevent API abuse."""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status


class RateLimiter:
    """Simple in-memory rate limiter by user ID."""
    
    def __init__(self, requests_per_minute: int = 20):
        self.requests_per_minute = requests_per_minute
        self.requests: dict[int, list[float]] = {}
    
    def check_limit(self, user_id: int) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        minute_ago = now - 60
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        self.requests[user_id] = [
            ts for ts in self.requests[user_id]
            if ts > minute_ago
        ]
        
        if len(self.requests[user_id]) >= self.requests_per_minute:
            return False
        
        self.requests[user_id].append(now)
        return True


api_rate_limiter = RateLimiter(requests_per_minute=20)
