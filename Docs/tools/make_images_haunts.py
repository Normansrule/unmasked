#!/usr/bin/env python3
"""
Pictures for round 42, a real small town with haunts to bust:

  haunts.png        the twelve one-of-a-kind buildings at night, each with its ghost out front and
                    its three violet signs, with the ghost's name and the haunt in a line
  haunts-inside.png six of the walk-in ground floors (round 43), where each ghost's last chase ends
  soft-cast.png     the cast with soft edges: boots, belts, collars and cuffs before (hard boxes and
                    cylinders) and after (Spooky/SoftBox.cs)

Drawn by Docs/tools/render3d.py from HollowCreek.json and Costumes.json, not captured in Unity.

    python3 Docs/tools/make_images_haunts.py            # both
    python3 Docs/tools/make_images_haunts.py haunts     # just one
"""
import json
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def ghost(m, p, c, ry):
    """The sheet ghost HauntBust.cs builds: head, body, a wavy hem, eyes and a little mouth."""
    R = r3.euler(0, ry, 0)
    par = (R, p, 1.0)
    ink = (0.08, 0.06, 0.1)
    m.add_shape("sphere", (0, 0.55, 0), (0.7, 0.7, 0.7), color=c, emissive=0.8, parent=par)
    m.add_shape("capsule", (0, 0.05, 0), (0.78, 0.55, 0.78), color=c, emissive=0.8, parent=par)
    for i in range(6):
        a = i * math.pi / 3
        m.add_shape("sphere", (math.cos(a) * 0.3, -0.42, math.sin(a) * 0.3), (0.24, 0.24, 0.24), color=c, emissive=0.8, parent=par)
    for s in (-1, 1):
        m.add_shape("sphere", (s * 0.12, 0.62, 0.31), (0.1, 0.14, 0.06), color=ink, parent=par)
        m.add_shape("capsule", (s * 0.38, 0.15, 0.05), (0.16, 0.22, 0.16), (0, 0, s * -40), color=c, emissive=0.8, parent=par)
    m.add_shape("sphere", (0, 0.45, 0.33), (0.12, 0.09, 0.05), color=ink, parent=par)


def wisp(m, p):
    v = (0.72, 0.6, 1.0)
    m.add_shape("sphere", (p[0], 0.9, p[2]), (0.22, 0.22, 0.22), color=v, emissive=1.2)
    m.add_shape("sphere", (p[0], 0.75, p[2]), (0.12, 0.2, 0.12), color=v, emissive=1.2)
    m.add_shape("cyl", (p[0], 0.01, p[2]), (0.9, 0.005, 0.9), color=(0.45, 0.35, 0.75), emissive=0.8)


