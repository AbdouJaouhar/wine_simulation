from typing import *
from dataclasses import dataclass, field
import bpy
import bmesh
import math
import mathutils
from mathutils import Vector
from random import randint, uniform, seed


@dataclass
class GrapeLSystem:
    m: int = 5
    ns: List[int] = field(default_factory=list)
    l: float = 1
    rl: float = 1
    rr: float = 0.75
    alpha: float = 45
    position_base = (0,0,0) 
    phi = 0
    theta = 0

    def extract_rules(self, string):
        replacements = []
        for k, c in enumerate(string):
            if c == "A" and k < len(string)-1 and string[k+1] in ["r", "f", "e", "p"]:
                next_string = string[k:].split(")")[0]
                i = int(float(next_string[3:].split(',')[0]))

                if string[k+1] != "e" and string[k+1] != "p":
                    j = int((next_string[3:].split(',')[1]))

                if string[k+1] == "r":
                    if i == 1:
                        new_comand = f"Ae({int(j*self.rl)})"
                    if i > 1:
                        print(i)
                        new_comand = f"F({j})[//Ar({i-1}, {int(j*self.rl)})][+({self.alpha})Af({self.ns[i-2]}, {int(j*self.rl)})]"

                if string[k+1] == "f":
                    if i > 1:
                        new_comand = f"F({j})[//Af({i-1}, {int(j*self.rl)})][+({self.alpha})Ae({j*self.rl})]"
                    if i == 1:
                        new_comand = f"Ae({int(j*self.rl)})"

                if string[k+1] == "e":
                    new_comand = f"F({i})[Ap({int(i*self.rl)})][+({self.alpha})Ap({int(i*self.rl)})][-({self.alpha})Ap({int(i*self.rl)})]"

                if string[k+1] == "p":
                    new_comand = f"F({i})S({int(self.l*self.rr)})"

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
        omega = f"Ar({self.m},{self.l})"

        for iteration in range(n_iter):
            omega = self.extract_rules(omega)
        self.instructions = omega
    
    def draw_segment(self, state, length):
        verts, phi, theta = state
        ret = bmesh.ops.extrude_vert_indiv(self.mesh_branch, verts=verts)
        
        x = length * math.sin(phi) * math.cos(theta)
        y = length * math.sin(phi) * math.sin(theta)
        z = - length * math.cos(phi)
        
        ret['verts'][0].co += Vector([x,y,z])
        
        return ret['verts'], phi, theta
        
    def draw(self, speed=1000):
        cursor = 0
        stack = []
        self.mesh_branch = bmesh.new()
        verts = [self.mesh_branch.verts.new(self.position_base)]
        
        phi = self.phi
        theta = self.theta
        
        while cursor < len(self.instructions):
            char = self.instructions[cursor]
            temp_string = self.instructions[cursor:]
            
            if char == "F":
                param = int(float(temp_string[2:].split(')')[0]))
                self.draw_segment([verts, phi, theta], param)
            elif char == "/":
                stack.append([verts, self.phi, self.theta])
                pass
            elif char == "[":
                stack.append([verts, phi, theta])
            elif char == "]":
                verts, phi, theta = stack.pop()

            elif char == "+":
                param = int(float(temp_string[2:].split(')')[0]))
                phi+=param
            elif char == "-":
                param = int(float(temp_string[2:].split(')')[0]))
                theta+=param
            elif char == "S":
                pass

            cursor += 1

        pass
    
    def show(self):
        me = bpy.data.meshes.new("branches")
        self.mesh_branch.to_mesh(me)
        self.mesh_branch.free()


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

grappe = GrapeLSystem(m=3, ns=[1, 2])
grappe.iterate(n_iter=10)
grappe.draw()
grappe.show()
