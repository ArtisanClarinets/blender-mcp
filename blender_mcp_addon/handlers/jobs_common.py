"""
Shared helpers for async job handler modules.

These helpers keep provider-specific handlers small and consistent while
remaining adapter-friendly for mocked or deferred provider integrations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, MutableMapping
import uuid


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def create_job_record(
    store: MutableMapping[str, Dict[str, Any]],
    provider: str,
    payload: Dict[str, Any],
    *,
    status: str = "pending",
    progress: float = 0.0,
    message: str = "Job created",
    external_id: str | None = None,
) -> Dict[str, Any]:
    """Create and persist a normalized job record."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    timestamp = utc_now_iso()
    job = {
        "job_id": job_id,
        "provider": provider,
        "status": status,
        "progress": float(progress),
        "message": message,
        "payload": payload,
        "result": None,
        "error": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    if external_id is not None:
        job["external_id"] = external_id

    store[job_id] = job
    return job


def update_job_record(job: Dict[str, Any], **fields: Any) -> Dict[str, Any]:
    """Update a job record and refresh its timestamp."""
    if not job:
        raise ValueError("job is required")

    job.update(fields)
    job["updated_at"] = utc_now_iso()
    return job


def complete_job_record(
    job: Dict[str, Any],
    result: Dict[str, Any],
    *,
    status: str = "completed",
    progress: float = 100.0,
    message: str = "Job completed",
) -> Dict[str, Any]:
    """Mark a job as completed with a result payload."""
    if not isinstance(result, dict):
        raise ValueError("result must be an object")

    return update_job_record(
        job,
        status=status,
        progress=float(progress),
        message=message,
        result=result,
        error=None,
    )


def build_job_snapshot(job: Dict[str, Any]) -> Dict[str, Any]:
    """Return a shallow copy suitable for responses."""
    if not job:
        raise ValueError("job is required")
    return dict(job)


def ensure_completed_job(job: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """Validate that a job exists and completed successfully."""
    if not job:
        raise ValueError(f"Job not found: {job_id}")

    if job.get("status") not in {"completed", "COMPLETED", "DONE"}:
        raise ValueError(
            f"Job is not completed. Current status: {job.get('status', 'unknown')}"
        )

    result = job.get("result")
    if not isinstance(result, dict):
        raise ValueError(f"Job result unavailable: {job_id}")

    return result


def build_import_response(
    provider: str,
    name: str,
    *,
    job_id: str | None = None,
    source: str | None = None,
    target_size: float | None = None,
    imported_objects: list[str] | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a normalized import response."""
    response: Dict[str, Any] = {
        "status": "success",
        "provider": provider,
        "name": name,
        "imported": True,
        "imported_objects": imported_objects or [name],
        "deferred_import": True,
    }
    if job_id is not None:
        response["job_id"] = job_id
    if source is not None:
        response["source"] = source
    if target_size is not None:
        response["target_size"] = float(target_size)
    if metadata:
        response.update(metadata)
    return response
