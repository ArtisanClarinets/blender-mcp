"""Advanced material and shading handlers for Blender MCP addon.

Implements PBR enhancements, subsurface scattering, volume materials, and anisotropic shaders.
"""

import bpy
import structlog
from typing import Any, Dict, List, Optional

from ...exceptions import BlenderMCPError

logger = structlog.get_logger(__name__)

def get_status() -> Dict[str, Any]:
    """Get advanced materials system status."""
    logger.info("Getting advanced materials status")
    return {
        "status": "ready",
        "features": {
            "subsurface_scattering": True,
            "volume_materials": True,
            "anisotropic_materials": True,
            "layered_materials": True,
        },
    }

def create_subsurface_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create subsurface scattering material for organic surfaces."""
    name = params.get("name")
    if not name:
        raise BlenderMCPError("name is required")

    base_color = params.get("base_color", [0.8, 0.8, 0.8])
    subsurface_color = params.get("subsurface_color", [0.8, 0.4, 0.2])
    subsurface_radius = params.get("subsurface_radius", [1.0, 0.2, 0.1])
    subsurface_weight = params.get("subsurface_weight", 0.5)
    subsurface_scale = params.get("subsurface_scale", 1.0)

    for color_list, color_name in [
        (base_color, "base_color"),
        (subsurface_color, "subsurface_color"),
        (subsurface_radius, "subsurface_radius"),
    ]:
        if not isinstance(color_list, list) or len(color_list) != 3:
            raise BlenderMCPError(f"{color_name} must be a list of 3 values [r, g, b]")
        for val in color_list:
            if not 0 <= val <= 1:
                raise BlenderMCPError(f"{color_name} values must be between 0 and 1")

    if not 0 <= subsurface_weight <= 1:
        raise BlenderMCPError("subsurface_weight must be between 0 and 1")

    if subsurface_scale <= 0:
        raise BlenderMCPError("subsurface_scale must be greater than 0")

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")

    if not bsdf:
        raise BlenderMCPError(
            f"Failed to create Principled BSDF node for material: {name}"
        )

    bsdf.inputs["Base Color"].default_value = base_color + [1.0]
    bsdf.inputs["Subsurface Weight"].default_value = subsurface_weight
    bsdf.inputs["Subsurface Color"].default_value = subsurface_color + [1.0]
    bsdf.inputs["Subsurface Radius"].default_value = subsurface_radius
    bsdf.inputs["Subsurface Scale"].default_value = subsurface_scale

    logger.info("Created subsurface material", name=name)
    return {
        "status": "success",
        "material_name": name,
        "type": "subsurface",
        "properties": {
            "base_color": base_color,
            "subsurface_weight": subsurface_weight,
            "subsurface_scale": subsurface_scale,
        },
    }

def create_volume_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create volume material for clouds, smoke, fire effects."""
    name = params.get("name")
    if not name:
        raise BlenderMCPError("name is required")

    volume_type = params.get("volume_type", "cloud")
    density = params.get("density", 1.0)
    color = params.get("color", [1.0, 1.0, 1.0])
    emission_strength = params.get("emission_strength", 0.0)

    valid_volume_types = ["cloud", "smoke", "fire", "fog"]
    if volume_type not in valid_volume_types:
        raise BlenderMCPError(f"volume_type must be one of: {valid_volume_types}")

    if not isinstance(color, list) or len(color) != 3:
        raise BlenderMCPError("color must be a list of 3 values [r, g, b]")
    for val in color:
        if not 0 <= val <= 1:
            raise BlenderMCPError("color values must be between 0 and 1")

    if density <= 0:
        raise BlenderMCPError("density must be greater than 0")

    if emission_strength < 0:
        raise BlenderMCPError("emission_strength must be non-negative")

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output = nodes.get("Material Output")
    if not output:
        raise BlenderMCPError(
            f"Failed to create Material Output node for material: {name}"
        )

    volume_scatter = nodes.new("ShaderNodeVolumeScatter")
    volume_scatter.inputs["Density"].default_value = density
    volume_scatter.inputs["Color"].default_value = color + [1.0]

    links.new(volume_scatter.outputs["Volume"], output.inputs["Volume"])

    if volume_type == "fire" and emission_strength > 0:
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = [1.0, 0.5, 0.0, 1.0]
        emission.inputs["Strength"].default_value = emission_strength

        mix_shader = nodes.new("ShaderNodeMixShader")
        mix_shader.inputs["Fac"].default_value = 0.5

        links.new(volume_scatter.outputs["Volume"], mix_shader.inputs[1])
        links.new(emission.outputs["Emission"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], output.inputs["Volume"])

    logger.info("Created volume material", name=name, type=volume_type)
    return {
        "status": "success",
        "material_name": name,
        "volume_type": volume_type,
        "properties": {
            "density": density,
            "color": color,
            "emission_strength": emission_strength if volume_type == "fire" else None,
        },
    }

