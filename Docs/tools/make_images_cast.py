#!/usr/bin/env python3
"""
Pictures for round 34's storybook character pass (storybook-cast.png): the four Mystery Club roles
before and after, lit the storybook way, plus their silhouettes in plain black, because a good
character reads from its outline alone. "Before" comes from the round 33 Costumes.json if you pass
its path; otherwise only the new cast is drawn.

Drawn by Docs/tools/render3d.py from Costumes.json, not captured in Unity.

It also draws hook-board.png: the Hook Board outside the Historical Society (Town/HookBoard.cs)
empty, half full and full, with the creek mist settling as the hooks fill.

    python3 Docs/tools/make_images_cast.py [old Costumes.json]
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
ROLES = ["Sleuth", "Techie", "Brawn", "Snacker"]
BLURB = {"Sleuth": "capelet, long coat, ear flaps", "Techie": "headphones, two aerials, pouches",
         "Brawn": "work gloves and boots", "Snacker": "round, bobble hat, satchel"}


def solvers_from(path):
    with open(path) as f:
        return {s["id"]: s for s in json.load(f)["solvers"]}


def stage(solvers, W, H, black=False):
    """The four roles in a row. black: their silhouettes, found by comparing against an empty stage."""
    L = r3.load_layout()
    m = r3.Mesh()
    floor = (0.62, 0.58, 0.5) if black else (0.11, 0.08, 0.13)
    m.add_shape("box", (0, -0.1, 0), (40, 0.2, 24), (0, 0, 0), floor)
    xs = [-3.3, -1.1, 1.1, 3.3]
    for x, sid in zip(xs, ROLES):
        parts = solvers[sid]["parts"]
        if black:
            parts = [dict(q, c=[0.02, 0.02, 0.03], m="solid") for q in parts]
        m.add_parts(parts, (x, 0, 0), 0)
    cam = r3.Camera((0, 1.25, 6.6), (0, 1.05, 0), 44, W, H)
    if black:
        import numpy as np
        empty = r3.Mesh()
        empty.add_shape("box", (0, -0.1, 0), (40, 0.2, 24), (0, 0, 0), floor)
        a = np.asarray(r3.render(L, cam, m, moon=False, fog_density=0.0, lights=[])).astype(int)
        b = np.asarray(r3.render(L, cam, empty, moon=False, fog_density=0.0, lights=[])).astype(int)
        ink = np.abs(a - b).sum(axis=2) > 24
        out = np.where(ink[..., None], np.array([24, 20, 22]), np.array([236, 226, 206])).astype(np.uint8)
        return Image.fromarray(out), cam, xs
    lights = [{"p": [3.0, 2.8, 2.6], "c": [0.8, 0.9, 1.0], "range": 8, "intensity": 1.4},
              {"p": [-3.0, 2.8, 2.6], "c": [1.0, 0.72, 0.45], "range": 8, "intensity": 1.4}]
    img = r3.render(L, cam, m, lights=lights, fog_density=0.01, **r3.STORYBOOK)
    return r3.story_grade(img), cam, xs


def make_storybook_cast(old_path=None):
    PW, PH = 1000, 420
    new = solvers_from(r3.COSTUMES_PATH)
    panels = []
    if old_path:
        panels.append(("Before", "Round 33: realistic proportions, small heads, similar outlines", stage(solvers_from(old_path), PW, PH)))
    panels.append(("After", "Storybook proportions: heads x1.3, eyes x1.18, hands x1.14, and a shape for every role", stage(new, PW, PH)))
    panels.append(("Silhouettes", "In plain black, each role still reads: the test the pass was built for", stage(new, PW, PH, black=True)))
    gap, top = 24, 92
    cols = 1
    rows = -(-len(panels) // cols)
    W = cols * PW + (cols + 1) * gap
    H = top + rows * (PH + 70) + 40
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((gap, 22), "The storybook cast", font=font(34, "Black"), fill=INK)
    d.text((gap, 62), "Bigger heads and eyes so faces read across a street, and an outline of its own for every role.",
           font=font(15, "Medium"), fill=MUTED)
    for i, (title, sub, (pic, cam, xs)) in enumerate(panels):
        x = gap + (i % cols) * (PW + gap)
        y = top + (i // cols) * (PH + 70)
        pd = ImageDraw.Draw(pic)
        for px_, sid in zip(xs, ROLES):
            p = cam.project((px_, -0.05, 0.5))[0]
            dark = title == "Silhouettes"
            pd.text((p[0], min(PH - 22, p[1] + 10)), sid, font=font(14, "Bold"), fill=(40, 30, 30) if dark else INK, anchor="mm")
            if title != "Before":
                pd.text((p[0], min(PH - 8, p[1] + 27)), BLURB[sid], font=font(11, "Medium"), fill=(90, 80, 70) if dark else MUTED, anchor="mm")
        img.paste(pic, (x, y))
        d.text((x, y + PH + 8), f"{i + 1}  {title}", font=font(18, "Bold"), fill=INK)
        d.text((x, y + PH + 34), sub, font=font(14, "Medium"), fill=MUTED)
    d.text((W / 2, H - 20), "Drawn by Docs/tools/render3d.py from Costumes.json, not an engine capture",
           font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "storybook-cast.png")


FAMILIES = ["Hatcher", "Quill", "Pemberton", "Blackwood", "Wren", "Finch", "Crane", "Ashby",
            "Thorne", "Pell", "Mabry", "Dunmore", "Hale", "Kettering", "Larkin", "Morrow",
            "Oakes", "Prewitt", "Rook", "Sable", "Tolliver", "Vance", "Whitlock", "Yarrow"]  # HookBoard.cs


def board_mesh(filled):
    """Town/HookBoard.cs's board, built from the same numbers, with the first `filled` lanterns hung."""
    m = r3.Mesh()
    m.add_shape("box", (0, -0.1, 0), (40, 0.2, 30), (0, 0, 0), (0.1, 0.12, 0.1))
    m.add_shape("box", (0, 0.0, 6), (40, 0.04, 6), (0, 0, 0), (0.16, 0.15, 0.17))  # Founders Way
    wood, trim, brass, roof = (0.36, 0.22, 0.13), (0.22, 0.13, 0.08), (0.78, 0.62, 0.3), (0.18, 0.24, 0.26)
    tin, glass = (0.2, 0.19, 0.22), (1.0, 0.78, 0.42)
    for x in (-2.35, 2.35):
        m.add_shape("box", (x, 1.5, 0), (0.18, 3, 0.18), (0, 0, 0), trim)
    m.add_shape("box", (0, 1.55, 0), (4.5, 2.1, 0.12), (0, 0, 0), wood)
    m.add_shape("box", (0, 2.66, 0), (4.7, 0.12, 0.2), (0, 0, 0), trim)
    m.add_shape("box", (0, 0.46, 0), (4.7, 0.12, 0.2), (0, 0, 0), trim)
    m.add_shape("box", (0, 3.12, 0.24), (5, 0.08, 0.75), (-28, 0, 0), roof)
    m.add_shape("box", (0, 3.12, -0.24), (5, 0.08, 0.75), (28, 0, 0), roof)
    for i in range(24):
        row, col = divmod(i, 6)
        x, y, z = -1.85 + col * 0.74, 2.2 - row * 0.48, 0.07
        m.add_shape("cyl", (x, y, z), (0.03, 0.05, 0.03), (90, 0, 0), brass)
        if i < filled:
            m.add_shape("cyl", (x, y - 0.17, z + 0.1), (0.13, 0.1, 0.13), (0, 0, 0), glass, emissive=1.6)
            m.add_shape("cyl", (x, y - 0.06, z + 0.1), (0.16, 0.015, 0.16), (0, 0, 0), tin)
            m.add_shape("cyl", (x, y - 0.28, z + 0.1), (0.16, 0.015, 0.16), (0, 0, 0), tin)
    sol = solvers_from(r3.COSTUMES_PATH)
    m.add_parts(sol["Sleuth"]["parts"], (3.2, 0, 1.4), -150)
    return m


