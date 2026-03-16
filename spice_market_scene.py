"""
Production-Quality Spice Market Scene Generator for Blender MCP
This script creates a complete, photoreal cinematic 3D spice market environment.
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler
from bpy_extras import mesh_utils

# =============================================================================
# SCENE CONFIGURATION
# =============================================================================

SCENE_CONFIG = {
    "corridor_width": 4.0,
    "corridor_length": 22.0,
    "corridor_height": 4.5,
    "stall_count": 7,
    "sun_position": (8, -5, 12),
    "sun_energy": 8.0,
    "sun_color": (1.0, 0.85, 0.65),
}

# Spice color definitions (RGB)
SPICE_COLORS = {
    "turmeric": (0.85, 0.65, 0.12),
    "paprika": (0.75, 0.15, 0.08),
    "chili_powder": (0.65, 0.12, 0.06),
    "cumin": (0.55, 0.35, 0.18),
    "coriander": (0.42, 0.28, 0.15),
    "cardamom": (0.25, 0.35, 0.22),
    "cinnamon": (0.55, 0.30, 0.12),
    "clove": (0.35, 0.20, 0.12),
    "saffron": (0.95, 0.65, 0.15),
    "peppercorn": (0.15, 0.12, 0.10),
    "mustard": (0.75, 0.70, 0.20),
    "ginger": (0.65, 0.45, 0.18),
    "sesame": (0.85, 0.80, 0.65),
    "nigella": (0.12, 0.12, 0.12),
    "sumac": (0.55, 0.12, 0.15),
    "curry": (0.70, 0.45, 0.15),
    "tea": (0.35, 0.50, 0.25),
    "rose": (0.65, 0.35, 0.45),
    "mint": (0.35, 0.55, 0.35),
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clear_scene():
    """Clear all mesh objects, materials, and collections."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clean up materials
    for material in bpy.data.materials:
        if material.users == 0:
            bpy.data.materials.remove(material)
    
    # Clean up meshes
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    
    print("Scene cleared")

def create_collection(name, parent=None):
    """Create a new collection."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    
    collection = bpy.data.collections.new(name)
    if parent:
        parent.children.link(collection)
    else:
        bpy.context.scene.collection.children.link(collection)
    return collection

def apply_transforms(obj):
    """Apply all transforms to an object."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def add_bevel_modifier(obj, width=0.002, segments=2):
    """Add bevel modifier for realistic edges."""
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = width
    bevel.segments = segments
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = 0.5236  # 30 degrees

def add_subsurf_modifier(obj, levels=2):
    """Add subdivision surface modifier."""
    subsurf = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    subsurf.levels = levels
    subsurf.render_levels = levels + 1

# =============================================================================
# MATERIAL CREATION
# =============================================================================

