"""Shared helpers for async job handler modules.

These helpers keep provider-specific handlers small and consistent while
remaining adapter-friendly for mocked or deferred provider integrations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, MutableMapping, Optional
import uuid

import structlog

from ...exceptions import BlenderMCPError

logger = structlog.get_logger(__name__)

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
    external_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create and persist a normalized job record."""
    if not isinstance(payload, dict):
        raise BlenderMCPError("payload must be an object")

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
    logger.info("Created job record", job_id=job_id, provider=provider)
    return job

def update_job_record(job: Dict[str, Any], **fields: Any) -> Dict[str, Any]:
    """Update a job record and refresh its timestamp."""
    if not job:
        raise BlenderMCPError("job is required")

    job.update(fields)
    job["updated_at"] = utc_now_iso()
    logger.info("Updated job record", job_id=job.get("job_id"))
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
        raise BlenderMCPError("result must be an object")

    logger.info("Completing job record", job_id=job.get("job_id"))
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
        raise BlenderMCPError("job is required")
    return dict(job)

def ensure_completed_job(job: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """Validate that a job exists and completed successfully."""
    if not job:
        raise BlenderMCPError(f"Job not found: {job_id}")

    if job.get("status") not in {"completed", "COMPLETED", "DONE"}:
        raise BlenderMCPError(
            f"Job is not completed. Current status: {job.get('status', 'unknown')}"
        )

    result = job.get("result")
    if not isinstance(result, dict):
        raise BlenderMCPError(f"Job result unavailable: {job_id}")

    return result

def build_import_response(
    provider: str,
    name: str,
    *,
    job_id: Optional[str] = None,
    source: Optional[str] = None,
    target_size: Optional[float] = None,
    imported_objects: Optional[list[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
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

    logger.info("Built import response", name=name, provider=provider)
    return response