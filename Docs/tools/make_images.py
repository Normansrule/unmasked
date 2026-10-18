#!/usr/bin/env python3
"""
Draws every README image and animation in Docs/images from code (Pillow + numpy), so they can be
regenerated whenever the game changes:  python3 Docs/tools/make_images.py
The 3D manor renders live in make_images_3d.py and the town ones in make_images_town.py (the "3d"
and "town" jobs, both included by default).

These are illustrations of the design (layout taken from TestRoomBuilder.cs, numbers from the
scripts), not in-engine screenshots. Real screenshots go in Docs/screenshots (F12 in game).
"""
import math
import os
import random
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Docs", "images")
os.makedirs(OUT, exist_ok=True)
SS = 2  # supersampling for smooth edges

# ---------------------------------------------------------------------------
# Palette and fonts
# ---------------------------------------------------------------------------
NIGHT = (14, 12, 28)
PANEL = (26, 22, 44)
INK = (232, 228, 245)
MUTED = (150, 142, 180)
WALL = (92, 84, 110)
FLOOR = (44, 34, 30)
GREEN = (80, 200, 120)
BLUE = (90, 150, 255)
ORANGE = (255, 150, 50)
YELLOW = (255, 215, 80)
RED = (240, 70, 70)
PURPLE = (150, 80, 210)
GHOST = (170, 230, 255)
CLUE = (255, 220, 70)

FONT_DIRS = ["/usr/share/fonts/opentype/inter", "/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts", "/Library/Fonts"]


def font(size, weight="Bold"):
    names = [f"Inter-{weight}.otf", f"InterDisplay-{weight}.otf", "DejaVuSans-Bold.ttf" if weight != "Regular" else "DejaVuSans.ttf", "arialbd.ttf", "Arial.ttf"]
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def canvas(w, h, color=NIGHT):
    img = Image.new("RGB", (w * SS, h * SS), color)
    return img, ImageDraw.Draw(img, "RGBA")


def finish(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def text(d, xy, s, size=16, fill=INK, weight="Bold", anchor="la"):
    d.text((xy[0] * SS, xy[1] * SS), s, font=font(size * SS, weight), fill=fill, anchor=anchor)


def rect(d, box, fill=None, outline=None, width=1, radius=0):
    b = [v * SS for v in box]
    if radius:
        d.rounded_rectangle(b, radius=radius * SS, fill=fill, outline=outline, width=width * SS)
    else:
        d.rectangle(b, fill=fill, outline=outline, width=width * SS)


def circle(d, c, r, fill=None, outline=None, width=1):
    d.ellipse([(c[0] - r) * SS, (c[1] - r) * SS, (c[0] + r) * SS, (c[1] + r) * SS], fill=fill, outline=outline, width=width * SS)


def poly(d, pts, fill=None, outline=None):
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=fill, outline=outline)


def line(d, pts, fill, width=2):
    d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=width * SS)


