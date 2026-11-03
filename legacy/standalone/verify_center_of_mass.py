"""Integration checks: run in Blender background mode."""
import importlib.util
from pathlib import Path
import bpy
from mathutils import Vector

spec = importlib.util.spec_from_file_location('center_of_mass', Path(__file__).with_name('center_of_mass.py'))
addon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(addon)
addon.register()


def check(obj, volume, center):
    bpy.context.view_layer.update()
    actual_volume, actual_center, _ = addon.solid_mass_properties(obj, bpy.context.evaluated_depsgraph_get())
    assert abs(actual_volume - volume) < max(1e-5, volume * 1e-6), (actual_volume, volume)
    assert (actual_center - Vector(center)).length < 1e-5, actual_center


cube = bpy.context.active_object
check(cube, 8, (0, 0, 0))
cube.scale = (-2, 3, 4)
cube.location = (10000, 4, -3)
cube.rotation_euler.z = 0.7
check(cube, 192, (10000, 4, -3))
cube.rotation_euler.z = 0
cube.location = (0, 0, 0)
cube.scale = (1, 1, 1)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0.75, 0, 0))
cutter = bpy.context.object
boolean = cube.modifiers.new('Asymmetric cavity', 'BOOLEAN')
boolean.operation = 'DIFFERENCE'
boolean.object = cutter
# Cutter removes x=[0.25,1], y,z=[-0.5,0.5]: volume .75, centroid x=.625.
check(cube, 7.25, (-0.75 * 0.625 / 7.25, 0, 0))
cube.modifiers.remove(boolean)
bpy.data.objects.remove(cutter, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
cube.select_set(True)
bpy.context.view_layer.objects.active = cube
assert bpy.ops.object.calculate_mass_ball() == {'FINISHED'}
marker = bpy.context.scene.mass_ball.marker
assert marker.get(addon.TAG) and marker.show_in_front and marker.hide_render
assert abs(marker.scale.x - 0.12) < 1e-6
bpy.context.scene.mass_ball.ball_radius = 0.3
assert abs(marker.scale.x - 0.3) < 1e-6
assert bpy.ops.object.calculate_mass_ball() == {'FINISHED'}
assert bpy.context.scene.mass_ball.marker == marker
bpy.ops.mesh.primitive_cube_add(size=2, location=(4, 0, 0))
cube.select_set(True)
assert bpy.ops.object.calculate_mass_ball() == {'FINISHED'}
assert (marker.location - Vector((2, 0, 0))).length < 1e-6
bpy.ops.mesh.primitive_plane_add()
try:
    addon.solid_mass_properties(bpy.context.object, bpy.context.evaluated_depsgraph_get())
except ValueError:
    pass
else:
    raise AssertionError('Open plane accepted')
addon.unregister()
addon.register()
addon.unregister()
print('PASS: volume, transforms, mirrored scale, Boolean cavity, weighted selection, ball creation/update/size, open mesh rejection, registration')
