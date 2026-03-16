"""
================================================================================
SPICE MARKET SCENE - COMPLETE PRODUCTION-READY IMPLEMENTATION
Execute this script in Blender's Scripting editor
================================================================================
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector, noise

# ==============================================================================
# CONFIGURATION
# ==============================================================================
random.seed(42)

SCENE_CONFIG = {
    "corridor_width": 4.0,
    "corridor_length": 22.0,
    "corridor_height": 4.5,
    "stall_count": 7,
}

SPICE_PALETTE = {
    "turmeric": (0.88, 0.65, 0.08),
    "paprika": (0.72, 0.12, 0.06),
    "chili": (0.65, 0.10, 0.05),
    "cumin": (0.55, 0.35, 0.15),
    "coriander": (0.42, 0.28, 0.12),
    "cardamom": (0.28, 0.38, 0.22),
    "cinnamon": (0.58, 0.32, 0.10),
    "clove": (0.32, 0.18, 0.10),
    "saffron": (0.95, 0.68, 0.12),
    "peppercorn": (0.15, 0.12, 0.10),
    "mustard": (0.78, 0.72, 0.18),
    "ginger": (0.68, 0.45, 0.15),
    "sesame": (0.88, 0.82, 0.68),
    "nigella": (0.12, 0.12, 0.12),
    "sumac": (0.58, 0.12, 0.18),
    "curry": (0.72, 0.42, 0.12),
}

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def clear_scene():
    """Clear the scene completely."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clean up unused data blocks
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for coll in list(bpy.data.collections):
        if coll.users == 0:
            bpy.data.collections.remove(coll)
    
    print("Scene cleared")

def create_collection(name, parent=None):
    """Create or get a collection."""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    
    coll = bpy.data.collections.new(name)
    if parent:
        parent.children.link(coll)
    else:
        bpy.context.scene.collection.children.link(coll)
    return coll

def add_bevel(obj, width=0.002, segments=2):
    """Add bevel modifier for realistic edges."""
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = width
    bevel.segments = segments
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = 0.5236

def add_subsurf(obj, levels=2):
    """Add subdivision surface."""
    subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = levels
    subsurf.render_levels = levels + 1

# ==============================================================================
# MATERIALS
# ==============================================================================

