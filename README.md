# Box Dimensions

Free Blender add-on for Blender 4.0 and later. Shows the active selected object's
overall X, Y and Z dimensions beside a bounding box in the 3D viewport.

## Install

1. Open Blender's Edit > Preferences > Add-ons.
2. Use the menu at the top right > Install from Disk (older versions: Install).
3. Choose `box_dimensions.zip` or `box_dimensions.py`, then enable Box Dimensions.
4. Select an object in the viewport. Press N and open the Dimensions tab.

Click **Dimensions** in the 3D viewport's top header to turn measurements on or
off. The same switch is also available in N > Dimensions > Show Dimensions.
When updating, disable the old add-on, install the new ZIP, then enable it again.

Dimensions update as the object changes and include evaluated modifiers.
Object axes follow its rotation; World axes measure a world-aligned box.
Choose scene units or explicit metric/imperial units. Explicit units respect
the scene's Unit Scale (at the default scale, one Blender unit is one meter).
Global viewport overlays must be enabled. Labels are viewport overlays and do
not appear in final renders. One active selected object is measured at a time.
Geometry Nodes instances should be realized to include their geometry in bounds.
When looking exactly along an axis, its dimension is hidden because that axis
projects to a point. Empty objects, cameras and lights are not measured.

## License

SPDX-License-Identifier: GPL-3.0-or-later

This add-on is free software, distributed under the GNU General Public License,
version 3 or (at your option) any later version, without warranty.
License text: https://www.gnu.org/licenses/gpl-3.0.html
