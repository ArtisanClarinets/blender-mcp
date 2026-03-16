"""
MCP Resources implementation for Blender MCP.

Provides resource definitions and reads for:
- Repo metadata
- Tool registry metadata
- Command registry metadata
- Protocol metadata
- Current scene state
- Pipeline project metadata
- And more...
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Callable
from urllib.parse import unquote

from .mcp_compat import FastMCP
from .tool_registry import discover_tool_specs
from .logging_config import get_logger

logger = get_logger("BlenderMCP.Resources")

# Resource URI schemes
RESOURCE_SCHEMES = {
    "repo": "Repository files and metadata",
    "scene": "Blender scene state",
    "pipeline": "Pipeline entities (projects, sequences, shots, assets)",
    "publish": "Publish lineage and manifests",
    "ocio": "Color pipeline configuration",
    "usd": "USD package metadata",
    "catalog": "Tool and command catalogs",
}

# Type alias for resource handlers
ResourceHandler = Callable[[str], Dict[str, Any]]


class ResourceRegistry:
    """Registry for MCP resources."""
    
    def __init__(self, mcp_server: FastMCP):
        self.mcp = mcp_server
        self._handlers: Dict[str, ResourceHandler] = {}
        self._templates: Dict[str, str] = {}  # uri_pattern -> description
    
    def register_handler(self, uri_prefix: str, handler: ResourceHandler) -> None:
        """Register a handler for a URI prefix."""
        self._handlers[uri_prefix] = handler
    
    def register_template(self, uri_pattern: str, description: str) -> None:
        """Register a resource template."""
        self._templates[uri_pattern] = description
    
    def get_handler(self, uri: str) -> Optional[ResourceHandler]:
        """Get the handler for a URI."""
        for prefix, handler in self._handlers.items():
            if uri.startswith(prefix):
                return handler
        return None
    
    def list_resources(self) -> List[Dict[str, str]]:
        """List all static resources."""
        resources = []
        
        # Add catalog resources
        resources.extend([
            {"uri": "catalog://tools", "name": "Tool Catalog", "mimeType": "application/json"},
            {"uri": "catalog://commands", "name": "Command Catalog", "mimeType": "application/json"},
            {"uri": "catalog://schemas", "name": "Schema Catalog", "mimeType": "application/json"},
            {"uri": "catalog://protocol", "name": "Protocol Capabilities", "mimeType": "application/json"},
            {"uri": "catalog://pipeline", "name": "Pipeline Capabilities", "mimeType": "application/json"},
        ])
        
        # Add scene resources
        resources.extend([
            {"uri": "scene://current", "name": "Current Scene", "mimeType": "application/json"},
            {"uri": "scene://selection", "name": "Selected Objects", "mimeType": "application/json"},
        ])
        
        # Add pipeline resources
        resources.extend([
            {"uri": "pipeline://projects", "name": "Pipeline Projects", "mimeType": "application/json"},
            {"uri": "pipeline://status", "name": "Pipeline Status", "mimeType": "application/json"},
        ])
        
        # Add publish resources
        resources.extend([
            {"uri": "publish://status", "name": "Publish System Status", "mimeType": "application/json"},
        ])
        
        # Add color resources
        resources.extend([
            {"uri": "ocio://status", "name": "Color Pipeline Status", "mimeType": "application/json"},
        ])
        
        # Add USD resources
        resources.extend([
            {"uri": "usd://status", "name": "USD System Status", "mimeType": "application/json"},
        ])
        
        return resources
    
    def list_templates(self) -> List[Dict[str, str]]:
        """List all resource templates."""
        return [
            {"uriTemplate": "repo://tree/{path}", "name": "Repository Tree", "mimeType": "application/json"},
            {"uriTemplate": "repo://file/{path}", "name": "Repository File", "mimeType": "text/plain"},
            {"uriTemplate": "scene://object/{object_name}", "name": "Scene Object", "mimeType": "application/json"},
            {"uriTemplate": "pipeline://project/{project_code}", "name": "Project Details", "mimeType": "application/json"},
            {"uriTemplate": "pipeline://sequence/{sequence_code}", "name": "Sequence Details", "mimeType": "application/json"},
            {"uriTemplate": "pipeline://shot/{shot_name}", "name": "Shot Details", "mimeType": "application/json"},
            {"uriTemplate": "pipeline://asset/{asset_type}/{asset_name}", "name": "Asset Details", "mimeType": "application/json"},
            {"uriTemplate": "publish://entity/{entity_type}/{entity_id}", "name": "Entity Publishes", "mimeType": "application/json"},
            {"uriTemplate": "publish://manifest/{publish_id}", "name": "Publish Manifest", "mimeType": "application/json"},
            {"uriTemplate": "ocio://project/{project_code}", "name": "Project Color Config", "mimeType": "application/json"},
            {"uriTemplate": "usd://package/{package_id}", "name": "USD Package", "mimeType": "application/json"},
        ]
    
    async def read_resource(self, uri: str) -> str:
        """Read a resource by URI."""
        handler = self.get_handler(uri)
        if handler:
            try:
                result = handler(uri)
                return json.dumps(result, indent=2, default=str)
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return json.dumps({"error": str(e)})
        
        # Handle static resources
        if uri == "catalog://tools":
            return json.dumps(_get_tool_catalog(), indent=2)
        elif uri == "catalog://commands":
            return json.dumps(_get_command_catalog(), indent=2)
        elif uri == "catalog://schemas":
            return json.dumps(_get_schema_catalog(), indent=2)
        elif uri == "catalog://protocol":
            return json.dumps(_get_protocol_capabilities(), indent=2)
        elif uri == "catalog://pipeline":
            return json.dumps(_get_pipeline_capabilities(), indent=2)
        elif uri == "scene://current":
            return json.dumps(await _get_scene_resource(), indent=2, default=str)
        elif uri == "scene://selection":
            return json.dumps(await _get_selection_resource(), indent=2, default=str)
        elif uri == "pipeline://projects":
            return json.dumps(_get_projects_resource(), indent=2, default=str)
        elif uri == "pipeline://status":
            return json.dumps(_get_pipeline_status(), indent=2)
        elif uri == "publish://status":
            return json.dumps(_get_publish_status(), indent=2)
        elif uri == "ocio://status":
            return json.dumps(_get_ocio_status(), indent=2)
        elif uri == "usd://status":
            return json.dumps(_get_usd_status(), indent=2)
        
        # Handle template resources
        if uri.startswith("repo://"):
            return json.dumps(_handle_repo_uri(uri), indent=2)
        elif uri.startswith("scene://object/"):
            return json.dumps(await _handle_scene_object_uri(uri), indent=2, default=str)
        elif uri.startswith("pipeline://"):
            return json.dumps(_handle_pipeline_uri(uri), indent=2, default=str)
        elif uri.startswith("publish://"):
            return json.dumps(_handle_publish_uri(uri), indent=2, default=str)
        elif uri.startswith("ocio://"):
            return json.dumps(_handle_ocio_uri(uri), indent=2)
        elif uri.startswith("usd://"):
            return json.dumps(_handle_usd_uri(uri), indent=2, default=str)
        
        return json.dumps({"error": f"Unknown resource URI: {uri}"})


# Resource data functions

def _get_tool_catalog() -> Dict[str, Any]:
    """Get the tool catalog."""
    specs = discover_tool_specs()
    return {
        "tools": [
            {
                "name": name,
                "description": spec.description,
                "command_name": spec.command_name,
                "module": spec.module,
                "parameters": [
                    {"name": p.name, "required": p.required, "type": p.annotation}
                    for p in spec.parameters
                ],
            }
            for name, spec in specs.items()
        ],
        "count": len(specs),
    }


def _get_command_catalog() -> Dict[str, Any]:
    """Get the command catalog."""
    try:
        from blender_mcp_addon.command_registry import COMMAND_HANDLERS
        return {
            "commands": [
                {"name": name, "available": callable(handler)}
                for name, handler in COMMAND_HANDLERS.items()
            ],
            "count": len(COMMAND_HANDLERS),
        }
    except ImportError:
        return {"commands": [], "count": 0, "error": "Addon not available"}


def _get_schema_catalog() -> Dict[str, Any]:
    """Get the schema catalog."""
    from .schemas import COMMAND_SCHEMAS
    return {
        "schemas": [
            {"command": name, "has_schema": schema is not None}
            for name, schema in COMMAND_SCHEMAS.items()
        ],
        "count": len(COMMAND_SCHEMAS),
    }


def _get_protocol_capabilities() -> Dict[str, Any]:
    """Get protocol capabilities."""
    return {
        "protocol_version": "2024-11-05",
        "features": {
            "tools": True,
            "prompts": True,
            "resources": True,
            "completions": True,
            "logging": True,
        },
        "transport": "stdio",
        "server_info": {
            "name": "BlenderMCP",
            "version": "1.5.5",
        },
    }


def _get_pipeline_capabilities() -> Dict[str, Any]:
    """Get pipeline capabilities."""
    from .pipeline import get_pipeline_storage
    from .pipeline.usd import get_usd_adapter
    from .pipeline.color import get_color_adapter
    from .pipeline.tracker import get_tracker_adapter
    
    storage = get_pipeline_storage()
    usd_adapter = get_usd_adapter()
    color_adapter = get_color_adapter()
    tracker_adapter = get_tracker_adapter()
    
    return {
        "pipeline_storage": {
            "available": True,
            "root_path": str(storage.root),
        },
        "usd": {
            "available": True,
            "usd_library_available": usd_adapter.usd_available,
        },
        "color": {
            "available": True,
            "ocio_library_available": color_adapter.ocio_available,
        },
        "tracker": {
            "available": True,
            "current_adapter": tracker_adapter.name,
            "connected": tracker_adapter.is_connected(),
        },
    }


async def _get_scene_resource() -> Dict[str, Any]:
    """Get the current scene resource."""
    try:
        from .core.connection import get_blender_connection
        blender = get_blender_connection()
        result = blender.send_command("get_scene_info", {})
        return {
            "available": True,
            "data": result,
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


async def _get_selection_resource() -> Dict[str, Any]:
    """Get the current selection resource."""
    try:
        from .core.connection import get_blender_connection
        blender = get_blender_connection()
        result = blender.send_command("get_selection", {})
        return {
            "available": True,
            "data": result,
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


def _get_projects_resource() -> Dict[str, Any]:
    """Get the projects resource."""
    try:
        from .pipeline import get_pipeline_storage
        storage = get_pipeline_storage()
        projects = storage.list_projects()
        return {
            "available": True,
            "projects": [
                {"code": p.code, "name": p.name, "status": p.status.value}
                for p in projects
            ],
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


def _get_pipeline_status() -> Dict[str, Any]:
    """Get pipeline status."""
    try:
        from .pipeline import get_pipeline_storage
        storage = get_pipeline_storage()
        return {
            "available": True,
            "storage_root": str(storage.root),
            "project_count": len(storage.list_projects()),
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


def _get_publish_status() -> Dict[str, Any]:
    """Get publish system status."""
    try:
        from .pipeline import get_pipeline_storage
        storage = get_pipeline_storage()
        return {
            "available": True,
            "publish_count": len(storage.list_publishes()),
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


def _get_ocio_status() -> Dict[str, Any]:
    """Get OCIO system status."""
    try:
        from .pipeline.color import get_color_adapter
        adapter = get_color_adapter()
        return {
            "available": True,
            "ocio_library_available": adapter.ocio_available,
            "supported_colorspaces": adapter.get_available_colorspaces()[:10],  # Limit for brevity
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


def _get_usd_status() -> Dict[str, Any]:
    """Get USD system status."""
    try:
        from .pipeline.usd import get_usd_adapter
        adapter = get_usd_adapter()
        return {
            "available": True,
            "usd_library_available": adapter.usd_available,
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }


# Template URI handlers

def _handle_repo_uri(uri: str) -> Dict[str, Any]:
    """Handle repo:// URIs."""
    parts = uri.replace("repo://", "").split("/", 1)
    if not parts or not parts[0]:
        return {"error": "Invalid repo URI"}
    
    action = parts[0]
    path = unquote(parts[1]) if len(parts) > 1 else "."
    
    # Security: ensure path stays within repo
    repo_root = Path(__file__).resolve().parents[2]
    target_path = (repo_root / path).resolve()
    
    if not str(target_path).startswith(str(repo_root)):
        return {"error": "Path traversal detected"}
    
    if action == "tree":
        if target_path.is_dir():
            return {
                "path": path,
                "type": "directory",
                "entries": [
                    {"name": e.name, "type": "directory" if e.is_dir() else "file"}
                    for e in target_path.iterdir()
                    if not e.name.startswith(".") and not e.name.startswith("__")
                ],
            }
        else:
            return {"error": "Not a directory", "path": path}
    
    elif action == "file":
        if target_path.is_file():
            try:
                content = target_path.read_text(encoding="utf-8", errors="replace")
                return {
                    "path": path,
                    "type": "file",
                    "size": target_path.stat().st_size,
                    "content": content[:10000],  # Limit content size
                    "truncated": target_path.stat().st_size > 10000,
                }
            except Exception as e:
                return {"error": str(e), "path": path}
        else:
            return {"error": "Not a file", "path": path}
    
    return {"error": f"Unknown repo action: {action}"}


