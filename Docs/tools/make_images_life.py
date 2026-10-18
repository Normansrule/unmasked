#!/usr/bin/env python3
"""
README images for round 17: Hollow Creek out trick-or-treating (Town/TownLife.cs), the train
across the valley, and the faces coming alive (Animation/FaceLife.cs). The kids, cars and train are
placed with the same seeded numbers as TownLife.cs, from the "life" block in HollowCreek.json.

    python3 Docs/tools/make_images_life.py               # everything
    python3 Docs/tools/make_images_life.py kids street   # just some
"""
import math
import os
import sys

import numpy as np
from PIL import ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import save_gif, save_png  # noqa: E402
from make_images_3d import label, title_text  # noqa: E402
from make_images_world import town  # noqa: E402

SKIN = [(0.96, 0.80, 0.68), (0.85, 0.64, 0.48), (0.62, 0.42, 0.28), (0.42, 0.27, 0.18)]
DARK = (0.12, 0.1, 0.12)
BUCKET = (0.95, 0.5, 0.12)


def kid_parts(costume, skin):
    """The same primitives as TownLife.BuildKid, at height 1: (shape, pos, scale, rot, colour, glow)."""
    main, accent, kind = tuple(costume["body"]), tuple(costume["accent"]), costume["kind"]
    out = [("capsule", (-0.1, 0.18, 0), (0.13, 0.18, 0.13), (0, 0, 0), DARK, 0),
           ("capsule", (0.1, 0.18, 0), (0.13, 0.18, 0.13), (0, 0, 0), DARK, 0),
           ("cyl", (0.3, 0.5, 0.12), (0.18, 0.09, 0.18), (0, 0, 0), BUCKET, 0.9),
           ("capsule", (0.24, 0.68, 0.08), (0.09, 0.16, 0.09), (0, 0, 20), main, 0)]
    if kind == "sheet":
        return out + [("capsule", (0, 0.66, 0), (0.56, 0.5, 0.5), (0, 0, 0), main, 0),
                      ("sphere", (-0.08, 0.95, 0.24), (0.07, 0.09, 0.03), (0, 0, 0), accent, 0),
                      ("sphere", (0.08, 0.95, 0.24), (0.07, 0.09, 0.03), (0, 0, 0), accent, 0)]
    if kind == "pumpkin":
        out.append(("sphere", (0, 0.56, 0), (0.62, 0.55, 0.6), (0, 0, 0), main, 0))
    else:
        out.append(("capsule", (0, 0.56, 0), (0.42, 0.34, 0.36), (0, 0, 0), main, 0))
    out.append(("sphere", (0, 1.02, 0), (0.32,) * 3, (0, 0, 0), accent if kind == "skeleton" else skin, 0))
    eye, glow = (accent, 0.9) if kind == "cat" else (DARK, 0)
    out += [("sphere", (-0.06, 1.05, 0.14), (0.05,) * 3, (0, 0, 0), eye, glow),
            ("sphere", (0.06, 1.05, 0.14), (0.05,) * 3, (0, 0, 0), eye, glow)]
    if kind == "witch":
        out += [("cyl", (0, 1.17, 0), (0.5, 0.01, 0.5), (0, 0, 0), main, 0),
                ("cyl", (0, 1.26, 0), (0.26, 0.08, 0.26), (0, 0, 0), accent, 0),
                ("cyl", (0, 1.4, 0), (0.17, 0.06, 0.17), (0, 0, 0), main, 0),
                ("cyl", (0.02, 1.51, 0), (0.09, 0.05, 0.09), (0, 0, -12), main, 0)]
    elif kind == "pumpkin":
        out.append(("cyl", (0, 1.2, 0), (0.06, 0.05, 0.06), (0, 0, 0), accent, 0))
    elif kind == "skeleton":
        out += [("box", (0, 0.72 - i * 0.1, 0.17), (0.3 - i * 0.04, 0.035, 0.03), (0, 0, 0), accent, 0) for i in range(3)]
    elif kind == "cat":
        out += [("box", (-0.1, 1.17, 0), (0.09,) * 3, (0, 0, 45), main, 0), ("box", (0.1, 1.17, 0), (0.09,) * 3, (0, 0, 45), main, 0),
                ("capsule", (0, 0.4, -0.25), (0.06, 0.22, 0.06), (-50, 0, 0), main, 0)]
    elif kind == "vampire":
        out += [("box", (0, 0.6, -0.17), (0.52, 0.74, 0.04), (0, 0, 0), accent, 0),
                ("box", (0, 0.88, -0.1), (0.5, 0.16, 0.04), (-20, 0, 0), main, 0)]
    elif kind == "pirate":
        out += [("sphere", (0, 1.1, 0), (0.34, 0.16, 0.34), (0, 0, 0), main, 0),
                ("box", (0, 0.56, 0.17), (0.34, 0.06, 0.04), (0, 0, 0), accent, 0),
                ("sphere", (0.06, 1.05, 0.15), (0.065,) * 3, (0, 0, 0), DARK, 0)]
    return out


