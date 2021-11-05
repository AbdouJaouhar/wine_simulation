import bpy
import bmesh
import operator
import mathutils
from dataclasses import dataclass, field
from copy import deepcopy
from typing import *
import math 



@dataclass
class Turtle:
    start_point: Tuple[float] = (0, 0, 0)
    transform = mathutils.Matrix.Identity(4)

    def rotate(self, angle, vector):
        #        angle = math.radians(angle)
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
    l: float = 1
    rl: float = 1
    rr: float = 0.75
    alpha: float = 45
    position_base = (0,0,0) 
    phi = 0
    theta = 0
    w = 0.1
    lw = 1/6

    def extract_rules(self, string):
        replacements = []
        for k, c in enumerate(string):
            if c == "A" and k < len(string)-1 and string[k+1] in ["r", "f", "e", "p"]:
                next_string = string[k:].split(")")[0]
                i = int(float(next_string[3:].split(',')[0]))

                if string[k+1] != "e" and string[k+1] != "p":
                    j = float((next_string[3:].split(',')[1]).replace(" ", ""))

                if string[k+1] == "r":
                    if i == 1:
                        new_comand = f"Ae({int(j*self.rl)})"
                    if i > 1:
                        new_comand = f"E(0,0,{self.l})[//Ar({i-1},{j*self.rl})][+({self.alpha})Af({self.ns[i-2]},{j*self.rl})]"

                if string[k+1] == "f":
                    if i > 1:
                        new_comand = f"E(0,0,{self.l})[//Af({i-1},{j*self.rl})][+({self.alpha})Ae({j*self.rl})]"
                    if i == 1:
                        new_comand = f"Ae({int(j*self.rl)})"

                if string[k+1] == "e":
                    new_comand = f"E(0,0,{self.l})[Ap({int(i*self.rl)})][+({self.alpha})Ap({int(i*self.rl)})][-({self.alpha})Ap({int(i*self.rl)})]"

                if string[k+1] == "p":
                    new_comand = f"E(1,0,{self.l})S({int(self.l*self.rr)})"
                
                
                replacements.append([k, k + len(next_string), new_comand])
                    
            if c == "E":
                next_string = string[k:].split(")")[0]
                type, theta, l = [float(p) for p in next_string[2:].split(',')]
                
                if type == 0:
                    new_comand = f"+({theta})!({self.w})F({l})"
                else:
                    if l == self.lw:
                        new_comand = f"+({theta})!({self.w})F({l})%"
                    else:
                        new_comand = f"+({theta})!({self.w})F({l})S({self.l*self.rr})"
#                new_comand = f"F({l})"     
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
        
    def draw(self):
        cursor = 0
        
        turtle = Turtle()
        drawer = Drawer(start_point=(0,0,0))
        turtle.rotate_x(math.pi)
        vertice = drawer.vertices[0]
        
        
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
                    turtle.forward(param)
                    vertice_old = vertice
                    vertice = drawer.forward(turtle, param)
                    drawer.connect(vertice_old, vertice)
                elif char == "/" and self.instructions[cursor+1] != "(":
                    turtle.rotate_z(math.pi/2)
                elif char == "[":
                    drawer.push_state(vertice, turtle)
                elif char == "]":
                    vertice, turtle = drawer.pop_state()
                elif char == "+":
                    param = float(temp_string[2:].split(')')[0])
                    turtle.rotate_x(math.radians(param))
                elif char == "-":
                    param = float(temp_string[2:].split(')')[0])
                    turtle.rotate_x(math.radians(-param))
                elif char == "S":
                    self.finitions = [*self.finitions, vertice]
                    
                elif char == "%":
                    ignore_next = True

                cursor += 1

        drawer.exec()

    

ns = [1,2]
grappe = GrapeLSystem(m=3, ns=ns, l=1)
grappe.iterate(n_iter=20)
grappe.draw()