def create_spice_material(name, base_color):
    """Create photorealistic spice powder material."""
    mat = bpy.data.materials.new(name=f"Spice_{name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.85
    bsdf.inputs['Specular'].default_value = 0.25
    bsdf.inputs['Subsurface'].default_value = 0.03
    bsdf.inputs['Subsurface Color'].default_value = (*base_color, 1.0)
    
    # Noise for variation
    noise_tex = nodes.new('ShaderNodeTexNoise')
    noise_tex.location = (-400, -200)
    noise_tex.inputs['Scale'].default_value = 20.0
    noise_tex.inputs['Detail'].default_value = 8.0
    
    # Color ramp for variation
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (-200, -200)
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[0].color = (*[c * 0.9 for c in base_color], 1.0)
    ramp.color_ramp.elements[1].color = (*[min(c * 1.1, 1.0) for c in base_color], 1.0)
    
    # Bump
    bump = nodes.new('ShaderNodeBump')
    bump.location = (-200, -400)
    bump.inputs['Strength'].default_value = 0.08
    
    # Links
    links.new(noise_tex.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(noise_tex.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_wood_material(name="Wood_Aged"):
    """Create aged wood material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf.inputs['Base Color'].default_value = (0.22, 0.15, 0.10, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.78
    
    # Wood grain
    wave = nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.inputs['Scale'].default_value = 4.0
    wave.inputs['Distortion'].default_value = 0.4
    
    links.new(wave.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_plaster_material(name="Plaster_Worn"):
    """Create worn plaster material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.72, 0.68, 0.58, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.92
    return mat

def create_brass_material(name="Brass_Worn"):
    """Create worn brass material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf.inputs['Base Color'].default_value = (0.70, 0.42, 0.15, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.38
    
    # Scratches
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 30.0
    
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.35, 0.22, 0.08, 1.0)
    ramp.color_ramp.elements[1].color = (0.78, 0.52, 0.20, 1.0)
    
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_fabric_material(name, color):
    """Create fabric material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.88
    return mat

def create_ceramic_material(name, color=(0.92, 0.88, 0.78)):
    """Create ceramic material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.32
    bsdf.inputs['Specular'].default_value = 0.45
    return mat

def create_stone_floor_material():
    """Create stone floor material."""
    mat = bpy.data.materials.new(name="Stone_Floor")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.42, 0.40, 0.36, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.82
    return mat

# ==============================================================================
# ARCHITECTURE
# ==============================================================================

def build_corridor():
    """Build the main corridor structure."""
    coll = create_collection("Architecture")
    
    w = SCENE_CONFIG["corridor_width"]
    l = SCENE_CONFIG["corridor_length"]
    h = SCENE_CONFIG["corridor_height"]
    
    plaster_mat = create_plaster_material()
    stone_mat = create_stone_floor_material()
    
    # Floor
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, l/2, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.scale = (w/2, l/2, 1)
    floor.data.materials.append(stone_mat)
    coll.objects.link(floor)
    bpy.context.scene.collection.objects.unlink(floor)
    
    # Left wall
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-w/2, l/2, h/2))
    wall_l = bpy.context.active_object
    wall_l.name = "Wall_Left"
    wall_l.scale = (0.05, l/2, h/2)
    wall_l.rotation_euler = (0, math.radians(90), 0)
    wall_l.data.materials.append(plaster_mat)
    coll.objects.link(wall_l)
    bpy.context.scene.collection.objects.unlink(wall_l)
    
    # Right wall
    bpy.ops.mesh.primitive_plane_add(size=1, location=(w/2, l/2, h/2))
    wall_r = bpy.context.active_object
    wall_r.name = "Wall_Right"
    wall_r.scale = (0.05, l/2, h/2)
    wall_r.rotation_euler = (0, math.radians(-90), 0)
    wall_r.data.materials.append(plaster_mat)
    coll.objects.link(wall_r)
    bpy.context.scene.collection.objects.unlink(wall_r)
    
    print("Corridor built")
    return coll

# ==============================================================================
# STALLS
# ==============================================================================

def create_stall(stall_idx, y_pos, side, stall_type):
    """Create a complete stall."""
    coll = create_collection(f"Stall_{stall_idx:02d}")
    
    w = SCENE_CONFIG["corridor_width"]
    
    x_pos = side * (w/2 - 0.7)
    counter_height = 0.9
    
    wood_mat = create_wood_material()
    
    # Counter
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, y_pos, counter_height/2))
    counter = bpy.context.active_object
    counter.name = f"Stall_{stall_idx}_Counter"
    counter.scale = (1.1, 0.65, counter_height/2)
    counter.data.materials.append(wood_mat)
    add_bevel(counter)
    coll.objects.link(counter)
    bpy.context.scene.collection.objects.unlink(counter)
    
    # Counter top
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, y_pos, counter_height + 0.02))
    top = bpy.context.active_object
    top.name = f"Stall_{stall_idx}_Top"
    top.scale = (1.15, 0.7, 0.02)
    top.data.materials.append(wood_mat)
    coll.objects.link(top)
    bpy.context.scene.collection.objects.unlink(top)
    
    # Awning
    awning_colors = [
        (0.88, 0.65, 0.22),
        (0.75, 0.35, 0.15),
        (0.45, 0.35, 0.55),
        (0.65, 0.55, 0.32),
    ]
    awning_color = awning_colors[stall_idx % len(awning_colors)]
    fabric_mat = create_fabric_material(f"Fabric_{stall_idx}", awning_color)
    
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x_pos + side * 0.25, y_pos, 3.3))
    awning = bpy.context.active_object
    awning.name = f"Stall_{stall_idx}_Awning"
    awning.scale = (1.4, 0.9, 1)
    awning.rotation_euler = (math.radians(random.uniform(-3, 3)), 0, 0)
    awning.data.materials.append(fabric_mat)
    coll.objects.link(awning)
    bpy.context.scene.collection.objects.unlink(awning)
    
    return {
        "collection": coll,
        "counter_loc": (x_pos, y_pos, counter_height),
        "side": side,
        "type": stall_type
    }

# ==============================================================================
# CONTAINERS & SPICES
# ==============================================================================

def create_brass_bowl(location, radius, name):
    """Create a brass bowl."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=20, ring_count=12)
    bowl = bpy.context.active_object
    bowl.name = name
    
    # Flatten
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.resize(value=(1, 1, 0.45))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    brass_mat = create_brass_material()
    bowl.data.materials.append(brass_mat)
    add_bevel(bowl, 0.001)
    
    return bowl

def create_spice_mound(location, spice_type, radius, name):
    """Create a spice mound."""
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius * 0.85,
        location=(location[0], location[1], location[2] + radius * 0.15),
        segments=16,
        ring_count=10
    )
    mound = bpy.context.active_object
    mound.name = name
    
    # Shape
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.resize(value=(1, 1, 0.55))
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Subsurf
    add_subsurf(mound, 2)
    
    # Displace
    displace = mound.modifiers.new(name="Displace", type='DISPLACE')
    displace.strength = 0.015
    tex = bpy.data.textures.new(name=f"Noise_{name}", type='NOISE')
    tex.noise_scale = 0.25
    displace.texture = tex
    
    # Material
    color = SPICE_PALETTE.get(spice_type, (0.5, 0.5, 0.5))
    mat = create_spice_material(spice_type, color)
    mound.data.materials.append(mat)
    
    return mound

def create_ceramic_jar(location, name):
    """Create a ceramic jar."""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.3, location=location, vertices=18)
    jar = bpy.context.active_object
    jar.name = name
    
    ceramic_mat = create_ceramic_material(name)
    jar.data.materials.append(ceramic_mat)
    
    return jar

# ==============================================================================
# HANGING GOODS
# ==============================================================================

def create_hanging_chilies(location, name):
    """Create hanging dried chilies."""
    coll = create_collection(name)
    
    # String
    bpy.ops.mesh.primitive_cylinder_add(radius=0.004, depth=0.7, location=location)
    string = bpy.context.active_object
    string.name = f"{name}_String"
    fabric_mat = create_fabric_material("String", (0.35, 0.28, 0.20))
    string.data.materials.append(fabric_mat)
    coll.objects.link(string)
    bpy.context.scene.collection.objects.unlink(string)
    
    # Chilies
    chili_mat = create_spice_material("chili", SPICE_PALETTE["chili"])
    for i in range(8):
        y_offset = random.uniform(-0.02, 0.02)
        z = location[2] - 0.25 - i * 0.06
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(location[0], location[1] + y_offset, z))
        chili = bpy.context.active_object
        chili.name = f"{name}_Chili_{i}"
        chili.scale = (1, 1, 2.8)
        chili.data.materials.append(chili_mat)
        coll.objects.link(chili)
        bpy.context.scene.collection.objects.unlink(chili)
    
    return coll

