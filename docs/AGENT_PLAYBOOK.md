# Agent Playbook for Blender MCP

## Golden Path for Autonomous Creation

This playbook outlines the recommended workflow for AI agents using Blender MCP.

## The Observe-Act-Observe Loop

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   OBSERVE   │────>│    PLAN     │────>│     ACT     │
│   (scene)   │     │  (analyze)  │     │  (modify)   │
└─────────────┘     └─────────────┘     └──────┬──────┘
       ↑                                         │
       └─────────────────────────────────────────┘
                    (verify)
```

## Step-by-Step Workflow

### 1. Initial Observation

Always start by observing the current scene state:

```python
# Get comprehensive scene information
result = call_tool("observe_scene", {
    "detail": "med",
    "include_screenshot": True
})

# Parse the response
scene_data = json.loads(result)
objects = scene_data["data"]["objects"]
scene_hash = scene_data["data"]["scene_hash"]
```

**What to look for:**
- Existing objects and their types
- Current camera position
- Lighting setup
- Scene bounds

### 2. Planning

Based on observation, plan your actions:

**Questions to answer:**
- What needs to be created?
- Where should objects be placed?
- What materials are needed?
- Are there size constraints?

### 3. Atomic Operations

Execute changes using atomic tools:

#### Creating Primitives

```python
# Create a cube
result = call_tool("create_primitive", {
    "type": "cube",
    "name": "Floor",
    "size": 10,
    "location": [0, 0, 0]
})

# Create a sphere
result = call_tool("create_primitive", {
    "type": "sphere",
    "name": "Ball",
    "size": 1,
    "location": [0, 0, 2]
})
```

#### Setting Up Lighting

```python
# Create key light
result = call_tool("create_light", {
    "type": "SUN",
    "energy": 3,
    "color": [1, 0.95, 0.8],
    "location": [5, 5, 10],
    "rotation": [0.5, 0, 0.5]
})

# Create fill light
result = call_tool("create_light", {
    "type": "AREA",
    "energy": 1,
    "color": [0.8, 0.9, 1],
    "location": [-5, 3, 5]
})
```

#### Setting Up Camera

```python
result = call_tool("create_camera", {
    "name": "MainCamera",
    "lens": 35,
    "location": [8, -8, 6],
    "look_at": [0, 0, 0]
})
```

### 4. Verification

After each action, verify the changes:

```python
# Check scene hash changed
new_result = call_tool("get_scene_hash", {})
new_hash = json.loads(new_result)["data"]["hash"]

if new_hash != scene_hash:
    print("Scene has changed")

# Take screenshot to verify visually
result = call_tool("get_viewport_screenshot", {"max_size": 1024})
```

## Best Practices

### 1. Never Use `execute_blender_code` Unless Needed

**Bad:**
```python
# Avoid this
result = call_tool("execute_blender_code", {
    "code": "bpy.ops.mesh.primitive_cube_add(size=2)"
})
```

**Good:**
```python
# Use atomic tools instead
result = call_tool("create_primitive", {
    "type": "cube",
    "size": 2
})
```

### 2. Use Request IDs

Always include request IDs for tracking:

```python
import uuid

request_id = str(uuid.uuid4())
result = call_tool("create_primitive", {
    "type": "cube"
}, request_id=request_id)
```

### 3. Use Idempotency Keys

For operations that should happen only once:

```python
result = call_tool("create_primitive", {
    "type": "cube",
    "name": "Floor"
}, idempotency_key="create-floor")
```

### 4. Verify Changes

Always verify before proceeding:

```python
# Before
before_hash = json.loads(call_tool("get_scene_hash", {}))["data"]["hash"]

# Make changes
call_tool("create_primitive", {"type": "cube"})

# After
after_hash = json.loads(call_tool("get_scene_hash", {}))["data"]["hash"]

if before_hash == after_hash:
    print("Warning: Scene did not change!")
```

## Common Patterns

### Creating a Scene from Scratch

```python
import json

# 1. Observe initial state
result = call_tool("observe_scene", {"detail": "low"})
initial = json.loads(result)

# 2. Clear existing objects (optional)
if initial["data"]["objects"]:
    object_ids = [obj["id"] for obj in initial["data"]["objects"]]
    call_tool("delete_objects", {"ids": object_ids})

# 3. Create floor
call_tool("create_primitive", {
    "type": "plane",
    "name": "Floor",
    "size": 20,
    "location": [0, 0, 0]
})

# 4. Create main object
call_tool("create_primitive", {
    "type": "cube",
    "name": "MainObject",
    "size": 2,
    "location": [0, 0, 1]
})

# 5. Add lighting
call_tool("create_light", {
    "type": "SUN",
    "energy": 3,
    "location": [5, 5, 10]
})

# 6. Set up camera
call_tool("create_camera", {
    "name": "MainCamera",
    "location": [8, -8, 6],
    "look_at": [0, 0, 0]
})

# 7. Verify
result = call_tool("observe_scene", {
    "detail": "med",
    "include_screenshot": True
})
final = json.loads(result)
print(f"Created {len(final['data']['objects'])} objects")
```

### Importing and Positioning Assets

```python
# 1. Search for asset
result = call_tool("search_polyhaven_assets", {
    "asset_type": "models",
    "categories": "furniture"
})
assets = json.loads(result)["data"]["results"]

# 2. Download asset
if assets:
    asset_id = assets[0]["id"]
    call_tool("download_polyhaven_asset", {
        "asset_id": asset_id,
        "asset_type": "models",
        "resolution": "2k"
    })

# 3. Position asset
result = call_tool("get_object_info", {"object_name": asset_id})
object_data = json.loads(result)["data"]

call_tool("set_transform", {
    "target_id": object_data["id"],
    "location": [0, 0, 0],
    "scale": [0.5, 0.5, 0.5]
})
```

### Exporting for Next.js

```python
# 1. Final verification
result = call_tool("observe_scene", {
    "detail": "high",
    "include_screenshot": True
})

# 2. Export bundle
result = call_tool("export_scene_bundle", {
    "slug": "my-scene",
    "nextjs_project_root": "/path/to/next-app",
    "mode": "scene",
    "generate_r3f": True
})

export_data = json.loads(result)["data"]
print(f"Exported to: {export_data['output_dir']}")
print(f"Files: {list(export_data['files'].keys())}")
```

## Error Handling

### Common Errors

**Connection Error:**
```python
try:
    result = call_tool("observe_scene", {})
except Exception as e:
    print(f"Connection failed: {e}")
    print("Ensure Blender is running with the addon enabled")
```

**Object Not Found:**
```python
result = call_tool("get_object_info", {"object_name": "NonExistent"})
data = json.loads(result)
if not data.get("ok"):
    print(f"Error: {data['error']['message']}")
```

**Invalid Parameters:**
```python
result = call_tool("create_primitive", {"type": "invalid_type"})
data = json.loads(result)
if not data.get("ok"):
    print(f"Invalid parameter: {data['error']['details']}")
```

## Performance Tips

1. **Batch operations** when possible
2. **Use low detail** for initial observations
3. **Cache scene hashes** to avoid redundant work
4. **Use screenshots sparingly** (they're slow)

## Summary

Remember the key principles:
1. **Observe first** - Always know the current state
2. **Use atomic tools** - Prefer specific tools over code execution
3. **Verify changes** - Check scene hash and screenshots
4. **Be idempotent** - Use idempotency keys for reliability
5. **Handle errors** - Gracefully handle failures