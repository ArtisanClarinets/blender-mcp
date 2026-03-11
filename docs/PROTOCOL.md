# Blender MCP Protocol Specification

## Overview

This document defines the communication protocol between the Python MCP server and the Blender addon.

## Communication Protocol

### Transport

- **Protocol**: TCP sockets
- **Default Host**: `localhost`
- **Default Port**: `9876`
- **Framing**: Newline-delimited JSON (NDJSON)

### Message Format

All messages are JSON objects terminated by a newline character (`\n`).

#### Command Envelope

```json
{
  "type": "command_name",
  "params": {
    "key": "value"
  },
  "request_id": "uuid-string",
  "idempotency_key": "optional-key",
  "meta": {}
}
```

**Fields:**
- `type` (required): Command type identifier
- `params` (required): Command-specific parameters
- `request_id` (required): Unique identifier for request correlation
- `idempotency_key` (optional): Key for idempotent operations
- `meta` (optional): Additional metadata

#### Response Envelope

```json
{
  "ok": true,
  "data": {},
  "error": {
    "code": "error_code",
    "message": "Error description",
    "details": {}
  },
  "request_id": "uuid-string",
  "meta": {}
}
```

**Fields:**
- `ok` (required): Boolean indicating success
- `data` (optional): Response data (present if ok=true)
- `error` (optional): Error information (present if ok=false)
  - `code`: Error code string
  - `message`: Human-readable error message
  - `details`: Additional error details
- `request_id` (required): Matches the request's request_id
- `meta` (optional): Response metadata

### Idempotency

Commands can include an `idempotency_key` to ensure they are executed only once. The server caches responses for idempotent commands and returns the cached result for duplicate keys.

**Idempotency Rules:**
1. Commands with the same `idempotency_key` return identical responses
2. Cached responses are kept for 24 hours
3. Only successful responses are cached
4. Observation commands should not use idempotency keys

## Command Types

### Observation Commands

#### `observe_scene`

Observe the current scene state.

**Parameters:**
```json
{
  "detail": "low|med|high",
  "include_screenshot": false,
  "max_screenshot_size": 800
}
```

**Response:**
```json
{
  "scene_hash": "abc123",
  "objects": [...],
  "collections": [...],
  "cameras": [...],
  "lights": [...],
  "world": {...},
  "render_settings": {...},
  "bounds": {...}
}
```

#### `get_scene_hash`

Get a stable hash of the scene state.

**Response:**
```json
{
  "hash": "abc123def456"
}
```

### Scene Operation Commands

#### `create_primitive`

Create a primitive object.

**Parameters:**
```json
{
  "type": "cube|sphere|cylinder|cone|torus|plane",
  "name": "optional-name",
  "size": 1.0,
  "location": [0, 0, 0],
  "rotation": [0, 0, 0],
  "scale": [1, 1, 1]
}
```

#### `set_transform`

Set object transform.

**Parameters:**
```json
{
  "target_id": "object-name-or-id",
  "location": [0, 0, 0],
  "rotation": [0, 0, 0],
  "scale": [1, 1, 1],
  "apply": false
}
```

### Export Commands

#### `export_glb`

Export to GLB format.

**Parameters:**
```json
{
  "target": "scene|selection|collection",
  "name": "export",
  "output_dir": "exports",
  "draco": true,
  "texture_embed": true,
  "y_up": true
}
```

#### `export_scene_bundle`

Export complete scene bundle for Next.js.

**Parameters:**
```json
{
  "slug": "scene-name",
  "nextjs_project_root": "/path/to/project",
  "mode": "scene|assets",
  "generate_r3f": false
}
```

### Job Commands

#### `create_job`

Create an async AI generation job.

**Parameters:**
```json
{
  "provider": "hyper3d|hunyuan3d",
  "payload": {
    "text_prompt": "description",
    "bbox_condition": [1, 1, 1]
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "provider": "hyper3d",
  "status": "pending"
}
```

#### `get_job`

Get job status.

**Parameters:**
```json
{
  "job_id": "uuid"
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "provider": "hyper3d",
  "status": "pending|running|completed|failed",
  "progress": 0.5,
  "message": "Processing...",
  "result": {...},
  "error": null
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `invalid_command` | Could not parse or validate command |
| `unknown_command` | Command type not recognized |
| `execution_error` | Error during command execution |
| `timeout` | Command execution timed out |
| `not_found` | Requested object/resource not found |
| `invalid_params` | Invalid or missing parameters |

## Examples

### Basic Command/Response

**Request:**
```json
{"type": "get_scene_info", "params": {}, "request_id": "req-123"}
```

**Response:**
```json
{"ok": true, "data": {"objects_count": 5}, "request_id": "req-123"}
```

### Error Response

**Request:**
```json
{"type": "get_object_info", "params": {}, "request_id": "req-456"}
```

**Response:**
```json
{"ok": false, "error": {"code": "invalid_params", "message": "object_name is required"}, "request_id": "req-456"}
```

### Idempotent Command

**Request:**
```json
{"type": "create_primitive", "params": {"type": "cube"}, "request_id": "req-789", "idempotency_key": "create-cube-1"}
```

Duplicate requests with the same `idempotency_key` will return the cached response.

## Implementation Notes

### Server Side (Python)

1. Use `asyncio.Lock` or threading lock for socket access
2. Implement request timeout handling
3. Validate all incoming commands
4. Log errors with context

### Addon Side (Blender)

1. Execute all Blender API calls on the main thread
2. Use `bpy.app.timers` for thread-safe execution
3. Maintain idempotency cache
4. Handle partial reads from socket

### Thread Safety

- Server: Thread-safe with connection locking
- Addon: All Blender operations on main thread
- Socket: Single-threaded access per connection