async def _handle_scene_object_uri(uri: str) -> Dict[str, Any]:
    """Handle scene://object/ URIs."""
    object_name = unquote(uri.replace("scene://object/", ""))
    
    try:
        from .core.connection import get_blender_connection
        blender = get_blender_connection()
        result = blender.send_command("get_object_info", {"object_name": object_name})
        return {
            "object_name": object_name,
            "data": result,
        }
    except Exception as e:
        return {
            "error": str(e),
            "object_name": object_name,
        }


def _handle_pipeline_uri(uri: str) -> Dict[str, Any]:
    """Handle pipeline:// URIs."""
    from .pipeline import get_pipeline_storage
    storage = get_pipeline_storage()
    
    path = uri.replace("pipeline://", "")
    parts = path.split("/")
    
    if len(parts) < 2:
        return {"error": "Invalid pipeline URI"}
    
    entity_type = parts[0]
    entity_id = unquote(parts[1])
    
    if entity_type == "project":
        project = storage.get_project(entity_id)
        if project:
            return project.model_dump()
        return {"error": f"Project not found: {entity_id}"}
    
    elif entity_type == "sequence":
        # Need project context - assume from all projects
        for project in storage.list_projects():
            seq = storage.get_sequence(project.code, entity_id)
            if seq:
                return seq.model_dump()
        return {"error": f"Sequence not found: {entity_id}"}
    
    elif entity_type == "shot":
        for project in storage.list_projects():
            shot = storage.get_shot(project.code, entity_id)
            if shot:
                return shot.model_dump()
        return {"error": f"Shot not found: {entity_id}"}
    
    elif entity_type == "asset":
        if len(parts) < 3:
            return {"error": "Asset URI requires asset_type and asset_name"}
        asset_type = entity_id
        asset_name = unquote(parts[2])
        for project in storage.list_projects():
            asset = storage.get_asset(project.code, asset_type, asset_name)
            if asset:
                return asset.model_dump()
        return {"error": f"Asset not found: {asset_type}/{asset_name}"}
    
    return {"error": f"Unknown entity type: {entity_type}"}