def save_gif(frames, name, ms):
    path = os.path.join(OUT, name)
    # One shared palette, no dithering: frames then differ only where things move, which keeps
    # the GIFs small.
    picks = frames[:: max(1, len(frames) // 12)]
    sheet = Image.new("RGB", (frames[0].width, frames[0].height * len(picks)))
    for i, f in enumerate(picks):
        sheet.paste(f, (0, i * f.height))
    base = sheet.quantize(colors=230, method=Image.MEDIANCUT)
    pal = [f.quantize(palette=base, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=ms, loop=0, optimize=False)
    # ImageMagick (optional) stores only the changed pixels per frame: about 4x smaller.
    if shutil.which("convert"):
        subprocess.run(["convert", path, "-layers", "Optimize", path], check=False)
    print(f"  {name}: {len(frames)} frames, {os.path.getsize(path) // 1024} KB")


def save_png(img, name):
    path = os.path.join(OUT, name)
    img.save(path, optimize=True)
    print(f"  {name}: {os.path.getsize(path) // 1024} KB")


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------
# Blackwood Manor test room (mirrors Assets/Unmasked/Scripts/Editor/TestRoomBuilder.cs)
# ---------------------------------------------------------------------------
WALLS = [  # (x1, z1, x2, z2) segments in world metres
    (-15, 15, 15, 15), (-15, -15, 15, -15), (15, -15, 15, 15), (-15, -15, -15, 15),
    (0, -15, 0, -0.75), (0, 0.75, 0, 15), (3, -4, 15, -4),
]
POSSESSABLES = {"Armchair": (-8, 4), "Vase": (-4, -6), "Armor": (4, 12), "Clock": (13.5, -10), "Bookcase": (-14, 8)}
LAMPS = [(-9, -2), (9, 3)]
SUSPECTS = {"Groundskeeper": ((-11, 12), (110, 150, 70)), "Heiress": ((-3, 10), (190, 90, 170)),
            "Rival": ((11, -12), (80, 100, 160)), "Cook": ((12, 10), (235, 235, 220))}
CLUE_SPOTS = [(-13, -2), (-6, 13), (-1.5, -13), (-10, -8), (3, 3), (13, 13), (6, -13), (13, -2), (2, -6), (-7, 7)]
PIECES = [(-12, 0), (12, 6), (-2, 12), (5, -10)]
TRAP_SITE = (-6, 0)
TRAPDOOR = (7, 7)
CELLAR = (-12, -12)
SOLVER_SPAWNS = [(-6 + i * 1.5, -12) for i in range(4)]
HAUNTER_SPAWN = (10, 0)


class MapView:
    def __init__(self, ox, oy, size):
        self.ox, self.oy, self.s = ox, oy, size / 30.0

    def p(self, x, z):
        return (self.ox + (x + 15) * self.s, self.oy + (15 - z) * self.s)


def draw_house(d, mv, labels=False, lamps_on=True):
    x0, y0 = mv.p(-15, 15)
    x1, y1 = mv.p(15, -15)
    rect(d, (x0, y0, x1, y1), fill=FLOOR)
    # floorboards
    cx, cy = mv.p(*CELLAR)
    rect(d, (cx - 2.5 * mv.s, cy - 2.5 * mv.s, cx + 2.5 * mv.s, cy + 2.5 * mv.s), fill=(20, 18, 18))
    if lamps_on:
        for lx, lz in LAMPS:
            c = mv.p(lx, lz)
            for r, a in ((7.5, 18), (5, 22), (3, 30)):
                circle(d, c, r * mv.s, fill=(255, 190, 110, a))
    for x1_, z1_, x2_, z2_ in WALLS:
        line(d, [mv.p(x1_, z1_), mv.p(x2_, z2_)], WALL, 5)
    # door
    line(d, [mv.p(0, -0.75), mv.p(0.9, 0.3)], (150, 90, 50), 3)
    # trapdoor
    tx, ty = mv.p(*TRAPDOOR)
    rect(d, (tx - 0.9 * mv.s, ty - 0.9 * mv.s, tx + 0.9 * mv.s, ty + 0.9 * mv.s), fill=(90, 55, 30), outline=(140, 90, 50), width=1)
    for name, (x, z) in POSSESSABLES.items():
        c = mv.p(x, z)
        rect(d, (c[0] - 0.6 * mv.s, c[1] - 0.6 * mv.s, c[0] + 0.6 * mv.s, c[1] + 0.6 * mv.s), fill=(120, 60, 60), radius=2)
    for lx, lz in LAMPS:
        circle(d, mv.p(lx, lz), 0.35 * mv.s, fill=(255, 200, 120))
    sx, sy = mv.p(*TRAP_SITE)
    circle(d, (sx, sy), 1.25 * mv.s, outline=(80, 200, 120, 160), width=2)
    for name, ((x, z), col) in SUSPECTS.items():
        circle(d, mv.p(x, z), 0.55 * mv.s, fill=col, outline=(0, 0, 0), width=1)
    if labels:
        small = 11
        for name, (x, z) in POSSESSABLES.items():
            c = mv.p(x, z)
            text(d, (c[0], c[1] + 0.9 * mv.s), name, small, MUTED, "Medium", "mt")
        for name, ((x, z), col) in SUSPECTS.items():
            c = mv.p(x, z)
            text(d, (c[0], c[1] - 0.9 * mv.s), name, small, col, "Bold", "mb")
        for i, (x, z) in enumerate(CLUE_SPOTS):
            c = mv.p(x, z)
            poly(d, [(c[0], c[1] - 5), (c[0] + 5, c[1]), (c[0], c[1] + 5), (c[0] - 5, c[1])], fill=CLUE)
        for x, z in PIECES:
            c = mv.p(x, z)
            rect(d, (c[0] - 4, c[1] - 4, c[0] + 4, c[1] + 4), fill=ORANGE)
        for x, z in SOLVER_SPAWNS:
            circle(d, mv.p(x, z), 4, fill=GREEN)
        circle(d, mv.p(*HAUNTER_SPAWN), 6, fill=GHOST + (160,))
        text(d, (sx, sy + 1.6 * mv.s), "Trap site", small, GREEN, "Bold", "mt")
        text(d, (tx, ty + 1.2 * mv.s), "Trapdoor", small, (220, 150, 90), "Bold", "mt")
        text(d, (cx, cy), "Cellar", small, MUTED, "Bold", "mm")
        text(d, mv.p(0.6, -1.6), "Door", small, (220, 150, 90), "Bold", "lt")
        text(d, mv.p(-14, 14.2), "WEST WING", 12, MUTED, "Bold", "lt")
        text(d, mv.p(1, 14.2), "EAST WING", 12, MUTED, "Bold", "lt")
        text(d, mv.p(4, -4.6), "STUDY", 12, MUTED, "Bold", "lt")


def make_map():
    img, d = canvas(760, 560)
    mv = MapView(20, 20, 520)
    draw_house(d, mv, labels=True)
    text(d, (560, 24), "Blackwood Manor", 22)
    text(d, (560, 52), "test room, top-down", 13, MUTED, "Medium")
    legend = [
        (GREEN, "circle", "Solver spawns"), (GHOST, "circle", "Haunter spawn"), (CLUE, "diamond", "Clue hiding spots (random each match)"),
        (ORANGE, "square", "Trap pieces (appear in Trap phase)"), ((120, 60, 60), "square", "Possessable furniture"),
        ((255, 200, 120), "circle", "Lamps (flicker, cut power)"), ((90, 55, 30), "square", "Trapdoor -> drops you in the cellar"),
        ((80, 200, 120), "ring", "Trap site: build here"),
    ]
    y = 90
    for col, shape, label in legend:
        c = (572, y + 7)
        if shape == "circle":
            circle(d, c, 6, fill=col)
        elif shape == "ring":
            circle(d, c, 6, outline=col, width=2)
        elif shape == "diamond":
            poly(d, [(c[0], c[1] - 6), (c[0] + 6, c[1]), (c[0], c[1] + 6), (c[0] - 6, c[1])], fill=col)
        else:
            rect(d, (c[0] - 6, c[1] - 6, c[0] + 6, c[1] + 6), fill=col)
        lines = wrap(label, 24)
        for j, ln in enumerate(lines):
            text(d, (586, y + j * 15), ln, 12, INK, "Medium")
        y += 18 + 15 * (len(lines) - 1) + 8
    text(d, (560, 470), "Suspects", 14)
    yy = 492
    for name, ((x, z), col) in SUSPECTS.items():
        circle(d, (570, yy + 6), 5, fill=col)
        text(d, (582, yy), name, 12, INK, "Medium")
        yy += 16
    save_png(finish(img), "testroom-map.png")


def wrap(s, n):
    words, out, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------------------
# match-demo.gif: a whole match in 16 seconds
# ---------------------------------------------------------------------------
class Track:
    """Keyframed position/value track: list of (time, value...)."""

    def __init__(self, keys):
        self.keys = keys

    def at(self, t):
        k = self.keys
        if t <= k[0][0]:
            return k[0][1:]
        for a, b in zip(k, k[1:]):
            if a[0] <= t <= b[0]:
                u = ease((t - a[0]) / max(1e-6, b[0] - a[0]))
                return tuple(lerp(x, y, u) for x, y in zip(a[1:], b[1:]))
        return k[-1][1:]


SOLVERS = [
    ("Sleuth", GREEN, Track([(0, -6, -12), (1.5, -9, -9), (2.6, -10, -8.4), (3.2, -10, -6), (5, -8.5, 1.5), (7.2, -7.6, 2.6), (8, -7, 1), (9.6, -11.6, 0.4), (10.6, -7, 0.4), (12.4, -6.6, -0.6), (16, -6.6, -0.6)])),
    ("Techie", BLUE, Track([(0, -4.5, -12), (2, -6, -2), (4.6, -7.2, 5.6), (5.6, -7.2, 5.6), (6.3, -10, 1), (7.4, -13, -5), (9, -13, -6), (11, -8, -2.5), (16, -8, -2.5)])),
    ("Brawn", ORANGE, Track([(0, -3, -12), (1.8, -0.6, -5), (2.6, 0, 0), (4, 5, 3), (6.5, 6, 2.2), (8.6, 5.4, 2.6), (9.6, 11.5, 5.8), (11.6, 1.6, 0), (12.6, -5, 0.8), (16, -5, 0.8)])),
    ("Snacker", YELLOW, Track([(0, -1.5, -12), (2, -2.5, -2), (3.6, -3, 8.6), (5.5, -3, 8.6), (7, -2, 11.5), (9.8, -2, 12), (11.2, -4, 5), (12.6, -3, 2.5), (13.4, -8.6, 0.6), (14, -9.6, 0.2), (16, -9.6, 0.2)])),
]
GHOST_TRACK = Track([(0, 10, 0), (1.5, 4, 0.3), (2.5, 0, 0), (3.6, -6, 3), (4.3, -8, 4), (6.2, -8, 4), (7, -4, 6), (9, 3, 8)])
COSTUME_TRACK = Track([(9.2, 3, 8), (10.4, -1, 6), (11.5, -1.5, 4.5), (12.6, -3.3, 3), (13.4, -5.4, 1.2), (13.8, -6, 0.1), (16, -6, 0.1)])
FEAR = [
    Track([(0, 5), (12, 10), (16, 10)]),
    Track([(0, 5), (4.6, 20), (5.6, 100), (8.5, 100), (9.5, 35), (16, 30)]),
    Track([(0, 5), (6.5, 15), (8.8, 55), (10, 40), (16, 30)]),
    Track([(0, 5), (11, 10), (13.5, 80), (14.2, 40), (16, 30)]),
]
PANIC_WINDOW = (5.6, 8.5)
FOUND_CLUES = [(3.0, "Fresh rose petals", "Gardening: Groundskeeper, Cook"), (7.4, "Muddy boot print", "Muddy boots: Groundskeeper")]
SEEDED_CLUE = (-10, -8.4)
LEAKED_CLUE = (-7.6, 3)
EVENTS = [
    (0.0, 2.2, "Night falls. Find clues before dawn."),
    (3.0, 4.4, "Clue found: Fresh rose petals"),
    (3.7, 5.2, "Snacker interviews the Heiress"),
    (4.4, 5.4, "Haunter possesses the armchair..."),
    (5.4, 6.8, "The armchair launches! Techie PANICS"),
    (6.3, 7.4, "The Haunter rolls fog over the Brawn"),
    (7.4, 8.8, "Clue found: Muddy boot print (leaked!)"),
    (8.8, 10.0, "Accusation: the Groundskeeper... CORRECT!"),
    (10.0, 12.6, "TRAP: gather 3 pieces, build the trap"),
    (12.6, 13.6, "Trap armed. Lure the Haunter in!"),
    (13.8, 16, "UNMASKED! It was Gus Thornbury!"),
]


def phase_at(t):
    if t < 9:
        return "INVESTIGATION", BLUE
    if t < 13.8:
        return "TRAP", ORANGE
    return "UNMASKED", GREEN


def make_match_demo():
    W, H, MAP = 760, 540, 500
    fps = 12
    frames = []
    total = 16.0
    random.seed(3)
    for f in range(int(total * fps)):
        t = f / fps
        img, d = canvas(W, H)
        mv = MapView(20, 20, MAP)
        lamp_flicker = not (5.0 < t < 6.2 and random.random() < 0.5)
        draw_house(d, mv, lamps_on=lamp_flicker)

        # clues on the floor
        if t < 3.0:
            c = mv.p(*SEEDED_CLUE)
            circle(d, c, 6 + 2 * math.sin(t * 6), fill=CLUE + (90,))
            circle(d, c, 4, fill=CLUE)
        if 6.1 < t < 7.4:
            c = mv.p(*LEAKED_CLUE)
            circle(d, c, 7 + 2 * math.sin(t * 8), fill=CLUE + (90,))
            circle(d, c, 4, fill=CLUE)

        # fog
        if 6.3 < t < 9.6:
            a = min(1, (t - 6.3) / 0.6, (9.6 - t) / 0.6)
            fx, fy = mv.p(6, 2.6)
            for i in range(6):
                ang = t * 0.6 + i
                circle(d, (fx + math.cos(ang) * 14, fy + math.sin(ang) * 10), 3.2 * mv.s, fill=(190, 200, 215, int(40 * a)))

        # trap phase: pieces and site
        site = mv.p(*TRAP_SITE)
        pieces_delivered = sum(1 for tt in (10.6, 11.6, 12.4) if t >= tt)
        if 9.0 <= t:
            for i, (x, z) in enumerate(PIECES[:3]):
                pickup = [9.6, 9.6, 9.8][i]
                if t < pickup:
                    c = mv.p(*[(-12, 0), (12, 6), (-2, 12)][i])
                    rect(d, (c[0] - 5, c[1] - 5, c[0] + 5, c[1] + 5), fill=ORANGE)
            if pieces_delivered:
                for i in range(pieces_delivered):
                    rect(d, (site[0] - 12 + i * 9, site[1] - 4, site[0] - 5 + i * 9, site[1] + 3), fill=ORANGE)
        if t >= 12.6:
            pulse = 1.25 + 0.15 * math.sin(t * 10)
            circle(d, site, pulse * mv.s, outline=(80, 255, 130), width=3)
        if t >= 13.8:
            cage = min(1, (t - 13.8) / 0.3)
            r = 1.4 * mv.s
            rect(d, (site[0] - r, site[1] - r, site[0] + r, site[1] + r), outline=(80, 255, 130), width=3)
            for i in range(-2, 3):
                line(d, [(site[0] + i * r / 2.5, site[1] - r), (site[0] + i * r / 2.5, site[1] - r + 2 * r * cage)], (80, 255, 130, 200), 2)

        # possessed armchair shake + launch
        if 4.3 < t < 6.2:
            ax, ay = mv.p(*POSSESSABLES["Armchair"])
            j = 2 if t < 5.4 else 0
            launch = max(0, min(1, (t - 5.4) / 0.4))
            tx, ty = mv.p(-7.2, 5.6)
            px, py = lerp(ax, tx, launch * 0.8), lerp(ay, ty, launch * 0.8)
            rect(d, (px - 7 + random.uniform(-j, j), py - 7 + random.uniform(-j, j), px + 7, py + 7), fill=(170, 70, 70), outline=GHOST, width=2)
            if 5.4 < t < 6.0:
                circle(d, (tx, ty), (t - 5.4) * 70, outline=(255, 90, 90, int(255 * (6.0 - t) / 0.6)), width=3)

        # ghost (only the Haunter sees it in game; shown here translucent)
        if t < 9:
            gx, gz = GHOST_TRACK.at(t)
            g = mv.p(gx, gz)
            visible = not (4.3 < t < 6.2)
            if visible:
                bob = math.sin(t * 5) * 2
                circle(d, (g[0], g[1] + bob), 9, fill=GHOST + (90,))
                circle(d, (g[0], g[1] + bob), 5, fill=GHOST + (170,))

        # costume Haunter in trap phase
        if 9.2 <= t:
            cx, cz = COSTUME_TRACK.at(t)
            c = mv.p(cx, cz)
            circle(d, c, 9, fill=PURPLE, outline=(20, 0, 30), width=2)
            if t < 14.2:
                rect(d, (c[0] - 4, c[1] - 5, c[0] + 4, c[1] + 2), fill=(240, 240, 225))
            else:  # mask flies off
                u = min(1, (t - 14.2) / 0.8)
                mx, my = c[0] + 40 * u, c[1] - 60 * u + 60 * u * u
                rect(d, (mx - 4, my - 5, mx + 4, my + 2), fill=(240, 240, 225))
                circle(d, (c[0], c[1] - 1), 5, fill=SUSPECTS["Groundskeeper"][1])

        # solvers with flashlight cones
        for i, (name, col, track) in enumerate(SOLVERS):
            x, z = track.at(t)
            px, pz = track.at(max(0, t - 0.15))
            p = mv.p(x, z)
            heading = math.atan2(-(z - pz), x - px) if abs(x - px) + abs(z - pz) > 0.01 else -math.pi / 2
            panicked = i == 1 and PANIC_WINDOW[0] <= t <= PANIC_WINDOW[1]
            if not panicked and t < 14.5:
                spread = 0.45
                cone = [p] + [(p[0] + math.cos(heading + a) * 70, p[1] + math.sin(heading + a) * 70) for a in (-spread, 0, spread)]
                poly(d, cone, fill=(255, 245, 200, 38))
            jit = (random.uniform(-2, 2), random.uniform(-2, 2)) if panicked else (0, 0)
            circle(d, (p[0] + jit[0], p[1] + jit[1]), 8, fill=RED if panicked else col, outline=(0, 0, 0), width=2)
            if panicked:
                text(d, (p[0], p[1] - 12), "AAAH!", 11, RED, "Black", "mb")
            if i == 3 and 3.7 < t < 5.2:
                rect(d, (p[0] + 8, p[1] - 30, p[0] + 92, p[1] - 12), fill=(255, 255, 255, 230), radius=6)
                text(d, (p[0] + 50, p[1] - 21), "Where were you?", 10, (30, 20, 40), "Bold", "mm")

        # ---- side panel ----
        px0 = MAP + 40
        rect(d, (px0, 20, W - 16, H - 20), fill=PANEL, radius=10)
        ph, phc = phase_at(t)
        text(d, (px0 + 14, 34), ph, 18, phc, "Black")
        remaining = max(0, 900 - t * 52)
        if t < 9:
            text(d, (px0 + 14, 58), f"Dawn in {int(remaining) // 60}:{int(remaining) % 60:02d}", 13, MUTED, "Medium")
        elif t < 13.8:
            text(d, (px0 + 14, 58), f"Pieces {min(3, pieces_delivered)}/3  {'ARMED' if t >= 12.6 else 'building'}", 13, MUTED, "Medium")
        else:
            text(d, (px0 + 14, 58), "Solvers win!", 13, GREEN, "Bold")

        text(d, (px0 + 14, 88), "FEAR", 12, MUTED)
        for i, (name, col, _) in enumerate(SOLVERS):
            y = 108 + i * 30
            fear = FEAR[i].at(t)[0]
            panicked = i == 1 and PANIC_WINDOW[0] <= t <= PANIC_WINDOW[1]
            text(d, (px0 + 14, y), name, 12, col)
            rect(d, (px0 + 80, y + 2, W - 30, y + 14), fill=(50, 44, 70), radius=4)
            bw = (W - 30 - px0 - 80) * fear / 100
            bar = RED if fear > 80 else (ORANGE if fear > 50 else col)
            if panicked and int(t * 8) % 2:
                bar = (255, 255, 255)
            rect(d, (px0 + 80, y + 2, px0 + 80 + bw, y + 14), fill=bar, radius=4)

        text(d, (px0 + 14, 236), "CLUES", 12, MUTED)
        y = 256
        found = [c for c in FOUND_CLUES if t >= c[0]]
        if not found:
            text(d, (px0 + 14, y), "none yet", 12, MUTED, "Medium")
        for when, name, desc in found:
            poly(d, [(px0 + 18, y + 2), (px0 + 23, y + 7), (px0 + 18, y + 12), (px0 + 13, y + 7)], fill=CLUE)
            text(d, (px0 + 30, y), name, 12, INK)
            text(d, (px0 + 30, y + 16), desc, 10, MUTED, "Medium")
            y += 38

        text(d, (px0 + 14, 350), "SUSPECTS", 12, MUTED)
        for i, (name, ((_, _), col)) in enumerate(SUSPECTS.items()):
            y = 370 + i * 20
            circle(d, (px0 + 20, y + 7), 5, fill=col)
            cleared = (name in ("Heiress", "Rival") and t >= 7.6) or (name == "Cook" and t >= 7.6)
            accused = name == "Groundskeeper" and t >= 8.8
            label = name + ("  <- culprit" if accused else "")
            text(d, (px0 + 32, y), label, 12, RED if accused else (MUTED if cleared else INK), "Bold" if accused else "Medium")
            if cleared:
                line(d, [(px0 + 32, y + 8), (px0 + 32 + 7 * len(name), y + 8)], MUTED, 1)

        # event caption
        for a, b, msg in EVENTS:
            if a <= t < b:
                alpha = int(255 * min(1, (t - a) / 0.25, (b - t) / 0.25))
                rect(d, (20, H - 64, MAP + 20, H - 26), fill=(0, 0, 0, int(alpha * 0.7)), radius=8)
                text(d, (20 + MAP / 2, H - 45), msg, 15, (255, 255, 255, alpha), "Bold", "mm")
        if t >= 13.8:
            s = min(1, (t - 13.8) / 0.4)
            text(d, (20 + MAP / 2, 130), "UNMASKED!", int(28 + 20 * s), (255, 240, 120), "Black", "mm")

        text(d, (px0 + 14, H - 52), "Illustration of a match.", 10, MUTED, "Medium")
        text(d, (px0 + 14, H - 38), "Not an in-game capture.", 10, MUTED, "Medium")
        frame = finish(img)
        frames.append(frame)
    frames += [frames[-1]] * 12  # hold the ending
    save_gif(frames, "testroom-match.gif", int(1000 / fps))


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
def make_banner():
    W, H = 900, 300
    frames = []
    random.seed(7)
    stars = [(random.uniform(0, W), random.uniform(0, H * 0.6), random.uniform(0.5, 1.6)) for _ in range(90)]
    windows = [(x, y) for x in range(610, 860, 40) for y in (150, 195)]
    n = 36
    for f in range(n):
        t = f / n
        img, d = canvas(W, H, (10, 8, 24))
        for i in range(H):  # sky gradient
            c = (int(10 + 20 * i / H), int(8 + 10 * i / H), int(24 + 40 * i / H))
            line(d, [(0, i), (W, i)], c, 1)
        for sx, sy, r in stars:
            tw = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 2 + sx)
            circle(d, (sx, sy), r, fill=(255, 255, 255, int(120 + 120 * tw)))
        circle(d, (780, 70), 46, fill=(250, 245, 215))
        circle(d, (760, 60), 46, fill=(255, 250, 230, 40))
        # manor silhouette
        sil = (6, 4, 14)
        rect(d, (580, 120, 880, 300), fill=sil)
        poly(d, [(570, 122), (730, 50), (890, 122)], fill=sil)
        rect(d, (650, 40, 680, 100), fill=sil)
        rect(d, (760, 90, 800, 130), fill=sil)
        poly(d, [(750, 92), (780, 60), (810, 92)], fill=sil)
        for i, (wx, wy) in enumerate(windows):
            on = (i * 7 + f // 4) % 5 != 0
            col = (255, 200, 90) if on else (40, 30, 30)
            rect(d, (wx, wy, wx + 18, wy + 26), fill=col)
        rect(d, (0, 270, W, H), fill=(4, 3, 10))
        # floating ghost
        gx = 515 + 12 * math.sin(t * 2 * math.pi)
        gy = 200 + 12 * math.sin(t * 4 * math.pi)
        circle(d, (gx, gy), 34, fill=GHOST + (60,))
        circle(d, (gx, gy - 6), 24, fill=(235, 250, 255, 220))
        rect(d, (gx - 24, gy - 6, gx + 24, gy + 26), fill=(235, 250, 255, 220))
        for k in range(4):
            wob = 4 * math.sin(t * 8 * math.pi + k)
            circle(d, (gx - 18 + k * 12, gy + 26 + wob), 6, fill=(235, 250, 255, 220))
        circle(d, (gx - 8, gy - 8), 4, fill=(20, 20, 30))
        circle(d, (gx + 8, gy - 8), 4, fill=(20, 20, 30))
        circle(d, (gx, gy + 6), 5, fill=(20, 20, 30))
        text(d, (40, 70), "UNMASKED", 78, (255, 238, 140), "Black")
        text(d, (44, 170), "A meddling-kids mystery. Find the clues,", 20, INK, "SemiBold")
        text(d, (44, 198), "catch the Haunter, pull off the mask.", 20, INK, "SemiBold")
        text(d, (44, 236), "2-4 Solvers  vs  1 Haunter  ·  Unity 6  ·  online co-op", 14, MUTED, "Medium")
        frames.append(finish(img))
    save_gif(frames, "banner.gif", 90)


# ---------------------------------------------------------------------------
# Fear meter
# ---------------------------------------------------------------------------
def make_fear():
    W, H = 640, 200
    beats = Track([(0, 5), (0.8, 5), (1.0, 25), (1.8, 22), (2.0, 45), (2.8, 42), (3.0, 75), (3.6, 72), (3.8, 100), (6.0, 100), (6.4, 35), (8, 20)])
    frames = []
    fps = 12
    labels = [(1.0, "Door slams! +15"), (2.0, "Phantom! +25"), (3.0, "Armchair! +30"), (3.8, "PANIC! You run screaming"), (6.0, "A friend calms you down (E)"), (6.6, "Friends nearby: fear fades faster")]
    for f in range(int(8 * fps)):
        t = f / fps
        img, d = canvas(W, H, PANEL)
        fear = beats.at(t)[0]
        panicked = 3.8 <= t < 6.0
        text(d, (24, 18), "FEAR METER", 16, MUTED)
        rect(d, (24, 50, W - 24, 86), fill=(50, 44, 70), radius=10)
        col = RED if fear > 80 else (ORANGE if fear > 50 else GREEN)
        if panicked and int(t * 8) % 2:
            col = (255, 255, 255)
        rect(d, (24, 50, 24 + (W - 48) * fear / 100, 86), fill=col, radius=10)
        text(d, (W - 30, 68), f"{fear:.0f}%", 16, INK, "Bold", "rm")
        # little solver
        cx = 80 + (300 if panicked else 0) * min(1, (t - 3.8) / 2.2 if panicked else 0)
        cy = 140 + (math.sin(t * 30) * 4 if panicked else 0)
        circle(d, (cx, cy), 18, fill=RED if panicked else GREEN, outline=(0, 0, 0), width=2)
        circle(d, (cx - 6, cy - 5), 4, fill=(255, 255, 255))
        circle(d, (cx + 6, cy - 5), 4, fill=(255, 255, 255))
        circle(d, (cx, cy + 7), 5 if fear > 50 else 2, fill=(20, 10, 10))
        msg = ""
        for a, m in labels:
            if t >= a:
                msg = m
        text(d, (200, 140), msg, 18, RED if panicked else INK, "Bold", "lm")
        frames.append(finish(img))
    save_gif(frames, "fear-meter.gif", int(1000 / fps))


# ---------------------------------------------------------------------------
# Unmasking
# ---------------------------------------------------------------------------
def make_unmask():
    W, H = 420, 320
    frames = []
    fps = 12
    for f in range(int(4 * fps)):
        t = f / fps
        img, d = canvas(W, H, (12, 10, 24))
        # cage glow
        for r in range(5):
            circle(d, (W / 2, 250), 120 - r * 10, fill=(80, 255, 130, 8))
        cx, cy = W / 2, 170
        # cloak
        poly(d, [(cx - 70, 300), (cx - 40, cy - 10), (cx + 40, cy - 10), (cx + 70, 300)], fill=PURPLE)
        # face beneath
        circle(d, (cx, cy - 40), 42, fill=(225, 190, 160))
        rect(d, (cx - 46, cy - 92, cx + 46, cy - 70), fill=(110, 150, 70), radius=6)  # groundskeeper cap
        circle(d, (cx - 14, cy - 44), 4, fill=(30, 20, 20))
        circle(d, (cx + 14, cy - 44), 4, fill=(30, 20, 20))
        line(d, [(cx - 16, cy - 20), (cx + 16, cy - 22)], (90, 40, 40), 3)
        # mask
        u = max(0, min(1, (t - 1.2) / 1.0))
        shake = (random.uniform(-3, 3) if t < 1.2 else 0)
        mx = cx + 120 * u + shake
        my = cy - 40 - 160 * u + 140 * u * u
        ang = 540 * u
        mask = Image.new("RGBA", (110 * SS, 120 * SS), (0, 0, 0, 0))
        md = ImageDraw.Draw(mask)
        md.ellipse([5 * SS, 5 * SS, 105 * SS, 115 * SS], fill=(245, 245, 230))
        md.ellipse([25 * SS, 35 * SS, 45 * SS, 55 * SS], fill=(10, 10, 10))
        md.ellipse([65 * SS, 35 * SS, 85 * SS, 55 * SS], fill=(10, 10, 10))
        md.polygon([(35 * SS, 85 * SS), (55 * SS, 75 * SS), (75 * SS, 85 * SS), (55 * SS, 100 * SS)], fill=(10, 10, 10))
        mask = mask.rotate(ang, expand=True, resample=Image.BICUBIC)
        img.paste(mask, (int(mx * SS - mask.width / 2), int(my * SS - mask.height / 2)), mask)
        d = ImageDraw.Draw(img, "RGBA")
        if t > 2.2:
            a = int(255 * min(1, (t - 2.2) / 0.4))
            text(d, (W / 2, 28), "It was Gus Thornbury,", 20, (255, 240, 140, a), "Black", "mm")
            text(d, (W / 2, 54), "the groundskeeper!", 20, (255, 240, 140, a), "Black", "mm")
        if t > 3.0:
            a = int(255 * min(1, (t - 3.0) / 0.4))
            text(d, (W / 2, 300), "\"...if it weren't for you meddling kids!\"", 13, (220, 220, 240, a), "Medium", "mm")
        frames.append(finish(img))
    frames += [frames[-1]] * 14
    save_gif(frames, "unmask.gif", int(1000 / fps))


# ---------------------------------------------------------------------------
# Haunter power cards
# ---------------------------------------------------------------------------
POWERS = [  # name, key, cost, cooldown, fear, leak, colour, blurb
    ("Slam Doors", "1", 15, 12, 15, 10, (200, 120, 70), "Doors nearby slam and jam"),
    ("Fog", "2", 20, 25, 3, 10, (170, 190, 210), "Fear creeps up inside it"),
    ("Trapdoor", "3", 25, 20, 30, 15, (150, 90, 50), "Drops a Solver to the cellar"),
    ("Phantom", "4", 25, 20, 25, 0, (230, 240, 255), "Fake ghost; flashlights pop it"),
    ("Costume Chase", "5", 40, 60, 35, 20, PURPLE, "Go physical and hunt them"),
    ("Villain power", "6", 30, 25, 30, 15, ORANGE, "Pumpkin toss, wail, wisps or hex (6 or Q)"),
]


def power_icon(d, kind, c):
    x, y = c
    if kind == 0:
        rect(d, (x - 16, y - 24, x + 16, y + 24), fill=(150, 90, 50), radius=3)
        circle(d, (x + 9, y), 3, fill=YELLOW)
        for i in range(3):
            line(d, [(x + 22 + i * 6, y - 16 + i * 4), (x + 30 + i * 6, y - 20 + i * 4)], INK, 2)
    elif kind == 1:
        for i in range(5):
            circle(d, (x - 20 + i * 10, y + math.sin(i) * 6), 14, fill=(200, 210, 225, 120))
    elif kind == 2:
        rect(d, (x - 24, y - 6, x + 24, y + 22), fill=(10, 8, 12))
        line(d, [(x - 24, y - 6), (x - 10, y - 26)], (150, 90, 50), 6)
        circle(d, (x + 4, y + 6), 6, fill=GREEN)
    elif kind == 3:
        circle(d, (x, y - 6), 18, fill=(240, 245, 255))
        rect(d, (x - 18, y - 6, x + 18, y + 18), fill=(240, 245, 255))
        circle(d, (x - 6, y - 8), 3, fill=(0, 0, 0))
        circle(d, (x + 6, y - 8), 3, fill=(0, 0, 0))
    elif kind == 5:
        # a carved jack-o'-lantern
        for dx, col in ((-12, (185, 82, 15)), (12, (185, 82, 15)), (0, (232, 115, 28))):
            circle(d, (x + dx, y + 2), 20, fill=col)
        rect(d, (x - 3, y - 28, x + 3, y - 16), fill=(79, 90, 34))
        poly(d, [(x - 14, y - 4), (x - 6, y - 12), (x - 2, y - 2)], fill=(255, 207, 74))
        poly(d, [(x + 14, y - 4), (x + 6, y - 12), (x + 2, y - 2)], fill=(255, 207, 74))
        poly(d, [(x - 16, y + 6), (x + 16, y + 6), (x + 8, y + 14), (x - 8, y + 14)], fill=(255, 207, 74))
    else:
        poly(d, [(x - 20, y + 26), (x - 10, y - 10), (x + 10, y - 10), (x + 20, y + 26)], fill=PURPLE)
        circle(d, (x, y - 16), 12, fill=(245, 245, 230))
        circle(d, (x - 4, y - 18), 2, fill=(0, 0, 0))
        circle(d, (x + 4, y - 18), 2, fill=(0, 0, 0))


def make_powers():
    cw, chh, gap = 168, 250, 12
    W = len(POWERS) * cw + (len(POWERS) + 1) * gap
    H = chh + 2 * gap + 40
    img, d = canvas(W, H)
    text(d, (gap, 12), "Haunter powers (keys 1-6). Every use costs Ectoplasm and may leak a real clue.", 14, INK, "SemiBold")
    for i, (name, key, cost, cd, fear, leak, col, blurb) in enumerate(POWERS):
        x = gap + i * (cw + gap)
        y = 44
        rect(d, (x, y, x + cw, y + chh), fill=PANEL, outline=col, width=2, radius=12)
        rect(d, (x + 10, y + 10, x + 34, y + 34), fill=col, radius=6)
        text(d, (x + 22, y + 22), key, 14, (20, 15, 30), "Black", "mm")
        text(d, (x + 42, y + 14), name, 14, INK)
        power_icon(d, i, (x + cw / 2, y + 82))
        for j, ln in enumerate(wrap(blurb, 22)):
            text(d, (x + cw / 2, y + 124 + j * 15), ln, 11, MUTED, "Medium", "mt")
        stats = [("Cost", cost, 40, (120, 220, 255)), ("Cooldown", cd, 60, YELLOW), ("Fear", fear, 35, RED), ("Leak %", leak, 20, ORANGE)]
        for k, (label, v, mx, sc) in enumerate(stats):
            yy = y + 166 + k * 20
            text(d, (x + 12, yy), label, 10, MUTED, "Medium")
            rect(d, (x + 72, yy + 2, x + cw - 30, yy + 11), fill=(50, 44, 70), radius=3)
            rect(d, (x + 72, yy + 2, x + 72 + (cw - 102) * v / mx, yy + 11), fill=sc, radius=3)
            text(d, (x + cw - 10, yy), str(v), 10, INK, "Bold", "ra")
    save_png(finish(img), "powers.png")


# ---------------------------------------------------------------------------
# Who knows what (network secrecy)
# ---------------------------------------------------------------------------
def make_secrets():
    W, H = 860, 400
    img, d = canvas(W, H)
    text(d, (W / 2, 24), "Who knows what? The server keeps the secrets.", 20, INK, "Black", "mm")
    boxes = [
        (30, "SERVER (host)", (120, 220, 255), ["Who the Haunter really is", "Every clue: real or planted", "Where clues are hidden", "The Haunter's position", "Ectoplasm, cooldowns, fear"]),
        (310, "SOLVER'S PC", GREEN, ["Clues only once found", "Suspects, interviews, board", "Possessed objects tremble", "Haunter only while in costume", "Never: identity, fake flags"]),
        (590, "HAUNTER'S PC", PURPLE, ["Their own secret identity", "Their ghost (others can't)", "Their Ectoplasm, cooldowns", "When they leaked a clue", "Never: what an unfound clue says"]),
    ]
    for x, title_, col, items in boxes:
        rect(d, (x, 60, x + 240, 340), fill=PANEL, outline=col, width=2, radius=12)
        text(d, (x + 120, 84), title_, 15, col, "Black", "mm")
        for i, it in enumerate(items):
            never = it.startswith("Never")
            mark = "x" if never else "+"
            circle(d, (x + 22, 122 + i * 40), 9, fill=RED if never else col)
            text(d, (x + 22, 122 + i * 40), mark, 11, (20, 15, 30), "Black", "mm")
            for j, ln in enumerate(wrap(it, 26)):
                text(d, (x + 38, 114 + i * 40 + j * 14), ln, 12, INK, "Medium")
    text(d, (W / 2, 368), "Clients ask (RPC). The server checks range, line of sight, phase, cost and cooldown, then decides.", 13, MUTED, "Medium", "mm")
    save_png(finish(img), "secrets.png")


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------
def make_controls():
    W, H = 860, 330
    img, d = canvas(W, H)
    rows = [list("123456"), list("QWERTG"), list("ASDFM"), ["Ctrl", "Space", "Tab", "Esc", "F12"]]
    solver = {"W", "A", "S", "D", "E", "F", "Space", "Tab", "Esc", "F12", "M"}
    haunter = {"W", "A", "S", "D", "E", "Space", "Ctrl", "Tab", "1", "2", "3", "4", "5", "6", "Q", "G", "Esc", "F12", "M"}
    desc = {"W": "move", "A": "move", "S": "move", "D": "move", "E": "use, possess", "F": "flashlight", "G": "fake clue",
            "Space": "jump / rise", "Ctrl": "sink", "Tab": "Suspect Board", "Esc": "free mouse", "F12": "screenshot",
            "1": "slam", "2": "fog", "3": "trapdoor", "4": "phantom", "5": "costume", "6": "villain", "Q": "villain", "R": "", "T": "", "M": "town map"}
    text(d, (20, 16), "Controls", 20)
    circle(d, (150, 28), 7, fill=GREEN)
    text(d, (162, 20), "Solver", 13, INK, "Medium")
    circle(d, (230, 28), 7, fill=PURPLE)
    text(d, (242, 20), "Haunter", 13, INK, "Medium")
    circle(d, (322, 28), 7, fill=(120, 200, 220))
    text(d, (334, 20), "Both", 13, INK, "Medium")
    y = 56
    for r, row in enumerate(rows):
        x = 20 + r * 24
        for k in row:
            w = 72 if len(k) <= 1 else 104
            s, h = k in solver, k in haunter
            col = (120, 200, 220) if s and h else (GREEN if s else (PURPLE if h else (60, 54, 80)))
            rect(d, (x, y, x + w, y + 52), fill=(36, 32, 56), outline=col, width=2, radius=8)
            text(d, (x + 8, y + 6), k, 15, INK)
            dsc = desc.get(k, "")
            if dsc:
                text(d, (x + 8, y + 32), dsc, 10, col, "Medium")
            x += w + 8
        y += 60
    mx = 680
    rect(d, (mx, 60, mx + 140, 250), fill=(36, 32, 56), outline=(120, 200, 220), width=2, radius=60)
    line(d, [(mx + 70, 60), (mx + 70, 140)], (120, 200, 220), 2)
    line(d, [(mx, 140), (mx + 140, 140)], (120, 200, 220), 2)
    text(d, (mx + 35, 105), "LMB", 12, PURPLE, "Bold", "mm")
    text(d, (mx + 105, 105), "RMB", 12, PURPLE, "Bold", "mm")
    text(d, (mx + 70, 175), "look around", 11, (120, 200, 220), "Medium", "mm")
    text(d, (mx + 70, 195), "LMB/RMB: possessed", 10, PURPLE, "Medium", "mm")
    text(d, (mx + 70, 210), "object actions", 10, PURPLE, "Medium", "mm")
    text(d, (20, 300), "In the Mystery Club van:  W/S gas and reverse,  A/D steer,  Space brake,  E get in or out", 13, GREEN, "Medium")
    save_png(finish(img), "controls.png")


# ---------------------------------------------------------------------------
# Progress (from Docs/PROGRESS.md)
# ---------------------------------------------------------------------------
def make_progress():
    md = open(os.path.join(ROOT, "Docs", "PROGRESS.md"), encoding="utf-8").read()
    sections = re.findall(r"^## (.+?)\n((?:- \[[ x]\].*\n?)+)", md, re.M)
    W = 760
    H = 70 + 44 * len(sections)
    img, d = canvas(W, H)
    total_done = total_all = 0
    for i, (name, body) in enumerate(sections):
        items = re.findall(r"- \[([ x])\]", body)
        done = items.count("x")
        total_done += done
        total_all += len(items)
        y = 56 + i * 44
        text(d, (20, y + 4), name, 13, INK, "SemiBold")
        rect(d, (320, y + 4, W - 90, y + 22), fill=(50, 44, 70), radius=8)
        frac = done / len(items) if items else 0
        col = GREEN if frac == 1 else (YELLOW if frac >= 0.5 else ORANGE)
        if frac > 0:
            rect(d, (320, y + 4, 320 + (W - 410) * frac, y + 22), fill=col, radius=8)
        text(d, (W - 20, y + 13), f"{done}/{len(items)}", 13, INK, "Bold", "rm")
    text(d, (20, 16), f"Progress: {total_done}/{total_all} tasks", 18, INK, "Black")
    save_png(finish(img), "progress.png")


if __name__ == "__main__":
    print("Drawing README images into", OUT)
    jobs = {"banner": make_banner, "fear": make_fear, "unmask": make_unmask, "powers": make_powers,
            "secrets": make_secrets, "controls": make_controls, "progress": make_progress,
            # the old flat test room, kept for reference (not in the README any more)
            "testroom-map": make_map, "testroom-match": make_match_demo}
    wanted = sys.argv[1:] or [j for j in jobs if not j.startswith("testroom")] + ["3d", "town"]
    for name in wanted:
        if name == "3d":
            import make_images_3d  # the 3D manor renders (slower: a few minutes)
            for job in make_images_3d.JOBS.values():
                job()
        elif name == "town":
            import make_images_town  # Hollow Creek: map, house cards, sizes, the van drive, events
            for job in make_images_town.JOBS.values():
                job()
        else:
            jobs[name]()
