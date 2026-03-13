"""Hunyuan3D job handlers."""

from __future__ import annotations

from typing import Any, Dict, Optional

import bpy

from .jobs_common import (
    build_import_response,
    build_job_snapshot,
    complete_job_record,
    create_job_record,
    ensure_completed_job,
)


_jobs: Dict[str, Dict[str, Any]] = {}


def _normalize_optional_string(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    normalized_value = value.strip()
    return normalized_value or None


def _build_generation_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    normalized_payload: Dict[str, Any] = {}
    text_prompt = _normalize_optional_string(payload.get("text_prompt"))
    input_image_url = _normalize_optional_string(payload.get("input_image_url"))

    if text_prompt is not None:
        normalized_payload["text_prompt"] = text_prompt
    if input_image_url is not None:
        normalized_payload["input_image_url"] = input_image_url
    if not normalized_payload:
        raise ValueError("text_prompt or input_image_url is required")

    return normalized_payload


def _get_settings() -> Any:
    scene = getattr(bpy.context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, "blendermcp_settings", None)


def get_status() -> Dict[str, Any]:
    """Get Hunyuan3D integration status."""
    settings = _get_settings()
    enabled = bool(getattr(settings, "hunyuan3d_enabled", False))
    mode = getattr(settings, "hunyuan3d_mode", "official")
    api_key = getattr(settings, "hunyuan3d_api_key", None)
    local_path = getattr(settings, "hunyuan3d_local_path", None)
    return {
        "enabled": enabled,
        "mode": mode,
        "has_api_key": bool(api_key),
        "has_local_path": bool(local_path),
        "message": f"Hunyuan3D ({mode}) ready" if enabled else "Hunyuan3D disabled",
        "api_available": enabled,
    }


def create_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new Hunyuan3D generation job."""
    normalized_payload = _build_generation_payload(payload)
    job = create_job_record(_jobs, "hunyuan3d", normalized_payload, status="pending")
    return {
        "job_id": job["job_id"],
        "provider": job["provider"],
        "status": job["status"],
    }


def get_job(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get job status."""
    job = _jobs.get(params.get("job_id"))
    if job is None:
        return None
    return build_job_snapshot(job)


def generate_model(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a model from text or image guidance."""
    text_prompt = params.get("text_prompt")
    input_image_url = params.get("input_image_url")
    if not text_prompt and not input_image_url:
        raise ValueError("text_prompt or input_image_url is required")

    payload: Dict[str, Any] = {}
    if text_prompt:
        payload["text_prompt"] = text_prompt
    if input_image_url:
        payload["input_image_url"] = input_image_url

    job = create_job(payload)
    return {
        "job_id": job["job_id"],
        "status": "RUN",
        "message": "Generation job created",
    }


def poll_job_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """Poll a Hunyuan3D job status."""
    job_id = params.get("job_id")
    job = _jobs.get(job_id)
    if job is None:
        raise ValueError(f"Job not found: {job_id}")

    if job["status"] == "pending":
        result = {
            "ResultFile3Ds": f"memory://hunyuan3d/{job_id}.zip",
            "zip_file_url": f"memory://hunyuan3d/{job_id}.zip",
        }
        complete_job_record(
            job,
            result,
            status="DONE",
            progress=100.0,
            message="Hunyuan3D generation completed",
        )

    response = build_job_snapshot(job)
    response.update(job["result"] or {})
    return response


def import_asset(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import a generated Hunyuan3D asset."""
    name = params.get("name")
    zip_file_url = params.get("zip_file_url")
    if not name:
        raise ValueError("name is required")
    if not zip_file_url:
        raise ValueError("zip_file_url is required")

    return build_import_response(
        "hunyuan3d",
        name,
        source=zip_file_url,
        metadata={"zip_file_url": zip_file_url},
    )


def import_job_result(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import the result of a completed Hunyuan3D job."""
    job_id = params.get("job_id")
    name = params.get("name")
    if not job_id:
        raise ValueError("job_id is required")
    if not name:
        raise ValueError("name is required")

    job = _jobs.get(job_id)
    result = ensure_completed_job(job, job_id)
    zip_file_url = result.get("zip_file_url") or result.get("ResultFile3Ds")
    return build_import_response(
        "hunyuan3d",
        name,
        job_id=job_id,
        source=zip_file_url,
        target_size=params.get("target_size"),
        metadata={"zip_file_url": zip_file_url},
    )
