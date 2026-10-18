#!/usr/bin/env python3
"""
3D pictures and animations of Blackwood Manor for the README, rendered from the same layout file
Unity builds the level from (Assets/Unmasked/Resources/BlackwoodManor.json).

    python3 Docs/tools/make_images_3d.py            # everything
    python3 Docs/tools/make_images_3d.py orbit      # just some: orbit walk cutaway floors match
                                                    #   hero villains turntable cast trail look

Illustrations of the design, not in-engine captures.
"""
import math
import os
import random
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import OUT, font, save_gif, save_png, ease, lerp, Track  # noqa: E402

L = r3.load_layout()
INK = (236, 232, 248)
MUTED = (170, 162, 200)


def label(d, xy, text, size=15, fill=INK, bg=(10, 8, 20, 170), anchor="mm"):
    f = font(size)
    box = d.textbbox(xy, text, font=f, anchor=anchor)
    d.rounded_rectangle([box[0] - 6, box[1] - 4, box[2] + 6, box[3] + 4], radius=6, fill=bg)
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def room_labels(img, cam, level, rooms_y=None, size=15, skip=()):
    d = ImageDraw.Draw(img, "RGBA")
    for room in L["rooms"]:
        if room["l"] != level or room["n"] in skip:
            continue
        mn, mx = room["min"], room["max"]
        y = (mn[1] + 1.2) if rooms_y is None else rooms_y
        p = cam.project(((mn[0] + mx[0]) / 2, y, (mn[2] + mx[2]) / 2))[0]
        if p[2] > 0:
            label(d, (p[0], p[1]), room["n"], size)


# ---------------------------------------------------------------------------
# Characters, bats and flicker (shared by the jobs below)
# ---------------------------------------------------------------------------
C3 = r3.costumes()
VILLAIN_IDS = ["HeadlessHorseman", "Banshee", "StingyJack", "BabaYaga"]
SUSPECT_NAMES = {"Groundskeeper": "Gus Thornbury", "Heiress": "Vivian Blackwood", "Rival": "Reginald Pike", "Cook": "Martha Bunce"}


def P(n, t, p, s, c, m="solid", r=(0, 0, 0), e=1.0):
    return {"n": n, "t": t, "p": list(p), "s": list(s), "r": list(r), "c": list(c), "m": m, "e": e, "k": ""}


def bats(t, center=(0, 13.5, 0), radius=15.0, n=14, scale=1.6):
    """The same flight paths as BatSwarm.cs."""
    m = r3.Mesh()
    dark = (0.06, 0.04, 0.08)
    for i in range(n):
        o = i * 2.399
        a = t * 0.35 * (1 + 0.15 * math.sin(o)) + o
        rad = radius * (0.7 + 0.3 * math.sin(t * 0.3 + o * 1.7))
        pos = (center[0] + math.cos(a) * rad, center[1] + 3 * math.sin(t * 0.7 + o), center[2] + math.sin(a) * rad)
        ry = math.degrees(math.atan2(-math.sin(a), math.cos(a)))
        flap = math.sin(t * 18 + o * 3) * 55
        f = math.radians(flap)
        parts = [P("Body", "sphere", (0, 0, 0), (0.14, 0.12, 0.24), dark),
                 P("Eyes", "sphere", (0, 0.02, 0.12), (0.08, 0.025, 0.02), (1, 0.25, 0.2), "emissive", e=3)]
        for side in (-1, 1):
            parts.append(P("Wing", "box", (side * 0.28 * math.cos(f), 0.28 * math.sin(f), 0), (0.5, 0.02, 0.26), dark, r=(0, 0, side * flap)))
        m.add_parts(parts, pos, ry, (0.8 + 0.4 * ((i * 7) % 5) / 4) * scale)
    return m


def flicker(lights, t):
    """Jack-o'-lanterns and candles breathe (the glows have no name; possessable lamps do)."""
    out = []
    for k, lt in enumerate(lights):
        lt = dict(lt)
        if "n" not in lt:
            lt["intensity"] = lt["intensity"] * (0.85 + 0.12 * math.sin(t * 7.3 + k * 1.7) + 0.08 * math.sin(t * 13.1 + k))
        out.append(lt)
    return out


def villain(mesh, vid, pos, ry, t=0.0, skip_mask=False, mask_motion=None):
    v = C3["villains"][vid]
    y = pos[1] + v["hover"] + (0.08 * math.sin(t * 2.2) if v["hover"] else 0)
    mesh.add_parts(v["parts"], (pos[0], y, pos[2]), ry, 1.0, skip_mask, mask_motion)


