"""
FoodLoop AI - In-Memory Rate Limiting Dependency
Provides sliding-window rate limiting for security-sensitive endpoints (auth, QR validation, AI queries).
"""
import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request
from app.utils.exceptions import RateLimitExceededError


class RateLimiter:
    """
    Sliding-window in-memory rate limiter dependency.
    Usage: Depends(RateLimiter(times=20, seconds=60))
    """
    def __init__(self, times: int = 60, seconds: int = 60):
        self.times = times
        self.seconds = seconds
        self._history: Dict[str, List[float]] = defaultdict(list)

    async def __call__(self, request: Request) -> bool:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        key = f"{client_ip}:{path}"

        now = time.time()
        window_start = now - self.seconds

        # Prune older entries
        self._history[key] = [t for t in self._history[key] if t > window_start]

        if len(self._history[key]) >= self.times:
            retry_after = int(self.seconds - (now - self._history[key][0]))
            raise RateLimitExceededError(
                message=f"Too many requests. Limit is {self.times} per {self.seconds} seconds.",
                details={"retry_after_seconds": max(1, retry_after)}
            )

        self._history[key].append(now)
        return True
