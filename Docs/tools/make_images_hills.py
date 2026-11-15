#!/usr/bin/env python3
"""
Pictures for round 48, hills and level changes:

  hills.png   four views of Hollow Creek before (flat) and after terrain.py: Main Street climbing from Pine
              Street in its cutting, the church above the sunken street, the raised bridge over the creek,
              and the terraces from the air

Drawn by Docs/tools/render3d.py from the layout files, not captured in Unity.

    python3 Docs/tools/make_images_hills.py [pre48/HollowCreek.json]
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_storybook import BG, INK, MUTED  # noqa: E402

# (label, eye x, eye height over the ground there, eye z, target x, target height over the ground, target z, fov)
SHOTS = [
    ("Main Street climbs from Pine Street in a cutting", 1.8, 1.7, 44, 0, 1.6, 92, 58),
    ("Steps up from the sunken street to the church", 7.5, 1.7, 76, -8, 1.0, 66, 60),
    ("Main Street on its embankment and the raised bridge", -26, 2.0, 197, -2, 0.5, 180, 58),
    ("Terraces stepping up the hill, seen from Pine Street", 70, 18, 30, 10, 0, 120, 55),
]


def ground(T, x, z):
    t = T.get("terrain")
    if not t:
        return 0.0
    i, j = math.floor(x - t["x0"]), math.floor(z - t["z0"])
    if not (0 <= i < t["nx"] and 0 <= j < t["nz"]):
        return 0.0
    c = t["cells"][j * t["nx"] + i]
    if c != "~":
        return t["levels"][t["alphabet"].index(c)]
    R = t["ramps"]
    for r in range(0, len(R), 7):
        x0, x1, z0, z1, ax, h0, h1 = R[r:r + 7]
        if x0 <= x < x1 and z0 <= z < z1:
            u = (x - x0) / (x1 - x0) if ax == 0 else (z - z0) / (z1 - z0)
            return h0 + (h1 - h0) * min(1, max(0, u))
    return 0.0


def shots(path, W, H):
    keep = r3.TOWN_PATH
    r3.TOWN_PATH = path
    try:
        merged, t, _ = r3.load_town()
    finally:
        r3.TOWN_PATH = keep
    with open(path) as f:
        T = json.load(f)
    mesh = r3.layout_mesh(merged)
    r3.horizon_mesh(t, mesh)
    out = []
    for label, ex, ey, ez, tx, ty, tz, fov in SHOTS:
        eye = (ex, ground(T, ex, ez) + ey, ez)
        target = (tx, ground(T, tx, tz) + ty, tz)
        out.append(r3.render(merged, r3.Camera(eye, target, fov, W, H), mesh, ss=1, horizon=t, fog_density=0.004,
                             ambient=(0.24, 0.21, 0.32), light_boost=1.7))
        print("  ", label, os.path.basename(path))
    return out


def main(old_town):
    W, H = 560, 330
    after = shots(r3.TOWN_PATH, W, H)
    before = shots(old_town, W, H) if old_town else None
    cols = 2 if before else 1
    out = Image.new("RGB", (16 + cols * (W + 16), 96 + len(SHOTS) * (H + 40)), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 22), "Hills and level changes", font=font(32, "Black"), fill=INK)
    d.text((16, 64), "Terraces, sunken and raised streets, retaining walls, steps and a raised bridge. Not an engine capture.",
           font=font(14), fill=MUTED)
    for row, shot in enumerate(SHOTS):
        y = 96 + row * (H + 40)
        for c in range(cols):
            img = (before[row] if c == 0 else after[row]) if before else after[row]
            x = 16 + c * (W + 16)
            out.paste(img, (x, y))
            tag = "before" if before and c == 0 else "after"
            d.text((x, y + H + 8), f"{shot[0]}, {tag}", font=font(14, "Bold"), fill=MUTED if tag == "before" else INK)
    save_png(out, "hills.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
