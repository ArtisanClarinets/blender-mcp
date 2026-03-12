import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, TypeVar

from tenacity import (
    Retrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


logger = logging.getLogger("blender_mcp.resilience")

F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpen(RuntimeError):
    pass


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 5.0,
        expected_exceptions: tuple[type[BaseException], ...] = (Exception,),
        time_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self._time_fn = time_fn
        self.failure_count = 0
        self.opened_at: float | None = None
        self.state = CircuitState.CLOSED

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            if self.opened_at is None:
                return False
            if self._time_fn() - self.opened_at < self.recovery_timeout:
                return False
            self.state = CircuitState.HALF_OPEN
            logger.info("Circuit breaker entering half-open state")
            return True

        return True

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None
        self.state = CircuitState.CLOSED

    def record_failure(self, error: BaseException | None = None) -> None:
        self.failure_count += 1
        self.opened_at = self._time_fn()

        if (
            self.state == CircuitState.HALF_OPEN
            or self.failure_count >= self.failure_threshold
        ):
            self.state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker opened",
                extra={
                    "failures": self.failure_count,
                    "error": str(error) if error else None,
                },
            )

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if not self.allow_request():
            raise CircuitBreakerOpen("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
        except self.expected_exceptions as error:
            self.record_failure(error)
            raise

        self.record_success()
        return result

    def __call__(self, func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.call(func, *args, **kwargs)

        return wrapper  # type: ignore[return-value]


def build_retry(
    *,
    attempts: int = 2,
    min_wait: float = 0.1,
    max_wait: float = 0.5,
    retry_exceptions: tuple[type[BaseException], ...] = (ConnectionError, TimeoutError),
) -> Retrying:
    return Retrying(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=min_wait, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
