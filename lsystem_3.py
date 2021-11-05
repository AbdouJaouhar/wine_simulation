import bpy
import bmesh
import operator
import mathutils
from dataclasses import dataclass, field
from copy import deepcopy
from typing import *
import math 

from random import randint, uniform, seed


@dataclass
class Turtle:
    start_point: Tuple[float] = (0, 0, 0)
    transform = mathutils.Matrix.Identity(4)

    def rotate(self, angle, vector):
        angle = math.radians(angle)
        self.transform = operator.matmul(
            self.transform, mathutils.Matrix.Rotation(angle, 4, vector))

    def rotate_x(self, angle):
        self.rotate(angle, mathutils.Vector((1.0, 0.0, 0.0)))

    def rotate_y(self, angle):
        self.rotate(angle, mathutils.Vector((0.0, 1.0, 0.0)))

    def rotate_z(self, angle):
        self.rotate(angle, mathutils.Vector((0.0, 0.0, 1.0)))

    def forward(self, length):
        vec = (0, 0, length)
        self.transform = operator.matmul(
            self.transform, mathutils.Matrix.Translation(vec))


@dataclass
class Drawer:
    start_point: Tuple[float] = (0, 0, 0)
    stack: List[Any] = field(default_factory=list)
    vertices: List[Any] = field(default_factory=list)
    pen_down: bool = False

    def __post_init__(self):
        self.bmesh = bmesh.new()
        self.vertices.append(self.bmesh.verts.new(self.start_point))

    def push_state(self, vertice, t):
        self.stack.append([vertice, deepcopy(t)])

    def pop_state(self):
        return self.stack.pop()

    def forward(self, t, length):

        vertice = self.bmesh.verts.new(operator.matmul(
            t.transform, mathutils.Vector((0, 0, length))))
        self.vertices.append(vertice)
#        self.connect(self.vertices[-2], self.vertices[-1])

        return vertice

    def connect(self, v1, v2):
        self.bmesh.edges.new((v1, v2))

    def exec(self):
        me = bpy.data.meshes.new("branches")
        self.bmesh.to_mesh(me)

        obj = bpy.data.objects.new("branches", me)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.modifier_add(type='SKIN')
        bpy.ops.object.modifier_add(type='SUBSURF')
        bpy.context.object.modifiers["Subdivision"].levels = 4

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        size = 0.1
        bpy.ops.transform.skin_resize(value=(size, size, size), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True,
                                      use_proportional_edit=True, proportional_edit_falloff='SMOOTH', proportional_size=0.564474, use_proportional_connected=False, use_proportional_projected=False)

        bpy.ops.object.editmode_toggle()

   
