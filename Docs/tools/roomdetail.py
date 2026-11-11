"""
Round 45: every room gets plenty to look at.

Lots of rooms in the houses and the manor were a floor, four walls and one or two big pieces.
furnish(L) walks every indoor room and dresses it for what it is: beds, wardrobes, nightstands and
toy chests in bedrooms; desks, bookcases and globes in studies; shelves of jars, sacks and barrels
in kitchens, pantries and cellars; a piano and a gramophone in a music room; framed paintings and
little lamps on the walls; a rug in the middle. Each piece is a handful of soft boxes, cylinders and
balls, so it reads as a real thing rather than a crate.

It only puts a piece where it fits: backed by a solid wall (never in front of a doorway or a tall
window), standing on a floor, clear of other furniture, stairs, doors, trapdoors, clue spots,
suspects and spawn points, and leaving a walkway in front. It's seeded from the room's name, so
every build is the same. dressing.finish() calls it, so every layout gets it when it's saved.

    import roomdetail; roomdetail.furnish(L)
"""
import math
import re
import zlib

# --- colours ------------------------------------------------------------------------------------
def _hex(h):
    return [round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4)]


WOOD = [_hex(h) for h in ("5a3a24", "6e4a2e", "4a2e1e", "7a5236", "3e2a1c")]
CLOTH = [_hex(h) for h in ("7a2e3a", "2e4a6a", "4a6a3a", "8a6a2a", "5a3a6a", "8a4a2a", "2e5a5a")]
BOOKS = [_hex(h) for h in ("8a2a2a", "2a4a7a", "3a6a3a", "c8a050", "5a2a5a", "7a5a3a", "2a2a2a", "a0602a")]
WHITE, CREAM, BRASS, IRON = _hex("ece4d4"), _hex("e8d8b0"), _hex("c8a040"), _hex("2a2a2e")
WARM, GLASS, GREEN, POT = _hex("ffd890"), _hex("a8c8d8"), _hex("3e6a32"), _hex("a05a3a")

STEP = 0.25        # metres between tries along a wall
INSET = 0.2        # from the wall's centre line to the back of a piece
WALK = 0.7         # free floor kept in front of every piece
DOOR_CLEAR = 1.1   # nothing within this of a doorway
SPOT_CLEAR = 0.8   # nor of a clue spot, suspect, spawn point, trapdoor


def _roll(*key):
    return zlib.crc32("|".join(str(k) for k in key).encode())


