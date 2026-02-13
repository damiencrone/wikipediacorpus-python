"""Token-bucket rate limiter with sync and async support."""

from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """Token-bucket rate limiter.

    Parameters
    ----------
    rate : float
        Tokens added per second.
    burst : int
        Maximum tokens in the bucket.
    """

    def __init__(self, rate: float = 50.0, burst: int = 10) -> None:
        self.rate = rate
        self.burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._async_lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def acquire(self) -> None:
        """Block until a token is available (sync)."""
        while True:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            sleep_time = (1.0 - self._tokens) / self.rate
            time.sleep(sleep_time)

    async def acquire_async(self) -> None:
        """Wait until a token is available (async)."""
        async with self._async_lock:
            while True:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                sleep_time = (1.0 - self._tokens) / self.rate
                await asyncio.sleep(sleep_time)


# Module-level default limiter
_default_limiter = RateLimiter()
