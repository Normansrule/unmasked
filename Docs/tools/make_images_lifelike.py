#!/usr/bin/env python3
"""
Pictures for round 46, more lifelike people and rooms:

  faces-pass.png     five faces before (round 45) and after: a nose grown out of the face, softer
                     jaws and cheeks, hair as one soft mass, on a grid twice as fine
  rooms-inside.png   standing inside four rooms: curtains at every window, things on the tables

Drawn by Docs/tools/render3d.py from Costumes.json and the layout files, not captured in Unity.

    python3 Docs/tools/make_images_lifelike.py [round45_smoothbody.py] [round45_resources_dir]
"""
import importlib.util
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
import smoothbody  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_characters import outfits, LIGHTS  # noqa: E402
from make_images_storybook import stage, BG, INK, MUTED, NEW  # noqa: E402

RES = os.path.join(r3.ROOT, "Assets", "Unmasked", "Resources")
CAST = [("Sleuth", "Sleuth"), ("Heiress", "The Heiress"), ("Cook", "The Cook"), ("Folk.Fortune", "Old Nell"), ("Folk.Mayor", "The Mayor")]
INSIDE = [("BlackwoodManor.json", "Blackwood Manor, master bedroom", 1, (-5, 6.2, 3.5), (-12, 4.6, 9)),
          ("BlackwoodManor.json", "Blackwood Manor, study", 0, (-5, 2.4, -3), (-12, 1.0, -9)),
          ("Houses/WillowLaneVictorian.json", "Willow Lane, parlor", 0, None, None),
          ("Houses/HollowCreekFarm.json", "Hollow Creek Farm, kitchen", 0, None, None)]


def face(parts, W, H):
    L = stage()
    m = r3.Mesh()
    m.add_parts(parts, (0, 0, 0), 20)
    cam = r3.Camera((0.3, 1.75, 1.25), (0, 1.68, 0), 34, W, H)
    return r3.story_grade(r3.render(L, cam, r3.layout_mesh(L), lights=LIGHTS, extra_mesh=m, fog_density=0.0, moon=False, **r3.STORYBOOK))


def make_faces(old_module):
    O = outfits(NEW)
    cw, ch = 300, 340
    out = Image.new("RGB", (16 + len(CAST) * (cw + 16), 96 + 2 * (ch + 40)), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 22), "Faces with a real nose", font=font(32, "Black"), fill=INK)
    d.text((16, 64), "Top: round 45. Bottom: the nose grows out of the face, softer jaws and cheeks, hair as one soft mass. Not an engine capture.",
           font=font(14), fill=MUTED)
    for row in (0, 1):
        if row == 0 and old_module:
            spec = importlib.util.spec_from_file_location("smoothbody", old_module)
            old = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(old)
            sys.modules["smoothbody"] = old
        else:
            sys.modules["smoothbody"] = smoothbody
        for i, (cid, name) in enumerate(CAST):
            x, y = 16 + i * (cw + 16), 96 + row * (ch + 40)
            out.paste(face(O[cid], cw, ch), (x, y))
            d.text((x, y + ch + 8), f"{name}, {'after' if row else 'before'}", font=font(14, "Bold"), fill=INK if row else MUTED)
            print("  ", name, "after" if row else "before")
    sys.modules["smoothbody"] = smoothbody
    save_png(out, "faces-pass.png")


def inside(path, title, level, eye, target, W, H):
    with open(path) as f:
        L = json.load(f)
    for k in r3._LIST_KEYS:
        L.setdefault(k, [])
    if eye is None:  # stand in a doorway-ish corner of the named room, looking across it
        name = title.split(", ")[1].lower()
        r = next(r for r in L["rooms"] if name in r["n"].lower())
        (x0, y0, z0), (x1, _, z1) = r["min"], r["max"]
        eye = (x0 + 0.5, y0 + 2.6, z0 + 0.5)
        target = (x1 - 1.2, y0 + 0.5, z1 - 1.2)
    mesh = r3.layout_mesh(L, levels=[level], cut_level=level, roof=False, grounds=False, window_glow=0.4, cut_height=3.0)
    return r3.render(L, r3.Camera(eye, target, 62, W, H), mesh, fog_density=0.002, light_boost=1.4, ambient=(0.3, 0.28, 0.34), moon=False)


def make_inside(old_dir):
    W, H = 560, 350
    cols = 2 if old_dir else 1
    out = Image.new("RGB", (16 + cols * (W + 16), 96 + len(INSIDE) * (H + 40)), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 22), "Standing in the rooms", font=font(32, "Black"), fill=INK)
    d.text((16, 64), ("Left: round 45. Right: " if old_dir else "") + "curtains on brass rods at every window, and teacups, books, candles, pies and flowers on the tables. Not an engine capture.",
           font=font(14), fill=MUTED)
    for row, (rel, title, level, eye, target) in enumerate(INSIDE):
        for col, base in enumerate(([old_dir] if old_dir else []) + [RES]):
            x, y = 16 + col * (W + 16), 96 + row * (H + 40)
            out.paste(inside(os.path.join(base, rel), title, level, eye, target, W, H), (x, y))
            after = base == RES
            d.text((x, y + H + 8), f"{title}{', after' if old_dir and after else ', before' if old_dir else ''}", font=font(14, "Bold"), fill=INK if after else MUTED)
            print("  ", title, "after" if after else "before")
    save_png(out, "rooms-inside.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    make_faces(args[0] if args else None)
    make_inside(args[1] if len(args) > 1 else None)
