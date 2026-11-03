# Center of Mass Ball

Blender add-on targeting Blender 4.0 and later.

## Install and use

1. In Blender, open Edit > Preferences > Add-ons > menu > Install from Disk
   (older versions: Install).
2. Select `center_of_mass.zip` and enable **Center of Mass Ball**.
3. In Object Mode, select the solid mesh object(s) making up your part.
4. In the 3D View, press **N**, open **Balance**, and click
   **Calculate / Update Center**.
5. A large orange ball marks the calculated center. Adjust **Ball Radius** to
   make it bigger or smaller. Click Calculate again after changing the model.

The ball starts with a diameter of 12% of the selection's largest dimension.
It appears in front of geometry, is excluded from future calculations, cannot
be accidentally selected in the viewport, and is hidden from renders.
In Solid shading, choose Color > Material or Object to see its orange color.
The ball is an actual mesh: hide/delete it before exporting all scene meshes,
or export only your selected model objects.

## Assumptions and limitations

Calculates solid volume, assuming the same uniform material density throughout.
Includes evaluated viewport modifiers, Boolean holes, rotation, and scale.
Boolean cutters should not also be selected. For overlapping solids, Boolean
Union them first: separate selected objects have their volumes added and any
overlap counts twice. Realize Geometry Nodes instances before calculating.

Meshes must be closed and have consistent normals; open/non-manifold meshes
are rejected. Use Edit Mode > select all > Shift+N to recalculate outward
normals when needed. Disconnected solid islands should all have outward normals;
intentional enclosed cavity surfaces should face into the cavity. Self-intersecting
meshes are not detected and can give incorrect results.

For balance around a hole/pivot, the center of the ball should lie on the pivot
axis. This version displays the center only; it does not infer hole axes or resize
your parts automatically. Recalculate manually after edits. Print infill,
different materials, and dynamic rotational balance are not modeled.

## License

SPDX-License-Identifier: GPL-3.0-or-later
Distributed without warranty under GNU GPL v3 or later.
https://www.gnu.org/licenses/gpl-3.0.html
