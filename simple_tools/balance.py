# SPDX-License-Identifier: GPL-3.0-or-later
bl_info = {
    "name": "Center of Mass Ball",
    "author": "OpenAI",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Balance",
    "description": "Estimate solid center of mass and display a large orange ball",
    "category": "Object",
}

import math
import bpy
import bmesh
from mathutils import Vector
from bpy.props import FloatProperty, PointerProperty, StringProperty

TAG = "center_of_simple_tools_mass_ball_marker"


def solid_mass_properties(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        if not mesh or not mesh.polygons:
            raise ValueError(f"{obj.name}: no solid geometry")
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            if any(not e.is_manifold or not e.is_contiguous for e in bm.edges):
                raise ValueError(f"{obj.name}: mesh must be closed with consistent face normals")
        finally:
            bm.free()
        mesh.calc_loop_triangles()
        # Integrate signed tetrahedra near the object to reduce cancellation.
        points = [evaluated.matrix_world @ v.co for v in mesh.vertices]
        local_origin = sum((v.co for v in mesh.vertices), Vector()) / len(mesh.vertices)
        origin = evaluated.matrix_world @ local_origin
        linear = evaluated.matrix_world.to_3x3()
        offsets = [linear @ (v.co - local_origin) for v in mesh.vertices]
        extent = max(p.length for p in offsets)
        volumes = []
        moments = [[], [], []]
        for tri in mesh.loop_triangles:
            a, b, c = (offsets[i] for i in tri.vertices)
            volume = a.dot(b.cross(c)) / 6.0
            centroid = (a + b + c) / 4.0
            volumes.append(volume)
            for axis in range(3):
                moments[axis].append(volume * centroid[axis])
        volume = math.fsum(volumes)
        if abs(volume) <= max(extent ** 3 * 1e-12, 1e-30):
            raise ValueError(f"{obj.name}: zero or ambiguous volume; check normals")
        center = origin + Vector([math.fsum(m) / volume for m in moments])
        return abs(volume), center, points
    finally:
        evaluated.to_mesh_clear()


def resize_marker(settings, context):
    marker = settings.marker
    if marker and marker.get(TAG):
        marker.scale = (settings.ball_radius,) * 3


class SIMPLECOM_Settings(bpy.types.PropertyGroup):
    ball_radius: FloatProperty(name="Ball Radius", default=0.15, min=0.000001,
                               subtype='DISTANCE', update=resize_marker)
    marker: PointerProperty(type=bpy.types.Object)
    result: StringProperty(default="Select solid meshes, then calculate.")


class SIMPLECOM_OT_calculate(bpy.types.Operator):
    bl_idname = "object.calculate_simple_tools_mass_ball"
    bl_label = "Calculate / Update Center"
    bl_description = "Calculate uniform-density center of selected closed meshes, including modifiers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(
            o.type == 'MESH' and not o.get(TAG) for o in context.selected_objects)

    def execute(self, context):
        objects = [o for o in context.selected_objects if o.type == 'MESH' and not o.get(TAG)]
        depsgraph = context.evaluated_depsgraph_get()
        try:
            solids = [solid_mass_properties(o, depsgraph) for o in objects]
        except ValueError as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        total = math.fsum(v for v, _, _ in solids)
        center = Vector([math.fsum(v * c[i] for v, c, _ in solids) / total for i in range(3)])
        settings = context.scene.simple_tools_mass_ball
        marker = settings.marker
        if not marker or not marker.get(TAG):
            mesh = bpy.data.meshes.new("Center of Mass Ball")
            bm = bmesh.new()
            bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
            bm.to_mesh(mesh)
            bm.free()
            marker = bpy.data.objects.new("Center of Mass • Ball", mesh)
            context.scene.collection.objects.link(marker)
            marker[TAG] = True
            marker.hide_render = True
            marker.show_in_front = True
            marker.hide_select = True
            marker.color = (1.0, 0.18, 0.015, 1.0)
            material = bpy.data.materials.new("Center of Mass Orange")
            material.diffuse_color = marker.color
            mesh.materials.append(material)
            for polygon in mesh.polygons:
                polygon.use_smooth = True
            settings.marker = marker
            points = [p for _, _, ps in solids for p in ps]
            span = max(max(p[i] for p in points) - min(p[i] for p in points) for i in range(3))
            settings.ball_radius = max(span * 0.06, 0.000001)
        marker.location = center
        resize_marker(settings, context)
        settings.result = f"Center: {center.x:.5g}, {center.y:.5g}, {center.z:.5g} BU"
        self.report({'INFO'}, f"Updated center from {len(objects)} solid mesh object(s)")
        return {'FINISHED'}


class SIMPLECOM_PT_panel(bpy.types.Panel):
    bl_label = "Center of Mass Ball"
    bl_idname = "SIMPLECOM_PT_simple_tools_mass_ball"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Balance"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.simple_tools_mass_ball
        layout.label(text="Select the solid parts to balance.")
        layout.operator(SIMPLECOM_OT_calculate.bl_idname, icon='SPHERE')
        layout.prop(settings, "ball_radius")
        layout.label(text=settings.result)
        layout.label(text="Uniform density • closed meshes")
        layout.label(text="Recalculate after geometry changes.")
        layout.label(text="Overlapping objects count twice.")


CLASSES = (SIMPLECOM_Settings, SIMPLECOM_OT_calculate, SIMPLECOM_PT_panel)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.simple_tools_mass_ball = PointerProperty(type=SIMPLECOM_Settings)


def unregister():
    del bpy.types.Scene.simple_tools_mass_ball
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
