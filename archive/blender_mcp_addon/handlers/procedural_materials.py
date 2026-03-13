"""Procedural and AI-assisted material handlers for Blender MCP."""

from __future__ import annotations

from typing import Any, Dict, List

import bpy



def _ensure_material(name: str) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (400, 0)
    return material



def _find_output(material: bpy.types.Material):
    for node in material.node_tree.nodes:
        if node.bl_idname == "ShaderNodeOutputMaterial":
            return node
    return material.node_tree.nodes.new(type="ShaderNodeOutputMaterial")



def get_status() -> Dict[str, Any]:
    return {"status": "ready", "features": ["procedural", "variation", "keyword_ai"]}



def generate_procedural_material(params: Dict[str, Any]) -> Dict[str, Any]:
    material_type = str(params.get("material_type") or "organic")
    name = str(params.get("name") or "ProceduralMaterial")
    parameters = dict(params.get("parameters") or {})
    scale = float(parameters.get("scale", 6.0))
    roughness = float(parameters.get("roughness", 0.45))

    material = _ensure_material(name)
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = _find_output(material)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (180, 0)
    tex = nodes.new(type="ShaderNodeTexNoise" if material_type in {"wood", "organic", "terrain"} else "ShaderNodeTexVoronoi")
    tex.location = (-400, 40)
    tex.inputs["Scale"].default_value = scale if "Scale" in tex.inputs else scale
    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.location = (-120, 40)

    palette = {
        "wood": ([0.18, 0.09, 0.03, 1.0], [0.55, 0.28, 0.12, 1.0]),
        "stone": ([0.18, 0.18, 0.18, 1.0], [0.65, 0.65, 0.62, 1.0]),
        "metal": ([0.25, 0.25, 0.27, 1.0], [0.75, 0.74, 0.72, 1.0]),
        "fabric": ([0.12, 0.14, 0.2, 1.0], [0.5, 0.52, 0.65, 1.0]),
        "terrain": ([0.12, 0.08, 0.04, 1.0], [0.24, 0.2, 0.1, 1.0]),
        "organic": ([0.22, 0.18, 0.14, 1.0], [0.68, 0.55, 0.42, 1.0]),
    }
    left, right = palette.get(material_type, palette["organic"])
    ramp.color_ramp.elements[0].color = left
    ramp.color_ramp.elements[1].color = right

    bsdf.inputs["Roughness"].default_value = roughness
    if material_type == "metal":
        bsdf.inputs["Metallic"].default_value = 0.85
    if material_type == "fabric":
        bsdf.inputs["Sheen Weight"].default_value = 0.35 if "Sheen Weight" in bsdf.inputs else 0.0

    links.new(tex.outputs[0], ramp.inputs[0])
    links.new(ramp.outputs[0], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs[0], output.inputs["Surface"])

    return {"status": "success", "material_name": name, "material_type": material_type}



def ai_generate_material(params: Dict[str, Any]) -> Dict[str, Any]:
    description = str(params.get("description") or "")
    name = str(params.get("name") or "AIMaterial")
    inferred_type = "organic"
    keyword_map = {
        "wood": "wood",
        "oak": "wood",
        "stone": "stone",
        "rock": "stone",
        "metal": "metal",
        "steel": "metal",
        "cloth": "fabric",
        "fabric": "fabric",
        "ground": "terrain",
        "soil": "terrain",
    }
    lowered = description.lower()
    for keyword, material_type in keyword_map.items():
        if keyword in lowered:
            inferred_type = material_type
            break
    result = generate_procedural_material({"material_type": inferred_type, "name": name})
    result["description"] = description
    result["inferred_type"] = inferred_type
    return result



def create_material_variations(params: Dict[str, Any]) -> Dict[str, Any]:
    base_material_name = str(params.get("base_material") or "").strip()
    variation_count = int(params.get("variation_count", 5))
    variation_type = str(params.get("variation_type") or "color")

    base_material = bpy.data.materials.get(base_material_name)
    if not base_material:
        raise ValueError(f"Base material not found: {base_material_name}")

    created: List[str] = []
    for index in range(1, max(variation_count, 1) + 1):
        variant = base_material.copy()
        variant.name = f"{base_material_name}_{variation_type}_{index:02d}"
        if variant.use_nodes:
            principled = next((node for node in variant.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
            if principled:
                if variation_type == "roughness":
                    principled.inputs["Roughness"].default_value = min(1.0, 0.15 * index)
                else:
                    color = principled.inputs["Base Color"].default_value
                    principled.inputs["Base Color"].default_value = [
                        min(1.0, color[0] + (0.04 * index)),
                        min(1.0, color[1] + (0.02 * index)),
                        min(1.0, color[2] + (0.01 * index)),
                        color[3],
                    ]
        created.append(variant.name)
    return {"status": "success", "created": created, "variation_type": variation_type}
