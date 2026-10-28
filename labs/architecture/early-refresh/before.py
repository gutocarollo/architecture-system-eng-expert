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
                task = asyncio.create_task(producer())
                # Slot-clearing and result-caching are driven by the task
                # settling, not by an awaiter reaching its finally — so a
                # cancelled awaiter can neither orphan the slot (forcing a 2nd
                # upstream call mid-flight) nor lose a successful result.
                task.add_done_callback(self._on_inflight_settled)
                self._inflight = task
            task = self._inflight

        # ``shield`` so a cancelled awaiter (request timeout / client disconnect,
        # which FastAPI propagates to the request task) does not cancel the
        # SHARED task and take every other coalesced caller down with it. Only
        # the cancelled caller raises; the rest still get the upstream result.
        return await asyncio.shield(task)

    def _on_inflight_settled(self, task: "asyncio.Task[T]") -> None:
        """Done-callback for the shared in-flight task.

        Runs exactly once, when the task settles, regardless of how many
        awaiters cancelled. Frees the slot and caches a successful result. A
        cancelled or failed task caches nothing (errors must retry), and
        retrieving the outcome here also marks any exception as consumed.
        """
        if self._inflight is task:
            self._inflight = None
        if task.cancelled() or task.exception() is not None:
            return
        result = task.result()
        # A buggy / over-narrow ``is_error`` predicate (e.g. ``d.get("error")``
        # on a payload that turns out not to be a dict) must NOT raise out of
        # this done-callback: the exception would be swallowed by the loop's
        # handler (logged as "Exception in callback ..." on every settle), the
        # slot is already cleared, and ``_value`` would never be set — silently
        # disabling the cache for that payload shape. The task settled normally,
        # so an unclassifiable result is treated as a cacheable success.
        is_error = False
        if self._is_error is not None:
            try:
                is_error = bool(self._is_error(result))
            except Exception:
                is_error = False
        if not is_error:
            self._value = result
            self._expires_at = time.monotonic() + self._ttl

    def invalidate(self) -> None:
        """Drop the cached value (next call refetches). Does not cancel an
        in-flight fetch."""
        self._value = None
        self._expires_at = 0.0
