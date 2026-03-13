"""Tripo3D job handlers."""

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


def _get_settings() -> Any:
    scene = getattr(bpy.context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, "blendermcp_settings", None)


def get_status() -> Dict[str, Any]:
    """Get Tripo3D integration status."""
    settings = _get_settings()
    enabled = bool(getattr(settings, "tripo3d_enabled", False))
    api_key = getattr(settings, "tripo3d_api_key", None)
    return {
        "enabled": enabled,
        "has_api_key": bool(api_key),
        "message": "Tripo3D ready" if enabled else "Tripo3D disabled",
    }


def create_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new Tripo3D generation job."""
    if not payload.get("text_prompt") and not payload.get("image_url"):
        raise ValueError("text_prompt or image_url is required")

    job = create_job_record(_jobs, "tripo3d", payload, status="pending")
    return {
        "job_id": job["job_id"],
        "provider": job["provider"],
        "status": job["status"],
        "task_id": job["job_id"],
    }


def get_job(params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get job status."""
    job = _jobs.get(params.get("job_id"))
    if job is None:
        return None
    return build_job_snapshot(job)


def generate_model(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a Tripo3D model from text or image input."""
    job = create_job(
        {
            "text_prompt": params.get("text_prompt"),
            "image_url": params.get("image_url"),
        }
    )
    return {
        "job_id": job["job_id"],
        "task_id": job["task_id"],
        "status": "PENDING",
        "message": "Generation task created",
    }


def poll_job_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """Poll a Tripo3D generation task."""
    task_id = params.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")

    job = _jobs.get(task_id)
    if job is None:
        raise ValueError(f"Job not found: {task_id}")

    if job["status"] == "pending":
        result = {"model_url": f"memory://tripo3d/{task_id}.glb", "task_id": task_id}
        complete_job_record(
            job,
            result,
            status="completed",
            progress=100.0,
            message="Tripo3D generation completed",
        )

    response = build_job_snapshot(job)
    response.update(job["result"] or {})
    return response


def import_model(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import a generated Tripo3D model."""
    model_url = params.get("model_url")
    name = params.get("name") or "Tripo3D_Model"
    if not model_url:
        raise ValueError("model_url is required")

    return build_import_response(
        "tripo3d",
        name,
        source=model_url,
        metadata={"model_url": model_url},
    )


def import_job_result(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import the result of a completed Tripo3D job."""
    job_id = params.get("job_id")
    name = params.get("name")
    if not job_id:
        raise ValueError("job_id is required")
    if not name:
        raise ValueError("name is required")

    job = _jobs.get(job_id)
    result = ensure_completed_job(job, job_id)
    return build_import_response(
        "tripo3d",
        name,
        job_id=job_id,
        source=result.get("model_url"),
        target_size=params.get("target_size"),
        metadata={
            "model_url": result.get("model_url"),
            "task_id": result.get("task_id"),
        },
    )