def create_spice_material(name, base_color, roughness=0.8, bump_strength=0.1):
    """Create a realistic spice powder material."""
    mat = bpy.data.materials.new(name=f"Spice_{name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Specular'].default_value = 0.3
    bsdf.inputs['Subsurface'].default_value = 0.05
    bsdf.inputs['Subsurface Color'].default_value = (*base_color, 1.0)
    
    # Noise for variation
    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-400, -200)
    noise.inputs['Scale'].default_value = 15.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Roughness'].default_value = 0.6
    
    # Color variation
    color_ramp = nodes.new('ShaderNodeValToRGB')
    color_ramp.location = (-200, -200)
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[1].position = 0.6
    color_ramp.color_ramp.elements[0].color = (*[c * 0.85 for c in base_color], 1.0)
    color_ramp.color_ramp.elements[1].color = (*[min(c * 1.15, 1.0) for c in base_color], 1.0)
    
    # Bump for texture
    bump = nodes.new('ShaderNodeBump')
    bump.location = (-200, -400)
    bump.inputs['Strength'].default_value = bump_strength
    
    # Links
    links = mat.node_tree.links
    links.new(noise.outputs['Fac'], color_ramp.inputs['Fac'])
    links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_aged_wood_material(name="Aged_Wood"):
    """Create aged wood material for stalls."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    # Wood color - aged brown
    bsdf.inputs['Base Color'].default_value = (0.25, 0.18, 0.12, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.75
    bsdf.inputs['Specular'].default_value = 0.2
    
    # Wood grain noise
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 8.0
    noise.inputs['Detail'].default_value = 6.0
    
    # Wave texture for grain
    wave = nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.inputs['Scale'].default_value = 3.0
    wave.inputs['Distortion'].default_value = 0.3
    
    links = mat.node_tree.links
    links.new(wave.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_worn_plaster_material(name="Worn_Plaster"):
    """Create worn plaster wall material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    # Cream/beige plaster
    bsdf.inputs['Base Color'].default_value = (0.75, 0.70, 0.60, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.9
    
    # Dirt and wear
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 5.0
    
    links = mat.node_tree.links
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_brass_material(name="Brass", worn=True):
    """Create brass/bronze container material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    # Brass color
    bsdf.inputs['Base Color'].default_value = (0.72, 0.45, 0.18, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.35 if worn else 0.15
    
    # Scratches and wear
    if worn:
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 25.0
        noise.inputs['Detail'].default_value = 8.0
        
        color_ramp = nodes.new('ShaderNodeValToRGB')
        color_ramp.color_ramp.elements[0].color = (0.4, 0.25, 0.1, 1.0)  # Darker worn areas
        color_ramp.color_ramp.elements[1].color = (0.8, 0.55, 0.22, 1.0)  # Shiny brass
        
        links = mat.node_tree.links
        links.new(noise.outputs['Fac'], color_ramp.inputs['Fac'])
        links.new(color_ramp.outputs['Color'], bsdf.inputs['Base Color'])
    
    links = mat.node_tree.links
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_ceramic_material(name="Ceramic", color=(0.9, 0.85, 0.75)):
    """Create ceramic jar material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.3
    bsdf.inputs['Specular'].default_value = 0.5
    
    links = mat.node_tree.links
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_fabric_material(name="Fabric", color=(0.7, 0.5, 0.2)):
    """Create fabric awning material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.85
    
    # Fabric weave texture
    wave = nodes.new('ShaderNodeTexWave')
    wave.inputs['Scale'].default_value = 50.0
    
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.02
    
    links = mat.node_tree.links
    links.new(wave.outputs['Color'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_stone_floor_material(name="Stone_Floor"):
    """Create worn stone/tile floor material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf.inputs['Base Color'].default_value = (0.45, 0.42, 0.38, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.8
    
    links = mat.node_tree.links
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

# =============================================================================
# ARCHITECTURE CREATION
# =============================================================================

def create_corridor_shell():
    """Create the main corridor structure."""
    collection = create_collection("Architecture")
    
    width = SCENE_CONFIG["corridor_width"]
    length = SCENE_CONFIG["corridor_length"]
    height = SCENE_CONFIG["corridor_height"]
    
    # Floor - worn stone tiles
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, length/2, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.scale = (width/2, length/2, 1)
    floor.data.materials.append(create_stone_floor_material())
    collection.objects.link(floor)
    bpy.context.scene.collection.objects.unlink(floor)
    
    # Left wall with irregularities
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-width/2, length/2, height/2))
    left_wall = bpy.context.active_object
    left_wall.name = "Wall_Left"
    left_wall.scale = (0.1, length/2, height/2)
    left_wall.rotation_euler = (0, math.radians(90), 0)
    left_wall.data.materials.append(create_worn_plaster_material())
    collection.objects.link(left_wall)
    bpy.context.scene.collection.objects.unlink(left_wall)
    
    # Right wall
    bpy.ops.mesh.primitive_plane_add(size=1, location=(width/2, length/2, height/2))
    right_wall = bpy.context.active_object
    right_wall.name = "Wall_Right"
    right_wall.scale = (0.1, length/2, height/2)
    right_wall.rotation_euler = (0, math.radians(-90), 0)
    right_wall.data.materials.append(create_worn_plaster_material())
    collection.objects.link(right_wall)
    bpy.context.scene.collection.objects.unlink(right_wall)
    
    # Ceiling/awning structure
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, length/2, height))
    ceiling = bpy.context.active_object
    ceiling.name = "Ceiling"
    ceiling.scale = (width/2, length/2, 1)
    ceiling.data.materials.append(create_fabric_material("Ceiling_Fabric", (0.6, 0.45, 0.25)))
    collection.objects.link(ceiling)
    bpy.context.scene.collection.objects.unlink(ceiling)
    
    print("Corridor shell created")
    return collection

