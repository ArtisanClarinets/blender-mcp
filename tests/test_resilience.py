import pytest

from blender_mcp.resilience import (
    CircuitBreaker,
    CircuitBreakerOpen,
    CircuitState,
    build_retry,
)


def test_circuit_breaker_starts_closed():
    breaker = CircuitBreaker()

    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request() is True


def test_circuit_breaker_opens_after_threshold():
    breaker = CircuitBreaker(
        failure_threshold=2,
        expected_exceptions=(ValueError,),
    )

    @breaker
    def fail() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        fail()
    with pytest.raises(ValueError):
        fail()

    assert breaker.state == CircuitState.OPEN
    with pytest.raises(CircuitBreakerOpen):
        fail()


def test_circuit_breaker_half_open_then_closes_on_success():
    current_time = 0.0

    def fake_time() -> float:
        return current_time

    breaker = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=5.0,
        expected_exceptions=(ValueError,),
        time_fn=fake_time,
    )

    @breaker
    def fail_once() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        fail_once()

    assert breaker.state == CircuitState.OPEN
    current_time = 5.1
    assert breaker.allow_request() is True
    assert breaker.state == CircuitState.HALF_OPEN

    @breaker
    def succeed() -> str:
        return "ok"

    assert succeed() == "ok"
    assert breaker.state == CircuitState.CLOSED


def test_build_retry_retries_until_success():
    calls = {"count": 0}

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise ConnectionError("temporary")
        return "ok"

    retrying = build_retry(
        attempts=3,
        min_wait=0.0,
        max_wait=0.0,
        retry_exceptions=(ConnectionError,),
    )

    assert retrying(flaky) == "ok"
    assert calls["count"] == 3
