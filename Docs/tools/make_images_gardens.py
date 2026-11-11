#!/usr/bin/env python3
"""
Pictures for round 47, people and front gardens:

  cast-smooth.png    four of the cast before (round 46) and after: a barrel chest melted into the
                     body instead of a puffy band on top, beards and mutton chops as soft hair, and
                     the skin relaxed so the grid's ripples are gone
  front-gardens.png  four front yards before and after frontyard.py: window boxes, foundation shrubs,
                     flowers down the path, clipped hedges, a rocker on the porch, leaves or a barrow

Drawn by Docs/tools/render3d.py from Costumes.json and the layout files, not captured in Unity.

    python3 Docs/tools/make_images_gardens.py [round46_smoothbody.py] [round46_HollowCreek.json]
"""
import importlib.util
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
import smoothbody  # noqa: E402
import frontyard  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_characters import outfits, LIGHTS  # noqa: E402
from make_images_storybook import stage, BG, INK, MUTED, NEW  # noqa: E402

CAST = [("Brawn", "The Brawn"), ("Groundskeeper", "The Groundskeeper"), ("Folk.Mayor", "The Mayor"), ("Heiress", "The Heiress")]
YARDS = [5, 13, 11, 19]   # Home numbers: a barrow, a leaf pile, a fenced yard, a porch with a lantern


def bust(parts, W, H):
    L = stage()
    m = r3.Mesh()
    m.add_parts(parts, (0, 0, 0), 20)
    cam = r3.Camera((0.5, 1.65, 1.7), (0, 1.45, 0), 34, W, H)
    return r3.story_grade(r3.render(L, cam, r3.layout_mesh(L), lights=LIGHTS, extra_mesh=m, fog_density=0.0, moon=False, **r3.STORYBOOK))


def make_cast(old_module):
    O = outfits(NEW)
    cw, ch = 330, 380
    out = Image.new("RGB", (16 + len(CAST) * (cw + 16), 96 + 2 * (ch + 40)), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 22), "One smooth body", font=font(32, "Black"), fill=INK)
    d.text((16, 64), "Top: round 46. Bottom: the chest melts into the body, beards become soft hair, the skin's ripples are ironed out. Not an engine capture.",
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
            out.paste(bust(O[cid], cw, ch), (x, y))
            d.text((x, y + ch + 8), f"{name}, {'after' if row else 'before'}", font=font(14, "Bold"), fill=INK if row else MUTED)
            print("  ", name, "after" if row else "before")
    sys.modules["smoothbody"] = smoothbody
    save_png(out, "cast-smooth.png")


def yard_shots(town_path, W, H):
    keep = r3.TOWN_PATH
    r3.TOWN_PATH = town_path
    try:
        merged, t, _ = r3.load_town()
    finally:
        r3.TOWN_PATH = keep
    mesh = r3.layout_mesh(merged)
    r3.horizon_mesh(t, mesh)
    by = {b["n"]: b for b in merged["boxes"]}
    shots = []
    for k in YARDS:
        h = frontyard._Home(k, by[f"Home{k}Body"], by[f"Home{k}Door"])
        dx, _, dz = by[f"Home{k}Door"]["p"]
        ox, oz = h.out
        side = (oz, -ox)   # step a little to one side of the path, so the porch isn't hidden behind the gate
        eye = (dx + ox * 9.5 + side[0] * 3.2, 1.9, dz + oz * 9.5 + side[1] * 3.2)
        target = (dx + ox * 3.0, 0.9, dz + oz * 3.0)
        shots.append(r3.render(merged, r3.Camera(eye, target, 55, W, H), mesh, ss=1, horizon=t, fog_density=0.006,
                               ambient=(0.2, 0.17, 0.28), light_boost=1.6))
        print("  ", f"Home{k}", os.path.basename(town_path))
    return shots


def make_gardens(old_town):
    W, H = 560, 330
    after = yard_shots(r3.TOWN_PATH, W, H)
    before = yard_shots(old_town, W, H) if old_town else None
    cols = 2 if before else 1
    out = Image.new("RGB", (16 + cols * (W + 16), 96 + len(YARDS) * (H + 40)), BG)
    d = ImageDraw.Draw(out)
    d.text((16, 22), "Front gardens", font=font(32, "Black"), fill=INK)
    d.text((16, 64), "Window boxes, shrubs, flowers down the path, clipped hedges, porch rockers, leaves and barrows. Not an engine capture.",
           font=font(14), fill=MUTED)
    with open(r3.TOWN_PATH) as f:
        T = json.load(f)
    doors = {b["n"]: b["p"] for b in T["boxes"] if b["n"].endswith("Door")}
    for row, k in enumerate(YARDS):
        y = 96 + row * (H + 40)
        dp = doors[f"Home{k}Door"]
        home = min(T["homes"], key=lambda h: (h["door"][0] - dp[0]) ** 2 + (h["door"][2] - dp[2]) ** 2)
        addr = home["address"]
        for c in range(cols):
            img = (before[row] if c == 0 else after[row]) if before else after[row]
            x = 16 + c * (W + 16)
            out.paste(img, (x, y))
            label = f"{addr}, {'before' if before and c == 0 else 'after'}"
            d.text((x, y + H + 8), label, font=font(14, "Bold"), fill=MUTED if before and c == 0 else INK)
    save_png(out, "front-gardens.png")


if __name__ == "__main__":
    args = sys.argv[1:]
    make_cast(args[0] if args else None)
    make_gardens(args[1] if len(args) > 1 else None)
