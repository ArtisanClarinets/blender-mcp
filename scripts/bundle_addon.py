# scripts/bundle_addon.py 
import os 
import re 
from pathlib import Path 

def get_bundle_order(): 
    """Define the order in which files should be bundled.""" 
    return [ 
        "protocol.py", 
        "utils.py", 
        "id.py", 
        "handlers/jobs/jobs_common.py", 
        "handlers/scene/scene_observe.py", 
        "handlers/scene/scene_ops.py", 
        "handlers/scene/camera.py", 
        "handlers/scene/composition.py", 
        "handlers/rendering/materials.py", 
        "handlers/scene/lighting.py", 
        "handlers/rendering/advanced_materials.py", 
        "handlers/asset/assets_polyhaven.py", 
        "handlers/asset/assets_sketchfab.py", 
        "handlers/jobs/jobs_hyper3d.py", 
        "handlers/jobs/jobs_hunyuan.py", 
        "handlers/jobs/jobs_tripo3d.py", 
        "handlers/character/rigging.py", 
        "handlers/character/animation.py", 
        "handlers/rendering/atmospherics_handler.py", 
        "handlers/rendering/procedural_materials.py", 
        "handlers/io/production.py", 
        "handlers/rendering/render_pipeline.py", 
        "handlers/ai/ai_creative.py", 
        "handlers/io/export_handler.py", 
        "command_registry.py", 
        "server.py", 
        "ui.py", 
        "__init__.py", 
    ] 

def bundle_addon(): 
    """Bundle the addon into a single file.""" 
    addon_dir = Path("blender_mcp_addon") 
    output_file = Path("addon.py") 
    bundle_order = get_bundle_order() 

    with open(output_file, "w", encoding="utf-8") as outfile: 
        outfile.write("# Blender MCP Addon - Single File Version\n") 
        outfile.write("# This file can be installed directly into Blender\n") 
        outfile.write("# Generated from blender_mcp_addon package\n\n") 

        for file_path in bundle_order: 
            full_path = addon_dir / file_path 
            if not full_path.exists(): 
                print(f"Warning: {full_path} not found, skipping.") 
                continue 

            with open(full_path, "r", encoding="utf-8") as infile: 
                content = infile.read() 
                # Remove bl_info from all but the main __init__.py 
                if file_path != "__init__.py": 
                    content = re.sub(r"bl_info\s*=\s*{[^}]+}", "", content) 
                # Remove relative imports 
                content = re.sub(r"from\s+\.\s+import\s+", "from ", content) 
                outfile.write(f"# --- Start of {file_path} ---\n") 
                outfile.write(content) 
                outfile.write(f"\n# --- End of {file_path} ---\n\n") 

    print(f"Successfully bundled addon to {output_file}") 

if __name__ == "__main__": 
    bundle_addon()