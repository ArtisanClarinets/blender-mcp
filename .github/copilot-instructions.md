# GitHub Copilot Instructions for Blender MCP

## Overview

This file provides instructions for GitHub Copilot when working with Blender MCP code.

## Core Principles

### 1. Prefer Atomic Tools

Always use specific MCP tools instead of generic code execution:

**Good:**
```python
# Use atomic tool
result = call_tool("create_primitive", {
    "type": "cube",
    "name": "Box",
    "location": [0, 0, 1]
})
```

**Bad:**
```python
# Avoid code execution when tools exist
result = call_tool("execute_blender_code", {
    "code": "bpy.ops.mesh.primitive_cube_add(location=(0,0,1))"
})
```

### 2. Always Observe First

Before making changes, observe the current scene state:

```python
# Get current state
result = call_tool("observe_scene", {
    "detail": "med",
    "include_screenshot": True
})
scene_data = json.loads(result)["data"]
```

### 3. Use Request IDs and Idempotency

Include request tracking for reliability:

```python
import uuid

request_id = str(uuid.uuid4())
idempotency_key = "create-floor-001"

result = call_tool("create_primitive", {
    "type": "cube",
    "name": "Floor"
}, request_id=request_id, idempotency_key=idempotency_key)
```

### 4. Verify Changes

Always verify changes were applied:

```python
# Get hash before
before = json.loads(call_tool("get_scene_hash", {}))["data"]["hash"]

# Make changes
call_tool("create_primitive", {"type": "sphere"})

# Verify hash changed
after = json.loads(call_tool("get_scene_hash", {}))["data"]["hash"]
assert before != after, "Scene did not change!"
```

### 5. Export Using export_scene_bundle

For Next.js integration, use the bundle export:

```python
result = call_tool("export_scene_bundle", {
    "slug": "my-scene",
    "nextjs_project_root": "/path/to/project",
    "generate_r3f": True
})
```

## Common Patterns

### Creating a Complete Scene

```python
def create_scene():
    # 1. Observe
    result = call_tool("observe_scene", {"detail": "low"})
    
    # 2. Create objects
    call_tool("create_primitive", {"type": "plane", "name": "Ground", "size": 20})
    call_tool("create_primitive", {"type": "cube", "name": "Box", "location": [0, 0, 1]})
    
    # 3. Add lighting
    call_tool("create_light", {"type": "SUN", "energy": 3, "location": [5, 5, 10]})
    
    # 4. Set camera
    call_tool("create_camera", {
        "name": "Camera",
        "location": [7, -7, 5],
        "look_at": [0, 0, 0]
    })
    
    # 5. Verify
    result = call_tool("observe_scene", {"detail": "med", "include_screenshot": True})
    return result
```

### Working with Assets

```python
def import_and_position_asset(asset_id, position):
    # Download
    call_tool("download_polyhaven_asset", {
        "asset_id": asset_id,
        "asset_type": "models",
        "resolution": "2k"
    })
    
    # Get object info
    result = call_tool("get_object_info", {"object_name": asset_id})
    obj_data = json.loads(result)["data"]
    
    # Position
    call_tool("set_transform", {
        "target_id": obj_data["id"],
        "location": position
    })
```

## Error Handling

Always handle errors gracefully:

```python
def safe_tool_call(tool_name, params):
    try:
        result = call_tool(tool_name, params)
        data = json.loads(result)
        
        if not data.get("ok"):
            error = data.get("error", {})
            print(f"Tool error: {error.get('message')}")
            return None
            
        return data.get("data")
    except Exception as e:
        print(f"Exception: {e}")
        return None
```

## Testing

When writing tests for Blender MCP:

1. Mock the socket connection
2. Test response envelope parsing
3. Verify error handling
4. Test idempotency behavior

## Documentation

When documenting Blender MCP tools:

1. Include parameter descriptions
2. Provide example usage
3. Show expected response format
4. Document error cases

## Code Style

- Use type hints for function signatures
- Document with docstrings
- Handle exceptions explicitly
- Log errors with context