#!/usr/bin/env python3
"""
Blender MCP Client Tool for Agent Integration

This module provides an MCP client interface that agents can use to interact
with Blender through the Model Context Protocol.
"""

import socket
import json
import logging
import uuid
from typing import Any, Dict, Optional
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BlenderMCPClient")

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 9876


@dataclass
class BlenderMCPClient:
    """Client for communicating with Blender MCP server"""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    _sock: Optional[socket.socket] = None

    def connect(self) -> bool:
        """Establish connection to Blender MCP server"""
        if self._sock:
            return True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.connect((self.host, self.port))
            logger.info(f"Connected to Blender MCP at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Blender MCP: {e}")
            return False

    def disconnect(self):
        """Close connection to Blender MCP server"""
        if self._sock:
            try:
                self._sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
            finally:
                self._sock = None

    def send_command(
        self,
        command_type: str,
        params: Dict[str, Any] = None,
        request_id: str = None,
        idempotency_key: str = None,
    ) -> Dict[str, Any]:
        """Send a command to Blender MCP and receive response using newline-delimited JSON"""
        if not self._sock and not self.connect():
            raise ConnectionError("Not connected to Blender MCP")

        # Generate request ID if not provided
        if not request_id:
            request_id = str(uuid.uuid4())

        command = {
            "type": command_type,
            "params": params or {},
            "request_id": request_id,
        }

        if idempotency_key:
            command["idempotency_key"] = idempotency_key

        try:
            logger.info(f"Sending command: {command_type} (request_id: {request_id})")

            # Send with newline delimiter
            message = json.dumps(command) + "\n"
            self._sock.sendall(message.encode("utf-8"))

            self._sock.settimeout(180.0)

            # Read response until newline
            buffer = b""
            while True:
                chunk = self._sock.recv(8192)
                if not chunk:
                    break
                buffer += chunk

                # Check for complete message
                if b"\n" in buffer:
                    line, _ = buffer.split(b"\n", 1)
                    try:
                        response = json.loads(line.decode("utf-8"))
                        return response
                    except json.JSONDecodeError:
                        continue

            raise Exception("No valid response received")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self._sock = None
            raise


