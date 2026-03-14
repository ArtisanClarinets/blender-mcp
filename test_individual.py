"""
Simple interactive test for Blender MCP.
Tests one command at a time.
"""

import socket
import json
import time


def send_command(command_type, params=None):
    """Send a single command and return response."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)  # 10 second timeout

    try:
        sock.connect(("localhost", 9876))

        command = {
            "type": command_type,
            "params": params or {},
            "request_id": f"test_{int(time.time() * 1000)}",
        }

        # Send command with newline
        message = json.dumps(command) + "\n"
        sock.sendall(message.encode("utf-8"))

        # Receive response
        buffer = b""
        while b"\n" not in buffer:
            data = sock.recv(4096)
            if not data:
                break
            buffer += data

        line, _ = buffer.split(b"\n", 1)
        response = json.loads(line.decode("utf-8"))
        return response

    except socket.timeout:
        return {"ok": False, "error": {"message": "Timeout waiting for response"}}
    except Exception as e:
        return {"ok": False, "error": {"message": str(e)}}
    finally:
        sock.close()


def test_command(name, command_type, params=None):
    """Test a single command."""
    print(f"\nTesting {name}...")
    response = send_command(command_type, params)

    if response.get("ok"):
        print(f"  [OK] {name} succeeded")
        return True, response
    else:
        print(
            f"  [FAIL] {name} failed: {response.get('error', {}).get('message', 'Unknown error')}"
        )
        return False, response


print("=" * 60)
print("Blender MCP Individual Tool Tests")
print("=" * 60)

# Test 1: Scene observation
success, scene_info = test_command("get_scene_info", "get_scene_info")
if success:
    print(f"  Scene: {scene_info['data']['name']}")
    print(f"  Objects: {scene_info['data']['objects_count']}")

# Test 2: Create cube
success, cube = test_command(
    "create_primitive (cube)",
    "create_primitive",
    {"type": "cube", "name": "TestCube", "location": [0, 0, 0]},
)
if success:
    cube_id = cube["data"]["id"]
    print(f"  Created: {cube['data']['name']} at {cube['data']['location']}")

# Test 3: Create sphere
success, sphere = test_command(
    "create_primitive (sphere)",
    "create_primitive",
    {"type": "sphere", "name": "TestSphere", "location": [3, 0, 0]},
)
if success:
    sphere_id = sphere["data"]["id"]
    print(f"  Created: {sphere['data']['name']} at {sphere['data']['location']}")

# Test 4: Create light
success, light = test_command(
    "create_light",
    "create_light",
    {"type": "POINT", "name": "TestLight", "location": [0, 0, 5], "energy": 100},
)
if success:
    print(f"  Created: {light['data']['name']} ({light['data']['light_type']})")

# Test 5: Create camera
success, camera = test_command(
    "create_camera", "create_camera", {"name": "TestCamera", "location": [5, 5, 5]}
)
if success:
    print(f"  Created: {camera['data']['name']}")

# Test 6: Set transform
if "cube_id" in locals():
    success, transform = test_command(
        "set_transform",
        "set_transform",
        {"target_id": cube_id, "location": [1, 1, 1], "scale": [2, 2, 2]},
    )
    if success:
        print(f"  New location: {transform['data']['location']}")

# Test 7: Select objects
if "cube_id" in locals() and "sphere_id" in locals():
    success, selection = test_command(
        "select_objects", "select_objects", {"ids": [cube_id, sphere_id], "mode": "set"}
    )
    if success:
        print(f"  Selected: {selection['data']['count']} objects")

# Test 8: Duplicate object
if "cube_id" in locals():
    success, dup = test_command(
        "duplicate_object", "duplicate_object", {"id": cube_id, "count": 1}
    )
    if success:
        print(f"  Duplicated: {len(dup['data']['duplicates'])} copies")

# Test 9: Create material
if "cube_id" in locals():
    success, mat = test_command(
        "assign_material_pbr",
        "assign_material_pbr",
        {
            "target_id": cube_id,
            "material_spec": {
                "name": "RedMaterial",
                "base_color": [1, 0, 0],
                "metallic": 0.5,
                "roughness": 0.3,
            },
        },
    )
    if success:
        print(f"  Assigned: {mat['data']['material_name']}")

# Test 10: Create three-point lighting
test_command(
    "create_three_point_lighting",
    "create_three_point_lighting",
    {"target_location": [0, 0, 0], "distance": 5},
)

print("\n" + "=" * 60)
print("Test complete! Check Blender to see the created objects.")
print("=" * 60)
