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
  * **early refresh** (opt-in) — past ``early_ttl`` (but before ``ttl``) the
    still-valid value is served *immediately* while a single background fetch
    refreshes it. No caller ever blocks on the producer at the expiry boundary,
    so a slow upstream (NextBilling tail latency) never stalls a poll — the
    stale-but-serveable value covers the refresh. Disabled by default
    (``early_ttl == ttl``), which keeps the plain single-flight behaviour.

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
        early_ttl_seconds: optional early-refresh threshold (seconds). Past it,
            but before ``ttl``, the value is served immediately while a single
            background fetch refreshes it — so no caller blocks on a slow
            producer at the expiry boundary. Must be <= ttl; defaults to ttl
            (early refresh disabled — plain single-flight + micro-cache).
    """

    def __init__(
        self,
        ttl_seconds: float,
        is_error: Optional[Callable[[T], bool]] = None,
        early_ttl_seconds: Optional[float] = None,
    ) -> None:
        self._ttl = max(0.0, ttl_seconds)
        # Early-refresh window. Default (None) == ttl => disabled: the early
        # branch in get() is never reached, so behaviour is the plain TTL cache.
        self._early_ttl = (
            self._ttl
            if early_ttl_seconds is None
            else max(0.0, min(early_ttl_seconds, self._ttl))
        )
        self._is_error = is_error
        self._value: Optional[T] = None
        self._expires_at: float = 0.0
        self._early_expires_at: float = 0.0
        self._inflight: "Optional[asyncio.Task[T]]" = None
        self._lock = asyncio.Lock()

    async def get(self, producer: Callable[[], Awaitable[T]]) -> T:
        """Return a fresh cached value, or coalesce onto a single in-flight
        call of ``producer`` if there is no fresh value."""
        # Fast path: a still-valid value needs no lock.
        value = self._value
        if value is not None and time.monotonic() < self._expires_at:
            # Past the early-refresh threshold (and only if enabled): serve the
            # still-valid value now and kick off ONE background fetch. The caller
            # does NOT await it, so a slow producer never stalls this poll.
            if time.monotonic() >= self._early_expires_at:
                self._start_background_refresh(producer)
            return value

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

    def _start_background_refresh(self, producer: Callable[[], Awaitable[T]]) -> None:
        """Launch a fire-and-forget, single-flighted refresh of the value.

        Used only on the early-refresh path, where the caller already has a
        serveable value and does NOT await this task — so there is no awaiter to
        cancel and the ``shield`` cancellation-isolation concern simply does not
        arise here. Single-flighted via the shared ``_inflight`` slot: if a fetch
        (foreground or background) is already running, this is a no-op. The
        check-and-set is atomic under asyncio (no await between), and the same
        done-callback caches the result.
        """
        if self._inflight is None:
            task = asyncio.create_task(producer())
            task.add_done_callback(self._on_inflight_settled)
            self._inflight = task

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
            settled_at = time.monotonic()
            self._value = result
            self._expires_at = settled_at + self._ttl
            self._early_expires_at = settled_at + self._early_ttl

    def invalidate(self) -> None:
        """Drop the cached value (next call refetches). Does not cancel an
        in-flight fetch."""
        self._value = None
        self._expires_at = 0.0
        self._early_expires_at = 0.0
