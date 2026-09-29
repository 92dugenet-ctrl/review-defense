"""V5.5 performance, concurrency and resilience primitives.

Framework-neutral controls for Review Defense.  They deliberately avoid network
calls and external service assumptions.  Adapters can compose these primitives
around database, object-store or provider operations.
"""
from __future__ import annotations

import hashlib
import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, Mapping, TypeVar

T = TypeVar("T")


class RetryExhaustedError(RuntimeError):
    def __init__(self, message: str, *, attempts: int, last_error: Exception) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.05
    max_delay_seconds: float = 1.0
    multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.base_delay_seconds < 0 or self.max_delay_seconds < 0:
            raise ValueError("retry delays must be non-negative")
        if self.base_delay_seconds > self.max_delay_seconds:
            raise ValueError("base delay cannot exceed max delay")
        if self.multiplier < 1:
            raise ValueError("multiplier must be >= 1")

    def delay_for(self, failed_attempt: int) -> float:
        if failed_attempt < 1:
            raise ValueError("failed_attempt must be positive")
        return min(self.max_delay_seconds, self.base_delay_seconds * (self.multiplier ** (failed_attempt - 1)))


class RetryExecutor(Generic[T]):
    def __init__(self, policy: RetryPolicy, *, sleep: Callable[[float], None] = time.sleep,
                 retryable: tuple[type[Exception], ...] = (TimeoutError, ConnectionError)) -> None:
        self.policy = policy
        self.sleep = sleep
        self.retryable = retryable

    def run(self, operation: Callable[[], T]) -> T:
        last: Exception | None = None
        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                return operation()
            except Exception as exc:
                last = exc
                if not isinstance(exc, self.retryable) or attempt >= self.policy.max_attempts:
                    if attempt >= self.policy.max_attempts and isinstance(exc, self.retryable):
                        raise RetryExhaustedError("retry budget exhausted", attempts=attempt, last_error=exc) from exc
                    raise
                self.sleep(self.policy.delay_for(attempt))
        assert last is not None
        raise RetryExhaustedError("retry budget exhausted", attempts=self.policy.max_attempts, last_error=last)


@dataclass(frozen=True)
class Deadline:
    end_monotonic: float

    @classmethod
    def after(cls, seconds: float, *, clock: Callable[[], float] = time.monotonic) -> "Deadline":
        if seconds <= 0:
            raise ValueError("deadline must be positive")
        return cls(clock() + seconds)

    def remaining(self, *, clock: Callable[[], float] = time.monotonic) -> float:
        return max(0.0, self.end_monotonic - clock())

    def expired(self, *, clock: Callable[[], float] = time.monotonic) -> bool:
        return self.remaining(clock=clock) <= 0

    def require_remaining(self, *, clock: Callable[[], float] = time.monotonic) -> float:
        remaining = self.remaining(clock=clock)
        if remaining <= 0:
            raise TimeoutError("operation deadline exceeded")
        return remaining


class IdempotencyConflict(RuntimeError):
    pass


class _Pending:
    def __init__(self, fingerprint: str) -> None:
        self.fingerprint = fingerprint
        self.done = False
        self.result: Any = None
        self.error: BaseException | None = None
        self.condition = threading.Condition()


