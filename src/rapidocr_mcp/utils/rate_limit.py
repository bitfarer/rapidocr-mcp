"""Rate limiting utilities."""

import asyncio
import time
from collections import deque
from loguru import logger

from ..config import settings


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests: int, period: int):
        self.requests = requests
        self.period = period
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self._lock:
            now = time.time()
            while self._timestamps and now - self._timestamps[0] >= self.period:
                self._timestamps.popleft()

            if len(self._timestamps) < self.requests:
                self._timestamps.append(now)
                return True
            return False

    async def wait_and_acquire(self) -> None:
        while not await self.acquire():
            await asyncio.sleep(0.1)


class ConcurrentLimiter:
    """Semaphore-based concurrent request limiter."""

    def __init__(self, max_concurrent: int):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def acquire(self):
        await self._semaphore.acquire()

    def release(self):
        self._semaphore.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()


rate_limiter = RateLimiter(settings.rate_limit_requests, settings.rate_limit_period)
concurrent_limiter = ConcurrentLimiter(settings.max_concurrent_requests)