def embers(img, cam, t, seed=3, count=70, box=((-2.6, 2.6), (-40, -12)), color=(255, 150, 60)):
    """Sparks drifting up from the pumpkins (drawn over the frame, like the particle system in Unity)."""
    d = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(seed)
    sx = img.width / cam.w
    for _ in range(count):
        x, z = rng.uniform(*box[0]), rng.uniform(*box[1])
        if abs(x) < 1.4:
            x = math.copysign(rng.uniform(1.6, 2.6), x or 1)
        speed, phase = rng.uniform(0.3, 0.7), rng.uniform(0, 3)
        y = (phase + t * speed) % 2.6
        x += 0.15 * math.sin(t * 2 + phase * 3)
        p = cam.project((x, y, z))[0]
        if p[2] <= 0.3:
            continue
        r = min(3.2, max(1.0, 16 / p[2])) * sx
        a = int(255 * (1 - y / 2.6))
        d.ellipse([p[0] * sx - r, p[1] * sx - r, p[0] * sx + r, p[1] * sx + r], fill=color + (a,))


def title_text(img, text, sub, y=0.5):
    d = ImageDraw.Draw(img, "RGBA")
    W, H = img.size
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.text((W / 2, H * y), text, font=font(64, "Black"), fill=(255, 120, 30, 220), anchor="mm")
    from PIL import ImageFilter
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    img.paste(glow, (0, 0), glow)
    d.text((W / 2, H * y), text, font=font(64, "Black"), fill=(255, 236, 200), anchor="mm", stroke_width=3, stroke_fill=(40, 14, 30))
    d.text((W / 2, H * y + 46), sub, font=font(16, "Bold"), fill=(236, 220, 255), anchor="mm", stroke_width=2, stroke_fill=(20, 10, 30))


def timed(name):
    def wrap(fn):
        def run():
            t = time.time()
            fn()
            print(f"    ({name} took {time.time() - t:.0f}s)")
        return run
    return wrap


# ---------------------------------------------------------------------------
@timed("orbit")
def make_orbit():
    """Exterior orbit around the manor at night."""
    mesh = r3.layout_mesh(L)
    frames = []
    n = 40
    for i in range(n):
        a = math.radians(-120 + 360 * i / n)
        pos = (math.sin(a) * 50, 20 + 4 * math.sin(a * 2), math.cos(a) * -50)
        cam = r3.Camera(pos, (0, 4, 0), 42, 640, 360)
        t = i * 0.25
        img = r3.render(L, cam, mesh, extra_mesh=bats(t), lights=flicker(r3.all_lights(L), t))
        d = ImageDraw.Draw(img, "RGBA")
        label(d, (14, 16), "Blackwood Manor", 16, anchor="lt")
        frames.append(img)
    save_gif(frames, "manor-orbit.gif", 110)


# ---------------------------------------------------------------------------
WALK = [  # (time, camera position, look target)
    (-1.6, (0, 1.75, -41.5), (0, 4.6, -33)),
    (0.0, (0, 1.7, -37), (0, 3, -12)),
    (2.5, (0, 1.7, -29), (0, 3.5, -12)),
    (4.5, (3.5, 1.7, -22), (0, 2.5, -12)),
    (6.5, (0.4, 1.7, -15.5), (0, 1.8, -8)),
    (8.0, (0.2, 1.7, -11.2), (-1.5, 2.2, -4)),
    (9.5, (-1.2, 1.7, -8.2), (-2, 3.2, -2)),
    (10.6, (-2.0, 1.7, -6.4), (-2, 3.6, -1)),
    (12.6, (-2.0, 4.9, -1.6), (-2, 5.0, 4)),
    (14.0, (-0.5, 5.2, 3.2), (-6, 5.0, 6.8)),
    (15.6, (-3.2, 5.2, 6.6), (-10, 4.6, 7)),
    (17.4, (-8.0, 5.2, 6.6), (-13, 4.4, 7.5)),
]


@timed("walkthrough")
def make_walkthrough():
    """First-person walk: gate, fountain, front door, foyer, up the grand stairs, into the bedroom."""
    mesh = r3.layout_mesh(L)
    pos_track = Track([(t, *p) for t, p, _ in WALK])
    tgt_track = Track([(t, *g) for t, _, g in WALK])
    captions = [(-1.6, 0, "Under the jack-o'-lantern arch..."), (0, 3, "down the pumpkin trail..."), (3, 6.6, "past the fountain"), (6.6, 9.2, "into the foyer"),
                (9.2, 13.4, "up the grand staircase"), (13.4, 18, "the Heiress's bedroom")]
    fps = 6
    frames = []
    total = WALK[-1][0] - WALK[0][0]
    for f in range(int(total * fps) + 1):
        t = WALK[0][0] + f / fps
        pos = pos_track.at(t)
        # gentle head bob while walking
        pos = (pos[0], pos[1] + 0.04 * math.sin(t * 9), pos[2])
        cam = r3.Camera(pos, tgt_track.at(t), 68, 640, 360)
        img = r3.render(L, cam, mesh, fog_density=0.018, ambient=(0.13, 0.10, 0.2), extra_mesh=bats(t),
                        lights=flicker(r3.all_lights(L), t))
        d = ImageDraw.Draw(img, "RGBA")
        for a, b, msg in captions:
            if a <= t < b:
                label(d, (320, 334), msg, 15)
        here = ""
        for room in sorted(L["rooms"], key=lambda rm: (rm["max"][0] - rm["min"][0]) * (rm["max"][2] - rm["min"][2])):
            mn, mx = room["min"], room["max"]
            if mn[0] <= pos[0] <= mx[0] and mn[2] <= pos[2] <= mx[2] and mn[1] - 0.5 <= pos[1] - 1.0 < mx[1]:
                here = room["n"]
                break
        if here:
            label(d, (12, 14), here, 13, anchor="lt")
        frames.append(img)
    frames += [frames[-1]] * 6
    save_gif(frames, "manor-walkthrough.gif", int(1000 / fps))