# --- the pieces ---------------------------------------------------------------------------------
# Each piece is (width along the wall, depth into the room, height, parts). A part is
# (name, shape, (x, y, z), (sx, sy, sz), colour, mode) in the piece's own frame: x along the wall,
# y up from the floor, z out from the wall. The first part is the solid one you bump into.
def bed(k):
    w, c, b = WOOD[k % 5], CLOTH[k % 7], CLOTH[(k // 7) % 7]
    return 1.5, 2.15, 1.2, [
        ("Frame", "rbox", (0, 0.24, 1.08), (1.5, 0.3, 2.0), w, "solid"),
        ("Mattress", "rbox", (0, 0.46, 1.12), (1.4, 0.18, 1.86), WHITE, "nocollide"),
        ("Quilt", "rbox", (0, 0.53, 1.38), (1.46, 0.1, 1.36), c, "nocollide"),
        ("QuiltFold", "rcyl", (0, 0.58, 0.74), (0.09, 0.71, 0.09), b, "nocollide", (0, 0, 90)),
        ("Pillow", "sphere", (0, 0.62, 0.38), (0.9, 0.16, 0.36), WHITE, "nocollide"),
        ("Headboard", "rbox", (0, 0.62, 0.06), (1.6, 1.2, 0.1), w, "nocollide"),
        ("Footboard", "rbox", (0, 0.4, 2.06), (1.6, 0.62, 0.08), w, "nocollide"),
    ]


def nightstand(k):
    w = WOOD[k % 5]
    return 0.5, 0.45, 1.0, [
        ("Body", "rbox", (0, 0.3, 0.24), (0.5, 0.6, 0.44), w, "solid"),
        ("Knob", "sphere", (0, 0.42, 0.47), (0.05, 0.05, 0.05), BRASS, "nocollide"),
        ("LampBase", "rcyl", (0, 0.68, 0.24), (0.12, 0.08, 0.12), BRASS, "nocollide"),
        ("LampShade", "rcyl", (0, 0.86, 0.24), (0.3, 0.1, 0.3), WARM, "emissive"),
    ]


def wardrobe(k):
    w = WOOD[(k + 1) % 5]
    return 1.2, 0.6, 2.15, [
        ("Body", "rbox", (0, 1.04, 0.3), (1.2, 2.08, 0.6), w, "solid"),
        ("Crown", "rbox", (0, 2.12, 0.3), (1.3, 0.1, 0.66), WOOD[(k + 3) % 5], "nocollide"),
        ("Seam", "box", (0, 1.1, 0.605), (0.02, 1.7, 0.01), IRON, "nocollide"),
        ("KnobL", "sphere", (-0.08, 1.1, 0.62), (0.05, 0.05, 0.05), BRASS, "nocollide"),
        ("KnobR", "sphere", (0.08, 1.1, 0.62), (0.05, 0.05, 0.05), BRASS, "nocollide"),
    ]


def dresser(k):
    w = WOOD[(k + 2) % 5]
    parts = [("Body", "rbox", (0, 0.45, 0.25), (1.1, 0.9, 0.5), w, "solid"),
             ("MirrorFrame", "rbox", (0, 1.42, 0.07), (0.72, 0.9, 0.05), w, "nocollide"),
             ("Mirror", "box", (0, 1.42, 0.1), (0.6, 0.78, 0.01), GLASS, "glass")]
    for i in range(3):
        parts.append((f"Drawer{i}", "box", (0, 0.2 + 0.27 * i, 0.505), (1.0, 0.02, 0.01), IRON, "nocollide"))
        parts.append((f"Pull{i}", "sphere", (0, 0.32 + 0.27 * i, 0.51), (0.06, 0.04, 0.04), BRASS, "nocollide"))
    return 1.1, 0.5, 1.9, parts


def toychest(k):
    c = CLOTH[k % 7]
    return 0.9, 0.5, 0.9, [
        ("Box", "rbox", (0, 0.24, 0.26), (0.9, 0.48, 0.5), c, "solid"),
        ("Lid", "rbox", (0, 0.5, 0.26), (0.94, 0.06, 0.54), WOOD[k % 5], "nocollide"),
        ("Ball", "sphere", (0.25, 0.65, 0.3), (0.22, 0.22, 0.22), CLOTH[(k + 3) % 7], "nocollide"),
        ("Bear", "sphere", (-0.2, 0.68, 0.24), (0.2, 0.26, 0.18), _hex("a0703a"), "nocollide"),
        ("BearHead", "sphere", (-0.2, 0.88, 0.24), (0.16, 0.15, 0.15), _hex("a0703a"), "nocollide"),
    ]


def crib(k):
    w = WOOD[(k + 4) % 5]
    parts = [("Base", "rbox", (0, 0.4, 0.4), (1.3, 0.12, 0.7), w, "solid"),
             ("Blanket", "rbox", (0, 0.5, 0.42), (1.2, 0.08, 0.62), CLOTH[k % 7], "nocollide")]
    for i in range(9):
        x = -0.6 + i * 0.15
        parts.append((f"Bar{i}", "cyl", (x, 0.6, 0.76), (0.03, 0.3, 0.03), w, "nocollide"))
    parts.append(("RailF", "rbox", (0, 0.92, 0.76), (1.3, 0.05, 0.05), w, "nocollide"))
    parts.append(("RailB", "rbox", (0, 0.92, 0.06), (1.3, 0.05, 0.05), w, "nocollide"))
    return 1.3, 0.8, 1.0, parts


def rocking_horse(k):
    c = _hex("c8b090")
    return 0.9, 0.5, 0.9, [
        ("Body", "capsule", (0, 0.5, 0.26), (0.26, 0.3, 0.26), c, "solid", (0, 0, 90)),
        ("Head", "capsule", (0.34, 0.72, 0.26), (0.14, 0.14, 0.14), c, "nocollide", (0, 0, -30)),
        ("Mane", "rbox", (0.26, 0.8, 0.26), (0.08, 0.2, 0.06), _hex("4a2a1a"), "nocollide"),
        ("Rocker", "rcyl", (0, 0.06, 0.26), (0.05, 0.42, 0.3), _hex("8a2a2a"), "nocollide", (0, 0, 90)),
    ]


def bookcase(k):
    w = WOOD[k % 5]
    parts = [("Body", "box", (0, 1.0, 0.17), (1.0, 2.0, 0.34), w, "solid"),
             ("Top", "rbox", (0, 2.03, 0.18), (1.08, 0.06, 0.38), WOOD[(k + 2) % 5], "nocollide")]
    for s in range(4):
        y = 0.12 + s * 0.48
        parts.append((f"Shelf{s}", "box", (0, y, 0.3), (0.94, 0.03, 0.06), WOOD[(k + 1) % 5], "nocollide"))
        x = -0.43
        for b in range(3):
            r = _roll(k, s, b)
            bw = 0.18 + (r % 7) * 0.025
            bh = 0.26 + (r // 7 % 5) * 0.03
            parts.append((f"Books{s}{b}", "box", (x + bw / 2, y + bh / 2 + 0.02, 0.3), (bw, bh, 0.05), BOOKS[r % len(BOOKS)], "nocollide"))
            x += bw + 0.04 + (r % 3) * 0.03
    return 1.0, 0.36, 2.06, parts


def desk(k):
    w = WOOD[(k + 3) % 5]
    return 1.3, 1.35, 1.2, [
        ("Top", "rbox", (0, 0.74, 0.34), (1.3, 0.06, 0.66), w, "solid"),
        ("Pedestal", "rbox", (0.42, 0.36, 0.34), (0.42, 0.72, 0.6), w, "nocollide"),
        ("LegA", "rcyl", (-0.58, 0.36, 0.1), (0.06, 0.36, 0.06), w, "nocollide"),
        ("LegB", "rcyl", (-0.58, 0.36, 0.6), (0.06, 0.36, 0.06), w, "nocollide"),
        ("Lamp", "rcyl", (0.42, 0.9, 0.18), (0.08, 0.12, 0.08), BRASS, "nocollide"),
        ("LampShade", "capsule", (0.36, 1.04, 0.22), (0.12, 0.08, 0.26), _hex("2e6a3a"), "emissive", (90, 0, 0)),
        ("Papers", "box", (-0.15, 0.775, 0.4), (0.32, 0.01, 0.24), CREAM, "nocollide", (0, 12, 0)),
        ("BookStack", "rbox", (-0.45, 0.84, 0.22), (0.24, 0.14, 0.18), BOOKS[k % len(BOOKS)], "nocollide"),
        ("Inkpot", "sphere", (0.05, 0.8, 0.18), (0.07, 0.07, 0.07), IRON, "nocollide"),
        ("ChairSeat", "rbox", (0, 0.46, 1.0), (0.48, 0.07, 0.46), w, "nocollide"),
        ("ChairBack", "rbox", (0, 0.78, 1.21), (0.46, 0.56, 0.06), w, "nocollide"),
        ("ChairLegs", "rbox", (0, 0.22, 1.0), (0.4, 0.44, 0.38), WOOD[(k + 4) % 5], "nocollide"),
    ]


def armchair(k):
    c = CLOTH[(k + 2) % 7]
    return 0.95, 0.9, 1.05, [
        ("Seat", "rbox", (0, 0.3, 0.48), (0.8, 0.32, 0.72), c, "solid"),
        ("Cushion", "rbox", (0, 0.5, 0.52), (0.66, 0.12, 0.6), c, "nocollide"),
        ("Back", "rbox", (0, 0.72, 0.16), (0.86, 0.78, 0.2), c, "nocollide"),
        ("ArmL", "rbox", (-0.42, 0.52, 0.48), (0.14, 0.36, 0.76), c, "nocollide"),
        ("ArmR", "rbox", (0.42, 0.52, 0.48), (0.14, 0.36, 0.76), c, "nocollide"),
        ("Throw", "rbox", (0.3, 0.75, 0.2), (0.3, 0.6, 0.06), CLOTH[(k + 5) % 7], "nocollide", (0, 0, 12)),
    ]


def side_table(k):
    w = WOOD[(k + 1) % 5]
    return 0.55, 0.55, 1.0, [
        ("Top", "rcyl", (0, 0.66, 0.28), (0.5, 0.03, 0.5), w, "solid"),
        ("Stem", "rcyl", (0, 0.33, 0.28), (0.07, 0.32, 0.07), w, "nocollide"),
        ("Foot", "rcyl", (0, 0.03, 0.28), (0.32, 0.03, 0.32), w, "nocollide"),
        ("Lamp", "sphere", (0, 0.76, 0.28), (0.14, 0.18, 0.14), _hex("6a8aa0"), "nocollide"),
        ("LampShade", "rcyl", (0, 0.94, 0.28), (0.32, 0.09, 0.32), WARM, "emissive"),
    ]


def clock(k):
    w = WOOD[(k + 2) % 5]
    return 0.55, 0.38, 2.15, [
        ("Case", "rbox", (0, 1.0, 0.19), (0.5, 2.0, 0.36), w, "solid"),
        ("Hood", "rbox", (0, 2.08, 0.19), (0.58, 0.16, 0.4), WOOD[(k + 4) % 5], "nocollide"),
        ("Face", "sphere", (0, 1.7, 0.38), (0.32, 0.32, 0.03), CREAM, "nocollide"),
        ("Hand", "box", (0.04, 1.74, 0.395), (0.02, 0.12, 0.01), IRON, "nocollide", (0, 0, -30)),
        ("Window", "box", (0, 0.95, 0.375), (0.26, 0.7, 0.01), GLASS, "glass"),
        ("Pendulum", "sphere", (0, 0.75, 0.35), (0.14, 0.14, 0.03), BRASS, "nocollide"),
    ]


def plant(k):
    return 0.6, 0.6, 1.3, [
        ("Pot", "rcyl", (0, 0.22, 0.3), (0.4, 0.22, 0.4), POT, "solid"),
        ("Soil", "rcyl", (0, 0.44, 0.3), (0.34, 0.02, 0.34), _hex("3a2a1a"), "nocollide"),
        ("Leaves", "sphere", (0, 0.82, 0.3), (0.62, 0.6, 0.58), GREEN, "nocollide"),
        ("Leaves2", "sphere", (0.12, 1.08, 0.24), (0.38, 0.4, 0.38), _hex("4e7a3a"), "nocollide"),
    ]


def coat_stand(k):
    return 0.6, 0.6, 1.9, [
        ("Pole", "rcyl", (0, 0.92, 0.3), (0.06, 0.9, 0.06), WOOD[k % 5], "solid"),
        ("Foot", "rcyl", (0, 0.03, 0.3), (0.42, 0.03, 0.42), WOOD[k % 5], "nocollide"),
        ("Coat", "capsule", (0.12, 1.3, 0.34), (0.3, 0.32, 0.22), CLOTH[k % 7], "nocollide"),
        ("Hat", "rcyl", (-0.1, 1.86, 0.28), (0.3, 0.04, 0.3), IRON, "nocollide"),
        ("HatTop", "rcyl", (-0.1, 1.94, 0.28), (0.18, 0.08, 0.18), IRON, "nocollide"),
        ("Umbrella", "rcyl", (-0.18, 0.5, 0.42), (0.05, 0.45, 0.05), _hex("2a2a3a"), "nocollide", (8, 0, 0)),
    ]


def piano(k):
    w = _hex("1e1612")
    return 1.5, 1.15, 1.35, [
        ("Body", "rbox", (0, 0.66, 0.3), (1.5, 1.32, 0.6), w, "solid"),
        ("Keys", "box", (0, 0.74, 0.68), (1.3, 0.04, 0.2), WHITE, "nocollide"),
        ("KeyLid", "rbox", (0, 0.82, 0.62), (1.36, 0.1, 0.06), w, "nocollide"),
        ("Music", "box", (0, 1.05, 0.62), (0.4, 0.28, 0.01), CREAM, "nocollide", (-12, 0, 0)),
        ("Candle", "rcyl", (0.6, 1.42, 0.3), (0.05, 0.1, 0.05), CREAM, "nocollide"),
        ("Flame", "sphere", (0.6, 1.55, 0.3), (0.04, 0.07, 0.04), WARM, "emissive"),
        ("Stool", "rcyl", (0, 0.45, 1.0), (0.42, 0.05, 0.36), CLOTH[k % 7], "nocollide"),
        ("StoolLeg", "rcyl", (0, 0.22, 1.0), (0.12, 0.22, 0.12), w, "nocollide"),
    ]


def gramophone(k):
    w = WOOD[k % 5]
    return 0.6, 0.6, 1.5, [
        ("Stand", "rbox", (0, 0.4, 0.3), (0.55, 0.8, 0.5), w, "solid"),
        ("Box", "rbox", (0, 0.9, 0.3), (0.42, 0.2, 0.4), WOOD[(k + 2) % 5], "nocollide"),
        ("Record", "rcyl", (0, 1.01, 0.3), (0.32, 0.01, 0.32), IRON, "nocollide"),
        ("Arm", "rcyl", (0.1, 1.1, 0.24), (0.03, 0.12, 0.03), BRASS, "nocollide", (40, 0, 0)),
        ("Horn", "sphere", (0.12, 1.3, 0.12), (0.36, 0.36, 0.2), BRASS, "nocollide", (-30, 0, 0)),
    ]


def harp(k):
    return 0.7, 0.7, 1.7, [
        ("Column", "rcyl", (-0.2, 0.85, 0.35), (0.06, 0.82, 0.06), BRASS, "solid"),
        ("Body", "rbox", (0.1, 0.7, 0.35), (0.14, 1.3, 0.16), WOOD[k % 5], "nocollide", (0, 0, -12)),
        ("Neck", "rcyl", (0, 1.6, 0.35), (0.06, 0.24, 0.06), BRASS, "nocollide", (0, 0, 70)),
        ("Base", "rbox", (0, 0.05, 0.35), (0.5, 0.1, 0.3), WOOD[k % 5], "nocollide"),
    ]


def sideboard(k):
    w = WOOD[(k + 1) % 5]
    return 1.6, 0.5, 1.2, [
        ("Body", "rbox", (0, 0.45, 0.25), (1.6, 0.9, 0.5), w, "solid"),
        ("Runner", "box", (0, 0.91, 0.25), (1.2, 0.01, 0.3), CREAM, "nocollide"),
        ("Bowl", "sphere", (0, 0.98, 0.25), (0.36, 0.14, 0.36), _hex("d8d0c0"), "nocollide"),
        ("Fruit", "sphere", (0.04, 1.04, 0.24), (0.12, 0.12, 0.12), _hex("c8401e"), "nocollide"),
        ("CandleA", "rcyl", (-0.55, 1.05, 0.25), (0.05, 0.14, 0.05), CREAM, "nocollide"),
        ("CandleB", "rcyl", (0.55, 1.05, 0.25), (0.05, 0.14, 0.05), CREAM, "nocollide"),
        ("FlameA", "sphere", (-0.55, 1.23, 0.25), (0.04, 0.07, 0.04), WARM, "emissive"),
        ("FlameB", "sphere", (0.55, 1.23, 0.25), (0.04, 0.07, 0.04), WARM, "emissive"),
    ]


def china_cabinet(k):
    w = WOOD[(k + 3) % 5]
    parts = [("Body", "rbox", (0, 1.0, 0.22), (1.1, 2.0, 0.44), w, "solid"),
             ("Glass", "box", (0, 1.35, 0.445), (0.92, 1.1, 0.01), GLASS, "glass")]
    for s in range(3):
        y = 0.9 + s * 0.38
        for i in range(3):
            parts.append((f"Plate{s}{i}", "sphere", (-0.3 + i * 0.3, y + 0.14, 0.12), (0.26, 0.26, 0.03), _hex("e8e0f0"), "nocollide"))
    return 1.1, 0.46, 2.0, parts


def washstand(k):
    return 0.9, 0.55, 1.9, [
        ("Cabinet", "rbox", (0, 0.4, 0.27), (0.9, 0.8, 0.5), WOOD[k % 5], "solid"),
        ("Basin", "sphere", (0, 0.86, 0.3), (0.5, 0.14, 0.4), WHITE, "nocollide"),
        ("Jug", "rcyl", (0.32, 0.95, 0.2), (0.12, 0.13, 0.12), _hex("6a8ab0"), "nocollide"),
        ("MirrorFrame", "rbox", (0, 1.5, 0.06), (0.6, 0.74, 0.05), BRASS, "nocollide"),
        ("Mirror", "box", (0, 1.5, 0.09), (0.5, 0.64, 0.01), GLASS, "glass"),
        ("Towel", "rbox", (-0.47, 0.6, 0.3), (0.04, 0.5, 0.3), CLOTH[k % 7], "nocollide"),
    ]


def barrel(k):
    w = WOOD[(k + 1) % 5]
    return 0.6, 0.6, 1.0, [
        ("Barrel", "rcyl", (0, 0.45, 0.3), (0.56, 0.45, 0.56), w, "solid"),
        ("HoopA", "cyl", (0, 0.2, 0.3), (0.58, 0.02, 0.58), IRON, "nocollide"),
        ("HoopB", "cyl", (0, 0.7, 0.3), (0.58, 0.02, 0.58), IRON, "nocollide"),
        ("Apples", "sphere", (0, 0.92, 0.3), (0.42, 0.12, 0.42), _hex("b8301e"), "nocollide"),
    ]


def sacks(k):
    c = _hex("c8b088")
    return 1.0, 0.6, 0.8, [
        ("SackA", "sphere", (-0.25, 0.3, 0.3), (0.5, 0.6, 0.45), c, "solid"),
        ("SackB", "sphere", (0.25, 0.27, 0.32), (0.48, 0.54, 0.44), _hex("b8a078"), "nocollide"),
        ("SackC", "sphere", (0.0, 0.62, 0.3), (0.42, 0.36, 0.4), c, "nocollide"),
        ("Tie", "rcyl", (0.0, 0.82, 0.3), (0.08, 0.04, 0.08), _hex("6a5a3a"), "nocollide"),
    ]


def crates(k):
    w = WOOD[(k + 3) % 5]
    return 1.0, 0.7, 1.2, [
        ("CrateA", "rbox", (-0.2, 0.3, 0.35), (0.6, 0.6, 0.6), w, "solid"),
        ("CrateB", "rbox", (0.25, 0.25, 0.35), (0.5, 0.5, 0.5), WOOD[(k + 1) % 5], "nocollide", (0, 14, 0)),
        ("CrateC", "rbox", (-0.15, 0.82, 0.33), (0.44, 0.44, 0.44), WOOD[(k + 2) % 5], "nocollide", (0, -10, 0)),
        ("Lantern", "rcyl", (0.25, 0.6, 0.35), (0.14, 0.1, 0.14), IRON, "nocollide"),
        ("LanternGlow", "sphere", (0.25, 0.72, 0.35), (0.1, 0.12, 0.1), WARM, "emissive"),
    ]


def jar_shelves(k):
    w = WOOD[(k + 4) % 5]
    parts = [("Frame", "box", (0, 0.95, 0.17), (1.2, 1.9, 0.34), w, "solid")]
    jars = [_hex(h) for h in ("c86a2a", "d8b040", "8a2a3a", "5a8a3a", "e8d8b0", "6a3a2a")]
    for s in range(3):
        y = 0.4 + s * 0.55
        parts.append((f"Shelf{s}", "box", (0, y, 0.3), (1.14, 0.03, 0.06), WOOD[k % 5], "nocollide"))
        for i in range(4):
            r = _roll(k, s, i)
            h = 0.16 + (r % 4) * 0.03
            parts.append((f"Jar{s}{i}", "rcyl", (-0.42 + i * 0.28, y + h / 2 + 0.02, 0.3), (0.14, h / 2, 0.14), jars[r % len(jars)], "nocollide"))
    return 1.2, 0.36, 1.9, parts


def dress_form(k):
    c = CLOTH[(k + 1) % 7]
    return 0.6, 0.6, 1.6, [
        ("Stem", "rcyl", (0, 0.5, 0.3), (0.05, 0.5, 0.05), WOOD[k % 5], "solid"),
        ("Foot", "rcyl", (0, 0.03, 0.3), (0.4, 0.03, 0.4), WOOD[k % 5], "nocollide"),
        ("Torso", "capsule", (0, 1.25, 0.3), (0.36, 0.26, 0.26), c, "nocollide"),
        ("Skirt", "rcyl", (0, 0.88, 0.3), (0.44, 0.12, 0.38), c, "nocollide"),
        ("Knob", "sphere", (0, 1.58, 0.3), (0.08, 0.06, 0.08), BRASS, "nocollide"),
    ]


def sewing_table(k):
    w = WOOD[(k + 2) % 5]
    return 1.0, 0.55, 1.0, [
        ("Top", "rbox", (0, 0.72, 0.28), (1.0, 0.05, 0.52), w, "solid"),
        ("Legs", "rbox", (0, 0.36, 0.28), (0.9, 0.7, 0.04), IRON, "nocollide"),
        ("Machine", "rbox", (-0.1, 0.86, 0.26), (0.42, 0.22, 0.16), IRON, "nocollide"),
        ("Wheel", "rcyl", (0.13, 0.88, 0.26), (0.14, 0.02, 0.14), BRASS, "nocollide", (0, 0, 90)),
        ("Fabric", "rbox", (0.32, 0.77, 0.3), (0.3, 0.04, 0.4), CLOTH[k % 7], "nocollide"),
        ("Spool", "rcyl", (0.2, 0.8, 0.12), (0.06, 0.05, 0.06), CLOTH[(k + 3) % 7], "nocollide"),
    ]


def globe(k):
    return 0.6, 0.6, 1.3, [
        ("Stand", "rcyl", (0, 0.4, 0.3), (0.1, 0.4, 0.1), WOOD[k % 5], "solid"),
        ("Foot", "rcyl", (0, 0.03, 0.3), (0.42, 0.03, 0.42), WOOD[k % 5], "nocollide"),
        ("Ring", "cyl", (0, 1.0, 0.3), (0.56, 0.02, 0.56), BRASS, "nocollide", (0, 0, 70)),
        ("Globe", "sphere", (0, 1.0, 0.3), (0.5, 0.5, 0.5), _hex("3a6a8a"), "nocollide"),
        ("Land", "sphere", (0.06, 1.06, 0.36), (0.32, 0.3, 0.4), _hex("8aa060"), "nocollide"),
    ]


def filing(k):
    parts = [("Body", "rbox", (0, 0.68, 0.28), (0.55, 1.36, 0.55), _hex("5a6a5a"), "solid")]
    for i in range(4):
        parts.append((f"Pull{i}", "rbox", (0, 0.24 + i * 0.32, 0.56), (0.16, 0.04, 0.03), BRASS, "nocollide"))
    parts.append(("Files", "rbox", (0, 1.42, 0.26), (0.42, 0.12, 0.34), CREAM, "nocollide", (0, 8, 0)))
    return 0.55, 0.56, 1.5, parts


def bench(k):
    w = WOOD[(k + 1) % 5]
    return 1.4, 0.5, 0.9, [
        ("Seat", "rbox", (0, 0.44, 0.25), (1.4, 0.08, 0.44), w, "solid"),
        ("Legs", "rbox", (0, 0.2, 0.25), (1.3, 0.4, 0.06), WOOD[(k + 3) % 5], "nocollide"),
        ("Cushion", "rbox", (-0.3, 0.52, 0.25), (0.5, 0.08, 0.38), CLOTH[k % 7], "nocollide"),
        ("Boots", "rbox", (0.4, 0.12, 0.3), (0.3, 0.24, 0.26), _hex("3a2a1e"), "nocollide"),
    ]


def display_shelf(k):
    w = WOOD[k % 5]
    parts = [("Frame", "box", (0, 0.8, 0.17), (1.2, 1.6, 0.34), w, "solid")]
    things = [_hex(h) for h in ("c8a040", "8a2a3a", "2e5a8a", "d8d0c0", "5a8a3a")]
    for s in range(3):
        y = 0.3 + s * 0.5
        parts.append((f"Shelf{s}", "box", (0, y, 0.3), (1.14, 0.03, 0.06), WOOD[(k + 2) % 5], "nocollide"))
        for i in range(3):
            r = _roll(k, "d", s, i)
            shape = ("sphere", "rcyl", "rbox")[r % 3]
            parts.append((f"Curio{s}{i}", shape, (-0.36 + i * 0.36, y + 0.12, 0.28), (0.18, 0.2 if shape != "rcyl" else 0.1, 0.18), things[r % 5], "nocollide"))
    return 1.2, 0.36, 1.6, parts


def stove(k):
    return 1.0, 0.65, 1.6, [
        ("Body", "rbox", (0, 0.45, 0.32), (1.0, 0.9, 0.62), IRON, "solid"),
        ("Pipe", "rcyl", (0.3, 1.25, 0.12), (0.14, 0.4, 0.14), IRON, "nocollide"),
        ("Pot", "rcyl", (-0.2, 1.0, 0.35), (0.3, 0.1, 0.3), _hex("8a8a90"), "nocollide"),
        ("Kettle", "sphere", (0.2, 0.98, 0.38), (0.24, 0.18, 0.24), _hex("b06a3a"), "nocollide"),
        ("Fire", "box", (0, 0.35, 0.635), (0.4, 0.16, 0.01), _hex("ff9a40"), "emissive"),
    ]


def corkboard(k):
    """For the club's HQ: a corkboard of clues with string between the pins."""
    parts = [("Board", "box", (0, 1.5, 0.04), (1.4, 0.9, 0.04), _hex("b8865a"), "solid")]
    for i in range(6):
        r = _roll(k, "pin", i)
        x, y = -0.5 + (i % 3) * 0.5 + (r % 7 - 3) * 0.02, 1.32 + (i // 3) * 0.36
        parts.append((f"Note{i}", "box", (x, y, 0.065), (0.24, 0.18, 0.01), (CREAM, _hex("f0e080"), _hex("e0b0b0"))[r % 3], "nocollide", (0, 0, (r % 11) - 5)))
        parts.append((f"Pin{i}", "sphere", (x, y + 0.07, 0.075), (0.03, 0.03, 0.03), _hex("c8302a"), "nocollide"))
    parts.append(("String", "box", (0, 1.5, 0.078), (1.0, 0.01, 0.005), _hex("c8302a"), "nocollide", (0, 0, 20)))
    return 1.4, 0.1, 2.0, parts


# what each kind of room gets, best first; "rug" and "art" are added for all of them
ROOMS = [
    (r"nursery|kids", [crib, toychest, rocking_horse, wardrobe, nightstand, bookcase, armchair]),
    (r"bed|guest|servant|quarters", [bed, nightstand, wardrobe, dresser, armchair, toychest, plant]),
    (r"kitchen", [stove, jar_shelves, sideboard, barrel, sacks, crates]),
    (r"pantry|mudroom", [jar_shelves, sacks, barrel, crates, coat_stand, bench]),
    (r"cellar|basement", [barrel, crates, jar_shelves, sacks, barrel, crates]),
    (r"study|office|curator", [desk, bookcase, globe, filing, armchair, clock, plant]),
    (r"library|reading|archive", [bookcase, desk, bookcase, globe, armchair, bookcase, filing]),
    (r"music", [piano, harp, gramophone, armchair, side_table, plant]),
    (r"dining", [sideboard, china_cabinet, clock, plant, side_table]),
    (r"bath", [washstand, plant, toychest]),
    (r"sewing", [sewing_table, dress_form, jar_shelves, armchair, toychest]),
    (r"gift|shop", [display_shelf, display_shelf, plant, bench]),
    (r"gallery|mask", [bench, plant, display_shelf, clock]),
    (r"hq|club", [corkboard, desk, bookcase, armchair, globe, filing, gramophone]),
    (r"hall|foyer|landing|entrance", [clock, coat_stand, bench, side_table, plant, armchair]),
    (r"parlor|parlour|living|sitting", [armchair, side_table, clock, bookcase, plant, gramophone, armchair]),
    (r".", [armchair, side_table, bookcase, plant, clock]),
]

# pieces a room only ever has one of, with the words that mean it already has one
ONCE = {bed: ("bed",), crib: ("crib", "cradle"), piano: ("piano",), harp: ("harp",), desk: ("desk", "bureau"),
        stove: ("stove", "range", "oven"), corkboard: ("board",), globe: ("globe",), clock: ("clock",),
        sewing_table: ("sewing",), washstand: ("sink", "basin", "washstand"), dress_form: ("dress form", "mannequin"),
        gramophone: ("gramophone", "phonograph"), wardrobe: ("wardrobe", "armoire"), dresser: ("dresser",),
        rocking_horse: ("rocking",), toychest: ("toy",), china_cabinet: ("china",), sideboard: ("sideboard",)}

PAINT = [_hex(h) for h in ("3a5a7a", "7a4a2a", "4a6a4a", "8a6a4a", "3a3a5a", "6a2a2a")]


# --- the room's surroundings -------------------------------------------------------------------
class Room:
    def __init__(self, L, r):
        self.L, self.r = L, r
        self.lo, self.hi = r["min"], r["max"]
        self.level = r["l"]
        cx, cz = (self.lo[0] + self.hi[0]) / 2, (self.lo[2] + self.hi[2]) / 2
        self.y0 = self.floor_at(cx, cz)
        if self.y0 is None:
            self.y0 = self.lo[1]
        box = [b for b in L["boxes"] if self._near(b)]
        self.solid = [b for b in box if b["m"] in ("solid", "glass", "nocollide", "emissive", "ghost")]
        self.keep = []  # (x, z, radius) circles nothing may stand in
        for d in L.get("doors", []):
            if abs(d.get("l", 0) - self.level) <= 0:
                self.keep.append((d["p"][0], d["p"][2], d.get("w", 1.2) / 2 + DOOR_CLEAR))
        for t in L.get("trapdoors", []):
            p = t.get("p")
            if p and self._here(p):
                self.keep.append((p[0], p[2], 1.2))
        for key in ("clueSpots", "suspects", "solverSpawns"):
            for s in L.get(key, []):
                if self._here(s["p"]):
                    self.keep.append((s["p"][0], s["p"][2], SPOT_CLEAR))
        hs = L.get("haunterSpawn")
        if isinstance(hs, dict) and "p" in hs and self._here(hs["p"]):
            self.keep.append((hs["p"][0], hs["p"][2], SPOT_CLEAR))
        elif isinstance(hs, list) and len(hs) == 3 and self._here(hs):
            self.keep.append((hs[0], hs[2], SPOT_CLEAR))
        self.objs = [b for b in self.solid if "Plinth" not in b["n"]]  # the foundation strip is only ankle-high trim
        for p in L.get("possessables", []):
            self.objs.append({"p": p["p"], "s": p.get("s", [0.8, 0.8, 0.8]), "r": [0, 0, 0], "g": "furniture", "n": p["n"], "m": "solid"})
        self.doorways = self._doorways()
        self.inset = [self._inset(side) for side in range(4)]

    def _inset(self, side):
        """How far the wall on a side reaches into the room (thick cellar walls reach further)."""
        (ox, oz), (ux, uz), (vx, vz), length = self.frame(side)
        deep = 0.0
        for b in self.solid:
            if b["g"] != "wall" or b["m"] != "solid":
                continue
            (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
            if py + sy / 2 < self.y0 + 0.3 or py - sy / 2 > self.y0 + 1.0:
                continue
            if vx:  # wall runs along z at x = ox
                if sz < sx or abs(px - ox) > sx / 2 + 0.01 or pz + sz / 2 < min(oz, oz + uz * length) or pz - sz / 2 > max(oz, oz + uz * length):
                    continue
                deep = max(deep, (px - ox) * vx + sx / 2)
            else:
                if sx < sz or abs(pz - oz) > sz / 2 + 0.01 or px + sx / 2 < min(ox, ox + ux * length) or px - sx / 2 > max(ox, ox + ux * length):
                    continue
                deep = max(deep, (pz - oz) * vz + sz / 2)
        return min(max(INSET, deep + 0.05), 0.6)

    def _here(self, p):
        """Is a point on this room's floor (not upstairs or down in the cellar)?"""
        return self.y0 - 1.0 <= p[1] <= self.y0 + 2.0

    def _near(self, b):
        (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
        e = max(sx, sz) / 2 if abs(b.get("r", [0, 0, 0])[1]) % 180 > 1 else 0
        return (px + sx / 2 + e > self.lo[0] - 1 and px - sx / 2 - e < self.hi[0] + 1 and pz + sz / 2 + e > self.lo[2] - 1
                and pz - sz / 2 - e < self.hi[2] + 1 and py + sy / 2 > self.lo[1] - 0.5 and py - sy / 2 < self.hi[1] + 0.5)

    def floor_at(self, x, z):
        best = None
        for b in self.L["boxes"]:
            (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
            if b["m"] not in ("solid",) or sy > 0.8 or abs(b.get("r", [0, 0, 0])[1]) % 180 > 1:
                continue
            if b["g"] not in ("floor", "ground", "porch", "trim", "stairs") and "Floor" not in b["n"]:
                continue
            top = py + sy / 2
            if abs(px - x) <= sx / 2 and abs(pz - z) <= sz / 2 and self.lo[1] - 0.3 <= top <= self.lo[1] + 1.3:
                best = top if best is None else max(best, top)
        return best

    def solid_at(self, x, y, z, walls_only=True):
        for b in self.solid:
            if walls_only and b["g"] != "wall":
                continue
            if b["m"] not in ("solid",):
                continue
            (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
            if abs(b.get("r", [0, 0, 0])[1]) % 180 > 1:
                continue
            if abs(px - x) <= sx / 2 + 0.02 and abs(py - y) <= sy / 2 and abs(pz - z) <= sz / 2 + 0.02:
                return True
        return False

    def _doorways(self):
        """Points along the room's edges where you can walk through: no wall at knee or chest height."""
        out = []
        y = self.y0
        for side in range(4):
            for t in self._along(side, 0.25):
                x, z = t
                if not self.solid_at(x, y + 0.5, z) and not self.solid_at(x, y + 1.3, z):
                    out.append((x, z))
        return out

    def _along(self, side, step):
        lo, hi = self.lo, self.hi
        if side in (0, 1):  # walls along x, at min z (0) and max z (1)
            z = lo[2] if side == 0 else hi[2]
            n = int((hi[0] - lo[0]) / step)
            return [(lo[0] + (i + 0.5) * (hi[0] - lo[0]) / n, z) for i in range(n)]
        x = lo[0] if side == 2 else hi[0]
        n = int((hi[2] - lo[2]) / step)
        return [(x, lo[2] + (i + 0.5) * (hi[2] - lo[2]) / n) for i in range(n)]

    def frame(self, side):
        """(origin on the wall line, along-wall unit, into-room unit, wall length) for a side."""
        lo, hi = self.lo, self.hi
        if side == 0:
            return (lo[0], lo[2]), (1, 0), (0, 1), hi[0] - lo[0]
        if side == 1:
            return (hi[0], hi[2]), (-1, 0), (0, -1), hi[0] - lo[0]
        if side == 2:
            return (lo[0], hi[2]), (0, -1), (1, 0), hi[2] - lo[2]
        return (hi[0], lo[2]), (0, 1), (-1, 0), hi[2] - lo[2]

    def clear(self, x0, z0, x1, z1, y_lo, y_hi, keep=True):
        """Is this floor rectangle free of everything (and inside the room)?"""
        if x0 < self.lo[0] or x1 > self.hi[0] or z0 < self.lo[2] or z1 > self.hi[2]:
            return False
        for b in self.objs:
            (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
            if py + sy / 2 <= y_lo or py - sy / 2 >= y_hi:
                continue
            if abs(b.get("r", [0, 0, 0])[1]) % 180 > 1:
                h = math.hypot(sx, sz) / 2
                sx = sz = 2 * h
            if px + sx / 2 > x0 and px - sx / 2 < x1 and pz + sz / 2 > z0 and pz - sz / 2 < z1:
                return False
        if keep:
            for (cx, cz, r) in self.keep + [(x, z, DOOR_CLEAR) for x, z in self.doorways]:
                nx, nz = min(max(cx, x0), x1), min(max(cz, z0), z1)
                if math.hypot(nx - cx, nz - cz) < r:
                    return False
        return True

    def floored(self, x0, z0, x1, z1):
        for x, z in ((x0 + 0.1, z0 + 0.1), (x1 - 0.1, z0 + 0.1), (x0 + 0.1, z1 - 0.1), (x1 - 0.1, z1 - 0.1)):
            f = self.floor_at(x, z)
            if f is None or abs(f - self.y0) > 0.06:
                return False
        return True


def _world(room, side, along, out, local):
    (ox, oz), (ux, uz), (vx, vz), _ = room.frame(side)
    x, y, z = local
    i = room.inset[side]
    return ox + ux * (along + x) + vx * (i + z), room.y0 + y, oz + uz * (along + x) + vz * (i + z)


TURN = (0, 180, 90, -90)  # how far a piece is turned to face out from each wall


def _size(side, s):
    """The piece's footprint in the world (for keeping later pieces clear of it)."""
    return (s[0], s[1], s[2]) if side in (0, 1) else (s[2], s[1], s[0])


def _rect(room, side, along, w, d):
    (ox, oz), (ux, uz), (vx, vz), _ = room.frame(side)
    xs, zs = [], []
    for a in (along - w / 2, along + w / 2):
        for b in (room.inset[side] - 0.05, room.inset[side] + d):
            xs.append(ox + ux * a + vx * b)
            zs.append(oz + uz * a + vz * b)
    return min(xs), min(zs), max(xs), max(zs)


def _backed(room, side, along, w, h):
    (ox, oz), (ux, uz), _, _ = room.frame(side)
    heights = [0.5] + ([1.5] if h > 1.05 else []) + ([2.0] if h > 1.8 else [])
    for f in (-0.45, 0.0, 0.45):
        a = along + f * w
        x, z = ox + ux * a, oz + uz * a
        for y in heights:
            if not room.solid_at(x, room.y0 + y, z):
                return False
    return True


def _emit(L, room, name, side, along, parts, level):
    for part in parts:
        pname, shape, p, s, c, mode = part[:6]
        rx, ry, rz = part[6] if len(part) > 6 else (0, 0, 0)
        ry = (ry + TURN[side] + 180) % 360 - 180
        pos = [round(v, 3) for v in _world(room, side, along, 0, p)]
        b = {"n": f"{name}{pname}", "t": shape, "p": pos, "s": [round(v, 3) for v in s], "r": [round(rx, 1), round(ry, 1), round(rz, 1)],
             "c": c, "m": mode, "l": level, "g": "furniture"}
        if mode == "emissive":
            b["e"] = 1.2
        L["boxes"].append(b)
        if mode == "solid":
            room.objs.append({"n": b["n"], "p": pos, "s": list(_size(side, s)), "r": [0, 0, 0], "g": "furniture", "m": "solid"})


def _place_wall(L, room, piece, k, tag, level, rng_key):
    w, d, h, parts = piece(k)
    sides = list(range(4))
    start = _roll(rng_key, "side") % 4
    sides = sides[start:] + sides[:start]
    for side in sides:
        _, _, _, length = room.frame(side)
        steps = int((length - w) / STEP)
        if steps < 1:
            continue
        offs = list(range(steps + 1))
        s0 = _roll(rng_key, side) % (steps + 1)
        offs = offs[s0:] + offs[:s0]
        for i in offs:
            along = w / 2 + 0.15 + i * STEP
            if along + w / 2 > length - 0.15:
                continue
            x0, z0, x1, z1 = _rect(room, side, along, w, d)
            fx0, fz0, fx1, fz1 = _rect(room, side, along, w + 0.1, d + WALK)
            if not room.clear(x0, z0, x1, z1, room.y0 + 0.05, room.y0 + h):
                continue
            if not room.clear(fx0, fz0, fx1, fz1, room.y0 + 0.05, room.y0 + 1.8, keep=True):
                continue
            if not room.floored(x0, z0, x1, z1) or not _backed(room, side, along, w, h):
                continue
            _emit(L, room, tag, side, along, parts, level)
            return True
    return False


def _place_art(L, room, n, tag, level, key):
    """Framed paintings and the odd sconce, on bare solid wall above whatever stands below."""
    placed = 0
    for side in range(4):
        (ox, oz), (ux, uz), (vx, vz), length = room.frame(side)
        i = 0.9 + (_roll(key, side) % 4) * 0.4
        while i < length - 0.9 and placed < n:
            x, z = ox + ux * i, oz + uz * i
            y = room.y0 + 1.75
            ok = all(room.solid_at(ox + ux * (i + f), y + dy, oz + uz * (i + f)) for f in (-0.45, 0, 0.45) for dy in (-0.4, 0.4))
            if ok:
                # nothing tall in front of it
                x0, z0, x1, z1 = _rect(room, side, i, 1.0, 0.4)
                if room.clear(x0 - 0.05, z0 - 0.05, x1 + 0.05, z1 + 0.05, room.y0 + 1.25, room.y0 + 2.3, keep=False):
                    r = _roll(key, side, int(i * 4))
                    fw, fh = 0.7 + (r % 3) * 0.15, 0.55 + (r // 3 % 3) * 0.12
                    parts = [("Frame", "rbox", (0, 1.75, -0.025), (fw, fh, 0.05), BRASS if r % 2 else WOOD[r % 5], "nocollide"),
                             ("Canvas", "box", (0, 1.75, 0.004), (fw - 0.12, fh - 0.12, 0.01), PAINT[r % len(PAINT)], "nocollide"),
                             ("Moon", "sphere", ((r % 5 - 2) * 0.05, 1.75 + fh * 0.18, 0.012), (0.1, 0.1, 0.01), CREAM, "nocollide"),
                             ("Hill", "sphere", (0, 1.75 - fh * 0.3, 0.011), (fw - 0.16, fh * 0.35, 0.01), _hex("2a3a2a"), "nocollide")]
                    _emit(L, room, f"{tag}Art{placed}", side, i, parts, level)
                    if r % 3 == 0:
                        _emit(L, room, f"{tag}Sconce{placed}", side, i + fw / 2 + 0.35,
                              [("Plate", "rbox", (0, 2.0, -0.03), (0.1, 0.2, 0.04), BRASS, "nocollide"),
                               ("Flame", "sphere", (0, 2.17, 0.03), (0.06, 0.1, 0.06), WARM, "emissive")], level)
                    placed += 1
                    i += 2.4
                    continue
            i += 0.5
    return placed


def _place_rug(L, room, tag, level, key):
    cx, cz = (room.lo[0] + room.hi[0]) / 2, (room.lo[2] + room.hi[2]) / 2
    w = min(3.2, (room.hi[0] - room.lo[0]) * 0.5)
    d = min(2.4, (room.hi[2] - room.lo[2]) * 0.5)
    if w < 1.2 or d < 1.0:
        return False
    if not room.floored(cx - w / 2, cz - d / 2, cx + w / 2, cz + d / 2):
        return False
    if not room.clear(cx - w / 2, cz - d / 2, cx + w / 2, cz + d / 2, room.y0 + 0.01, room.y0 + 0.06, keep=False):
        return False
    r = _roll(key, "rug")
    c, c2 = CLOTH[r % 7], CLOTH[(r // 7) % 7]
    y = room.y0
    L["boxes"].append({"n": f"{tag}Rug", "t": "rbox", "p": [round(cx, 3), round(y + 0.012, 3), round(cz, 3)], "s": [round(w, 3), 0.02, round(d, 3)],
                       "r": [0, 0, 0], "c": c, "m": "nocollide", "l": level, "g": "furniture"})
    L["boxes"].append({"n": f"{tag}RugBorder", "t": "rbox", "p": [round(cx, 3), round(y + 0.016, 3), round(cz, 3)], "s": [round(w - 0.3, 3), 0.02, round(d - 0.3, 3)],
                       "r": [0, 0, 0], "c": c2, "m": "nocollide", "l": level, "g": "furniture"})
    L["boxes"].append({"n": f"{tag}RugMiddle", "t": "rbox", "p": [round(cx, 3), round(y + 0.02, 3), round(cz, 3)], "s": [round(w - 0.5, 3), 0.02, round(d - 0.5, 3)],
                       "r": [0, 0, 0], "c": c, "m": "nocollide", "l": level, "g": "furniture"})
    return True


# --- round 46: curtains at the windows and things left out on tables -------------------------
DRAPES = [_hex(h) for h in ("7a2e3a", "2e4a6a", "4a6a3a", "8a6a2a", "5a3a6a", "c8b088", "6a2a2a")]


def _curtains(L, room, tag, level):
    """Drapes either side of every window in the room, on a brass rod, tied back."""
    made = 0
    lo, hi = room.lo, room.hi
    for b in list(L["boxes"]):
        if b["m"] != "glass" or b["g"] != "wall":
            continue
        (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
        along_x = sx > sz
        # which way is indoors: the side whose point is in this room
        for out in (-1, 1):
            ix, iz = (px, pz + out * 0.5) if along_x else (px + out * 0.5, pz)
            if lo[0] < ix < hi[0] and lo[2] < iz < hi[2] and room.y0 - 0.1 < py - sy / 2 < room.y0 + 2.0:
                break
        else:
            continue
        side = (0 if out > 0 else 1) if along_x else (2 if out > 0 else 3)
        (ox, oz), (ux, uz), _, _ = room.frame(side)
        centre = (px - ox) * ux + (pz - oz) * uz  # how far along the wall the window sits
        width = sx if along_x else sz
        top, bottom = py + sy / 2 - room.y0, py - sy / 2 - room.y0
        r = _roll(tag, round(px, 1), round(pz, 1))
        c = DRAPES[r % len(DRAPES)]
        name = f"{tag}Curtain{made}"
        drop = max(1.0, top + 0.18 - max(0.05, bottom - 0.25))
        parts = [("Rod", "rcyl", (0, top + 0.2, 0.06), (0.04, width / 2 + 0.45, 0.04), BRASS, "nocollide", (0, 0, 90)),
                 ("FinialL", "sphere", (-(width / 2 + 0.45), top + 0.2, 0.06), (0.08, 0.08, 0.08), BRASS, "nocollide"),
                 ("FinialR", "sphere", (width / 2 + 0.45, top + 0.2, 0.06), (0.08, 0.08, 0.08), BRASS, "nocollide"),
                 ("Valance", "rbox", (0, top + 0.1, 0.1), (width + 0.5, 0.2, 0.05), c, "nocollide")]
        for k, sgn in (("L", -1), ("R", 1)):
            x = sgn * (width / 2 + 0.18)
            parts.append((f"Drape{k}", "rbox", (x, top + 0.18 - drop / 2, 0.09), (0.34, drop, 0.06), c, "nocollide"))
            parts.append((f"Fold{k}", "rcyl", (x - sgn * 0.06, top + 0.18 - drop / 2, 0.12), (0.06, drop / 2 - 0.02, 0.04), c, "nocollide"))
            parts.append((f"Tie{k}", "rcyl", (x, top - drop * 0.55, 0.12), (0.2, 0.03, 0.1), BRASS, "nocollide"))
        _emit(L, room, name, side, centre, parts, level)
        made += 1
    return made


def _things(k):
    """A little still life for a table top: (name, shape, (dx, dy, dz), size, colour, mode) from the spot."""
    china = _hex("ece8f0")
    sets = [
        [("Cup", "rcyl", (0, 0.05, 0), (0.08, 0.05, 0.08), china, "nocollide"), ("Saucer", "rcyl", (0, 0.008, 0), (0.15, 0.008, 0.15), china, "nocollide"),
         ("Tea", "rcyl", (0, 0.095, 0), (0.07, 0.004, 0.07), _hex("7a4a2a"), "nocollide")],
        [("Books", "rbox", (0, 0.05, 0), (0.24, 0.1, 0.18), BOOKS[k % len(BOOKS)], "nocollide", (0, 15, 0)),
         ("BookTop", "rbox", (0.01, 0.13, 0), (0.2, 0.06, 0.15), BOOKS[(k + 3) % len(BOOKS)], "nocollide", (0, -10, 0))],
        [("Candle", "rcyl", (0, 0.1, 0), (0.05, 0.1, 0.05), CREAM, "nocollide"), ("Holder", "rcyl", (0, 0.01, 0), (0.12, 0.01, 0.12), BRASS, "nocollide"),
         ("Flame", "sphere", (0, 0.24, 0), (0.04, 0.07, 0.04), WARM, "emissive")],
        [("Vase", "sphere", (0, 0.12, 0), (0.14, 0.24, 0.14), _hex("4a6a8a"), "nocollide"),
         ("Flowers", "sphere", (0, 0.3, 0), (0.2, 0.14, 0.2), (_hex("d8641e"), _hex("e0a028"), _hex("c8401e"))[k % 3], "nocollide"),
         ("Leaves", "sphere", (0.05, 0.26, 0.03), (0.14, 0.08, 0.12), GREEN, "nocollide")],
        [("Plate", "rcyl", (0, 0.01, 0), (0.26, 0.01, 0.26), china, "nocollide"), ("Pie", "rcyl", (0, 0.04, 0), (0.2, 0.03, 0.2), _hex("c8904a"), "nocollide")],
        [("Teapot", "sphere", (0, 0.09, 0), (0.18, 0.16, 0.16), china, "nocollide"), ("Spout", "rcyl", (0.1, 0.12, 0), (0.03, 0.05, 0.03), china, "nocollide", (0, 0, -50)),
         ("Lid", "sphere", (0, 0.18, 0), (0.06, 0.04, 0.06), china, "nocollide")],
        [("Lamp", "sphere", (0, 0.1, 0), (0.14, 0.2, 0.14), _hex("8a6a3a"), "nocollide"), ("Shade", "rcyl", (0, 0.27, 0), (0.28, 0.08, 0.28), WARM, "emissive")],
        [("Letter", "box", (0, 0.003, 0), (0.2, 0.004, 0.14), CREAM, "nocollide", (0, 20, 0)), ("Pen", "rcyl", (0.06, 0.008, 0.02), (0.012, 0.07, 0.012), IRON, "nocollide", (0, 30, 90)),
         ("Glasses", "rcyl", (-0.06, 0.012, -0.03), (0.06, 0.006, 0.05), BRASS, "nocollide")],
        [("Pumpkin", "sphere", (0, 0.08, 0), (0.2, 0.16, 0.2), _hex("d8641e"), "nocollide"), ("Stem", "rcyl", (0, 0.18, 0), (0.025, 0.03, 0.025), _hex("4a3a1a"), "nocollide")],
    ]
    return sets[k % len(sets)]


def _clutter(L, room, tag, level):
    """Little things left out on the room's tables, desks, counters and sideboards."""
    made = 0
    tops = []
    for b in list(L["boxes"]):
        if b["g"] != "furniture" or b["m"] != "solid" or b["t"] not in ("box", "rbox", "rcyl", "cyl"):
            continue
        if abs(b.get("r", [0, 0, 0])[1]) % 90 > 1:
            continue
        (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
        if not (room.lo[0] < px < room.hi[0] and room.lo[2] < pz < room.hi[2]):
            continue
        hy = sy if b["t"] in ("cyl", "rcyl") else sy / 2
        top = py + hy - room.y0
        if abs(b.get("r", [0, 0, 0])[1]) % 180 > 1:
            sx, sz = sz, sx
        if not (0.55 <= top <= 1.15) or sx * sz < 0.25 or min(sx, sz) < 0.4:
            continue
        tops.append((b, px, py + hy, pz, sx, sz))
    for b, px, ty, pz, sx, sz in tops:
        # what already sits on this top
        sitting = [o for o in L["boxes"] if o is not b and abs((o["p"][1] - o["s"][1] / 2) - ty) < 0.12
                   and abs(o["p"][0] - px) < sx / 2 and abs(o["p"][2] - pz) < sz / 2]
        r = _roll(tag, b["n"])
        n = (2 + r % 3 if sx * sz > 1.2 else 1 + r % 3) if sx * sz > 0.6 else 1
        spots = [(-0.3, -0.2), (0.28, 0.15), (0.0, 0.25), (-0.15, 0.1), (0.3, -0.25)]
        for i in range(n):
            fx, fz = spots[(r + i) % len(spots)]
            x, z = px + fx * (sx - 0.3), pz + fz * (sz - 0.3)
            if any(abs(o["p"][0] - x) < o["s"][0] / 2 + 0.18 and abs(o["p"][2] - z) < o["s"][2] / 2 + 0.18 for o in sitting):
                continue
            for part in _things(r // 7 + i):
                pname, shape, (dx, dy, dz), size, c, mode = part[:6]
                rot = part[6] if len(part) > 6 else (0, 0, 0)
                hy = size[1] if shape in ("cyl", "rcyl") else size[1] / 2
                q = {"n": f"{tag}On{b['n']}{i}{pname}", "t": shape, "p": [round(x + dx, 3), round(ty + dy - (size[1] / 2 if shape not in ("cyl", "rcyl") else size[1]) + hy + 0.0, 3), round(z + dz, 3)],
                     "s": [round(v, 3) for v in size], "r": list(rot), "c": c, "m": mode, "l": level, "g": "furniture"}
                # sit the thing's base on the table top: dy is measured from the top to the thing's centre
                q["p"][1] = round(ty + dy, 3)
                if mode == "emissive":
                    q["e"] = 1.2
                L["boxes"].append(q)
                sitting.append(q)
            made += 1
    return made


def furnish(L):
    """Dresses every indoor room in the layout. Returns {room name: pieces added}."""
    out = {}
    for r in L.get("rooms", []):
        if r.get("l", 0) == 9:
            continue
        room = Room(L, r)
        area = (room.hi[0] - room.lo[0]) * (room.hi[2] - room.lo[2])
        tag = "Detail" + re.sub(r"[^A-Za-z0-9]", "", r["n"])
        kinds = next(k for pat, k in ROOMS if re.search(pat, r["n"].lower()))
        target = max(3, min(9, int(area / 9)))
        made = 0
        have = " ".join(b["n"].lower() for b in room.solid if b["g"] == "furniture") + " " + " ".join(
            p["n"].lower() for p in L.get("possessables", []) if room.lo[0] <= p["p"][0] <= room.hi[0] and room.lo[2] <= p["p"][2] <= room.hi[2] and room._here(p["p"]))
        used = set()
        for i in range(target + 6):
            if made >= target:
                break
            piece = kinds[i % len(kinds)]
            if piece in ONCE and (piece in used or any(w in have for w in ONCE[piece])):
                continue  # one bed (or piano, desk, stove...) to a room, and none if it already has one
            used.add(piece)
            key = (L.get("id", L.get("name", "")), r["n"], i)
            if _place_wall(L, room, piece, _roll(*key) % 97, f"{tag}{piece.__name__.title().replace('_', '')}{i}", r["l"], key):
                made += 1
        art = _place_art(L, room, max(1, min(4, int(area / 30))), tag, r["l"], (r["n"], "art"))
        rug = _place_rug(L, room, tag, r["l"], r["n"])
        drapes = _curtains(L, room, tag, r["l"])
        things = _clutter(L, room, tag, r["l"])
        out[r["n"]] = (made, art, int(rug), drapes, things)
    return out
