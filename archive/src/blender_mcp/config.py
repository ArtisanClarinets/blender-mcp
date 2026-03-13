"""Configuration helpers for Blender MCP."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    tomllib = None


@dataclass(frozen=True)
class TelemetryConfig:
    enabled: bool = False
    anonymous: bool = True
    tool_tracking: bool = True
    performance_tracking: bool = True
    supabase_url: str | None = None
    supabase_key: str | None = None



def _parse_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default



def _load_toml_config() -> dict[str, Any]:
    if tomllib is None:
        return {}

    config_path = os.getenv("BLENDER_MCP_CONFIG")
    candidates = [Path(config_path)] if config_path else []
    candidates.extend(
        [
            Path.cwd() / "studio_config.toml",
            Path.cwd() / "telemetry.toml",
        ]
    )

    for candidate in candidates:
        if candidate and candidate.exists():
            with candidate.open("rb") as handle:
                return tomllib.load(handle)
    return {}



def load_telemetry_config() -> TelemetryConfig:
    config = _load_toml_config().get("telemetry", {})
    return TelemetryConfig(
        enabled=_parse_bool(
            os.getenv("BLENDER_MCP_TELEMETRY_ENABLED"),
            _parse_bool(config.get("enabled"), False),
        ),
        anonymous=_parse_bool(
            os.getenv("BLENDER_MCP_TELEMETRY_ANONYMOUS"),
            _parse_bool(config.get("anonymous"), True),
        ),
        tool_tracking=_parse_bool(
            os.getenv("BLENDER_MCP_TELEMETRY_TOOL_TRACKING"),
            _parse_bool(config.get("tool_tracking"), True),
        ),
        performance_tracking=_parse_bool(
            os.getenv("BLENDER_MCP_TELEMETRY_PERFORMANCE_TRACKING"),
            _parse_bool(config.get("performance_tracking"), True),
        ),
        supabase_url=os.getenv("SUPABASE_URL") or config.get("supabase_url"),
        supabase_key=os.getenv("SUPABASE_KEY") or config.get("supabase_key"),
    )


telemetry_config = load_telemetry_config()
