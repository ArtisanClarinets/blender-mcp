"""
Fast test of Blender MCP server functionality (no rendering).
Tests all available tool functions except slow ones.
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

    command = {"type": command_type, "params": params, "request_id": request_id}

    # Send command
    message = json.dumps(command) + "\n"
    sock.sendall(message.encode("utf-8"))

    # Receive response
    buffer = b""
    while b"\n" not in buffer:
        data = sock.recv(4096)
        if not data:
            break
        buffer += data

    # Parse response
    line, _ = buffer.split(b"\n", 1)
    response = json.loads(line.decode("utf-8"))
    return response


def test_scene_observation(sock):
    """Test scene observation commands."""
    print("\n=== Testing Scene Observation ===")

    # Test get_scene_info
    print("Testing get_scene_info...")
    response = send_command(sock, "get_scene_info")
    assert response.get("ok") == True, f"get_scene_info failed: {response}"
    print(f"  Scene name: {response['data']['name']}")
    print(f"  Objects count: {response['data']['objects_count']}")
    print("  PASSED")

    # Test get_scene_hash
    print("Testing get_scene_hash...")
    response = send_command(sock, "get_scene_hash")
    assert response.get("ok") == True, f"get_scene_hash failed: {response}"
    print(f"  Hash: {response['data']['hash']}")
    print("  PASSED")

    # Test observe_scene
    print("Testing observe_scene...")
    response = send_command(sock, "observe_scene", {"detail": "low"})
    assert response.get("ok") == True, f"observe_scene failed: {response}"
    print(f"  Scene hash: {response['data']['scene_hash']}")
    print("  PASSED")

    # Test get_selection
    print("Testing get_selection...")
    response = send_command(sock, "get_selection")
    assert response.get("ok") == True, f"get_selection failed: {response}"
    print(f"  Selected count: {response['data']['count']}")
    print("  PASSED")


def test_object_creation(sock):
    """Test object creation commands."""
    print("\n=== Testing Object Creation ===")

    # Test create_primitive (cube)
    print("Testing create_primitive (cube)...")
    response = send_command(
        sock,
        "create_primitive",
        {"type": "cube", "name": "TestCube", "location": [0, 0, 0], "size": 2},
    )
    assert response.get("ok") == True, f"create_primitive failed: {response}"
    cube_id = response["data"]["id"]
    print(f"  Created cube: {response['data']['name']} (ID: {cube_id})")
    print("  PASSED")

    # Test create_primitive (sphere)
    print("Testing create_primitive (sphere)...")
    response = send_command(
        sock,
        "create_primitive",
        {"type": "sphere", "name": "TestSphere", "location": [3, 0, 0], "radius": 1},
    )
    assert response.get("ok") == True, f"create_primitive failed: {response}"
    sphere_id = response["data"]["id"]
    print(f"  Created sphere: {response['data']['name']} (ID: {sphere_id})")
    print("  PASSED")

    # Test create_empty
    print("Testing create_empty...")
    response = send_command(
        sock,
        "create_empty",
        {"name": "TestEmpty", "location": [0, 3, 0], "empty_type": "PLAIN_AXES"},
    )
    assert response.get("ok") == True, f"create_empty failed: {response}"
    empty_id = response["data"]["id"]
    print(f"  Created empty: {response['data']['name']} (ID: {empty_id})")
    print("  PASSED")

    # Test create_camera
    print("Testing create_camera...")
    response = send_command(
        sock,
        "create_camera",
        {"name": "TestCamera", "location": [5, 5, 5], "rotation": [0.785, 0, 0.785]},
    )
    assert response.get("ok") == True, f"create_camera failed: {response}"
    camera_id = response["data"]["id"]
    print(f"  Created camera: {response['data']['name']} (ID: {camera_id})")
    print("  PASSED")

    # Test create_light
    print("Testing create_light...")
    response = send_command(
        sock,
        "create_light",
        {
            "type": "POINT",
            "name": "TestLight",
            "location": [0, 0, 5],
            "energy": 100,
            "color": [1, 0.8, 0.6],
        },
    )
    assert response.get("ok") == True, f"create_light failed: {response}"
    light_id = response["data"]["id"]
    print(f"  Created light: {response['data']['name']} (ID: {light_id})")
    print("  PASSED")

    return cube_id, sphere_id, empty_id, camera_id, light_id


def test_object_manipulation(sock, cube_id, sphere_id):
    """Test object manipulation commands."""
    print("\n=== Testing Object Manipulation ===")

    # Test set_transform
    print("Testing set_transform...")
    response = send_command(
        sock,
        "set_transform",
        {
            "target_id": cube_id,
            "location": [1, 1, 1],
            "rotation": [0.5, 0, 0],
            "scale": [1.5, 1.5, 1.5],
        },
    )
    assert response.get("ok") == True, f"set_transform failed: {response}"
    print(f"  Transformed cube to: {response['data']['location']}")
    print("  PASSED")

    # Test select_objects
    print("Testing select_objects...")
    response = send_command(
        sock, "select_objects", {"ids": [cube_id, sphere_id], "mode": "set"}
    )
    assert response.get("ok") == True, f"select_objects failed: {response}"
    print(f"  Selected {response['data']['count']} objects")
    print("  PASSED")

    # Test duplicate_object
    print("Testing duplicate_object...")
    response = send_command(
        sock, "duplicate_object", {"id": cube_id, "count": 2, "linked": False}
    )
    assert response.get("ok") == True, f"duplicate_object failed: {response}"
    print(f"  Duplicated cube: {len(response['data']['duplicates'])} copies")
    print("  PASSED")

    # Test get_object_info
    print("Testing get_object_info...")
    response = send_command(sock, "get_object_info", {"object_name": cube_id})
    assert response.get("ok") == True, f"get_object_info failed: {response}"
    print(f"  Object info retrieved: {response['data']['name']}")
    print("  PASSED")


def test_materials(sock, cube_id):
    """Test material commands."""
    print("\n=== Testing Materials ===")

    # Test assign_material_pbr
    print("Testing assign_material_pbr...")
    response = send_command(
        sock,
        "assign_material_pbr",
        {
            "target_id": cube_id,
            "material_spec": {
                "name": "TestMaterial",
                "base_color": [1, 0, 0],
                "metallic": 0.5,
                "roughness": 0.3,
            },
        },
    )
    assert response.get("ok") == True, f"assign_material_pbr failed: {response}"
    print(f"  Assigned material: {response['data']['material_name']}")
    print("  PASSED")

    # Test create_bsdf_material
    print("Testing create_bsdf_material...")
    response = send_command(
        sock,
        "create_bsdf_material",
        {
            "name": "BSDFMaterial",
            "base_color": [0, 1, 0],
            "metallic": 0.0,
            "roughness": 0.5,
        },
    )
    assert response.get("ok") == True, f"create_bsdf_material failed: {response}"
    print(f"  Created BSDF material: {response['data']['name']}")
    print("  PASSED")

    # Test list_materials
    print("Testing list_materials...")
    response = send_command(sock, "list_materials")
    assert response.get("ok") == True, f"list_materials failed: {response}"
    print(f"  Materials count: {len(response['data']['materials'])}")
    print("  PASSED")


def test_lighting(sock):
    """Test lighting commands."""
    print("\n=== Testing Lighting ===")

    # Test create_three_point_lighting
    print("Testing create_three_point_lighting...")
    response = send_command(
        sock,
        "create_three_point_lighting",
        {"target_location": [0, 0, 0], "distance": 5},
    )
    assert response.get("ok") == True, f"create_three_point_lighting failed: {response}"
    print(f"  Created {len(response['data']['lights'])} lights")
    print("  PASSED")

    # Test list_lights
    print("Testing list_lights...")
    response = send_command(sock, "list_lights")
    assert response.get("ok") == True, f"list_lights failed: {response}"
    print(f"  Lights count: {len(response['data']['lights'])}")
    print("  PASSED")


def test_cleanup(sock, cube_id, sphere_id, empty_id, camera_id, light_id):
    """Test cleanup commands."""
    print("\n=== Testing Cleanup ===")

    # Test delete_objects
    print("Testing delete_objects...")
    response = send_command(
        sock, "delete_objects", {"ids": [empty_id, camera_id, light_id]}
    )
    assert response.get("ok") == True, f"delete_objects failed: {response}"
    print(f"  Deleted {len(response['data']['deleted'])} objects")
    print("  PASSED")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Blender MCP Fast Test Suite (No Rendering)")
    print("=" * 60)

    # Connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(("localhost", 9876))
        print("\nConnected to Blender MCP server")
    except ConnectionRefusedError:
        print("\nERROR: Could not connect to Blender MCP server")
        print("Make sure the addon is installed and server is running in Blender")
        sys.exit(1)

    try:
        # Run tests
        test_scene_observation(sock)
        cube_id, sphere_id, empty_id, camera_id, light_id = test_object_creation(sock)
        test_object_manipulation(sock, cube_id, sphere_id)
        test_materials(sock, cube_id)
        test_lighting(sock)
        test_cleanup(sock, cube_id, sphere_id, empty_id, camera_id, light_id)

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nCreated in Blender:")
        print("  - TestCube (with material)")
        print("  - TestSphere")
        print("  - TestEmpty (deleted)")
        print("  - TestCamera (deleted)")
        print("  - TestLight (deleted)")
        print("  - 2 Duplicates of TestCube")
        print("  - 3 Three-point lighting setup")
        print("\nCheck your Blender scene to see the created objects!")

    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        sock.close()


if __name__ == "__main__":
    run_all_tests()
