#!/usr/bin/env python3
"""
Pictures for round 38:

  lamplighter.png  Tobias Wick, the old lamplighter: front, three-quarter and side (the stoop),
                   with his lighting pole, and a creekside gas lamp dark and lit
                   (Costumes.json "Folk.Lamplighter" and Town/Lamplighter.cs, same shapes and numbers)
  creekside.png    the Creekside Path at night: lamps lit along the bank, two still dark, Tobias on
                   his bench by the bridge

Drawn by Docs/tools/render3d.py, not captured in Unity.

    python3 Docs/tools/make_images_lamplighter.py
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_porch import Builder  # noqa: E402

BG = (22, 18, 14)
INK = (243, 234, 219)
MUTED = (205, 191, 171)
FAINT = (162, 147, 127)
HERE = os.path.dirname(os.path.abspath(__file__))
COSTUMES = os.path.join(HERE, "..", "..", "Assets", "Unmasked", "Resources", "Costumes.json")

IRON, IRON_DARK = (0.16, 0.17, 0.18), (0.09, 0.1, 0.11)
GLASS_DARK, GLASS_LIT = (0.18, 0.24, 0.27), (1.0, 0.76, 0.4)
PILOT, FLAME, MOTH = (0.35, 0.6, 1.0), (1.0, 0.85, 0.5), (0.75, 0.7, 0.6)
ASH, BRASS = (0.55, 0.42, 0.28), (0.85, 0.68, 0.32)
WOOD = (0.36, 0.24, 0.15)
HEAD_Y = 3.25


def tobias_parts():
    with open(COSTUMES) as f:
        return next(o for o in json.load(f)["suspects"] if o["id"] == "Folk.Lamplighter")["parts"]


def pole(b):
    """Lamplighter.BuildPole."""
    b.part("cyl", (0, 1.42, 0), (0.045, 1.42, 0.045), ASH)
    b.part("cyl", (0, 2.86, 0), (0.06, 0.05, 0.06), BRASS)
    b.part("cube", (0.05, 2.98, 0), (0.1, 0.025, 0.025), BRASS)
    b.part("cube", (0.1, 2.94, 0), (0.025, 0.08, 0.025), BRASS)
    b.part("cyl", (-0.03, 2.96, 0), (0.02, 0.06, 0.02), BRASS)
    b.part("sphere", (-0.03, 3.05, 0), (0.05, 0.08, 0.05), (1.0, 0.72, 0.3), glow=2.0)


def lamp(b, lit, t=0.0):
    """CreekLamp.Build: base, fluted post, ladder bar, arm and the four-paned head."""
    b.part("cyl", (0, 0.12, 0), (0.42, 0.12, 0.42), IRON_DARK)
    b.part("cyl", (0, 0.32, 0), (0.3, 0.1, 0.3), IRON)
    b.part("cyl", (0, 1.6, 0), (0.12, 1.3, 0.12), IRON)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        b.part("cube", (math.cos(a) * 0.075, 0.95, math.sin(a) * 0.075), (0.035, 1.1, 0.035), IRON_DARK, (0, -math.degrees(a), 0))
    b.part("cyl", (0, 1.55, 0), (0.17, 0.04, 0.17), IRON_DARK)
    b.part("cube", (0, 2.75, 0), (0.7, 0.05, 0.05), IRON)
    for s in (-1, 1):
        b.part("sphere", (s * 0.36, 2.75, 0), (0.08,) * 3, IRON_DARK)
    b.part("cyl", (0, 2.95, 0), (0.09, 0.1, 0.09), IRON_DARK)
    b.part("cube", (0, 3.06, 0.18), (0.05, 0.05, 0.4), IRON)
    b.part("cyl", (0, 3.0, 0.36), (0.05, 0.05, 0.05), IRON, (90, 0, 0))
    hy, hz = HEAD_Y - 0.15, 0.35
    b.part("cyl", (0, hy - 0.04, hz), (0.3, 0.03, 0.3), IRON)
    b.part("cube", (0, hy + 0.2, hz), (0.3, 0.42, 0.3), GLASS_LIT if lit else GLASS_DARK, (0, 45, 0), glow=1.6 if lit else False)
    for i in range(4):
        a = i * math.pi / 2
        b.part("cube", (math.cos(a) * 0.215, hy + 0.2, hz + math.sin(a) * 0.215), (0.025, 0.46, 0.025), IRON_DARK)
    b.part("cyl", (0, hy + 0.44, hz), (0.38, 0.035, 0.38), IRON)
    b.part("cyl", (0, hy + 0.5, hz), (0.26, 0.04, 0.26), IRON)
    b.part("cyl", (0, hy + 0.56, hz), (0.14, 0.04, 0.14), IRON)
    b.part("sphere", (0, hy + 0.64, hz), (0.07, 0.1, 0.07), IRON_DARK)
    if lit:
        b.part("sphere", (0, hy + 0.14, hz), (0.08, 0.14, 0.08), FLAME, glow=2.4)
        for i in range(2):
            a = t * (2.2 + i * 0.7) + i * 3
            rr = 0.32 + 0.05 * i
            b.part("sphere", (math.cos(a) * rr, hy + 0.25 + math.sin(a * 1.7) * 0.12, hz + math.sin(a) * rr), (0.05, 0.012, 0.03), MOTH, (0, -math.degrees(a), 30))
    else:
        b.part("sphere", (0, hy + 0.14, hz), (0.05, 0.07, 0.05), PILOT, glow=1.6)


def lamp_light(at, ry=0.0):
    """Where CreekLamp's Glow sits, in the world: head + (0, 0.15, 0.2)."""
    a = math.radians(ry)
    lx, lz = 0.0, 0.35 + 0.2
    return {"p": [at[0] + lx * math.cos(a) + lz * math.sin(a), HEAD_Y, at[2] - lx * math.sin(a) + lz * math.cos(a)],
            "c": [1.0, 0.78, 0.46], "range": 10, "intensity": 1.25}