class IdempotencyStore(Generic[T]):
    """Thread-safe in-memory idempotency barrier.

    A key may execute at most once for a given request fingerprint. Concurrent
    callers wait for the first execution and receive the same result/error.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: dict[str, _Pending] = {}

    @staticmethod
    def fingerprint(payload: bytes | str | Mapping[str, Any]) -> str:
        if isinstance(payload, bytes):
            raw = payload
        elif isinstance(payload, str):
            raw = payload.encode("utf-8")
        else:
            import json
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def execute(self, key: str, fingerprint: str, operation: Callable[[], T]) -> T:
        if not key or not fingerprint:
            raise ValueError("idempotency key and fingerprint are required")
        with self._lock:
            existing = self._entries.get(key)
            if existing is None:
                entry = _Pending(fingerprint)
                self._entries[key] = entry
                owner = True
            else:
                if existing.fingerprint != fingerprint:
                    raise IdempotencyConflict("idempotency key reused with different request")
                entry = existing
                owner = False
        if owner:
            try:
                result = operation()
                with entry.condition:
                    entry.result = result
                    entry.done = True
                    entry.condition.notify_all()
                return result
            except BaseException as exc:
                with entry.condition:
                    entry.error = exc
                    entry.done = True
                    entry.condition.notify_all()
                raise
        with entry.condition:
            while not entry.done:
                entry.condition.wait()
            if entry.error is not None:
                raise entry.error
            return entry.result

    def size(self) -> int:
        with self._lock:
            return len(self._entries)


class CircuitOpenError(RuntimeError):
    pass


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int = 3, recovery_seconds: float = 30.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        if failure_threshold < 1 or recovery_seconds <= 0:
            raise ValueError("invalid circuit breaker configuration")
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.clock = clock
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at: float | None = None
        self._probe_in_flight = False

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._refresh_locked()
            return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failures

    def _refresh_locked(self) -> None:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if self.clock() - self._opened_at >= self.recovery_seconds:
                self._state = CircuitState.HALF_OPEN
                self._probe_in_flight = False

    def _before_call(self) -> None:
        with self._lock:
            self._refresh_locked()
            if self._state == CircuitState.OPEN:
                raise CircuitOpenError("circuit is open")
            if self._state == CircuitState.HALF_OPEN:
                if self._probe_in_flight:
                    raise CircuitOpenError("circuit recovery probe already in flight")
                self._probe_in_flight = True

    def _success(self) -> None:
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failures = 0
            self._opened_at = None
            self._probe_in_flight = False

    def _failure(self) -> None:
        with self._lock:
            self._probe_in_flight = False
            self._failures += 1
            if self._state == CircuitState.HALF_OPEN or self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = self.clock()

    def call(self, operation: Callable[[], T]) -> T:
        self._before_call()
        try:
            result = operation()
        except Exception:
            self._failure()
            raise
        self._success()
        return result


class ConcurrencyLimitError(RuntimeError):
    pass


class ConcurrencyGate:
    """Bound in-flight work to protect CPU, DB and provider resources."""
    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("limit must be positive")
        self.limit = limit
        self._semaphore = threading.BoundedSemaphore(limit)
        self._lock = threading.Lock()
        self._active = 0
        self._peak = 0

    def acquire(self, *, timeout: float | None = None) -> None:
        acquired = self._semaphore.acquire(timeout=timeout if timeout is not None else -1)
        if not acquired:
            raise ConcurrencyLimitError("concurrency limit reached")
        with self._lock:
            self._active += 1
            self._peak = max(self._peak, self._active)

    def release(self) -> None:
        with self._lock:
            if self._active <= 0:
                raise RuntimeError("concurrency gate released without acquire")
            self._active -= 1
        self._semaphore.release()

    def __enter__(self) -> "ConcurrencyGate":
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.release()

    @property
    def active(self) -> int:
        with self._lock:
            return self._active

    @property
    def peak(self) -> int:
        with self._lock:
            return self._peak


@dataclass(frozen=True)
class SlidingWindow:
    limit: int
    window_seconds: float

    def __post_init__(self) -> None:
        if self.limit < 1 or self.window_seconds <= 0:
            raise ValueError("invalid sliding window")


class ThroughputLimiter:
    """Small thread-safe rolling-window limiter for local/provider protection."""
    def __init__(self, config: SlidingWindow, *, clock: Callable[[], float] = time.monotonic) -> None:
        self.config = config
        self.clock = clock
        self._lock = threading.Lock()
        self._hits: deque[float] = deque()

    def allow(self) -> bool:
        now = self.clock()
        cutoff = now - self.config.window_seconds
        with self._lock:
            while self._hits and self._hits[0] <= cutoff:
                self._hits.popleft()
            if len(self._hits) >= self.config.limit:
                return False
            self._hits.append(now)
            return True