def add_kid(m, parts, pos, ry, h):
    R = r3.euler(0, ry, 0)
    for shape, p, s, r, c, e in parts:
        m.add_shape(shape, p, s, r, c, e, (R, np.array(pos, float), h))


def groups(t):
    """Every group of trick-or-treaters as TownLife.Build makes them: (walk, u, dir, side, kids)."""
    life = t["life"]
    rng = r3.Lcg(life["seed"])
    out = []
    for _ in range(life["groups"]):
        walk = life["walks"][int(rng.next() * len(life["walks"])) % len(life["walks"])]
        u = rng.next()
        d = -1.0 if rng.next() < 0.5 else 1.0
        side = -1.0 if rng.next() < 0.5 else 1.0
        rng.range(0.8, 1.3)  # speed
        kids = []
        for _ in range(2 + int(rng.next() * 3)):
            costume = life["costumes"][int(rng.next() * len(life["costumes"])) % len(life["costumes"])]
            h = rng.range(0.85, 1.2)
            skin = SKIN[int(rng.next() * len(SKIN)) % len(SKIN)]
            kids.append((costume, skin, h))
        rng.range(15, 40)  # first pause
        out.append((walk, u, d, side, kids))
    return out


def group_frame(walk, u, d, side):
    a, b = np.array(walk["from"], float), np.array(walk["to"], float)
    dirv = (b - a) / np.linalg.norm(b - a)
    right = np.array([dirv[1], -dirv[0]])
    p = a + (b - a) * u + right * side * walk["side"]
    heading = dirv * d
    ry = math.degrees(math.atan2(heading[0], heading[1]))
    return np.array([p[0], 0.06, p[1]]), ry, heading


def life_mesh(t, m=None):
    m = m or r3.Mesh()
    for walk, u, d, side, kids in groups(t):
        pos, ry, heading = group_frame(walk, u, d, side)
        R = r3.euler(0, ry, 0)
        for k, (costume, skin, h) in enumerate(kids):
            off = R @ np.array([-0.35 if k % 2 == 0 else 0.35, 0, -k * 0.8])
            add_kid(m, kid_parts(costume, skin), pos + off, ry, h)
    return m


def car_mesh(m, pos, ry, paint):
    R = r3.euler(0, ry, 0)
    par = (R, np.array(pos, float), 1.0)
    head, tail, tyre = (1, 0.92, 0.7), (1, 0.15, 0.1), (0.08, 0.08, 0.08)
    m.add_shape("box", (0, 0.55, 0), (1.8, 0.7, 4.2), (0, 0, 0), paint, 0, par)
    m.add_shape("box", (0, 1.1, -0.3), (1.6, 0.55, 2.2), (0, 0, 0), tuple(c * 0.8 for c in paint), 0, par)
    m.add_shape("box", (0, 1.1, -0.3), (1.62, 0.4, 2.0), (0, 0, 0), (0.35, 0.4, 0.5), 0, par)
    for s in (-1, 1):
        m.add_shape("sphere", (s * 0.6, 0.6, 2.1), (0.3, 0.22, 0.1), (0, 0, 0), head, 1.6, par)
        m.add_shape("sphere", (s * 0.65, 0.65, -2.1), (0.28, 0.16, 0.08), (0, 0, 0), tail, 1.6, par)
        for z in (1.3, -1.3):
            m.add_shape("cyl", (s * 0.85, 0.3, z), (0.55, 0.12, 0.55), (0, 0, 90), tyre, 0, par)


