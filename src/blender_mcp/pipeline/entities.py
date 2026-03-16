"""
Pipeline entity models for Blender MCP Studio

Defines the core domain entities for production pipeline management.
All entities are Pydantic models for validation and serialization.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field, field_validator


class EntityStatus(str, Enum):
    """Status values for pipeline entities."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"


class PublishStage(str, Enum):
    """Pipeline stages for publishes."""
    LAYOUT = "layout"
    ANIMATION = "animation"
    LIGHTING = "lighting"
    RENDER = "render"
    COMP = "comp"
    FINAL = "final"


class AssetType(str, Enum):
    """Types of assets in the pipeline."""
    CHARACTER = "character"
    PROP = "prop"
    ENVIRONMENT = "environment"
    VEHICLE = "vehicle"
    CREATURE = "creature"
    FX = "fx"
    CAMERA = "camera"
    LIGHTING = "lighting"
    MATERIAL = "material"


class Project(BaseModel):
    """A production project."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(..., min_length=1, max_length=32, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    name: str = Field(..., min_length=1)
    description: str = ""
    status: EntityStatus = EntityStatus.ACTIVE
    
    # Color pipeline
    ocio_config_path: Optional[str] = None
    working_colorspace: str = "ACES - ACEScg"
    render_colorspace: str = "ACES - ACEScg"
    display_colorspace: str = "ACES - sRGB"
    
    # Paths
    root_path: Optional[str] = Field(default=None, description="Absolute path to project root")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "unknown"
    
    # Tracker integration
    tracker_adapter: Optional[str] = None
    tracker_project_id: Optional[str] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Sequence(BaseModel):
    """A sequence of shots within a project."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(..., min_length=1, max_length=32, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    name: str = Field(..., min_length=1)
    description: str = ""
    status: EntityStatus = EntityStatus.ACTIVE
    
    # Project reference
    project_code: str = Field(..., min_length=1)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Tracker
    tracker_sequence_id: Optional[str] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Shot(BaseModel):
    """A shot within a sequence."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    shot_number: int = Field(..., gt=0)
    description: str = ""
    status: EntityStatus = EntityStatus.ACTIVE
    
    # Hierarchy
    project_code: str = Field(..., min_length=1)
    sequence_code: str = Field(..., min_length=1)
    
    # Timing
    frame_start: int = Field(default=1001, ge=1)
    frame_end: int = Field(default=1100, ge=1)
    frame_rate: float = Field(default=24.0, gt=0)
    
    # Assets
    required_assets: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Tracker
    tracker_shot_id: Optional[str] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class AssetVariant(BaseModel):
    """A variant of an asset (e.g., LOD, damage state)."""
    
    name: str = Field(..., min_length=1)
    description: str = ""
    lod_level: Optional[int] = None
    is_default: bool = False


class Asset(BaseModel):
    """An asset in the pipeline."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    asset_type: AssetType
    description: str = ""
    status: EntityStatus = EntityStatus.ACTIVE
    
    # Hierarchy
    project_code: str = Field(..., min_length=1)
    
    # Variants
    variants: List[AssetVariant] = Field(default_factory=list)
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list)  # Asset IDs
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Tracker
    tracker_asset_id: Optional[str] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class Workfile(BaseModel):
    """A workfile/session for an entity."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["shot", "asset"]
    entity_id: str = Field(..., min_length=1)
    
    # File info
    file_path: str = Field(..., min_length=1)
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    
    # Version
    version_number: int = Field(default=1, ge=1)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "unknown"
    
    # Scene state (if captured)
    scene_hash: Optional[str] = None
    blender_version: Optional[str] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ValidationResult(BaseModel):
    """Validation result for a publish."""
    
    passed: bool
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class PublishArtifact(BaseModel):
    """An artifact produced by a publish."""
    
    name: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    artifact_type: str = Field(..., min_length=1)  # e.g., "usd", "alembic", "fbx", "preview"
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Publish(BaseModel):
    """A published version of an entity."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    publish_id: str = Field(..., min_length=1, description="Unique publish identifier")
    
    # Entity reference
    entity_type: Literal["shot", "asset"]
    entity_id: str = Field(..., min_length=1)
    
    # Version info
    version: int = Field(..., ge=1)
    stage: PublishStage
    status: EntityStatus = EntityStatus.PENDING
    
    # Source
    source_workfile_id: Optional[str] = None
    source_file_path: Optional[str] = None
    source_scene_hash: Optional[str] = None
    blender_version: Optional[str] = None
    
    # Content
    description: str = ""
    artifacts: List[PublishArtifact] = Field(default_factory=list)
    previews: List[PublishArtifact] = Field(default_factory=list)
    
    # Validation
    validation: Optional[ValidationResult] = None
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list)  # Publish IDs
    
    # Lineage
    parent_publish_id: Optional[str] = None
    child_publish_ids: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "unknown"
    
    # Tracker sync
    tracker_sync_state: Optional[TrackerSyncState] = None
    
    # USD metadata
    usd_package_id: Optional[str] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ReviewVersion(BaseModel):
    """A reviewable version of a shot or asset."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["shot", "asset"]
    entity_id: str = Field(..., min_length=1)
    publish_id: Optional[str] = None
    
    # Version info
    version_number: int = Field(..., ge=1)
    stage: PublishStage
    
    # Review data
    review_type: str = "visual"  # visual, technical, director
    status: EntityStatus = EntityStatus.PENDING
    notes: str = ""
    reviewer: Optional[str] = None
    
    # Media
    preview_paths: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ColorPipelineConfig(BaseModel):
    """Color pipeline configuration for a project."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_code: str = Field(..., min_length=1)
    
    # OCIO config
    ocio_config_path: Optional[str] = None
    ocio_config_name: Optional[str] = None
    ocio_config_version: Optional[str] = None
    
    # Colorspaces
    working_colorspace: str = "ACES - ACEScg"
    render_colorspace: str = "ACES - ACEScg"
    display_colorspace: str = "ACES - sRGB"
    texture_colorspace: str = "Utility - sRGB - Texture"
    
    # Display/View
    default_display: str = "ACES"
    default_view: str = "sRGB"
    
    # Output policy
    exr_compression: str = "zip16"
    exr_datatype: str = "half"
    
    # Validation
    strict_validation: bool = False
    allowed_input_colorspaces: List[str] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class USDLayerInfo(BaseModel):
    """Information about a USD layer."""
    
    name: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    layer_type: Literal["subLayer", "reference", "payload"]
    prim_path: Optional[str] = None
    variant_set: Optional[str] = None
    variant_selection: Optional[str] = None


