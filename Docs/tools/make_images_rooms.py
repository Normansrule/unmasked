#!/usr/bin/env python3
"""
Pictures for round 45, realistic people and rooms full of things:

  smooth-cast.png    the cast before (separate toy pieces) and after (one smooth skin, smoothbody.py)
  rooms-full.png     rooms before and after roomdetail.py dressed them, walls cut away

Drawn by Docs/tools/render3d.py from Costumes.json and the layout files, not captured in Unity.

    python3 Docs/tools/make_images_rooms.py [old_layout_dir]   # old_layout_dir: round 44's Resources
"""
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_characters import outfits, LIGHTS  # noqa: E402
from make_images_storybook import stage, BG, INK, MUTED, NEW  # noqa: E402

RES = os.path.join(r3.ROOT, "Assets", "Unmasked", "Resources")
CAST = [("Sleuth", "Sleuth"), ("Heiress", "The Heiress"), ("Brawn", "Brawn"), ("Folk.Fortune", "Old Nell"), ("Cook", "The Cook")]
ROOMS = [("Houses/WillowLaneVictorian.json", "Willow Lane upstairs", 1, (8, 17, -15), (1, 3.2, -1)),
         ("BlackwoodManor.json", "Blackwood Manor upstairs", 1, (-2, 20, -22), (-10, 3.5, -4)),
         ("Houses/HollowCreekFarm.json", "Hollow Creek Farm downstairs", 0, (6, 17, -17), (-1, 0, -1))]


def figure(parts, smooth, W, H, face=False):
    L = stage()
    m = r3.Mesh()
    m.add_parts(parts, (0, 0, 0), 20, smooth=smooth)
    cam = r3.Camera((0.25, 1.6, 1.5), (0, 1.5, 0), 34, W, H) if face else r3.Camera((0.5, 1.25, 3.6), (0, 1.05, 0), 34, W, H)
    return r3.story_grade(r3.render(L, cam, r3.layout_mesh(L), lights=LIGHTS, extra_mesh=m, fog_density=0.0, moon=False, **r3.STORYBOOK))


def make_cast():
    O = outfits(NEW)
    cw, ch, fh = 300, 420, 220
    out = Image.new("RGB", (16 + len(CAST) * (cw + 16), 96 + 2 * (ch + fh + 48)), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 22), "Real bodies, not toy pieces", font=font(32, "Black"), fill=INK)
    d.text((16, 64), "Top: round 44, separate capsules and balls. Bottom: one smooth skin per person. Not an engine capture.", font=font(14), fill=MUTED)
    for row, smooth in enumerate((False, True)):
        for i, (cid, name) in enumerate(CAST):
            x, y = 16 + i * (cw + 16), 96 + row * (ch + fh + 48)
            out.paste(figure(O[cid], smooth, cw, ch), (x, y))
            out.paste(figure(O[cid], smooth, cw, fh, face=True), (x, y + ch + 4))
            d.text((x, y + ch + fh + 12), f"{name}, {'after' if smooth else 'before'}", font=font(14, "Bold"), fill=INK if smooth else MUTED)
            print("  ", name, "after" if smooth else "before")
    save_png(out, "smooth-cast.png")


def cutaway(path, level, eye, target, W, H):
    with open(path) as f:
        L = json.load(f)
    for k in r3._LIST_KEYS:
        L.setdefault(k, [])
    mesh = r3.layout_mesh(L, levels=[level], cut_level=level, roof=False, grounds=False, window_glow=0.4, cut_height=1.3)
    return r3.render(L, r3.Camera(eye, target, 44, W, H), mesh, fog_density=0.002, light_boost=1.4, ambient=(0.27, 0.25, 0.32), moon=False)


def make_rooms(old_dir):
    W, H = 560, 380
    out = Image.new("RGB", (16 + 2 * (W + 16), 96 + len(ROOMS) * (H + 40)), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 22), "Rooms full of things", font=font(32, "Black"), fill=INK)
    d.text((16, 64), "Left: round 44. Right: beds, wardrobes, desks, bookcases, pianos, paintings and rugs in every room. Walls cut away. Not an engine capture.",
           font=font(14), fill=MUTED)
    for row, (rel, title, level, eye, target) in enumerate(ROOMS):
        for col, base in enumerate((old_dir, RES)):
            x, y = 16 + col * (W + 16), 96 + row * (H + 40)
            out.paste(cutaway(os.path.join(base, rel), level, eye, target, W, H), (x, y))
            d.text((x, y + H + 8), f"{title}, {'after' if col else 'before'}", font=font(14, "Bold"), fill=INK if col else MUTED)
            print("  ", title, "after" if col else "before")
    save_png(out, "rooms-full.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] != ["rooms"]:
        make_cast()
    if args and args[-1] != "cast":
        make_rooms(args[-1])
