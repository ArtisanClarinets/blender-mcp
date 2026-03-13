"""Generate the public Blender MCP skill manifest from the live tool surface."""

from __future__ import annotations

import json
from pathlib import Path

from blender_mcp.tool_registry import build_skill_manifest_payload


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_path = project_root / "skills" / "blender_mcp.json"
    output_path.write_text(
        json.dumps(build_skill_manifest_payload(), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
