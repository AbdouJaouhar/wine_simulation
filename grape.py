# This script uses bmesh operators to make 2 links of a chain.

import bpy
import bmesh
import math
import mathutils
from mathutils import Vector
from random import randint, uniform, seed


seed(10)

def get_base(bm, verts, number=12):
    distance_function = lambda i : 0.1
    
    theta_bound = (-math.pi,math.pi)
    phi_bound = (-math.pi/8, math.pi/8)
    
    
    vertices_base = []
    for i in range(number):
        ret = bmesh.ops.extrude_vert_indiv(bm, verts=verts)

        for v in ret['verts']:
            x = distance_function(i) * math.sin(uniform(*phi_bound)) * math.cos(uniform(*theta_bound))
            y = distance_function(i) * math.sin(uniform(*phi_bound)) * math.sin(uniform(*theta_bound))
            z = - distance_function(i) * math.cos(uniform(*phi_bound))
            
            v.co += Vector([x,y,z])
        verts = ret['verts']
        vertices_base.append(verts[0])
        
    print(vertices_base)
    return vertices_base

def generate_next(bm, verts, generation=1, base_angle=0.2):
    ret = bmesh.ops.extrude_vert_indiv(bm, verts=verts)
    ret2 = bmesh.ops.extrude_vert_indiv(bm, verts=verts)

    for v in ret['verts']:
        v.co += Vector([uniform(-0.2,0.2)/generation,uniform(-0.2,0.2)/generation,-uniform(0.1,0.2)/generation])
        
    for v in ret2['verts']:
        v.co += Vector([uniform(-0.2,0.2)/generation,uniform(-0.2,0.2)/generation,-uniform(0.05,0.15)/generation])
        
    return [*ret['verts'], *ret2['verts']]

# Make a new BMesh
bm = bmesh.new()

ret = [bm.verts.new((0,0,0))]

def get_childs(bm, ret, n_gen=5):
    for i in range(1,n_gen):
        ret = generate_next(bm, ret, i)
        
    return ret

vertices_base = get_base(bm, ret)

finitions = []
for vert in vertices_base:
    ret = [vert]
    ret = get_childs(bm, ret)
    finitions = [*finitions, *ret]

grappes = []
for i, vert in enumerate(finitions):
    mesh = bpy.data.meshes.new(f'baie_{i}')


    # Construct the bmesh sphere and assign it to the blender mesh.
    bm_temp = bmesh.new()
    bmesh.ops.create_uvsphere(bm_temp, u_segments=32, v_segments=16, diameter=0.03)
    bmesh.ops.translate(
        bm_temp,
        verts=bm_temp.verts,
        vec=vert.co.to_tuple()
    )
    
    bm_temp.to_mesh(mesh)
    bm_temp.free()

    obj_grappe_temp = bpy.data.objects.new(f'baie_{i}', mesh)
#    obj_grappe_temp.location = vert.co
    bpy.context.collection.objects.link(obj_grappe_temp)
    obj_grappe_temp.select_set(True)
    bpy.ops.object.shade_smooth()
    grappes.append(obj_grappe_temp)


# Finish up, write the bmesh into a new mesh
me = bpy.data.meshes.new("Mesh")
bm.to_mesh(me)
bm.free()


# Add the mesh to the scene
obj = bpy.data.objects.new("Object", me)
bpy.context.collection.objects.link(obj)

# Select and make active
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.modifier_add(type='SKIN')
bpy.ops.object.modifier_add(type='SUBSURF')
bpy.context.object.modifiers["Subdivision"].levels = 4

bpy.ops.object.editmode_toggle()
bpy.ops.mesh.select_all(action='SELECT')

bpy.ops.transform.skin_resize(value=(0.02,0.02,0.02), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=True, proportional_edit_falloff='SMOOTH', proportional_size=0.564474, use_proportional_connected=False, use_proportional_projected=False)

bpy.ops.object.editmode_toggle()