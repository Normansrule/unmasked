#!/usr/bin/env python3
"""
README images for round 19: the people of Hollow Creek (the "folk" block of HollowCreek.json that
Town/Townsperson.cs reads, dressed by make_costumes.py FOLK) and the errands they send the club on.

    python3 Docs/tools/make_images_folk.py                # everything
    python3 Docs/tools/make_images_folk.py folk errand    # just some
"""
import os
import sys
import textwrap

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_3d import label, title_text  # noqa: E402

_TOWN = None


def town():
    global _TOWN
    if _TOWN is None:
        merged, t, _ = r3.load_town()
        mesh = r3.layout_mesh(merged)
        r3.horizon_mesh(t, mesh)
        _TOWN = (merged, t, mesh)
    return _TOWN


def outfit(fid):
    return r3.costumes()["suspects"]["Folk." + fid]["parts"]


def bubble(img, at, text, width=34, size=14):
    """A speech bubble with a tail pointing down at `at` (screen x, y)."""
    d = ImageDraw.Draw(img, "RGBA")
    lines = textwrap.wrap(text, width)
    f = font(size, "Medium")
    w = max(d.textlength(ln, font=f) for ln in lines) + 28
    h = len(lines) * (size + 6) + 18
    x0 = min(max(10, at[0] - w / 2), img.width - w - 10)
    y0 = max(10, at[1] - h - 18)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=14, fill=(250, 240, 220, 240), outline=(120, 80, 50), width=2)
    d.polygon([(at[0] - 9, y0 + h - 1), (at[0] + 9, y0 + h - 1), (at[0], y0 + h + 16)], fill=(250, 240, 220, 240))
    for i, ln in enumerate(lines):
        d.text((x0 + 14, y0 + 10 + i * (size + 6)), ln, font=f, fill=(60, 40, 30))


def make_folk():
    """The five townsfolk side by side, with who they are and what they've lost."""
    t = r3.load_town()[1]
    folk = t["folk"]
    W, H = 1500, 640
    m = r3.Mesh()
    m.add_shape("box", (0, -0.1, 0), (40, 0.2, 24), (0, 0, 0), (0.12, 0.09, 0.13))
    xs = [(2 - i) * 1.25 for i in range(len(folk))]  # this camera looks down -z, so +x is on the left
    for x, f in zip(xs, folk):
        m.add_parts(outfit(f["id"]), (x, 0, 0), -10 if x > 0 else (10 if x < 0 else 0))
    lights = [{"p": [-3.0, 2.8, 2.6], "c": [1.0, 0.72, 0.45], "range": 9, "intensity": 1.4},
              {"p": [3.0, 2.8, 2.6], "c": [0.75, 0.8, 1.0], "range": 9, "intensity": 1.3},
              {"p": [0.0, 1.0, 1.8], "c": [1.0, 0.55, 0.25], "range": 4, "intensity": 0.8}]
    cam = r3.Camera((0, 1.55, 7.6), (0, 1.15, 0), 30, W, H)
    img = r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.0, ambient=(0.24, 0.19, 0.3), moon=False)
    d = ImageDraw.Draw(img, "RGBA")
    for x, f in zip(xs, folk):
        p = cam.project((x, 0.0, 0.6))[0]
        y = min(H - 70, p[1] + 4)
        label(d, (p[0], y), f["name"], 14)
        d.text((p[0], y + 21), f["job"], font=font(12, "Medium"), fill=(200, 190, 225), anchor="mm")
        d.text((p[0], y + 39), "lost: " + f["itemName"], font=font(12, "Bold"), fill=(255, 196, 110), anchor="mm")
    title_text(img, "The people of Hollow Creek", "Talk to them for the town's side of the story. Each has lost something tonight.", 0.09)
    save_png(img, "townsfolk.png")


def scene_with(extra):
    """The town mesh plus characters and props placed in town coordinates: [(parts, pos, ry, scale)]."""
    m = r3.Mesh()
    for parts, pos, ry, sc in extra:
        m.add_parts(parts, pos, ry, sc)
    return m


def make_errand():
    """Old Nell at her stall asking for her cat, and Midnight found glowing among the headstones."""
    merged, t, mesh = town()
    nell = next(f for f in t["folk"] if f["id"] == "Fortune")
    props = r3.costumes()["props"]
    all_lights = r3.all_lights(merged)
    VW, VH = 760, 470

    def shot(eye, target, extra, extra_lights):
        cam = r3.Camera(eye, target, 52, VW, VH)
        p = np.array(eye)
        lights = [lt for lt in all_lights if np.linalg.norm(np.array(lt["p"]) - p) < 50 + lt["range"]] + extra_lights
        img = r3.render(merged, cam, mesh, extra_mesh=scene_with(extra), lights=lights, horizon=t, horizon_t=1.0,
                        fog_density=0.01, light_boost=1.2, ambient=(0.2, 0.16, 0.3))
        return cam, img

    # 1. At the stall: Nell asks, a Solver listens
    nx, _, nz = nell["p"]
    solver = r3.costumes()["solvers"]["Sleuth"]["parts"]
    cam, a = shot((nx + 2.6, 2.0, nz - 4.4), (nx - 0.4, 1.2, nz - 0.4),
                  [(outfit("Fortune"), (nx, 0, nz), 200, 1.0), (solver, (nx - 1.3, 0, nz - 1.7), 37, 1.0)], [])
    head = cam.project((nx, 2.2, nz))[0]
    bubble(a, (head[0], head[1]), nell["ask"])
    # 2. In the churchyard: Midnight, glowing so she can be found in the dark
    ix, iy, iz = nell["itemP"]
    glow = [{"p": [ix, 0.8, iz], "c": [1.0, 0.8, 0.45], "range": 3.5, "intensity": 1.2}]
    cam, b = shot((ix + 0.3, 1.9, iz - 3.4), (ix, 0.35, iz), [(props["cat"]["parts"], (ix, 0, iz), nell["itemRy"], 1.0)], glow)
    cat = cam.project((ix, 0.6, iz))[0]
    label(ImageDraw.Draw(b, "RGBA"), (cat[0], cat[1] - 46), "Pick up Midnight the cat  [E]", 14, fill=(255, 220, 160))

    W, H = 2 * VW + 30, VH + 150
    img = Image.new("RGB", (W, H), (16, 12, 26))
    img.paste(a, (10, 120))
    img.paste(b, (VW + 20, 120))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((W / 2, 36), "Errands around town", font=font(34, "Black"), fill=(255, 200, 120), anchor="mm")
    d.text((W / 2, 76), "Find what they lost and bring it back: they'll vouch for the club, one more alibi check on the case.",
           font=font(15, "Medium"), fill=(225, 215, 240), anchor="mm")
    d.text((20, 100), "1. Old Nell at her festival stall", font=font(14, "Bold"), fill=(255, 220, 160))
    d.text((VW + 30, 100), "2. Midnight, among the headstones behind the church", font=font(14, "Bold"), fill=(255, 220, 160))
    save_png(img, "errands.png")


JOBS = {"folk": make_folk, "errand": make_errand}

if __name__ == "__main__":
    for job in sys.argv[1:] or list(JOBS):
        print(f"  {job}...", flush=True)
        JOBS[job]()
