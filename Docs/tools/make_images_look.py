#!/usr/bin/env python3
"""
The Halloween look up close, for the README and Docs/ART_DIRECTION.md:

  carvings.png        every jack-o'-lantern carving, side by side
  nights-of-jack.png  the set pieces around town (arches, a jack-o'-lantern tree, porches, string lights)
  before-after.png    the houses before and after the detail pass (needs a "before" house-cards.png)

    python3 Docs/tools/make_images_look.py                 # carvings and set pieces
    python3 Docs/tools/make_images_look.py before OLD.png  # the comparison, from an older house-cards.png

Rendered from the same files Unity builds the town from. Illustrations, not in-engine captures.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_3d import label, timed, INK, MUTED  # noqa: E402

KINDS = [("jack", "Classic"), ("jack_grin", "Toothy grin"), ("jack_scary", "Angry"), ("jack_surprised", "Surprised"),
         ("jack_wink", "Wink"), ("jack_tall", "Tall"), ("jack_white", "Ghost white")]


@timed("carvings")
def make_carvings():
    props = r3.costumes()["props"]
    W, H, gap = 980, 300, 1.15
    m = r3.Mesh()
    n = len(KINDS)
    m.add_shape("box", (0, -0.05, -3), (n * gap + 12, 0.1, 14), (0, 0, 0), (0.16, 0.2, 0.14), surface=r3.SURFACE_ID["grass"])
    lights = []
    xs = [(i - (n - 1) / 2) * gap for i in range(n)]
    for (kind, _), x in zip(KINDS, xs):
        m.add_parts(props[kind]["parts"], (-x, 0, 0), 0, 1.45)
        lights.append({"p": [-x, 0.42, 0.05], "c": [1, 0.62, 0.25], "range": 1.3, "intensity": 1.2})
        lights.append({"p": [-x + 0.3, 1.1, 1.4], "c": [1, 0.75, 0.5], "range": 2.6, "intensity": 0.9})
    for k in range(8):  # gourds and little pumpkins between them, a step back
        m.add_parts(props["pumpkin" if k % 2 else "gourds"]["parts"], (-(k - 3.5) * gap, 0, -0.55), k * 40, 0.5 if k % 2 else 1.0)
    cam = r3.Camera((0, 1.0, 5.2), (0, 0.45, 0), 34, W, H)
    img = r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.03, ambient=(0.24, 0.2, 0.34),
                    moon_color=(0.35, 0.3, 0.55), moon=False)
    d = ImageDraw.Draw(img, "RGBA")
    for (kind, name), x in zip(KINDS, xs):
        sx, sy, _ = cam.project([-x, 0, 0.6])[0]
        label(d, (sx, H - 22), name, 13, INK)
    label(d, (W / 2, 22), "No two alike: the town's jack-o'-lanterns pick from these carvings", 15, (255, 200, 120))
    save_png(img, "carvings.png")


# Set pieces: (title, caption, camera position, target), in town coordinates
def _lot(lot_id):
    return next(l for l in r3.load_town()[1]["lots"] if l["id"] == lot_id)["offset"]


@timed("setpieces")
def make_setpieces():
    merged, town, houses = r3.load_town()
    off = {lot["id"]: lot["offset"] for lot in town["lots"]}

    def at(lot, x, y, z):
        o = off[lot]
        return (o[0] + x, o[1] + y, o[2] + z)

    shots = [
        ("Porch display", "cornstalks, mums, a pumpkin stack, a wreath",
         at("PembertonCottage", 3.2, 1.7, -10.2), at("PembertonCottage", -0.2, 1.0, -5.6)),
        ("Jack-o'-lantern arch", "over the cottage gate and into the square",
         at("PembertonCottage", 2.4, 1.6, -19.0), at("PembertonCottage", 0.0, 1.9, -12.7)),
        ("Jack-o'-lantern tree", "the Victorian's back garden",
         at("WillowLaneVictorian", -2.5, 2.4, 11.0), at("WillowLaneVictorian", -7.0, 2.0, 17.5)),
        ("String lights", "the Victorian's wraparound porch",
         at("WillowLaneVictorian", 6.0, 2.6, -17.0), at("WillowLaneVictorian", -1.0, 2.0, -8.5)),
        ("Into the corn maze", "a lit arch at the farm",
         at("HollowCreekFarm", -19.5, 1.9, -24.0), at("HollowCreekFarm", -22.5, 1.9, -16.7)),
        ("Main Street", "lights across the road downtown",
         (2.5, 2.0, -66.0), (-1.0, 3.0, -30.0)),
    ]
    TW, TH, cols = 420, 250, 3
    rows = math.ceil(len(shots) / cols)
    sheet = Image.new("RGB", (cols * TW + (cols + 1) * 10, rows * (TH + 10) + 10 + 44), (14, 10, 24))
    d = ImageDraw.Draw(sheet)
    d.text((sheet.width / 2, 24), "Nights of the Jack, around Hollow Creek", font=font(18), fill=(255, 200, 120), anchor="mm")
    print("  building the town mesh...")
    mesh = r3.layout_mesh(merged)
    all_lights = r3.all_lights(merged)
    for i, (title, caption, pos, tgt) in enumerate(shots):
        cam = r3.Camera(pos, tgt, 52, TW, TH)
        p = np.array(pos)
        lights = [lt for lt in all_lights if np.linalg.norm(np.array(lt["p"]) - p) < 45 + lt["range"]]
        img = r3.render(merged, cam, mesh, lights=lights, fog_density=0.012, light_boost=1.25, ambient=(0.19, 0.15, 0.3))
        dd = ImageDraw.Draw(img, "RGBA")
        dd.rounded_rectangle([8, TH - 52, TW - 8, TH - 8], radius=8, fill=(10, 8, 20, 190))
        dd.text((18, TH - 44), title, font=font(15), fill=INK)
        dd.text((18, TH - 24), caption, font=font(12), fill=MUTED)
        x, y = 10 + (i % cols) * (TW + 10), 44 + (i // cols) * (TH + 10)
        sheet.paste(img, (x, y))
        print(f"    {title} done")
    save_png(sheet, "nights-of-jack.png")


def make_before_after(old_path):
    """Before/after: the cottage and the Victorian from an older house-cards.png and the current one."""
    here = os.path.join(r3.ROOT, "Docs", "images", "house-cards.png")
    old, new = Image.open(old_path).convert("RGB"), Image.open(here).convert("RGB")
    panels = [(10, 10, 410, 260), (10, 746, 410, 996)]  # outside views: cottage, Victorian
    W = 2 * 400 + 30
    out = Image.new("RGB", (W, 40 + len(panels) * 260), (14, 10, 24))
    d = ImageDraw.Draw(out)
    d.text((10 + 200, 22), "Before", font=font(17), fill=MUTED, anchor="mm")
    d.text((20 + 400 + 200, 22), "After", font=font(15), fill=(255, 200, 120), anchor="mm")
    for k, box in enumerate(panels):
        y = 40 + k * 260
        out.paste(old.crop(box), (10, y))
        out.paste(new.crop(box), (20 + 400, y))
    save_png(out, "before-after.png")


JOBS = {"carvings": make_carvings, "setpieces": make_setpieces}

if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["before"]:
        make_before_after(args[1])
    else:
        for name in args or list(JOBS):
            print(f"  rendering {name}...")
            JOBS[name]()
