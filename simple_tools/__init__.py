# SPDX-License-Identifier: GPL-3.0-or-later
bl_info = {
    "name": "SimpleTools",
    "author": "SimpleTools / OpenAI",
    "version": (1, 3, 0),
    "blender": (4, 0, 0),
    "location": "3D View > Sidebar > SimpleTools",
    "description": "Dimensions, center of mass, transform copying and batch export in one sidebar",
    "category": "3D View",
}

import bpy
from bpy.props import EnumProperty, PointerProperty
from . import dimensions, balance, transforms, batch_export


def redraw(self, context):
    dimensions.redraw()


class SIMPLETOOLS_Settings(bpy.types.PropertyGroup):
    tool: EnumProperty(name="Tool", items=[
        ('DIMENSIONS', 'Dimensions', 'Measure the selected object', 'DRIVER_DISTANCE', 0),
        ('BALANCE', 'Center of Mass', 'Calculate the center-of-mass ball', 'SPHERE', 1),
        ('TRANSFORMS', 'Copy Transform', 'Copy and paste mesh transforms', 'OBJECT_ORIGIN', 2),
        ('EXPORT', 'Batch Export', 'Export meshes relative to their origins', 'EXPORT', 3),
    ], default='DIMENSIONS', update=redraw)


class SIMPLETOOLS_PT_main(bpy.types.Panel):
    bl_label = "SimpleTools"
    bl_idname = "SIMPLETOOLS_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SimpleTools'

    def draw(self, context):
        column = self.layout.column(align=True)
        column.prop(context.scene.simple_tools, 'tool', expand=True)


def dimensions_poll(cls, context):
    return context.scene.simple_tools.tool == 'DIMENSIONS'


def balance_poll(cls, context):
    return context.scene.simple_tools.tool == 'BALANCE'


def configure_panels():
    for panel, poll in ((dimensions.VIEW3D_PT_simple_tools_dimensions, dimensions_poll),
                        (balance.SIMPLECOM_PT_panel, balance_poll)):
        panel.bl_category = 'SimpleTools'
        panel.bl_parent_id = SIMPLETOOLS_PT_main.bl_idname
        panel.poll = classmethod(poll)


def register():
    bpy.utils.register_class(SIMPLETOOLS_Settings)
    bpy.types.Scene.simple_tools = PointerProperty(type=SIMPLETOOLS_Settings)
    bpy.utils.register_class(SIMPLETOOLS_PT_main)
    configure_panels()
    dimensions.register()
    balance.register()
    transforms.register()
    batch_export.register()


def unregister():
    batch_export.unregister()
    transforms.unregister()
    balance.unregister()
    dimensions.unregister()
    bpy.utils.unregister_class(SIMPLETOOLS_PT_main)
    del bpy.types.Scene.simple_tools
    bpy.utils.unregister_class(SIMPLETOOLS_Settings)
