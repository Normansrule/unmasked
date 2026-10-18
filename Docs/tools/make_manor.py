#!/usr/bin/env python3
"""
Designs Blackwood Manor, the 3D level, and writes it to
Assets/Unmasked/Resources/BlackwoodManor.json.

That one file is the single source of truth for the level:
  - Unity reads it in Unmasked > Build Blackwood Manor (Editor/ManorBuilder.cs) and at runtime for
    room names (House/ManorLayout.cs).
  - Docs/tools/render3d.py reads it to draw the 3D pictures in the README.

Units are metres, y is up, +z is north. Positions are centres. Rotations are Unity Euler angles.
Sizes: for "box" the full size; for "cyl" and "capsule" Unity's localScale (so height = 2 * y).

    python3 Docs/tools/make_manor.py
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Assets", "Unmasked", "Resources", "BlackwoodManor.json")

# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------
X0, X1, Z0, Z1 = -16.0, 16.0, -12.0, 12.0  # manor footprint (outer wall centre lines)
STOREY = 3.5           # floor-to-floor height
SLAB = 0.3             # floor thickness
OUTER_T, INNER_T = 0.4, 0.2
CELLAR_Y = -3.5        # cellar floor
ROOF_BASE = 2 * STOREY + 0.2
RIDGE = 4.6            # roof height above ROOF_BASE
STEP_RISE, STEP_RUN = 0.25, 0.35
DOOR_H, WIN_LO, WIN_HI = 2.4, 1.0, 2.6


def rgb(h):
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4)]


C = {
    "outer": rgb("6f6a78"), "inner": rgb("8a7f73"), "upper_inner": rgb("7d6f86"), "cellar": rgb("4d4a47"),
    "floor": rgb("5a3e2b"), "upper_floor": rgb("6b4a35"), "cellar_floor": rgb("3a3633"), "tile": rgb("5e5c58"),
    "roof": rgb("2e2a3a"), "trim": rgb("3b2f2a"), "glass": rgb("ffcf7a"), "glass_dark": rgb("5a6b8c"),
    "grass": rgb("2f4a2a"), "gravel": rgb("7a756c"), "hedge": rgb("1f3d22"), "stone": rgb("8d8f94"),
    "wood": rgb("6b4426"), "dark_wood": rgb("3d2616"), "red": rgb("8a2a2a"), "rug": rgb("6e1f2f"),
    "brass": rgb("b08d3c"), "iron": rgb("26262b"), "white": rgb("dedbd2"), "water": rgb("3d6c8f"),
    "book1": rgb("7a2e2e"), "book2": rgb("2e4a7a"), "book3": rgb("3d6b3a"), "fire": rgb("ff8a2a"),
    "bark": rgb("3a2c22"), "plant": rgb("3f7a3a"), "copper": rgb("a5612f"), "sack": rgb("cdbf9b"),
}

L = {
    "name": "Blackwood Manor",
    "boxes": [], "doors": [], "trapdoors": [], "possessables": [], "lights": [], "suspects": [],
    "clueSpots": [], "trapPieces": [], "trapSite": None, "solverSpawns": [], "haunterSpawn": None, "rooms": [],
    "decor": [], "glows": [],
}

# Levels: -1 cellar, 0 ground, 1 upstairs, 2 roof, 9 grounds outside.


def box(name, p, s, color, level, mode="solid", tag="", shape="box", r=(0, 0, 0)):
    L["boxes"].append({"n": name, "t": shape, "p": [round(v, 3) for v in p], "s": [round(v, 3) for v in s],
                       "r": [round(v, 2) for v in r], "c": color, "m": mode, "l": level, "g": tag})


def pt(p):
    return {"p": [round(v, 3) for v in p]}


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------
def wall(name, axis, fixed, a0, a1, y0, h, level, color, thickness, openings=(), tag="wall"):
    """
    axis 'x': the wall runs along x at z=fixed. axis 'z': runs along z at x=fixed.
    openings: (centre, width, bottom, top, kind) with kind 'door' or 'window'.
    """
    ops = sorted(openings, key=lambda o: o[0])

    def put(n, a_lo, a_hi, b_lo, b_hi, col=color, mode="solid", t=thickness):
        if a_hi - a_lo < 0.01 or b_hi - b_lo < 0.01:
            return
        mid, length = (a_lo + a_hi) / 2, a_hi - a_lo
        y, hh = y0 + (b_lo + b_hi) / 2, b_hi - b_lo
        if axis == "x":
            box(n, (mid, y, fixed), (length, hh, t), col, level, mode, tag)
        else:
            box(n, (fixed, y, mid), (t, hh, length), col, level, mode, tag)

    cur = a0
    for i, (c, w, lo, hi, kind) in enumerate(ops):
        put(f"{name}_seg{i}", cur, c - w / 2, 0, h)
        put(f"{name}_below{i}", c - w / 2, c + w / 2, 0, lo)
        put(f"{name}_above{i}", c - w / 2, c + w / 2, hi, h)
        if kind == "window":
            put(f"{name}_glass{i}", c - w / 2, c + w / 2, lo, hi, C["glass"], "glass", 0.06)
            # window frame cross
            put(f"{name}_mullion{i}", c - 0.04, c + 0.04, lo, hi, C["trim"], "solid", thickness + 0.04)
        cur = c + w / 2
    put(f"{name}_seg_end", cur, a1, 0, h)


def slab(name, y_top, x0, x1, z0, z1, holes, color, level, thickness=SLAB, tag="floor"):
    """A floor rectangle with rectangular holes cut out of it."""
    xs = sorted({x0, x1, *[v for h in holes for v in (h[0], h[1]) if x0 < v < x1]})
    zs = sorted({z0, z1, *[v for h in holes for v in (h[2], h[3]) if z0 < v < z1]})
    cells = []
    for i in range(len(xs) - 1):
        col = []
        for j in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            inside = any(h[0] < cx < h[1] and h[2] < cz < h[3] for h in holes)
            col.append(not inside)
        cells.append(col)
    n = 0
    for i in range(len(xs) - 1):
        j = 0
        while j < len(zs) - 1:
            if not cells[i][j]:
                j += 1
                continue
            k = j
            while k + 1 < len(zs) - 1 and cells[i][k + 1]:
                k += 1
            box(f"{name}_{n}", ((xs[i] + xs[i + 1]) / 2, y_top - thickness / 2, (zs[j] + zs[k + 1]) / 2),
                (xs[i + 1] - xs[i], thickness, zs[k + 1] - zs[j]), color, level, "solid", tag)
            n += 1
            j = k + 1


def stairs(name, x0, x1, z_start, y_base, steps, direction, level, color, down=False):
    """Straight stairs running along z. Up: tops go y_base+rise..; down: start at y_base and descend."""
    for k in range(1, steps + 1):
        z_lo = z_start + (k - 1) * STEP_RUN * direction
        z_hi = z_lo + STEP_RUN * direction
        zc = (z_lo + z_hi) / 2
        if down:
            top = y_base - k * STEP_RISE
            bottom = y_base - steps * STEP_RISE
        else:
            top = y_base + k * STEP_RISE
            bottom = y_base
        box(f"{name}_step{k}", ((x0 + x1) / 2, (top + bottom) / 2, zc), (x1 - x0, top - bottom, STEP_RUN), color, level, "solid", "stairs")
    # banister on both sides
    length = steps * STEP_RUN
    zc = z_start + direction * length / 2
    rise = steps * STEP_RISE * (-1 if down else 1)
    ang = math.degrees(math.atan2(rise, length)) * direction
    yc = y_base + rise / 2 + 0.95
    for side, x in (("L", x0 - 0.05), ("R", x1 + 0.05)):
        box(f"{name}_rail{side}", (x, yc, zc), (0.08, 0.08, math.hypot(length, rise)), C["dark_wood"], level, "nocollide", "rail", r=(-ang, 0, 0))


def railing(name, a0, a1, axis, fixed, y, level):
    mid, length = (a0 + a1) / 2, a1 - a0
    if axis == "x":
        box(name, (mid, y + 0.5, fixed), (length, 1.0, 0.08), C["dark_wood"], level, "solid", "rail")
    else:
        box(name, (fixed, y + 0.5, mid), (0.08, 1.0, length), C["dark_wood"], level, "solid", "rail")


def room(name, level, x0, x1, z0, z1, y0, y1):
    L["rooms"].append({"n": name, "l": level, "min": [x0, y0, z0], "max": [x1, y1, z1]})


def possessable(name, shape, p, s, color, physics, level):
    L["possessables"].append({"n": name, "t": shape, "p": list(p), "s": list(s), "c": color, "phys": physics, "l": level})


def light(name, p, color, rng, intensity, level, fixture_shape="cyl", fixture_offset=(0, -0.4, 0), fixture_size=(0.25, 0.8, 0.25), fixture_color=None):
    L["lights"].append({"n": name, "p": list(p), "c": color, "range": rng, "intensity": intensity, "l": level,
                        "ft": fixture_shape, "fo": list(fixture_offset), "fs": list(fixture_size), "fc": fixture_color or C["brass"]})


def suspect(sid, p, color, ry=180):
    L["suspects"].append({"id": sid, "p": list(p), "c": color, "ry": ry})


def decor(kind, p, ry=0.0, sc=1.0, level=9):
    """A Halloween prop from Costumes.json (see make_costumes.py): jack, pumpkin, candle, cobweb..."""
    L["decor"].append({"k": kind, "p": [round(v, 3) for v in p], "ry": round(ry, 1), "sc": round(sc, 3), "l": level})


def glow(p, color, rng, intensity, level=9):
    """A plain point light that flickers (not possessable): lights the jack-o'-lantern trail and friends."""
    L["glows"].append({"p": [round(v, 3) for v in p], "c": color, "range": rng, "intensity": intensity, "l": level})