# ---------------------------------------------------------------------------
@timed("cutaway")
def make_cutaway():
    cam = r3.Camera((24, 30, -32), (0, 0, 0), 40, 1000, 600)
    mesh = r3.layout_mesh(L, levels=[0, -1], cut_level=0, roof=False, grounds=False, window_glow=0.4)
    img = r3.render(L, cam, mesh, fog_density=0.003, light_boost=1.3, ambient=(0.24, 0.23, 0.30), moon=False)
    room_labels(img, cam, 0, rooms_y=1.6, size=16)
    d = ImageDraw.Draw(img, "RGBA")
    label(d, (20, 22), "Ground floor (walls cut away)", 18, anchor="lt")
    for name, p in (("Grand stairs", (-2, 2.2, -3.5)), ("Cellar stairs", (2, 0.8, 7.5)), ("Trap site", (1.2, 0.5, -7.5))):
        s = cam.project(p)[0]
        label(d, (s[0], s[1]), name, 12, fill=(255, 220, 140))
    save_png(img, "manor-cutaway.png")


@timed("floors")
def make_floors():
    W, H = 420, 330
    panels = []
    specs = [(-1, "Cellar", (0, -3.5, 4), [-1]), (0, "Ground floor", (0, 0, 0), [0]), (1, "Upstairs", (0, 3.5, 0), [1])]
    for level, title, center, levels in specs:
        cx, cy, cz = center
        cam = r3.Camera((cx + 22, cy + 32, cz - 30), center, 38, W, H)
        mesh = r3.layout_mesh(L, levels=levels, cut_level=level, roof=False, grounds=False, window_glow=0.4)
        img = r3.render(L, cam, mesh, fog_density=0.002, light_boost=1.4, ambient=(0.25, 0.24, 0.31), moon=False)
        room_labels(img, cam, level, rooms_y=cy + 1.4, size=11)
        d = ImageDraw.Draw(img, "RGBA")
        label(d, (12, 14), title, 15, anchor="lt")
        panels.append(img)
    sheet = Image.new("RGB", (W * 3 + 20, H), (14, 12, 28))
    for i, p in enumerate(panels):
        sheet.paste(p, (i * (W + 10), 0))
    save_png(sheet, "manor-floors.png")


# ---------------------------------------------------------------------------
# A match in 3D (ground floor cutaway)
# ---------------------------------------------------------------------------
GREEN, BLUE, ORANGE, YELLOW, RED = (0.35, 0.85, 0.5), (0.4, 0.6, 1.0), (1.0, 0.6, 0.2), (1.0, 0.85, 0.3), (1.0, 0.25, 0.25)
PURPLE, GHOST, MASK = (0.55, 0.3, 0.8), (0.7, 0.92, 1.0), (0.95, 0.95, 0.88)

SOLVERS = [
    ("Sleuth", GREEN, Track([(0, 0, 0, -14), (1.5, -1, 0, -9.5), (3, -4.6, 0, -7), (4.6, -12, 0, -9), (5.6, -14, 0, -10.4),
                             (6.6, -10, 0, -2.6), (7.4, -7.8, 0, 1.6), (8.4, -4.6, 0, 1), (10, -0.2, 0, -6.4), (16, -0.2, 0, -6.4)])),
    ("Techie", BLUE, Track([(0, 1, 0, -14.5), (1.6, 0.6, 0, -4), (2.8, -4.6, 0, 1), (4.4, -8, 0, 3.8), (5.6, -8, 0, 3.8),
                            (6.6, -12, 0, 6), (8.4, -13.4, 0, 9.2), (9.6, -13.8, 0, 9), (10.6, -4.6, 0, 1), (11.5, 0.2, 0, -8.6), (16, 0.2, 0, -8.6)])),
    ("Brawn", ORANGE, Track([(0, -1, 0, -14.5), (1.6, 2, 0, -8.4), (3, 4.6, 0, -7), (4.6, 9, 0, -8.4), (8.4, 9.5, 0, -8),
                             (10, 14, 0, -1.8), (11, 4.6, 0, -7), (11.8, 2.4, 0, -7.2), (16, 2.4, 0, -7.2)])),
    ("Snacker", YELLOW, Track([(0, 0.5, 0, -15.5), (1.6, 2.5, 0, -9), (2.6, 4.6, 0, -7), (3.4, 9.6, 0, 1.2), (4.2, 11.6, 0, 7.6),
                               (9, 11.6, 0, 7.6), (9.8, 4.6, 0, 8), (10.3, 2, 0, 5.3), (11.0, 2, -3.5, 9.9), (11.4, 2, -3.5, 9.9),
                               (12.1, 2, 0, 5.3), (12.6, -1.6, 0, 4.6), (13.2, 1.0, 0, -6.2), (16, 1.0, 0, -6.2)])),
]
FEAR = [Track([(0, 5), (16, 12)]),
        Track([(0, 5), (4.4, 20), (5.6, 100), (8.6, 100), (9.6, 35), (16, 30)]),
        Track([(0, 5), (6, 12), (8.6, 58), (10, 40), (13.3, 36), (13.45, 82), (14.4, 50), (16, 40)]),
        Track([(0, 5), (12.4, 15), (13.4, 70), (14.2, 40), (16, 30)])]
