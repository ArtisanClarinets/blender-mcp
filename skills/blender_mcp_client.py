#!/usr/bin/env python3
"""
Blender MCP Client Tool for Agent Integration

This module provides an MCP client interface that agents can use to interact
with Blender through the Model Context Protocol.
"""

import socket
import json
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Blender MCP and receive response"""
        if not self._sock and not self.connect():
            raise ConnectionError("Not connected to Blender MCP")

        command = {"type": command_type, "params": params or {}}

        try:
            logger.info(f"Sending command: {command_type}")
            self._sock.sendall(json.dumps(command).encode('utf-8'))

            self._sock.settimeout(180.0)

            chunks = []
            while True:
                try:
                    chunk = self._sock.recv(8192)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    data = b''.join(chunks)
                    json.loads(data.decode('utf-8'))
                    return json.loads(data.decode('utf-8'))
                except json.JSONDecodeError:
                    continue
                except socket.timeout:
                    break
            if chunks:
                data = b''.join(chunks)
                return json.loads(data.decode('utf-8'))
            raise Exception("No data received")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self._sock = None
            raise


# Tool definitions for agent integration
TOOLS = {
    "get_scene_info": {
        "description": "Get detailed information about the current Blender scene",
        "parameters": {}
    },
    "get_object_info": {
        "description": "Get detailed information about a specific object",
        "parameters": {"object_name": {"type": "string", "description": "Name of the object"}}
    },
    "get_viewport_screenshot": {
        "description": "Capture a screenshot of the current Blender 3D viewport",
        "parameters": {"max_size": {"type": "integer", "description": "Max dimension in pixels", "default": 800}}
    },
    "execute_blender_code": {
        "description": "Execute arbitrary Python code in Blender",
        "parameters": {"code": {"type": "string", "description": "Python code to execute"}}
    },
    "get_polyhaven_status": {
        "description": "Check if PolyHaven integration is enabled",
        "parameters": {}
    },
    "get_polyhaven_categories": {
        "description": "Get PolyHaven asset categories",
        "parameters": {"asset_type": {"type": "string", "description": "hdris/textures/models/all", "default": "hdris"}}
    },
    "search_polyhaven_assets": {
        "description": "Search PolyHaven for assets",
        "parameters": {
            "asset_type": {"type": "string", "description": "Type of assets"},
            "categories": {"type": "string", "description": "Comma-separated categories"}
        }
    },
    "download_polyhaven_asset": {
        "description": "Download and import a PolyHaven asset",
        "parameters": {
            "asset_id": {"type": "string", "description": "Asset ID"},
            "asset_type": {"type": "string", "description": "hdris/textures/models"},
            "resolution": {"type": "string", "description": "1k/2k/4k", "default": "1k"},
            "file_format": {"type": "string", "description": "Optional format"}
        }
    },
    "set_texture": {
        "description": "Apply a texture to an object",
        "parameters": {
            "object_name": {"type": "string", "description": "Object name"},
            "texture_id": {"type": "string", "description": "Texture ID"}
        }
    },
    "get_sketchfab_status": {
        "description": "Check Sketchfab integration status",
        "parameters": {}
    },
    "search_sketchfab_models": {
        "description": "Search Sketchfab for models",
        "parameters": {
            "query": {"type": "string", "description": "Search query"},
            "categories": {"type": "string", "description": "Comma-separated categories"},
            "count": {"type": "integer", "description": "Max results", "default": 20},
            "downloadable": {"type": "boolean", "description": "Only downloadable", "default": True}
        }
    },
    "get_sketchfab_model_preview": {
        "description": "Get preview thumbnail of a Sketchfab model",
        "parameters": {"uid": {"type": "string", "description": "Model UID"}}
    },
    "download_sketchfab_model": {
        "description": "Download and import a Sketchfab model",
        "parameters": {
            "uid": {"type": "string", "description": "Model UID"},
            "target_size": {"type": "number", "description": "Target size in meters"}
        }
    },
    "get_hyper3d_status": {
        "description": "Check Hyper3D Rodin integration status",
        "parameters": {}
    },
    "generate_hyper3d_model_via_text": {
        "description": "Generate 3D model using Hyper3D from text",
        "parameters": {
            "text_prompt": {"type": "string", "description": "English description"},
            "bbox_condition": {"type": "array", "description": "Optional [L,W,H] ratio"}
        }
    },
    "generate_hyper3d_model_via_images": {
        "description": "Generate 3D model using Hyper3D from images",
        "parameters": {
            "input_image_paths": {"type": "array", "description": "Absolute paths to images"},
            "input_image_urls": {"type": "array", "description": "Image URLs"},
            "bbox_condition": {"type": "array", "description": "Optional [L,W,H] ratio"}
        }
    },
    "poll_rodin_job_status": {
        "description": "Check Hyper3D generation status",
        "parameters": {
            "subscription_key": {"type": "string", "description": "For MAIN_SITE mode"},
            "request_id": {"type": "string", "description": "For FAL_AI mode"}
        }
    },
    "import_generated_asset": {
        "description": "Import Hyper3D generated asset",
        "parameters": {
            "name": {"type": "string", "description": "Object name in scene"},
            "task_uuid": {"type": "string", "description": "For MAIN_SITE mode"},
            "request_id": {"type": "string", "description": "For FAL_AI mode"}
        }
    },
    "get_hunyuan3d_status": {
        "description": "Check Hunyuan3D integration status",
        "parameters": {}
    },
    "generate_hunyuan3d_model": {
        "description": "Generate 3D model using Hunyuan3D",
        "parameters": {
            "text_prompt": {"type": "string", "description": "Description in English/Chinese"},
            "input_image_url": {"type": "string", "description": "Optional image URL"}
        }
    },
    "poll_hunyuan_job_status": {
        "description": "Check Hunyuan3D job status",
        "parameters": {"job_id": {"type": "string", "description": "Job ID"}}
    },
    "import_generated_asset_hunyuan": {
        "description": "Import Hunyuan3D generated asset",
        "parameters": {
            "name": {"type": "string", "description": "Object name"},
            "zip_file_url": {"type": "string", "description": "ZIP file URL"}
        }
    }
}


def call_tool(tool_name: str, params: Dict[str, Any] = None) -> str:
    """Call a Blender MCP tool and return the result"""
    client = BlenderMCPClient()
    try:
        if not client.connect():
            return "Error: Could not connect to Blender MCP server. Ensure Blender is running with the addon enabled."

        result = client.send_command(tool_name, params or {})

        if result.get("status") == "error":
            return f"Error: {result.get('message', 'Unknown error')}"

        return json.dumps(result.get("result", {}), indent=2)
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