def make_hook_board():
    PW, PH = 520, 380
    L = r3.load_layout()
    cam = r3.Camera((1.2, 1.9, 7.2), (0.3, 1.5, 0), 46, PW, PH)
    sb = r3.STORYBOOK
    panels = []
    for filled, title, sub in ((0, "No lanterns home", "Empty hooks, and the creek mist up to your knees"),
                               (12, "Twelve hooks filled", "+5 candy a lantern; the mist sits lower all over town"),
                               (24, "The new Lantern Watch", "All twenty-four home: the board glows, the mist lies low")):
        k = filled / 24
        mist = sb["mist"][:3] + (sb["mist"][3] * (1 - 0.45 * k), sb["mist"][4] * (1 - 0.5 * k) * 3.0)
        glow = 0.15 if filled == 0 else 0.4 + 1.0 * k
        lights = [{"p": [0, 1.8, 2.0], "c": [1.0, 0.76, 0.44], "range": 7, "intensity": glow * 1.4}]
        pic = r3.render(L, cam, board_mesh(filled), lights=lights, fog_density=0.008, **{**sb, "mist": mist})
        panels.append((title, sub, r3.story_grade(pic)))
    gap, top = 24, 92
    W = 3 * PW + 4 * gap
    H = top + PH + 110
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((gap, 22), "The Hook Board", font=font(34, "Black"), fill=INK)
    d.text((gap, 62), "Outside the Historical Society: hang each lost lantern on its 1823 family's hook. Every one pushes the mist back down to the creek.",
           font=font(15, "Medium"), fill=MUTED)
    for i, (title, sub, pic) in enumerate(panels):
        x = gap + i * (PW + gap)
        img.paste(pic, (x, top))
        d.text((x, top + PH + 8), f"{i + 1}  {title}", font=font(18, "Bold"), fill=INK)
        d.text((x, top + PH + 34), sub, font=font(14, "Medium"), fill=MUTED)
    d.text((W / 2, H - 20), "Drawn by Docs/tools/render3d.py with HookBoard.cs's own numbers, not an engine capture",
           font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "hook-board.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    make_storybook_cast(args[0] if args else None)
    make_hook_board()