PANIC = (5.6, 8.6)
GHOST_T = Track([(0, 0, 2.6, 9), (2, -1, 2.8, 6), (3.6, -6, 1.8, 3.4), (4.3, -7, 1.2, 3)])
COSTUME_T = Track([(11.6, -2, 3.5, -1.2), (13.2, -2, 0, -6.1), (13.8, -0.4, 0, -7.0), (14.2, 1.2, 0, -7.5), (16, 1.2, 0, -7.5)])
ARMCHAIR = (-7, 0.45, 3)
LEAKED = (-7.6, 0.25, 2.0)
SEEDED = (-14.5, 0.25, -11)
CAPTIONS = [(0, 2.4, "Night falls. The Mystery Club walks in."), (2.4, 3.8, "The chandelier flickers..."),
            (3.8, 5.4, "Snacker interviews the Cook"), (4.4, 5.6, "Something is inside the armchair..."),
            (5.6, 6.6, "Clue in the study: fresh rose petals"), (6.6, 7.4, "The armchair LAUNCHES. Techie panics!"),
            (7.4, 8.8, "Sleuth finds a leaked clue: a muddy boot print"), (8.8, 9.8, "\"It's the Groundskeeper!\"  Correct!"),
            (9.8, 12.2, "TRAP: fetch pieces (one is down in the cellar)"), (12.2, 13.4, "The Headless Horseman rides down... and hurls a flaming pumpkin!"),
            (13.4, 14.4, "Trap armed... it's coming..."), (14.4, 16.5, "UNMASKED! It was Gus Thornbury!")]


def phase(t):
    return ("INVESTIGATION", (120, 170, 255)) if t < 8.8 else (("TRAP", (255, 160, 70)) if t < 14.2 else ("UNMASKED", (110, 230, 140)))