def facing(dx, dz):
    """The y rotation that makes a prop's face (+z) point along (dx, dz)."""
    return math.degrees(math.atan2(dx, dz))


def door(p, rot_y, width, level, name):
    L["doors"].append({"n": name, "p": list(p), "ry": rot_y, "w": width, "h": DOOR_H, "l": level})


# ---------------------------------------------------------------------------
# The manor
# ---------------------------------------------------------------------------
G0, G1 = 0.0, STOREY  # ground and upper floor levels

# Holes
STAIR_UP = (-3.2, -0.8, -6.0, -6.0 + 14 * STEP_RUN)       # foyer grand stairs, hole in upper floor
CELLAR_HOLE = (1.0, 3.0, 5.0, 5.0 + 14 * STEP_RUN)          # back hall stairs down, hole in ground floor

# --- Floors and ceilings ---
slab("CellarFloor", CELLAR_Y, -16, 12, -2, 12, [], C["cellar_floor"], -1)
slab("GroundFloor", G0, X0, X1, Z0, Z1, [CELLAR_HOLE], C["floor"], 0)
slab("UpperFloor", G1, X0, X1, Z0, Z1, [STAIR_UP], C["upper_floor"], 1)
slab("Ceiling", 2 * STOREY + 0.2, X0 - 0.2, X1 + 0.2, Z0 - 0.2, Z1 + 0.2, [], C["trim"], 2, 0.25, "ceiling")
# kitchen tiles and foyer rug on top of the floor
box("KitchenTiles", (10, 0.01, 7), (11.6, 0.02, 9.6), C["tile"], 0, "nocollide", "decor")
box("FoyerRug", (1.2, 0.01, -8.5), (3.2, 0.02, 6), C["rug"], 0, "nocollide", "decor")
box("UpperRug", (1.6, G1 + 0.01, 4), (2.4, 0.02, 12), C["rug"], 1, "nocollide", "decor")

# --- Cellar walls ---
wall("CellarW", "z", -16, -2, 12, CELLAR_Y, 3.5, -1, C["cellar"], OUTER_T)
wall("CellarE", "z", 12, -2, 12, CELLAR_Y, 3.5, -1, C["cellar"], OUTER_T)
wall("CellarS", "x", -2, -16, 12, CELLAR_Y, 3.5, -1, C["cellar"], OUTER_T)
wall("CellarN", "x", 12, -16, 12, CELLAR_Y, 3.5, -1, C["cellar"], OUTER_T)
wall("CellarPillarRow", "x", 5, -16, -4, CELLAR_Y, 3.5, -1, C["cellar"], 0.5, [(-12, 2.5, 0, 3.5, "door"), (-7, 2.5, 0, 3.5, "door")])
room("Cellar", -1, -16, 12, -2, 12, CELLAR_Y, 0)

# --- Ground floor outer walls ---
win = lambda c: (c, 1.4, WIN_LO, WIN_HI, "window")
wall("G_S", "x", Z0, X0 - 0.2, X1 + 0.2, G0, STOREY, 0, C["outer"], OUTER_T,
     [win(-12), win(-7.5), (0, 2.0, 0, 2.6, "door"), win(7.5), win(12)])
wall("G_N", "x", Z1, X0 - 0.2, X1 + 0.2, G0, STOREY, 0, C["outer"], OUTER_T,
     [win(-12), win(-7.5), win(0), win(7.5), (12.5, 1.4, 0, DOOR_H, "door")])
wall("G_W", "z", X0, Z0, Z1, G0, STOREY, 0, C["outer"], OUTER_T, [win(-8), win(-4), win(4), win(8.5)])
wall("G_E", "z", X1, Z0, Z1, G0, STOREY, 0, C["outer"], OUTER_T, [win(-8), win(-4), win(5), win(9)])

