#!/usr/bin/env python3
"""
Picture for round 39's character pass:

  characters-detail.png  close-ups of the cast after the detail pass (the four Solvers, Tobias Wick
                         and a trick-or-treater), and one face before and after

Drawn by Docs/tools/render3d.py from Costumes.json (and TownLife.BuildKid's shapes), not captured
in Unity. The "before" face reads an older Costumes.json if one is passed:

    python3 Docs/tools/make_images_characters.py [path/to/old/Costumes.json]
"""
import json
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


def outfits(path):
    with open(path) as f:
        d = json.load(f)
    out = {o["id"]: o["parts"] for o in d["solvers"]}
    out.update({o["id"]: o["parts"] for o in d["suspects"]})
    return out


def head_y(parts):
    return next((q["p"][1] for q in parts if q["n"] == "Head"), 1.8)


LIGHTS = [{"p": [0.9, 2.6, 1.6], "c": [1.0, 0.86, 0.68], "range": 6, "intensity": 0.95},
          {"p": [-1.2, 2.0, 1.3], "c": [0.6, 0.8, 0.95], "range": 6, "intensity": 0.55},
          {"p": [0.0, 2.4, -1.4], "c": [0.7, 0.85, 1.0], "range": 5, "intensity": 0.5}]


def portrait(L, parts, W, H, ry=18, dist=1.55):
    m = r3.Mesh()
    m.add_parts(parts, (0, 0, 0), ry)
    y = head_y(parts)
    cam = r3.Camera((0.0, y + 0.04, dist), (0.0, y - 0.06, 0), 34, W, H)
    pic = r3.render(L, cam, m, lights=LIGHTS, fog_density=0.0, moon=False, **r3.STORYBOOK)
    return r3.story_grade(pic)


def kid_portrait(L, W, H):
    from make_images_porch import kid
    m = r3.Mesh()
    costume = {"kind": "witch", "body": [0.32, 0.18, 0.42], "accent": [0.55, 0.85, 0.35]}
    kid(m, (0, 0, 0), costume, (0.96, 0.78, 0.64), 1.0)
    cam = r3.Camera((0.0, 1.12, 0.9), (0.0, 1.02, 0), 34, W, H)
    pic = r3.render(L, cam, m, lights=LIGHTS, fog_density=0.0, moon=False, **r3.STORYBOOK)
    return r3.story_grade(pic)


def main(old_path=None):
    L = r3.load_layout()
    new = outfits(r3.COSTUMES_PATH)
    gap, top = 24, 96
    PW, PH = 300, 360
    cast = [("Sleuth", "Sleuth"), ("Techie", "Techie"), ("Brawn", "Brawn"), ("Snacker", "Snacker"),
            ("Folk.Lamplighter", "Tobias Wick")]
    tiles = [(name, portrait(L, new[cid], PW, PH)) for cid, name in cast]
    tiles.append(("A trick-or-treater", kid_portrait(L, PW, PH)))
    cols = 3
    rows = -(-len(tiles) // cols)
    BW, BH = 420, 420
    before = []
    if old_path and os.path.exists(old_path):
        old = outfits(old_path)
        before = [("Before (round 38)", portrait(L, old["Folk.Mayor"], BW, BH, ry=15, dist=1.2)),
                  ("After", portrait(L, new["Folk.Mayor"], BW, BH, ry=15, dist=1.2))]
    W = gap + cols * (PW + gap) + (BW + gap if before else 0) + gap
    H = top + rows * (PH + 44) + 110
    H = max(H, top + 2 * (BH + 44) + 110) if before else H
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((gap, 22), "Closer up: the cast in detail", font=font(34, "Black"), fill=INK)
    d.text((gap, 64), "Two-tone irises with a second glint, lower lashes, a lid crease, a soft blush, smile corners, shiny noses and hair, "
                      "fingernails, laces and socks.", font=font(15, "Medium"), fill=MUTED)
    for i, (name, pic) in enumerate(tiles):
        x = gap + (i % cols) * (PW + gap)
        y = top + (i // cols) * (PH + 44)
        img.paste(pic, (x, y))
        d.text((x, y + PH + 8), name, font=font(16, "Bold"), fill=INK)
    if before:
        x = gap + cols * (PW + gap) + gap
        for j, (name, pic) in enumerate(before):
            y = top + j * (BH + 44)
            img.paste(pic, (x, y))
            d.text((x, y + BH + 8), f"Mayor Beaumont: {name}", font=font(16, "Bold"), fill=INK)
    d.text((W / 2, H - 20), "Drawn by Docs/tools/render3d.py, not an engine capture", font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "characters-detail.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
