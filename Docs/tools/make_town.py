#!/usr/bin/env python3
"""
Designs Hollow Creek, the little town the mysteries happen in, and writes it to
Assets/Unmasked/Resources/HollowCreek.json.

The Solvers start each night at Mystery Club HQ. A call comes in, they pile into the van and drive
across town to the haunted house: a cottage, a farm, a Victorian or Blackwood Manor at the end of
Main Street, over the creek. Every house is fully built on its own lot, so you can drive past the
others too. The town map in the game (M) and the README map are drawn from this file.

Run make_manor.py and make_houses.py first: the lots read the houses' JSON for their size.

    python3 Docs/tools/make_town.py
"""
import json
import math
import random
import os

import dressing as hw
from layoutlib import Layout, rgb, RESOURCES

T = Layout("Hollow Creek", "HollowCreek", "Town",
           "A sleepy river town on Halloween night. Mystery Club HQ is at the south end of Main Street.")
C = {"grass": rgb("27391f"), "road": rgb("2b2a30"), "line": rgb("d8c25a"), "walk": rgb("6e6a64"), "water": rgb("2d4f6e"),
     "wood": rgb("5b4027"), "trim": rgb("e8e0d0"), "roof": rgb("2e2a3a"), "brick": rgb("7a3e32"), "stone": rgb("8d8f94"),
     "hq": rgb("2f6a6a"), "hq_roof": rgb("e8731c"), "lot": rgb("3a3a40"), "iron": rgb("26262b"), "glass": rgb("ffcf7a")}
ROAD_W = 8.0

# ---------------------------------------------------------------------------
# The houses on the map. offset = where the house's local origin sits in town.
# ---------------------------------------------------------------------------
LOTS = [
    {"id": "PembertonCottage", "resource": "Houses/PembertonCottage", "offset": [70, 0, 24], "difficulty": 1,
     "street": "14 Elm Street"},
    {"id": "HollowCreekFarm", "resource": "Houses/HollowCreekFarm", "offset": [-90, 0, 26], "difficulty": 2,
     "street": "Old Mill Road"},
    {"id": "WillowLaneVictorian", "resource": "Houses/WillowLaneVictorian", "offset": [60, 0, 132], "difficulty": 3,
     "street": "3 Willow Lane"},
    {"id": "HistoricalSociety", "resource": "Houses/HistoricalSociety", "offset": [62, 0, -58], "difficulty": 5,
     "street": "1 Founders Way"},
    {"id": "BlackwoodManor", "resource": "BlackwoodManor", "offset": [0, 0, 250], "difficulty": 4,
     "street": "The end of Main Street", "name": "Blackwood Manor", "style": "Manor", "size": "Huge", "floors": 3,
     "blurb": "The old Blackwood estate past the creek: a cellar, two floors and a roof, a greenhouse, a "
              "cemetery and a pumpkin patch. Huge: the longest night."},
]


def load_house(lot):
    with open(os.path.join(RESOURCES, lot["resource"] + ".json")) as f:
        return json.load(f)


for lot in LOTS:
    H = load_house(lot)
    ox, _, oz = lot["offset"]
    if "lot" in H:
        (x0, z0), (x1, z1) = H["lot"]["min"], H["lot"]["max"]
    else:  # Blackwood Manor: its lawn is the lot
        lawn = [b for b in H["boxes"] if b["g"] == "ground"]
        x0 = min(b["p"][0] - b["s"][0] / 2 for b in lawn)
        x1 = max(b["p"][0] + b["s"][0] / 2 for b in lawn)
        z0 = min(b["p"][2] - b["s"][2] / 2 for b in lawn)
        z1 = max(b["p"][2] + b["s"][2] / 2 for b in lawn)
    lot.setdefault("name", H["name"])
    lot.setdefault("style", H.get("style", ""))
    lot.setdefault("size", H.get("size", ""))
    lot.setdefault("floors", H.get("floors", 1))
    lot.setdefault("blurb", H.get("blurb", ""))
    lot["lot"] = {"min": [x0 + ox, z0 + oz], "max": [x1 + ox, z1 + oz]}
    lot["center"] = [round(ox + (x0 + x1) / 2, 2), 0, round(oz + (z0 + z1) / 2, 2)]
    sp = H["solverSpawns"][0]["p"]
    lot["arrival"] = [round(ox + 0.0, 2), 0, round(oz + sp[2] - 3.0, 2)]  # where the van parks, at the gate
    # The street remembers (Town/HouseMood.cs): what goes up in the front yard once the house's case
    # is solved, between the gate and the porch. Hidden until then; the haunted look is lights only.
    gx, gz = lot["arrival"][0], lot["arrival"][2]
    front = [b["p"][2] - b["s"][2] / 2 + oz for b in H["boxes"]
             if b["g"] not in ("ground",) and abs(b["p"][0]) < 3 and b["p"][1] < 3 and b["p"][2] - b["s"][2] / 2 + oz > gz + 3.5]
    depth = min(6.0, (min(front) if front else gz + 8) - gz - 1.2)
    items = []
    for i in range(3):  # paper-bag lanterns lining the walk
        z = gz + 1.0 + i * (depth - 1.0) / 2
        items += [{"k": "luminaria", "p": [gx - 1.3, 0, round(z, 2)], "ry": 0, "sc": 1.0},
                  {"k": "luminaria", "p": [gx + 1.3, 0, round(z, 2)], "ry": 0, "sc": 1.0}]
    items += [{"k": "jack_grin", "p": [gx - 2.6, 0, gz + 0.6], "ry": 180, "sc": 0.9},
              {"k": "jack_wink", "p": [gx + 2.6, 0, gz + 0.6], "ry": 180, "sc": 0.9},
              {"k": "party_table", "p": [gx + 4.6, 0, round(gz + depth * 0.55, 2)], "ry": 180, "sc": 1.0},
              {"k": "pumpkin_stack", "p": [gx - 4.4, 0, round(gz + depth * 0.5, 2)], "ry": 20, "sc": 0.8}]
    lot["afterglow"] = {
        "items": items,
        "banner": [gx, 0, gz + 0.5],  # two posts either side of the gate, a cloth and a string of bulbs between
        "bannerWidth": 5.2,
        "bannerText": "THANK YOU, MYSTERY CLUB!",
        "haunt": [gx, 2.6, round(gz + depth * 0.5, 2)],  # the violet light over the yard while the call is open
    }
    lot["rooms"] = len(H["rooms"])
    lot["pieces"] = len(H["boxes"])
    lot["area"] = round((x1 - x0) * (z1 - z0))