# =============================================================================
# STALL CREATION
# =============================================================================

def create_stall_counter(location, width, depth, height, name="Stall_Counter"):
    """Create a stall counter with storage."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    counter = bpy.context.active_object
    counter.name = name
    counter.scale = (width/2, depth/2, height/2)
    counter.data.materials.append(create_aged_wood_material())
    add_bevel_modifier(counter, width=0.005)
    
    # Counter top
    top_loc = (location[0], location[1], location[2] + height/2 + 0.02)
    bpy.ops.mesh.primitive_cube_add(size=1, location=top_loc)
    top = bpy.context.active_object
    top.name = f"{name}_Top"
    top.scale = (width/2 + 0.05, depth/2 + 0.05, 0.02)
    top.data.materials.append(create_aged_wood_material())
    
    return counter

def create_shelving_unit(location, width, height, depth, tiers=3, name="Shelves"):
    """Create shelving unit for stall."""
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    
    # Vertical supports
    for side in [-1, 1]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(location[0] + side * width/2, location[1], location[2] + height/2))
        support = bpy.context.active_object
        support.name = f"{name}_Support_{side}"
        support.scale = (0.03, depth/2, height/2)
        support.data.materials.append(create_aged_wood_material())
        collection.objects.link(support)
        bpy.context.scene.collection.objects.unlink(support)
    
    # Horizontal shelves
    for i in range(tiers):
        shelf_height = location[2] + (i + 1) * (height / (tiers + 0.5))
        bpy.ops.mesh.primitive_cube_add(size=1, location=(location[0], location[1], shelf_height))
        shelf = bpy.context.active_object
        shelf.name = f"{name}_Shelf_{i}"
        shelf.scale = (width/2 + 0.02, depth/2, 0.015)
        shelf.data.materials.append(create_aged_wood_material())
        collection.objects.link(shelf)
        bpy.context.scene.collection.objects.unlink(shelf)
    
    return collection

def create_stall_structure(stall_index, position_along_corridor, side):
    """Create a complete stall with all elements."""
    collection = create_collection(f"Stall_{stall_index:02d}")
    
    width = random.uniform(1.8, 2.5)
    depth = random.uniform(1.0, 1.5)
    counter_height = 0.9
    
    x_pos = side * (SCENE_CONFIG["corridor_width"]/2 - depth/2 - 0.3)
    y_pos = position_along_corridor
    
    # Counter
    counter_loc = (x_pos, y_pos, counter_height/2)
    counter = create_stall_counter(counter_loc, width, depth, counter_height, f"Stall_{stall_index}_Counter")
    collection.objects.link(counter)
    bpy.context.scene.collection.objects.unlink(counter)
    
    # Shelving behind counter
    shelf_loc = (x_pos, y_pos - depth/2 - 0.2, counter_height)
    shelves = create_shelving_unit(shelf_loc, width * 0.9, 1.8, 0.4, tiers=random.randint(2, 4), name=f"Stall_{stall_index}_Shelves")
    collection.children.link(shelves)
    
    # Awning/canopy
    awning_loc = (x_pos + side * 0.3, y_pos, 3.2)
    bpy.ops.mesh.primitive_plane_add(size=1, location=awning_loc)
    awning = bpy.context.active_object
    awning.name = f"Stall_{stall_index}_Awning"
    awning.scale = (width/2 + 0.3, depth/2 + 0.4, 1)
    awning.rotation_euler = (math.radians(random.uniform(-5, 5)), 0, 0)
    
    # Random awning colors
    awning_colors = [
        (0.85, 0.65, 0.25),  # Saffron
        (0.75, 0.35, 0.15),  # Rust
        (0.45, 0.35, 0.55),  # Faded indigo
        (0.65, 0.55, 0.35),  # Olive
    ]
    color = random.choice(awning_colors)
    awning.data.materials.append(create_fabric_material(f"Awning_{stall_index}", color))
    collection.objects.link(awning)
    bpy.context.scene.collection.objects.unlink(awning)
    
    return {
        "collection": collection,
        "counter_location": counter_loc,
        "counter_size": (width, depth, counter_height),
        "shelf_location": shelf_loc,
        "side": side
    }

# =============================================================================
# CONTAINER CREATION
# =============================================================================

def create_brass_bowl(location, radius, name="Brass_Bowl"):
    """Create a brass bowl for spices."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, ring_count=16, segments=24)
    bowl = bpy.context.active_object
    bowl.name = name
    
    # Flatten bottom
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.resize(value=(1, 1, 0.4))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    bowl.data.materials.append(create_brass_material(f"{name}_Mat"))
    add_bevel_modifier(bowl, width=0.001)
    
    return bowl

