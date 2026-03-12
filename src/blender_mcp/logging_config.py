import logging
import os
import sys
from typing import Any

import structlog


_LOGGING_CONFIGURED = False


def configure_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    log_level = os.getenv("BLENDER_MCP_LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("BLENDER_MCP_LOG_FORMAT", "json").lower()

    renderer: structlog.types.Processor
    if log_format == "console":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=log_level, format="%(message)s", stream=sys.stderr)
    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    configure_logging()
    return structlog.get_logger(name).bind()


class LogContext:
    def __init__(
        self, logger: structlog.stdlib.BoundLogger | None = None, **context: Any
    ):
        self._logger = logger
        self._context = {
            key: value for key, value in context.items() if value is not None
        }

    def __enter__(self) -> structlog.stdlib.BoundLogger:
        logger = self._logger or get_logger("blender_mcp")
        return logger.bind(**self._context)

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