# Tool definitions for agent integration
TOOLS = {
    # Observation tools
    "observe_scene": {
        "description": "Observe the current scene state with configurable detail level",
        "parameters": {
            "detail": {
                "type": "string",
                "description": "Level of detail (low, med, high)",
                "default": "med",
            },
            "include_screenshot": {
                "type": "boolean",
                "description": "Whether to capture screenshot",
                "default": False,
            },
            "max_screenshot_size": {
                "type": "integer",
                "description": "Max screenshot dimension",
                "default": 800,
            },
        },
    },
    "get_scene_hash": {
        "description": "Get a stable hash of the current scene state",
        "parameters": {},
    },
    "get_scene_info": {
        "description": "Get detailed information about the current Blender scene",
        "parameters": {},
    },
    "get_object_info": {
        "description": "Get detailed information about a specific object",
        "parameters": {
            "object_name": {"type": "string", "description": "Name or ID of the object"}
        },
    },
    "get_viewport_screenshot": {
        "description": "Capture a screenshot of the current Blender 3D viewport",
        "parameters": {
            "max_size": {
                "type": "integer",
                "description": "Max dimension in pixels",
                "default": 800,
            }
        },
    },
    "get_selection": {
        "description": "Get information about currently selected objects",
        "parameters": {},
    },
    # Scene operations
    "create_primitive": {
        "description": "Create a primitive object (cube, sphere, cylinder, cone, torus, plane)",
        "parameters": {
            "type": {"type": "string", "description": "Primitive type"},
            "name": {"type": "string", "description": "Optional name"},
            "size": {"type": "number", "description": "Optional size"},
            "location": {"type": "array", "description": "Optional [x, y, z] location"},
            "rotation": {"type": "array", "description": "Optional [x, y, z] rotation"},
            "scale": {"type": "array", "description": "Optional [x, y, z] scale"},
        },
    },
    "create_empty": {
        "description": "Create an empty object",
        "parameters": {
            "name": {"type": "string", "description": "Optional name"},
            "location": {"type": "array", "description": "Optional [x, y, z] location"},
        },
    },
    "create_camera": {
        "description": "Create a camera",
        "parameters": {
            "name": {"type": "string", "description": "Optional name"},
            "lens": {"type": "number", "description": "Optional focal length in mm"},
            "location": {"type": "array", "description": "Optional [x, y, z] location"},
            "look_at": {
                "type": "array",
                "description": "Optional [x, y, z] point to look at",
            },
        },
    },
    "create_light": {
        "description": "Create a light (point, sun, spot, area)",
        "parameters": {
            "type": {"type": "string", "description": "Light type"},
            "energy": {"type": "number", "description": "Light energy/strength"},
            "color": {"type": "array", "description": "Optional [r, g, b] color"},
            "location": {"type": "array", "description": "Optional [x, y, z] location"},
            "rotation": {"type": "array", "description": "Optional [x, y, z] rotation"},
        },
    },
    "set_transform": {
        "description": "Set object transform",
        "parameters": {
            "target_id": {"type": "string", "description": "Object name or ID"},
            "location": {"type": "array", "description": "Optional [x, y, z] location"},
            "rotation": {"type": "array", "description": "Optional [x, y, z] rotation"},
            "scale": {"type": "array", "description": "Optional [x, y, z] scale"},
            "apply": {
                "type": "boolean",
                "description": "Whether to apply transform",
                "default": False,
            },
        },
    },
    "select_objects": {
        "description": "Select objects in the scene",
        "parameters": {
            "ids": {"type": "array", "description": "List of object names or IDs"},
            "mode": {
                "type": "string",
                "description": "Selection mode (set, add, remove)",
                "default": "set",
            },
        },
    },
    "delete_objects": {
        "description": "Delete objects from the scene",
        "parameters": {
            "ids": {"type": "array", "description": "List of object names or IDs"}
        },
    },
    "duplicate_object": {
        "description": "Duplicate an object",
        "parameters": {
            "id": {"type": "string", "description": "Object name or ID"},
            "linked": {
                "type": "boolean",
                "description": "Create linked duplicates",
                "default": False,
            },
            "count": {
                "type": "integer",
                "description": "Number of duplicates",
                "default": 1,
            },
        },
    },
    "assign_material_pbr": {
        "description": "Assign PBR material to an object",
        "parameters": {
            "target_id": {"type": "string", "description": "Object name or ID"},
            "material_spec": {
                "type": "object",
                "description": "Material specification",
            },
        },
    },
    "set_world_hdri": {
        "description": "Set world HDRI environment",
        "parameters": {
            "asset_id": {"type": "string", "description": "PolyHaven HDRI asset ID"},
            "resolution": {
                "type": "string",
                "description": "Resolution (1k, 2k, 4k, 8k)",
                "default": "2k",
            },
        },
    },
    "execute_blender_code": {
        "description": "Execute arbitrary Python code in Blender (use with caution)",
        "parameters": {
            "code": {"type": "string", "description": "Python code to execute"}
        },
    },
    # Export tools
    "export_glb": {
        "description": "Export scene or selection to GLB format",
        "parameters": {
            "target": {
                "type": "string",
                "description": "What to export (scene, selection, collection)",
                "default": "scene",
            },
            "name": {
                "type": "string",
                "description": "Name for exported file",
                "default": "export",
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory",
                "default": "exports",
            },
            "draco": {
                "type": "boolean",
                "description": "Use Draco compression",
                "default": True,
            },
            "texture_embed": {
                "type": "boolean",
                "description": "Embed textures",
                "default": True,
            },
            "y_up": {
                "type": "boolean",
                "description": "Use Y-up coordinate system",
                "default": True,
            },
        },
    },
    "render_preview": {
        "description": "Render a preview image",
        "parameters": {
            "output_path": {"type": "string", "description": "Path to save image"},
            "camera": {"type": "string", "description": "Optional camera name"},
            "resolution": {
                "type": "array",
                "description": "[width, height] in pixels",
                "default": [512, 512],
            },
        },
    },
    "export_scene_bundle": {
        "description": "Export complete scene bundle for Next.js 16",
        "parameters": {
            "slug": {"type": "string", "description": "Unique identifier"},
            "nextjs_project_root": {
                "type": "string",
                "description": "Path to Next.js project",
            },
            "mode": {
                "type": "string",
                "description": "Export mode (scene, assets)",
                "default": "scene",
            },
            "generate_r3f": {
                "type": "boolean",
                "description": "Generate R3F components",
                "default": False,
            },
        },
    },
    # Job management
    "create_job": {
        "description": "Create async AI generation job",
        "parameters": {
            "provider": {
                "type": "string",
                "description": "Provider (hyper3d, hunyuan3d)",
            },
            "payload": {"type": "object", "description": "Job-specific payload"},
        },
    },
    "get_job": {
        "description": "Get job status",
        "parameters": {"job_id": {"type": "string", "description": "Job ID"}},
    },
    "import_job_result": {
        "description": "Import completed job result",
        "parameters": {
            "job_id": {"type": "string", "description": "Job ID"},
            "name": {"type": "string", "description": "Object name"},
            "target_size": {"type": "number", "description": "Optional target size"},
        },
    },
    # PolyHaven Integration
    "get_polyhaven_status": {
        "description": "Check if PolyHaven integration is enabled",
        "parameters": {},
    },
    "get_polyhaven_categories": {
        "description": "Get PolyHaven asset categories",
        "parameters": {
            "asset_type": {
                "type": "string",
                "description": "hdris/textures/models/all",
                "default": "hdris",
            }
        },
    },
    "search_polyhaven_assets": {
        "description": "Search PolyHaven for assets",
        "parameters": {
            "asset_type": {"type": "string", "description": "Type of assets"},
            "categories": {
                "type": "string",
                "description": "Comma-separated categories",
            },
        },
    },
    "download_polyhaven_asset": {
        "description": "Download and import a PolyHaven asset",
        "parameters": {
            "asset_id": {"type": "string", "description": "Asset ID"},
            "asset_type": {"type": "string", "description": "hdris/textures/models"},
            "resolution": {
                "type": "string",
                "description": "1k/2k/4k",
                "default": "1k",
            },
            "file_format": {"type": "string", "description": "Optional format"},
        },
    },
    "set_texture": {
        "description": "Apply a texture to an object",
        "parameters": {
            "object_name": {"type": "string", "description": "Object name"},
            "texture_id": {"type": "string", "description": "Texture ID"},
        },
    },
    # Sketchfab Integration
    "get_sketchfab_status": {
        "description": "Check Sketchfab integration status",
        "parameters": {},
    },
    "search_sketchfab_models": {
        "description": "Search Sketchfab for models",
        "parameters": {
            "query": {"type": "string", "description": "Search query"},
            "categories": {
                "type": "string",
                "description": "Comma-separated categories",
            },
            "count": {"type": "integer", "description": "Max results", "default": 20},
            "downloadable": {
                "type": "boolean",
                "description": "Only downloadable",
                "default": True,
            },
        },
    },
    "get_sketchfab_model_preview": {
        "description": "Get preview thumbnail of a Sketchfab model",
        "parameters": {"uid": {"type": "string", "description": "Model UID"}},
    },
    "download_sketchfab_model": {
        "description": "Download and import a Sketchfab model",
        "parameters": {
            "uid": {"type": "string", "description": "Model UID"},
            "target_size": {"type": "number", "description": "Target size in meters"},
        },
    },
    # Hyper3D Integration
    "get_hyper3d_status": {
        "description": "Check Hyper3D Rodin integration status",
        "parameters": {},
    },
    "generate_hyper3d_model_via_text": {
        "description": "Generate 3D model using Hyper3D from text",
        "parameters": {
            "text_prompt": {"type": "string", "description": "English description"},
            "bbox_condition": {
                "type": "array",
                "description": "Optional [L,W,H] ratio",
            },
        },
    },
    "generate_hyper3d_model_via_images": {
        "description": "Generate 3D model using Hyper3D from images",
        "parameters": {
            "input_image_paths": {
                "type": "array",
                "description": "Absolute paths to images",
            },
            "input_image_urls": {"type": "array", "description": "Image URLs"},
            "bbox_condition": {
                "type": "array",
                "description": "Optional [L,W,H] ratio",
            },
        },
    },
    "poll_rodin_job_status": {
        "description": "Check Hyper3D generation status",
        "parameters": {
            "subscription_key": {"type": "string", "description": "For MAIN_SITE mode"},
            "request_id": {"type": "string", "description": "For FAL_AI mode"},
        },
    },
    "import_generated_asset": {
        "description": "Import Hyper3D generated asset",
        "parameters": {
            "name": {"type": "string", "description": "Object name in scene"},
            "task_uuid": {"type": "string", "description": "For MAIN_SITE mode"},
            "request_id": {"type": "string", "description": "For FAL_AI mode"},
        },
    },
    # Hunyuan3D Integration
    "get_hunyuan3d_status": {
        "description": "Check Hunyuan3D integration status",
        "parameters": {},
    },
    "generate_hunyuan3d_model": {
        "description": "Generate 3D model using Hunyuan3D",
        "parameters": {
            "text_prompt": {
                "type": "string",
                "description": "Description in English/Chinese",
            },
            "input_image_url": {"type": "string", "description": "Optional image URL"},
        },
    },
    "poll_hunyuan_job_status": {
        "description": "Check Hunyuan3D job status",
        "parameters": {"job_id": {"type": "string", "description": "Job ID"}},
    },
    "import_generated_asset_hunyuan": {
        "description": "Import Hunyuan3D generated asset",
        "parameters": {
            "name": {"type": "string", "description": "Object name"},
            "zip_file_url": {"type": "string", "description": "ZIP file URL"},
        },
    },
}


