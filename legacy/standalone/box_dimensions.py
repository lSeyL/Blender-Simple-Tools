bl_info = {
    "name": "Box Dimensions",
    "author": "OpenAI",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "3D View > Sidebar > Dimensions",
    "description": "Display overall object dimensions on a bounding box",
    "category": "3D View",
}

import bpy
import blf
import gpu
from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d
from gpu_extras.batch import batch_for_shader
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, IntProperty

_handler = None
EDGES = ((0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
         (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7))


def redraw(self=None, context=None):
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def bounds(obj, depsgraph, world=False):
    """Evaluated geometry includes modifiers; local axes follow object rotation."""
    if obj.mode == 'EDIT' and obj.type == 'MESH':
        obj.update_from_editmode()
    evaluated = obj.evaluated_get(depsgraph)
    if evaluated.type not in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'VOLUME', 'LATTICE'}:
        return None
    raw = [Vector(p) for p in evaluated.bound_box]
    if all(tuple(p) == (-1, -1, -1) for p in raw):
        return None
    matrix = evaluated.matrix_world
    if world:
        raw = [matrix @ p for p in raw]
    lo = [min(p[i] for p in raw) for i in range(3)]
    hi = [max(p[i] for p in raw) for i in range(3)]
    points = [Vector((hi[0] if n & 1 else lo[0],
                      hi[1] if n & 2 else lo[1],
                      hi[2] if n & 4 else lo[2])) for n in range(8)]
    if not world:
        points = [matrix @ p for p in points]
    lengths = [(points[1 << i] - points[0]).length for i in range(3)]
    return points, lengths


def format_length(value, settings, scene):
    unit = settings.units
    if unit == 'SCENE':
        if scene.unit_settings.system == 'NONE':
            return f"{value:.{settings.precision}f} BU"
        return bpy.utils.units.to_string(
            scene.unit_settings.system, 'LENGTH',
            value * scene.unit_settings.scale_length,
            precision=settings.precision, split_unit=False)
    factors = {'MM': (1000, 'mm'), 'CM': (100, 'cm'), 'M': (1, 'm'),
               'IN': (1 / 0.0254, 'in'), 'FT': (1 / 0.3048, 'ft')}
    factor, suffix = factors[unit]
    return f"{value * scene.unit_settings.scale_length * factor:.{settings.precision}f} {suffix}"


def draw():
    context = bpy.context
    if not context.region_data or not context.scene:
        return
    settings = context.scene.box_dimensions
    if not settings.enabled or not context.space_data.overlay.show_overlays:
        return
    obj = context.active_object
    if obj is None or not obj.select_get() or not obj.visible_get():
        return
    result = bounds(obj, context.evaluated_depsgraph_get(), settings.axes == 'WORLD')
    if result is None:
        return
    corners, lengths = result
    projected = [location_3d_to_region_2d(context.region, context.region_data, p)
                 for p in corners]
    segments = []
    if settings.show_box:
        for a, b in EDGES:
            if projected[a] is not None and projected[b] is not None:
                segments.extend((projected[a], projected[b]))
    labels = []
    visible = [p for p in projected if p is not None]
    if not visible:
        return
    center = sum(visible, Vector((0, 0))) / len(visible)
    for axis in range(3):
        candidates = []
        for a, b in EDGES:
            if a ^ b != 1 << axis:
                continue
            p, q = projected[a], projected[b]
            if p is None or q is None or (q - p).length < 8:
                continue
            midpoint = (p + q) / 2
            candidates.append(((midpoint - center).length, p, q, midpoint))
        if not candidates:
            continue
        _, p, q, midpoint = max(candidates, key=lambda candidate: candidate[0])
        direction = q - p
        normal = Vector((-direction.y, direction.x)).normalized()
        if normal.dot(midpoint - center) < 0:
            normal.negate()
        offset = normal * settings.offset
        start, end = p + offset, q + offset
        tick = normal * 4
        segments.extend((p, start + tick, q, end + tick, start, end,
                         start - tick, start + tick, end - tick, end + tick))
        labels.append(((start + end) / 2 + normal * 12,
                       f"{'XYZ'[axis]}: {format_length(lengths[axis], settings, context.scene)}"))
    gpu.state.blend_set('ALPHA')
    try:
        if segments:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'LINES', {'pos': segments})
            shader.bind()
            shader.uniform_float('color', settings.color)
            batch.draw(shader)
        blf.size(0, settings.text_size)
        blf.enable(0, blf.SHADOW)
        blf.shadow(0, 3, 0, 0, 0, 1)
        blf.shadow_offset(0, 1, -1)
        try:
            blf.color(0, *settings.color)
            for point, label in labels:
                width, height = blf.dimensions(0, label)
                blf.position(0, point.x - width / 2, point.y - height / 2, 0)
                blf.draw(0, label)
        finally:
            blf.disable(0, blf.SHADOW)
    finally:
        gpu.state.blend_set('NONE')


class BoxDimensionsSettings(bpy.types.PropertyGroup):
    enabled: BoolProperty(name="Show Dimensions", default=True, update=redraw)
    show_box: BoolProperty(name="Show Bounding Box", default=True, update=redraw)
    axes: EnumProperty(name="Axes", items=[
        ('LOCAL', 'Object', 'Box follows the object rotation'),
        ('WORLD', 'World', 'Box aligns with world X, Y and Z')], update=redraw)
    units: EnumProperty(name="Units", items=[
        ('SCENE', 'Scene Units', ''), ('MM', 'Millimeters', ''),
        ('CM', 'Centimeters', ''), ('M', 'Meters', ''),
        ('IN', 'Inches', ''), ('FT', 'Feet', '')], update=redraw)
    precision: IntProperty(name="Precision", default=2, min=0, max=6, update=redraw)
    text_size: IntProperty(name="Text Size", default=16, min=8, max=48, update=redraw)
    offset: IntProperty(name="Label Offset", default=28, min=10, max=150, update=redraw)
    color: FloatVectorProperty(name="Color", subtype='COLOR', size=4,
                              default=(1, 0.7, 0.15, 1), min=0, max=1, update=redraw)


class VIEW3D_PT_box_dimensions(bpy.types.Panel):
    bl_label = "Box Dimensions"
    bl_idname = "VIEW3D_PT_box_dimensions"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dimensions'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.box_dimensions
        layout.prop(settings, 'enabled')
        column = layout.column()
        column.active = settings.enabled
        for prop in ('show_box', 'axes', 'units', 'precision', 'text_size', 'offset', 'color'):
            column.prop(settings, prop)
        layout.label(text="Select an object to measure.")
        layout.label(text="Overall size, including modifiers.")


CLASSES = (BoxDimensionsSettings, VIEW3D_PT_box_dimensions)


def draw_header(self, context):
    settings = context.scene.box_dimensions
    self.layout.prop(settings, 'enabled', text="Dimensions", toggle=True)


def register():
    global _handler
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.box_dimensions = bpy.props.PointerProperty(type=BoxDimensionsSettings)
    bpy.types.VIEW3D_HT_header.append(draw_header)
    _handler = bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')
    redraw()


def unregister():
    global _handler
    bpy.types.VIEW3D_HT_header.remove(draw_header)
    if _handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handler, 'WINDOW')
        _handler = None
    del bpy.types.Scene.box_dimensions
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    redraw()


if __name__ == '__main__':
    register()
