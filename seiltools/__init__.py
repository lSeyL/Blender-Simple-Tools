# SPDX-License-Identifier: GPL-3.0-or-later
bl_info = {
    "name": "SeilTools",
    "author": "SeilTools / OpenAI",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "3D View > Sidebar > SeilTools",
    "description": "Dimensions, center of mass and transform copying in one sidebar",
    "category": "3D View",
}

import bpy
from bpy.props import EnumProperty, PointerProperty
from . import dimensions, balance, transforms


def redraw(self, context):
    dimensions.redraw()


class SEILTOOLS_Settings(bpy.types.PropertyGroup):
    tool: EnumProperty(name="Tool", items=[
        ('DIMENSIONS', 'Dimensions', 'Measure the selected object', 'DRIVER_DISTANCE', 0),
        ('BALANCE', 'Center of Mass', 'Calculate the center-of-mass ball', 'SPHERE', 1),
        ('TRANSFORMS', 'Copy Transform', 'Copy and paste mesh transforms', 'OBJECT_ORIGIN', 2),
    ], default='DIMENSIONS', update=redraw)


class SEILTOOLS_PT_main(bpy.types.Panel):
    bl_label = "SeilTools"
    bl_idname = "SEILTOOLS_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SeilTools'

    def draw(self, context):
        column = self.layout.column(align=True)
        column.prop(context.scene.seiltools, 'tool', expand=True)


def dimensions_poll(cls, context):
    return context.scene.seiltools.tool == 'DIMENSIONS'


def balance_poll(cls, context):
    return context.scene.seiltools.tool == 'BALANCE'


def configure_panels():
    for panel, poll in ((dimensions.VIEW3D_PT_seiltools_dimensions, dimensions_poll),
                        (balance.SEILCOM_PT_panel, balance_poll)):
        panel.bl_category = 'SeilTools'
        panel.bl_parent_id = SEILTOOLS_PT_main.bl_idname
        panel.poll = classmethod(poll)


def register():
    bpy.utils.register_class(SEILTOOLS_Settings)
    bpy.types.Scene.seiltools = PointerProperty(type=SEILTOOLS_Settings)
    bpy.utils.register_class(SEILTOOLS_PT_main)
    configure_panels()
    dimensions.register()
    balance.register()
    transforms.register()


def unregister():
    transforms.unregister()
    balance.unregister()
    dimensions.unregister()
    bpy.utils.unregister_class(SEILTOOLS_PT_main)
    del bpy.types.Scene.seiltools
    bpy.utils.unregister_class(SEILTOOLS_Settings)
