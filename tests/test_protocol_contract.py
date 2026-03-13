"""Contract tests for addon response envelope shape."""

import importlib.util
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ADDON_PROTOCOL_PATH = PROJECT_ROOT / "blender_mcp_addon" / "protocol.py"


def _get_addon_protocol():
    """Load addon protocol module without importing bpy (addon __init__.py)."""
    if not ADDON_PROTOCOL_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        "addon_protocol", ADDON_PROTOCOL_PATH
    )
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "response",
    [
        ("success", lambda p: p.create_success_response({"k": "v"}, request_id="rid-1")),
        ("error", lambda p: p.create_error_response("code", "msg", request_id="rid-2")),
        ("response_ok_true", lambda p: p.create_response(ok=True, data=1, request_id="r")),
        ("response_ok_false", lambda p: p.create_response(ok=False, error={"code": "e", "message": "m"}, request_id="r")),
    ],
)
def test_addon_response_has_ok_and_request_id(response):
    """Addon responses must include 'ok' and 'request_id' for client correlation."""
    protocol = _get_addon_protocol()
    if protocol is None:
        pytest.skip("blender_mcp_addon not importable")

    _, build = response
    resp = build(protocol)
    assert "ok" in resp
    assert "request_id" in resp
    assert isinstance(resp["ok"], bool)
    if resp["ok"]:
        assert "data" in resp or "error" not in resp or resp.get("error") is None
    else:
        assert "error" in resp
        assert "message" in resp["error"]