# --- Ground floor interior walls ---
d = lambda c, w=1.4: (c, w, 0, DOOR_H, "door")
wall("G_FoyerWest", "z", -4, Z0, Z1, G0, STOREY, 0, C["inner"], INNER_T, [d(-7), d(1), d(8)])
wall("G_FoyerEast", "z", 4, Z0, Z1, G0, STOREY, 0, C["inner"], INNER_T, [d(-7), d(8)])
wall("G_StudyLibrary", "x", -2, X0, -4, G0, STOREY, 0, C["inner"], INNER_T, [d(-10)])
wall("G_DiningKitchen", "x", 2, 4, X1, G0, STOREY, 0, C["inner"], INNER_T, [d(10)])
wall("G_FoyerBackHall", "x", 4, -4, 4, G0, STOREY, 0, C["inner"], INNER_T, [d(-1.6, 1.6)])

door((-4, 0, -7.7), 0, 1.4, 0, "Door_Study")
door((-4, 0, 0.3), 0, 1.4, 0, "Door_Library")
door((-4, 0, 7.3), 0, 1.4, 0, "Door_LibraryBackHall")
door((4, 0, -7.7), 0, 1.4, 0, "Door_Dining")
door((4, 0, 7.3), 0, 1.4, 0, "Door_KitchenBackHall")
door((-10.7, 0, -2), 90, 1.4, 0, "Door_StudyLibrary")
door((9.3, 0, 2), 90, 1.4, 0, "Door_DiningKitchen")
door((-2.4, 0, 4), 90, 1.6, 0, "Door_BackHall")
door((-1, 0, Z0), 90, 2.0, 0, "Door_Front")
door((11.8, 0, Z1), 90, 1.4, 0, "Door_Garden")

room("Foyer", 0, -4, 4, Z0, 4, G0, G1)
room("Library", 0, X0, -4, -2, Z1, G0, G1)
room("Study", 0, X0, -4, Z0, -2, G0, G1)
room("Dining Room", 0, 4, X1, Z0, 2, G0, G1)
room("Kitchen", 0, 4, X1, 2, Z1, G0, G1)
room("Back Hall", 0, -4, 4, 4, Z1, G0, G1)

# --- Stairs ---
stairs("GrandStairs", STAIR_UP[0], STAIR_UP[1], -6.0, G0, 14, 1, 0, C["dark_wood"])
railing("StairwellRailW", STAIR_UP[2], STAIR_UP[3], "z", STAIR_UP[0] - 0.05, G1, 1)
railing("StairwellRailE", STAIR_UP[2], STAIR_UP[3], "z", STAIR_UP[1] + 0.05, G1, 1)
railing("StairwellRailS", STAIR_UP[0], STAIR_UP[1], "x", STAIR_UP[2] - 0.05, G1, 1)
stairs("CellarStairs", CELLAR_HOLE[0], CELLAR_HOLE[1], 5.0, G0, 14, 1, -1, C["stone"], down=True)
railing("CellarRailW", CELLAR_HOLE[2], CELLAR_HOLE[3], "z", CELLAR_HOLE[0] - 0.05, G0, 0)
railing("CellarRailE", CELLAR_HOLE[2], CELLAR_HOLE[3], "z", CELLAR_HOLE[1] + 0.05, G0, 0)
railing("CellarRailN", CELLAR_HOLE[0], CELLAR_HOLE[1], "x", CELLAR_HOLE[3] + 0.05, G0, 0)

# --- Upper floor walls ---
wall("U_S", "x", Z0, X0 - 0.2, X1 + 0.2, G1, STOREY + 0.2, 1, C["outer"], OUTER_T, [win(-12), win(-7.5), win(0), win(7.5), win(12)])
wall("U_N", "x", Z1, X0 - 0.2, X1 + 0.2, G1, STOREY + 0.2, 1, C["outer"], OUTER_T, [win(-12), win(-7.5), win(0), win(7.5), win(12)])
wall("U_W", "z", X0, Z0, Z1, G1, STOREY + 0.2, 1, C["outer"], OUTER_T, [win(-8), win(-4), win(4), win(8.5)])
wall("U_E", "z", X1, Z0, Z1, G1, STOREY + 0.2, 1, C["outer"], OUTER_T, [win(-8), win(-4), win(5), win(9)])
wall("U_HallWest", "z", -4, Z0, Z1, G1, STOREY, 1, C["upper_inner"], INNER_T, [d(-8), d(7)])
wall("U_HallEast", "z", 4, Z0, Z1, G1, STOREY, 1, C["upper_inner"], INNER_T, [d(-8), d(7)])
wall("U_WestSplit", "x", 2, X0, -4, G1, STOREY, 1, C["upper_inner"], INNER_T)
wall("U_EastSplit", "x", 2, 4, X1, G1, STOREY, 1, C["upper_inner"], INNER_T)
door((-4, G1, -8.7), 0, 1.4, 1, "Door_GuestRoom")
door((-4, G1, 6.3), 0, 1.4, 1, "Door_MasterBedroom")
door((4, G1, -8.7), 0, 1.4, 1, "Door_Gallery")
door((4, G1, 6.3), 0, 1.4, 1, "Door_Servants")
room("Upstairs Hall", 1, -4, 4, Z0, Z1, G1, 2 * STOREY)
room("Master Bedroom", 1, X0, -4, 2, Z1, G1, 2 * STOREY)
room("Guest Room", 1, X0, -4, Z0, 2, G1, 2 * STOREY)
room("Servants' Quarters", 1, 4, X1, 2, Z1, G1, 2 * STOREY)
room("Portrait Gallery", 1, 4, X1, Z0, 2, G1, 2 * STOREY)

# --- Roof: gable along x, stepped gable ends, chimneys ---
half = (Z1 - Z0) / 2 + 0.6
slope = math.hypot(half, RIDGE)
ang = math.degrees(math.atan2(RIDGE, half))
box("RoofSouth", (0, ROOF_BASE + RIDGE / 2, -half / 2), (X1 - X0 + 1.2, 0.3, slope), C["roof"], 2, "solid", "roof", r=(-ang, 0, 0))
box("RoofNorth", (0, ROOF_BASE + RIDGE / 2, half / 2), (X1 - X0 + 1.2, 0.3, slope), C["roof"], 2, "solid", "roof", r=(ang, 0, 0))
box("RoofRidge", (0, ROOF_BASE + RIDGE + 0.05, 0), (X1 - X0 + 1.4, 0.25, 0.4), C["trim"], 2, "solid", "roof")
steps_n = 10
for i in range(steps_n):
    y_lo = ROOF_BASE + i * RIDGE / steps_n
    hw = (Z1 - Z0) / 2 * (1 - (i + 0.5) / steps_n)
    for side, x in (("W", X0), ("E", X1)):
        box(f"Gable{side}{i}", (x, y_lo + RIDGE / steps_n / 2, 0), (OUTER_T, RIDGE / steps_n, 2 * hw), C["outer"], 2, "solid", "roof")
