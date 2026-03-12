"""
Socket server for Blender MCP Addon

Handles TCP socket connections and dispatches commands.
"""

import bpy
import threading
import socket
import json
import traceback
from typing import Dict, Any, Optional

from . import protocol
from .handlers import (
    scene_observe,
    scene_ops,
    camera,
    composition,
    materials,
    lighting,
    export_handler,
    assets_polyhaven,
    assets_sketchfab,
    jobs_hyper3d,
    jobs_hunyuan,
    jobs_tripo3d,
)


class BlenderMCPServer:
    """TCP socket server for Blender MCP."""

    def __init__(self, host="localhost", port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        self.idempotency_cache = {}  # Cache for idempotent commands

    def start(self):
        """Start the server."""
        if self.running:
            print("[BlenderMCP] Server is already running")
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.running = True

            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()

            print(f"[BlenderMCP] Server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"[BlenderMCP] Failed to start server: {e}")
            self.running = False

    def stop(self):
        """Stop the server."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        if self.server_thread:
            self.server_thread.join(timeout=2.0)
        print("[BlenderMCP] Server stopped")

    def _server_loop(self):
        """Main server loop."""
        while self.running:
            try:
                self.socket.settimeout(1.0)
                client, address = self.socket.accept()
                print(f"[BlenderMCP] Client connected from {address}")
                self._handle_client(client)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[BlenderMCP] Server error: {e}")

    def _handle_client(self, client: socket.socket):
        """Handle a client connection."""
        buffer = b""

        try:
            while self.running:
                # Receive data
                data = client.recv(4096)
                if not data:
                    break

                buffer += data

                # Process complete messages (newline-delimited)
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)

                    # Parse command
                    command = protocol.parse_command(line)
                    if not command:
                        response = protocol.create_error_response(
                            "invalid_command",
                            "Could not parse command",
                            request_id=None,
                        )
                    else:
                        # Execute command
                        response = self._execute_command(command)

                    # Send response
                    response_bytes = protocol.encode_command(response)
                    client.sendall(response_bytes)

        except Exception as e:
            print(f"[BlenderMCP] Client handler error: {e}")
        finally:
            client.close()
            print("[BlenderMCP] Client disconnected")

    def _execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command and return response."""
        command_type = protocol.get_command_type(command)
        params = protocol.get_command_params(command)
        request_id = protocol.get_request_id(command)
        idempotency_key = protocol.get_idempotency_key(command)

        # Check idempotency cache
        if idempotency_key and idempotency_key in self.idempotency_cache:
            cached_response = self.idempotency_cache[idempotency_key].copy()
            cached_response["request_id"] = request_id  # Update request ID
            return cached_response

        # Execute on main thread
        result_container: Dict[str, Any] = {}

        def execute_wrapper():
            try:
                result_container["result"] = self._dispatch_command(
                    command_type, params
                )
            except Exception as exc:
                traceback.print_exc()
                result_container["error"] = exc
            return None

        bpy.app.timers.register(execute_wrapper, first_interval=0.0)

        # Wait for result (blocking)
        import time

        timeout = 30.0
        start_time = time.time()
        while time.time() - start_time < timeout:
            if "result" in result_container or "error" in result_container:
                break
            time.sleep(0.01)

        # Build response
        if "error" in result_container:
            response = protocol.create_error_response(
                code="execution_error",
                message=str(result_container["error"]),
                request_id=request_id,
            )
        elif "result" in result_container:
            response = protocol.create_success_response(
                data=result_container["result"],
                request_id=request_id,
            )
        else:
            response = protocol.create_error_response(
                "timeout", "Command execution timed out", request_id=request_id
            )

        # Cache if idempotent
        if idempotency_key and "error" not in result_container:
            self.idempotency_cache[idempotency_key] = response.copy()

        return response

    def _dispatch_command(self, command_type: str, params: Dict[str, Any]) -> Any:
        """Dispatch command to appropriate handler."""
        # Scene observation
        if command_type == "observe_scene":
            return scene_observe.observe_scene(params)
        elif command_type == "get_scene_hash":
            return scene_observe.get_scene_hash()
        elif command_type == "get_scene_info":
            return scene_observe.get_scene_info()
        elif command_type == "get_object_info":
            return scene_observe.get_object_info(params)
        elif command_type == "get_viewport_screenshot":
            return scene_observe.get_viewport_screenshot(params)
        elif command_type == "get_selection":
            return scene_observe.get_selection()

        # Scene operations
        elif command_type == "create_primitive":
            return scene_ops.create_primitive(params)
        elif command_type == "create_empty":
            return scene_ops.create_empty(params)
        elif command_type == "create_camera":
            return scene_ops.create_camera(params)
        elif command_type == "create_light":
            return scene_ops.create_light(params)
        elif command_type == "create_composition_camera":
            return camera.create_composition_camera(params)
        elif command_type == "create_isometric_camera":
            return camera.create_isometric_camera(params)
        elif command_type == "set_camera_depth_of_field":
            return camera.set_camera_depth_of_field(params)
        elif command_type == "apply_camera_preset":
            return camera.apply_camera_preset(params)
        elif command_type == "set_active_camera":
            return camera.set_active_camera(params)
        elif command_type == "list_cameras":
            return camera.list_cameras()
        elif command_type == "frame_camera_to_selection":
            return camera.frame_camera_to_selection(params)
        elif command_type == "set_transform":
            return scene_ops.set_transform(params)
        elif command_type == "select_objects":
            return scene_ops.select_objects(params)
        elif command_type == "delete_objects":
            return scene_ops.delete_objects(params)
        elif command_type == "duplicate_object":
            return scene_ops.duplicate_object(params)
        elif command_type == "assign_material_pbr":
            return scene_ops.assign_material_pbr(params)
        elif command_type == "create_bsdf_material":
            return materials.create_bsdf_material(params)
        elif command_type == "create_emission_material":
            return materials.create_emission_material(params)
        elif command_type == "create_glass_material":
            return materials.create_glass_material(params)
        elif command_type == "create_metal_material":
            return materials.create_metal_material(params)
        elif command_type == "create_subsurface_material":
            return materials.create_subsurface_material(params)
        elif command_type == "create_procedural_texture":
            return materials.create_procedural_texture(params)
        elif command_type == "assign_material":
            return materials.assign_material(params)
        elif command_type == "list_materials":
            return materials.list_materials()
        elif command_type == "delete_material":
            return materials.delete_material(params)
        elif command_type == "create_three_point_lighting":
            return lighting.create_three_point_lighting(params)
        elif command_type == "create_studio_lighting":
            return lighting.create_studio_lighting(params)
        elif command_type == "create_hdri_environment":
            return lighting.create_hdri_environment(params)
        elif command_type == "create_area_light":
            return lighting.create_area_light(params)
        elif command_type == "create_volumetric_lighting":
            return lighting.create_volumetric_lighting(params)
        elif command_type == "adjust_light_exposure":
            return lighting.adjust_light_exposure(params)
        elif command_type == "clear_lights":
            return lighting.clear_lights()
        elif command_type == "list_lights":
            return lighting.list_lights()
        elif command_type == "compose_product_shot":
            return composition.compose_product_shot(params)
        elif command_type == "compose_isometric_scene":
            return composition.compose_isometric_scene(params)
        elif command_type == "compose_character_scene":
            return composition.compose_character_scene(params)
        elif command_type == "compose_automotive_shot":
            return composition.compose_automotive_shot(params)
        elif command_type == "compose_food_shot":
            return composition.compose_food_shot(params)
        elif command_type == "compose_jewelry_shot":
            return composition.compose_jewelry_shot(params)
        elif command_type == "compose_architectural_shot":
            return composition.compose_architectural_shot(params)
        elif command_type == "compose_studio_setup":
            return composition.compose_studio_setup(params)
        elif command_type == "clear_scene":
            return composition.clear_scene(params)
        elif command_type == "setup_render_settings":
            return composition.setup_render_settings(params)
        elif command_type == "set_world_hdri":
            return scene_ops.set_world_hdri(params)
        elif command_type == "execute_blender_code":
            return scene_ops.execute_blender_code(params)

        # Export
        elif command_type == "export_glb":
            return export_handler.export_glb(params)
        elif command_type == "render_preview":
            return export_handler.render_preview(params)
        elif command_type == "export_scene_bundle":
            return export_handler.export_scene_bundle(params)

        # Assets - PolyHaven
        elif command_type == "get_polyhaven_status":
            return assets_polyhaven.get_status()
        elif command_type == "get_polyhaven_categories":
            return assets_polyhaven.get_categories(params)
        elif command_type == "search_polyhaven_assets":
            return assets_polyhaven.search_assets(params)
        elif command_type == "download_polyhaven_asset":
            return assets_polyhaven.download_asset(params)
        elif command_type == "set_texture":
            return assets_polyhaven.set_texture(params)

        # Assets - Sketchfab
        elif command_type == "get_sketchfab_status":
            return assets_sketchfab.get_status()
        elif command_type == "search_sketchfab_models":
            return assets_sketchfab.search_models(params)
        elif command_type == "get_sketchfab_model_preview":
            return assets_sketchfab.get_model_preview(params)
        elif command_type == "download_sketchfab_model":
            return assets_sketchfab.download_model(params)

        # Jobs - Hyper3D
        elif command_type == "get_hyper3d_status":
            return jobs_hyper3d.get_status()
        elif command_type == "generate_hyper3d_model_via_text":
            return jobs_hyper3d.generate_via_text(params)
        elif command_type == "generate_hyper3d_model_via_images":
            return jobs_hyper3d.generate_via_images(params)
        elif command_type == "poll_rodin_job_status":
            return jobs_hyper3d.poll_job_status(params)
        elif command_type == "import_generated_asset":
            return jobs_hyper3d.import_asset(params)

        # Jobs - Hunyuan3D
        elif command_type == "get_hunyuan3d_status":
            return jobs_hunyuan.get_status()
        elif command_type == "generate_hunyuan3d_model":
            return jobs_hunyuan.generate_model(params)
        elif command_type == "poll_hunyuan_job_status":
            return jobs_hunyuan.poll_job_status(params)
        elif command_type == "import_generated_asset_hunyuan":
            return jobs_hunyuan.import_asset(params)

        # Jobs - Tripo3D
        elif command_type == "get_tripo3d_status":
            return jobs_tripo3d.get_status()
        elif command_type == "generate_tripo3d_model":
            return jobs_tripo3d.generate_model(params)
        elif command_type == "poll_tripo3d_status":
            return jobs_tripo3d.poll_job_status(params)
        elif command_type == "import_tripo3d_model":
            return jobs_tripo3d.import_model(params)

        # Unified job API
        elif command_type == "create_job":
            provider = params.get("provider")
            if provider == "hyper3d":
                return jobs_hyper3d.create_job(params.get("payload", {}))
            elif provider == "hunyuan3d":
                return jobs_hunyuan.create_job(params.get("payload", {}))
            elif provider == "tripo3d":
                return jobs_tripo3d.create_job(params.get("payload", {}))
            else:
                raise ValueError(f"Unknown provider: {provider}")
        elif command_type == "get_job":
            for handler in (jobs_hyper3d, jobs_hunyuan, jobs_tripo3d):
                result = handler.get_job(params)
                if result:
                    return result
            raise ValueError(f"Job not found: {params.get('job_id')}")
        elif command_type == "import_job_result":
            for handler in (jobs_hyper3d, jobs_hunyuan, jobs_tripo3d):
                job = handler.get_job(params)
                if job:
                    return handler.import_job_result(params)
            raise ValueError(f"Job not found: {params.get('job_id')}")

        else:
            raise ValueError(f"Unknown command type: {command_type}")


# Global server instance
_server_instance = None


def get_server() -> Optional[BlenderMCPServer]:
    """Get the global server instance."""
    return _server_instance


def start_server(host="localhost", port=9876):
    """Start the global server."""
    global _server_instance
    if _server_instance is None:
        _server_instance = BlenderMCPServer(host, port)
    _server_instance.start()


def stop_server():
    """Stop the global server."""
    global _server_instance
    if _server_instance:
        _server_instance.stop()
        _server_instance = None


def register():
    """Register server module."""
    pass


def unregister():
    """Unregister server module."""
    stop_server()
