"""
Single-flight + micro-cache for hot, parameterless async producers.

A plain TTL cache does NOT stop a request storm: at the instant a key expires,
every concurrent caller sees a miss and they all launch the upstream call at
once (cache stampede). This combines two protections so that does not happen:

  * **single-flight** — while a fetch is in flight, concurrent callers await the
    SAME task instead of each launching their own. K concurrent callers => 1
    upstream call.
  * **micro-cache** — a *successful* result is reused for ``ttl`` seconds, so
    repeat calls inside the window don't touch the producer at all.

Scope is per-process (one instance per gunicorn worker): coalescing needs a
shared in-process future, so it cannot span workers — with W workers the
upstream ceiling is ~W calls per TTL window, not 1. Errors are never cached, so
a transient upstream failure isn't pinned for the whole window.

Designed for a global payload polled frequently by many clients — e.g. the
NextBilling online-calls feed, which the call-sprint banner polls every 1.5s
per active call and which returns identical bytes for every advisor.
"""
from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


class SingleFlightCache(Generic[T]):
    """Coalesces concurrent calls to one async producer and serves a short TTL
    cache of its last successful result.

    Args:
        ttl_seconds: how long a successful result stays fresh. Keep it <= the
            client poll interval so freshness never regresses.
        is_error: optional predicate; when it returns True for a result, that
            result is returned to callers but NOT cached (so failures retry).
    """

    def __init__(
        self,
        ttl_seconds: float,
        is_error: Optional[Callable[[T], bool]] = None,
    ) -> None:
        self._ttl = max(0.0, ttl_seconds)
        self._is_error = is_error
        self._value: Optional[T] = None
        self._expires_at: float = 0.0
        self._inflight: "Optional[asyncio.Task[T]]" = None
        self._lock = asyncio.Lock()

    async def get(self, producer: Callable[[], Awaitable[T]]) -> T:
        """Return a fresh cached value, or coalesce onto a single in-flight
        call of ``producer`` if there is no fresh value."""
        # Fast path: a fresh value needs no lock.
        if self._value is not None and time.monotonic() < self._expires_at:
            return self._value

        async with self._lock:
            # Re-check under the lock — another caller may have just refreshed.
            if self._value is not None and time.monotonic() < self._expires_at:
                return self._value
            if self._inflight is None:
                self._inflight = asyncio.create_task(producer())
            task = self._inflight

        try:
            result = await task
        finally:
            # Clear the slot so the next expiry starts a new flight. Only the
            # task we launched clears it (a newer flight must survive).
            async with self._lock:
                if self._inflight is task:
                    self._inflight = None

        if self._is_error is None or not self._is_error(result):
            self._value = result
            self._expires_at = time.monotonic() + self._ttl
        return result

    def invalidate(self) -> None:
        """Drop the cached value (next call refetches). Does not cancel an
        in-flight fetch."""
        self._value = None
        self._expires_at = 0.0
