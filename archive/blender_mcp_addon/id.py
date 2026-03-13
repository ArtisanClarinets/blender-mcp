"""
ID utilities for Blender MCP Addon

Provides stable ID assignment and resolution for Blender objects.
"""

import bpy
import uuid
from typing import Optional


MCP_UUID_KEY = "mcp_uuid"


def assign_uuid(obj: bpy.types.ID) -> str:
    """
    Assign a stable UUID to a Blender object.

    Args:
        obj: Blender ID object

    Returns:
        The assigned UUID
    """
    if MCP_UUID_KEY not in obj:
        obj[MCP_UUID_KEY] = str(uuid.uuid4())
    return obj[MCP_UUID_KEY]


def get_uuid(obj: bpy.types.ID) -> Optional[str]:
    """
    Get the UUID of an object if assigned.

    Args:
        obj: Blender ID object

    Returns:
        UUID string or None
    """
    return obj.get(MCP_UUID_KEY)


def resolve_id(id_or_name: str) -> Optional[bpy.types.Object]:
    """
    Resolve an ID or name to a Blender object.

    First tries to find by UUID, then by name.

    Args:
        id_or_name: Object ID (UUID) or name

    Returns:
        Blender object or None
    """
    # Try to find by UUID first
    for obj in bpy.data.objects:
        if get_uuid(obj) == id_or_name:
            return obj

    # Try to find by name
    if id_or_name in bpy.data.objects:
        return bpy.data.objects[id_or_name]

    return None


def resolve_multiple_ids(ids_or_names: list) -> list:
    """
    Resolve multiple IDs or names to Blender objects.

    Args:
        ids_or_names: List of object IDs or names

    Returns:
        List of resolved Blender objects
    """
    result = []
    for id_or_name in ids_or_names:
        obj = resolve_id(id_or_name)
        if obj:
            result.append(obj)
    return result


def get_object_info_with_uuid(obj: bpy.types.Object) -> dict:
    """
    Get object info including UUID.

    Args:
        obj: Blender object

    Returns:
        Dictionary with object info
    """
    uuid = assign_uuid(obj)

    return {
        "id": uuid,
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation": list(obj.rotation_euler),
        "scale": list(obj.scale),
        "dimensions": list(obj.dimensions),
        "visible": obj.visible_get(),
        "selected": obj.select_get(),
    }
