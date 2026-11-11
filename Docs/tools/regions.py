"""
The wider world around Hollow Creek (round 39): six haunted places past the edge of town, joined
to it by real roads you can drive, plus curiosities hidden all over for sharp-eyed explorers.

    Ravenhold Castle   up in the Blackthorn Hills, north of Blackwood Manor
    The Moonlight Circus   a shut-down travelling circus on the fairground west of town
    Gloamwood Tower    a fourteen-storey high rise that never finished letting, south of HQ
    Gull Harbor        the port east of town, with Saltmarsh Lighthouse out on the breakwater
    Wreckers' Beach    sand, beach huts, a wrecked ghost ship and Smugglers' Cave in the cliff
    Hag's Hollow       a swamp south-west of the circus, with a crooked witch's cottage

Called from make_town.py (build(...)) before the town is saved. Everything is boxes, decor and
glows in the town's own format, so TownBuilder builds it like the rest of town. A few named
pieces move at runtime (Town/WorldLife.cs): anything called Spin_* turns, Blink_* blinks,
Bob_* bobs. The curiosities (Town/Curio.cs) and the places (regions) go in HollowCreek.json.
"""
import math
import random

# The whole world on the map: the town plus the regions round it.
WORLD = (-360.0, 345.0, -275.0, 510.0)   # x0, x1, z0, z1
SEA_X = 340.0                              # the coast: sea to the east of this