def _handle_publish_uri(uri: str) -> Dict[str, Any]:
    """Handle publish:// URIs."""
    from .pipeline import get_pipeline_storage
    storage = get_pipeline_storage()
    
    path = uri.replace("publish://", "")
    parts = path.split("/")
    
    if len(parts) < 2:
        return {"error": "Invalid publish URI"}
    
    action = parts[0]
    
    if action == "entity":
        if len(parts) < 3:
            return {"error": "Entity URI requires entity_type and entity_id"}
        entity_type = parts[1]
        entity_id = unquote(parts[2])
        publishes = storage.list_publishes(entity_type, entity_id)
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "publishes": [p.model_dump() for p in publishes],
        }
    
    elif action == "manifest":
        publish_id = unquote(parts[1])
        publish = storage.get_publish(publish_id)
        if publish:
            return publish.model_dump()
        return {"error": f"Publish not found: {publish_id}"}
    
    return {"error": f"Unknown publish action: {action}"}


def _handle_ocio_uri(uri: str) -> Dict[str, Any]:
    """Handle ocio:// URIs."""
    from .pipeline.color import get_color_adapter
    adapter = get_color_adapter()
    
    path = uri.replace("ocio://", "")
    parts = path.split("/")
    
    if len(parts) < 2:
        return {"error": "Invalid ocio URI"}
    
    action = parts[0]
    project_code = unquote(parts[1])
    
    if action == "project":
        config = adapter.get_color_pipeline(project_code)
        return config.model_dump()
    
    return {"error": f"Unknown ocio action: {action}"}


def _handle_usd_uri(uri: str) -> Dict[str, Any]:
    """Handle usd:// URIs."""
    from .pipeline import get_pipeline_storage
    storage = get_pipeline_storage()
    
    path = uri.replace("usd://", "")
    parts = path.split("/")
    
    if len(parts) < 2:
        return {"error": "Invalid usd URI"}
    
    action = parts[0]
    package_id = unquote(parts[1])
    
    if action == "package":
        package = storage.get_usd_package(package_id)
        if package:
            return package.model_dump()
        return {"error": f"USD package not found: {package_id}"}
    
    return {"error": f"Unknown usd action: {action}"}


# Global registry instance
_resource_registry: Optional[ResourceRegistry] = None


def get_resource_registry(mcp_server: Optional[FastMCP] = None) -> ResourceRegistry:
    """Get the global resource registry."""
    global _resource_registry
    if _resource_registry is None:
        if mcp_server is None:
            raise ValueError("MCP server required for initial registry creation")
        _resource_registry = ResourceRegistry(mcp_server)
    return _resource_registry