# ---------------------------------------------------------------------------
# Ground, roads, the creek
# ---------------------------------------------------------------------------
TX0, TX1, TZ0, TZ1 = -170.0, 130.0, -110.0, 300.0
T.box("Ground", ((TX0 + TX1) / 2, -0.27, (TZ0 + TZ1) / 2), (TX1 - TX0, 0.5, TZ1 - TZ0), C["grass"], 9, "solid", "ground")


def road(name, x0, z0, x1, z1, w=ROAD_W, dashes=True):
    """A straight road from (x0, z0) to (x1, z1), axis-aligned."""
    along_x = abs(x1 - x0) > abs(z1 - z0)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    length = abs(x1 - x0) if along_x else abs(z1 - z0)
    size = (length, 0.1, w) if along_x else (w, 0.1, length)
    T.box(name, (cx, -0.03, cz), size, C["road"], 9, "solid", "road")
    for side in (-1, 1):  # sidewalks
        off = side * (w / 2 + 0.9)
        p = (cx, 0.0, cz + off) if along_x else (cx + off, 0.0, cz)
        s = (length, 0.12, 1.8) if along_x else (1.8, 0.12, length)
        T.box(f"{name}Walk{'LR'[side > 0]}", p, s, C["walk"], 9, "solid", "road")
    if dashes:
        n = int(length / 6)
        for i in range(n):
            a = -length / 2 + 3 + i * 6
            p = (cx + a, 0.025, cz) if along_x else (cx, 0.025, cz + a)
            s = (2.4, 0.02, 0.18) if along_x else (0.18, 0.02, 2.4)
            T.box(f"{name}Dash{i}", p, s, C["line"], 9, "nocollide", "road")
    T.room(name, 9, min(x0, x1) - w / 2 - 2, max(x0, x1) + w / 2 + 2, min(z0, z1) - w / 2 - 2, max(z0, z1) + w / 2 + 2, -2, 12)


road("Main Street", 0, -96, 0, 207)
road("Elm Street", -125, 0, 100, 0)
road("Willow Lane", 4, 106, 96, 106)
road("Founders Way", 4, -84, 104, -84)  # out to the Historical Society
for lot in [lot for lot in LOTS if lot["id"] != "BlackwoodManor"]:  # driveways from the road to each gate
    gx, gz = lot["offset"][0], lot["lot"]["min"][1]
    T.box(f"Drive_{lot['id']}", (gx, -0.02, gz - 2.5), (5.0, 0.1, 5.2), C["road"], 9, "solid", "road")

# The creek, with a bridge where Main Street crosses it
CREEK_Z = 185.0
T.box("Creek", ((TX0 + TX1) / 2, -0.04, CREEK_Z), (TX1 - TX0, 0.06, 10.0), C["water"], 9, "nocollide", "water")
T.box("BridgeDeck", (0, 0.12, CREEK_Z), (ROAD_W + 2, 0.3, 14.0), C["wood"], 9, "solid", "road")
for side in (-1, 1):
    T.box(f"BridgeRail{side}", (side * (ROAD_W / 2 + 0.8), 0.9, CREEK_Z), (0.2, 1.2, 14.0), C["wood"], 9, "solid", "fence")
    for k in range(5):
        T.box(f"BridgePost{side}{k}", (side * (ROAD_W / 2 + 0.8), 0.7, CREEK_Z - 6 + k * 3), (0.35, 1.6, 0.35), C["wood"], 9, "solid", "fence")
T.room("Hollow Creek Bridge", 9, -12, 12, CREEK_Z - 9, CREEK_Z + 9, -2, 12)

# ---------------------------------------------------------------------------
# Buildings: helpers
# ---------------------------------------------------------------------------


