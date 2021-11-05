import bpy
import bmesh
import operator
import mathutils
from dataclasses import dataclass, field
from copy import deepcopy
from typing import *


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
