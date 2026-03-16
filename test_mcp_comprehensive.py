"""
Comprehensive test of Blender MCP server functionality.
This script tests all available tool functions through the MCP protocol.
"""

import socket
import json
import time
import sys


def send_command(sock, command_type, params=None, request_id=None):
    """Send a command to the MCP server and return the response."""
    if params is None:
        params = {}
    if request_id is None:
        request_id = f"test_{int(time.time() * 1000)}"
    
    command = {
        "type": command_type,
        "params": params,
        "request_id": request_id
    }
    
    # Send command
    message = json.dumps(command) + "\n"
    sock.sendall(message.encode('utf-8'))
    
    # Receive response
    buffer = b""
    while b"\n" not in buffer:
        data = sock.recv(4096)
        if not data:
            break
        buffer += data
    
    # Parse response
    line, _ = buffer.split(b"\n", 1)
    response = json.loads(line.decode('utf-8'))
    return response


def test_scene_observation(sock):
    """Test scene observation commands."""
    print("\n=== Testing Scene Observation ===")
    
    # Test get_scene_info
    print("Testing get_scene_info...")
    response = send_command(sock, "get_scene_info")
    assert response.get("ok") == True, f"get_scene_info failed: {response}"
    print("[OK] get_scene_info works")
    
    # Test get_scene_hash
    print("Testing get_scene_hash...")
    response = send_command(sock, "get_scene_hash")
    assert response.get("ok") == True, f"get_scene_hash failed: {response}"
    print("[OK] get_scene_hash works")
    
    # Test get_selection
    print("Testing get_selection...")
    response = send_command(sock, "get_selection")
    assert response.get("ok") == True, f"get_selection failed: {response}"
    print("[OK] get_selection works")
    
    # Test observe_scene
    print("Testing observe_scene...")
    response = send_command(sock, "observe_scene", {"include_metadata": True})
    assert response.get("ok") == True, f"observe_scene failed: {response}"
    print("[OK] observe_scene works")


def test_primitives(sock):
    """Test primitive creation commands."""
    print("\n=== Testing Primitives ===")
    
    # Test create_primitive (cube)
    print("Testing create_primitive (cube)...")
    response = send_command(sock, "create_primitive", {
        "type": "cube",
        "name": "TestCube",
        "location": [0, 0, 0],
        "size": 2
    })
    assert response.get("ok") == True, f"create_primitive cube failed: {response}"
    print("[OK] create_primitive (cube) works")
    
    # Test create_primitive (sphere)
    print("Testing create_primitive (sphere)...")
    response = send_command(sock, "create_primitive", {
        "type": "sphere",
        "name": "TestSphere",
        "location": [3, 0, 0],
        "radius": 1
    })
    assert response.get("ok") == True, f"create_primitive sphere failed: {response}"
    print("[OK] create_primitive (sphere) works")
    
    # Test create_primitive (cylinder)
    print("Testing create_primitive (cylinder)...")
    response = send_command(sock, "create_primitive", {
        "type": "cylinder",
        "name": "TestCylinder",
        "location": [-3, 0, 0],
        "radius": 0.5,
        "depth": 2
    })
    assert response.get("ok") == True, f"create_primitive cylinder failed: {response}"
    print("[OK] create_primitive (cylinder) works")
    
    # Test create_empty
    print("Testing create_empty...")
    response = send_command(sock, "create_empty", {
        "name": "TestEmpty",
        "location": [0, 3, 0]
    })
    assert response.get("ok") == True, f"create_empty failed: {response}"
    print("[OK] create_empty works")


def test_cameras(sock):
    """Test camera commands."""
    print("\n=== Testing Cameras ===")
    
    # Test create_camera
    print("Testing create_camera...")
    response = send_command(sock, "create_camera", {
        "name": "TestCamera",
        "location": [5, 5, 5],
        "rotation": [0.785, 0, 0.785]
    })
    assert response.get("ok") == True, f"create_camera failed: {response}"
    print("[OK] create_camera works")
    
    # Test list_cameras
    print("Testing list_cameras...")
    response = send_command(sock, "list_cameras")
    assert response.get("ok") == True, f"list_cameras failed: {response}"
    print("[OK] list_cameras works")
    
    # Test set_active_camera
    print("Testing set_active_camera...")
    response = send_command(sock, "set_active_camera", {"name": "TestCamera"})
    assert response.get("ok") == True, f"set_active_camera failed: {response}"
    print("[OK] set_active_camera works")


