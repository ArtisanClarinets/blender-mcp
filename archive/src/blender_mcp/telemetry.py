"""Privacy-focused, anonymous telemetry for Blender MCP."""

from __future__ import annotations

import logging
import os
import platform
import queue
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any

from . import __version__
from .config import telemetry_config

if telemetry_config.enabled:
    try:  # pragma: no cover - optional dependency path
        from supabase import Client, create_client

        HAS_SUPABASE = True
    except Exception:  # pragma: no cover
        HAS_SUPABASE = False
else:
    HAS_SUPABASE = False


class TelemetryStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"


@dataclass
class TelemetryEvent:
    tool_name: str
    status: TelemetryStatus
    duration: float
    timestamp: float
    user_id: str
    session_id: str
    request_id: str
    metadata: dict[str, Any]


class TelemetryCollector:
    """Collects and processes telemetry events."""

    def __init__(self) -> None:
        self.events: queue.Queue[TelemetryEvent] = queue.Queue()
        self.threads: list[threading.Thread] = []
        self.running = False
        self.logger = logging.getLogger("BlenderMCPTelemetry")

    def start(self) -> None:
        if not telemetry_config.enabled or self.running:
            return
        self.running = True
        collector_thread = threading.Thread(target=self._collect_loop, daemon=True)
        collector_thread.start()
        self.threads.append(collector_thread)
        self.logger.info("Telemetry collector started")

    def stop(self) -> None:
        self.running = False
        for thread in self.threads:
            thread.join(timeout=1.0)
        self.threads = []
        self.logger.info("Telemetry collector stopped")

    def record_event(self, event: TelemetryEvent) -> None:
        if not telemetry_config.enabled:
            return
        self.events.put(event)
        self.logger.debug(
            "Telemetry event queued",
            extra={
                "tool_name": event.tool_name,
                "status": event.status.value,
                "duration": event.duration,
            },
        )

    def _collect_loop(self) -> None:
        while self.running:
            try:
                event = self.events.get(timeout=1.0)
            except queue.Empty:
                continue
            try:
                self._process_event(event)
            except Exception as exc:  # pragma: no cover
                self.logger.debug("Telemetry processing failed: %s", exc)

    def _process_event(self, event: TelemetryEvent) -> None:
        if not HAS_SUPABASE:
            return
        client: Client = create_client(
            telemetry_config.supabase_url or os.getenv("SUPABASE_URL", ""),
            telemetry_config.supabase_key or os.getenv("SUPABASE_KEY", ""),
        )
        payload = {
            "tool_name": event.tool_name,
            "status": event.status.value,
            "duration": event.duration,
            "timestamp": event.timestamp,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "request_id": event.request_id,
            "metadata": event.metadata,
            "platform": platform.system(),
            "python_version": sys.version.split()[0],
            "anonymous": telemetry_config.anonymous,
            "tool_tracking": telemetry_config.tool_tracking,
            "performance_tracking": telemetry_config.performance_tracking,
        }
        client.table("telemetry_events").insert([payload]).execute()


collector = TelemetryCollector()
collector.start()


def record_startup() -> None:
    if not telemetry_config.enabled:
        return
    collector.record_event(
        TelemetryEvent(
            tool_name="startup",
            status=TelemetryStatus.SUCCESS,
            duration=0.0,
            timestamp=time.time(),
            user_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            request_id="",
            metadata={
                "version": __version__,
                "platform": platform.system(),
                "python_version": sys.version.split()[0],
            },
        )
    )



def _coerce_status(status: TelemetryStatus | bool | str | None) -> TelemetryStatus:
    if isinstance(status, TelemetryStatus):
        return status
    if isinstance(status, bool):
        return TelemetryStatus.SUCCESS if status else TelemetryStatus.FAILURE
    if isinstance(status, str):
        text = status.strip().lower()
        for item in TelemetryStatus:
            if item.value == text:
                return item
    return TelemetryStatus.SKIPPED



def record_tool_usage(
    tool_name: str,
    status: TelemetryStatus | bool | str,
    duration: float,
    request_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    if not telemetry_config.enabled:
        return
    collector.record_event(
        TelemetryEvent(
            tool_name=tool_name,
            status=_coerce_status(status),
            duration=duration,
            timestamp=time.time(),
            user_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4()),
            request_id=request_id,
            metadata=metadata or {},
        )
    )



def get_telemetry() -> dict[str, Any]:
    return {
        "enabled": telemetry_config.enabled,
        "anonymous": telemetry_config.anonymous,
        "tool_tracking": telemetry_config.tool_tracking,
        "performance_tracking": telemetry_config.performance_tracking,
        "supabase_available": HAS_SUPABASE,
    }