def tobias(m, parts, at, ry, with_pole=True, bench=False):
    m.add_parts(parts, at, ry)
    if with_pole:
        # Lamplighter.Build: poleHome at (0.5, 0.04, 0.1) in his turn, leaning a touch.
        a = math.radians(ry)
        x, z = 0.47, 0.06
        b = Builder(m, (at[0] + x * math.cos(a) + z * math.sin(a), at[1] + 0.04, at[2] - x * math.sin(a) + z * math.cos(a)), ry)
        pole(b)
    if bench:
        a = math.radians(ry)
        bz = -1.1
        b = Builder(m, (at[0] + bz * math.sin(a), 0, at[2] + bz * math.cos(a)), ry)
        b.part("cube", (0, 0.45, 0), (1.6, 0.06, 0.45), WOOD)
        b.part("cube", (0, 0.78, -0.2), (1.6, 0.3, 0.05), WOOD, (-10, 0, 0))
        for s in (-1, 1):
            b.part("cube", (s * 0.7, 0.22, 0), (0.06, 0.44, 0.4), IRON_DARK)


def make_sheet():
    L = r3.load_layout()
    sb = r3.STORYBOOK
    parts = tobias_parts()
    gap, top = 24, 96
    TW, TH = 300, 520
    views = [("Front", 180), ("Three-quarter", 215), ("Side: the stoop", 270)]
    tiles = []
    for name, ry in views:
        m = r3.Mesh()
        m.add_shape("box", (0, -0.05, 0), (6, 0.1, 6), (0, 0, 0), (0.17, 0.14, 0.12))
        tobias(m, parts, (0, 0, 0), ry)
        cam = r3.Camera((0, 1.8, -6.6), (0, 1.58, 0), 33, TW, TH)
        pic = r3.render(L, cam, m, lights=[{"p": [-1.6, 2.6, -2.4], "c": [1.0, 0.84, 0.62], "range": 9, "intensity": 1.15},
                                           {"p": [1.8, 1.8, 1.6], "c": [0.55, 0.8, 0.95], "range": 8, "intensity": 0.6},
                                           {"p": [-0.1, 3.4, -0.2], "c": [1.0, 0.72, 0.4], "range": 3, "intensity": 0.6}],
                        fog_density=0.0, moon=False, **sb)
        tiles.append((name, r3.story_grade(pic)))
    LW, LH = 230, TH
    lamps = []
    for name, lit in (("Dark: a blue pilot", False), ("Lit: amber, and moths", True)):
        m = r3.Mesh()
        m.add_shape("box", (0, -0.05, 0), (6, 0.1, 6), (0, 0, 0), (0.17, 0.14, 0.12))
        lamp(Builder(m, (0, 0, 0), 180), lit, 1.3)
        lights = [{"p": [-1.8, 2.4, -2.8], "c": [0.55, 0.75, 0.9], "range": 9, "intensity": 0.7}]
        if lit:
            lights.append({"p": [0, HEAD_Y, -0.55], "c": [1.0, 0.78, 0.46], "range": 10, "intensity": 1.25})
        cam = r3.Camera((0, 2.0, -7.4), (0, 1.78, 0), 33, LW, LH)
        pic = r3.render(L, cam, m, lights=lights, fog_density=0.0, moon=False, **sb)
        lamps.append((name, r3.story_grade(pic)))
    W = gap + 3 * (TW + gap) + 2 * (LW + gap) + gap
    H = top + TH + 150
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((gap, 22), "Tobias Wick, the lamplighter", font=font(34, "Black"), fill=INK)
    d.text((gap, 64), "He has lit the creek lamps every Halloween since he was your age. Tonight his knees won't do the bank, so he lends you the pole.",
           font=font(15, "Medium"), fill=MUTED)
    x = gap
    for name, pic in tiles:
        img.paste(pic, (x, top))
        d.text((x, top + TH + 8), name, font=font(15, "Bold"), fill=INK)
        x += TW + gap
    x += gap
    for name, pic in lamps:
        img.paste(pic, (x, top))
        d.text((x, top + TH + 8), name, font=font(15, "Bold"), fill=INK)
        x += LW + gap
    notes = ("Tall, lanky and stooped. Plum greatcoat with brass buttons, a mustard muffler, flat cap with a brass lamp badge, "
             "round spectacles, bushy white brows and mutton-chop whiskers.")
    d.text((gap, top + TH + 40), notes, font=font(14, "Medium"), fill=MUTED)
    d.text((gap, top + TH + 62), "The gas lamp: a fluted iron post with a ladder bar, a curled arm, and a four-paned head with a pitched cap.",
           font=font(14, "Medium"), fill=MUTED)
    d.text((W / 2, H - 20), "Drawn by Docs/tools/render3d.py with Costumes.json and Lamplighter.cs's own shapes, not an engine capture",
           font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "lamplighter.png")


