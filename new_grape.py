import bpy
import bmesh
import math
import mathutils
from mathutils import Vector
from random import randint, uniform, seed

class Grape(object):
    
    def __init__(self, ns= 6, position_base = (0,0,0), stage=1, mildiou_frequency=0.5, mildiou_intensity=0.5, number = 20):
        self.ns = ns
        self.position_base = position_base
        self.stage = stage
        self.mildiou_frequency = mildiou_frequency
        self.mildiou_intensity = mildiou_intensity
        self.number = number
        self.finitions = []
        
        for obj in bpy.data.objects:
            obj.select_set(False)
        
    def sigmoid(self, x, min_y, max_y, min_x, max_x, transform = lambda x : x):
        return (max_y-min_y)/(1+math.exp(-(transform(x)-(min_x+max_x)/2)))+min_y
    
    def distance_rachis(self, i):
        return self.sigmoid(self.number-i-1, 0.3, 1, 0,self.number+3)
    
    def distance_first_orders(self, i, rachis_index = 0):
        return self.sigmoid(self.number-i-1, 0.2, uniform(0.7,1.3), 0, 5, transform=lambda x: x)
        
    def generate_rachis(self, distance_function = None, theta_bound = (-math.pi,math.pi), phi_bound = (-math.pi/16, math.pi/16)):
        
        
        if distance_function is None:
            distance_function = self.distance_rachis
            
        self.mesh_branch = bmesh.new()
        verts = [self.mesh_branch.verts.new(self.position_base)]
        vertices_base = []
        
        for i in range(self.number):
            r = distance_function(i)
            ret = bmesh.ops.extrude_vert_indiv(self.mesh_branch, verts=verts)
            
            sign = lambda x: bool(x > 0) - bool(x < 0)
            phi = uniform(*phi_bound)
            theta = sign(uniform(-1,1))*90
            theta = 0
            phi = 0
            
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.sin(phi) * math.sin(theta)
            z = - r * math.cos(phi)
            
            ret['verts'][0].co += Vector([x,y,z])
            verts = ret['verts']
            vertices_base.append(ret['verts'][0])
                
            
        self.vertices_base = vertices_base
        
    def generate_first_order_routine(self, verts, generation=1, index=1, distance_function = None, theta = 0, phi = 0):
        
        ret = bmesh.ops.extrude_vert_indiv(self.mesh_branch, verts=verts)
        
        if distance_function is None:
            distance_function = self.distance_first_orders
            
        r = distance_function(index)
        phi = phi
        
        for v in ret['verts']:
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.sin(phi) * math.sin(theta)
            z = - r * math.cos(phi)
            
            v.co += Vector([x,y,z])
             
        
        return ret['verts']
    
        
    def generate_first_order(self, index, theta, phi, theta_bound = (-math.pi, math.pi), phi_bound = (-math.pi/3, math.pi/3)):
        ret = [self.vertices_base[index]]
        n_second_order = math.ceil(6/(index+1))
        
        if n_second_order > 2:
            last = 1
        else:
            last = 0
            
        theta_second_order = uniform(*theta_bound)
        for i in range(n_second_order-last):
            current_theta = theta+index*2*math.pi/3
            current_theta = 0
            ret = self.generate_first_order_routine(ret, generation=i, index=index,theta=current_theta, phi=math.pi/4)
            
#            ret_second = self.generate_first_order_routine(
#                ret,
#                generation=1,
#                index=1,
#                distance_function = lambda _ : 1.4,
#                theta = theta_second_order+i*2*60,
#                phi = 0
#            )
#             
            self.finitions = [*self.finitions, *ret]
        
    def generate_first_orders(self, theta_bound = (-math.pi, math.pi), phi_bound = (0, math.pi/2)):
        sign = lambda x: bool(x > 0) - bool(x < 0)
        
        phi = uniform(*phi_bound)
        phi_sign = sign(phi)
        phi = phi_sign * max(abs(phi), 20)
        
        theta = uniform(*theta_bound)
        
        for i in range(len(self.vertices_base)-1):
            self.generate_first_order(i, theta, phi)
    
    def draw_bairies(self):
        grappes = []
        for i, vert in enumerate(self.finitions):
            mesh = bpy.data.meshes.new(f'baie_{vert.index}')


            # Construct the bmesh sphere and assign it to the blender mesh.
            bm_temp = bmesh.new()
            bmesh.ops.create_uvsphere(bm_temp, u_segments=32, v_segments=16, diameter=0.5)
            print(self.mesh_branch.verts)
            bmesh.ops.translate(
                bm_temp,
                verts=bm_temp.verts,
                vec=vert.co.to_tuple()
            )
            
            bm_temp.to_mesh(mesh)
            bm_temp.free()

            obj_grappe_temp = bpy.data.objects.new(f'baie_{i}', mesh)
            bpy.context.collection.objects.link(obj_grappe_temp)
            obj_grappe_temp.select_set(True)
            bpy.ops.object.shade_smooth()
            grappes.append(obj_grappe_temp)
        
    def construct_branches(self):
        me = bpy.data.meshes.new("branches")
        self.mesh_branch.to_mesh(me)
#        self.mesh_branch.free()


        # Add the mesh to the scene
        obj = bpy.data.objects.new("branches", me)
        bpy.context.collection.objects.link(obj)

        # Select and make active
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.modifier_add(type='SKIN')
        bpy.ops.object.modifier_add(type='SUBSURF')
        bpy.context.object.modifiers["Subdivision"].levels = 4
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        size = 0.1
        bpy.ops.transform.skin_resize(value=(size, size , size), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=True, proportional_edit_falloff='SMOOTH', proportional_size=0.564474, use_proportional_connected=False, use_proportional_projected=False)


        bpy.ops.object.editmode_toggle()

grape = Grape()
grape.generate_rachis()
grape.generate_first_orders()
#grape.draw_bairies()
grape.construct_branches()