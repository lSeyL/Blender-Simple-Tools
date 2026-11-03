# Simple Tools

One Blender add-on with a **Simple Tools** sidebar and three tool tabs:

- **Dimensions**: bounding box, X/Y/Z labels, units, colors, and axis settings.
- **Center of Mass**: calculate a large adjustable orange ball at the selected
  solids' volume-weighted center.
- **Copy Transform**: copy a mesh's world position, rotation and scale, then
  paste that saved transform onto one or more selected meshes.

## Copy Transform

In Object Mode, select the source mesh, open Simple Tools > Copy Transform, and
click **Copy Transform**. Select the destination mesh(es), then click
**Apply Transform to Selected**. The saved transform is a snapshot; changing
or deleting the source afterwards does not change it. All selected meshes
receive it, including the source if it is selected. Ctrl+Z undoes the operation.
This matches object origins and transforms, not bounding-box sizes. It does
not bake scale into mesh vertices. Parent transforms are taken into account.
Constraints, drivers, or animation on destinations can override the result;
shear from rotated nonuniformly scaled parents may not be representable exactly.
Linked, read-only destinations are rejected. Non-mesh selections are ignored.

To update Simple Tools, disable the previous version, install the updated ZIP,
and enable it again. Restart Blender if the old version remains loaded.

## Installation

1. Disable the old **SeilTools**, **Box Dimensions**, and **Center of Mass Ball** add-ons
   if you have installed them, to avoid duplicate controls and dimension overlays.
2. Open Edit > Preferences > Add-ons > menu > Install from Disk (older versions:
   Install), select `install/simple_tools.zip`, and enable **Simple Tools**.
3. In the 3D View press **N** and choose **Simple Tools**.
4. Use the **Dimensions**, **Center of Mass**, and **Copy Transform** buttons to switch tools.

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
- `legacy/` ? older standalone add-ons and SeilTools installer, kept for reference.
- `build.py` ? rebuild the installer with `python build.py`.

Run checks with:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --factory-startup --python-exit-code 1 --python tests/verify_simple_tools.py
```

The renamed add-on installs separately from SeilTools. Disable the old add-on
before enabling Simple Tools; settings are not migrated automatically.