def test_lights(sock):
    """Test lighting commands."""
    print("\n=== Testing Lights ===")
    
    # Test create_light
    print("Testing create_light...")
    response = send_command(sock, "create_light", {
        "type": "SUN",
        "name": "TestSun",
        "location": [0, 0, 10],
        "energy": 5
    })
    assert response.get("ok") == True, f"create_light failed: {response}"
    print("[OK] create_light works")
    
    # Test list_lights
    print("Testing list_lights...")
    response = send_command(sock, "list_lights")
    assert response.get("ok") == True, f"list_lights failed: {response}"
    print("[OK] list_lights works")
    
    # Test create_three_point_lighting
    print("Testing create_three_point_lighting...")
    response = send_command(sock, "create_three_point_lighting", {
        "key_energy": 10,
        "fill_energy": 5,
        "back_energy": 7
    })
    assert response.get("ok") == True, f"create_three_point_lighting failed: {response}"
    print("[OK] create_three_point_lighting works")


def test_materials(sock):
    """Test material commands."""
    print("\n=== Testing Materials ===")
    
    # First select an object
    send_command(sock, "select_objects", {"names": ["TestCube"]})
    
    # Test assign_material_pbr
    print("Testing assign_material_pbr...")
    response = send_command(sock, "assign_material_pbr", {
        "object_name": "TestCube",
        "material_name": "TestPBRMaterial",
        "base_color": [1.0, 0.2, 0.2],
        "roughness": 0.5,
        "metallic": 0.8
    })
    assert response.get("ok") == True, f"assign_material_pbr failed: {response}"
    print("[OK] assign_material_pbr works")
    
    # Test list_materials
    print("Testing list_materials...")
    response = send_command(sock, "list_materials")
    assert response.get("ok") == True, f"list_materials failed: {response}"
    print("[OK] list_materials works")
    
    # Test create_bsdf_material
    print("Testing create_bsdf_material...")
    response = send_command(sock, "create_bsdf_material", {
        "name": "TestBSDF",
        "base_color": [0.2, 0.5, 1.0],
        "roughness": 0.3
    })
    assert response.get("ok") == True, f"create_bsdf_material failed: {response}"
    print("[OK] create_bsdf_material works")
    
    # Test assign_material
    print("Testing assign_material...")
    response = send_command(sock, "assign_material", {
        "object_name": "TestSphere",
        "material_name": "TestBSDF"
    })
    assert response.get("ok") == True, f"assign_material failed: {response}"
    print("[OK] assign_material works")


def test_transforms(sock):
    """Test transform commands."""
    print("\n=== Testing Transforms ===")
    
    # Test set_transform
    print("Testing set_transform...")
    response = send_command(sock, "set_transform", {
        "name": "TestCube",
        "location": [2, 2, 2],
        "rotation": [0.5, 0.5, 0.5],
        "scale": [1.5, 1.5, 1.5]
    })
    assert response.get("ok") == True, f"set_transform failed: {response}"
    print("[OK] set_transform works")
    
    # Test get_object_info
    print("Testing get_object_info...")
    response = send_command(sock, "get_object_info", {"object_name": "TestCube"})
    assert response.get("ok") == True, f"get_object_info failed: {response}"
    print("[OK] get_object_info works")


def test_composition(sock):
    """Test composition commands."""
    print("\n=== Testing Composition ===")
    
    # Test compose_product_shot
    print("Testing compose_product_shot...")
    response = send_command(sock, "compose_product_shot", {
        "object_name": "TestCube",
        "background": "white"
    })
    assert response.get("ok") == True, f"compose_product_shot failed: {response}"
    print("[OK] compose_product_shot works")
    
    # Test compose_studio_setup
    print("Testing compose_studio_setup...")
    response = send_command(sock, "compose_studio_setup", {
        "backdrop": "white"
    })
    assert response.get("ok") == True, f"compose_studio_setup failed: {response}"
    print("[OK] compose_studio_setup works")


