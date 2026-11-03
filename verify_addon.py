"""Run with Blender --background --factory-startup --python verify_addon.py."""
import importlib.util
import math
from pathlib import Path
import bpy

spec = importlib.util.spec_from_file_location('box_dimensions', Path(__file__).with_name('box_dimensions.py'))
addon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(addon)
addon.register()
obj = bpy.context.active_object
obj.scale = (2, 3, 4)
bpy.context.view_layer.update()


def check(expected, world=False):
    result = addon.bounds(obj, bpy.context.evaluated_depsgraph_get(), world)
    assert all(abs(a - b) < 0.0001 for a, b in zip(result[1], expected)), result[1]


check((4, 6, 8))
obj.rotation_euler.z = math.pi / 2
bpy.context.view_layer.update()
check((4, 6, 8))
check((6, 4, 8), True)
modifier = obj.modifiers.new('Array measurement test', 'ARRAY')
modifier.count = 2
check((8, 6, 8))
settings = bpy.context.scene.box_dimensions
settings.units = 'MM'
assert addon.format_length(2, settings, bpy.context.scene) == '2000.00 mm'
bpy.context.scene.unit_settings.scale_length = 0.001
assert addon.format_length(2, settings, bpy.context.scene) == '2.00 mm'
addon.unregister()
addon.register()
addon.unregister()
print('PASS: registration, scaling, rotation, world bounds, modifiers, units, re-registration')
