#!/usr/bin/env python3
"""
Pictures for round 39, the world past the edge of town:

  world-map.png   the whole world from above, brightened like the in-game map (M): Hollow Creek in
                  the middle, the six haunted places round it, the roads out, and where the
                  curiosities hide
  regions.png     the six haunted places at night, one frame each: Ravenhold Castle, the Moonlight
                  Circus, Gloamwood Tower, Saltmarsh Lighthouse at Gull Harbor, the Mary Grey on
                  Wreckers' Beach, and Old Mother Gloam's cottage in Hag's Hollow

Drawn by Docs/tools/render3d.py from HollowCreek.json (regions.py builds them), not captured in Unity.

    python3 Docs/tools/make_images_regions.py            # both
    python3 Docs/tools/make_images_regions.py map        # just one
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_3d import label  # noqa: E402

BG = (22, 18, 14)
INK = (243, 234, 219)
MUTED = (205, 191, 171)
NOTE = "Drawn from the game's own layout by Docs/tools/render3d.py, not an engine capture."

_TOWN = None


def town():
    global _TOWN
    if _TOWN is None:
        merged, t, _ = r3.load_town()
        mesh = r3.layout_mesh(merged)
        r3.horizon_mesh(t, mesh)
        _TOWN = (merged, t, mesh)
    return _TOWN


def make_map():
    merged, t, mesh = town()
    x0, z0, x1, z1 = t["world"]
    W = 1500
    H = int(W * (z1 - z0) / (x1 - x0))
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    # Straight down (a hair off vertical so the camera has an up direction): north is up.
    cam = r3.Camera((cx, 700, cz - 0.01), (cx, 0, cz), 50, W, H, ortho=z1 - z0)
    img = r3.render(merged, cam, mesh, ss=1, moon=False, fog_density=0.0, ambient=(0.42, 0.38, 0.5), moon_color=(0.55, 0.5, 0.75))
    d = ImageDraw.Draw(img, "RGBA")

    def at(x, z):
        p = cam.project([[x, 0, z]])[0]
        return p[0], p[1]

    for c in t["curios"]:
        px, py = at(c["p"][0], c["p"][2])
        d.text((px, py), "★", font=font(15, "Bold"), fill=(255, 226, 150), anchor="mm", stroke_width=2, stroke_fill=(30, 20, 10))
    for r in t["regions"]:
        mx, mz = (r["min"][0] + r["max"][0]) / 2, (r["min"][1] + r["max"][1]) / 2
        px, py = at(mx, mz)
        label(d, (px, py - 70 if r["id"] in ("circus", "tower") else py), r["n"], 20, fill=(236, 214, 255))
    px, py = at(-20, 95)
    label(d, (px, py), "Hollow Creek", 24, fill=(255, 220, 160))
    px, py = at(395, -60)
    d.text((px, py), "the sea", font=font(18, "Bold"), fill=(170, 200, 230), anchor="mm")
    # a legend strip along the bottom
    d.rectangle([0, H - 40, W, H], fill=(14, 11, 20, 215))
    d.text((18, H - 20), "★ a curiosity (press E to read its story)   ·   roads lead out of town to all six places   ·   north is up",
           font=font(15, "Bold"), fill=MUTED, anchor="lm")
    d.text((W - 18, H - 20), "not an engine capture", font=font(13), fill=(160, 150, 140), anchor="rm")
    save_png(img, "world-map.png")


SHOTS = [
    # name, caption, camera, target, fov
    ("Ravenhold Castle", "Up in the Blackthorn Hills: walls, towers, the great hall and its crows",
     (40, 30, 360), (-40, 12, 435), 52),
    ("The Moonlight Circus", "The big top, a carousel that still turns and a Ferris wheel that never stops",
     (-226, 9, -52), (-292, 9, 4), 62),
    ("Gloamwood Tower", "Fourteen floors, a few lights on, a fire escape all the way to the roof",
     (-34, 5, -178), (18, 28, -226), 60),
    ("Saltmarsh Lighthouse", "Out on the breakwater at Gull Harbor: climb the stair to the gallery",
     (330, 16, 20), (398, 12, 70), 55),
    ("Wreckers' Beach", "The Mary Grey on the sand, beach huts, and Smugglers' Cave in the cliff",
     (296, 7, 168), (330, 4, 212), 60),
    ("Hag's Hollow", "Old Mother Gloam's crooked cottage, the cauldron, and green lights in the reeds",
     (-240, 8, -235), (-272, 2.5, -195), 58),
]


def make_regions(which=None):
    merged, t, mesh = town()
    cw, ch = 760, 430
    pad, head = 18, 96
    out = Image.new("RGB", (pad + 2 * (cw + pad), head + 3 * (ch + 52) + 40), BG)
    d = ImageDraw.Draw(out)
    d.text((pad, 26), "The haunted places past the edge of town", font=font(34, "Black"), fill=INK)
    d.text((pad, 68), "Six new places to drive out to, each with curiosities hidden in it. " + NOTE, font=font(15), fill=MUTED)
    for i, (name, cap, pos, target, fov) in enumerate(SHOTS):
        if which is not None and i not in which:
            continue
        cam = r3.Camera(pos, target, fov, cw, ch)
        img = r3.render(merged, cam, mesh, ss=2, horizon=t, horizon_t=i * 0.7, fog_density=0.0045)
        x, y = pad + (i % 2) * (cw + pad), head + (i // 2) * (ch + 52)
        out.paste(img, (x, y))
        d.text((x, y + ch + 8), name, font=font(19, "Bold"), fill=INK)
        d.text((x, y + ch + 31), cap, font=font(14), fill=MUTED)
        print("  ", name)
    save_png(out, "regions.png")


if __name__ == "__main__":
    args = set(sys.argv[1:])
    if not args or "map" in args:
        make_map()
    if not args or "regions" in args:
        make_regions()
