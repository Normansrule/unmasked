#!/usr/bin/env python3
"""
Pictures for round 36:

  carving.png  the carving bench outside HQ: every eye, nose and mouth you can pick, and a porch
               of six jack-o'-lanterns (Town/CarvingBench.cs, same shapes and numbers)
  kids.png     the trick-or-treaters with storybook heads, all nine costumes including the new
               mummy and bat (Town/TownLife.cs BuildKid, same shapes and numbers)

Drawn by Docs/tools/render3d.py, not captured in Unity.

    python3 Docs/tools/make_images_porch.py
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402

BG = (22, 18, 14)
INK = (243, 234, 219)
MUTED = (205, 191, 171)
FAINT = (162, 147, 127)
SKIN, GLOW, STEM = (0.91, 0.45, 0.11), (1.0, 0.74, 0.32), (0.32, 0.42, 0.18)
EYES = ["Triangles", "Round", "Angry", "Sleepy"]
NOSES = ["Triangle", "Button", "None"]
MOUTHS = ["Grin", "Toothy", "Oh!", "Wobbly"]
SHAPE = {"cube": "box", "sphere": "sphere", "cyl": "cyl", "capsule": "capsule"}


class Builder:
    """Adds Unity-style primitives under a simple (position, yaw, scale) parent."""

    def __init__(self, mesh, at=(0, 0, 0), ry=0.0, scale=1.0):
        self.m, self.at, self.ry, self.k = mesh, np.array(at, float), ry, scale

    def part(self, kind, p, s, c, rot=(0, 0, 0), glow=False):
        a = np.radians(self.ry)
        x, y, z = (v * self.k for v in p)
        wx, wz = x * np.cos(a) + z * np.sin(a), -x * np.sin(a) + z * np.cos(a)
        pos = tuple(self.at + np.array([wx, y, wz]))
        self.m.add_shape(SHAPE[kind], pos, tuple(v * self.k for v in s), (rot[0], rot[1] + self.ry, rot[2]), c,
                        emissive=(glow if isinstance(glow, float) else 1.4) if glow else 0.0)


def pumpkin(b, e, n, m):
    """CarvingBench.BuildPumpkin."""
    import math
    b.part("sphere", (0, 0.22, 0), (0.5, 0.42, 0.48), SKIN)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        b.part("sphere", (math.sin(a) * 0.07, 0.22, math.cos(a) * 0.07), (0.38, 0.4, 0.38), SKIN)
    b.part("cyl", (0.01, 0.46, 0), (0.05, 0.05, 0.05), STEM, (0, 0, -14))
    z = 0.245
    for s in (-1, 1):
        at = (s * 0.09, 0.29, z)
        if e == 0:
            b.part("cube", at, (0.07, 0.07, 0.02), GLOW, (0, 0, 45), True)
        elif e == 1:
            b.part("sphere", at, (0.08, 0.08, 0.02), GLOW, glow=True)
        elif e == 2:
            b.part("cube", (at[0], at[1] - 0.01, z), (0.1, 0.035, 0.02), GLOW, (0, 0, s * 22), True)
        else:
            b.part("capsule", (at[0], at[1] - 0.015, z), (0.025, 0.05, 0.02), GLOW, (0, 0, 90), True)
    if n == 0:
        b.part("cube", (0, 0.21, z + 0.005), (0.04, 0.04, 0.02), GLOW, (0, 0, 45), True)
    elif n == 1:
        b.part("sphere", (0, 0.21, z + 0.005), (0.04, 0.04, 0.02), GLOW, glow=True)
    my = 0.13
    if m == 0:
        for i in range(-3, 4):
            b.part("cube", (i * 0.032, my + i * i * 0.004, z - abs(i) * 0.008), (0.03, 0.035, 0.02), GLOW, (0, -i * 8, i * 6), True)
    elif m == 1:
        b.part("cube", (0, my, z - 0.005), (0.22, 0.06, 0.02), GLOW, glow=True)
        b.part("cube", (-0.04, my + 0.018, z + 0.002), (0.03, 0.03, 0.025), SKIN)
        b.part("cube", (0.05, my - 0.018, z + 0.002), (0.03, 0.03, 0.025), SKIN)
    elif m == 2:
        b.part("sphere", (0, my, z), (0.07, 0.09, 0.02), GLOW, glow=True)
    else:
        for i in range(-2, 3):
            b.part("cube", (i * 0.04, my + (0.008 if i % 2 == 0 else -0.008), z - abs(i) * 0.01), (0.045, 0.02, 0.02), GLOW, (0, -i * 10, 30 if i % 2 == 0 else -30), True)


def make_carving():
    L = r3.load_layout()
    sb = r3.STORYBOOK
    gap, top = 24, 92
    # Top: one row per choice, a pumpkin for each option (the others left at their first choice).
    rows = [("Eyes", EYES, lambda k: (k, 0, 0)), ("Nose", NOSES, lambda k: (0, k, 0)), ("Mouth", MOUTHS, lambda k: (0, 0, k))]
    CW, CH = 220, 200
    tiles = []
    for label, opts, pick in rows:
        for k, name in enumerate(opts):
            m = r3.Mesh()
            m.add_shape("box", (0, -0.05, 0), (4, 0.1, 4), (0, 0, 0), (0.22, 0.15, 0.1))
            pumpkin(Builder(m), *pick(k))
            cam = r3.Camera((0, 0.32, 1.05), (0, 0.24, 0), 34, CW, CH)
            pic = r3.render(L, cam, m, lights=[{"p": [0.6, 0.9, 1.2], "c": [1.0, 0.85, 0.7], "range": 4, "intensity": 1.1},
                                    {"p": [-0.8, 0.6, 0.8], "c": [0.6, 0.85, 0.95], "range": 4, "intensity": 0.5}],
                            fog_density=0.0, moon=False, **sb)
            tiles.append((label, name, r3.story_grade(pic)))
    # Bottom: six on the porch against the HQ wall, as CarvingBench.RebuildPorch lays them out.
    PW, PH = 4 * CW + 3 * gap, 330
    m = r3.Mesh()
    m.add_shape("box", (0, -0.05, 0), (12, 0.1, 8), (0, 0, 0), (0.2, 0.17, 0.15))
    m.add_shape("box", (0, 1.6, -0.4), (8, 3.2, 0.3), (0, 0, 0), (0.36, 0.3, 0.28))
    faces = [(0, 0, 0), (2, 1, 1), (1, 2, 2), (3, 0, 3), (2, 0, 0), (0, 1, 1)]
    for k, f in enumerate(faces):
        x = -1.4 + k * 0.55
        z = 0.35 - (k % 2) * 0.45 + 0.4
        pumpkin(Builder(m, (x, 0, z - 0.4), (k % 3 - 1) * 12, 0.9 + (k % 3) * 0.08), *f)
    cam = r3.Camera((0, 0.75, 2.5), (0, 0.28, 0.2), 40, PW, PH)
    porch = r3.render(L, cam, m, lights=[{"p": [0, 0.6, 1.2], "c": [1.0, 0.7, 0.38], "range": 5, "intensity": 0.9}],
                      fog_density=0.0, moon=False, **sb)
    porch = r3.story_grade(porch)
    W = 4 * CW + 5 * gap + 260
    H = top + 3 * (CH + 40) + PH + 110
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((gap, 22), "The carving bench", font=font(34, "Black"), fill=INK)
    d.text((gap, 62), "Outside HQ: pick the eyes, the nose and the mouth, and your jack-o'-lantern joins the porch. One a night; the porch keeps six.",
           font=font(15, "Medium"), fill=MUTED)
    y = top
    for r_i, (label, opts, _) in enumerate(rows):
        d.text((gap, y + CH / 2 - 10), label, font=font(20, "Bold"), fill=INK)
        for k, (lbl, name, pic) in enumerate([t for t in tiles if t[0] == label]):
            x = gap + 120 + k * (CW + gap)
            img.paste(pic, (int(x), y))
            d.text((x, y + CH + 6), name, font=font(14, "Medium"), fill=MUTED)
        y += CH + 40
    img.paste(porch, (gap + 120, y))
    d.text((gap, y + PH / 2 - 10), "Porch", font=font(20, "Bold"), fill=INK)
    d.text((gap + 120, y + PH + 8), "Six on the HQ porch, lit, faces out to the parking lot", font=font(14, "Medium"), fill=MUTED)
    d.text((W / 2, H - 20), "Drawn by Docs/tools/render3d.py with CarvingBench.cs's own shapes, not an engine capture",
           font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "carving.png")


def kid(m, at, costume, skin, h):
    """TownLife.BuildKid, storybook heads (round 36)."""
    b = Builder(m, at, 0, h)
    t = Builder(m, (at[0], at[1] + 0.08 * h, at[2]), 0, h)
    kind = costume["kind"]
    main, accent, dark = tuple(costume["body"]), tuple(costume["accent"]), (0.12, 0.1, 0.12)
    b.part("capsule", (-0.1, 0.18, 0), (0.13, 0.18, 0.13), dark)
    b.part("capsule", (0.1, 0.18, 0), (0.13, 0.18, 0.13), dark)
    for sx in (-0.1, 0.1):  # little shoes (round 39)
        b.part("sphere", (sx, 0.035, 0.06), (0.14, 0.08, 0.2), (0.3, 0.18, 0.12))
    b.part("cyl", (0.3, 0.5, 0.12), (0.18, 0.09, 0.18), (0.95, 0.5, 0.12), glow=0.45)
    b.part("capsule", (0.24, 0.68, 0.08), (0.09, 0.16, 0.09), main, (0, 0, 20))
    if kind == "sheet":
        b.part("capsule", (0, 0.66, 0), (0.56, 0.5, 0.5), main)
        b.part("sphere", (-0.08, 0.95, 0.24), (0.07, 0.09, 0.03), accent)
        b.part("sphere", (0.08, 0.95, 0.24), (0.07, 0.09, 0.03), accent)
        return
    if kind == "pumpkin":
        b.part("sphere", (0, 0.56, 0), (0.62, 0.55, 0.6), main)
    else:
        b.part("capsule", (0, 0.56, 0), (0.42, 0.34, 0.36), main)
    head = accent if kind in ("skeleton", "mummy") else skin
    b.part("sphere", (0, 1.08, 0), (0.42, 0.4, 0.4), head)
    cat = kind == "cat"
    iris = [(0.42, 0.28, 0.16), (0.3, 0.5, 0.75), (0.35, 0.55, 0.3)][len(kind) % 3]
    if kind != "skeleton":
        b.part("sphere", (0, 1.05, 0.2), (0.045, 0.035, 0.035), tuple(v * 0.96 for v in head))
    for s in (-1, 1):
        ex, ey, ez = s * 0.08, 1.11, 0.17
        if kind == "skeleton":
            b.part("sphere", (ex, ey, ez), (0.1, 0.11, 0.05), dark)
            continue
        b.part("sphere", (ex, ey, ez), (0.085, 0.09, 0.04), accent if cat else (0.95, 0.93, 0.88), glow=cat)
        if not cat:
            b.part("sphere", (ex, ey - 0.004, ez + 0.012), (0.062, 0.066, 0.02), iris)
        b.part("sphere", (ex, ey - 0.005, ez + 0.018), (0.02 if cat else 0.036, 0.04, 0.02), dark)
        b.part("sphere", (ex + 0.012, ey + 0.014, ez + 0.026), (0.016,) * 3, (1, 1, 1), glow=True)
        b.part("sphere", (ex - 0.01, ey - 0.012, ez + 0.026), (0.008,) * 3, (1, 1, 1), glow=True)
        b.part("capsule", (ex + s * 0.008, ey + 0.042, ez + 0.012), (0.012, 0.045, 0.012), dark, (0, 0, 90 - s * 10))
        if kind != "mummy":
            blush = tuple(a + (b_ - a) * 0.45 for a, b_ in zip(skin, (0.95, 0.45, 0.45)))
            b.part("sphere", (s * 0.13, 1.04, 0.15), (0.07, 0.04, 0.03), blush)
    b.part("capsule", (0, 1.0, 0.18), (0.018, 0.045, 0.018), dark, (0, 0, 90))
    if kind == "witch":
        t.part("cyl", (0, 1.17, 0), (0.58, 0.01, 0.58), main)
        t.part("cyl", (0, 1.26, 0), (0.3, 0.08, 0.3), accent)
        t.part("cyl", (0, 1.4, 0), (0.2, 0.06, 0.2), main)
        t.part("cyl", (0.03, 1.53, 0), (0.1, 0.06, 0.1), main, (0, 0, -16))
    elif kind == "pumpkin":
        t.part("cyl", (0, 1.22, 0), (0.06, 0.05, 0.06), accent)
    elif kind == "mummy":
        for i in range(5):
            b.part("cyl", (0, 0.38 + i * 0.11, 0), (0.44 - abs(i - 2) * 0.03, 0.02, 0.38), accent, (0, i * 37, 8 if i % 2 == 0 else -8))
        for i in range(3):
            t.part("cyl", (0, 0.95 + i * 0.09, 0), (0.44, 0.018, 0.42), main, (0, 0, 10 if i % 2 == 0 else -10))
        b.part("cube", (-0.2, 0.42, 0.1), (0.05, 0.24, 0.01), accent, (0, 0, -12))
    elif kind == "bat":
        for s in (-1, 1):
            b.part("cube", (s * 0.38, 0.66, -0.06), (0.42, 0.26, 0.02), accent, (0, s * 20, s * -18))
            b.part("cube", (s * 0.52, 0.56, -0.1), (0.2, 0.16, 0.02), accent, (0, s * 20, s * 30))
            t.part("cube", (s * 0.12, 1.2, 0), (0.08, 0.14, 0.04), main, (0, 0, s * -18))
    elif kind == "skeleton":
        for i in range(3):
            b.part("cube", (0, 0.72 - i * 0.1, 0.17), (0.3 - i * 0.04, 0.035, 0.03), accent)
    elif kind == "cat":
        t.part("cube", (-0.12, 1.17, 0), (0.1,) * 3, main, (0, 0, 45))
        t.part("cube", (0.12, 1.17, 0), (0.1,) * 3, main, (0, 0, 45))
        b.part("capsule", (0, 0.4, -0.25), (0.06, 0.22, 0.06), main, (-50, 0, 0))
    elif kind == "vampire":
        b.part("cube", (0, 0.6, -0.17), (0.52, 0.74, 0.04), accent)
        b.part("cube", (0, 0.88, -0.1), (0.5, 0.16, 0.04), main, (-20, 0, 0))
    elif kind == "pirate":
        t.part("sphere", (0, 1.1, 0), (0.44, 0.18, 0.43), main)
        b.part("cube", (0, 0.56, 0.17), (0.34, 0.06, 0.04), accent)
        b.part("sphere", (0.08, 1.11, 0.2), (0.1, 0.1, 0.03), dark)


def make_kids():
    town = json.load(open(r3.TOWN_PATH))
    costumes = town["life"]["costumes"]
    skins = [(0.95, 0.79, 0.65), (0.77, 0.55, 0.39), (0.55, 0.35, 0.23), (0.91, 0.71, 0.56)]
    L = r3.load_layout()
    m = r3.Mesh()
    m.add_shape("box", (0, -0.05, 0), (20, 0.1, 8), (0, 0, 0), (0.12, 0.16, 0.16))
    n = len(costumes)
    xs = [(-(n - 1) / 2 + i) * 0.85 for i in range(n)]
    for i, (x, c) in enumerate(zip(xs, costumes)):
        kid(m, (x, 0, 0), c, skins[i % 4], 0.95 + (i % 3) * 0.05)
    W, H = 1300, 420
    cam = r3.Camera((0, 0.95, 5.3), (0, 0.65, 0), 40, W, H)
    lights = [{"p": [-2, 2.2, 2.0], "c": [1.0, 0.75, 0.45], "range": 7, "intensity": 1.2},
              {"p": [2.5, 2.0, 2.0], "c": [0.6, 0.85, 0.95], "range": 7, "intensity": 0.9}]
    pic = r3.story_grade(r3.render(L, cam, m, lights=lights, fog_density=0.0, **r3.STORYBOOK))
    pd = ImageDraw.Draw(pic)
    for x, c in zip(xs, costumes):
        p = cam.project((x, -0.02, 0.45))[0]
        pd.text((p[0], min(H - 14, p[1] + 12)), c["kind"].capitalize(), font=font(14, "Bold"), fill=INK, anchor="mm")
    img = Image.new("RGB", (W + 48, H + 150), BG)
    img.paste(pic, (24, 92))
    d = ImageDraw.Draw(img)
    d.text((24, 22), "The trick-or-treaters", font=font(34, "Black"), fill=INK)
    d.text((24, 62), "Storybook heads with real eyes, rosy cheeks and a smile, and two new costumes: the mummy and the bat.",
           font=font(15, "Medium"), fill=MUTED)
    d.text(((W + 48) / 2, H + 125), "Drawn by Docs/tools/render3d.py with TownLife.cs's own shapes, not an engine capture",
           font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "kids.png")


if __name__ == "__main__":
    make_carving()
    make_kids()