for side, x in (("W", -10), ("E", 10)):
    box(f"Chimney{side}", (x, ROOF_BASE + RIDGE * 0.7, 4), (1.4, RIDGE * 1.4 + 1.5, 1.4), rgb("5b3a33"), 2, "solid", "roof")
    box(f"ChimneyCap{side}", (x, ROOF_BASE + RIDGE * 1.4 + 0.2, 4), (1.7, 0.2, 1.7), C["stone"], 2, "solid", "roof")
# cornice trim between floors
for name, z in (("CorniceS", Z0 - 0.25), ("CorniceN", Z1 + 0.25)):
    box(name, (0, G1, z), (X1 - X0 + 0.9, 0.3, 0.2), C["trim"], 1, "nocollide", "trim")

# --- Porch ---
box("PorchFloor", (0, 0.03, Z0 - 1.4), (5.2, 0.06, 2.6), C["stone"], 9, "nocollide", "porch")
for x in (-2, 2):
    box(f"PorchColumn{x}", (x, 1.5, Z0 - 1.6), (0.35, 3.0, 0.35), C["white"], 9, "solid", "porch")
box("PorchRoof", (0, 3.1, Z0 - 1.2), (5.2, 0.2, 2.6), C["roof"], 9, "solid", "porch")

# ---------------------------------------------------------------------------
# Furniture (static) and possessables
# ---------------------------------------------------------------------------
def shelf(name, p, along_x, length, level):
    x, y, z = p
    sx, sz = (length, 0.5) if along_x else (0.5, length)
    box(name, (x, y + 1.25, z), (sx, 2.5, sz), C["dark_wood"], level, "solid", "furniture")
    for k, col in enumerate((C["book1"], C["book2"], C["book3"], C["book1"])):
        off = (0.3 if along_x else 0)
        bx, bz = (x, z + (0.27 if not along_x else 0)) if False else (x, z)
        box(f"{name}_books{k}", (x + (0 if along_x else 0.02), y + 0.45 + k * 0.55, z + (0.02 if along_x else 0)),
            (sx * 0.92 if along_x else 0.52, 0.32, 0.52 if along_x else sz * 0.92), col, level, "nocollide", "decor")


def table(name, p, size, level, color=None, legs=True):
    x, y, z = p
    sx, h, sz = size
    box(name, (x, y + h - 0.05, z), (sx, 0.1, sz), color or C["wood"], level, "solid", "furniture")
    if legs:
        for dx in (-1, 1):
            for dz in (-1, 1):
                box(f"{name}_leg{dx}{dz}", (x + dx * (sx / 2 - 0.1), y + (h - 0.1) / 2, z + dz * (sz / 2 - 0.1)), (0.1, h - 0.1, 0.1), C["dark_wood"], level, "solid", "furniture")


def bed(name, p, level, along_x=True):
    x, y, z = p
    sx, sz = (2.2, 1.6) if along_x else (1.6, 2.2)
    box(name, (x, y + 0.3, z), (sx, 0.6, sz), C["dark_wood"], level, "solid", "furniture")
    box(f"{name}_sheet", (x, y + 0.65, z), (sx * 0.95, 0.12, sz * 0.95), C["white"], level, "nocollide", "decor")
    hx, hz = (x - sx / 2, z) if along_x else (x, z + sz / 2)
    box(f"{name}_head", (hx, y + 0.75, hz), (0.15 if along_x else sx, 1.5, sz if along_x else 0.15), C["dark_wood"], level, "solid", "furniture")


def painting(name, p, along_x, level, color):
    x, y, z = p
    box(name, (x, y, z), (1.2 if along_x else 0.06, 0.9, 0.06 if along_x else 1.2), C["brass"], level, "nocollide", "decor")
    box(f"{name}_canvas", (x, y, z), (1.0 if along_x else 0.08, 0.7, 0.08 if along_x else 1.0), color, level, "nocollide", "decor")


# Foyer
possessable("Suit of Armor (West)", "capsule", (-3.2, 1.0, -10.8), (0.7, 1.0, 0.7), C["stone"], False, 0)
possessable("Suit of Armor (East)", "capsule", (3.2, 1.0, -10.8), (0.7, 1.0, 0.7), C["stone"], False, 0)
light("Chandelier", (1.5, 2.7, -8.5), rgb("ffd28a"), 11, 1.8, 0, "cyl", (0, 0.15, 0), (0.9, 0.1, 0.9))
table("FoyerTable", (2.8, 0, -1.5), (1.4, 0.9, 0.6), 0)
painting("PortraitFoyer", (0, 2.0, 3.85), True, 0, rgb("4a3a6a"))

# Library
for i, z in enumerate((-0.5, 3.5, 7.5)):
    shelf(f"LibShelfW{i}", (-15.5, 0, z + 1.5), False, 3.0, 0)
shelf("LibShelfN1", (-12.5, 0, 11.5), True, 3.0, 0)
shelf("LibShelfN2", (-7.5, 0, 11.5), True, 3.0, 0)
table("ReadingTable", (-10, 0, 5), (2.4, 0.8, 1.2), 0)
possessable("Armchair", "box", (-7, 0.45, 3), (1.0, 0.9, 1.0), C["red"], True, 0)
possessable("Wingback Chair", "box", (-12.8, 0.45, 2.2), (1.0, 0.9, 1.0), rgb("5a2a4a"), True, 0)
box("Fireplace", (-10, 1.0, -1.65), (2.4, 2.0, 0.5), C["stone"], 0, "solid", "furniture")
box("FireplaceMouth", (-10, 0.5, -1.4), (1.2, 0.8, 0.1), rgb("120c08"), 0, "nocollide", "decor")
light("Fireplace Fire", (-10, 0.5, -1.0), C["fire"], 9, 2.2, 0, "box", (0, -0.25, -0.1), (0.8, 0.2, 0.3), C["fire"])

# Study
table("Desk", (-10, 0, -8), (2.0, 0.85, 1.0), 0, C["dark_wood"])
possessable("Grandfather Clock", "box", (-15.4, 1.2, -6), (0.6, 2.4, 0.8), C["dark_wood"], False, 0)
possessable("Globe", "cyl", (-6, 0.6, -10.5), (0.7, 0.6, 0.7), C["brass"], True, 0)
light("Desk Lamp", (-9.4, 1.25, -8.2), rgb("ffe0a0"), 7, 1.3, 0, "cyl", (0, -0.2, 0), (0.15, 0.4, 0.15))
shelf("StudyShelf", (-12.5, 0, -11.5), True, 4.0, 0)
box("Safe", (-15.3, 0.5, -10.8), (0.9, 1.0, 0.9), C["iron"], 0, "solid", "furniture")

# Dining
table("DiningTable", (10, 0, -5), (6.0, 0.85, 1.6), 0, C["dark_wood"])
for i, x in enumerate((8, 10, 12)):
    for dz in (-1.3, 1.3):
        box(f"DiningChair{i}{int(dz > 0)}", (x, 0.5, -5 + dz), (0.5, 1.0, 0.5), C["wood"], 0, "solid", "furniture")
