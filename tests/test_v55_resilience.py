import threading
import time

import pytest

from src.resilience import (
    CircuitBreaker, CircuitOpenError, CircuitState, ConcurrencyGate,
    ConcurrencyLimitError, Deadline, IdempotencyConflict, IdempotencyStore,
    RetryExecutor, RetryExhaustedError, RetryPolicy, SlidingWindow,
    ThroughputLimiter,
)


def test_retry_only_retries_transient_errors_and_backoff_is_bounded():
    sleeps = []
    attempts = []
    policy = RetryPolicy(max_attempts=4, base_delay_seconds=0.1, max_delay_seconds=0.25)
    executor = RetryExecutor(policy, sleep=sleeps.append)

    def op():
        attempts.append(1)
        if len(attempts) < 4:
            raise TimeoutError("temporary")
        return "ok"

    assert executor.run(op) == "ok"
    assert len(attempts) == 4
    assert sleeps == [0.1, 0.2, 0.25]


def test_retry_does_not_retry_non_transient_error():
    calls = []
    executor = RetryExecutor(RetryPolicy(max_attempts=4), sleep=calls.append)
    with pytest.raises(ValueError):
        executor.run(lambda: (_ for _ in ()).throw(ValueError("bad input")))
    assert calls == []


def test_retry_exhaustion_preserves_last_error():
    executor = RetryExecutor(RetryPolicy(max_attempts=3, base_delay_seconds=0), sleep=lambda _: None)
    with pytest.raises(RetryExhaustedError) as exc:
        executor.run(lambda: (_ for _ in ()).throw(ConnectionError("down")))
    assert exc.value.attempts == 3
    assert isinstance(exc.value.last_error, ConnectionError)


def test_deadline_expires_and_requires_remaining():
    clock_value = [100.0]
    clock = lambda: clock_value[0]
    deadline = Deadline.after(5, clock=clock)
    assert deadline.remaining(clock=clock) == 5
    clock_value[0] = 105.0
    assert deadline.expired(clock=clock)
    with pytest.raises(TimeoutError):
        deadline.require_remaining(clock=clock)


def test_idempotency_executes_concurrent_request_once():
    store = IdempotencyStore()
    started = threading.Event()
    release = threading.Event()
    calls = []
    results = []

    def operation():
        calls.append(1)
        started.set()
        release.wait(2)
        return "same-result"

    def worker():
        results.append(store.execute("key-1", "fp-1", operation))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    assert started.wait(1)
    time.sleep(0.02)
    release.set()
    for thread in threads:
        thread.join(1)

    assert len(calls) == 1
    assert results == ["same-result"] * 8
    assert store.size() == 1


def test_idempotency_rejects_key_reuse_with_different_payload():
    store = IdempotencyStore()
    assert store.execute("k", "a", lambda: 10) == 10
    with pytest.raises(IdempotencyConflict):
        store.execute("k", "b", lambda: 20)


def test_idempotency_replays_failure_to_waiting_callers():
    store = IdempotencyStore()
    calls = []

    def failing():
        calls.append(1)
        raise TimeoutError("temporary failure")

    with pytest.raises(TimeoutError):
        store.execute("k", "a", failing)
    with pytest.raises(TimeoutError):
        store.execute("k", "a", failing)
    assert len(calls) == 1


def test_circuit_breaker_opens_and_recovers():
    clock_value = [0.0]
    clock = lambda: clock_value[0]
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=10, clock=clock)

    with pytest.raises(ConnectionError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectionError("down")))
    assert breaker.state == CircuitState.CLOSED
    with pytest.raises(ConnectionError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectionError("down")))
    assert breaker.state == CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        breaker.call(lambda: "must-not-run")

    clock_value[0] = 10.0
    assert breaker.state == CircuitState.HALF_OPEN
    assert breaker.call(lambda: "recovered") == "recovered"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


def test_circuit_breaker_half_open_allows_one_probe():
    clock_value = [0.0]
    breaker = CircuitBreaker(failure_threshold=1, recovery_seconds=5, clock=lambda: clock_value[0])
    with pytest.raises(ConnectionError):
        breaker.call(lambda: (_ for _ in ()).throw(ConnectionError("down")))
    clock_value[0] = 5
    entered = threading.Event()
    release = threading.Event()

    def probe():
        def op():
            entered.set()
            release.wait(1)
            return "ok"
        return breaker.call(op)

    t = threading.Thread(target=probe)
    t.start()
    assert entered.wait(1)
    with pytest.raises(CircuitOpenError):
        breaker.call(lambda: "second-probe")
    release.set()
    t.join(1)
    assert breaker.state == CircuitState.CLOSED


def test_concurrency_gate_enforces_limit_and_tracks_peak():
    gate = ConcurrencyGate(2)
    entered = threading.Event()
    worker_count = [0]
    worker_lock = threading.Lock()
    release = threading.Event()
    errors = []

    def worker():
        try:
            with gate:
                with worker_lock:
                    worker_count[0] += 1
                    if worker_count[0] == 2:
                        entered.set()
                release.wait(1)
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    assert entered.wait(1)
    assert gate.active == 2
    assert gate.peak == 2
    with pytest.raises(ConcurrencyLimitError):
        gate.acquire(timeout=0.01)
    release.set()
    for t in threads:
        t.join(1)
    assert not errors
    assert gate.active == 0


def test_throughput_limiter_uses_rolling_window():
    now = [100.0]
    limiter = ThroughputLimiter(SlidingWindow(2, 10), clock=lambda: now[0])
    assert limiter.allow()
    assert limiter.allow()
    assert not limiter.allow()
    now[0] = 110.1
    assert limiter.allow()


def test_retry_policy_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)
    with pytest.raises(ValueError):
        RetryPolicy(base_delay_seconds=2, max_delay_seconds=1)


def test_concurrency_gate_rejects_invalid_limit():
    with pytest.raises(ValueError):
        ConcurrencyGate(0)