def create_garlic_braid(location, name):
    """Create garlic braid."""
    coll = create_collection(name)
    
    for i in range(5):
        z = location[2] - i * 0.1
        x = location[0] + random.uniform(-0.02, 0.02)
        y = location[1] + random.uniform(-0.02, 0.02)
        
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(x, y, z))
        garlic = bpy.context.active_object
        garlic.name = f"{name}_Garlic_{i}"
        garlic.scale = (1, 1, 1.25)
        
        mat = bpy.data.materials.new(f"Garlic_{i}")
        mat.use_nodes = True
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.92, 0.88, 0.78, 1.0)
        mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.68
        garlic.data.materials.append(mat)
        
        coll.objects.link(garlic)
        bpy.context.scene.collection.objects.unlink(garlic)
    
    return coll

# ==============================================================================
# LIGHTING
# ==============================================================================

def setup_lighting():
    """Setup cinematic lighting."""
    coll = create_collection("Lighting")
    
    # Sun
    bpy.ops.object.light_add(type='SUN', location=(8, -5, 12))
    sun = bpy.context.active_object
    sun.name = "Sun_Main"
    sun.data.energy = 7.5
    sun.data.color = (1.0, 0.85, 0.65)
    sun.rotation_euler = (math.radians(58), 0, math.radians(28))
    sun.data.angle = math.radians(6)
    coll.objects.link(sun)
    bpy.context.scene.collection.objects.unlink(sun)
    
    # Fill
    bpy.ops.object.light_add(type='AREA', location=(-2, 8, 3.5))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 1.8
    fill.data.color = (0.92, 0.88, 0.82)
    fill.data.size = 4.5
    fill.rotation_euler = (math.radians(-25), 0, math.radians(-18))
    coll.objects.link(fill)
    bpy.context.scene.collection.objects.unlink(fill)
    
    # Rim
    bpy.ops.object.light_add(type='AREA', location=(3, 6, 2.5))
    rim = bpy.context.active_object
    rim.name = "Rim_Light"
    rim.data.energy = 1.2
    rim.data.color = (1.0, 0.92, 0.78)
    rim.data.size = 2.5
    rim.rotation_euler = (math.radians(-15), 0, math.radians(42))
    coll.objects.link(rim)
    bpy.context.scene.collection.objects.unlink(rim)
    
    print("Lighting setup complete")
    return coll

