from typing import *
from dataclasses import dataclass, field
import bpy
import bmesh
import math
import mathutils
from mathutils import Vector
from random import randint, uniform, seed
from time import time
# https://github.com/krljg/lsystem/


class Pen():
    def __init__(self):
        self.radius = 0.1
        self.material = None

    def get_radius(self):
        return self.radius

    def set_radius(self, radius):
        self.radius = radius

    def get_material(self):
        return self.material

    def set_material(self, material):
        self.material = material

    def start(self, trans_mat):
        pass

    def move_and_draw(self, trans_mat):
        pass

    def move(self, trans_mat):
        pass

    def end(self):
        """Return a mesh"""
        return None

    def start_branch(self):
        pass

    def end_branch(self):
        return None

    def start_face(self):
        pass

    def end_face(self):
        return None


class BMeshPen(Pen):
    def __init__(self):
        Pen.__init__(self)
        self.bmesh = None
        self.last_vertices = None
        self.material = None
        self.stack = []

    def set_material(self, material):
        self.material = material

    def reset(self):
        self.bmesh = bmesh.new()
        self.stack = []

    def start(self, trans_mat):
        self.reset()
        self.last_vertices = self.create_vertices(trans_mat)

    def move_and_draw(self, trans_mat):
        new_vertices = self.create_vertices(trans_mat)
        new_faces = self.connect(self.last_vertices, new_vertices)
        self.last_vertices = new_vertices

        if self.material is not None:
            for f in new_faces:
                f.material_index = self.material

    def move(self, trans_mat):
        self.last_vertices = self.create_vertices(trans_mat)

    def end(self):
        """Return a mesh"""
        if not self.stack:
            if self.bmesh is None:  # end() can be called before start()
                return None
            mesh = bpy.data.meshes.new("lsystem.bmesh")
            self.bmesh.to_mesh(mesh)
            return mesh

        self.last_vertices, self.radius, self.material = self.stack.pop()
        return None

    def start_branch(self):
        self.stack.append((self.last_vertices, self.radius, self.material))

    def end_branch(self):
        return self.end()

    def create_vertices(self, trans_mat):
        raise Exception("create_vertices not implemented")

    def connect(self, last_vertices, new_vertices):
        raise Exception("connect not implemented")


class BLinePen(BMeshPen):
    def __init__(self):
        BMeshPen.__init__(self)

    def create_vertices(self, trans_mat):
        v1 = self.bmesh.verts.new(util.matmul(
            trans_mat, mathutils.Vector((self.radius, 0, 0))))
        v2 = self.bmesh.verts.new(util.matmul(
            trans_mat, mathutils.Vector((-self.radius, 0, 0))))
        return [v1, v2]

    def connect(self, last_vertices, new_vertices):
        return [self.bmesh.faces.new((last_vertices[0], last_vertices[1], new_vertices[1], new_vertices[0]))]


class BlObject:
    def __init__(self, radius, name="lsystem"):
        self.stack = []
        self.radius = radius
        self.pen = pen.CylPen(4)
        self.materials = []
        self.bmesh = bmesh.new()
        self.mesh = bpy.data.meshes.new(name)
        self.object = bpy.data.objects.new(self.mesh.name, self.mesh)
        self.last_indices = []

    def set_pen(self, name, transform):
        self.end_mesh_part()

        if name == "line":
            self.pen = BLinePen()
        else:
            print("No pen with name '"+name+"' found")
            return
        self.start_new_mesh_part(transform)

    def set_material(self, name):
        if name not in self.materials:
            self.materials.append(name)
            mat = bpy.data.materials.get(name)
            self.mesh.materials.append(mat)
        index = self.materials.index(name)
        self.pen.set_material(index)

    def scale_radius(self, scale):
        self.pen.set_radius(self.pen.get_radius() * scale)

    def set_radius(self, radius):
        self.pen.set_radius(radius)

    def get_radius(self):
        return self.pen.get_radius()

    def push(self, transform):
        t = (transform, self.pen)
        self.pen.start_branch()
        self.stack.append(t)

    def pop(self):
        if not self.stack:
            return None
        transform, pen = self.stack.pop()
        if self.pen is not pen:
            self.end_mesh_part()
        self.pen = pen
        mesh = self.pen.end_branch()
        if mesh is not None:
            self.bmesh.from_mesh(mesh)
        return transform

    def is_new_mesh_part(self):
        return self.last_indices is None

    def start_new_mesh_part(self, transform):
        self.end_mesh_part()
        self.pen.set_radius(self.radius)
        self.pen.start(transform)

    def end_mesh_part(self):
        # pen.end() will return a mesh if it's really the end and not just a branch closing
        new_mesh = self.pen.end()
        if new_mesh is not None:
            self.bmesh.from_mesh(new_mesh)

    def get_last_indices(self):
        return self.last_indices

    def set_last_indices(self, indices):
        self.last_indices = indices

    def finish(self, context):
        # print("turtle.finish")
        # print(str(self.pen))
        new_mesh = self.pen.end()
        if new_mesh is not None:
            self.bmesh.from_mesh(new_mesh)

        # me = bpy.data.meshes.new("lsystem")
        self.bmesh.to_mesh(self.mesh)
        base = util.link(context, self.object)

        return self.object, base

    def move_and_draw(self, transform):
        self.pen.move_and_draw(transform)

    def move(self, transform):
        self.pen.move(transform)