def make_scene():
    L = r3.load_layout()
    sb = r3.STORYBOOK
    parts = tobias_parts()
    m = r3.Mesh()
    # A stretch of the north bank, in the town's own numbers (creek at z 0 here, creekZ in town).
    m.add_shape("box", (0, -0.25, 14), (120, 0.5, 20), (0, 0, 0), (0.16, 0.2, 0.13))          # the north bank
    m.add_shape("box", (0, -0.25, -16), (120, 0.5, 20), (0, 0, 0), (0.15, 0.19, 0.12))        # the south bank
    m.add_shape("box", (0, -0.12, -1), (120, 0.06, 10.0), (0, 0, 0), (0.1, 0.2, 0.27))       # the creek
    m.add_shape("box", (0, -0.02, 11.5), (90, 0.08, 2.6), (0, 0, 0), (0.42, 0.35, 0.27))     # the Creekside Path
    # The bridge where Main Street crosses (town x -12..12 is -2..22 here: x is town x + 10)
    m.add_shape("box", (10, 0.3, -1), (24, 0.3, 18), (0, 0, 0), (0.36, 0.32, 0.3))
    for s in (-1, 1):
        m.add_shape("box", (10 + s * 11.6, 0.75, -1), (0.4, 0.7, 18), (0, 0, 0), (0.42, 0.38, 0.35))
    m.add_shape("box", (10, 0.0, 12), (24, 0.1, 10), (0, 0, 0), (0.12, 0.12, 0.14))           # Main Street
    for i in range(22):  # reeds along the water's edge
        x = -60 + i * 3.1
        if -3 < x < 23:
            continue
        m.add_shape("box", (x, 0.35, 4.4 + (i % 3) * 0.35), (0.05, 0.55, 0.05), (0, 0, (i % 5 - 2) * 6), (0.22, 0.3, 0.16))
    xs = [x + 10 for x in (-66, -42, -18, 18, 36)]
    lights = []
    for k, x in enumerate(xs):
        lit = k != 0
        lamp(Builder(m, (x, 0, 9.0), 0), lit, k * 0.7)
        if lit:
            lights.append(lamp_light((x, 0, 9.0), 0))
    tobias(m, parts, (-0.5, 0, 13.3), 160, with_pole=True, bench=True)
    W, H = 1600, 760
    cam = r3.Camera((-1, 2.4, -4.5), (-11, 1.6, 11), 56, W, H)
    lights += [{"p": [-0.5, 2.4, 11.5], "c": [1.0, 0.8, 0.55], "range": 6, "intensity": 0.6}]
    pic = r3.render(L, cam, m, lights=lights, fog_density=0.012, **sb)
    pic = r3.story_grade(pic)
    img = Image.new("RGB", (W, H + 110), BG)
    img.paste(pic, (0, 0))
    d = ImageDraw.Draw(img)
    d.text((24, H + 18), "The Creekside Path, most of the way lit", font=font(26, "Black"), fill=INK)
    d.text((24, H + 56), "Twelve gas lamps on the bank, six each side of the bridge. Tobias waits by his bench at the bridge; the far lamp is still dark.",
           font=font(15, "Medium"), fill=MUTED)
    d.text((W - 24, H + 92), "Drawn by Docs/tools/render3d.py, not an engine capture", font=font(12, "Medium"), fill=FAINT, anchor="rm")
    save_png(img, "creekside.png")


if __name__ == "__main__":
    which = sys.argv[1:] or ["sheet", "scene"]
    if "sheet" in which:
        make_sheet()
    if "scene" in which:
        make_scene()