possessable("Dining Chair", "box", (13.8, 0.5, -5), (0.55, 1.0, 0.55), C["wood"], True, 0)
possessable("China Cabinet", "box", (15.3, 1.1, -9), (0.7, 2.2, 2.4), C["dark_wood"], False, 0)
light("Candelabra", (10, 1.25, -5), rgb("ffc070"), 8, 1.4, 0, "cyl", (0, -0.2, 0), (0.25, 0.4, 0.25))
painting("PortraitDining", (10, 2.0, -11.75), True, 0, rgb("6a3a3a"))

# Kitchen
box("CounterN", (10, 0.45, 11.4), (8.0, 0.9, 0.8), C["white"], 0, "solid", "furniture")
box("CounterE", (15.4, 0.45, 7), (0.8, 0.9, 6.0), C["white"], 0, "solid", "furniture")
box("Stove", (6.5, 0.5, 11.3), (1.6, 1.0, 1.0), C["iron"], 0, "solid", "furniture")
box("StoveHood", (6.5, 2.4, 11.5), (1.6, 0.8, 0.8), C["copper"], 0, "solid", "furniture")
table("KitchenTable", (9.5, 0, 6.5), (2.2, 0.85, 1.2), 0)
for k in range(3):
    box(f"FlourSack{k}", (14.8 - k * 0.7, 0.35, 3.2), (0.6, 0.7, 0.5), C["sack"], 0, "solid", "furniture")
possessable("Copper Pot", "cyl", (9.2, 1.0, 6.6), (0.45, 0.3, 0.45), C["copper"], True, 0)
possessable("Kitchen Stool", "box", (11.3, 0.35, 5.5), (0.45, 0.7, 0.45), C["wood"], True, 0)
light("Kitchen Lamp", (9.5, 2.9, 6.5), rgb("fff0c8"), 9, 1.15, 0, "cyl", (0, 0.2, 0), (0.6, 0.25, 0.6))

# Back hall
possessable("Coat Rack", "cyl", (-3.2, 1.0, 11.2), (0.25, 1.0, 0.25), C["dark_wood"], False, 0)
light("Wall Sconce", (-3.75, 2.2, 6.5), rgb("ffd090"), 6, 1.1, 0, "box", (0.1, 0, 0), (0.15, 0.4, 0.2))

# Cellar
for i, x in enumerate((-14, -10, -6)):
    box(f"WineRack{i}", (x, CELLAR_Y + 1.1, 11.4), (3.0, 2.2, 0.6), C["dark_wood"], -1, "solid", "furniture")
for i, (x, z) in enumerate(((-13, 1), (-12, 0.5), (8, 1), (9.2, 0.6))):
    box(f"Barrel{i}", (x, CELLAR_Y + 0.6, z), (0.9, 0.6, 0.9), C["wood"], -1, "solid", "furniture", "cyl")
possessable("Rolling Barrel", "cyl", (-2, CELLAR_Y + 0.6, 0.5), (0.9, 0.6, 0.9), C["wood"], True, -1)
possessable("Boiler", "cyl", (9.5, CELLAR_Y + 1.2, 10.5), (1.6, 1.2, 1.6), C["copper"], False, -1)
for i, (x, z) in enumerate(((-15, 7), (-15, 5.8), (6, -1.2))):
    box(f"Crate{i}", (x, CELLAR_Y + 0.4, z), (0.8, 0.8, 0.8), C["wood"], -1, "solid", "furniture")
light("Cellar Bulb", (-4, CELLAR_Y + 3.0, 4), rgb("ffd27a"), 12, 1.5, -1, "cyl", (0, 0.2, 0), (0.2, 0.3, 0.2))

# Upstairs
bed("MasterBed", (-13.5, G1, 7), 1)
possessable("Wardrobe", "box", (-6, G1 + 1.1, 11.4), (2.0, 2.2, 0.8), C["dark_wood"], False, 1)
possessable("Vanity Mirror", "box", (-15.5, G1 + 0.9, 3.5), (0.5, 1.8, 1.2), rgb("9aa7b8"), False, 1)
light("Bedside Lamp", (-14.8, G1 + 0.9, 9.3), rgb("ffd6a0"), 7, 1.2, 1, "cyl", (0, -0.25, 0), (0.3, 0.5, 0.3))
bed("GuestBed", (-13.5, G1, -8), 1)
possessable("Rocking Chair", "box", (-7, G1 + 0.5, -4), (0.7, 1.0, 0.9), C["wood"], True, 1)
box("GuestDresser", (-6, G1 + 0.5, -11.5), (1.8, 1.0, 0.6), C["dark_wood"], 1, "solid", "furniture")
for i, z in enumerate((-10, -6, -2)):
    painting(f"Gallery{i}", (15.75, G1 + 2.0, z), False, 1, [rgb("4a3a6a"), rgb("2e4a3a"), rgb("6a4a2a")][i])
possessable("Marble Bust", "cyl", (10, G1 + 1.3, -6), (0.5, 0.35, 0.5), C["white"], True, 1)
box("BustPlinth", (10, G1 + 0.55, -6), (0.6, 1.1, 0.6), C["stone"], 1, "solid", "furniture")
possessable("Dress Dummy", "capsule", (7, G1 + 0.9, -10.5), (0.6, 0.9, 0.6), rgb("c7b9a8"), False, 1)
light("Gallery Lamp", (12.5, G1 + 2.9, -5), rgb("ffe2b0"), 9, 1.3, 1, "cyl", (0, 0.2, 0), (0.5, 0.2, 0.5))
bed("ServantBed1", (13.5, G1, 9), 1)
bed("ServantBed2", (13.5, G1, 4.5), 1)
possessable("Old Trunk", "box", (7, G1 + 0.35, 10.8), (1.2, 0.7, 0.7), C["wood"], True, 1)
light("Servant Candle", (8, G1 + 1.0, 5), rgb("ffc070"), 6, 1.0, 1, "cyl", (0, -0.2, 0), (0.12, 0.4, 0.12))
light("Hall Lamp", (0, G1 + 2.9, 5), rgb("ffd8a0"), 10, 1.4, 1, "cyl", (0, 0.2, 0), (0.5, 0.2, 0.5))

# ---------------------------------------------------------------------------
# Grounds
# ---------------------------------------------------------------------------
GX0, GX1, GZ0, GZ1 = -44.0, 44.0, -42.0, 38.0
slab("Lawn", 0.0, GX0, GX1, GZ0, GZ1, [(X0 - 0.2, X1 + 0.2, Z0 - 0.2, Z1 + 0.2)], C["grass"], 9, 0.4, "ground")
box("FrontPath", (0, 0.02, -26), (3.0, 0.04, 26), C["gravel"], 9, "nocollide", "path")
box("SidePath", (16, 0.02, 15.5), (16, 0.04, 2.4), C["gravel"], 9, "nocollide", "path")

