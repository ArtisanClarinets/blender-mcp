# Blender MCP User Guide

## Canonical installation path

Use the packaged Blender addon, not the legacy single-file `addon.py` path.

1. Run `python scripts/build_addon_zip.py`
2. In Blender, open **Edit > Preferences > Add-ons**
3. Click **Install...** and choose `dist/blender_mcp_addon.zip`
4. Enable **Blender MCP**
5. Start the Blender-side socket server from the add-on panel

## Development workflow

Install the Python package in editable mode:

```bash
pip install -e '.[dev]'
```

Generate the public MCP skill manifest from the live tool surface:

```bash
python scripts/generate_skill_manifest.py
```

Run the automated test suite:

```bash
pytest -q
```

## Studio-oriented features available

- Core scene observation and scene manipulation
- Camera, composition, lighting, materials, and export workflows
- Unified AI job wrappers for Hyper3D, Hunyuan3D, and Tripo3D
- Rigging, animation, atmospherics, procedural materials, render pipeline, production tracking, and AI-assist helpers
- Scene-local shot/version/review metadata for autonomous workflows
- Render-job planning, pass setup, and stereoscopic configuration helpers

## Important scope note

This repo now includes stronger production primitives, but it is still a Blender-first orchestration layer. It is not a full substitute for USD-centric scene assembly, editorial, review, or studio tracker infrastructure.
