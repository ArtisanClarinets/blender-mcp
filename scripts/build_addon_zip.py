"""Package the canonical multi-file Blender addon for distribution."""

from __future__ import annotations

import shutil
from pathlib import Path



def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    dist_dir = project_root / "dist"
    staging_dir = dist_dir / "blender_mcp_addon"
    zip_base = dist_dir / "blender_mcp_addon"

    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(project_root / "blender_mcp_addon", staging_dir)
    shutil.make_archive(str(zip_base), "zip", root_dir=dist_dir, base_dir="blender_mcp_addon")
    print(f"Built {zip_base}.zip")


if __name__ == "__main__":
    main()
