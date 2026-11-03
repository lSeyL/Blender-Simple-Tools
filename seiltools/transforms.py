# SPDX-License-Identifier: GPL-3.0-or-later
"""Copy a mesh's world transform, then paste it onto selected meshes."""
import bpy
from bpy.props import BoolProperty, FloatVectorProperty, StringProperty
from mathutils import Matrix


def is_mesh(obj):
    return obj is not None and obj.type == 'MESH' and not obj.get('center_of_mass_ball_marker')


class SEILTOOLS_TransformSettings(bpy.types.PropertyGroup):
    has_copy: BoolProperty(default=False)
    source_name: StringProperty()
    matrix: FloatVectorProperty(size=16)


class SEILTOOLS_OT_copy_transform(bpy.types.Operator):
    bl_idname = 'seiltools.copy_transform'
    bl_label = 'Copy Transform'
    bl_description = 'Store the active mesh world position, rotation and scale for later use'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and is_mesh(context.active_object)

    def execute(self, context):
        context.view_layer.update()
        source = context.active_object
        matrix = source.evaluated_get(context.evaluated_depsgraph_get()).matrix_world.copy()
        settings = context.scene.seiltools_transform
        settings.matrix = tuple(value for row in matrix for value in row)
        settings.source_name = source.name
        settings.has_copy = True
        self.report({'INFO'}, f'Copied transform from {source.name}')
        return {'FINISHED'}


class SEILTOOLS_OT_apply_transform(bpy.types.Operator):
    bl_idname = 'seiltools.apply_transform'
    bl_label = 'Apply Transform to Selected'
    bl_description = 'Set selected meshes to the saved world position, rotation and scale'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and context.scene.seiltools_transform.has_copy
                and any(is_mesh(o) for o in context.selected_objects))

    def execute(self, context):
        targets = [o for o in context.selected_objects if is_mesh(o)]
        if any(not o.is_editable for o in targets):
            self.report({'ERROR'}, 'Selected meshes must be editable local objects')
            return {'CANCELLED'}
        settings = context.scene.seiltools_transform
        matrix = Matrix([settings.matrix[i:i + 4] for i in range(0, 16, 4)])
        # Update parents first when both parent and child are targets.
        def depth(obj):
            count = 0
            while obj.parent:
                obj = obj.parent
                count += 1
            return count
        for target in sorted(targets, key=depth):
            target.matrix_world = matrix.copy()
            context.view_layer.update()
        self.report({'INFO'}, f'Applied saved transform to {len(targets)} mesh(es)')
        return {'FINISHED'}


class SEILTOOLS_PT_transforms(bpy.types.Panel):
    bl_label = 'Copy Transform'
    bl_idname = 'SEILTOOLS_PT_transforms'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SeilTools'
    bl_parent_id = 'SEILTOOLS_PT_main'

    @classmethod
    def poll(cls, context):
        return context.scene.seiltools.tool == 'TRANSFORMS'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.seiltools_transform
        layout.label(text='1. Select the source mesh.')
        layout.operator('seiltools.copy_transform', icon='COPYDOWN')
        if settings.has_copy:
            layout.label(text=f'Saved: {settings.source_name}', icon='CHECKMARK')
        layout.separator()
        layout.label(text='2. Select destination mesh(es).')
        layout.operator('seiltools.apply_transform', icon='PASTEDOWN')
        layout.label(text='Copies position, rotation and scale.')
        layout.label(text='World space. Ctrl+Z to undo.')


CLASSES = (SEILTOOLS_TransformSettings, SEILTOOLS_OT_copy_transform,
           SEILTOOLS_OT_apply_transform, SEILTOOLS_PT_transforms)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.seiltools_transform = bpy.props.PointerProperty(type=SEILTOOLS_TransformSettings)


def unregister():
    del bpy.types.Scene.seiltools_transform
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
