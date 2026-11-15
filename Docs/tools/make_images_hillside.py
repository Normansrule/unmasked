#!/usr/bin/env python3
"""
Pictures for round 49, life on the hills:

  hillside.png  four views before (round 48) and after hillside.py: ivy down the walls of the sunken
                Main Street, the lantern at the church steps, a stairway down the creek bank to its
                landing, and the bench at the top looking over the water

Drawn by Docs/tools/render3d.py from the layout files, not captured in Unity.

    python3 Docs/tools/make_images_hillside.py [pre49/HollowCreek.json]
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
from make_images_hills import ground  # noqa: E402

# (label, eye x, eye height over the ground there, eye z, target x, target height over the ground, target z, fov)
SHOTS = [
    ("Ivy down the walls of the sunken Main Street", 0.5, 1.7, 112, 2, 1.6, 140, 58),
    ("A lantern at the top of the church steps", 6.5, 1.7, 73, -9, 1.4, 65, 60),
    ("A stairway down the creek bank to its landing", -36.5, 1.6, 186, -42, 2.0, 173, 60),
    ("A bench at the top, looking over the creek", -47, 1.6, 166.5, -40, -0.5, 186, 62),
]


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
    d.text((16, 22), "Life on the hills", font=font(32, "Black"), fill=INK)
    d.text((16, 64), "Ivy on the retaining walls, lanterns at the steps, stairways and landings on the creek bank. Not an engine capture.",
           font=font(14), fill=MUTED)
    for row, shot in enumerate(SHOTS):
        y = 96 + row * (H + 40)
        for c in range(cols):
            img = (before[row] if c == 0 else after[row]) if before else after[row]
            x = 16 + c * (W + 16)
            out.paste(img, (x, y))
            tag = "before" if before and c == 0 else "after"
            d.text((x, y + H + 8), f"{shot[0]}, {tag}", font=font(14, "Bold"), fill=MUTED if tag == "before" else INK)
    save_png(out, "hillside.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