def create_ceramic_jar(location, height, radius, name="Ceramic_Jar"):
    """Create a ceramic jar."""
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=location, vertices=20)
    jar = bpy.context.active_object
    jar.name = name
    
    # Taper the top slightly
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    jar.data.materials.append(create_ceramic_material(f"{name}_Mat"))
    
    return jar

def create_woven_basket(location, width, height, name="Basket"):
    """Create a woven basket."""
    bpy.ops.mesh.primitive_cylinder_add(radius=width/2, depth=height, location=location, vertices=16)
    basket = bpy.context.active_object
    basket.name = name
    
    # Taper
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.resize(value=(1.15, 1.15, 1))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    basket.data.materials.append(create_fabric_material(f"{name}_Mat", (0.55, 0.40, 0.22)))
    
    return basket

# =============================================================================
# SPICE MOUND CREATION
# =============================================================================

def create_spice_mound(location, spice_type, container_radius, name="Spice_Mound"):
    """Create a realistic spice mound."""
    # Create base dome
    mound_height = container_radius * random.uniform(0.4, 0.7)
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=container_radius * 0.85,
        location=(location[0], location[1], location[2] + container_radius * 0.2),
        ring_count=12,
        segments=20
    )
    mound = bpy.context.active_object
    mound.name = f"{name}_{spice_type}"
    
    # Flatten bottom and shape
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.resize(value=(1, 1, 0.5))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Add noise displacement for organic look
    subsurf = mound.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2
    
    displace = mound.modifiers.new(name="Displace", type='DISPLACE')
    displace.strength = 0.02
    displace.mid_level = 0.5
    
    # Create texture for displacement
    tex = bpy.data.textures.new(name=f"{spice_type}_noise", type='NOISE')
    tex.noise_scale = 0.3
    tex.noise_depth = 2
    displace.texture = tex
    
    # Apply material
    color = SPICE_COLORS.get(spice_type, (0.5, 0.5, 0.5))
    mat = create_spice_material(spice_type, color)
    mound.data.materials.append(mat)
    
    return mound

# =============================================================================
# HANGING GOODS
# =============================================================================

def create_hanging_chilies(location, length, name="Hanging_Chilies"):
    """Create a string of hanging dried chilies."""
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    
    # Main string
    bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=length, location=location)
    string = bpy.context.active_object
    string.name = f"{name}_String"
    string.data.materials.append(create_fabric_material("String", (0.4, 0.3, 0.2)))
    collection.objects.link(string)
    bpy.context.scene.collection.objects.unlink(string)
    
    # Individual chilies
    chili_count = int(length * 8)
    for i in range(chili_count):
        t = i / chili_count
        chili_loc = (location[0] + random.uniform(-0.02, 0.02), 
                     location[1] + random.uniform(-0.02, 0.02),
                     location[2] - t * length + length/2)
        
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=chili_loc)
        chili = bpy.context.active_object
        chili.name = f"{name}_Chili_{i}"
        chili.scale = (1, 1, 2.5)
        
        # Red chili material
        mat = create_spice_material("chili", SPICE_COLORS["chili_powder"])
        chili.data.materials.append(mat)
        collection.objects.link(chili)
        bpy.context.scene.collection.objects.unlink(chili)
    
    return collection

