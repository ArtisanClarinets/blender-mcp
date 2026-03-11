"""
Utility functions for Blender MCP Addon

Provides common utilities for file operations, JSON handling, etc.
"""

import os
import json
import tempfile
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional


def ensure_dir(path: str) -> str:
    """
    Ensure a directory exists.

    Args:
        path: Directory path

    Returns:
        The directory path
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def write_json(data: Dict[str, Any], path: str, indent: int = 2) -> str:
    """
    Write data to JSON file.

    Args:
        data: Data to write
        path: File path
        indent: JSON indentation

    Returns:
        The file path
    """
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    return path


def read_json(path: str) -> Optional[Dict[str, Any]]:
    """
    Read data from JSON file.

    Args:
        path: File path

    Returns:
        Data dictionary or None if file doesn't exist
    """
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_hash(data: Any) -> str:
    """
    Compute a stable hash of data.

    Args:
        data: Data to hash

    Returns:
        Hash string
    """
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()[:16]


def get_temp_dir() -> str:
    """Get a temporary directory for the addon."""
    temp_dir = os.path.join(tempfile.gettempdir(), "blender_mcp")
    ensure_dir(temp_dir)
    return temp_dir


def safe_filename(name: str) -> str:
    """
    Convert a name to a safe filename.

    Args:
        name: Original name

    Returns:
        Safe filename
    """
    # Remove or replace unsafe characters
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    return safe.strip("_")


def format_error(error: Exception) -> Dict[str, Any]:
    """
    Format an exception for response.

    Args:
        error: Exception to format

    Returns:
        Error dictionary
    """
    return {"type": type(error).__name__, "message": str(error)}


def get_scene_bounds() -> Dict[str, Any]:
    """
    Get the bounding box of the entire scene.

    Returns:
        Dictionary with min/max bounds
    """
    import bpy

    min_bound = [float("inf")] * 3
    max_bound = [float("-inf")] * 3

    for obj in bpy.data.objects:
        if obj.type == "MESH":
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ corner
                for i in range(3):
                    min_bound[i] = min(min_bound[i], world_corner[i])
                    max_bound[i] = max(max_bound[i], world_corner[i])

    # Handle empty scene
    if min_bound[0] == float("inf"):
        min_bound = [0, 0, 0]
        max_bound = [0, 0, 0]

    return {
        "min": min_bound,
        "max": max_bound,
        "center": [(min_bound[i] + max_bound[i]) / 2 for i in range(3)],
        "size": [max_bound[i] - min_bound[i] for i in range(3)],
    }
