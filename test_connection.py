"""
Simple connectivity test for Blender MCP server.
Run this to verify the server is running and responding.
"""

import socket
import json


def test_connection():
    """Test basic connectivity to the Blender MCP server."""
    print("Testing connection to Blender MCP server...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("localhost", 9876))

        # Send a simple command
        command = {"type": "get_scene_info", "params": {}, "request_id": "test_001"}

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

        if response.get("ok"):
            print("[OK] Server is running and responding!")
            print(f"  Scene: {response['data']['name']}")
            print(f"  Objects: {response['data']['objects_count']}")
            return True
        else:
            print(f"[FAIL] Server returned error: {response}")
            return False

    except ConnectionRefusedError:
        print("[FAIL] Could not connect to server on localhost:9876")
        print("  Make sure Blender is running with the MCP addon enabled")
        return False
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        return False
    finally:
        sock.close()


if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
