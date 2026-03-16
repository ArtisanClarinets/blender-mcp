#!/usr/bin/env python3
"""
Test script to verify the Blender MCP connection fix.
This script tests the connection between the MCP server and Blender addon.
"""

import socket
import json
import time
import sys

def test_blender_connection(host="localhost", port=9876):
    """Test connection to Blender MCP addon."""
    print(f"Testing connection to Blender MCP addon at {host}:{port}")
    
    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        
        print("Attempting to connect...")
        sock.connect((host, port))
        print("✓ Connection established")
        
        # Test 1: Simple ping command
        print("\nTest 1: Ping command")
        ping_command = {
            "type": "ping",
            "params": {},
            "request_id": "test_ping_1"
        }
        
        sock.sendall((json.dumps(ping_command) + "\n").encode('utf-8'))
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8').strip())
        
        if response.get("ok") and response.get("data", {}).get("status") == "ok":
            print("✓ Ping test passed")
        else:
            print(f"✗ Ping test failed: {response}")
            return False
        
        # Test 2: Get scene info
        print("\nTest 2: Get scene info")
        scene_command = {
            "type": "get_scene_info",
            "params": {},
            "request_id": "test_scene_1"
        }
        
        sock.sendall((json.dumps(scene_command) + "\n").encode('utf-8'))
        response_data = sock.recv(4096)
        response = json.loads(response_data.decode('utf-8').strip())
        
        if response.get("ok") and "data" in response:
            scene_data = response["data"]
            print(f"✓ Scene info test passed")
            print(f"  Scene: {scene_data.get('name', 'Unknown')}")
            print(f"  Objects: {scene_data.get('objects_count', 0)}")
            print(f"  Frame range: {scene_data.get('frame_start', 0)}-{scene_data.get('frame_end', 0)}")
        else:
            print(f"✗ Scene info test failed: {response}")
            return False
        
        # Test 3: Connection stability test
        print("\nTest 3: Connection stability")
        for i in range(3):
            stability_command = {
                "type": "ping",
                "params": {},
                "request_id": f"stability_test_{i}"
            }
            
            sock.sendall((json.dumps(stability_command) + "\n").encode('utf-8'))
            response_data = sock.recv(4096)
            response = json.loads(response_data.decode('utf-8').strip())
            
            if response.get("ok"):
                print(f"✓ Stability test {i+1}/3 passed")
            else:
                print(f"✗ Stability test {i+1}/3 failed: {response}")
                return False
            
            time.sleep(0.1)
        
        sock.close()
        print("\n✓ All tests passed! Connection is working correctly.")
        return True
        
    except socket.timeout:
        print(f"✗ Connection timeout - Blender addon may not be running")
        return False
    except ConnectionRefusedError:
        print(f"✗ Connection refused - Blender addon is not listening on port {port}")
        return False
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False

def test_mcp_server_connection():
    """Test connection to the MCP server itself."""
    print("\n" + "="*50)
    print("Testing MCP Server Connection")
    print("="*50)
    
    try:
        # Import the MCP connection module
        sys.path.insert(0, 'src')
        from blender_mcp.core.connection import get_blender_connection
        
        print("Attempting to connect to Blender via MCP server...")
        connection = get_blender_connection()
        print("✓ MCP server connection established")
        
        # Test the connection
        print("Testing MCP server connection...")
        result = connection.send_command("ping", {})
        
        if result.get("status") == "ok":
            print("✓ MCP server connection test passed")
            return True
        else:
            print(f"✗ MCP server connection test failed: {result}")
            return False
            
    except Exception as e:
        print(f"✗ MCP server connection failed: {e}")
        return False

if __name__ == "__main__":
    print("Blender MCP Connection Test")
    print("="*50)
    
    # Test direct connection to Blender addon
    blender_ok = test_blender_connection()
    
    # Test MCP server connection
    mcp_ok = test_mcp_server_connection()
    
    print("\n" + "="*50)
    print("Test Summary:")
    print(f"Blender Addon Connection: {'✓ PASS' if blender_ok else '✗ FAIL'}")
    print(f"MCP Server Connection: {'✓ PASS' if mcp_ok else '✗ FAIL'}")
    
    if blender_ok and mcp_ok:
        print("\n🎉 All connection tests passed! The blender-mcp setup is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some connection tests failed. Please check:")
        print("1. Blender is running with the blender-mcp addon enabled")
        print("2. The server is started in Blender (click 'Start Server')")
        print("3. No firewall is blocking port 9876")
        print("4. The MCP server is properly configured")
        sys.exit(1)