# ==============================================================================
# CAMERAS
# ==============================================================================

def create_cameras():
    """Create all cinematic cameras."""
    coll = create_collection("Cameras")
    cameras = {}
    
    # Shot 1: Establishing
    bpy.ops.object.camera_add(location=(0, -2.5, 2.8))
    cam1 = bpy.context.active_object
    cam1.name = "CAM_Establishing"
    cam1.rotation_euler = (math.radians(78), 0, 0)
    cam1.data.lens = 30
    coll.objects.link(cam1)
    bpy.context.scene.collection.objects.unlink(cam1)
    cameras["establishing"] = cam1
    
    # Shot 2: Diagonal
    bpy.ops.object.camera_add(location=(1.4, 3, 1.5))
    cam2 = bpy.context.active_object
    cam2.name = "CAM_Diagonal"
    cam2.rotation_euler = (math.radians(82), 0, math.radians(-22))
    cam2.data.lens = 35
    cam2.data.dof.use_dof = True
    cam2.data.dof.focus_distance = 3.2
    cam2.data.dof.aperture_fstop = 2.8
    coll.objects.link(cam2)
    bpy.context.scene.collection.objects.unlink(cam2)
    cameras["diagonal"] = cam2
    
    # Shot 3: Macro
    bpy.ops.object.camera_add(location=(0.25, 6, 1.52))
    cam3 = bpy.context.active_object
    cam3.name = "CAM_Macro"
    cam3.rotation_euler = (math.radians(90), 0, 0)
    cam3.data.lens = 85
    cam3.data.dof.use_dof = True
    cam3.data.dof.focus_distance = 0.45
    cam3.data.dof.aperture_fstop = 1.8
    coll.objects.link(cam3)
    bpy.context.scene.collection.objects.unlink(cam3)
    cameras["macro"] = cam3
    
    # Shot 4: Hanging FG
    bpy.ops.object.camera_add(location=(0, 9, 2.3))
    cam4 = bpy.context.active_object
    cam4.name = "CAM_Hanging_FG"
    cam4.rotation_euler = (math.radians(86), 0, 0)
    cam4.data.lens = 42
    cam4.data.dof.use_dof = True
    cam4.data.dof.focus_distance = 5.5
    cam4.data.dof.aperture_fstop = 2.8
    coll.objects.link(cam4)
    bpy.context.scene.collection.objects.unlink(cam4)
    cameras["hanging_fg"] = cam4
    
    # Shot 5: Beauty
    bpy.ops.object.camera_add(location=(-0.4, 11, 1.85))
    cam5 = bpy.context.active_object
    cam5.name = "CAM_Beauty"
    cam5.rotation_euler = (math.radians(88), 0, math.radians(4))
    cam5.data.lens = 50
    cam5.data.dof.use_dof = True
    cam5.data.dof.focus_distance = 4.2
    cam5.data.dof.aperture_fstop = 2.8
    coll.objects.link(cam5)
    bpy.context.scene.collection.objects.unlink(cam5)
    cameras["beauty"] = cam5
    
    # Set active
    bpy.context.scene.camera = cam5
    
    print("Cameras created")
    return cameras

# ==============================================================================
# RENDER SETTINGS
# ==============================================================================

def setup_render():
    """Configure render settings."""
    scene = bpy.context.scene
    
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 512
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPTIX'
    
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - High Contrast'
    
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '16'
    
    print("Render settings configured")

# ==============================================================================
# MAIN BUILD
# ==============================================================================