@dataclass
class Turtle:
    seed: int
    radius = 0.1
    angle = math.radians(25.7)
    length = 1.0
    expansion = 1.1
    shrinkage = 0.9
    fat = 1.2
    slinkage = 0.8
    transform = mathutils.Matrix.Identity(4)
    direction = (0.0, 0.0, 1.0)
    object_stack = []
    seed = seed
    tropism_vector = (0.0, 0.0, 0.0)
    tropism_force = 0
    sym_func_map = {}

    def set_radius(self, radius):
        self.radius = radius

    def set_angle(self, angle):
        self.angle = angle

    def set_length(self, length):
        self.length = length

    def set_expansion(self, expansion):
        self.expansion = expansion

    def set_shrinkage(self, shrinkage):
        self.shrinkage = shrinkage

    def set_fat(self, fat):
        self.fat = fat

    def set_slinkage(self, slinkage):
        self.slinkage = slinkage

    def set_direction(self, direction):
        self.direction = direction
        up = mathutils.Vector((0.0, 0.0, 1.0))
        old_direction = util.matmul(self.transform, up)
        quat = old_direction.rotation_difference(direction)
        rot_matrix = quat.to_matrix().to_4x4()
        self.transform = util.matmul(self.transform, rot_matrix)

    def rotate(self, angle, vector):
        self.transform = util.matmul(
            self.transform, mathutils.Matrix.Rotation(angle, 4, vector))

    def rotate_y(self, angle):
        self.rotate(angle, mathutils.Vector((0.0, 1.0, 0.0)))

    def rotate_x(self, angle):
        self.rotate(angle, mathutils.Vector((1.0, 0.0, 0.0)))

    def rotate_z(self, angle):
        self.rotate(angle, mathutils.Vector((0.0, 0.0, 1.0)))


@dataclass
class GrapeLSystem:
    m: int = 5
    ns: List[int] = field(default_factory=list)
    l: float = 1
    rl: float = 1.2
    rr: float = 0.9
    alpha: float = 45
    position_base = (0, 0, 0)
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
        phi = math.radians(phi)
        theta = theta

        ret = bmesh.ops.extrude_vert_indiv(self.mesh_branch, verts=verts)

        x = length * math.sin(phi) * math.cos(theta)
        y = length * math.sin(phi) * math.sin(theta)
        z = - length * math.cos(phi)

        ret['verts'][0].co += Vector([x, y, z])

        return ret['verts'], phi, theta

    def draw(self):
        cursor = 0
        stack = []
        self.mesh_branch = bmesh.new()
        verts = [self.mesh_branch.verts.new(self.position_base)]

        phi = self.phi
        theta = self.theta

        self.finitions = []
        internode = 0
        number_berries = 0
        while cursor < len(self.instructions):
            char = self.instructions[cursor]
            temp_string = self.instructions[cursor:]

            if char == "F":
                param = int(float(temp_string[2:].split(')')[0]))
                verts, phi, theta = self.draw_segment(
                    [verts, phi, theta], param)
                internode += 1
            elif char == "/" and self.instructions[cursor+1] != "(":
                theta += 90
            elif char == "[":
                stack.append([verts, phi, theta])
            elif char == "]":
                verts, phi, theta = stack.pop()

            elif char == "+":
                param = int(float(temp_string[2:].split(')')[0]))
                phi += param
            elif char == "-":
                param = int(float(temp_string[2:].split(')')[0]))
                phi -= param
            elif char == "S":
                self.finitions = [*self.finitions, *verts]
                number_berries += 1

            cursor += 1
        print(f"Number internode : {internode}")
        print(f"Number berries : {number_berries}")
        pass

    def draw_bairies(self):
        grappes = []
        for i, vert in enumerate(self.finitions):
            mesh = bpy.data.meshes.new(f'baie_{vert.index}')

            # Construct the bmesh sphere and assign it to the blender mesh.
            bm_temp = bmesh.new()
            bmesh.ops.create_uvsphere(
                bm_temp, u_segments=32, v_segments=16, diameter=0.5)
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

    def show(self):
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
        bpy.ops.transform.skin_resize(value=(size, size, size), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True,
                                      use_proportional_edit=True, proportional_edit_falloff='SMOOTH', proportional_size=0.564474, use_proportional_connected=False, use_proportional_projected=False)

        bpy.ops.object.editmode_toggle()


ns = [2, 1]
grappe = GrapeLSystem(m=3, ns=ns[::-1])
t0 = time()
grappe.iterate(n_iter=10)
grappe.draw()
# grappe.draw_bairies()
print(f"Time : {round((time()-t0)*1000)}ms")
grappe.show()
