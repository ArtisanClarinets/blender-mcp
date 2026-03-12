import json
import logging

import structlog

from blender_mcp.logging_config import LogContext, get_logger


def test_get_logger_returns_structlog_logger():
    logger = get_logger("test.logger")

    assert isinstance(logger, structlog.stdlib.BoundLogger)


def test_log_context_binds_structured_fields(caplog):
    logger = get_logger("test.logger")

    with caplog.at_level(logging.INFO):
        with LogContext(logger, request_id="req-123", tool="ping") as contextual_logger:
            contextual_logger.info("hello", attempt=1)

    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["event"] == "hello"
    assert payload["request_id"] == "req-123"
    assert payload["tool"] == "ping"
    assert payload["attempt"] == 1