def create_garlic_braid(location, name="Garlic_Braid"):
    """Create a braided garlic hanging."""
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    
    # Garlic heads
    for i in range(6):
        garlic_loc = (location[0] + random.uniform(-0.03, 0.03),
                      location[1] + random.uniform(-0.03, 0.03),
                      location[2] - i * 0.12)
        
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=garlic_loc)
        garlic = bpy.context.active_object
        garlic.name = f"{name}_Garlic_{i}"
        garlic.scale = (1, 1, 1.3)
        
        # Garlic material - white with papery texture
        mat = bpy.data.materials.new(f"Garlic_{i}")
        mat.use_nodes = True
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.85, 0.75, 1.0)
        mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.7
        garlic.data.materials.append(mat)
        
        collection.objects.link(garlic)
        bpy.context.scene.collection.objects.unlink(garlic)
    
    return collection

def create_herb_bundle(location, name="Herb_Bundle"):
    """Create a hanging bundle of dried herbs."""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=0.4, location=location)
    bundle = bpy.context.active_object
    bundle.name = name
    
    # Green/brown herb material
    mat = create_spice_material("herbs", (0.25, 0.4, 0.2))
    bundle.data.materials.append(mat)
    
    return bundle

# =============================================================================
# LIGHTING SETUP
# =============================================================================

def setup_lighting():
    """Create cinematic lighting for the spice market."""
    collection = create_collection("Lighting")
    
    # Main sun light - warm directional
    bpy.ops.object.light_add(type='SUN', location=SCENE_CONFIG["sun_position"])
    sun = bpy.context.active_object
    sun.name = "Sun_Main"
    sun.data.energy = SCENE_CONFIG["sun_energy"]
    sun.data.color = SCENE_CONFIG["sun_color"]
    sun.rotation_euler = (math.radians(60), 0, math.radians(30))
    sun.data.angle = math.radians(8)  # Soft shadows
    collection.objects.link(sun)
    bpy.context.scene.collection.objects.unlink(sun)
    
    # Fill light - softer bounce simulation
    bpy.ops.object.light_add(type='AREA', location=(-2, 8, 3))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 2.0
    fill.data.color = (0.9, 0.85, 0.8)
    fill.data.size = 4.0
    fill.rotation_euler = (math.radians(-30), 0, math.radians(-20))
    collection.objects.link(fill)
    bpy.context.scene.collection.objects.unlink(fill)
    
    # Rim light for depth
    bpy.ops.object.light_add(type='AREA', location=(3, 5, 2))
    rim = bpy.context.active_object
    rim.name = "Rim_Light"
    rim.data.energy = 1.5
    rim.data.color = (1.0, 0.9, 0.75)
    rim.data.size = 2.0
    rim.rotation_euler = (math.radians(-20), 0, math.radians(45))
    collection.objects.link(rim)
    bpy.context.scene.collection.objects.unlink(rim)
    
    print("Lighting setup complete")
    return collection

# =============================================================================
# CAMERA SETUP
# =============================================================================

