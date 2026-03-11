"""
Privacy-focused, anonymous telemetry for Blender MCP
Tracks tool usage, DAU/MAU, and performance metrics
"""

import contextlib
import json
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
from pathlib import Path
from typing import Any

# Load configuration
from .config import telemetry_config


# Check if Supabase is available
if telemetry_config.enabled:
    try:
        from supabase import create_client, Client

        HAS_SUPABASE = True
    except ImportError:
        HAS_SUPABASE = False
else:
    HAS_SUPABASE = False


try:
    import tomli
except ImportError:
    try:
        import tomllib as tomli
    except ImportError:
        tomli = None


class TelemetryStatus(Enum):
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
    metadata: dict


class TelemetryCollector:
    """Collects and processes telemetry events."""

    def __init__(self):
        self.events = queue.Queue()
        self.threads = []
        self.running = False
        self.logger = logging.getLogger("BlenderMCPTelemetry")

    def start(self):
        """Start the telemetry collector."""
        if not telemetry_config.enabled:
            self.logger.info("Telemetry disabled by configuration")
            return

        self.running = True
        collector_thread = threading.Thread(target=self._collect_loop, daemon=True)
        collector_thread.start()
        self.threads.append(collector_thread)

        self.logger.info("Telemetry collector started")

    def stop(self):
        """Stop the telemetry collector."""
        self.running = False
        for thread in self.threads:
            thread.join()
        self.threads = []

        self.logger.info("Telemetry collector stopped")

    def record_event(self, event: TelemetryEvent):
        """Record a telemetry event."""
        if not telemetry_config.enabled:
            return

        self.events.put(event)

        # Log to console for debugging
        self.logger.debug(
            f"Telemetry: {event.tool_name} - {event.status.value} in {event.duration:.2f}s"
        )

    def _collect_loop(self):
        """Main loop for collecting and processing events."""
        while self.running:
            try:
                event = self.events.get(timeout=1.0)
                if event:
                    self._process_event(event)
            except queue.Empty:
                continue

    def _process_event(self, event: TelemetryEvent):
        """Process a single telemetry event."""
        if not HAS_SUPABASE:
            self.logger.debug("Supabase not available, skipping telemetry")
            return

        try:
            client = create_client(
                telemetry_config.supabase_url or os.getenv("SUPABASE_URL"),
                telemetry_config.supabase_key or os.getenv("SUPABASE_KEY"),
            )

            # Prepare data
            data = {
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

            # Insert into database
            client.table("telemetry_events").insert([data]).execute()

            self.logger.debug(f"Telemetry event recorded: {event.tool_name}")

        except Exception as e:
            self.logger.error(f"Failed to record telemetry event: {e}")


# Global collector instance
collector = TelemetryCollector()
collector.start()


def record_startup():
    """Record startup event."""
    if not telemetry_config.enabled:
        return

    event = TelemetryEvent(
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

    collector.record_event(event)


def record_tool_usage(
    tool_name: str,
    status: TelemetryStatus,
    duration: float,
    request_id: str,
    metadata: dict = None,
):
    """Record tool usage event."""
    if not telemetry_config.enabled:
        return

    event = TelemetryEvent(
        tool_name=tool_name,
        status=status,
        duration=duration,
        timestamp=time.time(),
        user_id=str(uuid.uuid4()),
        session_id=str(uuid.uuid4()),
        request_id=request_id,
        metadata=metadata or {},
    )

    collector.record_event(event)


def get_telemetry():
    """Get telemetry status."""
    return {
        "enabled": telemetry_config.enabled,
        "anonymous": telemetry_config.anonymous,
        "tool_tracking": telemetry_config.tool_tracking,
        "performance_tracking": telemetry_config.performance_tracking,
        "supabase_available": HAS_SUPABASE,
    }