# Iron fence with a front gate
post_gap = 3.0
for side, (a0, a1, fixed, axis) in {"S": (GX0 + 2, GX1 - 2, GZ0 + 2, "x"), "N": (GX0 + 2, GX1 - 2, GZ1 - 2, "x"),
                                     "W": (GZ0 + 2, GZ1 - 2, GX0 + 2, "z"), "E": (GZ0 + 2, GZ1 - 2, GX1 - 2, "z")}.items():
    n = int((a1 - a0) / post_gap)
    for i in range(n + 1):
        a = a0 + i * (a1 - a0) / n
        if side == "S" and abs(a) < 2.5:
            continue  # gate opening
        pos = (a, 1.0, fixed) if axis == "x" else (fixed, 1.0, a)
        box(f"Fence{side}{i}", pos, (0.15, 2.0, 0.15), C["iron"], 9, "solid", "fence")
    for k, y in enumerate((0.4, 1.8)):
        if side == "S":
            for part, (b0, b1) in enumerate(((a0, -2.5), (2.5, a1))):
                box(f"FenceRail{side}{k}{part}", ((b0 + b1) / 2, y, fixed), (b1 - b0, 0.08, 0.08), C["iron"], 9, "solid", "fence")
        else:
            mid, length = (a0 + a1) / 2, a1 - a0
            pos, size = ((mid, y, fixed), (length, 0.08, 0.08)) if axis == "x" else ((fixed, y, mid), (0.08, 0.08, length))
            box(f"FenceRail{side}{k}", pos, size, C["iron"], 9, "solid", "fence")
for x in (-2.6, 2.6):
    box(f"GatePillar{x}", (x, 1.4, GZ0 + 2), (0.7, 2.8, 0.7), C["stone"], 9, "solid", "fence")

# Fountain
box("FountainBasin", (0, 0.35, -24), (6.0, 0.35, 6.0), C["stone"], 9, "solid", "fountain", "cyl")
box("FountainWater", (0, 0.66, -24), (5.4, 0.02, 5.4), C["water"], 9, "nocollide", "fountain", "cyl")
box("FountainPillar", (0, 1.4, -24), (0.6, 0.7, 0.6), C["stone"], 9, "solid", "fountain", "cyl")
box("FountainBowl", (0, 2.2, -24), (1.8, 0.1, 1.8), C["stone"], 9, "solid", "fountain", "cyl")

