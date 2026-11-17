# SPDX-License-Identifier: GPL-3.0-or-later
"""Export evaluated static meshes without editing the source scene."""
import shutil
from pathlib import Path
import re
import tempfile

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

COLLECTION_NAME = 'Export_Ready_Plugin'


def output_path(directory, name, extension, reserved):
    # Use portable filenames, including Windows device-name protection.
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).rstrip(' .') or 'Mesh'
    stem = stem[:180]
    if stem.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL',
                                    *(f'COM{i}' for i in range(1, 10)),
                                    *(f'LPT{i}' for i in range(1, 10))}:
        stem = '_' + stem
    candidate = stem + extension
    index = 1
    while candidate.casefold() in reserved:
        candidate = f'{stem}_{index:03d}{extension}'
        index += 1
    reserved.add(candidate.casefold())
    return directory / candidate


def export_entries(collection, directory, folders):
    """Yield direct links per collection path; flat exports stay deduplicated."""
    if not folders:
        for obj in sorted(collection.all_objects, key=lambda obj: obj.name):
            if obj.type == 'MESH':
                yield obj, directory
        return
    for obj in sorted(collection.objects, key=lambda obj: obj.name):
        if obj.type == 'MESH':
            yield obj, directory
    # Allocate sibling folder names independently of filenames. Reuse folders
    # on subsequent exports, while separating names that sanitize identically.
    reserved = set()
    existing = {p.name.casefold(): p for p in directory.iterdir()} if directory.is_dir() else {}
    for child in sorted(collection.children, key=lambda child: child.name):
        folder = output_path(directory, child.name, '', reserved)
        folder = existing.get(folder.name.casefold(), folder)
        yield from export_entries(child, folder, True)


def export_mesh(context, source, depsgraph, scene, filepath, file_format, fbx_units_scale=False):
    mesh = None
    obj = None
    try:
        evaluated = source.evaluated_get(depsgraph)
        mesh = bpy.data.meshes.new_from_object(
            evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
        # Bake the full linear world transform (including parent shear), but
        # remove translation only: zero remains the intended object pivot.
        matrix = evaluated.matrix_world.copy()
        matrix.translation = (0, 0, 0)
        mesh.transform(matrix)
        if matrix.determinant() < 0:
            mesh.flip_normals()
        mesh.update()
        obj = bpy.data.objects.new(source.name + '_Export', mesh)
        scene.collection.objects.link(obj)
        # Evaluated meshes alone do not include object-linked material overrides.
        for index, slot in enumerate(evaluated.material_slots):
            if index < len(mesh.materials):
                mesh.materials[index] = slot.material
        layer = scene.view_layers[0]
        layer.objects.active = obj
        obj.select_set(True, view_layer=layer)
        with context.temp_override(scene=scene, view_layer=layer,
                                   active_object=obj, object=obj,
                                   selected_objects=[obj], selected_editable_objects=[obj]):
            if file_format == 'FBX':
                result = bpy.ops.export_scene.fbx(
                    filepath=str(filepath), check_existing=False,
                    use_selection=True, object_types={'MESH'},
                    global_scale=1.0, apply_unit_scale=True,
                    apply_scale_options='FBX_SCALE_UNITS' if fbx_units_scale else 'FBX_SCALE_NONE',
                    use_mesh_modifiers=False, bake_anim=False,
                    path_mode='COPY', embed_textures=True,
                    axis_forward='-Z', axis_up='Y')
            else:
                result = bpy.ops.export_scene.gltf(
                    filepath=str(filepath), check_existing=False,
                    export_format='GLB', use_selection=True,
                    export_animations=False, export_materials='EXPORT',
                    export_yup=True)
        if result != {'FINISHED'} or not filepath.is_file():
            raise RuntimeError('Exporter did not produce a file')
    finally:
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)
        if mesh is not None:
            bpy.data.meshes.remove(mesh)


class SIMPLETOOLS_ExportSettings(bpy.types.PropertyGroup):
    format: EnumProperty(name='Format', items=[
        ('FBX', 'FBX', 'Export an FBX file per mesh'),
        ('GLB', 'GLB', 'Export a binary glTF file per mesh'),
    ], default='FBX')
    directory: StringProperty(name='Output Directory', subtype='DIR_PATH', default='//Exports/')
    fbx_units_scale: BoolProperty(
        name='FBX Units Scale', default=False,
        description='Store scene unit conversion in FBX unit metadata instead of object transforms')
    collection_folders: BoolProperty(
        name='Create Collection Folders', default=False,
        description='Mirror nested collections as folders; meshes linked to multiple collections export in each folder')


class SIMPLETOOLS_OT_create_export_collection(bpy.types.Operator):
    bl_idname = 'simple_tools.create_export_collection'
    bl_label = 'Create Export Collection'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        collection = bpy.data.collections.get(COLLECTION_NAME)
        if collection is None:
            collection = bpy.data.collections.new(COLLECTION_NAME)
        if collection not in tuple(context.scene.collection.children_recursive):
            context.scene.collection.children.link(collection)
        self.report({'INFO'}, f'Collection ready: {COLLECTION_NAME}')
        return {'FINISHED'}


