# Blender MCP Protocol Documentation

This document describes the communication protocols used by Blender MCP.

**Important**: Blender MCP uses TWO distinct protocols:

1. **MCP Protocol** (External): The Model Context Protocol that AI assistants use
2. **Internal Blender Socket Protocol** (Internal): JSON-over-TCP between Python server and Blender addon

---

## Part 1: MCP Protocol (External)

The Model Context Protocol (MCP) is the primary protocol for AI assistants to interact with Blender MCP.

### Transport

- **Protocol**: stdio (Standard Input/Output)
- **Format**: JSON-RPC 2.0
- **SDK**: FastMCP (Python MCP SDK)

### Server Capabilities

The MCP server advertises the following capabilities:

```json
{
  "protocolVersion": "2024-11-05",
  "serverInfo": {
    "name": "BlenderMCP",
    "version": "1.5.5"
  },
  "capabilities": {
    "tools": { "listChanged": false },
    "prompts": { "listChanged": false },
    "resources": { "subscribe": false, "listChanged": false },
    "completions": {},
    "logging": {}
  }
}
```

### MCP Features

#### Tools

Tools are invoked via the `tools/call` method. See the tool catalog at `catalog://tools` resource.

Example tool call:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_scene_info",
    "arguments": {}
  }
}
```

#### Prompts

Prompts are retrieved via the `prompts/get` method.

Available prompts:
- `asset_creation_strategy`
- `production_pipeline_strategy`
- `animation_rigging_strategy`
- `autonomous_production_workflow`

#### Resources

Resources are accessed via the `resources/read` method.

Static resources:
- `catalog://tools`
- `catalog://commands`
- `catalog://schemas`
- `catalog://protocol`
- `catalog://pipeline`
- `scene://current`
- `scene://selection`
- `pipeline://projects`
- `pipeline://status`
- `publish://status`
- `ocio://status`
- `usd://status`

Resource templates:
- `repo://tree/{path}`
- `repo://file/{path}`
- `scene://object/{object_name}`
- `pipeline://project/{project_code}`
- `pipeline://sequence/{sequence_code}`
- `pipeline://shot/{shot_name}`
- `pipeline://asset/{asset_type}/{asset_name}`
- `publish://entity/{entity_type}/{entity_id}`
- `publish://manifest/{publish_id}`
- `ocio://project/{project_code}`
- `usd://package/{package_id}`

#### Completions

Completions are requested via the `completion/complete` method.

Supported completions:
- Project codes
- Sequence codes
- Shot names
- Asset types and names
- Object names
- Colorspaces
- Tracker adapters

---

## Part 2: Internal Blender Socket Protocol

The internal protocol is used for communication between the Python MCP server and the Blender addon. This is an implementation detail and not part of the public MCP API.

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

### Command Types

See the command catalog at `catalog://commands` resource for the full list.

Common commands:
- `observe_scene` - Observe the current scene state
- `get_scene_info` - Get scene information
- `get_object_info` - Get object information
- `create_primitive` - Create a primitive object
- `set_transform` - Set object transform
- `export_glb` - Export to GLB format

### Error Codes

| Code | Description |
|------|-------------|
| `invalid_command` | Could not parse or validate command |
| `unknown_command` | Command type not recognized |
| `execution_error` | Error during command execution |
| `timeout` | Command execution timed out |
| `not_found` | Requested object/resource not found |
| `invalid_params` | Invalid or missing parameters |

### Examples

#### Basic Command/Response

**Request:**
```json
{"type": "get_scene_info", "params": {}, "request_id": "req-123"}
```

**Response:**
```json
{"ok": true, "data": {"objects_count": 5}, "request_id": "req-123"}
```

#### Error Response

**Request:**
```json
{"type": "get_object_info", "params": {}, "request_id": "req-456"}
```

**Response:**
```json
{"ok": false, "error": {"code": "invalid_params", "message": "object_name is required"}, "request_id": "req-456"}
```

#### Idempotent Command

**Request:**
```json
{"type": "create_primitive", "params": {"type": "cube"}, "request_id": "req-789", "idempotency_key": "create-cube-1"}
```

Duplicate requests with the same `idempotency_key` will return the cached response.

---

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

---

## Summary

- **AI Assistants** use the **MCP Protocol** (stdio, JSON-RPC)
- **Internal Communication** uses the **Blender Socket Protocol** (TCP, NDJSON)
- The MCP server translates between these protocols
- Resources and Completions are part of MCP, not the internal protocol