def building(name, x0, x1, z0, z1, h, wall, roof, door_side, gable=True, windows=True, sign=None, level=9):
    """A closed town building (not explorable) with glowing windows and a door facing the street."""
    T.box(f"{name}Body", ((x0 + x1) / 2, h / 2, (z0 + z1) / 2), (x1 - x0, h, z1 - z0), wall, level, "solid", "building")
    if gable:
        T.gable_roof(f"{name}Roof", x0, x1, z0, z1, h, min(4.0, (z1 - z0) * 0.35), roof, wall, level=level, overhang=0.4)
    else:
        T.box(f"{name}Roof", ((x0 + x1) / 2, h + 0.3, (z0 + z1) / 2), (x1 - x0 + 0.4, 0.6, z1 - z0 + 0.4), roof, level, "solid", "roof")
    floors = max(1, int(h // 3))
    if windows:
        for side in ("S", "N", "W", "E"):
            along_x = side in ("S", "N")
            a0, a1 = (x0, x1) if along_x else (z0, z1)
            n = max(1, int((a1 - a0) / 3.5))
            for f in range(floors):
                for i in range(n):
                    a = a0 + (i + 0.5) * (a1 - a0) / n
                    y = 1.7 + f * 3.0
                    if side == door_side and f == 0 and abs(a - (a0 + a1) / 2) < 1.5:
                        continue
                    lit = (hash((name, side, f, i)) % 3) != 0
                    col = C["glass"] if lit else rgb("3a4660")
                    if along_x:
                        p = (a, y, (z0 if side == "S" else z1) + (-0.05 if side == "S" else 0.05))
                        s = (1.1, 1.3, 0.06)
                    else:
                        p = ((x0 if side == "W" else x1) + (-0.05 if side == "W" else 0.05), y, a)
                        s = (0.06, 1.3, 1.1)
                    T.box(f"{name}Win{side}{f}{i}", p, s, col, level, "glass" if lit else "solid", "window")
    mid = ((x0 + x1) / 2, (z0 + z1) / 2)
    door = {"S": ((mid[0], 1.15, z0 - 0.06), (1.4, 2.3, 0.08)), "N": ((mid[0], 1.15, z1 + 0.06), (1.4, 2.3, 0.08)),
            "W": ((x0 - 0.06, 1.15, mid[1]), (0.08, 2.3, 1.4)), "E": ((x1 + 0.06, 1.15, mid[1]), (0.08, 2.3, 1.4))}[door_side]
    T.box(f"{name}Door", door[0], door[1], rgb("4a2a1a"), level, "solid", "door")
    if sign:
        txt, col = sign
        p, s = door
        off = {"S": (0, 0, -0.1), "N": (0, 0, 0.1), "W": (-0.1, 0, 0), "E": (0.1, 0, 0)}[door_side]
        big = (3.2, 0.8, 0.12) if door_side in ("S", "N") else (0.12, 0.8, 3.2)
        T.box(f"{name}Sign", (p[0] + off[0], min(h - 0.6, 3.1), p[2] + off[2]), big, col, level, "emissive", "sign")
        T.glow((p[0] + off[0] * 8, 3.0, p[2] + off[2] * 8), col, 7, 0.8)


def street_lamps(name, x0, z0, x1, z1, every=22.0, side_off=ROAD_W / 2 + 1.6):
    along_x = abs(x1 - x0) > abs(z1 - z0)
    length = abs(x1 - x0) if along_x else abs(z1 - z0)
    n = int(length / every)
    for i in range(n + 1):
        f = i / max(1, n)
        x, z = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
        s = 1 if i % 2 == 0 else -1
        if along_x:
            p, ry = (x, 0, z + s * side_off), (180 if s > 0 else 0)
        else:
            p, ry = (x + s * side_off, 0, z), (-90 if s > 0 else 90)
        T.decor("streetlamp", p, ry)
        a = math.radians(ry)
        T.glow((p[0] + math.sin(a) * 0.7, 3.8, p[2] + math.cos(a) * 0.7), rgb("ffcf7a"), 13, 1.1)


# ---------------------------------------------------------------------------
# Mystery Club HQ: where every night starts
# ---------------------------------------------------------------------------
HX0, HX1, HZ0, HZ1, HH = -30.0, -16.0, -82.0, -66.0, 4.2
T.slab("HQFloor", 0.05, HX0, HX1, HZ0, HZ1, [], rgb("5a4a3a"), 0, 0.1)
T.box("ParkingLot", (-10.0, -0.02, -74.0), (12.0, 0.1, 18.0), C["lot"], 9, "solid", "road")
for i in range(4):
    T.box(f"ParkingLine{i}", (-10.0, 0.04, -81.0 + i * 4.5), (8.0, 0.02, 0.15), C["trim"], 9, "nocollide", "road")


def hq_wall(name, axis, fixed, a0, a1, openings):
    T.wall(name, axis, fixed, a0, a1, 0.0, HH, 0, C["hq"], 0.3, openings, trim=C["trim"])


hq_wall("HQ_S", "x", HZ0, HX0 - 0.15, HX1 + 0.15, [(-26.0, 1.4, 1.0, 2.6, "window"), (-20.0, 1.4, 1.0, 2.6, "window")])
hq_wall("HQ_N", "x", HZ1, HX0 - 0.15, HX1 + 0.15, [(-26.0, 1.4, 1.0, 2.6, "window"), (-20.0, 1.4, 1.0, 2.6, "window")])
hq_wall("HQ_W", "z", HX0, HZ0 + 0.15, HZ1 - 0.15, [(-74.0, 2.0, 1.0, 2.6, "window")])
hq_wall("HQ_E", "z", HX1, HZ0 + 0.15, HZ1 - 0.15, [(-74.0, 3.6, 0.0, 3.2, "door"), (-79.0, 1.6, 1.0, 2.6, "window"),
                                                   (-69.0, 1.6, 1.0, 2.6, "window")])
T.box("HQRoof", ((HX0 + HX1) / 2, HH + 0.15, (HZ0 + HZ1) / 2), (HX1 - HX0 + 1.2, 0.3, HZ1 - HZ0 + 1.2), C["hq_roof"], 2, "solid", "roof")
T.box("HQSign", (HX1 + 0.25, HH - 0.2, -74.0), (0.15, 1.0, 6.0), rgb("f6e27a"), 9, "emissive", "sign")
T.box("HQLogo", (HX1 + 0.35, HH - 0.2, -74.0), (0.1, 1.6, 1.6), C["hq_roof"], 9, "solid", "sign", "cyl", r=(0, 0, 90))
T.glow((HX1 + 2.5, 3.5, -74.0), rgb("f6e27a"), 10, 1.2)
T.door((HX1, 0.05, -75.8), 0, 1.8, 0, "Door_HQ_L")
T.door((HX1, 0.05, -72.2), 180, 1.8, 0, "Door_HQ_R")
T.box("Couch", (-27.5, 0.45, -70.0), (1.0, 0.9, 3.0), rgb("c8732c"), 0, "solid", "furniture")
T.table("MapTable", (-23.0, 0.05, -74.0), (3.0, 0.85, 2.0), 0, C["wood"], C["wood"])
T.box("MapTop", (-23.0, 0.92, -74.0), (2.8, 0.02, 1.8), rgb("e8dcb8"), 0, "nocollide", "decor")
T.box("SnackBar", (-19.0, 0.55, -80.8), (5.0, 1.1, 0.8), rgb("8a2a2a"), 0, "solid", "furniture")
T.box("Lockers", (-29.6, 1.1, -78.0), (0.6, 2.2, 4.0), rgb("4a5a6a"), 0, "solid", "furniture")
T.decor("callboard", (-29.3, 0.05, -74.0), 90)
# The keepsake shelf: something from every solved case sits here (KeepsakeDisplay in Unity)
T.box("KeepsakeShelf", (-23.0, 1.15, -66.4), (3.6, 0.08, 0.45), C["wood"], 0, "solid", "furniture")
T.box("KeepsakeShelf_L", (-24.75, 0.575, -66.4), (0.08, 1.15, 0.45), C["wood"], 0, "solid", "furniture")
T.box("KeepsakeShelf_R", (-21.25, 0.575, -66.4), (0.08, 1.15, 0.45), C["wood"], 0, "solid", "furniture")
T.box("KeepsakePlaque", (-23.0, 1.75, -66.17), (1.6, 0.35, 0.04), rgb("e8dcb8"), 0, "nocollide", "decor")
T.decor("jack", (-19.0, 1.1, -80.8), 180, 0.6)
T.decor("candle", (-23.0, 0.95, -74.4), 0)
T.light("HQ Light", (-23.0, 3.8, -74.0), rgb("fff0c8"), 14, 1.4, 0, "cyl", (0, 0.2, 0), (0.8, 0.15, 0.8))
T.light("HQ Lamp", (-27.5, 1.6, -68.0), rgb("ffd8a0"), 7, 1.0, 0, "cyl", (0, -0.8, 0), (0.08, 0.8, 0.08))
T.room("Mystery Club HQ", 0, HX0, HX1, HZ0, HZ1, -1, HH)
T.room("HQ Parking", 9, -16, -4, -83, -65, -2, 10)
T.L["hq"] = {
    "spawns": [{"p": [-25.0 + (i % 2) * 2.5, 0.15, -70.0 - (i // 2) * 2.5]} for i in range(4)],
    "haunter": {"p": [-26.0, 1.0, -79.0]},
    "van": {"p": [-10.0, 0.1, -76.0], "ry": 90.0},
    "board": {"p": [-29.3, 0.05, -74.0], "ry": 90.0},
    # The dressing-up trunk (Town/CostumeTrunk.cs): put on or take off the Lantern Watch costume
    "trunk": {"p": [-18.0, 0.05, -67.3], "ry": 180.0},
    # One spot on the keepsake shelf per case, in the order the cases get harder
    "keepsakes": [{"house": h, "p": [-24.4 + i * 0.7, 1.19, -66.4]}
                  for i, h in enumerate(["PembertonCottage", "HollowCreekFarm", "WillowLaneVictorian", "BlackwoodManor",
                                         "HistoricalSociety"])],
}

# ---------------------------------------------------------------------------
# Downtown: shops along Main Street and the town square
# ---------------------------------------------------------------------------
SHOPS = [  # name, x0, x1, z0, z1, h, wall, roof, door side, sign colour
    ("Diner", 7, 19, -50, -38, 4.0, rgb("c8c0b0"), rgb("8a2a2a"), "W", rgb("ff4a7a")),
    ("General Store", 7, 21, -32, -18, 5.5, rgb("8a6a4a"), rgb("3a2e2a"), "W", rgb("9dff8a")),
    ("Post Office", 7, 17, -64, -54, 4.5, rgb("7a4a3a"), C["roof"], "W", rgb("7ab0ff")),
    ("Hardware", -19, -7, -58, -46, 4.5, rgb("5a6a7a"), C["roof"], "E", rgb("ffb347")),
    ("Bookshop", -16, -7, -45, -36, 6.5, rgb("6a4a6a"), rgb("2a2a3a"), "E", rgb("e8a0ff")),
    ("Barber", -16, -7, -96, -88, 4.0, rgb("8a8f94"), C["roof"], "E", rgb("ff6a6a")),
    ("Library", 10, 26, 22, 36, 7.0, rgb("8a7a6a"), rgb("2a3a4a"), "W", rgb("ffe08a")),
    ("Fire Station", -26, -8, 22, 38, 6.0, rgb("8a2a24"), C["roof"], "E", rgb("ff6a3a")),
]
for name, x0, x1, z0, z1, h, wall, roof, side, sign in SHOPS:
    building(name.replace(" ", ""), x0, x1, z0, z1, h, wall, roof, side, gable=h < 5, sign=(name, sign))
    T.room(name, 9, x0, x1, z0, z1, -1, h + 4)

# Church with a steeple, west of Main Street
building("Church", -34, -18, 56, 80, 7.0, rgb("b8b0a0"), rgb("2a2a3a"), "E")
for i in range(6):
    w = 3.6 * (1 - i / 6) + 0.2
    T.box(f"Steeple{i}", (-15.0, 7.0 + i * 1.6 + 0.8, 68.0), (w, 1.6, w), rgb("b8b0a0") if i < 2 else rgb("2a2a3a"), 9, "solid", "roof")
T.box("SteepleBase", (-15.0, 3.5, 68.0), (3.8, 7.0, 3.8), rgb("b8b0a0"), 9, "solid", "building")
T.box("Cross", (-15.0, 17.6, 68.0), (0.15, 1.4, 0.15), C["iron"], 9, "solid", "roof")
T.room("Church", 9, -36, -12, 54, 82, -1, 20)
for i in range(12):  # churchyard
    x, z = -40 + (i % 4) * 3.0, 86 + (i // 4) * 3.0
    T.box(f"Headstone{i}", (x, 0.45, z), (0.7, 0.9, 0.18), C["stone"], 9, "solid", "grave")
    if i % 3 == 0:
        T.decor("candle", (x + 0.4, 0, z - 0.4), 0, 1.2)
        T.glow((x + 0.4, 0.4, z - 0.4), rgb("ffb347"), 3, 0.7)
T.room("Churchyard", 9, -42, -28, 84, 96, -1, 10)

# Filler houses: the rest of the neighbourhood (closed, but lit up for Halloween)
FILLER = [  # x0, x1, z0, z1, wall, roof, door side
    (-30, -18, 12, 20, rgb("7a8a9a"), rgb("3a2e2a"), "S"), (-50, -38, 12, 22, rgb("c8a06a"), rgb("4a2e2a"), "S"),
    (28, 40, 10, 20, rgb("9a7aa0"), rgb("2e2a3a"), "S"), (24, 36, -22, -12, rgb("a0b08a"), rgb("3a2e2a"), "N"),
    (40, 52, -22, -12, rgb("d0c0a0"), rgb("5a2a2a"), "N"), (-52, -40, -22, -12, rgb("8a9aa0"), rgb("2e2a3a"), "N"),
    (12, 24, 112, 122, rgb("b07a6a"), rgb("2e2a3a"), "S"), (12, 24, 92, 100, rgb("7a9a8a"), rgb("3a2e2a"), "N"),
    (-24, -10, 120, 132, rgb("a08a6a"), rgb("2e2a3a"), "E"), (-24, -10, 140, 152, rgb("6a7a9a"), rgb("3a2e2a"), "E"),
    (14, 26, 150, 162, rgb("8a6a6a"), rgb("2e2a3a"), "W"), (-76, -64, -22, -12, rgb("9a9a7a"), rgb("4a2e2a"), "N"),
]
for i, (x0, x1, z0, z1, wall, roof, side) in enumerate(FILLER):
    building(f"House{i}", x0, x1, z0, z1, 3.4, wall, roof, side)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    front = {"S": (cx, z0 - 1.2), "N": (cx, z1 + 1.2), "W": (x0 - 1.2, cz), "E": (x1 + 1.2, cz)}[side]
    ry = {"S": 180, "N": 0, "W": -90, "E": 90}[side]
    T.decor("jack", (front[0] - 0.9, 0, front[1]), ry, 0.8)
    T.decor("pumpkin", (front[0] + 0.9, 0, front[1]), ry + 30, 0.7)
    if i % 2 == 0:
        T.glow((front[0] - 0.9, 0.5, front[1]), rgb("ff9a3a"), 4, 0.8)
    if i % 3 == 0:
        T.tree(f"YardTree{i}", x1 + 2.5, z1 - 1.0, 6.0, rgb(["c04a2a", "d0662a", "b8862a"][i % 3]))

# Town square: a bandstand, the Harvest Festival stalls, string lights and a pumpkin pyramid
SQX0, SQX1, SQZ0, SQZ1 = -38.0, -8.0, -34.0, -8.0
T.box("Square", ((SQX0 + SQX1) / 2, -0.01, (SQZ0 + SQZ1) / 2), (SQX1 - SQX0, 0.1, SQZ1 - SQZ0), rgb("6a625a"), 9, "solid", "road")
BX, BZ = -23.0, -21.0
T.box("BandstandFloor", (BX, 0.3, BZ), (7.0, 0.6, 7.0), C["trim"], 9, "solid", "floor")
for i in range(8):
    a = math.radians(i * 45 + 22.5)
    T.box(f"BandstandPost{i}", (BX + 3.2 * math.cos(a), 1.9, BZ + 3.2 * math.sin(a)), (0.18, 2.6, 0.18), C["trim"], 9, "solid", "porch")
for i in range(5):
    w = 7.6 * (1 - i / 5) + 0.3
    T.box(f"BandstandRoof{i}", (BX, 3.3 + i * 0.35, BZ), (w, 0.35, w), rgb("8a2a2a") if i % 2 == 0 else C["trim"], 9, "solid", "roof",
          r=(0, 22.5 * (i % 2), 0))
for k, (x, z) in enumerate(((-34, -12), (-34, -30), (-12, -30))):
    T.box(f"Stall{k}", (x, 1.2, z), (3.0, 2.4, 2.2), C["wood"], 9, "solid", "furniture")
    T.box(f"StallRoof{k}", (x, 2.6, z), (3.4, 0.25, 2.6), [rgb("e8731c"), rgb("6a2a8a"), rgb("2f6a6a")][k], 9, "solid", "roof", r=(-12, 0, 0))
    T.decor("jack", (x, 1.25, z - 1.2), 180, 0.6)
    T.glow((x, 2.0, z - 1.6), rgb("ffb347"), 6, 0.9)
for i in range(10):  # pumpkin pyramid
    row = 0 if i < 6 else (1 if i < 9 else 2)
    idx = i if row == 0 else (i - 6 if row == 1 else 0)
    n = 3 - row
    x = BX + 7.5 + (idx % n - (n - 1) / 2) * 0.6
    z = BZ - 4.5 + (idx // n) * 0.55
    T.decor("jack" if row == 2 else "pumpkin", (x, row * 0.42, z), 180, 0.9)
T.glow((BX + 7.5, 1.4, BZ - 4.3), rgb("ff9a3a"), 6, 1.0)
# String lights from the bandstand's peak out to poles at the square's corners
for k, (x, z) in enumerate(((SQX0 + 1, SQZ0 + 1), (SQX1 - 1, SQZ0 + 1), (SQX0 + 1, SQZ1 - 1), (SQX1 - 1, SQZ1 - 1))):
    T.box(f"LightPole{k}", (x, 2.0, z), (0.14, 4.0, 0.14), C["iron"], 9, "solid", "decor")
    hw.string_lights(T, (BX, 4.7, BZ), (x, 3.9, z), 18, 0.6)
for i, (x, z, ry) in enumerate(((-36, -20, 90), (-10, -26, -90), (-23, -32, 0))):
    T.decor("bench", (x, 0, z), ry)
for x, z in ((-36, -33), (-10, -10), (-36, -10)):
    T.decor("haybale", (x, 0, z), 30)
    T.decor("scarecrow", (x + 1.5, 0, z), 180)
T.room("Town Square", 9, SQX0, SQX1, SQZ0, SQZ1, -1, 12)

# Nights of the Jack comes to town: an arch of jack-o'-lanterns into the square and a jack-o'-lantern tree
rng = random.Random(1031)
hw.jack_arch(T, SQX1 - 0.4, (SQZ0 + SQZ1) / 2, 3.8, 3.6, 90, rng=rng)
hw.jack_tree(T, -30.0, -27.5, 4.4, rng=rng)

# Lights strung across Main Street downtown, and a porch display at HQ
for z in (-50.0, -28.0, -6.0):
    for side in (-1, 1):
        T.box(f"StringPole{z}{side}", (side * 5.0, 2.4, z), (0.12, 4.8, 0.12), C["iron"], 9, "solid", "decor")
    hw.string_lights(T, (-5.0, 4.7, z), (5.0, 4.7, z), 16, 0.5)
hw.porch_display(T, HX1 + 0.8, 0.05, -74.0, 90, 4.0, rng=rng)

# A few neighbours went all out: string lights along the eaves and cornstalks by the door
for i, (x0, x1, z0, z1, wall, roof, side) in enumerate(FILLER):
    if i % 3 != 1:
        continue
    if side in ("S", "N"):
        z = z0 - 0.25 if side == "S" else z1 + 0.25
        hw.string_lights(T, (x0, 3.25, z), (x1, 3.25, z), 14, 0.25, colors=("bulb_orange", "bulb_purple"))
        for x in ((x0 + x1) / 2 - 1.6, (x0 + x1) / 2 + 1.6):
            T.decor("cornstalks", (x, 0, z - (0.4 if side == "S" else -0.4)), 0)
    else:
        x = x1 + 0.25 if side == "E" else x0 - 0.25
        hw.string_lights(T, (x, 3.25, z0), (x, 3.25, z1), 14, 0.25, colors=("bulb_orange", "bulb_green"))
        for z in ((z0 + z1) / 2 - 1.6, (z0 + z1) / 2 + 1.6):
            T.decor("cornstalks", (x + (0.4 if side == "E" else -0.4), 0, z), 0)

# Street lamps along every road
street_lamps("MainLamps", 0, -94, 0, 175)
street_lamps("MainLampsNorth", 0, 196, 0, 205, 9)
street_lamps("ElmLamps", -120, 0, 96, 0)
street_lamps("WillowLamps", 10, 106, 94, 106)
street_lamps("FoundersLamps", 10, -84, 100, -84)

# The woods around town
k = 0
for x in range(int(TX0) + 6, int(TX1) - 4, 13):
    for z in (TZ0 + 6, TZ1 - 6):
        T.tree(f"Wood{k}", x + (k % 3) * 2.0, z + (k % 2) * 3.0, 7.0 + (k % 4), None if k % 3 else rgb("6a3a2a"))
        k += 1
for z in range(int(TZ0) + 18, int(TZ1) - 12, 14):
    for x in (TX0 + 6, TX1 - 6):
        T.tree(f"Wood{k}", x + (k % 2) * 3.0, z + (k % 3) * 2.0, 7.0 + (k % 4), None if k % 3 else rgb("6a3a2a"))
        k += 1
for i, (x, z) in enumerate(((-60, 90), (-75, 140), (-110, 120), (90, 60), (100, 200), (-60, 200), (40, 200), (-140, -60),
                            (110, -30), (95, -40), (-80, -80), (-130, 160))):
    T.tree(f"Grove{i}", x, z, 8.0, None if i % 2 else rgb("8a4a2a"))

# Named zones for the map and "where am I?" (houses describe themselves)
T.room("Hollow Creek", 9, TX0, TX1, TZ0, TZ1, -5, 60)

# ---------------------------------------------------------------------------
# Special events: one may be rolled when a call comes in
# ---------------------------------------------------------------------------
T.L["events"] = [
    {"id": "BloodMoon", "name": "Blood Moon", "color": rgb("ff3a3a"),
     "blurb": "A red moon rises. The Haunter's ectoplasm refills faster and every scare hits harder."},
    {"id": "Thunderstorm", "name": "Thunderstorm", "color": rgb("9fd6ff"),
     "blurb": "Lightning lights up the house for a heartbeat. Lamps flicker and sometimes blow out."},
    {"id": "PeaSoupFog", "name": "Pea-Soup Fog", "color": rgb("bfe9de"),
     "blurb": "A thick fog rolls in off the creek. You can barely see the end of your flashlight beam."},
    {"id": "PowerOutage", "name": "Power Outage", "color": rgb("ffcf7a"),
     "blurb": "The whole street goes dark. Every lamp in the house starts off; flashlights drain faster."},
    {"id": "HarvestFestival", "name": "Harvest Festival", "color": rgb("e8731c"),
     "blurb": "The town is out celebrating. Solvers are braver (less fear), but dawn comes sooner."},
]
# ---------------------------------------------------------------------------
# Beyond the edge of town (Horizon.cs in Unity, horizon_mesh in render3d): Hollow Creek sits in a
# valley. Rings of hills follow the camera like a sky, so they never get closer; on them sit far-off
# farm lights and landmarks (Ravensford's steeple, the old lighthouse on Gull Point, a windmill, a
# water tower). The roads carry on out of town past the edge of the map, lit by street lamps until
# the fog takes them, and a band of forest closes in around the fields.
# Each ring's height at angle a (degrees, 0 = north, clockwise) is base + sum(amp * sin(freq*a + phase)),
# with waves a flat list of (amp, freq, phase) triples (Unity's JsonUtility can't read nested lists).
# ---------------------------------------------------------------------------
T.L["horizon"] = {
    "rings": [
        {"radius": 600, "color": rgb("2a2244"), "base": 55, "waves": [22, 3, 0.4, 14, 7, 1.9, 8, 13, 4.1]},
        {"radius": 570, "color": rgb("1d1832"), "base": 36, "waves": [16, 4, 2.2, 10, 9, 0.7, 5, 17, 3.3]},
        {"radius": 540, "color": rgb("141024"), "base": 20, "waves": [11, 5, 1.1, 6, 11, 2.8, 3, 23, 0.2]},
    ],
    # Landmarks: kind, angle, which ring they stand on (0 = farthest), size
    "landmarks": [
        {"kind": "steeple", "angle": 20, "ring": 1, "size": 1.7, "name": "Ravensford church"},
        {"kind": "lighthouse", "angle": 115, "ring": 0, "size": 1.9, "name": "Gull Point lighthouse"},
        {"kind": "windmill", "angle": 200, "ring": 2, "size": 1.7, "name": "Hatcher's old windmill"},
        {"kind": "watertower", "angle": 285, "ring": 1, "size": 1.6, "name": "Ravensford water tower"},
        {"kind": "castle", "angle": 330, "ring": 0, "size": 2.1, "name": "Thornbury ruins"},
    ],
    # Far-off windows and farm lights, scattered along the rings (seeded, so every machine agrees)
    "lights": {"count": 140, "seed": 7, "colors": rgb("ffcf7a") + rgb("ffb347") + rgb("fff0c8") + rgb("ff8a3a")},
    # The roads keep going past the edge of the map
    "roads": [
        {"name": "Main Street south", "from": [0, -96], "to": [0, -620], "sign": "Ravensford 12 mi"},
        {"name": "Main Street north", "from": [0, 207], "to": [0, 760], "sign": "Gull Point 9 mi"},
        {"name": "Elm Street west", "from": [-125, 0], "to": [-700, 0], "sign": "Old Mill Road"},
        {"name": "Elm Street east", "from": [100, 0], "to": [700, 0], "sign": "Thornbury 6 mi"},
    ],
    "roadWidth": ROAD_W,
    "lampEvery": 28,
    # Forest band just outside the town fields
    "forest": {"inner": 25, "outer": 140, "count": 900, "seed": 3, "town": [TX0, TZ0, TX1, TZ1]},
}
# ---------------------------------------------------------------------------
# Life in town (Town/TownLife.cs): trick-or-treaters on the sidewalks who pass on rumours, cars on
# the roads out of town, and a train crossing the valley far away. Everything is seeded, so every
# machine (and the README renderer) sees the same town.
# ---------------------------------------------------------------------------
T.L["life"] = {
    # Sidewalks the trick-or-treaters walk up and down: (from, to) along each street, offset to the walk
    "walks": [
        {"name": "Main Street", "from": [0, -92], "to": [0, 203], "side": ROAD_W / 2 + 0.9},
        {"name": "Elm Street", "from": [-121, 0], "to": [96, 0], "side": ROAD_W / 2 + 0.9},
        {"name": "Willow Lane", "from": [8, 106], "to": [92, 106], "side": ROAD_W / 2 + 0.9},
        {"name": "Founders Way", "from": [8, -84], "to": [100, -84], "side": ROAD_W / 2 + 0.9},
    ],
    "groups": 10, "seed": 5,
    # Kid costumes: body, accent and hat colours plus a shape (sheet, witch, pumpkin, skeleton, cat, vampire, pirate)
    "costumes": [
        {"kind": "sheet", "body": rgb("eeeae0"), "accent": rgb("1a1420")},
        {"kind": "witch", "body": rgb("2a1d3a"), "accent": rgb("7a3fa0")},
        {"kind": "pumpkin", "body": rgb("e0772a"), "accent": rgb("3e6b2a")},
        {"kind": "skeleton", "body": rgb("1c1a20"), "accent": rgb("e8e4da")},
        {"kind": "cat", "body": rgb("222026"), "accent": rgb("f0c040")},
        {"kind": "vampire", "body": rgb("161218"), "accent": rgb("a01c24")},
        {"kind": "pirate", "body": rgb("6a2a22"), "accent": rgb("e8d8a8")},
    ],
    # What the townsfolk say when you walk past (a call's own rumours come from Cases.cs)
    "rumours": [
        "Trick or treat! ... Are you the Mystery Club? My mum says you're real detectives!",
        "The Historical Society might close after Halloween. Hardly anyone visits the museum.",
        "Miss Wren at the museum gives out the best candy. Full-size bars!",
        "My big brother saw a light up at the old windmill. Nobody's lived there for years.",
        "Somebody borrowed the old festival masks from the museum. Grown-ups keep whispering about it.",
        "If you go past the church, the bells ring by themselves at midnight. Probably.",
        "The lighthouse on Gull Point is still lit. Nobody knows who keeps it going.",
    ],
    # Cars on the roads out of town (headlights coming, tail lights going)
    "cars": 10, "carSeed": 9, "carSpeed": [11, 17],
    # A train crossing the valley in front of the nearest hills, windows lit
    "train": {"radius": 528, "y": 15, "cars": 10, "from": 40, "to": 175, "speed": 1.4},
}
# ---------------------------------------------------------------------------
# The people of Hollow Creek (Town/Townsperson.cs): five grown-ups out on Halloween night. Talk to
# them for the town's side of the Mask Keeper story; each has lost something somewhere in town.
# Bring it back and they put in a word for the club: one more alibi check (tonight, or on the next case).
# ---------------------------------------------------------------------------
T.L["folk"] = [
    {"id": "Mayor", "piece": "Sash", "pieceName": "a festival sash", "pieceBlurb": "the Mayor's old festival sash, cut down to size", "name": "Mayor Harold Beaumont", "job": "Mayor of Hollow Creek", "p": [-23.0, 0, -26.4], "ry": 180,
     "item": "pumpkin_warty", "itemName": "the prize pumpkin", "itemP": [-44.0, 0, 8.6], "itemRy": 30,
     "ask": "Our prize pumpkin rolled clean off the festival cart and away down Elm Street, west of Main! Find it and the Mayor owes you one.",
     "thanks": "The prize pumpkin! Splendid. I'll have a word with a few people for you.",
     "lines": ["Lending the old masks to the festival was my idea. It seemed like a good idea at the time.",
               "The museum's budget? Let's just say the board has been talking to a man from the city.",
               "Hollow Creek has never been so well looked after. Don't tell the sheriff I said so."]},
    {"id": "Fortune", "piece": "Charm", "pieceName": "a moon charm", "pieceBlurb": "a tin moon on a string. 'For courage, dearie.'", "name": "Old Nell Thistle", "job": "Fortune teller", "p": [-34.0, 0, -31.9], "ry": 180,
     "item": "cat", "itemName": "Midnight the cat", "itemP": [-35.5, 0, 90.6], "itemRy": 150,
     "ask": "My cat Midnight has wandered off among the headstones behind the church. She likes the candles. Bring her home, dearie.",
     "thanks": "Midnight! There you are. The cards say someone is lying about where they were tonight.",
     "lines": ["The masks remember everyone who ever wore them. That's why they work.",
               "I read the cards for a man in a fine waistcoat last week. Coins, coins, coins. And a key.",
               "The oldest mask has no face of its own. It borrows yours."]},
    {"id": "Reverend", "piece": "Bell", "pieceName": "a little handbell", "pieceBlurb": "the Sunday-school handbell: ring it and the dark feels smaller", "name": "Reverend Amos Gale", "job": "Minister of the church", "p": [-11.4, 0, 61.0], "ry": 90,
     "item": "lantern", "itemName": "the sexton's lantern", "itemP": [-7.0, 0, 171.5], "itemRy": 0,
     "ask": "The sexton's lantern has gone from the churchyard gate. Someone saw it down by the bridge. We can't leave the dead in the dark tonight.",
     "thanks": "Bless you. People tell a minister things. Ask one more of them where they really were.",
     "lines": ["The founders carved the Hollow Creek Mask their first winter here, to frighten off whatever walked the woods.",
               "Every mask in the museum was blessed in this church once. I'm not sure it took.",
               "Edie Wren rings our bells on Sundays. There's ink on the bell rope every time."]},
    {"id": "Diner", "piece": "Lantern", "pieceName": "a tin-can lantern", "pieceBlurb": "a coffee can with star holes punched in it and a candle inside", "name": "Dot Kowalski", "job": "Runs the diner", "p": [5.7, 0, -41.0], "ry": -90,
     "item": "wreath", "itemName": "Dot's door wreath", "itemP": [19.2, 0, -67.2], "itemRy": -90,
     "ask": "The wind took my door wreath clean off! Last I saw it was cartwheeling past the Post Office. Coffee's on me if you find it.",
     "thanks": "My wreath! Here's a tip with your coffee: folks talk in my back booth, and I'll vouch for you.",
     "lines": ["Busy night! Half the town's been in asking about those masks.",
               "Mortimer Vane tips like it hurts him. Sat in my back booth with a fella from the city last week.",
               "Rosa from the museum tea room buys my pie crusts. Don't tell a soul."]},
    {"id": "Sheriff", "piece": "Badge", "pieceName": "a tin star", "pieceBlurb": "a deputy's tin star, 'for the duration of the night'", "name": "Sheriff Ruth Calloway", "job": "Sheriff", "p": [6.2, 0, 170.0], "ry": -90,
     "item": "jack_grin", "itemName": "the station's jack-o'-lantern", "itemP": [-28.4, 0, 30.0], "itemRy": 90,
     "ask": "Some joker swiped the jack-o'-lantern off the station steps. Kids saw it heading for the Fire Station. Fetch it back? I'm on bridge duty.",
     "thanks": "Much obliged. I'll tell folks to answer your questions straight.",
     "lines": ["Nobody crosses this bridge after ten unless I wave them through. Quiet night so far.",
               "Walter Finch and I go back. Thirty years walking that museum and never missed a night.",
               "Plenty of folks heading out to Ravensford tonight. The train's running late again."]},
]

T.L["lots"] = LOTS
T.L["roads"] = [r for r in ("Main Street", "Elm Street", "Willow Lane", "Founders Way")]
T.L["creekZ"] = CREEK_Z

if __name__ == "__main__":
    T.save("HollowCreek.json", house=False)
    for lot in LOTS:
        (x0, z0), (x1, z1) = lot["lot"]["min"], lot["lot"]["max"]
        print(f"  {lot['name']:24s} {lot['size']:7s} lot {x1 - x0:.0f} x {z1 - z0:.0f} m, {lot['rooms']} rooms, {lot['pieces']} pieces")
