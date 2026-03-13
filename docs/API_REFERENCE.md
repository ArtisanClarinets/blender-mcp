# Blender MCP API Reference

The authoritative API surface is generated from the live codebase.

## Regenerate the manifest

```bash
python scripts/generate_skill_manifest.py
```

That command writes `skills/blender_mcp.json`, which now serves as the canonical machine-readable tool manifest.

## Registry-backed surfaces

- Python MCP tool discovery: `src/blender_mcp/tool_registry.py`
- Blender addon command dispatch: `blender_mcp_addon/command_registry.py`
- Payload validation: `src/blender_mcp/schemas.py`

## Command categories

- Scene observe / scene ops
- Camera / composition / lighting
- Materials / procedural materials
- Export / asset ingestion / AI jobs
- Rigging / animation / atmospherics
- Production tracking / render pipeline / AI creative

## Compatibility notes

- `addon.py` is retained for legacy compatibility, but the packaged `blender_mcp_addon/` addon is the canonical install target.
- Dynamic validation is permissive for legacy and evolving commands, while stricter validation remains for core, high-confidence command payloads.