def create_cameras():
    """Create the 5 required cinematic cameras."""
    collection = create_collection("Cameras")
    cameras = {}
    
    # Shot 1 - Establishing push-in
    bpy.ops.object.camera_add(location=(0, -3, 2.5))
    cam1 = bpy.context.active_object
    cam1.name = "CAM_Establishing"
    cam1.rotation_euler = (math.radians(75), 0, 0)
    cam1.data.lens = 28
    collection.objects.link(cam1)
    bpy.context.scene.collection.objects.unlink(cam1)
    cameras["establishing"] = cam1
    
    # Shot 2 - Merchant-side diagonal
    bpy.ops.object.camera_add(location=(1.5, 2, 1.4))
    cam2 = bpy.context.active_object
    cam2.name = "CAM_Diagonal"
    cam2.rotation_euler = (math.radians(82), 0, math.radians(-25))
    cam2.data.lens = 35
    cam2.data.dof.use_dof = True
    cam2.data.dof.focus_distance = 3.0
    cam2.data.dof.aperture_fstop = 2.8
    collection.objects.link(cam2)
    bpy.context.scene.collection.objects.unlink(cam2)
    cameras["diagonal"] = cam2
    
    # Shot 3 - Macro/hero texture shot
    bpy.ops.object.camera_add(location=(0.3, 5, 1.55))
    cam3 = bpy.context.active_object
    cam3.name = "CAM_Macro"
    cam3.rotation_euler = (math.radians(90), 0, 0)
    cam3.data.lens = 85
    cam3.data.dof.use_dof = True
    cam3.data.dof.focus_distance = 0.5
    cam3.data.dof.aperture_fstop = 2.0
    collection.objects.link(cam3)
    bpy.context.scene.collection.objects.unlink(cam3)
    cameras["macro"] = cam3
    
    # Shot 4 - Hanging foreground shot
    bpy.ops.object.camera_add(location=(0, 8, 2.2))
    cam4 = bpy.context.active_object
    cam4.name = "CAM_Hanging_FG"
    cam4.rotation_euler = (math.radians(85), 0, 0)
    cam4.data.lens = 40
    cam4.data.dof.use_dof = True
    cam4.data.dof.focus_distance = 5.0
    cam4.data.dof.aperture_fstop = 2.8
    collection.objects.link(cam4)
    bpy.context.scene.collection.objects.unlink(cam4)
    cameras["hanging_fg"] = cam4
    
    # Shot 5 - Closing premium beauty shot
    bpy.ops.object.camera_add(location=(-0.5, 10, 1.8))
    cam5 = bpy.context.active_object
    cam5.name = "CAM_Beauty"
    cam5.rotation_euler = (math.radians(88), 0, math.radians(5))
    cam5.data.lens = 50
    cam5.data.dof.use_dof = True
    cam5.data.dof.focus_distance = 4.0
    cam5.data.dof.aperture_fstop = 2.8
    collection.objects.link(cam5)
    bpy.context.scene.collection.objects.unlink(cam5)
    cameras["beauty"] = cam5
    
    print("Cameras created")
    return cameras

# =============================================================================
# RENDER SETTINGS
# =============================================================================

def setup_render_settings():
    """Configure production render settings."""
    scene = bpy.context.scene
    
    # Engine
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    
    # Quality
    scene.cycles.samples = 512
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPTIX'
    
    # Resolution
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    
    # Color management
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - High Contrast'
    
    # Output
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '16'
    
    print("Render settings configured")

# =============================================================================
# MAIN SCENE ASSEMBLY
# =============================================================================