# Cemetery (west)
for i in range(9):
    gx, gz = -34 + (i % 3) * 4, -22 + (i // 3) * 4.5
    box(f"Gravestone{i}", (gx, 0.6, gz), (1.0, 1.2 + (i % 2) * 0.3, 0.25), C["stone"], 9, "solid", "cemetery")
box("Crypt", (-34, 1.6, -4), (5.0, 3.2, 4.0), rgb("5d5e66"), 9, "solid", "cemetery")
box("CryptRoof", (-34, 3.4, -4), (5.6, 0.4, 4.6), C["stone"], 9, "solid", "cemetery")

# Hedge garden (north-west)
for i, (x, z, sx, sz) in enumerate(((-30, 18, 14, 1.2), (-30, 30, 14, 1.2), (-37, 24, 1.2, 12), (-23, 21, 1.2, 6),
                                    (-30, 24, 6, 1.2), (-27, 27, 1.2, 4))):
    box(f"Hedge{i}", (x, 0.8, z), (sx, 1.6, sz), C["hedge"], 9, "solid", "hedge")

# Greenhouse (north-east): the groundskeeper's domain
GH = (28.0, 22.0)
for i, (x, z, sx, sz) in enumerate(((GH[0], GH[1] - 4, 10, 0.08), (GH[0], GH[1] + 4, 10, 0.08),
                                    (GH[0] + 5, GH[1], 0.08, 8), (GH[0] - 5, GH[1] - 2.7, 0.08, 2.6), (GH[0] - 5, GH[1] + 2.7, 0.08, 2.6))):
    box(f"GreenhouseGlass{i}", (x, 1.6, z), (sx, 3.2, sz), C["glass_dark"], 9, "glass", "greenhouse")
for i, (dx, dz) in enumerate(((-5, -4), (5, -4), (-5, 4), (5, 4), (0, -4), (0, 4))):
    box(f"GreenhouseFrame{i}", (GH[0] + dx, 1.7, GH[1] + dz), (0.15, 3.4, 0.15), C["white"], 9, "solid", "greenhouse")
box("GreenhouseRoof", (GH[0], 3.45, GH[1]), (10.4, 0.1, 8.4), C["glass_dark"], 9, "glass", "greenhouse")
for i, z in enumerate((GH[1] - 2, GH[1] + 2)):
    box(f"PlantTable{i}", (GH[0] + 0.5, 0.45, z), (7.0, 0.9, 1.0), C["wood"], 9, "solid", "greenhouse")
    for k in range(6):
        box(f"Plant{i}{k}", (GH[0] - 2.4 + k * 1.15, 1.15, z), (0.5, 0.5, 0.5), C["plant"], 9, "nocollide", "greenhouse")
possessable("Wheelbarrow", "box", (GH[0] - 7, 0.4, GH[1] - 5), (1.4, 0.6, 0.8), C["copper"], True, 9)
light("Greenhouse Lamp", (GH[0], 2.9, GH[1]), rgb("d0ffb0"), 9, 1.2, 9, "cyl", (0, 0.2, 0), (0.4, 0.2, 0.4))

# Dead trees
for i, (x, z, h) in enumerate(((-22, -30, 7), (20, -32, 8), (-38, 10, 6.5), (36, -10, 7.5), (-14, 30, 6), (38, 32, 7), (24, 4, 6))):
    box(f"Tree{i}Trunk", (x, h / 2, z), (0.6, h, 0.6), C["bark"], 9, "solid", "tree")
    for k, (ry, rz, y) in enumerate(((20, 40, 0.6), (140, 35, 0.75), (260, 45, 0.85))):
        length = h * 0.45
        # Unity Euler (0, ry, rz): local up tilted by rz around z, then turned by ry around y.
        ux, uy = -math.sin(math.radians(rz)), math.cos(math.radians(rz))
        dx, dz = ux * math.cos(math.radians(ry)), -ux * math.sin(math.radians(ry))
        box(f"Tree{i}Branch{k}", (x + dx * length / 2, h * y + uy * length / 2, z + dz * length / 2), (0.25, length, 0.25),
            C["bark"], 9, "nocollide", "tree", r=(0, ry, rz))

    # Jack-o'-lanterns hung from two of the trees, like the lit trees on the Nights of the Jack trail
    if i in (0, 1, 3):
        for k, (ry, rz, y) in enumerate(((20, 40, 0.6), (140, 35, 0.75), (260, 45, 0.85))):
            length = h * 0.45
            ux, uy = -math.sin(math.radians(rz)), math.cos(math.radians(rz))
            dx, dz = ux * math.cos(math.radians(ry)), -ux * math.sin(math.radians(ry))
            tip = (x + dx * length * 0.85, h * y + uy * length * 0.85, z + dz * length * 0.85)
            box(f"Tree{i}Rope{k}", (tip[0], tip[1] - 0.35, tip[2]), (0.03, 0.7, 0.03), rgb("6b5a3a"), 9, "nocollide", "decor")
            decor("jack", (tip[0], tip[1] - 1.15, tip[2]), facing(-dx, -dz), 0.75)
        glow((x, h * 0.55, z), rgb("ff8a2a"), 7, 1.1)

# Path lanterns (possessable)
for i, (x, z) in enumerate(((-2.4, -18), (2.4, -30), (-2.4, -36))):
    light(f"Lantern {i + 1}", (x, 2.4, z), rgb("ffd27a"), 9, 1.6, 9, "cyl", (0, -1.2, 0), (0.15, 2.4, 0.15), C["iron"])

# ---------------------------------------------------------------------------
# Halloween night: a jack-o'-lantern trail (after LA's "Nights of the Jack"), a pumpkin patch,
# candles, cobwebs and a witch's cauldron. Props come from Costumes.json.
# ---------------------------------------------------------------------------
JACK_GLOW = rgb("ff8a2a")

# The gate arch: jacks piled on the pillars and a rainbow of them over the gate
for x in (-2.6, 2.6):
    decor("jack", (x, 2.8, GZ0 + 2), 180, 1.3)
for k in range(9):
    a = math.pi * k / 8
    decor("jack", (2.4 * math.cos(a), 3.0 + 1.6 * math.sin(a), GZ0 + 2), 180, 0.85)
glow((0, 3.6, GZ0 + 1.2), JACK_GLOW, 8, 1.6)

# The trail: carved pumpkins lining both sides of the front path, big and small
random_sizes = [1.0, 0.75, 1.25, 0.9, 1.1, 0.7, 1.35, 0.85]
n = 0
for z in [v * 1.5 for v in range(-26, -9)]:
    if -28.5 < z < -19.5:
        continue  # the fountain gets its own ring
    for side in (-1, 1):
        n += 1
        sc = random_sizes[n % len(random_sizes)]
        decor("jack", (side * (1.95 + 0.15 * (n % 3)), 0.0, z + 0.3 * side), facing(-side, 0.25), sc)
        if n % 5 == 0:
            decor("pumpkin", (side * 2.55, 0.0, z + 0.6), facing(-side, 0), 0.7)
    if int(z * 2) % 9 == 0:
        glow((0, 0.8, z), JACK_GLOW, 6, 1.4)
for z in (-37.5, -31.5, -17.5):
    for side in (-1, 1):
        decor("haybale", (side * 3.3, 0, z), 90, 1.0)
        decor("jack", (side * 3.3, 0.6, z - 0.15), facing(-side, 0), 1.0)

# A ring of jack-o'-lanterns around the fountain
for k in range(14):
    a = 2 * math.pi * k / 14
    dx, dz = math.sin(a), math.cos(a)
    decor("jack", (dx * 3.75, 0.0, -24 + dz * 3.75), facing(dx, dz), 0.9 + 0.25 * (k % 2))
for k in range(4):
    a = 2 * math.pi * (k + 0.5) / 4
    glow((math.sin(a) * 4.2, 0.9, -24 + math.cos(a) * 4.2), JACK_GLOW, 6, 1.3)

# Porch: the biggest pumpkins guard the front door
for side in (-1, 1):
    decor("jack", (side * 1.7, 0.06, Z0 - 2.2), facing(0, -1), 1.6)
    decor("jack", (side * 2.4, 0.06, Z0 - 1.0), facing(0, -1), 1.15)
    decor("pumpkin", (side * 2.35, 0.06, Z0 - 2.4), 30 * side, 1.1)
    decor("pumpkin", (side * 2.3, 0.75, Z0 - 2.35), -20 * side, 0.7)
    decor("candle", (side * 1.25, 0.06, Z0 - 2.7), 0, 1.2)
glow((0, 1.2, Z0 - 2.8), JACK_GLOW, 7, 1.5)

# Pumpkin patch (south-east) with a pumpkin-headed scarecrow and crows
PX, PZ = 30.0, -24.0
box("PatchDirt", (PX, 0.015, PZ), (16, 0.03, 16), rgb("3b2a1e"), 9, "nocollide", "patch")
for row in range(6):
    box(f"PatchVine{row}", (PX, 0.04, PZ - 6.5 + row * 2.6), (14, 0.05, 0.18), rgb("3d5a22"), 9, "nocollide", "patch")
    for col in range(6):
        x = PX - 6.2 + col * 2.5 + (0.6 if row % 2 else 0)
        z = PZ - 6.5 + row * 2.6 + 0.35 * math.sin(col * 2.1 + row)
        if abs(x - PX) < 1.6 and abs(z - PZ) < 1.6:
            continue  # the scarecrow stands here
        lit = (row * 6 + col) % 7 == 3
        decor("jack" if lit else "pumpkin", (x, 0.0, z), facing(-1, -1) + col * 23, 0.8 + 0.35 * ((row + col) % 3))
decor("scarecrow", (PX, 0.0, PZ), facing(-1, -0.6), 1.15)
for k, (x, z) in enumerate(((PX - 7.6, PZ - 5), (PX - 7.6, PZ + 3), (PX + 7.4, PZ + 7))):
    decor("haybale", (x, 0, z), 15 * k, 1.0)
    decor("crow", (x, 0.6, z), 200 + 40 * k, 1.0)
decor("crow", (PX + 0.75, 1.5, PZ), 100, 1.0)
glow((PX, 2.4, PZ), JACK_GLOW, 9, 1.4)
glow((PX - 4, 0.8, PZ + 4), JACK_GLOW, 6, 1.1)
room("Pumpkin Patch", 9, PX - 8, PX + 8, PZ - 8, PZ + 8, -1, 8)

# Cemetery: candles and lanterns on the graves, crows, and a witch's cauldron by the crypt
for i in range(9):
    gx, gz = -34 + (i % 3) * 4, -22 + (i // 3) * 4.5
    decor("candle" if i % 2 else "lantern", (gx + 0.35, 0.0, gz - 0.45), 0, 1.3)
    if i % 3 == 1:
        decor("crow", (gx, 1.2 + (i % 2) * 0.3, gz), 160 + 30 * i, 1.0)
    if i % 2 == 0:
        decor("jack", (gx - 0.4, 0.0, gz - 0.5), 180, 0.6)
decor("cauldron", (-34, 0, -0.9), 0, 1.3)
for k in range(5):
    decor("candle", (-35.5 + k * 0.75, 0, -1.8 - 0.4 * math.sin(k)), 0, 1.4)
glow((-34, 1.3, -0.9), rgb("9dff8a"), 8, 1.8)
for k, (x, z) in enumerate(((-30, -18), (-36, -12), (-32, -24))):
    glow((x, 1.3, z), rgb("9dff8a") if k % 2 else rgb("ffb347"), 5, 1.1)

# Candles and jacks indoors
for i, x in enumerate((8.0, 9.0, 11.0, 12.0)):
    decor("candle", (x, 0.85, -5 + (0.3 if i % 2 else -0.3)), 0, 1.0, 0)
decor("jack", (10, 0.85, -5), 180, 0.6, 0)
decor("jack", (2.8, 0.9, -1.5), 180, 0.7, 0)
decor("jack", (9.5, 0.85, 6.5), -120, 0.55, 0)
decor("candle", (-10.6, 0.8, 5.2), 0, 1.0, 0)
decor("candle", (-9.4, 0.8, 4.8), 0, 1.0, 0)
decor("candle", (-14.8, G1 + 0.6, 9.8), 0, 1.0, 1)
decor("jack", (-4.6, CELLAR_Y, 1.0), 45, 0.8, -1)

# Cobwebs in the corners
WEB_ROOMS = [  # (x0, x1, z0, z1, ceiling y, level, corners)
    (-4, 4, Z0, 4, G1 - SLAB, 0, ("sw", "se")), (X0, -4, -2, Z1, G1 - SLAB, 0, ("nw", "ne")),
    (X0, -4, Z0, -2, G1 - SLAB, 0, ("sw",)), (4, X1, Z0, 2, G1 - SLAB, 0, ("se", "sw")),
    (-4, 4, 4, Z1, G1 - SLAB, 0, ("nw",)), (X0, -4, 2, Z1, 2 * STOREY - 0.05, 1, ("nw", "sw")),
    (X0, -4, Z0, 2, 2 * STOREY - 0.05, 1, ("sw",)), (4, X1, Z0, 2, 2 * STOREY - 0.05, 1, ("se", "ne")),
    (4, X1, 2, Z1, 2 * STOREY - 0.05, 1, ("ne",)), (-16, 12, -2, 12, -SLAB, -1, ("nw", "ne", "sw", "se")),
]
for x0, x1, z0, z1, ceil, level, corners in WEB_ROOMS:
    for c in corners:
        cx, dx = (x0 + 0.2, 1) if c[1] == "w" else (x1 - 0.2, -1)
        cz, dz = (z0 + 0.2, 1) if c[0] == "s" else (z1 - 0.2, -1)
        d = 0.6 / math.sqrt(2)
        decor("cobweb", (cx + dx * d, ceil - 0.02, cz + dz * d), facing(dx, dz), 1.0, level)

# ---------------------------------------------------------------------------
# Gameplay points
# ---------------------------------------------------------------------------
L["trapdoors"] += [
    {"n": "Kitchen Trapdoor", "p": [12.5, 0.0, 8.0], "drop": [10.8, CELLAR_Y + 0.2, 7.5]},
    {"n": "Library Trapdoor", "p": [-10.0, 0.0, 8.5], "drop": [-10.0, CELLAR_Y + 0.2, 8.0]},
    {"n": "Gallery Trapdoor", "p": [7.0, G1, -4.0], "drop": [6.0, 0.2, -0.5]},
]
suspect("Groundskeeper", (GH[0] - 1, 0, GH[1]), rgb("6e9646"), -90)
suspect("Heiress", (-9, G1, 6), rgb("be5aaa"), 90)
suspect("Rival", (11, G1, -9), rgb("5064a0"), -90)
suspect("Cook", (12.5, 0, 9.5), rgb("ebebdc"), -120)

for p in ((-13.5, 0.2, 0.5), (-8, 0.2, 10.5), (-14.5, 0.2, -11), (-5.5, 0.2, -4), (2.5, 0.2, 10.5), (14.5, 0.2, -11),
          (7, 0.2, -1), (14.5, 0.2, 4.5), (-12, CELLAR_Y + 0.2, 9.5), (6, CELLAR_Y + 0.2, 8), (-14.5, G1 + 0.2, 11),
          (-6, G1 + 0.2, -6), (15, G1 + 0.2, 0.5), (8, G1 + 0.2, 8), (-1.5, G1 + 0.2, 10.5), (-30, 0.2, 24),
          (-32, 0.2, -18), (30, 0.2, 21), (10, 0.2, -22), (-6, 0.2, -32)):
    L["clueSpots"].append(pt(p))
for p in ((-14, 0.25, 9), (-14.5, CELLAR_Y + 0.25, 3), (14.5, 0.25, -1.5), (14.5, G1 + 0.25, -11), (-35, 0.25, -12)):
    L["trapPieces"].append(pt(p))
L["trapSite"] = pt((1.2, 0, -7.5))
for i in range(4):
    L["solverSpawns"].append(pt((-2.25 + i * 1.5, 0.1, -34)))
L["haunterSpawn"] = pt((0, G1 + 1.0, 9))
room("Grounds", 9, GX0, GX1, GZ0, GZ1, -1, 30)
room("Greenhouse", 9, GH[0] - 5, GH[0] + 5, GH[1] - 4, GH[1] + 4, -1, 4)
room("Cemetery", 9, -40, -26, -26, 0, -1, 8)

import dressing  # noqa: E402  (window trim, foundations, surfaces, varied jack-o'-lanterns)


class _Here:  # lets the shared Halloween set pieces add to this layout
    pass


_H = _Here()
_H.L, _H.box, _H.decor, _H.glow = L, box, decor, glow

# A few more touches: ghosts in the dead trees, a cat on the crypt, a watcher at an upstairs window
for x, z, h in ((-38, 10, 6.5), (24, 4, 6)):
    L_ = h * 0.45 * 0.85
    ux = -math.sin(math.radians(35))
    tip = (x + ux * math.cos(math.radians(140)) * L_, h * 0.75 + math.cos(math.radians(35)) * L_, z - ux * math.sin(math.radians(140)) * L_)
    decor("ghost_hang", tip, 200)
    glow((tip[0], tip[1] - 1.2, tip[2]), rgb("bfe9de"), 4, 0.6)
decor("cat", (-33.0, 3.6, -5.6), 190)
decor("spider", (9.0, 0.1, -13.6), 180, 1.3)
decor("window_ghost", (-7.5, G1, -11.55), 180, 1.0, 1)
dressing.graves(_H, -37.5, -2.0, 3, 1.0)
dressing.luminarias(_H, (0.0, -21.0), (0.0, -13.5), 1.5, 2.7, glow_every=2)
L["shutter"] = rgb("2a2430")
dressing.finish(L)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(L, f, separators=(",", ":"))
print(f"Wrote {OUT}: {len(L['boxes'])} boxes, {len(L['doors'])} doors, {len(L['possessables'])} possessables, "
      f"{len(L['lights'])} lights, {len(L['decor'])} Halloween props, {len(L['glows'])} glows, "
      f"{len(L['rooms'])} rooms, {os.path.getsize(OUT) // 1024} KB")
