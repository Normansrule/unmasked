#!/usr/bin/env python3
"""
Pictures for round 44, nicer people and livelier streets:

  cast-pass.png     five of the cast before (round 43) and after: chunky storybook hands instead of
                    thin spread fingers, and skirts and coat tails that flare like cloth
  street-life.png   Hollow Creek's sidewalks with their new trees, hydrants, post boxes, bins,
                    newspaper boxes and street signs (Docs/tools/streetlife.py)

Drawn by Docs/tools/render3d.py from Costumes.json and HollowCreek.json, not captured in Unity.

    python3 Docs/tools/make_images_storybook.py [old/Costumes.json]   # both
    python3 Docs/tools/make_images_storybook.py street                # just the streets
"""
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_characters import outfits, LIGHTS  # noqa: E402

BG = (22, 18, 14)
INK = (243, 234, 219)
MUTED = (205, 191, 171)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NEW = os.path.join(ROOT, "Assets", "Unmasked", "Resources", "Costumes.json")
CAST = [("Sleuth", "Sleuth"), ("Heiress", "The Heiress"), ("Folk.Fortune", "Old Nell"), ("Snacker", "Snacker"), ("Cook", "The Cook")]


def stage():
    L = {"boxes": [{"n": "Floor", "t": "box", "p": [0, -0.05, 0], "s": [8, 0.1, 8], "r": [0, 0, 0], "c": [0.2, 0.17, 0.15], "m": "solid", "l": 0, "g": "ground"}],
         "lights": [], "glows": [], "decor": [], "name": "stage"}
    for k in r3._LIST_KEYS:
        L.setdefault(k, [])
    return L


def figure(L, parts, W, H):
    m = r3.Mesh()
    m.add_parts(parts, (0, 0, 0), 20)
    cam = r3.Camera((0.5, 1.25, 3.6), (0, 1.05, 0), 34, W, H)
    return r3.story_grade(r3.render(L, cam, r3.layout_mesh(L), lights=LIGHTS, extra_mesh=m, fog_density=0.0, moon=False, **r3.STORYBOOK))


def make_cast(old_path):
    old, new = outfits(old_path), outfits(NEW)
    L = stage()
    cw, ch = 300, 420
    out = Image.new("RGB", (16 + len(CAST) * (cw + 16), 96 + 2 * (ch + 40)), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 22), "Nicer people", font=font(32, "Black"), fill=INK)
    d.text((16, 64), "Top: round 43. Bottom: chunky storybook hands, and skirts and coat tails that flare like cloth. Not an engine capture.",
           font=font(14), fill=MUTED)
    for row, src in enumerate((old, new)):
        for i, (cid, name) in enumerate(CAST):
            x, y = 16 + i * (cw + 16), 96 + row * (ch + 40)
            out.paste(figure(L, src[cid], cw, ch), (x, y))
            d.text((x, y + ch + 8), f"{name}, {'after' if row else 'before'}", font=font(14, "Bold"), fill=INK if row else MUTED)
            print("  ", name, "after" if row else "before")
    save_png(out, "cast-pass.png")


def make_street():
    merged, t, _ = r3.load_town()
    mesh = r3.layout_mesh(merged)
    r3.horizon_mesh(t, mesh)
    shots = [("Main Street, looking north", (3.2, 1.7, 70.0), (7.5, 1.2, 100.0)),
             ("A corner sign on Main Street", (2.8, 2.0, -97.0), (6.3, 1.8, -91.0)),
             ("Elm Street", (6.0, 1.7, -3.0), (40.0, 1.2, -8.0)),
             ("Over the rooftops", (-10.0, 14.0, -110.0), (-10.0, 0.0, -50.0))]
    cw, ch, pad, head = 700, 394, 16, 96
    out = Image.new("RGB", (pad + 2 * (cw + pad), head + 2 * (ch + 40) + 10), BG)
    d = ImageDraw.Draw(out)
    d.text((pad, 24), "Life along the streets", font=font(32, "Black"), fill=INK)
    d.text((pad, 66), "Autumn trees with fallen leaves, hydrants, post boxes, bins, newspaper boxes and street signs on every sidewalk. Not an engine capture.",
           font=font(14), fill=MUTED)
    for i, (label, p, tg) in enumerate(shots):
        img = r3.render(merged, r3.Camera(p, tg, 58, cw, ch), mesh, ss=2, horizon=t, fog_density=0.006,
                        ambient=(0.16, 0.13, 0.24), light_boost=1.5)
        x, y = pad + (i % 2) * (cw + pad), head + (i // 2) * (ch + 40)
        out.paste(img, (x, y))
        d.text((x, y + ch + 8), label, font=font(16, "Bold"), fill=INK)
        print("  ", label)
    save_png(out, "street-life.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] != ["street"]:
        make_cast(args[0] if args else NEW)
    if not args or args[:1] == ["street"] or args[0].endswith(".json"):
        make_street()
