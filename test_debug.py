"""
Debug test to identify where the active_object error is occurring.
"""

import socket
import json


def send_command(command_type, params=None):
    """Send a command and return response."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", 9876))

    command = {"type": command_type, "params": params or {}, "request_id": "debug_001"}

    message = json.dumps(command) + "\n"
    sock.sendall(message.encode("utf-8"))

    buffer = b""
    while b"\n" not in buffer:
        data = sock.recv(4096)
        if not data:
            break
        buffer += data

    line, _ = buffer.split(b"\n", 1)
    response = json.loads(line.decode("utf-8"))
    sock.close()
    return response


# Test get_scene_hash first (should work)
print("Testing get_scene_hash...")
response = send_command("get_scene_hash")
print(f"Response: {response}")

# Test observe_scene
print("\nTesting observe_scene...")
response = send_command("observe_scene", {"detail": "low"})
print(f"Response: {json.dumps(response, indent=2)[:500]}...")

# Test get_scene_info
print("\nTesting get_scene_info...")
response = send_command("get_scene_info")
print(f"Response: {json.dumps(response, indent=2)[:500]}...")