def test_rendering(sock):
    """Test rendering commands."""
    print("\n=== Testing Rendering ===")
    
    # Test setup_render_settings
    print("Testing setup_render_settings...")
    response = send_command(sock, "setup_render_settings", {
        "engine": "EEVEE",
        "resolution_x": 1920,
        "resolution_y": 1080,
        "samples": 64
    })
    assert response.get("ok") == True, f"setup_render_settings failed: {response}"
    print("[OK] setup_render_settings works")


def test_export(sock):
    """Test export commands."""
    print("\n=== Testing Export ===")
    
    # Test export_glb
    print("Testing export_glb...")
    response = send_command(sock, "export_glb", {
        "filepath": "//test_export.glb",
        "selected_only": False
    })
    assert response.get("ok") == True, f"export_glb failed: {response}"
    print("[OK] export_glb works")


def test_provider_status(sock):
    """Test provider status commands."""
    print("\n=== Testing Provider Status ===")
    
    # Test get_polyhaven_status
    print("Testing get_polyhaven_status...")
    response = send_command(sock, "get_polyhaven_status")
    assert response.get("ok") == True, f"get_polyhaven_status failed: {response}"
    print("[OK] get_polyhaven_status works")
    
    # Test get_sketchfab_status
    print("Testing get_sketchfab_status...")
    response = send_command(sock, "get_sketchfab_status")
    assert response.get("ok") == True, f"get_sketchfab_status failed: {response}"
    print("[OK] get_sketchfab_status works")
    
    # Test get_hyper3d_status
    print("Testing get_hyper3d_status...")
    response = send_command(sock, "get_hyper3d_status")
    assert response.get("ok") == True, f"get_hyper3d_status failed: {response}"
    print("[OK] get_hyper3d_status works")
    
    # Test get_hunyuan3d_status
    print("Testing get_hunyuan3d_status...")
    response = send_command(sock, "get_hunyuan3d_status")
    assert response.get("ok") == True, f"get_hunyuan3d_status failed: {response}"
    print("[OK] get_hunyuan3d_status works")
    
    # Test get_tripo3d_status
    print("Testing get_tripo3d_status...")
    response = send_command(sock, "get_tripo3d_status")
    assert response.get("ok") == True, f"get_tripo3d_status failed: {response}"
    print("[OK] get_tripo3d_status works")


def test_code_execution(sock):
    """Test code execution command."""
    print("\n=== Testing Code Execution ===")
    
    # Test execute_blender_code
    print("Testing execute_blender_code...")
    response = send_command(sock, "execute_blender_code", {
        "code": "print('Hello from MCP!'); bpy.ops.mesh.primitive_cone_add(name='TestCone')"
    })
    assert response.get("ok") == True, f"execute_blender_code failed: {response}"
    print("[OK] execute_blender_code works")


def test_cleanup(sock):
    """Test cleanup commands."""
    print("\n=== Testing Cleanup ===")
    
    # Test delete_objects
    print("Testing delete_objects...")
    response = send_command(sock, "delete_objects", {
        "names": ["TestCone"]
    })
    assert response.get("ok") == True, f"delete_objects failed: {response}"
    print("[OK] delete_objects works")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Blender MCP Comprehensive Test Suite")
    print("=" * 60)
    
    # Connect to the MCP server
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", 9876))
        sock.settimeout(30.0)
        print("\n[OK] Connected to MCP server on localhost:9876")
    except Exception as e:
        print(f"\n[FAIL] Failed to connect to MCP server: {e}")
        print("Make sure Blender is running with the MCP addon enabled and server started.")
        sys.exit(1)
    
    try:
        # Run all test suites
        test_scene_observation(sock)
        test_primitives(sock)
        test_cameras(sock)
        test_lights(sock)
        test_materials(sock)
        test_transforms(sock)
        test_composition(sock)
        test_rendering(sock)
        test_export(sock)
        test_provider_status(sock)
        test_code_execution(sock)
        test_cleanup(sock)
        
        print("\n" + "=" * 60)
        print("[OK] ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sock.close()
        print("\n[OK] Disconnected from MCP server")


if __name__ == "__main__":
    run_all_tests()