def build(T, C, rgb, building, town_rect):
    rng = random.Random(39)
    TX0, TX1, TZ0, TZ1 = town_rect
    out = {"regions": [], "curios": [], "clear": []}

    def box(n, p, s, c, mode="solid", tag="building", shape="box", r=(0, 0, 0)):
        T.box(n, p, s, c, 9, mode, tag, shape, r)

    LOOKS = {  # what the club camera (Snapshots.cs) needs in the middle of the picture for the album
        "castle": (-40, 22, 443), "circus": (-310, 13.5, -38), "tower": (24, 65.3, -218),  # the beacon on top
        "harbor": (SEA_X + 58, 22, 70), "beach": (327, 10, 205), "swamp": (-272, 7.5, -195),
    }

    def region(rid, name, kind, blurb, x0, x1, z0, z1, rooms=()):
        out["regions"].append({"id": rid, "n": name, "kind": kind, "blurb": blurb, "min": [x0, z0], "max": [x1, z1],
                               "look": list(LOOKS[rid])})
        T.room(name, 9, x0, x1, z0, z1, -5, 80)
        out["clear"].append([x0 - 6, z0 - 6, x1 + 6, z1 + 6])

    def curio(cid, name, kind, where, lore, p):
        out["curios"].append({"id": cid, "n": name, "kind": kind, "where": where, "lore": lore, "p": [round(v, 2) for v in p]})

    def road(n, x0, x1, z0, z1, lamps=True):
        """A straight road (solid, drivable) with street lamps down one side."""
        box(n, ((x0 + x1) / 2, -0.03, (z0 + z1) / 2), (x1 - x0, 0.1, z1 - z0), C["road"], tag="road")
        along_x = (x1 - x0) > (z1 - z0)
        out["clear"].append([x0 - 4, z0 - 4, x1 + 4, z1 + 4])
        length = (x1 - x0) if along_x else (z1 - z0)
        for i in range(int(length // 4)):  # the centre line
            if i % 2:
                continue
            if along_x:
                box(f"{n}Dash{i}", (x0 + 2 + i * 4, 0.025, (z0 + z1) / 2), (2.4, 0.02, 0.18), C["line"], "nocollide", "road")
            else:
                box(f"{n}Dash{i}", ((x0 + x1) / 2, 0.025, z0 + 2 + i * 4), (0.18, 0.02, 2.4), C["line"], "nocollide", "road")
        if lamps:
            for i in range(int(length // 26) + 1):
                if along_x:
                    T.decor("streetlamp", (x0 + 6 + i * 26, 0, z1 + 1.4), 180)
                else:
                    T.decor("streetlamp", (x1 + 1.4, 0, z0 + 6 + i * 26), -90)

    def ground(n, x0, x1, z0, z1, c, top=0.0, tag="patch", tile=48.0):
        """A ground surface in tiles of about `tile` metres (so each is only lit by lamps near it)."""
        nx, nz = max(1, round((x1 - x0) / tile)), max(1, round((z1 - z0) / tile))
        for i in range(nx):
            for j in range(nz):
                a0, a1 = x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx
                b0, b1 = z0 + (z1 - z0) * j / nz, z0 + (z1 - z0) * (j + 1) / nz
                if a0 >= TX0 and a1 <= TX1 and b0 >= TZ0 and b1 <= TZ1:
                    continue  # the town has its own ground
                box(f"{n}_{i}_{j}", ((a0 + a1) / 2, top - 0.25, (b0 + b1) / 2), (a1 - a0, 0.5, b1 - b0), c, tag=tag)

    def tree(n, x, z, h, leaves=None):
        T.tree(n, x, z, h, leaves)

    def window_grid(n, x0, x1, z0, z1, y0, floors, fh, per, lit_chance, side_list="SNWE", glass=None):
        """Windows on a block's faces: lit warm, dark, or (rarely) a violet glow where something moves."""
        warm, dark, violet = glass or rgb("ffcf7a"), rgb("1a1c26"), rgb("b48cff")
        for side in side_list:
            along_x = side in "SN"
            a0, a1 = (x0, x1) if along_x else (z0, z1)
            for f in range(floors):
                y = y0 + f * fh + fh * 0.55
                for k in range(per):
                    a = a0 + (a1 - a0) * (k + 0.5) / per
                    roll = rng.random()
                    c, mode = (violet, "emissive") if roll < 0.04 else (warm, "emissive") if roll < lit_chance else (dark, "solid")
                    w = min(1.6, (a1 - a0) / per * 0.55)
                    if side == "S":
                        box(f"{n}W{side}{f}_{k}", (a, y, z0 - 0.06), (w, fh * 0.45, 0.1), c, mode, "glass")
                    elif side == "N":
                        box(f"{n}W{side}{f}_{k}", (a, y, z1 + 0.06), (w, fh * 0.45, 0.1), c, mode, "glass")
                    elif side == "W":
                        box(f"{n}W{side}{f}_{k}", (x0 - 0.06, y, a), (0.1, fh * 0.45, w), c, mode, "glass")
                    else:
                        box(f"{n}W{side}{f}_{k}", (x1 + 0.06, y, a), (0.1, fh * 0.45, w), c, mode, "glass")

    # -------------------------------------------------------------------------------------------
    # The ground of the wider world, the sea, and the roads out of town
    # -------------------------------------------------------------------------------------------
    X0, X1, Z0, Z1 = WORLD
    # Four bands round the town (which has its own ground): south, north, west and east.
    ground("WorldGroundS", X0, SEA_X, Z0, TZ0, C["grass"], top=-0.04)
    ground("WorldGroundN", X0, SEA_X, TZ1, Z1, C["grass"], top=-0.04)
    ground("WorldGroundW", X0, TX0, TZ0, TZ1, C["grass"], top=-0.04)
    ground("WorldGroundE", TX1, SEA_X, TZ0, TZ1, C["grass"], top=-0.04)
    # The sea: a shallow bay you can wade into at low tide, and the far water beyond it.
    box("SeaBed", (SEA_X + 160, -0.3, (Z0 + Z1) / 2), (320, 0.5, Z1 - Z0 + 300), rgb("6a6248"), tag="ground")
    box("Sea", (SEA_X + 160, 0.0, (Z0 + Z1) / 2), (320, 0.06, Z1 - Z0 + 300), rgb("1f3f58"), "nocollide", "water")

    road("RoadToCircus", -215, TX0, -4, 4)
    road("RoadToHarbor", TX1, 236, -4, 4)
    road("RoadToTower", -4, 4, -170, TZ0)
    road("RoadToHills", -4, 4, TZ1, 335)
    road("RoadToHollow", -274, -266, -120, -40)
    road("HarborToBeach", 252, 260, 100, 150)

    # -------------------------------------------------------------------------------------------
    # Ravenhold Castle, up in the Blackthorn Hills (north)
    # -------------------------------------------------------------------------------------------
    stone, stone_d, slate = rgb("6f6e72"), rgb("4f4e54"), rgb("2a2c3a")
    region("castle", "Ravenhold Castle", "castle",
           "A ruined castle on the hilltop above the manor. The Ravenholds left in 1790 and the lights still come on.",
           -110, 30, 335, 490)
    PY = 6.0  # the plateau's height
    # The hill: a plateau with stepped, rocky sides, and a road ramping up to the gate.
    box("HillTop", (-40, PY / 2 - 0.25, 425), (130, PY, 110), rgb("2e3a26"), tag="ground")
    for k, (grow, h) in enumerate(((8, PY * 0.66), (16, PY * 0.33))):
        box(f"HillStep{k}", (-40, h / 2 - 0.25, 425), (130 + grow, h, 110 + grow), rgb("33402a"), tag="ground")
    for i in range(26):  # boulders round the slopes
        a = rng.uniform(0, math.tau)
        x, z = -40 + math.cos(a) * rng.uniform(66, 78), 425 + math.sin(a) * rng.uniform(56, 66)
        if abs(x) < 8 and z < 380:
            continue
        s = rng.uniform(1.5, 4)
        box(f"Boulder{i}", (x, s * 0.3, z), (s, s * 0.7, s * 0.9), rgb("55545a"), tag="stone", r=(rng.uniform(-10, 10), rng.uniform(0, 90), rng.uniform(-10, 10)))
    ramp_len = 34.0
    ang = math.degrees(math.atan2(PY, ramp_len))
    box("HillRamp", (0, PY / 2 - 0.1, 335 + ramp_len / 2), (8, 0.3, math.hypot(ramp_len, PY)), C["road"], tag="road", r=(-ang, 0, 0))
    for side in (-1, 1):
        box(f"HillRampWall{side}", (side * 4.4, PY / 2 + 0.4, 335 + ramp_len / 2), (0.6, 1.0, math.hypot(ramp_len, PY)), stone_d, tag="stone", r=(-ang, 0, 0))
    # Curtain walls with battlements, round corner towers, a gatehouse to the south.
    CX0, CX1, CZ0, CZ1 = -78.0, -2.0, 390.0, 466.0
    WALL_H, WT = 9.0, 2.0
    gate_x = -40.0

    def battlements(n, x0, x1, z0, z1, y):
        along_x = (x1 - x0) > (z1 - z0)
        length = (x1 - x0) if along_x else (z1 - z0)
        for i in range(int(length // 2.2)):
            a = (x0 if along_x else z0) + 1.1 + i * 2.2
            if along_x:
                box(f"{n}M{i}", (a, y + 0.7, (z0 + z1) / 2), (1.1, 1.4, z1 - z0), stone)
            else:
                box(f"{n}M{i}", ((x0 + x1) / 2, y + 0.7, a), (x1 - x0, 1.4, 1.1), stone)

    # south wall with the gate
    for n, a0, a1 in (("CastleWallSW", CX0, gate_x - 4), ("CastleWallSE", gate_x + 4, CX1)):
        box(n, ((a0 + a1) / 2, PY + WALL_H / 2, CZ0), (a1 - a0, WALL_H, WT), stone)
        battlements(n, a0, a1, CZ0 - WT / 2, CZ0 + WT / 2, PY + WALL_H)
    box("CastleWallN", ((CX0 + CX1) / 2, PY + WALL_H / 2, CZ1), (CX1 - CX0, WALL_H, WT), stone)
    battlements("CastleWallN", CX0, CX1, CZ1 - WT / 2, CZ1 + WT / 2, PY + WALL_H)
    for n, x in (("CastleWallW", CX0), ("CastleWallE", CX1)):
        box(n, (x, PY + WALL_H / 2, (CZ0 + CZ1) / 2), (WT, WALL_H, CZ1 - CZ0), stone)
        battlements(n, x - WT / 2, x + WT / 2, CZ0, CZ1, PY + WALL_H)
    # the gatehouse: two square towers and an arch with the portcullis wound up
    for side in (-1, 1):
        gx = gate_x + side * 6
        box(f"GateTower{side}", (gx, PY + 7, CZ0), (4.5, 14, 5), stone_d)
        battlements(f"GateTower{side}", gx - 2.25, gx + 2.25, CZ0 - 2.5, CZ0 + 2.5, PY + 14)
        box(f"GateSlit{side}", (gx, PY + 9, CZ0 - 2.56), (0.3, 1.6, 0.1), rgb("ffb35a"), "emissive", "glass")
    box("GateArch", (gate_x, PY + WALL_H - 1.5, CZ0), (8, 3, WT + 0.4), stone_d)
    for i in range(7):
        box(f"Portcullis{i}", (gate_x - 3 + i, PY + WALL_H - 1.1, CZ0 - 1.3), (0.12, 2.2, 0.12), rgb("1e1e22"))
    box("PortcullisBar", (gate_x, PY + WALL_H - 1.9, CZ0 - 1.3), (6.4, 0.14, 0.14), rgb("1e1e22"))
    # round corner towers with pointed slate roofs and a flag each
    for i, (tx, tz) in enumerate(((CX0, CZ0), (CX1, CZ0), (CX0, CZ1), (CX1, CZ1))):
        box(f"CastleTower{i}", (tx, PY + 7.5, tz), (7, 7.5, 7), stone, shape="cyl")
        box(f"CastleTowerRing{i}", (tx, PY + 15.2, tz), (7.8, 0.4, 7.8), stone_d, shape="cyl")
        for k in range(5):  # a cone of shrinking discs
            w = 7.6 - k * 1.5
            box(f"CastleTowerRoof{i}_{k}", (tx, PY + 15.8 + k * 1.1, tz), (w, 0.55, w), slate, shape="cyl", tag="roof")
        box(f"CastleFlagPole{i}", (tx, PY + 23, tz), (0.12, 2.4, 0.12), rgb("1e1e22"))
        box(f"Spin_Flag{i}", (tx + 0.8, PY + 23.8, tz), (1.5, 0.9, 0.05), rgb("6a1f2a"), "nocollide", "flag")
        for k in range(3):
            a = k * 2.1 + i
            box(f"TowerWin{i}_{k}", (tx + math.cos(a) * 3.52, PY + 9 + k * 1.2, tz + math.sin(a) * 3.52), (0.5, 1.2, 0.5),
                rgb("b48cff") if (i + k) % 3 == 0 else rgb("ffb35a"), "emissive", "glass")
    # the keep, with a great hall you can walk into
    KX0, KX1, KZ0, KZ1 = -62.0, -18.0, 428.0, 458.0
    KH = 15.0
    T.wall("KeepS", "x", KZ0, KX0, KX1, PY, KH, 9, stone, 1.2,
           openings=[(gate_x, 3.0, 0, 4.2, "door"), (KX0 + 7, 1.6, 6, 9, "window"), (KX1 - 7, 1.6, 6, 9, "window")], tag="building",
           glass=rgb("ffb35a"))
    T.wall("KeepN", "x", KZ1, KX0, KX1, PY, KH, 9, stone, 1.2, openings=[(gate_x, 1.6, 6, 10, "window")], tag="building", glass=rgb("b48cff"))
    T.wall("KeepW", "z", KX0, KZ0, KZ1, PY, KH, 9, stone, 1.2, openings=[(443, 1.6, 6, 9, "window")], tag="building", glass=rgb("ffb35a"))
    T.wall("KeepE", "z", KX1, KZ0, KZ1, PY, KH, 9, stone, 1.2, openings=[(443, 1.6, 6, 9, "window")], tag="building", glass=rgb("ffb35a"))
    box("KeepFloor", ((KX0 + KX1) / 2, PY + 0.05, (KZ0 + KZ1) / 2), (KX1 - KX0, 0.1, KZ1 - KZ0), rgb("4a3a2e"), tag="floor")
    box("KeepRoof", ((KX0 + KX1) / 2, PY + KH + 0.3, (KZ0 + KZ1) / 2), (KX1 - KX0 + 0.6, 0.6, KZ1 - KZ0 + 0.6), stone_d, tag="roof")
    battlements("KeepRoofS", KX0, KX1, KZ0 - 0.6, KZ0 + 0.6, PY + KH + 0.6)
    battlements("KeepRoofN", KX0, KX1, KZ1 - 0.6, KZ1 + 0.6, PY + KH + 0.6)
    T.room("The Great Hall", 9, KX0, KX1, KZ0, KZ1, PY - 1, PY + KH)
    # great hall: a long table set for a feast nobody came to, a throne, banners, armour, a fireplace
    box("FeastTable", (gate_x, PY + 0.85, 444), (3, 0.15, 18), rgb("4a2e1c"), tag="furniture")
    for k in range(6):
        for side in (-1, 1):
            box(f"FeastChair{k}{side}", (gate_x + side * 2.2, PY + 0.6, 437 + k * 2.8), (0.8, 1.2, 0.8), rgb("3a2416"), tag="furniture")
        box(f"FeastPlate{k}", (gate_x - 0.6, PY + 0.95, 437 + k * 2.8), (0.5, 0.04, 0.5), rgb("c8c4b8"), shape="cyl", tag="furniture")
        box(f"FeastGoblet{k}", (gate_x + 0.7, PY + 1.1, 437 + k * 2.8), (0.15, 0.2, 0.15), rgb("c8a85a"), shape="cyl", tag="furniture")
    for k in range(3):
        T.decor("candle", (gate_x, PY + 0.93, 439 + k * 5), 0)
        T.glow((gate_x, PY + 1.6, 439 + k * 5), rgb("ffb35a"), 8, 0.9)
    box("Throne", (gate_x, PY + 1.4, 456.4), (2.0, 2.8, 1.2), rgb("5a1a24"), tag="furniture")
    box("ThroneBack", (gate_x, PY + 3.3, 456.9), (2.2, 1.6, 0.3), rgb("c8a85a"), tag="furniture")
    for k, x in enumerate((KX0 + 1.0, KX1 - 1.0)):
        for b in range(3):
            box(f"Banner{k}{b}", (x, PY + 8, 434 + b * 9), (0.1, 5, 2.2), rgb("6a1f2a") if b % 2 == 0 else rgb("1f3a5a"), "nocollide", "flag")
        for b in range(2):
            ax, az = x + (0.8 if k == 0 else -0.8), 438.5 + b * 9
            box(f"Armour{k}{b}Legs", (ax, PY + 0.6, az), (0.5, 1.2, 0.4), rgb("9a9ca4"), tag="furniture")
            box(f"Armour{k}{b}Body", (ax, PY + 1.6, az), (0.7, 0.9, 0.45), rgb("a8aab2"), tag="furniture")
            box(f"Armour{k}{b}Helm", (ax, PY + 2.25, az), (0.4, 0.45, 0.4), rgb("b8bac2"), shape="sphere", tag="furniture")
            box(f"Armour{k}{b}Visor", (ax + (0.2 if k == 0 else -0.2), PY + 2.25, az), (0.05, 0.08, 0.3), rgb("ff5a3a"), "emissive", "glass")
    box("Fireplace", (KX1 - 1.0, PY + 1.5, 452), (1.2, 3, 4), stone_d, tag="furniture")
    box("FireplaceFire", (KX1 - 1.4, PY + 0.6, 452), (0.6, 0.8, 2.4), rgb("ff7a2a"), "emissive", "glass")
    T.glow((KX1 - 2.5, PY + 1.4, 452), rgb("ff8a3a"), 12, 1.4)
    box("Chandelier", (gate_x, PY + 9, 444), (3.5, 0.3, 3.5), rgb("2a2622"), shape="cyl", tag="furniture")
    T.glow((gate_x, PY + 8.4, 444), rgb("b48cff"), 16, 0.9)
    # the courtyard: a well, a cart, crows on the walls, the old chapel graves outside
    box("Well", (-66, PY + 0.5, 410), (2.4, 1.0, 2.4), stone_d, shape="cyl", tag="stone")
    box("WellWater", (-66, PY + 0.95, 410), (2.0, 0.05, 2.0), rgb("2d5a4a"), "emissive", "glass", shape="cyl")
    box("WellRoof", (-66, PY + 3.2, 410), (3.0, 0.3, 3.0), slate, shape="cyl", tag="roof")
    for side in (-1, 1):
        box(f"WellPost{side}", (-66 + side * 1.1, PY + 2.0, 410), (0.2, 2.2, 0.2), rgb("3a2a1c"))
    box("Cart", (-14, PY + 0.8, 404), (2.0, 0.6, 3.2), rgb("4a3020"), tag="furniture")
    for side in (-1, 1):
        box(f"CartWheel{side}", (-14 + side * 1.1, PY + 0.6, 404), (1.2, 0.12, 1.2), rgb("2a1c12"), shape="cyl", r=(0, 0, 90))
    T.decor("haybale", (-12, PY, 409), 20)
    for i in range(8):
        T.decor("crow", (CX0 + 6 + i * 9, PY + WALL_H + 1.4, CZ0), 180 + rng.uniform(-30, 30))
    for i in range(10):
        T.decor("tomb_cross" if i % 2 else "tomb_round", (12 + (i % 5) * 3.2, PY, 404 + (i // 5) * 4), 180 + rng.uniform(-12, 12))
    T.glow((gate_x, PY + 4, CZ0 - 4), rgb("ffb35a"), 14, 1.2)
    T.glow((-40, PY + 3, 412), rgb("b48cff"), 18, 0.8)
    curio("castle-helm", "The rusted helm", "helm", "Ravenhold Castle, the great hall",
          "A knight's helmet with a dent shaped exactly like a frying pan. Someone in 1790 had a very bad day.", (KX0 + 2.5, PY, 449))
    curio("castle-key", "A key bigger than your hand", "key", "the castle well",
          "It fits no door in the castle. The Ravenholds' last letter mentions 'the little door under the hill'.", (-63.5, PY, 412))
    curio("castle-portrait", "A slashed portrait", "frame", "the castle gatehouse",
          "Lady Ravenhold, painted in 1788. Someone cut out her face and left the smile.", (gate_x + 6, PY, CZ0 + 3.5))
    curio("castle-raven", "A stuffed raven", "raven", "the castle's north-east tower",
          "Its glass eyes follow you. The label says 'Edgar. Good boy.'", (CX1 - 2, PY, CZ1 - 2))

    # -------------------------------------------------------------------------------------------
    # The Moonlight Circus, on the old fairground west of town
    # -------------------------------------------------------------------------------------------
    region("circus", "The Moonlight Circus", "circus",
           "A travelling circus that pulled in one October and never pulled out. The carousel still turns at midnight.",
           -350, -215, -60, 95)
    ground("Fairground", -345, -215, -55, 90, rgb("4a3e2a"), top=0.0, tag="path", tile=44)
    red, cream, gold, navy = rgb("b0282e"), rgb("efe2c4"), rgb("e8c96a"), rgb("23305a")
    # the big top: a ring of striped canvas, a cone roof, flags, a way in on the east side
    BX, BZ, BR = -290.0, 20.0, 17.0
    seg = 28
    for i in range(seg):
        a = i / seg * math.tau
        if abs(math.atan2(math.sin(a), math.cos(a))) < 0.24:  # the entrance faces east, towards town
            continue
        x, z = BX + math.cos(a) * BR, BZ + math.sin(a) * BR
        box(f"BigTopWall{i}", (x, 3.5, z), (BR * math.tau / seg + 0.15, 7, 0.3), red if i % 2 else cream, tag="tent",
            r=(0, -math.degrees(a) + 90, 0))
    for k in range(7):
        w = 2 * (BR + 0.6) * (1 - k / 7.5)
        box(f"BigTopRoof{k}", (BX, 7.2 + k * 1.3, BZ), (w, 0.7, w), red if k % 2 == 0 else cream, shape="cyl", tag="roof")
    box("BigTopPole", (BX, 9, BZ), (0.5, 18, 0.5), gold, shape="cyl")
    box("Spin_BigTopFlag", (BX + 1.2, 17.8, BZ), (2.2, 1.2, 0.05), navy, "nocollide", "flag")
    for side in (-1, 1):
        box(f"BigTopAwning{side}", (BX + BR + 1.5, 4.2, BZ + side * 2.6), (3.2, 0.25, 0.25), gold)
    box("BigTopSign", (BX + BR + 3.0, 5.2, BZ), (0.3, 1.4, 6.5), navy, tag="sign")
    box("BigTopSignLights", (BX + BR + 3.18, 5.2, BZ), (0.1, 0.9, 5.8), gold, "emissive", "glass")
    T.room("The Big Top", 9, BX - BR, BX + BR, BZ - BR, BZ + BR, -1, 16)
    box("CircusRing", (BX, 0.25, BZ), (11, 0.5, 11), red, shape="cyl", tag="furniture")
    box("CircusRingSand", (BX, 0.27, BZ), (10.2, 0.5, 10.2), rgb("c8a868"), shape="cyl", tag="floor")
    for row in range(4):  # bleachers on the far side
        r_ = BR - 1.2 - row * 1.3
        for i in range(10):
            a = math.pi * 0.35 + i / 10 * math.pi * 1.3
            box(f"Bleacher{row}_{i}", (BX + math.cos(a) * r_, 0.4 + (3 - row) * 0.5, BZ + math.sin(a) * r_), (4.4, 0.8 + (3 - row) * 1.0, 1.2),
                navy if row % 2 else rgb("3a3a50"), tag="furniture", r=(0, -math.degrees(a) + 90, 0))
    for side in (-1, 1):
        box(f"TrapezePole{side}", (BX, 6, BZ + side * 6), (0.25, 12, 0.25), rgb("c8c8d0"), shape="cyl")
    box("TrapezeBar", (BX, 9.5, BZ), (0.1, 0.1, 2.2), rgb("c8c8d0"))
    box("TrapezeRopeA", (BX, 10.8, BZ - 1.1), (0.04, 2.6, 0.04), cream)
    box("TrapezeRopeB", (BX, 10.8, BZ + 1.1), (0.04, 2.6, 0.04), cream)
    box("Spin_Spotlight", (BX, 0.6, BZ), (0.6, 0.02, 0.6), rgb("fff2c8"), "emissive", "glass", shape="cyl")
    T.glow((BX, 6, BZ), rgb("ffe0a0"), 20, 1.3)
    T.glow((BX + 6, 3, BZ + 8), rgb("b48cff"), 12, 0.7)
    # the clown car, left mid-trick in the ring
    box("ClownCar", (BX + 2.5, 0.9, BZ - 2), (1.4, 0.8, 2.4), rgb("e8c040"), tag="furniture")
    box("ClownCarTop", (BX + 2.5, 1.5, BZ - 2.2), (1.2, 0.5, 1.2), rgb("3a8ad0"), tag="furniture")
    for i in range(4):
        box(f"ClownCarWheel{i}", (BX + 2.5 + (0.75 if i % 2 else -0.75), 0.75, BZ - 2 + (0.8 if i < 2 else -0.8)), (0.6, 0.15, 0.6), rgb("1a1a1a"), shape="cyl", r=(0, 0, 90))
    # the carousel
    CXc, CZc = -246.0, -28.0
    box("CarouselBase", (CXc, 0.3, CZc), (12, 0.6, 12), rgb("6a2a5a"), shape="cyl", tag="furniture")
    box("Spin_Carousel", (CXc, 0.65, CZc), (11, 0.1, 11), gold, "nocollide", "furniture", shape="cyl")
    box("CarouselPole", (CXc, 3, CZc), (0.8, 6, 0.8), gold, shape="cyl")
    for k in range(4):
        w = 13 - k * 3
        box(f"CarouselRoof{k}", (CXc, 5.6 + k * 0.7, CZc), (w, 0.4, w), red if k % 2 == 0 else cream, shape="cyl", tag="roof")
    for i in range(8):
        a = i / 8 * math.tau
        hx, hz = CXc + math.cos(a) * 4.2, CZc + math.sin(a) * 4.2
        box(f"CarouselHorsePole{i}", (hx, 3, hz), (0.1, 5, 0.1), gold, shape="cyl")
        horse = [cream, rgb("2a2a30"), rgb("c87a3a"), rgb("8a8ad0")][i % 4]
        box(f"CarouselHorse{i}", (hx, 1.6 + 0.3 * (i % 2), hz), (0.5, 0.6, 1.4), horse, tag="furniture", r=(0, -math.degrees(a), 0))
        box(f"CarouselHorseHead{i}", (hx + math.cos(a + math.pi / 2) * 0.6, 2.1 + 0.3 * (i % 2), hz + math.sin(a + math.pi / 2) * 0.6), (0.35, 0.7, 0.4), horse, tag="furniture", r=(0, -math.degrees(a), 0))
    for i in range(16):
        a = i / 16 * math.tau
        T.decor("bulb_orange" if i % 2 else "bulb_purple", (CXc + math.cos(a) * 6.3, 5.3, CZc + math.sin(a) * 6.3), 0)
    T.glow((CXc, 4, CZc), rgb("ffcf7a"), 14, 1.1)
    # the Ferris wheel, standing still against the sky (WorldLife turns the wheel slowly)
    FX, FZ, FR = -310.0, -38.0, 12.0
    for side in (-1, 1):
        for lean in (-1, 1):
            box(f"FerrisLeg{side}{lean}", (FX + lean * 3.2, FR / 2 + 0.6, FZ + side * 1.6), (0.4, FR + 2.4, 0.4), rgb("c8c8d0"), r=(0, 0, lean * -14))
    box("FerrisAxle", (FX, FR + 1.5, FZ), (0.5, 0.5, 3.6), rgb("c8c8d0"), shape="cyl", r=(90, 0, 0))
    for i in range(16):
        a = i / 16 * 360
        box(f"Spin_FerrisSpoke{i}", (FX, FR + 1.5, FZ), (0.18, FR * 2, 0.18), rgb("e8e8f0"), "nocollide", r=(0, 0, a))
        ar = math.radians(a)
        cx, cy = FX + math.sin(ar) * FR, FR + 1.5 + math.cos(ar) * FR
        box(f"Spin_FerrisRim{i}", (cx, cy, FZ), (0.25, FR * math.tau / 16 + 0.2, 0.25), gold, "nocollide", r=(0, 0, a + 90))
        if i % 2 == 0:
            box(f"Spin_FerrisCar{i}", (cx, cy - 1.0, FZ), (1.4, 1.2, 1.4), [red, navy, rgb("3a8a5a"), rgb("e8c040")][(i // 2) % 4], "nocollide", "furniture")
        T.decor("bulb_orange" if i % 3 else "bulb_green", (cx, cy, FZ + 0.4), 0)
    # booths along the midway, a ticket booth, caravans, a fortune teller's wagon, a popcorn cart
    stall = [(red, cream), (navy, gold), (rgb("3a8a5a"), cream), (rgb("6a2a5a"), gold)]
    games = ["Ring Toss", "Hook-a-Duck", "Test Your Nerve", "Bottle Shy", "Guess Your Fate", "Splat the Bat"]
    for i, name in enumerate(games):
        sx, sz = -330 + i * 15, 70.0
        a, b = stall[i % 4]
        box(f"Booth{i}", (sx, 1.3, sz), (5, 2.6, 3), a, tag="building")
        box(f"Booth{i}Counter", (sx, 1.1, sz - 1.7), (5, 0.2, 0.6), b, tag="furniture")
        for k in range(5):
            box(f"Booth{i}Awning{k}", (sx - 2 + k, 3.0, sz - 1.9), (1.0, 0.15, 1.4), a if k % 2 else b, tag="roof", r=(-18, 0, 0))
        for k in range(3):
            box(f"Booth{i}Prize{k}", (sx - 1.2 + k * 1.2, 1.6, sz + 0.2), (0.6, 0.7, 0.4), [rgb("e88aa8"), rgb("8ad0e8"), rgb("e8e070")][k], shape="sphere", tag="furniture")
        T.glow((sx, 2.6, sz - 2.4), rgb("ffcf7a"), 6, 0.6)
    box("TicketBooth", (-222, 1.4, 6), (2.4, 2.8, 2.4), red, tag="building")
    box("TicketBoothRoof", (-222, 3.1, 6), (3.2, 0.6, 3.2), gold, shape="cyl", tag="roof")
    box("TicketBoothWindow", (-220.75, 1.7, 6), (0.1, 0.9, 1.2), rgb("ffcf7a"), "emissive", "glass")
    for side in (-1, 1):  # the arch over the way in
        box(f"CircusArchPost{side}", (-218, 3.5, side * 5.5), (0.6, 7, 0.6), gold, shape="cyl")
    box("CircusArch", (-218, 7.2, 0), (0.6, 1.4, 12), red, tag="sign")
    box("CircusArchLights", (-217.65, 7.2, 0), (0.1, 0.8, 10.5), gold, "emissive", "glass")
    for i in range(5):
        cx_, cz_ = -335 + (i % 3) * 9, -50 + (i // 3) * 9
        col = [rgb("2f5a6a"), rgb("6a2a3a"), rgb("4a3a6a")][i % 3]
        box(f"Caravan{i}", (cx_, 1.6, cz_), (3, 2.4, 6), col, tag="building")
        box(f"Caravan{i}Roof", (cx_, 3.0, cz_), (3.2, 0.5, 6.4), cream, tag="roof", shape="capsule", r=(90, 0, 0))
        for side in (-1, 1):
            box(f"Caravan{i}Wheel{side}", (cx_ + side * 1.6, 0.6, cz_ + 1.5), (1.2, 0.12, 1.2), rgb("6a4a2a"), shape="cyl", r=(0, 0, 90))
        box(f"Caravan{i}Window", (cx_ + 1.56, 1.9, cz_), (0.08, 0.7, 1.2), rgb("ffcf7a") if i % 2 else rgb("b48cff"), "emissive", "glass")
    box("FortuneWagon", (-232, 1.7, 62), (3.2, 2.6, 5.5), rgb("4a1a5a"), tag="building")
    box("FortuneWagonRoof", (-232, 3.2, 62), (3.4, 0.6, 5.8), gold, tag="roof", shape="capsule", r=(90, 0, 0))
    box("FortuneCrystal", (-230.3, 1.8, 62), (0.5, 0.5, 0.5), rgb("9fd8ff"), "emissive", "glass", shape="sphere")
    T.glow((-229.5, 2, 62), rgb("9fd8ff"), 8, 0.9)
    box("PopcornCart", (-250, 1.0, 40), (1.6, 1.4, 1.0), red, tag="furniture")
    box("PopcornGlass", (-250, 2.0, 40), (1.2, 0.8, 0.8), rgb("fff2c8"), "emissive", "glass")
    box("PopcornRoof", (-250, 2.6, 40), (1.8, 0.3, 1.2), cream, tag="roof")
    for i in range(10):
        T.decor("bulb_orange" if i % 2 else "bulb_purple", (-240 + i * 2.2, 3.2, 3.6), 0)
    for i in range(6):
        T.decor("haybale", (-260 - i * 4.5, 0, -50 + (i % 2) * 2), rng.uniform(0, 90))
    curio("circus-nose", "A squeaky red nose", "nose", "the circus ring",
          "It still squeaks. Nobody has worn it since Bimbo the Clown walked into the mirror maze and didn't walk out.", (BX - 3, 0.5, BZ + 2))
    curio("circus-ticket", "Admit One, 31 Oct 1958", "ticket", "the ticket booth",
          "Unused. Someone bought a ticket for the last show and never came. Or came, and never left.", (-221, 0, 8.5))
    curio("circus-dummy", "A ventriloquist's dummy", "doll", "a caravan at the back of the fairground",
          "His name is Mr. Pocket. You'd swear his mouth moved. You're sure it didn't.", (-326, 0, -46))
    curio("circus-poster", "The last poster", "frame", "the Ferris wheel",
          "'The Moonlight Circus: one night only.' The date has been scratched off with a fingernail.", (FX + 4, 0, FZ + 3))

    # -------------------------------------------------------------------------------------------
    # Gloamwood Tower, the high rise south of HQ
    # -------------------------------------------------------------------------------------------
    region("tower", "Gloamwood Tower", "tower",
           "Fourteen storeys of flats that opened in 1974 and never filled up. The lift still stops at 13.",
           -60, 80, -270, -170)
    ground("TowerPlaza", -55, 75, -262, -172, rgb("5a5a60"), top=0.0, tag="path", tile=44)
    concrete, concrete_d = rgb("8a8a90"), rgb("5a5a62")
    GX0, GX1, GZ0, GZ1 = 6.0, 30.0, -236.0, -212.0
    FLOORS, FH = 14, 3.5
    LOBBY = 4.5
    # the lobby walls with a revolving door, then the tower above in one block
    T.wall("TowerLobbyN", "x", GZ1, GX0, GX1, 0, LOBBY, 9, concrete_d, 0.5, openings=[(18, 3.0, 0, 3.2, "door"), (11, 3, 0.8, 3.6, "window"), (25, 3, 0.8, 3.6, "window")], tag="building")
    T.wall("TowerLobbyS", "x", GZ0, GX0, GX1, 0, LOBBY, 9, concrete_d, 0.5, tag="building")
    T.wall("TowerLobbyW", "z", GX0, GZ0, GZ1, 0, LOBBY, 9, concrete_d, 0.5, tag="building")
    T.wall("TowerLobbyE", "z", GX1, GZ0, GZ1, 0, LOBBY, 9, concrete_d, 0.5, tag="building")
    box("TowerLobbyFloor", (18, 0.05, -224), (24, 0.1, 24), rgb("c8c0b0"), tag="floor")
    box("TowerLobbyCeiling", (18, LOBBY - 0.15, -224), (24, 0.3, 24), rgb("d8d4cc"), tag="ceiling")
    T.room("Gloamwood Tower lobby", 9, GX0, GX1, GZ0, GZ1, -1, LOBBY)
    TH = FLOORS * FH
    box("TowerBody", (18, LOBBY + TH / 2, -224), (24, TH, 24), concrete, tag="building")
    for f in range(FLOORS + 1):  # floor bands
        box(f"TowerBand{f}", (18, LOBBY + f * FH, -224), (24.4, 0.3, 24.4), concrete_d)
    window_grid("Tower", GX0, GX1, GZ0, GZ1, LOBBY, FLOORS, FH, 5, 0.35)
    box("TowerRoof", (18, LOBBY + TH + 0.4, -224), (24.6, 0.8, 24.6), concrete_d, tag="roof")
    box("TowerWaterTank", (12, LOBBY + TH + 3, -230), (3.5, 4, 3.5), rgb("6a4a3a"), shape="cyl", tag="roof")
    box("TowerAntenna", (24, LOBBY + TH + 6, -218), (0.3, 11, 0.3), rgb("c8c8d0"), shape="cyl")
    box("Blink_TowerBeacon", (24, LOBBY + TH + 11.8, -218), (0.6, 0.6, 0.6), rgb("ff3a3a"), "emissive", "glass", shape="sphere")
    box("TowerSign", (18, LOBBY + TH - 1.5, GZ1 + 0.3), (16, 2.2, 0.3), rgb("1a1a24"), tag="sign")
    box("TowerSignNeon", (18, LOBBY + TH - 1.5, GZ1 + 0.5), (14, 1.2, 0.1), rgb("6affd0"), "emissive", "glass")
    # the lobby: reception desk, lift doors with the floor dial stuck at 13, post boxes, plants, a chandelier
    box("ReceptionDesk", (12, 0.55, -224), (1.2, 1.1, 5), rgb("4a3a2a"), tag="furniture")
    box("ReceptionBell", (12, 1.15, -223), (0.2, 0.1, 0.2), gold, shape="sphere", tag="furniture")
    for k in range(2):
        box(f"LiftDoor{k}", (22 + k * 3.2, 1.4, GZ0 + 0.3), (2.6, 2.8, 0.1), rgb("b8b8c0"), tag="furniture")
        box(f"LiftDial{k}", (22 + k * 3.2, 3.2, GZ0 + 0.3), (0.6, 0.6, 0.08), rgb("ffb35a"), "emissive", "glass", shape="cyl", r=(90, 0, 0))
    for i in range(12):
        box(f"PostBox{i}", (GX1 - 0.35, 1.2 + (i // 4) * 0.45, -230 + (i % 4) * 0.6), (0.2, 0.4, 0.55), rgb("8a6a3a") if i != 7 else rgb("6a2a5a"), tag="furniture")
    for i, (px, pz) in enumerate(((8, -214), (28, -214), (8, -234))):
        box(f"LobbyPlant{i}Pot", (px, 0.4, pz), (0.8, 0.8, 0.8), rgb("6a4a3a"), shape="cyl", tag="furniture")
        box(f"LobbyPlant{i}", (px, 1.4, pz), (1.2, 1.4, 1.2), rgb("2a5a2a"), "nocollide", "tree", "sphere")
    box("LobbyChandelier", (18, LOBBY - 0.6, -224), (2.0, 0.4, 2.0), gold, "emissive", "glass", shape="sphere")
    T.glow((18, LOBBY - 1.2, -224), rgb("ffe0a0"), 14, 1.0)
    # the fire escape up the east face: a landing per floor and stairs between them, all the way to the roof
    FEX = GX1 + 1.6
    # Two lanes (flights alternate between them so they never overlap) and two landing spots:
    # A at the north end, B one flight (14 steps of 0.25 m, 4.9 m long) further south.
    RUN = 14 * 0.35
    A0 = -218.5            # landing A runs A0 .. A0 + 3
    B1 = A0 - RUN          # landing B runs B1 - 3 .. B1
    iron = rgb("2a2a30")
    for f in range(FLOORS + 1):
        y = LOBBY + f * FH
        zc = A0 + 1.5 if f % 2 == 0 else B1 - 1.5
        box(f"FireLanding{f}", (FEX, y - 0.1, zc), (2.6, 0.2, 3.0), iron, tag="stairs")
        box(f"FireRail{f}", (FEX + 1.3, y + 0.5, zc), (0.08, 1.0, 3.0), iron)
    # from the pavement up to the first landing (18 steps), on the outer lane
    T.stairs("FireStairsGround_", FEX, FEX + 1.2, A0 - 18 * 0.35, 0.0, 18, 1, 9, iron)
    for f in range(FLOORS):
        if f % 2 == 0:   # A down to B, inner lane
            T.stairs(f"FireStairsF{f}_", FEX - 1.2, FEX, A0, LOBBY + f * FH, 14, -1, 9, iron)
        else:            # B back up to A, outer lane
            T.stairs(f"FireStairsF{f}_", FEX, FEX + 1.2, B1, LOBBY + f * FH, 14, 1, 9, iron)
    box("TowerRoofRail", (18, LOBBY + TH + 1.3, GZ0 - 0.2), (24.6, 1.0, 0.1), rgb("2a2a30"))
    box("RoofDoorHut", (8, LOBBY + TH + 1.8, -216), (3, 2.8, 3), concrete_d, tag="building")
    T.room("The roof of Gloamwood Tower", 9, GX0, GX1 + 3, GZ0, GZ1, LOBBY + TH - 1, LOBBY + TH + 20)
    # a bit of street: shops, a diner, a bus stop
    building("TowerDiner", -40, -20, -240, -226, 4.2, rgb("d8d0c0"), rgb("b0282e"), "N", gable=False)
    box("DinerNeon", (-30, 3.6, -225.7), (10, 0.9, 0.1), rgb("ff6aa0"), "emissive", "glass")
    building("TowerLaundry", -14, 0, -240, -228, 4.0, rgb("8a9a9a"), rgb("2e2a3a"), "N", gable=False)
    building("TowerShops", 40, 70, -240, -226, 5.5, rgb("7a3e32"), rgb("2e2a3a"), "N", gable=False)
    box("BusStop", (-10, 1.3, -205), (4, 0.15, 1.6), rgb("2a2a30"))
    for side in (-1, 1):
        box(f"BusStopPost{side}", (-10 + side * 1.9, 0.65, -205.6), (0.1, 1.3, 0.1), rgb("2a2a30"))
    box("BusStopSign", (-12.4, 2.0, -204.6), (0.1, 0.8, 0.8), rgb("e8c040"), shape="cyl", r=(0, 0, 90))
    for i in range(3):
        cx_ = -30 + i * 9
        col = [rgb("6a2a2a"), rgb("2a4a6a"), rgb("4a4a3a")][i]
        box(f"ParkedCar{i}", (cx_, 0.7, -200), (4.2, 1.0, 1.9), col, tag="furniture")
        box(f"ParkedCar{i}Top", (cx_ - 0.3, 1.5, -200), (2.2, 0.7, 1.7), col, tag="furniture")
    for i in range(6):
        T.decor("streetlamp", (-48 + i * 22, 0, -195), 180)
    curio("tower-lift", "The lift button for 13", "button", "the Gloamwood Tower lobby",
          "Somebody has pressed it so often the number has worn off. There is no thirteenth floor on the plans.", (24.5, 0, GZ0 + 1.5))
    curio("tower-letter", "An unopened letter", "letter", "post box 8 in the lobby",
          "Addressed to Flat 13B. Postmarked 1974, 1985, 1999 and last Tuesday.", (GX1 - 1.5, 0, -228))
    curio("tower-roof", "A deckchair facing the moon", "chair", "the roof of Gloamwood Tower",
          "Two mugs beside it, both still warm. You climbed fourteen floors for this view. It's worth it.", (14, LOBBY + TH + 0.8, -228))

    # -------------------------------------------------------------------------------------------
    # Gull Harbor and Saltmarsh Lighthouse (east)
    # -------------------------------------------------------------------------------------------
    region("harbor", "Gull Harbor", "harbor",
           "The fishing port. The boats are tied up, the fish market's shut, and the lighthouse keeper hasn't been seen since the fog.",
           236, SEA_X + 70, -120, 100)
    quay = rgb("6a6660")
    ground("Quay", 236, SEA_X, -120, 100, quay, top=0.0, tag="path", tile=40)
    box("SeaWall", (SEA_X - 0.4, 0.5, -10), (0.8, 1.0, 220), rgb("4a4a50"), tag="stone")
    for i in range(22):
        T.decor("crow" if i % 7 == 0 else "luminaria" if i % 5 == 0 else "bench", (SEA_X - 3, 0, -110 + i * 10), -90) if i % 3 == 0 else None
    wood = rgb("5b4027")
    piers = [(-80, 44), (-30, 56), (20, 40)]
    for k, (pz, plen) in enumerate(piers):
        box(f"Pier{k}", (SEA_X + plen / 2, 0.6, pz), (plen, 0.3, 4.5), wood, tag="deck")
        for i in range(int(plen // 4)):
            for side in (-1, 1):
                box(f"Pier{k}Post{i}{side}", (SEA_X + 2 + i * 4, 0.2, pz + side * 2.1), (0.35, 1.6, 0.35), rgb("3a2a1c"), shape="cyl")
        # a fishing boat tied up beside each pier
        bx_, bz_ = SEA_X + plen * 0.6, pz + 6
        col = [rgb("b0282e"), rgb("2a5a7a"), rgb("e8e0d0")][k]
        box(f"Boat{k}Hull", (bx_, 0.6, bz_), (10, 1.6, 3.4), col, tag="furniture")
        box(f"Boat{k}Bow", (bx_ + 5.6, 0.7, bz_), (2.4, 1.4, 2.4), col, tag="furniture", r=(0, 45, 0))
        box(f"Boat{k}Deck", (bx_, 1.45, bz_), (10.4, 0.12, 3.6), wood, tag="deck")
        box(f"Boat{k}Cabin", (bx_ - 2, 2.4, bz_), (3, 1.8, 2.6), rgb("e8e0d0"), tag="building")
        box(f"Boat{k}CabinWin", (bx_ - 0.48, 2.6, bz_), (0.08, 0.6, 1.8), rgb("ffcf7a") if k != 1 else rgb("1a1c26"), "emissive" if k != 1 else "solid", "glass")
        box(f"Boat{k}Mast", (bx_ + 1.5, 5, bz_), (0.2, 7, 0.2), wood, shape="cyl")
        box(f"Boat{k}Lamp", (bx_ + 1.5, 8.6, bz_), (0.3, 0.3, 0.3), rgb("ffb35a"), "emissive", "glass", shape="sphere")
        T.glow((bx_ + 1.5, 8.2, bz_), rgb("ffb35a"), 9, 0.7)
    # warehouses, the harbour master's office, the fish market, crates and barrels, a crane
    for i, (wx, wz) in enumerate(((256, -100), (256, -70), (256, -40))):
        building(f"Warehouse{i}", wx - 14, wx + 14, wz - 10, wz + 10, 8, [rgb("6a3a2a"), rgb("4a5a5a"), rgb("5a4a3a")][i], rgb("2e2a3a"), "E")
    building("HarbourMaster", 290, 304, 40, 52, 6, rgb("e8e0d0"), rgb("2a5a7a"), "E")
    box("HarbourClock", (304.2, 5, 46), (0.2, 1.4, 1.4), rgb("f2ece2"), shape="cyl", r=(0, 0, 90))
    for i in range(4):
        sx = 280 + i * 7
        box(f"FishStall{i}", (sx, 1.0, -8), (5, 0.9, 2.4), rgb("e8e0d0"), tag="furniture")
        for k in range(4):
            box(f"FishStall{i}Canopy{k}", (sx - 1.9 + k * 1.25, 2.6, -8), (1.25, 0.1, 2.8), rgb("2a5a7a") if k % 2 else rgb("e8e0d0"), tag="roof")
        for side in (-1, 1):
            box(f"FishStall{i}Post{side}", (sx + side * 2.4, 1.3, -9.1), (0.1, 2.6, 0.1), rgb("e8e0d0"))
    for i in range(18):
        cx_, cz_ = rng.uniform(276, 334), rng.uniform(-110, 90)
        if abs(cz_ + 8) < 4 or (288 < cx_ < 306 and 38 < cz_ < 54):
            continue
        if rng.random() < 0.5:
            s = rng.uniform(0.8, 1.4)
            box(f"Crate{i}", (cx_, s / 2, cz_), (s, s, s), rgb("8a6a3a"), tag="furniture", r=(0, rng.uniform(0, 90), 0))
        else:
            box(f"Barrel{i}", (cx_, 0.6, cz_), (0.9, 0.6, 0.9), rgb("5a3a22"), shape="cyl", tag="furniture")
    box("CraneBase", (322, 5, -60), (2, 10, 2), rgb("e8b030"))
    box("CraneArm", (330, 10.4, -60), (18, 0.8, 0.8), rgb("e8b030"))
    box("CraneCable", (338, 7.5, -60), (0.06, 5, 0.06), rgb("2a2a30"))
    box("Bob_CraneHook", (338, 4.8, -60), (0.5, 0.6, 0.3), rgb("2a2a30"))
    for i in range(8):
        T.decor("streetlamp", (244, 0, -110 + i * 26), 90)
    # the breakwater and Saltmarsh Lighthouse at its end
    LX, LZ = SEA_X + 58, 70.0
    for i in range(16):
        a = rng.uniform(-0.6, 0.6)
        box(f"Breakwater{i}", (SEA_X + 4 + i * 3.4, 0.5, 70 + rng.uniform(-1.2, 1.2)), (3.6, 1.6 + rng.uniform(0, 0.8), 4 + rng.uniform(0, 1.5)), rgb("4a4a52"), tag="stone", r=(a * 10, rng.uniform(0, 40), a * 8))
    box("BreakwaterPath", (SEA_X + 28, 1.1, 70), (56, 0.3, 2.6), rgb("6a6660"), tag="path")
    box("LighthouseRock", (LX, 0.8, LZ), (16, 2.0, 16), rgb("3e3e46"), shape="cyl", tag="stone")
    bands = [rgb("f2ece2"), rgb("b0282e")]
    for k in range(7):
        w = 6.4 - k * 0.42
        box(f"LighthouseBand{k}", (LX, 2.0 + k * 2.6 + 1.3, LZ), (w, 1.3, w), bands[k % 2], shape="cyl", tag="building")
    top = 2.0 + 7 * 2.6
    box("LighthouseGallery", (LX, top + 0.2, LZ), (5.6, 0.25, 5.6), rgb("2a2a30"), shape="cyl")
    box("LighthouseRail", (LX, top + 0.9, LZ), (5.4, 0.6, 5.4), rgb("2a2a30"), "nocollide", shape="cyl")
    box("LighthouseLamp", (LX, top + 1.9, LZ), (2.6, 1.6, 2.6), rgb("fff2c8"), "emissive", "glass", shape="cyl")
    box("LighthouseCap", (LX, top + 3.0, LZ), (3.4, 0.6, 3.4), rgb("2a2a30"), shape="cyl", tag="roof")
    box("LighthouseCap2", (LX, top + 3.6, LZ), (2.0, 0.6, 2.0), rgb("2a2a30"), shape="cyl", tag="roof")
    box("LighthouseVane", (LX, top + 4.4, LZ), (0.1, 1.0, 0.1), rgb("2a2a30"))
    box("Spin_LighthouseBeam", (LX + 12, top + 1.9, LZ), (24, 1.2, 1.2), rgb("fff2c8"), "nocollide", "beam")
    box("LighthouseDoor", (LX - 3.15, 3.2, LZ), (0.2, 2.4, 1.3), rgb("2a3a5a"), tag="building")
    T.glow((LX, top + 1.9, LZ), rgb("fff2c8"), 30, 1.6)
    # An iron stair spirals up the outside, from the rock by the door to the gallery (two turns).
    rock_top, gallery_top = 1.8, top + 0.33
    n_steps = int(round((gallery_top - rock_top) / 0.25))
    for k in range(n_steps):
        y = rock_top + (k + 1) * (gallery_top - rock_top) / n_steps
        band = min(6, max(0, int((y - 2.0) // 2.6)))
        rb = (6.4 - band * 0.42) / 2
        a = math.radians(200 + k * 9.6)
        R = rb + 0.7
        box(f"LighthouseStep{k}", (LX + math.cos(a) * R, y - 0.08, LZ + math.sin(a) * R), (1.4, 0.16, 0.62),
            rgb("2a2a30"), tag="stairs", r=(0, -math.degrees(a), 0))
        if k % 3 == 0:  # a post for the handrail
            box(f"LighthouseStepPost{k}", (LX + math.cos(a) * (R + 0.66), y + 0.45, LZ + math.sin(a) * (R + 0.66)), (0.05, 0.9, 0.05), rgb("2a2a30"), "nocollide")
    box("KeeperCottage", (LX - 4, 2.9, LZ + 7), (5, 2.6, 4), rgb("e8e0d0"), tag="building")
    box("KeeperCottageRoof", (LX - 4, 4.6, LZ + 7), (5.6, 0.8, 4.6), rgb("b0282e"), tag="roof")
    box("KeeperCottageWin", (LX - 1.44, 3.0, LZ + 7), (0.1, 0.9, 1.0), rgb("1a1c26"), tag="glass")
    T.room("Saltmarsh Lighthouse", 9, LX - 8, LX + 8, LZ - 8, LZ + 8, -1, 30)
    curio("harbor-bottle", "A message in a bottle", "bottle", "the end of the long pier",
          "'If you find this, the fog is not fog. Tell the keeper to keep the lamp lit. — S.' It is dated tomorrow.", (SEA_X + 54, 0.75, -30))
    curio("harbor-log", "The keeper's logbook", "book", "the lighthouse door",
          "The last entry: 'Lamp lit. Fog thick. Someone is knocking from the sea side.' The rest of the page is wet.", (LX - 4.2, 1.8, LZ + 1.5))
    curio("harbor-hook", "A gold tooth on a fish hook", "tooth", "the fish market",
          "The fishmonger swears it came out of a cod. The cod, she says, was grinning.", (283, 0, -10.5))
    curio("harbor-anchor", "A tiny anchor charm", "anchor", "a fishing boat by the middle pier",
          "Sailors give them to children for luck. This one is engraved 'for Pip, come home'.", (SEA_X + 33.6 - 2, 1.5, -24))

    # -------------------------------------------------------------------------------------------
    # Wreckers' Beach, the ghost ship and Smugglers' Cave (north-east)
    # -------------------------------------------------------------------------------------------
    region("beach", "Wreckers' Beach", "beach",
           "A long curve of sand under the cliffs. A ship ran aground here in 1847 and its lantern still swings.",
           236, SEA_X + 40, 100, 300)
    sand = rgb("b8a070")
    ground("Sand", 236, SEA_X, 100, 300, sand, top=0.02, tag="path", tile=40)
    box("Boardwalk", (248, 0.25, 200), (6, 0.3, 190), wood, tag="deck")
    for i in range(6):  # beach huts in a row
        hz = 120 + i * 11
        col = [rgb("e88aa8"), rgb("8ad0e8"), rgb("e8e070"), rgb("8ae8a8"), rgb("c8a0e8"), rgb("e8b07a")][i]
        box(f"BeachHut{i}", (258, 1.5, hz), (3.2, 3, 3.2), col, tag="building")
        box(f"BeachHut{i}Stripe", (259.62, 1.5, hz), (0.05, 3, 1.0), rgb("f2ece2"), tag="building")
        box(f"BeachHut{i}RoofA", (258, 3.4, hz - 0.85), (3.4, 0.15, 1.9), rgb("2a2a30"), tag="roof", r=(-28, 0, 0))
        box(f"BeachHut{i}RoofB", (258, 3.4, hz + 0.85), (3.4, 0.15, 1.9), rgb("2a2a30"), tag="roof", r=(28, 0, 0))
    for i in range(5):
        ux, uz = rng.uniform(280, 325), rng.uniform(115, 235)
        box(f"Umbrella{i}Pole", (ux, 1.1, uz), (0.08, 2.2, 0.08), rgb("e8e0d0"), shape="cyl")
        box(f"Umbrella{i}", (ux, 2.2, uz), (2.6, 0.25, 2.6), [rgb("b0282e"), rgb("2a5a7a")][i % 2], shape="cyl", tag="roof")
    box("LifeguardTower", (300, 2.2, 180), (2.4, 0.3, 2.4), rgb("e8e0d0"))
    for i in range(4):
        box(f"LifeguardLeg{i}", (300 + (1 if i % 2 else -1), 1.0, 180 + (1 if i < 2 else -1)), (0.2, 2.2, 0.2), rgb("e8e0d0"))
    box("LifeguardHut", (300, 3.2, 180), (2.0, 1.8, 2.0), rgb("b0282e"), tag="building")
    box("Bonfire", (290, 0.3, 150), (2, 0.6, 2), rgb("3a2a1c"), shape="cyl")
    box("BonfireFlame", (290, 0.9, 150), (1.2, 1.4, 1.2), rgb("ff8a3a"), "emissive", "glass", shape="sphere")
    T.glow((290, 1.6, 150), rgb("ff8a3a"), 12, 1.5)
    for i in range(6):
        a = i / 6 * math.tau
        box(f"BonfireLog{i}", (290 + math.cos(a) * 2.6, 0.25, 150 + math.sin(a) * 2.6), (1.6, 0.5, 0.5), rgb("5a3a22"), shape="capsule", r=(0, -math.degrees(a), 90))
    box("Sandcastle", (310, 0.4, 130), (2, 0.8, 2), rgb("c8b080"), tag="furniture")
    for i in range(4):
        box(f"SandcastleTower{i}", (309.2 + (1.6 if i % 2 else 0), 1.0, 129.2 + (1.6 if i > 1 else 0)), (0.5, 1.2, 0.5), rgb("c8b080"), shape="cyl", tag="furniture")
    for i in range(8):
        box(f"Driftwood{i}", (rng.uniform(300, 336), 0.15, rng.uniform(110, 240)), (rng.uniform(1.5, 3.5), 0.3, 0.35), rgb("9a8a70"), tag="furniture", r=(0, rng.uniform(0, 180), 0))
    # the ghost ship, run aground and listing, its lantern still lit
    SX, SZ = 330.0, 205.0
    box("WreckHull", (SX, 2.0, SZ), (7, 4.5, 26), rgb("3a2a1e"), tag="building", r=(0, 12, 14))
    box("WreckDeck", (SX - 0.4, 4.2, SZ), (6.4, 0.25, 25), rgb("4a3a28"), tag="deck", r=(0, 12, 14))
    box("WreckBow", (SX - 2.6, 2.5, SZ + 13.5), (4.5, 3.5, 4.5), rgb("3a2a1e"), tag="building", r=(0, 57, 14))
    box("WreckMainMast", (SX - 1.5, 10, SZ), (0.5, 14, 0.5), rgb("3a2a1e"), shape="cyl", r=(0, 12, 14))
    box("WreckBrokenMast", (SX + 3, 1.2, SZ - 9), (0.45, 9, 0.45), rgb("3a2a1e"), shape="cyl", r=(80, 30, 0))
    box("WreckSail", (SX - 2.3, 10.5, SZ + 0.2), (0.08, 7, 6), rgb("c8c4b8"), "ghost", "sail", r=(0, 12, 14))
    box("WreckSail2", (SX - 2.0, 7.5, SZ - 5), (0.08, 4, 5), rgb("c8c4b8"), "ghost", "sail", r=(0, 12, 20))
    box("Bob_WreckLantern", (SX - 3.4, 8.0, SZ + 11), (0.5, 0.7, 0.5), rgb("9fffc0"), "emissive", "glass")
    T.glow((SX - 3.4, 7.6, SZ + 11), rgb("9fffc0"), 14, 1.2)
    for i in range(5):
        box(f"WreckPort{i}", (SX - 3.6, 2.6, SZ - 8 + i * 4), (0.1, 0.6, 0.6), rgb("9fffc0") if i in (1, 3) else rgb("1a1c26"), "emissive" if i in (1, 3) else "solid", "glass", shape="cyl", r=(0, 0, 90))
    T.room("The wreck of the Mary Grey", 9, SX - 8, SX + 8, SZ - 15, SZ + 15, -2, 20)
    # the cliffs to the north, and Smugglers' Cave in them
    rock, rock_d = rgb("4a4640"), rgb("36332f")
    CZ_ = 262.0
    for i in range(18):  # the cliff face: big leaning blocks
        x = 238 + i * 6
        if 288 < x < 300:
            continue  # the cave mouth
        h = 14 + rng.uniform(-3, 6)
        box(f"Cliff{i}", (x, h / 2 - 0.5, CZ_ + 6 + rng.uniform(-1, 1)), (6.8, h, 14 + rng.uniform(0, 4)), rock if i % 2 else rock_d, tag="stone", r=(rng.uniform(-4, 4), rng.uniform(-6, 6), rng.uniform(-3, 3)))
    box("CliffTop", (290, 17, 288), (120, 6, 40), rock_d, tag="stone")
    box("CliffGrass", (290, 20.1, 290), (120, 0.3, 36), rgb("2e3a26"), tag="ground")
    # the cave: a passage into the cliff and a chamber at the end
    box("CaveArch", (294, 8.5, CZ_ + 0.5), (12, 7, 3), rock_d, tag="stone")
    box("CaveRoof", (294, 7.0, CZ_ + 14), (12, 2, 24), rock_d, tag="stone")
    for side in (-1, 1):
        box(f"CaveWall{side}", (294 + side * 5.5, 3.0, CZ_ + 14), (1.5, 6.2, 24), rock, tag="stone")
    box("CaveFloor", (294, 0.05, CZ_ + 14), (10, 0.1, 24), rgb("5a5248"), tag="floor")
    box("CaveBack", (294, 3.0, CZ_ + 26.5), (12, 6.2, 1.5), rock, tag="stone")
    T.room("Smugglers' Cave", 9, 288, 300, CZ_, CZ_ + 26, -1, 7)
    for i in range(10):  # stalactites, glowing mushrooms, crystals
        sx = 290 + rng.uniform(0, 8)
        sz = CZ_ + 4 + i * 2.1
        box(f"Stalactite{i}", (sx, 5.4, sz), (0.3, 1.2 + rng.uniform(0, 0.8), 0.3), rock, shape="cyl")
        if i % 2 == 0:
            box(f"CaveMushroom{i}", (290 + (i % 4) * 2.6, 0.25, sz), (0.4, 0.25, 0.4), rgb("6affd0"), "emissive", "glass", shape="sphere")
        if i % 3 == 0:
            box(f"CaveCrystal{i}", (289.4 if i % 2 else 298.6, 0.8, sz), (0.4, 1.4, 0.4), rgb("b48cff"), "emissive", "glass", r=(0, 0, 15 if i % 2 else -15))
    T.glow((294, 2.4, CZ_ + 10), rgb("6affd0"), 10, 0.8)
    T.glow((294, 2.4, CZ_ + 22), rgb("b48cff"), 10, 0.9)
    box("TreasureChest", (294, 0.45, CZ_ + 24.5), (1.4, 0.8, 0.9), rgb("5a3a1e"), tag="furniture")
    box("TreasureChestLid", (294, 1.1, CZ_ + 24.9), (1.4, 0.15, 0.9), rgb("5a3a1e"), tag="furniture", r=(-50, 0, 0))
    box("TreasureGold", (294, 0.9, CZ_ + 24.5), (1.2, 0.2, 0.7), gold, "emissive", "glass")
    T.glow((294, 1.4, CZ_ + 24.0), gold, 6, 0.9)
    T.decor("skeleton", (291, 0, CZ_ + 23.5), 30)
    T.decor("lantern", (297, 0, CZ_ + 18), 0)
    box("TidePool", (296, 0.06, CZ_ + 8), (3, 0.05, 2.2), rgb("2d6a8a"), "emissive", "glass", shape="cyl")
    curio("beach-shell", "A whispering shell", "shell", "the beach huts",
          "Hold it to your ear: not the sea, but someone humming a sea shanty, a little off-key.", (261, 0.02, 153))
    curio("beach-figurehead", "The figurehead's lost eye", "gem", "the wreck of the Mary Grey",
          "A green glass eye. The figurehead on the bow has an empty socket, and is looking for it.", (SX - 6, 0.02, SZ + 16))
    curio("beach-map", "A smuggler's map", "map", "Smugglers' Cave",
          "X marks the spot. The spot is the Hollow Creek Historical Society. Interesting.", (291.5, 0, CZ_ + 20))
    curio("beach-coin", "A doubloon dated 1699", "coin", "the bonfire on the sand",
          "Still warm from the fire. Pirates once came ashore here; the town only admits to 'traders'.", (293, 0.02, 152.5))

    # -------------------------------------------------------------------------------------------
    # Hag's Hollow, the swamp (south-west)
    # -------------------------------------------------------------------------------------------
    region("swamp", "Hag's Hollow", "swamp",
           "A drowned wood where the will-o'-the-wisps come from. Old Mother Gloam's cottage leans further every year.",
           -350, -200, -260, -120)
    ground("Swamp", -350, -200, -260, -120, rgb("2a3424"), top=-0.02, tag="patch", tile=50)
    for i in range(14):  # murky pools
        px, pz = rng.uniform(-340, -210), rng.uniform(-250, -130)
        if -290 < px < -255 and -215 < pz < -175:
            continue
        w = rng.uniform(5, 12)
        box(f"SwampPool{i}", (px, 0.0, pz), (w, 0.05, w * rng.uniform(0.6, 1.0)), rgb("2a4a3a"), "glass", "water", shape="cyl")
    for i in range(22):  # dead trees
        tx_, tz_ = rng.uniform(-345, -205), rng.uniform(-255, -125)
        if -290 < tx_ < -255 and -215 < tz_ < -175:
            continue
        tree(f"SwampTree{i}", tx_, tz_, rng.uniform(6, 11))
    # boardwalk to the cottage
    for i in range(14):
        box(f"SwampPlank{i}", (-270 + rng.uniform(-0.3, 0.3), 0.2, -124 - i * 4.2), (2.4, 0.15, 3.6), rgb("4a3a28"), tag="deck", r=(0, rng.uniform(-6, 6), 0))
    # Old Mother Gloam's crooked cottage
    HX, HZ = -272.0, -195.0
    box("HagCottage", (HX, 2.3, HZ), (7, 4.6, 6), rgb("5a4a3a"), tag="building", r=(0, 8, 4))
    box("HagCottageRoofA", (HX - 0.3, 5.6, HZ - 1.6), (8, 0.3, 4.2), rgb("3a3028"), tag="roof", r=(-35, 8, 6))
    box("HagCottageRoofB", (HX + 0.3, 5.6, HZ + 1.6), (8, 0.3, 4.2), rgb("3a3028"), tag="roof", r=(35, 8, 2))
    box("HagChimney", (HX + 2.4, 7.2, HZ + 0.8), (1.0, 3.2, 1.0), rgb("4a3a32"), r=(0, 0, -10))
    box("Bob_ChimneySmoke", (HX + 2.9, 9.4, HZ + 0.8), (1.2, 1.2, 1.2), rgb("6affa0"), "ghost", "smoke", shape="sphere")
    box("HagDoor", (HX + 0.2, 1.3, HZ - 3.05), (1.2, 2.4, 0.15), rgb("2a1e14"), r=(0, 8, 4))
    for i, wx in enumerate((-2, 2)):
        box(f"HagWindow{i}", (HX + wx, 2.6, HZ - 3.06), (1.0, 0.9, 0.1), rgb("9fff9f"), "emissive", "glass", r=(0, 8, 4))
    T.decor("cauldron", (HX - 2, 0, HZ - 5), 0)
    box("CauldronBrew", (HX - 2, 0.8, HZ - 5), (0.8, 0.1, 0.8), rgb("6affa0"), "emissive", "glass", shape="cyl")
    T.glow((HX - 2, 1.4, HZ - 5), rgb("6affa0"), 9, 1.0)
    T.glow((HX, 2.6, HZ - 4), rgb("9fff9f"), 10, 0.8)
    for i in range(7):
        T.decor("jack_scary" if i % 2 else "turnip", (HX - 4 + i * 1.3, 0, HZ - 6.5), 180)
    for i in range(12):  # little green lights over the water
        T.glow((rng.uniform(-340, -210), 1.2 + rng.uniform(0, 1.5), rng.uniform(-250, -130)), rgb("9fff9f"), 4, 0.6)
    box("Rowboat", (-318, 0.25, -150), (1.6, 0.5, 4), rgb("5a3a22"), tag="furniture", r=(0, 30, 0))
    for i in range(10):
        box(f"Toadstool{i}", (rng.uniform(-345, -205), 0.2, rng.uniform(-255, -125)), (0.5, 0.2, 0.5), rgb("b0282e"), shape="sphere", tag="furniture")
    T.room("Old Mother Gloam's cottage", 9, HX - 4, HX + 4, HZ - 3.5, HZ + 3.5, -1, 8)
    curio("swamp-broom", "A broom with no bristles", "broom", "Old Mother Gloam's porch",
          "The bristles are missing because, a note says, 'they went on ahead'.", (HX + 2, 0, HZ - 4.5))
    curio("swamp-jar", "A jar of fireflies", "jar", "the rowboat in the reeds",
          "Labelled 'Wisp seed. Do not open before the first frost.' They glow brighter when you smile.", (-317, 0.5, -149))
    curio("swamp-recipe", "Half a recipe", "letter", "beside the cauldron",
          "'...three toadstools, one sigh, a spoon of moonlight, and stir widdershins.' The rest is a soup stain.", (HX - 3.4, 0, HZ - 5.6))

    # -------------------------------------------------------------------------------------------
    # Hidden details back in town and along the roads
    # -------------------------------------------------------------------------------------------
    curio("town-gnome", "A garden gnome with fangs", "gnome", "under the bridge on Main Street",
          "Somebody painted tiny fangs on him. He looks thrilled about it.", (-5, 0, 179))
    curio("town-watch", "A stopped pocket watch", "watch", "the bandstand in Town Square",
          "Stopped at 11:57. Every Halloween it's found here; every November it vanishes again.", (-24, 0.6, -25))
    curio("road-sign", "A signpost that points the wrong way", "sign", "the road up to the castle",
          "One arm says 'Ravenhold Castle'. The other says 'Don't'.", (6, 0, 322))
    curio("road-shoe", "A single dancing shoe", "shoe", "the road out to the circus",
          "Red, sequinned, size four. The other one is still dancing somewhere.", (-198, 0, 6))
    curio("road-umbrella", "A black umbrella, still dry", "umbrella", "the road to Gull Harbor",
          "It hasn't rained in a week, yet it's open, and the ground beneath it is wet.", (190, 0, -6))

    # -------------------------------------------------------------------------------------------
    # Wayside spots: little places in the fields and woods between the big ones, for wanderers
    # -------------------------------------------------------------------------------------------
    def clearing(x, z, r):
        out["clear"].append([x - r, z - r, x + r, z + r])

    # The Nine Widows: a ring of standing stones in the hills west of the castle
    clearing(-150, 380, 18)
    box("WidowsMound", (-150, 0.2, 380), (22, 0.6, 22), rgb("33402a"), tag="ground", shape="cyl")
    for i in range(9):
        a = i / 9 * math.tau
        h = 3.2 + (i % 3) * 0.6
        box(f"Widow{i}", (-150 + math.cos(a) * 8, h / 2, 380 + math.sin(a) * 8), (1.3, h, 0.7), rgb("6a6a70"), tag="stone",
            r=(rng.uniform(-6, 6), -math.degrees(a) + 90, rng.uniform(-6, 6)))
    box("WidowsAltar", (-150, 0.6, 380), (2.4, 0.8, 1.4), rgb("55545a"), tag="stone")
    T.glow((-150, 1.6, 380), rgb("b48cff"), 9, 0.9)
    T.decor("crow", (-150, 0.95, 380.3), 40)
    curio("wayside-stones", "A ribbon on the altar stone", "ticket", "the Nine Widows, in the hills west of the castle",
          "Nine stones, nine widows, says the story: they danced on a Sunday and stood still for good. "
          "Somebody leaves a ribbon here every year. This one says 'Still dancing.'", (-150, 1.0, 381.3))

    # Gallows Field (no gallows, just scarecrows): a field of haybales and scarecrows north-east of town
    clearing(190, 255, 26)
    box("StubbleField", (190, -0.02, 255), (46, 0.06, 40), rgb("8a7038"), "nocollide", "patch")
    for i in range(7):
        T.decor("scarecrow", (172 + (i % 4) * 12, 0, 240 + (i // 4) * 18 + (i % 2) * 4), rng.uniform(150, 210))
    for i in range(10):
        T.decor("haybale", (rng.uniform(170, 210), 0, rng.uniform(238, 272)), rng.uniform(0, 180))
    for i in range(14):
        T.decor("crow", (rng.uniform(168, 212), 0, rng.uniform(236, 274)), rng.uniform(0, 360), 0.8)
    for i in range(12):  # a split-rail fence round two sides
        box(f"FieldRail{i}", (168 + i * 3.8, 0.7, 234), (3.8, 0.12, 0.12), C["wood"], tag="fence")
        box(f"FieldPost{i}", (166.1 + i * 3.8, 0.55, 234), (0.2, 1.1, 0.2), C["wood"], tag="fence")
    curio("wayside-scarecrow", "A scarecrow's diary", "book", "the scarecrow field north-east of town",
          "'Day 212. The crows have stopped pretending to be scared. Day 213. Tried a new face. They laughed.'", (199.5, 0, 260.5))

    # The Wishing Well and a crooked oak, in the fields north-west of town
    clearing(-225, 205, 16)
    box("WishingWellWall", (-225, 0.55, 205), (2.6, 1.1, 2.6), rgb("6a6a70"), shape="cyl", tag="stone")
    box("WishingWellWater", (-225, 0.9, 205), (2.1, 0.05, 2.1), rgb("1f3f58"), "emissive", "water", shape="cyl")
    for side in (-1, 1):
        box(f"WishingWellPost{side}", (-225 + side * 1.1, 1.9, 205), (0.18, 1.8, 0.18), C["wood"], tag="fence")
    box("WishingWellRoof", (-225, 3.0, 205), (2.8, 0.15, 1.6), rgb("5a3a22"), tag="roof", r=(0, 0, 0))
    box("WishingWellBucket", (-225, 1.6, 205), (0.4, 0.35, 0.4), rgb("6a4a2a"), shape="cyl", tag="furniture")
    T.tree("WishingOak", -232, 212, 9, rgb("a0402a"))
    T.glow((-225, 1.2, 205), rgb("9fdcff"), 6, 0.7)
    curio("wayside-well", "A wish, fished out of the well", "coin", "the wishing well north-west of town",
          "A penny with a note wrapped round it: 'I wish my brother would stop hiding my lantern. — Tobias, aged 9.'", (-223.2, 0.02, 206.4))

    # Whisker Hill: a little pet cemetery between the swamp and the tower
    clearing(-140, -190, 16)
    box("WhiskerHill", (-140, 0.15, -190), (20, 0.5, 18), rgb("2e3a26"), tag="ground", shape="cyl")
    names_rng = random.Random(7)
    for i in range(14):
        x, z = -146 + (i % 5) * 3, -195 + (i // 5) * 3.6
        T.decor("tomb_round" if names_rng.random() < 0.6 else "tomb_cross", (x, 0.35, z), 180 + names_rng.uniform(-12, 12), 0.55)
    for i in range(8):  # a little picket fence on the south side
        box(f"WhiskerPicket{i}", (-150 + i * 2.8, 0.75, -199.5), (0.12, 0.9, 0.12), rgb("e8e0d0"), tag="fence")
    box("WhiskerRail", (-140.2, 0.95, -199.5), (20, 0.1, 0.08), rgb("e8e0d0"), tag="fence")
    T.decor("cat", (-139, 0.35, -186), 200)
    T.decor("luminaria", (-142, 0.35, -191), 0)
    T.decor("luminaria", (-136, 0.35, -191), 0)
    T.glow((-139, 1.0, -189), rgb("ffcf7a"), 7, 0.8)
    curio("wayside-collar", "A bell on a collar", "watch", "Whisker Hill, the pet cemetery",
          "The tag says 'Midnight'. When the wind blows, the bell rings, and somewhere a cat answers.", (-133.5, 0.35, -188))

    # The old mine in the north-east hills: a timber-framed adit, rails and a cart
    clearing(125, 430, 18)
    box("MineHill", (125, 3.5, 440), (34, 7.0, 18), rgb("2e3a26"), tag="ground")
    box("MineMouth", (125, 1.6, 430.9), (4.0, 3.2, 0.2), rgb("0a0a0e"), "solid", "glass")
    for side in (-1, 1):
        box(f"MineProp{side}", (125 + side * 2.2, 1.8, 430.6), (0.4, 3.6, 0.4), C["wood"], tag="fence")
    box("MineLintel", (125, 3.7, 430.6), (5.0, 0.45, 0.45), C["wood"], tag="fence")
    box("MineSign", (125, 4.4, 430.5), (3.0, 0.7, 0.1), rgb("c8b48a"), tag="sign")
    for side in (-0.6, 0.6):
        box(f"MineRail{side}", (125 + side, 0.05, 422), (0.1, 0.1, 18), rgb("4a4a52"), "nocollide", "road")
    for i in range(9):
        box(f"MineSleeper{i}", (125, 0.03, 414 + i * 2), (2.0, 0.08, 0.35), C["wood"], "nocollide", "road")
    box("MineCart", (125, 0.7, 418), (1.6, 1.0, 2.2), rgb("5a4a3a"), tag="furniture")
    T.decor("lantern", (123.2, 3.0, 430.3), 0)
    T.glow((125, 2.4, 429), rgb("ffb35a"), 7, 0.8)
    curio("wayside-canary", "An empty birdcage", "jar", "the old mine in the north-east hills",
          "A miner's canary cage, door open. Scratched inside: 'She sang the whole way out. We followed her.'", (127.6, 0, 428.2))

    # The roads continue past the regions to the horizon (Horizon.cs draws those); trees stay off them.
    return out