@dataclass
class GrapeLSystem:
    m: int = 5
    ns: List[int] = field(default_factory=list)
    l: float = 5
    rl: float = 1
    rr: float = 0.9
    alpha: float = 45
    
    alpha_y: float = 60
    alpha_r: float = 120
    wi: float = 1.5
    ni :int = 3
    position_base = (0,0,0) 
    phi = 0
    theta = 0
    lw = 3
    re = 0.6
    r_rr = 0.99
    r_rf = 0.89
    r_ff = 0.99
    r_p = 1.5
    r_e = 0.6
    r_w = 0.98
    
    def __post_init__(self):
        
        self.turtle = Turtle()
        self.drawer = Drawer(start_point=(0,0,0))

    def extract_rules(self, string):
        replacements = []
        faces_names = ["c", "v", "b", "n"]
        face_to_index = {"c" : 0, "v" : 1, "b" : 2, "n" : 3}
        face_to_rotation = {"c" : "//", "v" : "/", "b" : "//", "n" : "_"}
        
        for k, c in enumerate(string):
            if c == "A" and k < len(string)-1 and string[k+1] in ["b", "n", "c", "v", "f", "e", "p"]:
                next_string = string[k:].split(")")[0]
                params = next_string[3:].split(',')
                
                if string[k+1] == "e" or string[k+1] == "p":
                    l = float(params[0])
                    w = float(params[1])
                else:
                    i = float(params[0])
                    l = float(params[1])
                    w = float(params[2])

             
                if (string[k+1] == "c" or string[k+1] == "v" or string[k+1] == "b" or string[k+1] == "n" or string[k+1] == "f") and i == 1:
                    new_comand = f"Ae({l*self.re}, {w})"
                    
                elif (string[k+1] == "c" or string[k+1] == "v" or string[k+1] == "b" or string[k+1] == "n") and i > 1:
                    face_name = string[k+1]
                    new_face_name = faces_names[(face_to_index[face_name]+1)%4]
                    new_comand = f"E(0,0,0,{l},{w})[{face_to_rotation[face_name]}A{new_face_name}({i-1}, {l*self.r_rr},{w})][+({self.alpha_y})Af({self.ni},{l*self.r_rf},{w})]"
                elif string[k+1] == "f" and i > 1:
                    new_command = f"E(0,0,0,{l},{w})[_f({i-1},{l*self.r_ff},{w})][+({self.alpha_y})Ae({l*self.r_e},{w})]"
                    
                elif string[k+1] == "e":
                    new_comand = f"E(0,0,0,{l},{w})[Ap({l*self.r_p},{w})][+({self.alpha_y})/({self.alpha_r})Ap({l*self.r_p},{w})][-({self.alpha_y})_({self.alpha_r})Ap({l*self.r_p},{w})]"
                elif string[k+1] == "p":
                    new_comand = f"E(1,0,0,{l},{w})"
                replacements.append([k, k + len(next_string), new_comand])
                
            if c == "E":
                next_string = string[k:].split(")")[0]
                type, theta, phi, l, w = [float(p) for p in next_string[2:].split(',')]
                
                if type ==0:
                    new_comand = f"+({theta})&({phi})!({w*self.r_w})F({l})"
                else:
                    if l == self.lw:
                        new_comand = f"+({theta})&({phi})!({w*self.r_w})F({l})%"
                    else:
                        new_comand = f"+({theta})&({phi})!({w*self.r_w})F({l})S({uniform(2, self.lw)})"
                        
                replacements.append([k, k + len(next_string), new_comand])

        decalage = 0

        for replacement in replacements:
            start, end, new_comand = replacement
            length_diff = len(new_comand) - (end-start)

            before = string[:max(0, start+decalage)]
            after = string[min(end+decalage, len(string)):]

            string = before + new_comand + after

            decalage += length_diff

        return string

    def iterate(self, n_iter: int = 10):
        omega = f"Ac({self.m},{self.l}, {self.wi})"

        for iteration in range(n_iter):
            omega = self.extract_rules(omega)
        self.instructions = omega
        
    def draw(self):
        cursor = 0
        
        self.turtle.rotate_x(180)
        vertice = self.drawer.vertices[0]
        
        
        self.finitions = []
        ignore_next = False
        
        print(self.instructions)
        
        while cursor < len(self.instructions):
            char = self.instructions[cursor]
            temp_string = self.instructions[cursor:]
            if ignore_next:
                cursor +=1 
                ignore_next = False
            else:
                if char == "F":
                    param = float(temp_string[2:].split(')')[0])
                    self.turtle.forward(param)
                    vertice_old = vertice
                    vertice = self.drawer.forward(self.turtle, param)
                    self.drawer.connect(vertice_old, vertice)
                elif char == "/" and self.instructions[cursor+1] != "(":
                    self.turtle.rotate_z(60)
                elif char == "/" and self.instructions[cursor+1] == "(":
                    param = float(temp_string[2:].split(')')[0])
                    self.turtle.rotate_z(param)
                elif char == "_" and self.instructions[cursor+1] != "(":
                    self.turtle.rotate_z(-60)
                elif char == "_" and self.instructions[cursor+1] == "(":
                    param = float(temp_string[2:].split(')')[0])
                    self.turtle.rotate_z(-param)
                elif char == "[":
                    self.drawer.push_state(vertice, self.turtle)
                elif char == "]":
                    vertice, self.turtle = self.drawer.pop_state()
                    
                elif char == "+" and self.instructions[cursor+1] == "(":
                    param = float(temp_string[2:].split(')')[0])
                    self.turtle.rotate_x(param)
                elif char == "-" and self.instructions[cursor+1] == "(":
                    param = float(temp_string[2:].split(')')[0])
                    self.turtle.rotate_x(-param)
                elif char == "&" and self.instructions[cursor+1] != "(":
                    turtle.rotate_y(60)
                elif char == "&" and self.instructions[cursor+1] == "(":
                    param = float(temp_string[2:].split(')')[0])
                    self.turtle.rotate_y(param)
                    
                elif char == "^" and self.instructions[cursor+1] != "(":
                    self.turtle.rotate_y(-60)
                elif char == "^" and self.instructions[cursor+1] == "(":
                    param = float(temp_string[2:].split(')')[0])
                    self.turtle.rotate_y(-param)
                elif char == "S":
                    size = float(temp_string[2:].split(')')[0])
                    self.finitions = [*self.finitions, [vertice, size]]
                    
                elif char == "%":
                    ignore_next = True

                cursor += 1


    
    def draw_bairies(self):
        grappes = []
        for i, (vert, size) in enumerate(self.finitions):
            mesh = bpy.data.meshes.new(f'baie_{vert.index}')


            # Construct the bmesh sphere and assign it to the blender mesh.
            bm_temp = bmesh.new()
            bmesh.ops.create_uvsphere(bm_temp, u_segments=32, v_segments=16, diameter=size/15)
           
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

grappe = GrapeLSystem(m=7, l=0.3, wi=3, ni=1)
grappe.iterate(n_iter=15)
grappe.draw()
grappe.draw_bairies()
grappe.drawer.exec()