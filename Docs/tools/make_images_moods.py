#!/usr/bin/env python3
"""
Pictures for round 35:

  moods.png  one suspect's face in the five moods FaceLife.cs can show (calm, happy, worried,
             surprised, cross), made with the same numbers the game uses
  wisp.png   a will-o'-the-wisp (Town/Wisp.cs) rising off the creek and leading the way

Drawn by Docs/tools/render3d.py from Costumes.json and HollowCreek.json, not captured in Unity.

    python3 Docs/tools/make_images_moods.py
"""
import math
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402

BG = (22, 18, 14)
INK = (243, 234, 219)
MUTED = (205, 191, 171)
FAINT = (162, 147, 127)

# FaceLife.cs, LateUpdate: tilt, browUp, lidUp, mouthOpen, mouthWide, cheekUp
MOODS = [
    ("Calm", "Most of the time", (0, 0, 0, 0, 0, 0)),
    ("Happy", "A neighbour says thank you", (0, 0.004, 0, 0, 0.25, 0.008)),
    ("Worried", "Every suspect, when questioned", (14, 0.004, 0, 0, -0.15, 0)),
    ("Surprised", "Everyone, as the mask comes off", (0, 0.016, 0.008, 1.4, -0.25, 0)),
    ("Cross", "Caught", (-16, -0.006, -0.005, 0, -0.1, 0)),
]


def feel(parts, mood):
    tilt, brow_up, lid_up, mouth_open, mouth_wide, cheek_up = mood
    out = []
    for q in parts:
        n = q["n"]
        side = -1 if n.endswith("L") else 1
        q = dict(q, p=list(q["p"]), s=list(q["s"]), r=list(q.get("r", (0, 0, 0))))
        if n in ("BrowL", "BrowR"):
            q["p"][1] += brow_up
            q["r"][2] += -side * tilt
        elif n in ("LidL", "LidR"):
            q["p"][1] += lid_up
        elif n == "Lips":
            q["s"][0] *= 1 + mouth_open
            q["s"][1] *= 1 + mouth_wide
        elif n in ("CheekL", "CheekR"):
            q["p"][1] += cheek_up
        out.append(q)
    return out


def make_moods(who="Heiress"):
    C = r3.costumes()
    parts = C["suspects"][who]["parts"]
    head = next(q for q in parts if q["n"] == "Head")["p"]
    L = r3.load_layout()
    PW, PH = 300, 340
    cam = r3.Camera((head[0], head[1] + 0.02, head[2] + 1.15), (head[0], head[1] - 0.02, head[2]), 30, PW, PH)
    lights = [{"p": [0.8, head[1] + 0.6, 1.4], "c": [1.0, 0.8, 0.55], "range": 5, "intensity": 0.6},
              {"p": [-0.9, head[1] + 0.2, 1.0], "c": [0.55, 0.8, 0.9], "range": 5, "intensity": 0.35}]
    gap, top = 20, 92
    W = len(MOODS) * PW + (len(MOODS) + 1) * gap
    H = top + PH + 100
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((gap, 22), "Faces that feel something", font=font(34, "Black"), fill=INK)
    d.text((gap, 62), "FaceLife moods: brows tilt and lift, lids open, the mouth opens or widens, the cheeks rise. The same for every suspect, so a face never gives the culprit away.",
           font=font(15, "Medium"), fill=MUTED)
    for i, (name, sub, mood) in enumerate(MOODS):
        m = r3.Mesh()
        m.add_parts(feel(parts, mood), (0, 0, 0), 0)
        pic = r3.render(L, cam, m, lights=lights, fog_density=0.0, moon=False, **r3.STORYBOOK)
        x = gap + i * (PW + gap)
        img.paste(r3.story_grade(pic), (x, top))
        d.text((x, top + PH + 8), name, font=font(18, "Bold"), fill=INK)
        d.text((x, top + PH + 34), sub, font=font(13, "Medium"), fill=MUTED)
    d.text((W / 2, H - 20), "Drawn by Docs/tools/render3d.py with FaceLife.cs's own numbers, not an engine capture",
           font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "moods.png")


def make_wisp():
    merged, town, _ = r3.load_town()
    mesh = r3.layout_mesh(merged)
    cz = town["creekZ"]
    W, H = 1200, 560
    # The wisp's path: risen off the creek, then out across the bank, with two Solvers following.
    path = [(-22 + 1.4 * k, 1.5 + 0.18 * math.sin(k * 1.3), cz - 2.5 - 1.1 * k) for k in range(9)]
    mid = path[4]
    # Side on to the path, from the town side of the creek.
    cam = r3.Camera((mid[0] - 0.62 * 8.5, 2.0, mid[2] - 0.79 * 8.5), (mid[0], 1.2, mid[2]), 52, W, H)
    extra = r3.Mesh()
    for k, p in enumerate(path):
        f = (k + 1) / len(path)
        extra.add_shape("sphere", p, (0.06 + 0.1 * f,) * 3, (0, 0, 0), (0.3, 0.85, 0.66), emissive=0.25 + 0.6 * f)
    head = path[-1]
    extra.add_shape("sphere", head, (0.3, 0.3, 0.3), (0, 0, 0), (0.5, 1.0, 0.8), emissive=1.0)
    sol = r3.costumes()["solvers"]
    # Following on behind it, facing the way it's going.
    extra.add_parts(sol["Sleuth"]["parts"], (path[2][0] - 0.6, 0, path[2][2] + 0.4), 128)
    extra.add_parts(sol["Snacker"]["parts"], (path[0][0] - 0.8, 0, path[0][2] + 1.0), 128)
    lights = [{"p": list(head), "c": [0.5, 1.0, 0.85], "range": 7, "intensity": 2.0}]
    sb = r3.STORYBOOK
    pic = r3.render(merged, cam, mesh, extra_mesh=extra, lights=lights, fog_density=0.006, **sb)
    pic = r3.story_grade(pic)
    img = Image.new("RGB", (W + 48, H + 160), BG)
    img.paste(pic, (24, 92))
    d = ImageDraw.Draw(img)
    d.text((24, 22), "Will-o'-the-wisps", font=font(34, "Black"), fill=INK)
    d.text((24, 62), "Find three lanterns yourself, then green lights start rising off the creek between cases. Keep up, and one leads you to a lantern you've missed.",
           font=font(15, "Medium"), fill=MUTED)
    d.text(((W + 48) / 2, H + 130), "Drawn by Docs/tools/render3d.py from HollowCreek.json and Wisp.cs, not an engine capture",
           font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "wisp.png")


if __name__ == "__main__":
    make_moods()
    make_wisp()
