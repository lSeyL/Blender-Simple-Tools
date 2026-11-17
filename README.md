# SimpleTools

One Blender add-on with a **SimpleTools** sidebar and four tool tabs:

- **Dimensions**: bounding box, X/Y/Z labels, units, colors, and axis settings.
- **Center of Mass**: calculate a large adjustable orange ball at the selected
  solids' volume-weighted center.
- **Copy Transform**: copy a mesh's world position, rotation and scale, then
  paste that saved transform onto one or more selected meshes.
- **Batch Export**: export each mesh in `Export_Ready_Plugin` as FBX or GLB
  relative to its own origin.

## Batch Export

Open SimpleTools > Batch Export and click **Create Export Collection** if needed.
Move or link meshes into `Export_Ready_Plugin` (nested collections are included).
Choose FBX or GLB, set the output directory, and click **Export All** in Object Mode.
The default `//Exports/` directory is relative to the saved blend file; save first
or choose an absolute directory.

Each file uses the object name. Invalid filename characters are replaced, and
case-insensitive collisions or existing files receive numbered suffixes.
Meshes export as static evaluated geometry at the current frame, including
viewport modifiers and object material overrides. World rotation, scale, and
parent effects are baked into temporary mesh copies; only world translation is
removed. The pivot remains the object's original origin, not its bounding-box
center. Source geometry, transforms, parenting, selection, and active object stay
unchanged. Standard exporter axis and scene-unit conversion is retained.

Include meshes in the active view layer before exporting. Realize Geometry Nodes
instances first. Animation, rigs, and editable modifier stacks are not exported.
Materials and textures use the standard Blender FBX/glTF conversion; procedural
shaders may require baking for matching appearance in other applications.
Failures are reported per object and temporary objects, meshes, and scenes are
removed. Successful files remain when another mesh fails.

## Copy Transform

In Object Mode, select the source mesh, open SimpleTools > Copy Transform, and
click **Copy Transform**. Select the destination mesh(es), then click
**Apply Transform to Selected**. The saved transform is a snapshot; changing
or deleting the source afterwards does not change it. All selected meshes
receive it, including the source if it is selected. Ctrl+Z undoes the operation.
This matches object origins and transforms, not bounding-box sizes. It does
not bake scale into mesh vertices. Parent transforms are taken into account.
Constraints, drivers, or animation on destinations can override the result;
shear from rotated nonuniformly scaled parents may not be representable exactly.
Linked, read-only destinations are rejected. Non-mesh selections are ignored.

To update SimpleTools, disable the previous version, install the updated ZIP,
and enable it again. Restart Blender if the old version remains loaded.

## Installation

1. Disable previous versions of **SimpleTools**, **Box Dimensions**, and **Center of Mass Ball** add-ons
   if you have installed them, to avoid duplicate controls and dimension overlays.
2. Open Edit > Preferences > Add-ons > menu > Install from Disk (older versions:
   Install), select `install/simple_tools.zip`, and enable **SimpleTools**.
3. In the 3D View press **N** and choose **SimpleTools**.
4. Use the **Dimensions**, **Center of Mass**, **Copy Transform**, and **Batch Export** buttons to switch tools.

Switching tabs preserves each tool's settings. Dimension overlays stay on while
using the other tab unless you turn off Show Dimensions or the header toggle.
Select your solid meshes in Object Mode and click Calculate / Update Center
after edits to update the ball. Ball Radius controls its size.

Center of mass assumes closed solids with uniform density. Boolean holes and
viewport modifiers are included. Do not select Boolean cutters. Union overlapping
solids first to avoid counting overlap twice. Realize Geometry Nodes instances.
The marker is hidden from renders but is a mesh: exclude it from exports.
The tool does not automatically adjust geometry or determine a hole's pivot axis.

Targets Blender 4.0 and later; integration tested with Blender 5.2.3.
See legacy/standalone/CENTER_OF_MASS_README.md and legacy/standalone/BOX_DIMENSIONS_README.md for further tool limitations.

SPDX-License-Identifier: GPL-3.0-or-later

## Project layout

- `simple_tools/` ? current add-on source.
- `install/simple_tools.zip` ? install this ZIP in Blender.
- `tests/` ? Blender integration checks.
- `legacy/` ? older standalone add-ons and SimpleTools installer, kept for reference.
- `build.py` ? rebuild the installer with `python build.py`.

Run checks with:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python tests/verify_simple_tools.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python tests/verify_batch_export.py
```

Disable older installations before enabling this version of SimpleTools;
settings from the legacy installer are not migrated automatically.
