"""Run with Blender --background --factory-startup --python-exit-code 1 --python tests/verify_simple_tools.py."""
import sys
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import simple_tools

simple_tools.register()
assert simple_tools.dimensions.VIEW3D_PT_simple_tools_dimensions.poll(bpy.context)
assert not simple_tools.balance.SIMPLECOM_PT_panel.poll(bpy.context)
bpy.context.scene.simple_tools.tool = 'BALANCE'
assert not simple_tools.dimensions.VIEW3D_PT_simple_tools_dimensions.poll(bpy.context)
assert simple_tools.balance.SIMPLECOM_PT_panel.poll(bpy.context)

bpy.context.scene.simple_tools.tool = 'TRANSFORMS'
assert simple_tools.transforms.SIMPLETOOLS_PT_transforms.poll(bpy.context)
assert not simple_tools.balance.SIMPLECOM_PT_panel.poll(bpy.context)
assert not bpy.ops.simple_tools.apply_transform.poll()
source = bpy.context.active_object
source.location = (3, -2, 7)
source.rotation_euler = (0.2, -0.5, 1.1)
source.scale = (2, 3, 4)
bpy.context.view_layer.update()
expected = source.matrix_world.copy()
assert bpy.ops.simple_tools.copy_transform() == {'FINISHED'}
source.location.x = 100
bpy.ops.mesh.primitive_cube_add(location=(9, 9, 9))
parent = bpy.context.object
parent.rotation_mode = 'QUATERNION'
bpy.ops.mesh.primitive_cube_add()
child = bpy.context.object
child.parent = parent
parent.select_set(True)
vertex_before = child.data.vertices[0].co.copy()
assert bpy.ops.simple_tools.apply_transform() == {'FINISHED'}
for target in (parent, child):
    assert max(abs(target.matrix_world[r][c] - expected[r][c])
               for r in range(4) for c in range(4)) < 1e-5, target.matrix_world
assert child.data.vertices[0].co == vertex_before
assert source.location.x == 100
bpy.data.objects.remove(source, do_unlink=True)
assert bpy.ops.simple_tools.apply_transform() == {'FINISHED'}
print('PASS: transform snapshot, multiple targets, quaternion rotation, parent handling, deleted source, unchanged mesh')

# Run the original geometric regression checks against the bundled tools.
for filename, module, substitutions in [
    ('verify_addon.py', simple_tools.dimensions, [('box_dimensions', 'simple_tools_dimensions')]),
    ('verify_center_of_mass.py', simple_tools.balance, [('mass_ball', 'simple_tools_mass_ball')]),
]:
    bpy.ops.wm.read_factory_settings(use_empty=False)
    source = (root / "legacy" / "standalone" / filename).read_text(encoding='utf-8')
    start = source.index('spec = ')
    end = source.index('addon.register()', start) + len('addon.register()')
    source = source[:start] + source[end:]
    source = source.replace('addon.register()', '').replace('addon.unregister()', '')
    for old, new in substitutions:
        source = source.replace(old, new)
    exec(compile(source, filename, 'exec'), {'addon': module, '__file__': str(root / "legacy" / "standalone" / filename)})

simple_tools.unregister()
simple_tools.register()
simple_tools.unregister()
print('PASS: Simple Tools tab switching, bundled tool regressions, clean re-registration')