def make_haunts():
    merged, t, _ = r3.load_town()
    mesh = r3.layout_mesh(merged)
    r3.horizon_mesh(t, mesh)
    haunts = t["haunts"]
    cw, ch, pad, head, cols = 470, 300, 16, 96, 3
    rows = math.ceil(len(haunts) / cols)
    out = Image.new("RGB", (pad + cols * (cw + pad), head + rows * (ch + 58) + 30), BG)
    d = ImageDraw.Draw(out)
    d.text((pad, 24), "A real small town, and a haunt in every one", font=font(32, "Black"), fill=INK)
    d.text((pad, 66), "Twelve one-of-a-kind buildings. Read the three violet signs, then catch the ghost. Drawn from the game's layout by render3d.py, not an engine capture.",
           font=font(14), fill=MUTED)
    for i, h in enumerate(haunts):
        door = h["door"]
        ry = h["ry"]
        out_dir = (-math.sin(math.radians(ry)) * -1, math.cos(math.radians(ry)) * -1)  # toward the street
        fx, fz = {0: (0, 1), 180: (0, -1), 90: (1, 0), -90: (-1, 0)}[int(ry)]
        cx, cz = (h["min"][0] + h["max"][0]) / 2, (h["min"][1] + h["max"][1]) / 2
        side = (-fz, fx)
        cam_p = (door[0] + fx * 19 + side[0] * 7, 6.5, door[2] + fz * 19 + side[1] * 7)
        target = (cx, 4.2, cz)
        extra = r3.Mesh()
        hide = h["hide"]
        ghost(extra, (hide[0], hide[1], hide[2]), tuple(h["c"]), ry + 180)
        for s in h["signs"]:
            wisp(extra, s["p"])
        cam = r3.Camera(cam_p, target, 50, cw, ch)
        img = r3.render(merged, cam, mesh, ss=2, extra_mesh=extra, horizon=t, horizon_t=i * 0.4, fog_density=0.006, ambient=(0.16, 0.13, 0.24), light_boost=1.5)
        x, y = pad + (i % cols) * (cw + pad), head + (i // cols) * (ch + 58)
        out.paste(img, (x, y))
        d.text((x, y + ch + 7), f"{h['n']}: {h['ghost']}", font=font(16, "Bold"), fill=INK)
        d.text((x, y + ch + 29), h["blurb"][:78] + ("…" if len(h["blurb"]) > 78 else ""), font=font(12), fill=MUTED)
        print("  ", h["n"])
    save_png(out, "haunts.png")


def make_inside():
    merged, t, _ = r3.load_town()
    mesh = r3.layout_mesh(merged)
    picks = ["cinema", "bakery", "musichall", "apothecary", "laundry", "toyshop"]
    haunts = [h for k in picks for h in t["haunts"] if h["id"] == k]
    cw, ch, pad, head, cols = 470, 300, 16, 96, 3
    rows = math.ceil(len(haunts) / cols)
    out = Image.new("RGB", (pad + cols * (cw + pad), head + rows * (ch + 40) + 20), BG)
    d = ImageDraw.Draw(out)
    d.text((pad, 24), "Step inside", font=font(32, "Black"), fill=INK)
    d.text((pad, 66), "Every haunt's ground floor is a room you can walk into, and the ghost's last chase ends here. Drawn from the layout, not an engine capture.",
           font=font(14), fill=MUTED)
    for i, h in enumerate(haunts):
        door = h["door"]
        cx, cz = (h["min"][0] + h["max"][0]) / 2, (h["min"][1] + h["max"][1]) / 2
        dx, dz = cx - door[0], cz - door[2]
        k = math.hypot(dx, dz)
        dx, dz = dx / k, dz / k
        extra = r3.Mesh()
        hide = h["hide"][6:9]
        ghost(extra, (hide[0], hide[1] - 0.3, hide[2]), tuple(h["c"]), h["ry"] + 180)
        cam = r3.Camera((door[0] + dx * 0.9, 2.3, door[2] + dz * 0.9), (cx + dx * 4.5, 1.2, cz + dz * 4.5), 72, cw, ch)
        img = r3.render(merged, cam, mesh, ss=2, extra_mesh=extra, moon=False, fog_density=0.004, ambient=(0.2, 0.17, 0.22), light_boost=1.6)
        x, y = pad + (i % cols) * (cw + pad), head + (i // cols) * (ch + 40)
        out.paste(img, (x, y))
        d.text((x, y + ch + 8), f"Inside {h['n']}", font=font(16, "Bold"), fill=INK)
        print("  ", h["n"])
    save_png(out, "haunts-inside.png")


def make_soft():
    with open(os.path.join(ROOT, "Assets", "Unmasked", "Resources", "Costumes.json")) as f:
        C = json.load(f)
    who = [o for o in C["solvers"]] + [o for o in C["suspects"]][:2]
    cw, ch = 300, 420
    out = Image.new("RGB", (16 + len(who) * (cw + 16), 96 + 2 * (ch + 40)), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 22), "Softer people", font=font(32, "Black"), fill=INK)
    d.text((16, 64), "Top: boots, belts, collars and cuffs as hard boxes and cylinders. Bottom: the same parts with soft rounded edges. Not an engine capture.",
           font=font(14), fill=MUTED)
    stage = {"boxes": [{"n": "Floor", "t": "box", "p": [0, -0.05, 0], "s": [8, 0.1, 8], "r": [0, 0, 0], "c": [0.2, 0.17, 0.15], "m": "solid", "l": 0, "g": "ground"}],
             "lights": [], "decor": [],
             "glows": [{"n": "Key", "p": [1.5, 3.2, 2.5], "c": [1, 0.85, 0.65], "range": 12, "intensity": 1.6, "l": 0}]}
    for k in r3._LIST_KEYS:
        stage.setdefault(k, [])
    stage["name"] = "stage"
    for row, soft in enumerate((False, True)):
        for i, o in enumerate(who):
            parts = o["parts"] if soft else [dict(q, t={"rbox": "box", "rcyl": "cyl"}.get(q["t"], q["t"])) for q in o["parts"]]
            m = r3.Mesh()
            m.add_parts(parts, (0, 0, 0), ry=20)
            sm = r3.layout_mesh(stage)
            cam = r3.Camera((0.9, 1.4, 4.4), (0, 1.08, 0), 32, cw, ch)
            img = r3.render(stage, cam, sm, ss=2, moon=False, extra_mesh=m, fog_density=0.0)
            x, y = 16 + i * (cw + 16), 96 + row * (ch + 40)
            out.paste(img, (x, y))
            d.text((x, y + ch + 8), f"{o['id']}, {'soft' if soft else 'before'}", font=font(14, "Bold"), fill=INK if soft else MUTED)
    save_png(out, "soft-cast.png")


if __name__ == "__main__":
    args = set(sys.argv[1:])
    if not args or "haunts" in args:
        make_haunts()
    if not args or "inside" in args:
        make_inside()
    if not args or "soft" in args:
        make_soft()