def cars(t):
    """The cars at the start, as TownLife.Build places them: (position, heading)."""
    life, h = t["life"], t["horizon"]
    rng = r3.Lcg(life["carSeed"])
    out = []
    for _ in range(life["cars"]):
        road = h["roads"][int(rng.next() * len(h["roads"])) % len(h["roads"])]
        u, incoming = rng.next(), rng.next() < 0.5
        rng.range(*life["carSpeed"])
        paint = (rng.range(0.1, 0.5), rng.range(0.1, 0.3), rng.range(0.12, 0.4))
        a, b = np.array(road["from"], float), np.array(road["to"], float)
        start, end = (b, a + (b - a) / np.linalg.norm(b - a) * 25) if incoming else (a, b)
        dirv = (end - start) / np.linalg.norm(end - start)
        p = start + (end - start) * u + np.array([dirv[1], -dirv[0]]) * 2
        out.append(((p[0], 0, p[1]), math.degrees(math.atan2(dirv[0], dirv[1])), paint))
    return out


def make_kids():
    """Every kid costume in a row, with their buckets."""
    t = town()[1]
    costumes = t["life"]["costumes"]
    W, H = 1400, 520
    m = r3.Mesh()
    m.add_shape("box", (0, -0.1, 0), (30, 0.2, 20), (0, 0, 0), (0.13, 0.12, 0.13))
    xs = [(len(costumes) - 1) / 2 * 1.0 - i * 1.0 for i in range(len(costumes))]
    for i, (x, c) in enumerate(zip(xs, costumes)):
        add_kid(m, kid_parts(c, SKIN[i % len(SKIN)]), (x, 0, 0), -10 if x > 0 else 10, 1.05)
    lights = [{"p": [-2.5, 2.2, 2.4], "c": [1.0, 0.7, 0.45], "range": 7, "intensity": 1.4},
              {"p": [2.5, 2.2, 2.4], "c": [0.75, 0.8, 1.0], "range": 7, "intensity": 1.2},
              {"p": [0, 0.6, 1.2], "c": [1.0, 0.55, 0.2], "range": 4, "intensity": 0.9}]
    cam = r3.Camera((0, 1.2, 7.0), (0, 0.62, 0), 27, W, H)
    img = r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.0, ambient=(0.24, 0.19, 0.3), moon=False)
    d = ImageDraw.Draw(img, "RGBA")
    for x, c in zip(xs, costumes):
        p = cam.project((x, 0.0, 0.4))[0]
        label(d, (p[0], p[1] + 14), c["kind"].capitalize(), 13)
    title_text(img, "Hollow Creek is out trick-or-treating", "Groups of kids walk every street with their candy buckets, and stop to tell you what they've heard", 0.1)
    save_png(img, "trick-or-treaters.png")


def make_street():
    """Main Street at night with the trick-or-treaters out, one group stopping to talk."""
    merged, t, mesh = town()
    m = life_mesh(t)
    gs = groups(t)
    # Stand near the first group on Main Street and look up the street past them.
    pick = next(g for g in gs if g[0]["name"] == "Main Street")
    pos, ry, heading = group_frame(*pick[:4])
    h3 = np.array([heading[0], 0, heading[1]])
    lateral = np.array([heading[1], 0, -heading[0]])
    eye = pos + h3 * 6.5 + lateral * 2.0 + np.array([0, 1.7, 0])
    W, H = 1280, 640
    cam = r3.Camera(eye, pos + np.array([0, 0.9, 0]) - h3 * 10, 55, W, H)
    lights = r3.all_lights(merged)
    img = r3.render(merged, cam, mesh, extra_mesh=m, lights=lights, horizon=t, horizon_t=3.0, fog_density=0.006)
    d = ImageDraw.Draw(img, "RGBA")
    rumour = t["life"]["rumours"][1]
    sp = cam.project(pos + np.array([0, 2.2, 0]))[0]
    label(d, (sp[0], sp[1] - 20), rumour, 15, fill=(255, 236, 190), bg=(20, 14, 30, 210))
    title_text(img, "Someone's always out tonight", "Kids stop to chat when you walk past: town gossip, and rumours about tonight's call", 0.09)
    save_png(img, "living-town.png")