def build_scene():
    """Build the complete spice market scene."""
    print("\n" + "="*70)
    print("SPICE MARKET SCENE - PRODUCTION BUILD")
    print("="*70 + "\n")
    
    # Setup
    clear_scene()
    setup_render()
    
    main_coll = create_collection("Spice_Market")
    
    # Architecture
    print("[1/7] Building corridor architecture...")
    arch_coll = build_corridor()
    main_coll.children.link(arch_coll)
    
    # Stalls
    print("[2/7] Creating stalls...")
    stalls_coll = create_collection("Stalls")
    main_coll.children.link(stalls_coll)
    
    stall_configs = [
        (2.5, -1, "bulk"),
        (5.5, 1, "premium"),
        (8.5, -1, "blends"),
        (11.5, 1, "herbs"),
        (14.5, -1, "goods"),
        (17.5, 1, "preserves"),
        (20.5, -1, "tea"),
    ]
    
    stalls = []
    for idx, (y_pos, side, s_type) in enumerate(stall_configs):
        stall = create_stall(idx + 1, y_pos, side, s_type)
        stalls.append(stall)
        stalls_coll.children.link(stall["collection"])
    
    # Props
    print("[3/7] Adding containers and spices...")
    props_coll = create_collection("Props")
    main_coll.children.link(props_coll)
    
    spice_list = list(SPICE_PALETTE.keys())
    spice_idx = 0
    
    for stall in stalls:
        cx, cy, cz = stall["counter_loc"]
        
        if stall["type"] == "bulk":
            for j in range(4):
                bx = cx + (j - 1.5) * 0.35
                bowl = create_brass_bowl((bx, cy, cz + 0.35), 0.16, f"Bowl_{stall['type']}_{j}")
                props_coll.objects.link(bowl)
                bpy.context.scene.collection.objects.unlink(bowl)
                
                spice = spice_list[spice_idx % len(spice_list)]
                mound = create_spice_mound((bx, cy, cz + 0.35), spice, 0.13, f"Mound_{spice}_{j}")
                props_coll.objects.link(mound)
                bpy.context.scene.collection.objects.unlink(mound)
                spice_idx += 1
                
        elif stall["type"] == "premium":
            for j in range(5):
                jx = cx + (j - 2) * 0.22
                jar = create_ceramic_jar((jx, cy, cz + 0.18), f"Jar_{j}")
                props_coll.objects.link(jar)
                bpy.context.scene.collection.objects.unlink(jar)
    
    # Hanging goods
    print("[4/7] Adding hanging goods...")
    hanging_coll = create_collection("Hanging")
    main_coll.children.link(hanging_coll)
    
    for i in range(8):
        y_pos = 3.5 + i * 2.3
        x_pos = random.choice([-1.25, 1.25])
        
        if i % 3 == 0:
            chilies = create_hanging_chilies((x_pos, y_pos, 3.8), f"Chilies_{i}")
            hanging_coll.children.link(chilies)
        elif i % 3 == 1:
            garlic = create_garlic_braid((x_pos + random.uniform(-0.15, 0.15), y_pos, 3.7), f"Garlic_{i}")
            hanging_coll.children.link(garlic)
    
    # Lighting
    print("[5/7] Setting up lighting...")
    light_coll = setup_lighting()
    main_coll.children.link(light_coll)
    
    # Cameras
    print("[6/7] Creating cameras...")
    cam_coll = create_collection("Cameras")
    main_coll.children.link(cam_coll)
    cameras = create_cameras()
    for cam in cameras.values():
        cam_coll.objects.link(cam)
        bpy.context.scene.collection.objects.unlink(cam)
    
    # Finalize
    print("[7/7] Finalizing...")
    
    # Stats
    obj_count = len(bpy.context.scene.objects)
    mat_count = len(bpy.data.materials)
    
    print("\n" + "="*70)
    print("BUILD COMPLETE!")
    print("="*70)
    print(f"Total objects: {obj_count}")
    print(f"Total materials: {mat_count}")
    print(f"Collections: Architecture, Stalls, Props, Hanging, Lighting, Cameras")
    print("\nCameras:")
    print("  - CAM_Establishing (wide establishing shot)")
    print("  - CAM_Diagonal (merchant-side diagonal)")
    print("  - CAM_Macro (hero texture shot)")
    print("  - CAM_Hanging_FG (hanging foreground)")
    print("  - CAM_Beauty (premium beauty shot)")
    print("\nActive camera: CAM_Beauty")
    print("="*70 + "\n")
    
    return main_coll

# ==============================================================================
# EXECUTE
# ==============================================================================

if __name__ == "__main__":
    build_scene()