def call_tool(
    tool_name: str,
    params: Dict[str, Any] = None,
    request_id: str = None,
    idempotency_key: str = None,
) -> str:
    """Call a Blender MCP tool and return the result"""
    client = BlenderMCPClient()
    try:
        if not client.connect():
            return "Error: Could not connect to Blender MCP server. Ensure Blender is running with the addon enabled."

        result = client.send_command(
            tool_name, params or {}, request_id, idempotency_key
        )

        # Handle new response envelope format
        if result.get("ok"):
            return json.dumps(result.get("data", {}), indent=2)
        else:
            error = result.get("error", {})
            return f"Error: {error.get('message', 'Unknown error')}"

    except Exception as e:
        return f"Error calling {tool_name}: {str(e)}"
    finally:
        client.disconnect()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: blender_mcp_client.py <tool_name> [params_json]")
        print("\nAvailable tools:")
        for tool_name, tool_info in TOOLS.items():
            print(f"  - {tool_name}: {tool_info['description']}")
        sys.exit(1)

    tool_name = sys.argv[1]
    params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    if tool_name not in TOOLS:
        print(f"Unknown tool: {tool_name}")
        print("\nAvailable tools:")
        for name, info in TOOLS.items():
            print(f"  - {name}: {info['description']}")
        sys.exit(1)

    result = call_tool(tool_name, params)
    print(result)