@timed("match")
def make_match():
    cam = r3.Camera((20, 27, -30), (0, 0, -1.5), 42, 720, 450)
    big = r3.big_camera(cam)
    static_layout = dict(L)
    static_layout["possessables"] = [p for p in L["possessables"] if p["n"] != "Armchair"]
    static = r3.layout_mesh(static_layout, levels=[0], cut_level=0, roof=False, grounds=False, window_glow=0.35)
    base = r3.rasterize(big, static)
    random.seed(5)
    fps = 12
    frames = []
    for f in range(int(16.5 * fps)):
        t = f / fps
        dyn = r3.Mesh()
        lights = [dict(lt) for lt in L["lights"] if lt["l"] == 0]
        for lt in lights:
            if lt["n"] == "Chandelier" and 2.4 < t < 3.8:
                lt["intensity"] = lt["intensity"] * random.choice((0.05, 0.3, 1.0, 0.1))
        # armchair: shakes while possessed, then launches at the Techie
        ax, ay, az = ARMCHAIR
        if 4.4 < t < 5.6:
            ax += random.uniform(-0.08, 0.08)
            az += random.uniform(-0.08, 0.08)
        elif t >= 5.6:
            u = min(1, (t - 5.6) / 0.5)
            ax, ay, az = lerp(ax, -8.2, u), ay + 1.6 * math.sin(u * math.pi) , lerp(az, 4.4, u)
        dyn.add_shape("box", (ax, ay, az), (1, 0.9, 1), (0, 30 * max(0, min(1, (t - 5.6) / 0.5)), 0), (0.55, 0.12, 0.12),
                      0.25 if 4.4 < t < 5.6 else 0)
        # clues
        if t < 5.6:
            dyn.add_shape("box", SEEDED, (0.3, 0.3, 0.3), (0, t * 90, 0), (1, 0.85, 0.2), 1.2)
        if 6.0 < t < 7.4:
            dyn.add_shape("box", LEAKED, (0.3, 0.3, 0.3), (0, t * 90, 0), (1, 0.85, 0.2), 1.2)
        # trap pieces, site and cage
        delivered = sum(1 for tt in (11.5, 11.8, 13.2) if t >= tt)
        if 8.8 <= t < 10.4:
            dyn.add_shape("box", (-14, 0.25, 9), (0.6, 0.5, 0.6), (0, 0, 0), (1, 0.5, 0.1), 0.8)
        if 8.8 <= t < 10.0:
            dyn.add_shape("box", (14.5, 0.25, -1.5), (0.6, 0.5, 0.6), (0, 0, 0), (1, 0.5, 0.1), 0.8)
        for k in range(delivered):
            dyn.add_shape("box", (0.4 + k * 0.7, 0.2, -7.5), (0.55, 0.4, 0.55), (0, 20 * k, 0), (1, 0.5, 0.1), 0.6)
        site = (1.2, 0, -7.5)
        armed = t >= 13.4
        dyn.add_shape("cyl", (site[0], 0.03, site[2]), (2.5, 0.02, 2.5), (0, 0, 0), (0.25, 0.9, 0.4), 0.9 if armed else 0.25)
        if t >= 14.2:
            drop = min(1, (t - 14.2) / 0.35)
            for dx in (-1.1, 1.1):
                for dz in (-1.1, 1.1):
                    dyn.add_shape("box", (site[0] + dx, 4.5 - 3 * drop, site[2] + dz), (0.12, 3, 0.12), (0, 0, 0), (0.3, 1, 0.45), 0.8)
            dyn.add_shape("box", (site[0], 6 - 3 * drop, site[2]), (2.4, 0.12, 2.4), (0, 0, 0), (0.3, 1, 0.45), 0.8)
        # solvers with flashlights
        for i, (name, col, track) in enumerate(SOLVERS):
            x, y, z = track.at(t)
            px, py, pz = track.at(max(0, t - 0.12))
            panicked = i == 1 and PANIC[0] <= t <= PANIC[1]
            jit = random.uniform(-0.06, 0.06) if panicked else 0
            hop = abs(math.sin(t * 22)) * 0.25 if panicked else abs(math.sin(t * 11)) * 0.05
            heading = math.atan2(x - px, z - pz) if abs(x - px) + abs(z - pz) > 1e-3 else 0
            flash = panicked and int(t * 8) % 2
            dyn.add_parts(C3["solvers"][name]["parts"], (x + jit, y + hop, z), math.degrees(heading), 1.0, tint=RED if flash else None)
            if not panicked and t < 14.4 and y > -1:
                lights.append({"p": [x + math.sin(heading) * 1.2, 1.4, z + math.cos(heading) * 1.2], "c": [1, 0.95, 0.8], "range": 5.5, "intensity": 1.1})
        # ghost (only the Haunter sees it in game)
        if t < 4.4:
            gx, gy, gz = GHOST_T.at(t)
            gy += 0.2 * math.sin(t * 5)
            dyn.add_shape("capsule", (gx, gy, gz), (0.5, 0.45, 0.5), (0, 0, 0), GHOST, 1.0)
            lights.append({"p": [gx, gy, gz], "c": [0.6, 0.85, 1], "range": 4, "intensity": 1.2})
        # tonight's legend, the Headless Horseman, comes down the stairs, throws a pumpkin, is caught and unmasked
        if t >= 11.6:
            hx, hy, hz = COSTUME_T.at(t)
            stun = t >= 14.2
            spin = (t - 14.2) * 400 if stun and t < 14.8 else 0
            motion = None
            if t >= 14.6:
                u = min(1, (t - 14.6) / 0.9)
                motion = ((-1.0 * u, 2.2 * u - 1.4 * u * u, 0.6 * u), (u * 540, u * 90, 0))
            villain(dyn, "HeadlessHorseman", (hx, hy, hz), 180 + spin, t, mask_motion=motion)
            lights.append({"p": [hx + 0.5, hy + 2.0, hz - 0.5], "c": [1, 0.5, 0.15], "range": 5, "intensity": 1.4})
            if t >= 14.6:
                # Under the costume: the Groundskeeper's face and straw hat where the flaming neck was
                dyn.add_shape("sphere", (hx, hy + 1.86, hz), (0.34, 0.38, 0.34), (0, 0, 0), (0.91, 0.71, 0.56), 0.15)
                dyn.add_shape("cyl", (hx, hy + 2.08, hz), (0.62, 0.015, 0.62), (0, 0, 0), (0.84, 0.7, 0.35), 0.15)
                dyn.add_shape("cyl", (hx, hy + 2.17, hz), (0.32, 0.09, 0.32), (0, 0, 0), (0.84, 0.7, 0.35), 0.15)
        # the flaming pumpkin: an arc from the Horseman's hand to the Brawn, then a burst
        if 12.7 <= t < 13.3:
            u = (t - 12.7) / 0.6
            a, b = np.array([-1.5, 2.6, -4.6]), np.array([2.4, 0.6, -7.2])
            pp = a + (b - a) * u + np.array([0, 2.2 * u * (1 - u) * 2, 0])
            dyn.add_parts(C3["props"]["jack"]["parts"], tuple(pp - np.array([0, 0.25, 0])), u * 720, 0.8)
            lights.append({"p": list(pp), "c": [1, 0.5, 0.15], "range": 6, "intensity": 2.0})
        elif 13.3 <= t < 13.9:
            u = (t - 13.3) / 0.6
            rng = random.Random(7)
            for k in range(14):
                ang, up = rng.uniform(0, 6.28), rng.uniform(0.2, 1.2)
                d = 0.4 + 2.2 * u
                dyn.add_shape("sphere", (2.4 + math.cos(ang) * d, 0.6 + up * d * 0.8 - 1.5 * u * u, -7.2 + math.sin(ang) * d),
                              (0.18 * (1 - u) + 0.05,) * 3, (0, 0, 0), (1, 0.55, 0.15), 2.5)
            lights.append({"p": [2.4, 1.0, -7.2], "c": [1, 0.55, 0.15], "range": 8 * (1 - u) + 2, "intensity": 3 * (1 - u)})
        gbuf = r3.rasterize(big, dyn, base)
        arr = r3.shade(gbuf, lights, big, fog_density=0.003, light_boost=1.3, ambient=(0.22, 0.21, 0.28),
                       background=r3.sky(big.w, big.h))
        img = r3.to_image(arr).resize((cam.w, cam.h), Image.LANCZOS)
        hud(img, t)
        frames.append(img)
    frames += [frames[-1]] * 10
    save_gif(frames, "match-3d.gif", int(1000 / fps))


