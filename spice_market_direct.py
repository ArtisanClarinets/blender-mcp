import bpy
import math
import random

# Set random seed for reproducibility
random.seed(42)

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Clean up
for mat in bpy.data.materials:
    if mat.users == 0:
        bpy.data.materials.remove(mat)

# Scene setup
WIDTH = 4.0
LENGTH = 22.0
HEIGHT = 4.5

# Materials
def create_spice_mat(name, color):
    mat = bpy.data.materials.new(name=f"Spice_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.8
    return mat

def create_wood_mat():
    mat = bpy.data.materials.new(name="Wood")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.25, 0.18, 0.12, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.75
    return mat

def create_plaster_mat():
    mat = bpy.data.materials.new(name="Plaster")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.75, 0.70, 0.60, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.9
    return mat

def create_brass_mat():
    mat = bpy.data.materials.new(name="Brass")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.72, 0.45, 0.18, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.35
    return mat

def create_fabric_mat(color):
    mat = bpy.data.materials.new(name="Fabric")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.85
    return mat

# Store materials
wood_mat = create_wood_mat()
plaster_mat = create_plaster_mat()
brass_mat = create_brass_mat()
fabric_mat = create_fabric_mat((0.85, 0.65, 0.25))

spice_colors = {
    "turmeric": (0.85, 0.65, 0.12),
    "paprika": (0.75, 0.15, 0.08),
    "cumin": (0.55, 0.35, 0.18),
    "saffron": (0.95, 0.65, 0.15),
}

spice_mats = {k: create_spice_mat(k, v) for k, v in spice_colors.items()}

# Create floor
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, LENGTH/2, 0))
floor = bpy.context.active_object
floor.name = "Floor"
floor.scale = (WIDTH/2, LENGTH/2, 1)
floor.data.materials.append(plaster_mat)

# Create walls
bpy.ops.mesh.primitive_plane_add(size=1, location=(-WIDTH/2, LENGTH/2, HEIGHT/2))
left_wall = bpy.context.active_object
left_wall.name = "Wall_Left"
left_wall.scale = (0.1, LENGTH/2, HEIGHT/2)
left_wall.rotation_euler = (0, math.radians(90), 0)
left_wall.data.materials.append(plaster_mat)

bpy.ops.mesh.primitive_plane_add(size=1, location=(WIDTH/2, LENGTH/2, HEIGHT/2))
right_wall = bpy.context.active_object
right_wall.name = "_Right"
right_wall.scale = (0.1, LENGTH/2, HEIGHT/2)
right_wall.rotation_euler = (0, math.radians(-90), 0)
right_wall.data.materials.append(plaster_mat)

# Create stalls
stall_positions = [2, 5, 8, 11, 14, 17, 20]
stall_types = ["bulk", "premium", "blends", "herbs", "goods", "preserves", "tea"]

for i, (y_pos, stall_type) in enumerate(zip(stall_positions, stall_types)):
    side = -1 if i % 2 == 0 else 1
    x_pos = side * (WIDTH/2 - 0.8)
    
    # Counter
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x_pos, y_pos, 0.45))
    counter = bpy.context.active_object
    counter.name = f"Stall_{i}_Counter"
    counter.scale = (1.0, 0.6, 0.45)
    counter.data.materials.append(wood_mat)
    
    # Awning
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x_pos + side * 0.2, y_pos, 3.2))
    awning = bpy.context.active_object
    awning.name = f"Stall_{i}_Awning"
    awning.scale = (1.3, 0.8, 1)
    awning.data.materials.append(fabric_mat)
    
    # Add spice bowls for bulk stall
    if stall_type == "bulk":
        for j in range(3):
            bx = x_pos + (j - 1) * 0.4
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(bx, y_pos, 1.0))
            bowl = bpy.context.active_object
            bowl.name = f"Bowl_{i}_{j}"
            bowl.scale = (1, 1, 0.4)
            bowl.data.materials.append(brass_mat)
            
            # Spice mound
            spice_name = list(spice_colors.keys())[j % len(spice_colors)]
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(bx, y_pos, 1.08))
            mound = bpy.context.active_object
            mound.name = f"Spice_{i}_{j}"
            mound.scale = (1, 1, 0.5)
            mound.data.materials.append(spice_mats[spice_name])

# Create hanging chilies
for i in range(5):
    y_pos = 4 + i * 3.5
    x_pos = random.choice([-1.3, 1.3])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.015, location=(x_pos, y_pos, 3.5))
    chili = bpy.context.active_object
    chili.name = f"Chili_{i}"
    chili.scale = (1, 1, 3)
    mat = create_spice_mat("chili", (0.75, 0.15, 0.08))
    chili.data.materials.append(mat)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(8, -5, 12))
sun = bpy.context.active_object
sun.name = "Sun"
sun.data.energy = 8.0
sun.data.color = (1.0, 0.85, 0.65)
sun.rotation_euler = (math.radians(60), 0, math.radians(30))

bpy.ops.object.light_add(type='AREA', location=(-2, 8, 3))
fill = bpy.context.active_object
fill.name = "Fill"
fill.data.energy = 2.0
fill.data.size = 4.0

# Cameras
# Beauty shot
bpy.ops.object.camera_add(location=(-0.5, 10, 1.8))
cam = bpy.context.active_object
cam.name = "CAM_Beauty"
cam.rotation_euler = (math.radians(88), 0, math.radians(5))
cam.data.lens = 50
bpy.context.scene.camera = cam

# Render settings
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.cycles.samples = 256

print("Spice market scene created!")
print(f"Objects: {len(bpy.context.scene.objects)}")
