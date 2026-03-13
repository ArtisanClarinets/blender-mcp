"""Production tracking helpers for Blender MCP.

These handlers provide a lightweight, scene-local production context suitable
for solo creators and small teams. They do not replace ShotGrid/FTrack/AYON,
but they do introduce consistent shot/version/review state so MCP agents stop
operating on anonymous scene edits.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC
from typing import Any, Dict

import bpy

STORE_KEY = "blender_mcp_production_store"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()



def _load_store() -> dict[str, Any]:
    scene = bpy.context.scene
    raw = scene.get(STORE_KEY)
    if not raw:
        return {"shots": {}, "reviews": []}
    try:
        return json.loads(raw)
    except Exception:
        return {"shots": {}, "reviews": []}



def _save_store(store: dict[str, Any]) -> None:
    bpy.context.scene[STORE_KEY] = json.dumps(store)



def _require_shot(store: dict[str, Any], shot_name: str) -> dict[str, Any]:
    shot = store.get("shots", {}).get(shot_name)
    if not shot:
        raise ValueError(f"Shot not found: {shot_name}")
    return shot



def _ensure_camera(name: str):
    camera_obj = bpy.data.objects.get(name)
    if camera_obj and getattr(camera_obj, "type", None) == "CAMERA":
        return camera_obj
    camera_data = bpy.data.cameras.new(name)
    camera_obj = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera_obj)
    return camera_obj



def get_status() -> Dict[str, Any]:
    store = _load_store()
    return {
        "status": "ready",
        "shots": len(store.get("shots", {})),
        "sequences": len(_sequences_set(store)),
        "review_enabled": True,
        "versioning_enabled": True,
    }


def _sequences_set(store: dict[str, Any]) -> set[str]:
    shots = store.get("shots", {})
    return {s.get("sequence") for s in shots.values() if s.get("sequence")}


def list_sequences(params: Dict[str, Any]) -> Dict[str, Any]:
    store = _load_store()
    names = sorted(_sequences_set(store))
    return {"status": "success", "sequences": names}


def get_sequence(params: Dict[str, Any]) -> Dict[str, Any]:
    sequence_name = str(params.get("sequence_name") or "").strip()
    if not sequence_name:
        raise ValueError("sequence_name is required")
    store = _load_store()
    shots = store.get("shots", {})
    matching = [s for s in shots.values() if s.get("sequence") == sequence_name]
    matching.sort(key=lambda s: (s.get("shot_number", 0), s.get("shot_name", "")))
    return {"status": "success", "sequence": sequence_name, "shots": matching}


def list_shots(params: Dict[str, Any]) -> Dict[str, Any]:
    sequence_name = (params.get("sequence_name") or "").strip() or None
    store = _load_store()
    shots = list(store.get("shots", {}).values())
    if sequence_name:
        shots = [s for s in shots if s.get("sequence") == sequence_name]
    shots.sort(key=lambda s: (s.get("sequence", ""), s.get("shot_number", 0), s.get("shot_name", "")))
    return {"status": "success", "shots": shots}



def create_shot(params: Dict[str, Any]) -> Dict[str, Any]:
    shot_name = str(params.get("shot_name") or "").strip()
    sequence = str(params.get("sequence") or "").strip()
    shot_number = int(params.get("shot_number", 0))
    description = str(params.get("description") or "").strip()
    duration = float(params.get("duration", 0.0))
    assets = list(params.get("assets") or [])

    if not shot_name:
        raise ValueError("shot_name is required")
    if not sequence:
        raise ValueError("sequence is required")
    if shot_number <= 0:
        raise ValueError("shot_number must be greater than 0")

    store = _load_store()
    shots = store.setdefault("shots", {})
    if shot_name in shots:
        raise ValueError(f"Shot already exists: {shot_name}")

    frame_rate = bpy.context.scene.render.fps
    frame_count = max(int(round(duration * frame_rate)), 1) if duration else 1
    shot = {
        "id": f"shot_{uuid.uuid4().hex[:12]}",
        "shot_name": shot_name,
        "sequence": sequence,
        "shot_number": shot_number,
        "description": description,
        "duration": duration,
        "frame_rate": frame_rate,
        "frame_range": [1, frame_count],
        "assets": assets,
        "camera": None,
        "versions": [],
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }
    shots[shot_name] = shot
    _save_store(store)
    return {"status": "success", "shot": shot}



def setup_shot_camera(params: Dict[str, Any]) -> Dict[str, Any]:
    shot_name = str(params.get("shot_name") or "").strip()
    camera_type = str(params.get("camera_type") or "cinema")
    focal_length = float(params.get("focal_length", 35.0))
    aperture = float(params.get("aperture", 2.8))
    shot_type = str(params.get("shot_type") or "wide")

    store = _load_store()
    shot = _require_shot(store, shot_name)

    camera_name = f"{shot_name}_CAM"
    camera_obj = _ensure_camera(camera_name)
    camera_obj.location = {
        "wide": (0.0, -8.0, 4.0),
        "medium": (0.0, -5.0, 3.0),
        "closeup": (0.0, -2.0, 1.8),
        "extreme": (0.0, -1.0, 1.5),
    }.get(shot_type, (0.0, -6.0, 3.0))
    camera_obj.rotation_euler = (1.2, 0.0, 0.0)
    camera_obj.data.lens = focal_length
    if hasattr(camera_obj.data, "dof"):
        camera_obj.data.dof.aperture_fstop = max(aperture, 0.1)
    bpy.context.scene.camera = camera_obj

    shot["camera"] = {
        "name": camera_name,
        "camera_type": camera_type,
        "focal_length": focal_length,
        "aperture": aperture,
        "shot_type": shot_type,
    }
    shot["updated_at"] = _utc_now()
    _save_store(store)

    return {"status": "success", "shot_name": shot_name, "camera": shot["camera"]}



def create_shot_version(params: Dict[str, Any]) -> Dict[str, Any]:
    shot_name = str(params.get("shot_name") or "").strip()
    version_type = str(params.get("version_type") or "animation")
    notes = str(params.get("notes") or "").strip()
    artist = str(params.get("artist") or "").strip() or None

    store = _load_store()
    shot = _require_shot(store, shot_name)
    versions = shot.setdefault("versions", [])
    version_number = len(versions) + 1
    version = {
        "version": f"v{version_number:03d}",
        "type": version_type,
        "notes": notes,
        "artist": artist,
        "status": "pending_review",
        "created_at": _utc_now(),
    }
    versions.append(version)
    shot["updated_at"] = _utc_now()
    _save_store(store)
    return {"status": "success", "shot_name": shot_name, "version": version}



def review_shot(params: Dict[str, Any]) -> Dict[str, Any]:
    shot_name = str(params.get("shot_name") or "").strip()
    version_name = str(params.get("version") or "").strip()
    review_type = str(params.get("review_type") or "visual")
    notes = str(params.get("notes") or "").strip()
    approved = bool(params.get("approved", False))

    store = _load_store()
    shot = _require_shot(store, shot_name)
    version = next((item for item in shot.get("versions", []) if item.get("version") == version_name), None)
    if version is None:
        raise ValueError(f"Version not found for shot {shot_name}: {version_name}")

    review = {
        "shot_name": shot_name,
        "version": version_name,
        "review_type": review_type,
        "notes": notes,
        "approved": approved,
        "timestamp": _utc_now(),
    }
    version["status"] = "approved" if approved else "changes_requested"
    version["last_review"] = review
    store.setdefault("reviews", []).append(review)
    shot["updated_at"] = _utc_now()
    _save_store(store)
    return {"status": "success", "review": review}