def make_valley():
    """Looking east along Elm Street: cars on the road out of town and the train crossing the valley."""
    merged, t, mesh = town()
    m = r3.Mesh()
    for pos, ry, paint in cars(t):
        car_mesh(m, pos, ry, paint)
    tr = t["life"]["train"]
    # The moment the train is in the middle of the view (east, about 100 degrees).
    tt = (100 - tr["from"]) / tr["speed"]
    W, H = 1400, 560
    cam = r3.Camera((96, 9, -6), (400, 16, -40), 58, W, H)
    img = r3.render(merged, cam, mesh, extra_mesh=m, horizon=t, horizon_t=tt, fog_density=0.0035, moon=False)
    title_text(img, "Somewhere to go", "Cars on the road to Thornbury, and the late train crossing the valley", 0.09)
    save_png(img, "valley-train.png")


def make_face():
    """One face up close: a blink, a glance at the camera, then talking (FaceLife.cs)."""
    c = r3.costumes()
    parts = c["suspects"]["PembertonCottage.Heiress"]["parts"]
    W, H = 420, 420
    frames = []
    n = 40
    lights = [{"p": [-1.0, 2.4, 1.6], "c": [1.0, 0.75, 0.5], "range": 5, "intensity": 0.75},
              {"p": [1.2, 2.0, 1.4], "c": [0.7, 0.75, 1.0], "range": 5, "intensity": 0.55}]
    hy = next(q["p"][1] for q in parts if q["n"] == "Head")  # people have their own heights now
    lights = [dict(L, p=[L["p"][0], L["p"][1] + hy - 1.78, L["p"][2]]) for L in lights]
    cam = r3.Camera((0, hy, 1.25), (0, hy - 0.04, 0), 30, W, H)
    detail = r3.detail(True)
    detail.__enter__()
    for i in range(n):
        s = i / n * 4.0  # seconds
        blink = math.sin(min(1, (s - 0.6) / 0.14) * math.pi) if 0.6 <= s < 0.74 else 0
        blink = max(blink, math.sin(min(1, (s - 2.9) / 0.14) * math.pi) if 2.9 <= s < 3.04 else 0)
        look = (-0.9, 0.2) if s < 1.2 else ((0.0, 0.0) if s < 2.2 else (0.5, -0.3))
        talking = 2.2 <= s < 3.8
        mouth = abs(math.sin(s * 13) * 0.6 + math.sin(s * 7.3) * 0.4) if talking else 0
        m = r3.Mesh()
        for q in parts:
            q = dict(q)
            p, sc = list(q["p"]), list(q["s"])
            if q["n"] in ("LidL", "LidR"):
                p[1] -= 0.024 * blink
                sc = [sc[0], sc[1] * (1 + 1.2 * blink), sc[2] * 1.1]
            if q["n"] in ("LashL", "LashR"):
                p[1] -= 0.034 * blink
            if q["n"] in ("BrowL", "BrowR"):
                p[1] += 0.006 * mouth
            if q["n"] in ("EyeL", "EyeR", "IrisL", "IrisR", "PupilL", "PupilR", "GlintL", "GlintR"):
                p[0] += look[0] * 0.012
                p[1] += look[1] * 0.008
            if q["n"] == "Lips":
                sc = [sc[0] * (1 + 1.6 * mouth), sc[1], sc[2]]
            e = q["e"] if q["m"] == "emissive" else 0.0
            m.add_shape(q["t"], p, sc, q["r"], q["c"], e)
        img = r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0, ambient=(0.26, 0.2, 0.3), moon=False, ss=2)
        d = ImageDraw.Draw(img, "RGBA")
        cap = "blinks" if s < 1.2 else ("looks at you" if s < 2.2 else "talks")
        label(d, (W / 2, H - 24), cap, 16, fill=(255, 220, 170))
        frames.append(img)
    detail.__exit__(None, None, None)
    save_gif(frames, "face-life.gif", 100)


JOBS = {"kids": make_kids, "street": make_street, "valley": make_valley, "face": make_face}

if __name__ == "__main__":
    for job in sys.argv[1:] or list(JOBS):
        print(f"  {job}...", flush=True)
        JOBS[job]()