class SIMPLETOOLS_OT_export_all(bpy.types.Operator):
    bl_idname = 'simple_tools.export_all'
    bl_label = 'Export All'
    bl_description = 'Export each mesh in Export_Ready_Plugin, including nested collections, at its own origin'

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        collection = bpy.data.collections.get(COLLECTION_NAME)
        if collection is None:
            self.report({'ERROR'}, f'Create {COLLECTION_NAME} first')
            return {'CANCELLED'}
        sources = sorted((o for o in collection.all_objects if o.type == 'MESH'),
                         key=lambda o: o.name)
        if not sources:
            self.report({'ERROR'}, 'Export collection contains no meshes')
            return {'CANCELLED'}
        settings = context.scene.simple_tools_export
        if not settings.directory.strip():
            self.report({'ERROR'}, 'Choose an output directory')
            return {'CANCELLED'}
        if settings.directory.startswith('//') and not bpy.data.filepath:
            self.report({'ERROR'}, 'Save the blend file first or choose an absolute output directory')
            return {'CANCELLED'}
        scene = None
        exported = 0
        errors = []
        try:
            directory = Path(bpy.path.abspath(settings.directory)).resolve()
            directory.mkdir(parents=True, exist_ok=True)
            entries = list(export_entries(collection, directory, settings.collection_folders))
            reservations = {}
            context.view_layer.update()
            depsgraph = context.evaluated_depsgraph_get()
            scene = bpy.data.scenes.new('SimpleTools Export Temporary')
            scene.unit_settings.system = context.scene.unit_settings.system
            scene.unit_settings.scale_length = context.scene.unit_settings.scale_length
            for source, output_directory in entries:
                try:
                    if source.name not in context.view_layer.objects:
                        raise RuntimeError('Mesh must be included in the active view layer')
                    if not output_directory.resolve().is_relative_to(directory):
                        raise RuntimeError('Collection folder resolves outside the output directory')
                    output_directory.mkdir(parents=True, exist_ok=True)
                    if output_directory not in reservations:
                        reservations[output_directory] = {p.name.casefold() for p in output_directory.iterdir()}
                    target = output_path(output_directory, source.name, '.' + settings.format.lower(),
                                         reservations[output_directory])
                    # Stage the export so a failed exporter never leaves a partial target.
                    with tempfile.TemporaryDirectory(prefix='.simple_tools_', dir=output_directory) as staging:
                        staged = Path(staging) / target.name
                        export_mesh(context, source, depsgraph, scene, staged, settings.format,
                                    settings.fbx_units_scale)
                        # Exclusive creation also protects against concurrent writers.
                        with target.open('xb') as destination:
                            try:
                                with staged.open('rb') as data:
                                    shutil.copyfileobj(data, destination)
                            except Exception:
                                destination.close()
                                target.unlink()
                                raise
                    exported += 1
                except Exception as exc:
                    errors.append(f'{source.name}: {exc}')
        except Exception as exc:
            errors.append(str(exc))
        finally:
            if scene is not None:
                bpy.data.scenes.remove(scene)
        for error in errors:
            self.report({'WARNING'}, error)
        self.report({'INFO'} if not errors else {'WARNING'},
                    f'Exported {exported} mesh(es); {len(errors)} error(s)')
        return {'FINISHED'} if exported else {'CANCELLED'}


class SIMPLETOOLS_PT_batch_export(bpy.types.Panel):
    bl_label = 'Batch Export'
    bl_idname = 'SIMPLETOOLS_PT_batch_export'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SimpleTools'
    bl_parent_id = 'SIMPLETOOLS_PT_main'

    @classmethod
    def poll(cls, context):
        return context.scene.simple_tools.tool == 'EXPORT'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.simple_tools_export
        layout.label(text=COLLECTION_NAME, icon='OUTLINER_COLLECTION')
        if bpy.data.collections.get(COLLECTION_NAME) is None:
            layout.operator('simple_tools.create_export_collection', icon='ADD')
        layout.prop(settings, 'format')
        if settings.format == 'FBX':
            layout.prop(settings, 'fbx_units_scale')
        layout.prop(settings, 'directory')
        layout.prop(settings, 'collection_folders')
        layout.operator('simple_tools.export_all', icon='EXPORT')
        layout.label(text='Each mesh exports at its own origin.')
        layout.label(text='Existing filenames get numbered suffixes.')


CLASSES = (SIMPLETOOLS_ExportSettings, SIMPLETOOLS_OT_create_export_collection,
           SIMPLETOOLS_OT_export_all, SIMPLETOOLS_PT_batch_export)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.simple_tools_export = bpy.props.PointerProperty(type=SIMPLETOOLS_ExportSettings)


def unregister():
    del bpy.types.Scene.simple_tools_export
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