def create_anisotropic_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create anisotropic material for hair, fabric, brushed metal."""
    name = params.get("name")
    if not name:
        raise BlenderMCPError("name is required")

    base_color = params.get("base_color", [0.8, 0.8, 0.8])
    anisotropic = params.get("anisotropic", 0.5)
    anisotropic_rotation = params.get("anisotropic_rotation", 0.0)
    roughness = params.get("roughness", 0.3)
    metallic = params.get("metallic", 0.0)

    if not isinstance(base_color, list) or len(base_color) != 3:
        raise BlenderMCPError("base_color must be a list of 3 values [r, g, b]")
    for val in base_color:
        if not 0 <= val <= 1:
            raise BlenderMCPError("base_color values must be between 0 and 1")

    if not -1 <= anisotropic <= 1:
        raise BlenderMCPError("anisotropic must be between -1 and 1")

    if not 0 <= anisotropic_rotation <= 1:
        raise BlenderMCPError("anisotropic_rotation must be between 0 and 1")

    if not 0 <= roughness <= 1:
        raise BlenderMCPError("roughness must be between 0 and 1")

    if not 0 <= metallic <= 1:
        raise BlenderMCPError("metallic must be between 0 and 1")

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")

    if not bsdf:
        raise BlenderMCPError(
            f"Failed to create Principled BSDF node for material: {name}"
        )

    bsdf.inputs["Base Color"].default_value = base_color + [1.0]
    bsdf.inputs["Anisotropic"].default_value = anisotropic
    bsdf.inputs["Anisotropic Rotation"].default_value = anisotropic_rotation
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    logger.info("Created anisotropic material", name=name)
    return {
        "status": "success",
        "material_name": name,
        "type": "anisotropic",
        "properties": {
            "base_color": base_color,
            "anisotropic": anisotropic,
            "roughness": roughness,
            "metallic": metallic,
        },
    }

def create_layered_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create layered material with multiple material layers."""
    name = params.get("name")
    if not name:
        raise BlenderMCPError("name is required")

    layers = params.get("layers", [])

    if not isinstance(layers, list):
        raise BlenderMCPError("layers must be a list")

    if len(layers) == 0:
        logger.warning(f"Creating layered material '{name}' with no layers")

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output = nodes.get("Material Output")
    if not output:
        raise BlenderMCPError(
            f"Failed to create Material Output node for material: {name}"
        )

    previous_shader = None

    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            logger.warning(f"Skipping invalid layer {i}: not a dictionary")
            continue

        layer_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        layer_bsdf.name = f"Layer_{i}_BSDF"
        layer_bsdf.label = f"Layer {i}"

        if "base_color" in layer:
            color = layer["base_color"]
            if isinstance(color, list) and len(color) == 3:
                layer_bsdf.inputs["Base Color"].default_value = color + [1.0]

        if "roughness" in layer:
            layer_bsdf.inputs["Roughness"].default_value = layer["roughness"]

        if "metallic" in layer:
            layer_bsdf.inputs["Metallic"].default_value = layer["metallic"]

        if previous_shader is None:
            links.new(layer_bsdf.outputs["BSDF"], output.inputs["Surface"])
            previous_shader = layer_bsdf
        else:
            mix_shader = nodes.new("ShaderNodeMixShader")
            mix_shader.name = f"Layer_Mix_{i}"

            mix_factor = layer.get("mix_factor", 0.5)
            if not 0 <= mix_factor <= 1:
                mix_factor = 0.5
            mix_shader.inputs["Fac"].default_value = mix_factor

            links.new(previous_shader.outputs["BSDF"], mix_shader.inputs[1])
            links.new(layer_bsdf.outputs["BSDF"], mix_shader.inputs[2])

            if i == len(layers) - 1:
                links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])

            previous_shader = mix_shader

    if previous_shader is None:
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    layer_count = len([n for n in nodes if "Layer_" in n.name])
    logger.info("Created layered material", name=name, layers=layer_count)
    return {
        "status": "success",
        "material_name": name,
        "layer_count": len(layers),
        "layers_processed": layer_count,
    }

def create_hair_material(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a simplified physically-inspired hair material."""
    name = params.get("name")
    if not name:
        raise BlenderMCPError("name is required")

    base_color = params.get("base_color", [0.18, 0.12, 0.08])
    roughness = float(params.get("roughness", 0.3))
    radial_roughness = float(params.get("radial_roughness", 0.1))
    coat = float(params.get("coat", 0.0))
    ior = float(params.get("ior", 1.55))
    melanin = float(params.get("melanin", 0.5))
    melanin_redness = float(params.get("melanin_redness", 0.0))

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)

    shader_type = "ShaderNodeBsdfHairPrincipled"
    hair = (
        nodes.new(shader_type)
        if hasattr(bpy.types, "ShaderNodeBsdfHairPrincipled")
        else nodes.new("ShaderNodeBsdfPrincipled")
    )
    hair.location = (0, 0)

    if hair.bl_idname == "ShaderNodeBsdfHairPrincipled":
        if "Color" in hair.inputs:
            hair.inputs["Color"].default_value = base_color + [1.0]
        if "Roughness" in hair.inputs:
            hair.inputs["Roughness"].default_value = roughness
        if "Radial Roughness" in hair.inputs:
            hair.inputs["Radial Roughness"].default_value = radial_roughness
        if "Coat" in hair.inputs:
            hair.inputs["Coat"].default_value = coat
        if "IOR" in hair.inputs:
            hair.inputs["IOR"].default_value = ior
        if "Melanin" in hair.inputs:
            hair.inputs["Melanin"].default_value = melanin
        if "Melanin Redness" in hair.inputs:
            hair.inputs["Melanin Redness"].default_value = melanin_redness
    else:
        hair.inputs["Base Color"].default_value = base_color + [1.0]
        hair.inputs["Roughness"].default_value = roughness
        if "Coat Weight" in hair.inputs:
            hair.inputs["Coat Weight"].default_value = coat
        if "IOR" in hair.inputs:
            hair.inputs["IOR"].default_value = ior

    links.new(hair.outputs[0], output.inputs["Surface"])
    logger.info("Created hair material", name=name)
    return {
        "status": "success",
        "material_name": name,
        "type": "hair",
        "properties": {
            "roughness": roughness,
            "radial_roughness": radial_roughness,
            "melanin": melanin,
            "melanin_redness": melanin_redness,
        },
    }