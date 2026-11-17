"""Blender integration tests for non-destructive batch export and round trips."""
import sys
import tempfile
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import simple_tools
from simple_tools import batch_export

simple_tools.register()
bpy.ops.simple_tools.create_export_collection()
collection = bpy.data.collections[batch_export.COLLECTION_NAME]
source = bpy.context.object
collection.objects.link(source)
source.name = 'Pivot:Mesh'
source.data.vertices[0].co.x -= 0.7  # Deliberately off-center pivot.
source.location = (11, 22, 33)
source.rotation_euler = (0.3, 0.5, 0.7)
source.scale = (-2, 3, 0.5)
material = bpy.data.materials.new('ExportMaterial')
material.diffuse_color = (0.2, 0.5, 0.7, 1)
source.data.materials.append(material)
modifier = source.modifiers.new('Bevel', 'BEVEL')
modifier.width = 0.1
modifier.segments = 2
parent = bpy.data.objects.new('Parent', None)
bpy.context.scene.collection.objects.link(parent)
parent.scale = (1.3, 0.8, 2)
parent.rotation_euler = (0.4, -0.2, 0.1)
source.parent = parent
bpy.context.view_layer.update()
original_matrix = source.matrix_world.copy()
original_vertices = [v.co.copy() for v in source.data.vertices]
selection = tuple(bpy.context.selected_objects)
active = bpy.context.view_layer.objects.active
scene = bpy.context.scene
mesh = bpy.data.meshes.new_from_object(source.evaluated_get(bpy.context.evaluated_depsgraph_get()))
expected = [original_matrix.to_3x3() @ v.co for v in mesh.vertices]
bpy.data.meshes.remove(mesh)

def bounds(points):
    return [(min(p[i] for p in points), max(p[i] for p in points)) for i in range(3)]

with tempfile.TemporaryDirectory() as directory:
    settings = scene.simple_tools_export
    settings.directory = directory
    for format in ('GLB', 'FBX'):
        settings.format = format
        before = (len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.scenes))
        assert bpy.ops.simple_tools.export_all() == {'FINISHED'}
        assert bpy.ops.simple_tools.export_all() == {'FINISHED'}
        assert before == (len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.scenes))
        assert source.matrix_world == original_matrix
        assert all(a == b.co for a, b in zip(original_vertices, source.data.vertices))
        assert tuple(bpy.context.selected_objects) == selection
        assert bpy.context.view_layer.objects.active == active
        assert bpy.context.scene == scene
        files = sorted(Path(directory).glob('*.' + format.lower()))
        assert len(files) == 2, files
        imported_before = set(bpy.data.objects)
        if format == 'GLB':
            bpy.ops.import_scene.gltf(filepath=str(files[0]))
        else:
            bpy.ops.import_scene.fbx(filepath=str(files[0]))
        imported = [o for o in bpy.data.objects if o not in imported_before]
        meshes = [o for o in imported if o.type == 'MESH']
        assert len(meshes) == 1
        obj = meshes[0]
        actual = [obj.matrix_world @ v.co for v in obj.data.vertices]
        assert max(abs(a - b) for pair1, pair2 in zip(bounds(expected), bounds(actual))
                   for a, b in zip(pair1, pair2)) < 0.001, (format, bounds(expected), bounds(actual))
        assert obj.matrix_world.translation.length < 0.0001
        assert obj.data.uv_layers
        assert obj.data.materials
        for obj in imported:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in selection:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = active
    # A forced exporter exception must remove temporary objects, meshes and scene.
    original_export = batch_export.export_mesh
    def fail(*args):
        raise RuntimeError('Injected failure')
    batch_export.export_mesh = fail
    before = (len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.scenes))
    assert bpy.ops.simple_tools.export_all() == {'CANCELLED'}
    assert before == (len(bpy.data.objects), len(bpy.data.meshes), len(bpy.data.scenes))
    assert not list(Path(directory).glob('.simple_tools_*'))
    batch_export.export_mesh = original_export
    # Force failure after allocating the temporary mesh/object, inside the exporter.
    temporary_scene = bpy.data.scenes.new('Failure test')
    before = (len(bpy.data.objects), len(bpy.data.meshes))
    class FailingContext:
        def temp_override(self, **kwargs):
            raise RuntimeError('Injected context failure after mesh allocation')
    try:
        batch_export.export_mesh(FailingContext(), source,
                                 bpy.context.evaluated_depsgraph_get(), temporary_scene,
                                 Path(directory) / 'missing' / 'test.glb', 'GLB')
    except Exception:
        pass
    else:
        raise AssertionError('Expected context failure')
    assert before == (len(bpy.data.objects), len(bpy.data.meshes))
    bpy.data.scenes.remove(temporary_scene)
    reserved = set()
    first = batch_export.output_path(Path(directory), 'A:B', '.glb', reserved)
    second = batch_export.output_path(Path(directory), 'a?b', '.glb', reserved)
    assert first.name == 'A_B.glb' and second.name == 'a_b_001.glb'
    vegetation = bpy.data.collections.new('Vegetation')
    grass = bpy.data.collections.new('Grass')
    trees = bpy.data.collections.new('Trees')
    collection.children.link(vegetation)
    vegetation.children.link(grass)
    vegetation.children.link(trees)
    collection.objects.unlink(source)
    grass.objects.link(source)
    trees.objects.link(source)  # Export each collection link in folder mode.
    bpy.context.view_layer.update()
    settings.collection_folders = True
    settings.format = 'FBX'
    settings.directory = str(Path(directory) / 'hierarchy')
    for _ in range(2):
        assert bpy.ops.simple_tools.export_all() == {'FINISHED'}
    for name in ('Grass', 'Trees'):
        folder = Path(settings.directory) / 'Vegetation' / name
        assert {p.name for p in folder.iterdir()} == {'Pivot_Mesh.fbx', 'Pivot_Mesh_001.fbx'}
    assert not list(Path(settings.directory).glob('*.fbx'))
    assert source.matrix_world == original_matrix
    assert tuple(bpy.context.selected_objects) == selection
    # Flat mode deduplicates multiply linked meshes and ignores nested paths.
    entries = list(batch_export.export_entries(collection, Path(directory), False))
    assert entries == [(source, Path(directory))]
    collision = bpy.data.collections.new('Gras:s')
    collision2 = bpy.data.collections.new('Gras?s')
    vegetation.children.link(collision)
    vegetation.children.link(collision2)
    collision.objects.link(source)
    collision2.objects.link(source)
    folders = [folder.name for obj, folder in
               batch_export.export_entries(collection, Path(directory), True)]
    assert 'Gras_s' in folders and 'Gras_s_001' in folders, folders
simple_tools.unregister()
simple_tools.register()
simple_tools.unregister()
print('PASS: FBX/GLB round trips, pivot, parent shear, mirrored scale, modifiers, UV/materials, collisions, cleanup and unchanged source')
print('PASS: collection folders, repeated exports, multiple collection links, flat deduplication and sanitized folder collisions')