def hud(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    name, col = phase(t)
    label(d, (14, 14), name, 16, fill=col, anchor="lt")
    for i, (sname, scol, _) in enumerate(SOLVERS):
        y = 14 + i * 22
        fear = FEAR[i].at(t)[0]
        x0 = 560
        d.text((x0, y), sname, font=font(11), fill=tuple(int(c * 255) for c in scol))
        d.rounded_rectangle([x0 + 58, y + 2, x0 + 150, y + 12], radius=4, fill=(40, 34, 60, 220))
        bar = (240, 70, 70) if fear > 80 else ((255, 160, 70) if fear > 50 else tuple(int(c * 255) for c in scol))
        if i == 1 and PANIC[0] <= t <= PANIC[1] and int(t * 8) % 2:
            bar = (255, 255, 255)
        d.rounded_rectangle([x0 + 58, y + 2, x0 + 58 + 92 * fear / 100, y + 12], radius=4, fill=bar)
    for a, b, msg in CAPTIONS:
        if a <= t < b:
            label(d, (360, 424), msg, 16)
    if t >= 14.4:
        s = min(1, (t - 14.4) / 0.4)
        d.text((360, 120), "UNMASKED!", font=font(int(30 + 22 * s), "Black"), fill=(255, 238, 130), anchor="mm",
               stroke_width=3, stroke_fill=(30, 20, 40))
    d.text((706, 444), "illustration, not an in-game capture", font=font(9, "Medium"), fill=MUTED, anchor="rb")


# ---------------------------------------------------------------------------
# Halloween night: the hero shot, the villains, the cast, the pumpkin trail, the look
# ---------------------------------------------------------------------------
@timed("hero")
def make_hero():
    """The README's opening shot: under the jack-o'-lantern arch, the Horseman waiting on the trail."""
    mesh = r3.layout_mesh(L)
    W, H = 800, 340
    frames = []
    n = 36
    for i in range(n):
        e = ease(i / (n - 1))
        t = i * 0.12
        cam = r3.Camera((lerp(-1.0, 0.4, e), lerp(3.6, 2.7, e), lerp(-41.4, -36.8, e)), (0, 3.4, -12), 50, W, H)
        dyn = bats(t * 2)
        villain(dyn, "HeadlessHorseman", (-3.0, 0, -29.5), 200, t)
        lights = flicker(r3.all_lights(L), t) + [{"p": [-2.6, 2.3, -30.0], "c": [1, 0.5, 0.15], "range": 6, "intensity": 1.8}]
        img = r3.render(L, cam, mesh, extra_mesh=dyn, lights=lights)
        embers(img, cam, t)
        title_text(img, "UNMASKED", "a spooky 3D asymmetric mystery  ·  Unity 6", 0.2)
        d = ImageDraw.Draw(img, "RGBA")
        d.text((W - 8, H - 6), "rendered from the game's own level and costume files", font=font(9, "Medium"), fill=MUTED, anchor="rb")
        frames.append(img)
    save_gif(frames, "hero.gif", 90)


def villain_stage(xs, ry=0.0, t=0.0, jacks=True):
    m = r3.Mesh()
    m.add_shape("box", (0, -0.1, 0), (40, 0.2, 24), (0, 0, 0), (0.11, 0.08, 0.13))
    m.add_shape("box", (0, 0.01, 0.3), (12.5, 0.02, 2.6), (0, 0, 0), (0.2, 0.13, 0.12))
    props = C3["props"]
    if jacks:
        for k in range(16):
            x = -7.5 + k * 1.0
            m.add_parts(props["jack" if k % 3 else "pumpkin"]["parts"], (x, 0, -2.4 - 0.3 * (k % 2)), 15 * math.sin(k), 0.9 + 0.3 * (k % 3 == 0))
        for x in (-6.6, 6.6):
            m.add_parts(props["haybale"]["parts"], (x, 0, -0.6), 90)
            m.add_parts(props["jack"]["parts"], (x, 0.6, -0.6), 0, 1.2)
        for x, h in ((-9, 7), (9.5, 6), (-5, 5.5), (6, 6.5)):
            m.add_shape("box", (x, h / 2, -6), (0.5, h, 0.5), (0, 0, 0), (0.1, 0.07, 0.08))
            m.add_shape("box", (x + 0.9, h * 0.7, -6), (0.2, 2.4, 0.2), (0, 0, -40), (0.1, 0.07, 0.08))
    for x, vid in zip(xs, VILLAIN_IDS):
        villain(m, vid, (x, 0, 0), ry, t)
    lights = [{"p": [-6.6, 1.0, 0.2], "c": [1, 0.55, 0.2], "range": 6, "intensity": 1.4},
              {"p": [6.6, 1.0, 0.2], "c": [1, 0.55, 0.2], "range": 6, "intensity": 1.4},
              {"p": [0, 0.7, -1.6], "c": [1, 0.5, 0.15], "range": 8, "intensity": 1.4}]
    for x, vid in zip(xs, VILLAIN_IDS):
        lights.append({"p": [x, 2.6, 1.8], "c": C3["villains"][vid]["glow"], "range": 5.5, "intensity": 1.3})
    return m, lights


@timed("villains")
def make_villains():
    W, H = 1200, 620
    xs = [4.2, 1.4, -1.4, -4.2]  # +x is screen-left when looking down -z
    m, lights = villain_stage(xs)
    cam = r3.Camera((0, 1.75, 8.6), (0, 1.25, 0), 38, W, H)
    img = r3.render(L, cam, m, lights=lights, fog_density=0.025, ambient=(0.17, 0.12, 0.26))
    d = ImageDraw.Draw(img, "RGBA")
    title_text(img, "Tonight's legends", "the Haunter picks a costume; the mystery is who is under it", 0.09)
    for x, vid in zip(xs, VILLAIN_IDS):
        v = C3["villains"][vid]
        p = cam.project((x, -0.1, 1.2))[0]
        cx, cy = p[0], min(H - 70, p[1] + 10)
        d.rounded_rectangle([cx - 132, cy - 4, cx + 132, cy + 62], radius=10, fill=(14, 8, 24, 215), outline=tuple(int(c * 255) for c in v["glow"]) + (255,), width=2)
        d.text((cx, cy + 12), v["name"], font=font(17, "Black"), fill=(255, 236, 210), anchor="mm")
        d.text((cx, cy + 32), v["origin"], font=font(11, "Medium"), fill=MUTED, anchor="mm")
        d.text((cx, cy + 50), f"[6 / Q]  {v['power']}", font=font(13, "Bold"), fill=tuple(int(c * 255) for c in v["glow"]), anchor="mm")
    save_png(img, "villains.png")


@timed("turntable")
def make_turntable():
    W, H = 860, 320
    xs = [3.3, 1.1, -1.1, -3.3]
    frames = []
    n = 30
    for i in range(n):
        ry = 360 * i / n
        m, lights = villain_stage(xs, ry, i * 0.2, jacks=False)
        for x in xs:
            m.add_shape("cyl", (x, 0.05, 0), (1.5, 0.05, 1.5), (0, 0, 0), (0.25, 0.17, 0.3))
        cam = r3.Camera((0, 1.6, 9.2), (0, 1.15, 0), 32, W, H)
        img = r3.render(L, cam, m, lights=lights, fog_density=0.0, ambient=(0.2, 0.15, 0.3), moon=False)
        d = ImageDraw.Draw(img, "RGBA")
        for x, vid in zip(xs, VILLAIN_IDS):
            p = cam.project((x, -0.1, 0.8))[0]
            label(d, (p[0], min(H - 16, p[1] + 4)), C3["villains"][vid]["name"], 13)
        frames.append(img)
    save_gif(frames, "villains-turntable.gif", 100)


@timed("cast")
def make_cast():
    W, H = 1200, 470
    m = r3.Mesh()
    m.add_shape("box", (0, -0.1, 0), (40, 0.2, 24), (0, 0, 0), (0.11, 0.08, 0.13))
    solvers = ["Sleuth", "Techie", "Brawn", "Snacker"]
    suspects = ["Groundskeeper", "Heiress", "Rival", "Cook"]
    sx = [6.2, 4.8, 3.4, 2.0]
    ux = [-2.0, -3.4, -4.8, -6.2]
    for x, sid in zip(sx, solvers):
        m.add_parts(C3["solvers"][sid]["parts"], (x, 0, 0), 15)
    for x, sid in zip(ux, suspects):
        m.add_parts(C3["suspects"][sid]["parts"], (x, 0, 0), -15)
    m.add_parts(C3["props"]["haybale"]["parts"], (0, 0, -0.2), 0)
    m.add_parts(C3["props"]["jack"]["parts"], (0, 0.6, -0.2), 0, 1.1)
    m.add_parts(C3["props"]["pumpkin"]["parts"], (0.55, 0, 0.6), 30, 0.8)
    m.add_parts(C3["props"]["jack"]["parts"], (-0.5, 0, 0.7), -20, 0.7)
    lights = [{"p": [4.0, 2.8, 2.6], "c": [0.8, 0.85, 1.0], "range": 7, "intensity": 1.3},
              {"p": [-4.0, 2.8, 2.6], "c": [1.0, 0.7, 0.45], "range": 7, "intensity": 1.3},
              {"p": [0, 0.8, 0], "c": [1, 0.55, 0.2], "range": 5, "intensity": 1.5}]
    cam = r3.Camera((0, 1.5, 9.8), (0, 1.15, 0), 40, W, H)
    img = r3.render(L, cam, m, lights=lights, fog_density=0.02, ambient=(0.2, 0.15, 0.28))
    d = ImageDraw.Draw(img, "RGBA")
    for x, name, sub in [(x, s, "") for x, s in zip(sx, solvers)] + [(x, SUSPECT_NAMES[s], s) for x, s in zip(ux, suspects)]:
        p = cam.project((x, -0.05, 0.6))[0]
        label(d, (p[0], p[1] + 8), name.replace(" ", "\n") if sub else name, 11)
        if sub:
            d.text((p[0], p[1] + 36), sub, font=font(10, "Medium"), fill=MUTED, anchor="mm")
    title_text(img, "The cast", "", 0.1)
    for x0, x1, text in ((sx[0], sx[-1], "The Mystery Club (players)"), (ux[0], ux[-1], "The suspects (one is the Haunter)")):
        p = cam.project(((x0 + x1) / 2, 2.55, 0))[0]
        label(d, (p[0], p[1]), text, 15, fill=(255, 200, 140))
    save_png(img, "cast.png")


@timed("trail")
def make_trail():
    """A knee-high dolly along the jack-o'-lantern trail (after LA's Nights of the Jack)."""
    mesh = r3.layout_mesh(L)
    W, H = 720, 340
    frames = []
    n = 44
    for i in range(n):
        u = i / (n - 1)
        t = i * 0.12
        z = lerp(-38.6, -31.0, u)
        cam = r3.Camera((-0.3, 0.8, z), (-2.7, 0.45, z + 2.3), 60, W, H)
        img = r3.render(L, cam, mesh, extra_mesh=bats(t * 2), lights=flicker(r3.all_lights(L), t), fog_density=0.02)
        embers(img, cam, t, count=110)
        d = ImageDraw.Draw(img, "RGBA")
        label(d, (14, 16), "The jack-o'-lantern trail", 15, anchor="lt")
        frames.append(img)
    save_gif(frames, "pumpkin-trail.gif", 110)


@timed("look")
def make_look():
    """Art direction board: before/after of the same view, plus the palette."""
    W, H = 560, 320
    cam = r3.Camera((0.5, 2.0, -34.5), (0, 2.4, -12), 54, W, H)
    plain = dict(L, decor=[], glows=[])
    before = r3.render(plain, cam, r3.layout_mesh(plain), cel=False, rim_strength=0, ambient=(0.10, 0.10, 0.16),
                       moon=(0.32, 0.36, 0.55), fog=(0.05, 0.05, 0.10))
    after = r3.render(L, cam, r3.layout_mesh(L), extra_mesh=bats(3.0), lights=flicker(r3.all_lights(L), 1.0))
    embers(after, cam, 1.0)
    board = Image.new("RGB", (W * 2 + 60, H + 210), (14, 10, 24))
    d = ImageDraw.Draw(board, "RGBA")
    d.text((20, 18), "The look: Halloween night", font=font(22, "Black"), fill=(255, 236, 210))
    d.text((20, 48), "Toon light bands, violet rim light, bloom on every jack-o'-lantern, purple fog, embers and bats",
           font=font(12, "Medium"), fill=MUTED)
    for k, (img, cap) in enumerate(((before, "Before: plain moonlight"), (after, "After: Halloween night"))):
        x = 20 + k * (W + 20)
        board.paste(img, (x, 76))
        label(d, (x + 10, 88), cap, 13, anchor="lt")
    pal = C3["palette"]
    names = list(pal.keys())
    sw = (W * 2 + 20) / len(names)
    for i, name in enumerate(names):
        h = pal[name].lstrip("#")
        col = tuple(int(h[j:j + 2], 16) for j in (0, 2, 4))
        x = 20 + i * sw
        d.rounded_rectangle([x + 2, H + 96, x + sw - 4, H + 150], radius=8, fill=col)
        d.text((x + sw / 2 - 1, H + 164), name.replace("_", " "), font=font(10, "Medium"), fill=MUTED, anchor="mm")
        d.text((x + sw / 2 - 1, H + 180), "#" + h, font=font(9, "Medium"), fill=(120, 110, 150), anchor="mm")
    save_png(board, "art-direction.png")


JOBS = {"cutaway": make_cutaway, "floors": make_floors, "orbit": make_orbit, "walk": make_walkthrough, "match": make_match,
        "hero": make_hero, "villains": make_villains, "turntable": make_turntable, "cast": make_cast, "trail": make_trail,
        "look": make_look}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(JOBS):
        print(f"  rendering {name}...")
        JOBS[name]()
