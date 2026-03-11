"""
Protocol definitions for Blender MCP

Defines the command and response envelopes used for communication between
Python server and Blender addon.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CommandEnvelope:
    """Envelope for commands sent from Python server to Blender addon."""

    type: str
    params: Dict[str, Any]
    request_id: str
    idempotency_key: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


@dataclass
class ResponseEnvelope:
    """Envelope for responses from Blender addon to Python server."""

    ok: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    request_id: str
    meta: Optional[Dict[str, Any]] = None


@dataclass
class SceneInfo:
    """Structured scene information."""

    objects: List[Dict[str, Any]]
    collections: List[Dict[str, Any]]
    cameras: List[Dict[str, Any]]
    lights: List[Dict[str, Any]]
    world: Dict[str, Any]
    render_settings: Dict[str, Any]
    scene_hash: str


@dataclass
class ObjectInfo:
    """Detailed information about a single object."""

    id: str
    name: str
    type: str
    location: List[float]
    rotation: List[float]
    scale: List[float]
    dimensions: List[float]
    materials: List[Dict[str, Any]]
    modifiers: List[Dict[str, Any]]
    collections: List[str]


@dataclass
class Transform:
    """Transformation data."""

    location: List[float]
    rotation: List[float]
    scale: List[float]
    matrix: List[List[float]]


@dataclass
class MaterialSpec:
    """Material specification for PBR materials."""

    base_color: Optional[List[float]] = None
    base_color_texture: Optional[str] = None
    metallic: Optional[float] = None
    roughness: Optional[float] = None
    normal_map: Optional[str] = None
    emission: Optional[List[float]] = None


@dataclass
class ExportManifest:
    """Manifest for Next.js export."""

    version: str
    timestamp: str
    objects: List[Dict[str, Any]]
    cameras: List[Dict[str, Any]]
    lights: List[Dict[str, Any]]
    world: Dict[str, Any]
    render_settings: Dict[str, Any]
    dependencies: List[str]
    units: Dict[str, Any]
    scale: float
    scene_hash: str


@dataclass
class JobInfo:
    """Unified job information."""

    job_id: str
    provider: str
    status: str
    progress: float
    message: str
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float


@dataclass
class ViewportScreenshot:
    """Screenshot information."""

    path: str
    width: int
    height: int
    format: str


@dataclass
class GLBExportSettings:
    """Settings for GLB export."""

    target: str
    name: str
    output_dir: str
    draco_compression: bool
    texture_embed: bool
    y_up: bool
    apply_modifiers: bool
    export_materials: bool
    export_animations: bool