def build_spice_market():
    """Build the complete spice market scene."""
    print("=" * 60)
    print("BUILDING SPICE MARKET SCENE")
    print("=" * 60)
    
    # Clear and setup
    clear_scene()
    setup_render_settings()
    
    # Create main collections
    main_collection = create_collection("Spice_Market")
    
    # Build architecture
    print("\n[1/8] Creating corridor architecture...")
    arch_collection = create_corridor_shell()
    main_collection.children.link(arch_collection)
    
    # Create stalls
    print("\n[2/8] Creating stalls...")
    stalls_collection = create_collection("Stalls")
    main_collection.children.link(stalls_collection)
    
    stall_configs = [
        (2, "left", "bulk_spices"),
        (5, "right", "premium_spices"),
        (8, "left", "custom_blends"),
        (11, "right", "dried_herbs"),
        (14, "left", "dry_goods"),
        (17, "right", "preserves"),
        (20, "left", "tea_corner"),
    ]
    
    stalls = []
    for idx, (y_pos, side, stall_type) in enumerate(stall_configs):
        side_val = -1 if side == "left" else 1
        stall = create_stall_structure(idx + 1, y_pos, side_val)
        stalls.append((stall, stall_type))
        stalls_collection.children.link(stall["collection"])
    
    # Add containers and spices to stalls
    print("\n[3/8] Adding containers and spices...")
    props_collection = create_collection("Props")
    main_collection.children.link(props_collection)
    
    spice_types = list(SPICE_COLORS.keys())
    spice_idx = 0
    
    for stall, stall_type in stalls:
        counter_loc = stall["counter_location"]
        counter_width = stall["counter_size"][0]
        
        # Add containers based on stall type
        if stall_type == "bulk_spices":
            # Large brass bowls with bulk spices
            for i in range(4):
                x_offset = (i - 1.5) * 0.4
                bowl_loc = (counter_loc[0] + x_offset, counter_loc[1], counter_loc[2] + 0.5)
                bowl = create_brass_bowl(bowl_loc, 0.18, f"Bowl_Bulk_{i}")
                props_collection.objects.link(bowl)
                bpy.context.scene.collection.objects.unlink(bowl)
                
                # Add spice mound
                spice_type = spice_types[spice_idx % len(spice_types)]
                mound = create_spice_mound(bowl_loc, spice_type, 0.15, f"Mound_{spice_type}")
                props_collection.objects.link(mound)
                bpy.context.scene.collection.objects.unlink(mound)
                spice_idx += 1
                
        elif stall_type == "premium_spices":
            # Smaller premium containers
            for i in range(6):
                x_offset = (i - 2.5) * 0.25
                jar_loc = (counter_loc[0] + x_offset, counter_loc[1], counter_loc[2] + 0.25)
                jar = create_ceramic_jar(jar_loc, 0.25, 0.1, f"Jar_Premium_{i}")
                props_collection.objects.link(jar)
                bpy.context.scene.collection.objects.unlink(jar)
                
        elif stall_type == "dried_herbs":
            # Baskets with herbs
            for i in range(3):
                x_offset = (i - 1) * 0.5
                basket_loc = (counter_loc[0] + x_offset, counter_loc[1], counter_loc[2] + 0.2)
                basket = create_woven_basket(basket_loc, 0.25, 0.15, f"Basket_Herbs_{i}")
                props_collection.objects.link(basket)
                bpy.context.scene.collection.objects.unlink(basket)
    
    # Add hanging goods
    print("\n[4/8] Adding hanging goods...")
    hanging_collection = create_collection("Hanging_Goods")
    main_collection.children.link(hanging_collection)
    
    # Hang chilies and garlic at various points
    for i in range(8):
        y_pos = 3 + i * 2.2
        x_pos = random.choice([-1.2, 1.2])
        
        if i % 3 == 0:
            # Hanging chilies
            chilies = create_hanging_chilies((x_pos, y_pos, 3.8), 0.6, f"Chilies_{i}")
            hanging_collection.children.link(chilies)
        elif i % 3 == 1:
            # Garlic braid
            garlic = create_garlic_braid((x_pos + random.uniform(-0.2, 0.2), y_pos, 3.7), f"Garlic_{i}")
            hanging_collection.children.link(garlic)
        else:
            # Herb bundle
            herbs = create_herb_bundle((x_pos, y_pos, 3.6), f"Herbs_{i}")
            hanging_collection.objects.link(herbs)
            bpy.context.scene.collection.objects.unlink(herbs)
    
    # Setup lighting
    print("\n[5/8] Setting up lighting...")
    lighting_collection = setup_lighting()
    main_collection.children.link(lighting_collection)
    
    # Create cameras
    print("\n[6/8] Creating cameras...")
    cameras_collection = create_collection("Cameras")
    main_collection.children.link(cameras_collection)
    cameras = create_cameras()
    for cam in cameras.values():
        cameras_collection.objects.link(cam)
        bpy.context.scene.collection.objects.unlink(cam)
    
    # Set active camera to beauty shot
    bpy.context.scene.camera = cameras["beauty"]
    
    print("\n[7/8] Finalizing scene...")
    
    # Organize scene
    for obj in bpy.context.scene.collection.objects:
        if obj.name not in [o.name for o in main_collection.objects]:
            for child_coll in main_collection.children:
                if obj.name not in [o.name for o in child_coll.objects]:
                    pass  # Already organized
    
    print("\n[8/8] Scene build complete!")
    print("=" * 60)
    print(f"Total objects: {len(bpy.context.scene.objects)}")
    print(f"Total materials: {len(bpy.data.materials)}")
    print(f"Total collections: {len(bpy.data.collections)}")
    print("=" * 60)
    
    return main_collection

# =============================================================================
# EXECUTE
# =============================================================================

if __name__ == "__main__":
    build_spice_market()