class USDVariantInfo(BaseModel):
    """Information about a USD variant."""
    
    name: str = Field(..., min_length=1)
    selections: List[str] = Field(default_factory=list)
    default_selection: Optional[str] = None


class USDPackage(BaseModel):
    """A USD package for an asset or shot."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_id: str = Field(..., min_length=1)
    
    # Entity reference
    entity_type: Literal["asset", "shot"]
    entity_id: str = Field(..., min_length=1)
    publish_id: Optional[str] = None
    
    # USD structure
    root_layer_path: str = Field(..., min_length=1)
    layers: List[USDLayerInfo] = Field(default_factory=list)
    variants: List[USDVariantInfo] = Field(default_factory=list)
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list)  # Package IDs
    
    # Metadata
    usd_version: str = "0.23.11"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TrackerSyncState(BaseModel):
    """Sync state for tracker integration."""
    
    entity_type: str = Field(..., min_length=1)
    local_id: str = Field(..., min_length=1)
    tracker_id: Optional[str] = None
    tracker_adapter: str = "local"
    
    # Sync status
    last_sync_at: Optional[datetime] = None
    sync_status: Literal["synced", "pending", "failed", "not_synced"] = "not_synced"
    last_error: Optional[str] = None
    
    # Version tracking
    local_version: int = 1
    tracker_version: Optional[int] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


def generate_publish_id(entity_type: str, entity_id: str, version: int) -> str:
    """Generate a unique publish ID (safe for filesystem)."""
    base = f"{entity_type}_{entity_id}_v{version:03d}"
    hash_suffix = hashlib.md5(base.encode()).hexdigest()[:8]
    return f"{base}_{hash_suffix}"


def generate_package_id(entity_type: str, entity_id: str, version: int) -> str:
    """Generate a unique USD package ID (safe for filesystem)."""
    base = f"usd_{entity_type}_{entity_id}_v{version:03d}"
    hash_suffix = hashlib.md5(base.encode()).hexdigest()[:8]
    return f"{base}_{hash_suffix}"
