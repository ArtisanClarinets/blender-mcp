"""Hyper3D job handlers."""

from __future__ import annotations

from typing import Any, Dict, Optional

import bpy

from .jobs_common import (
    build_import_response,
    build_job_snapshot,
    complete_job_record,
    create_job_record,
    ensure_completed_job,
    update_job_record,
)


_jobs: Dict[str, Dict[str, Any]] = {}


def _normalize_text_prompt(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    text_prompt = value.strip()
    return text_prompt or None


def _normalize_image_inputs(value: Any, field_name: str) -> Optional[list[Any]]:
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field_name} must be a non-empty list")
    return value


def _build_generation_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    normalized_payload: Dict[str, Any] = {}
    text_prompt = _normalize_text_prompt(payload.get("text_prompt"))
    input_image_paths = _normalize_image_inputs(
        payload.get("input_image_paths"), "input_image_paths"
    )
    input_image_urls = _normalize_image_inputs(
        payload.get("input_image_urls"), "input_image_urls"
    )

    if text_prompt is not None:
        normalized_payload["text_prompt"] = text_prompt
    if input_image_paths is not None:
        normalized_payload["input_image_paths"] = input_image_paths
    if input_image_urls is not None:
        normalized_payload["input_image_urls"] = input_image_urls
    if not normalized_payload:
        raise ValueError(
            "text_prompt, input_image_paths, or input_image_urls is required"
        )

    for optional_field in ("bbox_condition", "request_id", "subscription_key"):
        if payload.get(optional_field) is not None:
            normalized_payload[optional_field] = payload[optional_field]

    return normalized_payload


def _get_settings() -> Any:
    scene = getattr(bpy.context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, "blendermcp_settings", None)


def get_status() -> Dict[str, Any]:
    """Get Hyper3D integration status."""
    settings = _get_settings()
    enabled = bool(getattr(settings, "hyper3d_enabled", False))
    api_key = getattr(settings, "hyper3d_api_key", None)
    mode = getattr(settings, "hyper3d_mode", "main_site")
    return {
        "enabled": enabled,
        "has_api_key": bool(api_key),
        "mode": mode,
        "message": f"Hyper3D ({mode}) ready" if enabled else "Hyper3D disabled",
        "api_available": enabled,
        "modes": ["MAIN_SITE", "FAL_AI"],
    }


def _get_job_by_identifier(identifier: Optional[str]) -> Optional[Dict[str, Any]]:
    if not identifier:
        return None

    direct_match = _jobs.get(identifier)
    if direct_match is not None:
        return direct_match

    for job in _jobs.values():
        if job.get("external_id") == identifier:
            return job
    return None


def create_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new Hyper3D generation job."""
    normalized_payload = _build_generation_payload(payload)
    job = create_job_record(_jobs, "hyper3d", normalized_payload, status="pending")
    external_id = (
        normalized_payload.get("request_id")
        or normalized_payload.get("subscription_key")
        or job["job_id"]
    )
    update_job_record(job, external_id=external_id)
    return {
        "job_id": job["job_id"],
        "provider": job["provider"],
        "status": job["status"],
        "request_id": external_id,
    }


def get_job(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get job status."""
    job = _jobs.get(params.get("job_id"))
    if job is None:
        return None
    return build_job_snapshot(job)


def generate_via_text(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a model from text."""
    text_prompt = params.get("text_prompt")
    if not text_prompt:
        raise ValueError("text_prompt is required")

    payload = {"text_prompt": text_prompt}
    if params.get("bbox_condition") is not None:
        payload["bbox_condition"] = params["bbox_condition"]

    job = create_job(payload)
    return {
        "job_id": job["job_id"],
        "request_id": job["request_id"],
        "status": "IN_QUEUE",
        "message": "Text generation job created",
    }


def generate_via_images(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a model from image references."""
    input_image_paths = params.get("input_image_paths")
    input_image_urls = params.get("input_image_urls")
    if not input_image_paths and not input_image_urls:
        raise ValueError("input_image_paths or input_image_urls is required")

    payload: Dict[str, Any] = {}
    if input_image_paths:
        payload["input_image_paths"] = input_image_paths
    if input_image_urls:
        payload["input_image_urls"] = input_image_urls
    if params.get("bbox_condition") is not None:
        payload["bbox_condition"] = params["bbox_condition"]

    job = create_job(payload)
    return {
        "job_id": job["job_id"],
        "request_id": job["request_id"],
        "status": "IN_QUEUE",
        "message": "Image generation job created",
    }


def poll_job_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """Poll a Hyper3D job status."""
    identifier = params.get("request_id") or params.get("subscription_key")
    job = _get_job_by_identifier(identifier)
    if job is None:
        raise ValueError(
            "request_id or subscription_key must reference an existing job"
        )

    if job["status"] == "pending":
        result = {
            "request_id": job["external_id"],
            "task_uuid": job["job_id"],
            "model_url": f"memory://hyper3d/{job['job_id']}.glb",
        }
        complete_job_record(
            job,
            result,
            status="COMPLETED",
            progress=100.0,
            message="Hyper3D generation completed",
        )

    response = build_job_snapshot(job)
    response.update(job["result"] or {})
    return response


def import_asset(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import a generated Hyper3D asset."""
    name = params.get("name")
    if not name:
        raise ValueError("name is required")

    identifier = params.get("request_id") or params.get("task_uuid")
    job = _get_job_by_identifier(identifier)
    source = None
    metadata: Dict[str, Any] = {}
    if job is not None and job.get("result"):
        source = job["result"].get("model_url")
        metadata = {"request_id": job.get("external_id"), "task_uuid": job["job_id"]}
    elif identifier:
        source = f"memory://hyper3d/{identifier}.glb"
        metadata = {
            "request_id": params.get("request_id"),
            "task_uuid": params.get("task_uuid"),
        }

    return build_import_response(
        "hyper3d",
        name,
        job_id=job.get("job_id") if job else None,
        source=source,
        metadata={**metadata, "model_url": source} if source is not None else metadata,
    )


def import_job_result(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import the result of a completed Hyper3D job."""
    job_id = params.get("job_id")
    name = params.get("name")
    if not job_id:
        raise ValueError("job_id is required")
    if not name:
        raise ValueError("name is required")

    job = _jobs.get(job_id)
    result = ensure_completed_job(job, job_id)
    return build_import_response(
        "hyper3d",
        name,
        job_id=job_id,
        source=result.get("model_url"),
        target_size=params.get("target_size"),
        metadata={
            "model_url": result.get("model_url"),
            "request_id": result.get("request_id"),
            "task_uuid": result.get("task_uuid"),
        },
    )
