#!/usr/bin/env python3
"""
Designs the haunted houses of Hollow Creek (other than Blackwood Manor, which has its own script)
and writes each one to Assets/Unmasked/Resources/Houses/<Id>.json.

The houses differ on purpose, from a quick case to a long night:

  Pemberton Cottage       small     a tidy one-storey cottage, picket fence, garden shed
  Hollow Creek Farm       medium    two-storey farmhouse, red barn with a hayloft, corn maze, windmill
  Willow Lane Victorian   large     two storeys and a tower, wraparound porch, a nursery trapdoor
  Blackwood Manor         huge      (make_manor.py) cellar, two floors, roof, cemetery, greenhouse
  Historical Society      large     the fifth call: a museum with a mask gallery, reading room, archive

Every house has the same gameplay hooks as the manor: rooms, a spot for each of the four suspects,
clue spots, trap pieces, a trap site, where the Solvers arrive, and where the Haunter lurks.
Each is built in its own local space with the front door facing the road (-z); make_town.py places
them on their lots.

    python3 Docs/tools/make_houses.py
"""
import math
import random

from layoutlib import Layout, rgb, facing
import dressing as hw

STOREY = 3.25
OUTER, INNER = 0.3, 0.15


def win(c, w=1.2, lo=1.0, hi=2.3):
    return (c, w, lo, hi, "window")


def gap(c, w=1.2):
    return (c, w, 0, 2.3, "door")


def shell(H, name, x0, x1, z0, z1, y0, h, level, color, openings, glass=None, trim=None):
    """Four outer walls. openings: {'S': [...], 'N': [...], 'W': [...], 'E': [...]}."""
    t = OUTER
    H.wall(f"{name}S", "x", z0, x0 - t / 2, x1 + t / 2, y0, h, level, color, t, openings.get("S", ()), glass=glass, trim=trim)
    H.wall(f"{name}N", "x", z1, x0 - t / 2, x1 + t / 2, y0, h, level, color, t, openings.get("N", ()), glass=glass, trim=trim)
    H.wall(f"{name}W", "z", x0, z0 + t / 2, z1 - t / 2, y0, h, level, color, t, openings.get("W", ()), glass=glass, trim=trim)
    H.wall(f"{name}E", "z", x1, z0 + t / 2, z1 - t / 2, y0, h, level, color, t, openings.get("E", ()), glass=glass, trim=trim)


def inner(H, name, axis, fixed, a0, a1, y0, h, level, color, openings=()):
    H.wall(name, axis, fixed, a0, a1, y0, h, level, color, INNER, openings)


def door_x(H, name, c, z, y, w, level):
    """A door in a wall that runs along x (z fixed), centred at x=c."""
    H.door((c - w / 2, y, z), 90, w, level, name)


def door_z(H, name, x, c, y, w, level):
    """A door in a wall that runs along z (x fixed), centred at z=c."""
    H.door((x, y, c - w / 2), 0, w, level, name)


def lawn(H, x0, x1, z0, z1, holes, color):
    H.slab("Lawn", 0.0, x0, x1, z0, z1, holes, color, 9, 0.4, "ground")


def path(H, name, x0, x1, z0, z1, color):
    H.box(name, ((x0 + x1) / 2, 0.02, (z0 + z1) / 2), (x1 - x0, 0.06, z1 - z0), color, 9, "solid", "ground")


def porch(H, name, x0, x1, z0, z1, top, color, post_color, roof_color, roof_y, level=9, posts_on=("S",)):
    H.box(f"{name}Deck", ((x0 + x1) / 2, top / 2, (z0 + z1) / 2), (x1 - x0, top, z1 - z0), color, level, "solid", "floor")
    xs = [x0 + 0.2 + i * (x1 - x0 - 0.4) / max(1, round((x1 - x0) / 3)) for i in range(round((x1 - x0) / 3) + 1)]
    for i, x in enumerate(xs):
        H.box(f"{name}Post{i}", (x, top + (roof_y - top) / 2, z0 + 0.2), (0.18, roof_y - top, 0.18), post_color, level, "solid", "porch")
    H.box(f"{name}Roof", ((x0 + x1) / 2, roof_y + 0.08, (z0 + z1) / 2), (x1 - x0 + 0.4, 0.16, z1 - z0 + 0.4), roof_color, level, "solid", "roof",
          r=(-8, 0, 0))


def grave(H, name, x, z, color):
    H.box(name, (x, 0.45, z), (0.7, 0.9, 0.18), color, 9, "solid", "grave")
    H.box(f"{name}Top", (x, 0.92, z), (0.5, 0.12, 0.16), color, 9, "solid", "grave")


def jack_line(H, x0, z0, x1, z1, n, ry=180, sc=0.9, glow_every=2, level=9, y=0.0):
    for i in range(n):
        f = i / max(1, n - 1)
        x, z = x0 + (x1 - x0) * f, z0 + (z1 - z0) * f
        H.decor("jack", (x, y, z), ry, sc, level)
        if i % glow_every == 0:
            H.glow((x, y + 0.4, z), rgb("ff9a3a"), 4.5, 0.9, level)


# =============================================================================
# Pemberton Cottage: small and tidy, a quick case
# =============================================================================
def cottage():
    H = Layout("Pemberton Cottage", "PembertonCottage", "Cottage",
               "A tidy little cottage with a white picket fence. Mrs. Pemberton swears her teapot "
               "rattles at midnight. Small and quick: one floor, a garden and a shed.")
    H.L["size"] = "Small"
    H.L["storey"] = 3.0
    C = {"wall": rgb("e6d39a"), "inner": rgb("d8cdb5"), "trim": rgb("f2efe6"), "roof": rgb("7a3b2e"), "floor": rgb("8a5a3a"),
         "tile": rgb("b9c4c9"), "grass": rgb("2f4a2a"), "path": rgb("9a8f7c"), "wood": rgb("6b4426"), "sofa": rgb("4a6a8a"),
         "red": rgb("a83232"), "white": rgb("e8e4da"), "shed": rgb("6b7a5a"), "brick": rgb("8a4a3a")}
    X0, X1, Z0, Z1, CEIL = -7.0, 7.0, -5.0, 5.0, 3.0
    LX0, LX1, LZ0, LZ1 = -15.0, 15.0, -13.0, 13.0

    lawn(H, LX0, LX1, LZ0, LZ1, [(X0, X1, Z0, Z1)], C["grass"])
    H.slab("Floor", 0.0, X0, X1, Z0, Z1, [], C["floor"], 0, 0.3)
    H.box("KitchenTiles", (4, 0.01, -2), (5.8, 0.02, 5.8), C["tile"], 0, "nocollide", "floor")
    path(H, "FrontPath", -0.7, 0.7, LZ0, -7.0, C["path"])
    path(H, "ShedPath", 7.0, 10.6, -2.6, -1.4, C["path"])
    path(H, "ShedPath2", 9.4, 10.6, -2.6, 6.5, C["path"])
    porch(H, "Porch", -3.0, 3.0, -7.0, -5.0, 0.15, C["wood"], C["trim"], C["roof"], 2.8)

    shell(H, "Outer", X0, X1, Z0, Z1, 0.0, CEIL, 0, C["wall"], {
        "S": [gap(0.0), win(-4.5, 1.6), win(4.5, 1.6)],
        "N": [win(-4.0), win(1.5, 0.8, 1.4, 2.2), win(5.0)],
        "W": [win(-2.0), win(3.0)],
        "E": [gap(-2.0), win(3.0)],
    }, trim=C["trim"])
    inner(H, "WallHall", "x", 1.0, X0 + 0.15, X1 - 0.15, 0, CEIL, 0, C["inner"], [gap(-3.5, 1.0), gap(1.5, 0.9), gap(5.0, 1.0)])
    inner(H, "WallKitchen", "z", 1.0, Z0 + 0.15, 1.0, 0, CEIL, 0, C["inner"], [gap(-2.0, 1.8)])
    inner(H, "WallBath", "z", 0.0, 1.0, Z1 - 0.15, 0, CEIL, 0, C["inner"])
    inner(H, "WallStudy", "z", 3.0, 1.0, Z1 - 0.15, 0, CEIL, 0, C["inner"])
    H.ceiling("Ceiling", CEIL, X0, X1, Z0, Z1, C["white"])
    H.gable_roof("Roof", X0, X1, Z0, Z1, CEIL, 2.6, C["roof"], C["wall"])
    H.box("Chimney", (-5.0, 4.6, 2.2), (1.0, 3.0, 1.0), C["brick"], 2, "solid", "roof")

    door_x(H, "Door_Front", 0.0, Z0, 0, 1.2, 0)
    door_z(H, "Door_Back", X1, -2.0, 0, 1.2, 0)
    door_x(H, "Door_Bedroom", -3.5, 1.0, 0, 1.0, 0)
    door_x(H, "Door_Bathroom", 1.5, 1.0, 0, 0.9, 0)
    door_x(H, "Door_Study", 5.0, 1.0, 0, 1.0, 0)

    # Living room
    H.possessable("Floral Sofa", "box", (-4.0, 0.42, -4.2), (2.4, 0.84, 0.9), C["sofa"], True, 0)
    H.possessable("Rocking Chair", "box", (-1.2, 0.5, -1.2), (0.8, 1.0, 0.9), C["wood"], True, 0)
    H.table("CoffeeTable", (-4.0, 0, -2.4), (1.4, 0.45, 0.7), 0, C["wood"], C["wood"])
    H.possessable("Antique Radio", "box", (-6.5, 0.55, -1.0), (0.5, 1.1, 0.9), rgb("5a3a2a"), False, 0)
    H.box("Bookcase", (-6.65, 1.1, 0.0), (0.4, 2.2, 1.6), C["wood"], 0, "solid", "furniture")
    H.box("Hearth", (-6.7, 0.6, -3.0), (0.6, 1.2, 1.6), C["brick"], 0, "solid", "furniture")
    H.light("Fireplace", (-6.3, 0.4, -3.0), rgb("ff8a2a"), 7, 1.8, 0, "box", (0, -0.2, 0), (0.6, 0.15, 0.8), rgb("ff8a2a"))
    H.light("Floor Lamp", (-1.5, 1.6, -4.4), rgb("ffe0a0"), 7, 1.3, 0, "cyl", (0, -0.8, 0), (0.08, 0.8, 0.08))
    # Kitchen
    H.box("Counter", (6.55, 0.45, -2.0), (0.7, 0.9, 5.4), C["white"], 0, "solid", "furniture")
    H.box("Stove", (4.0, 0.45, -4.55), (1.0, 0.9, 0.7), rgb("2a2a2f"), 0, "solid", "furniture")
    H.possessable("Rattling Teapot", "sphere", (4.0, 1.05, -4.5), (0.35, 0.3, 0.35), rgb("c86a8a"), True, 0)
    H.table("KitchenTable", (3.5, 0, -1.5), (1.4, 0.78, 1.0), 0, C["white"], C["wood"])
    H.possessable("Kitchen Chair", "box", (2.4, 0.45, -1.5), (0.5, 0.9, 0.5), C["red"], True, 0)
    H.possessable("Fridge", "box", (6.4, 0.95, 0.3), (0.8, 1.9, 0.8), rgb("dfe8e8"), False, 0)
    H.light("Kitchen Light", (4.0, 2.8, -2.0), rgb("fff0c8"), 8, 1.2, 0, "cyl", (0, 0.1, 0), (0.5, 0.1, 0.5))
    # Bedroom, bathroom, study
    H.bed("Bed", (-4.0, 0, 3.6), 0, C["wood"], rgb("d8a0b0"))
    H.possessable("Wardrobe", "box", (-6.5, 1.0, 2.3), (0.7, 2.0, 1.4), C["wood"], False, 0)
    H.light("Bedside Lamp", (-1.0, 0.9, 4.4), rgb("ffd8a0"), 6, 1.1, 0, "cyl", (0, -0.2, 0), (0.2, 0.4, 0.2))
    H.box("Bathtub", (1.5, 0.3, 4.2), (2.4, 0.6, 1.0), C["white"], 0, "solid", "furniture")
    H.light("Bath Light", (1.5, 2.8, 2.5), rgb("e0f0ff"), 5, 1.0, 0, "cyl", (0, 0.1, 0), (0.3, 0.1, 0.3))
    H.table("Desk", (5.0, 0, 4.3), (1.6, 0.76, 0.7), 0, C["wood"], C["wood"])
    H.possessable("Typewriter", "box", (5.0, 0.9, 4.3), (0.5, 0.2, 0.4), rgb("2a2a2f"), True, 0)
    H.light("Desk Lamp", (6.0, 1.0, 4.5), rgb("ffe0a0"), 6, 1.2, 0, "cyl", (0, -0.2, 0), (0.15, 0.3, 0.15))

    # Garden shed (back right)
    SX0, SX1, SZ0, SZ1 = 8.0, 12.0, 6.5, 10.5
    H.slab("ShedFloor", 0.05, SX0, SX1, SZ0, SZ1, [], C["wood"], 9, 0.1)
    shell(H, "Shed", SX0, SX1, SZ0, SZ1, 0, 2.5, 9, C["shed"], {"S": [gap(10.0, 1.2)], "E": [win(8.5, 0.8)]})
    H.box("ShedRoof", (10, 2.75, 8.5), (4.6, 0.15, 4.8), C["roof"], 9, "solid", "roof", r=(-10, 0, 0))
    door_x(H, "Door_Shed", 10.0, SZ0, 0, 1.2, 9)
    H.light("Shed Bulb", (10.0, 2.3, 9.0), rgb("ffd08a"), 5, 1.0, 9, "cyl", (0, 0.1, 0), (0.1, 0.2, 0.1))
    H.possessable("Wheelbarrow", "box", (11.0, 0.35, 9.6), (0.7, 0.6, 1.2), rgb("7a2a2a"), True, 9)

    # Garden: picket fence, autumn trees, pumpkins and a vegetable patch
    H.picket_fence("Fence", LX0 + 0.3, LX1 - 0.3, LZ0 + 0.3, LZ1 - 0.3, gate=(0.0, 1.8))
    H.tree("Maple", -11.0, -8.0, 6.0, rgb("d0662a"))
    H.tree("Oak", 11.5, -9.0, 5.5, rgb("b8862a"))
    H.tree("BackMaple", -11.0, 9.5, 6.5, rgb("c04a2a"))
    path(H, "VegPatch", -6.0, 2.0, 7.5, 11.0, rgb("4a3424"))
    for i in range(6):
        H.decor("pumpkin", (-5.4 + i * 1.4, 0.04, 8.4 + (i % 2) * 1.4), i * 47, 0.8 + 0.2 * (i % 3))
    H.decor("scarecrow", (-1.8, 0.04, 10.4), 180)
    H.decor("mailbox", (2.0, 0, LZ0 - 0.5), 180)
    for x in (-2.6, 2.6):
        H.decor("jack", (x, 0.15, -6.7), 180, 0.9)
        H.glow((x, 0.6, -6.7), rgb("ff9a3a"), 5, 1.0)
    jack_line(H, -1.3, -12.0, -1.3, -8.0, 3, 90, 0.6)
    jack_line(H, 1.3, -12.0, 1.3, -8.0, 3, -90, 0.6)
    H.decor("crow", (-1.0, 1.04, LZ0 + 0.3), 180)
    H.decor("haybale", (-9.0, 0, -11.0), 15)
    H.decor("pumpkin", (-9.0, 0.6, -11.0), 0, 0.9)

    # Halloween, cottage style: cosy rather than creepy
    rng = random.Random(14)
    hw.porch_display(H, 0.0, 0.15, -5.3, 180, 2.0, rng=rng)
    hw.string_lights(H, (-3.1, 2.62, -7.15), (3.1, 2.62, -7.15), 16, 0.22)
    hw.jack_arch(H, 0.0, LZ0 + 0.3, 2.6, 3.1, 180, rng=rng)
    hw.graves(H, -6.5, -9.8, 3, 1.4, rng=rng)
    H.decor("ghost_hang", (-10.1, 4.4, -8.0), 150)
    H.glow((-10.1, 3.2, -8.0), rgb("bfe9de"), 4, 0.6)
    H.decor("cat", (2.6, 1.0, LZ0 + 0.3), 200)
    H.decor("skeleton", (-2.3, 0.15, -5.6), 165, 1.0)
    H.decor("pumpkin_warty", (8.6, 0.04, 9.4), 30, 1.1)
    H.decor("jack_white", (-8.4, 0.04, 8.6), 200, 1.0)
    H.light("Porch Light", (0.0, 2.6, -5.4), rgb("ffcf7a"), 7, 1.2, 9, "box", (0, 0.15, 0), (0.25, 0.3, 0.25))

    # Rooms
    H.room("Living Room", 0, X0, 1, Z0, 1, 0, CEIL)
    H.room("Kitchen", 0, 1, X1, Z0, 1, 0, CEIL)
    H.room("Bedroom", 0, X0, 0, 1, Z1, 0, CEIL)
    H.room("Bathroom", 0, 0, 3, 1, Z1, 0, CEIL)
    H.room("Study", 0, 3, X1, 1, Z1, 0, CEIL)
    H.room("Garden Shed", 9, SX0, SX1, SZ0, SZ1, -1, 3)
    H.room("Front Yard", 9, LX0, LX1, LZ0, Z0, -1, 12)
    H.room("Back Garden", 9, LX0, LX1, Z0, LZ1, -1, 12)

    # Gameplay
    H.suspect_spot("Groundskeeper", (-3.0, 0, 9.4), facing(0, -1))
    H.suspect_spot("Heiress", (-2.6, 0, -2.6), facing(-1, -0.5))
    H.suspect_spot("Rival", (6.0, 0, -9.0), facing(-1, 0.4))
    H.suspect_spot("Cook", (5.6, 0, -3.0), facing(-1, 0))
    for p in ((-6.5, 0.2, -4.5), (-2.0, 0.2, 0.5), (6.5, 0.2, 0.0), (2.5, 0.2, -4.5), (-6.5, 0.2, 4.5), (-1.0, 0.2, 2.0),
              (2.5, 0.2, 2.0), (6.5, 0.2, 2.0), (11.5, 0.2, 7.0), (-13.5, 0.2, 11.5), (13.5, 0.2, -11.5), (4.0, 0.2, 11.0)):
        H.clue(p)
    for p in ((8.6, 0.25, 10.0), (-6.0, 0.25, 1.6), (13.0, 0.25, 4.0)):
        H.trap_piece(p)
    H.L["trapSite"] = {"p": [0.0, 0.0, -9.5]}
    H.L["solverSpawns"] = [{"p": [-2.25 + i * 1.5, 0.1, LZ0 - 2.5]} for i in range(4)]
    H.L["haunterSpawn"] = {"p": [5.0, 1.0, 3.0]}
    H.L["lot"] = {"min": [LX0, LZ0], "max": [LX1, LZ1]}
    return H


# =============================================================================
# Hollow Creek Farm: a farmhouse, a barn with a hayloft, a corn maze and a windmill
# =============================================================================
def farm():
    H = Layout("Hollow Creek Farm", "HollowCreekFarm", "Farmhouse",
               "The Hatchers' farm at the edge of town. Lanterns float through the corn maze and "
               "something lives in the hayloft. Medium: a two-storey farmhouse, a barn and a big maze.")
    H.L["size"] = "Medium"
    H.L["floors"] = 2
    H.L["storey"] = STOREY
    C = {"wall": rgb("cfc6b4"), "inner": rgb("b8a88e"), "upper": rgb("a89a86"), "trim": rgb("efe9df"), "roof": rgb("4a3b33"),
         "floor": rgb("7a5232"), "barn": rgb("8a2a24"), "barn_trim": rgb("e8e0d0"), "grass": rgb("3a4a26"),
         "dirt": rgb("5a4030"), "gravel": rgb("8a7f6c"), "wood": rgb("6b4426"), "corn": rgb("7a7a34"), "hay": rgb("c9a64a"),
         "white": rgb("e0dccf"), "red": rgb("a83a2a")}
    X0, X1, Z0, Z1, S = -9.0, 9.0, -6.0, 6.0, STOREY
    LX0, LX1, LZ0, LZ1 = -35.0, 35.0, -20.0, 40.0
    BX0, BX1, BZ0, BZ1, BH = 14.0, 28.0, 10.0, 32.0, 6.0  # barn
    LOFT_Z = 21.0

    lawn(H, LX0, LX1, LZ0, LZ1, [(X0, X1, Z0, Z1), (BX0, BX1, BZ0, BZ1)], C["grass"])
    H.slab("Floor", 0.0, X0, X1, Z0, Z1, [], C["floor"], 0, 0.3)
    stair_hole = (-2.75, -1.25, 1.2, 5.85)
    H.slab("UpperFloor", S, X0, X1, Z0, Z1, [stair_hole], C["floor"], 1, 0.25)
    H.stairs("Stairs", -2.75, -1.25, 1.2, 0.0, 13, 1, 0, C["wood"])
    path(H, "Driveway", -1.2, 1.2, LZ0, -8.5, C["gravel"])
    path(H, "BarnDrive", 1.2, 21.0, -11.0, -8.6, C["gravel"])
    path(H, "BarnDrive2", 18.8, 23.2, -8.6, BZ0, C["gravel"])
    porch(H, "Porch", X0, X1, -8.5, Z0, 0.2, C["wood"], C["trim"], C["roof"], 2.9)

    shell(H, "Ground", X0, X1, Z0, Z1, 0.0, S, 0, C["wall"], {
        "S": [gap(0.0), win(-5.0, 1.4), win(5.0, 1.4)],
        "N": [gap(-6.0), win(4.5)],
        "W": [win(-3.0), win(3.0)],
        "E": [win(-3.0), win(3.5)],
    }, trim=C["trim"])
    shell(H, "Upper", X0, X1, Z0, Z1, S, S, 1, C["wall"], {
        "S": [win(-5.0), win(0.0, 1.0), win(5.0)],
        "N": [win(-5.0), win(5.0)],
        "W": [win(-3.0), win(3.0)],
        "E": [win(-3.0), win(3.0)],
    }, trim=C["trim"])
    # ground floor: parlor | kitchen in front, mudroom | stair hall | pantry behind
    inner(H, "G_Mid", "x", 1.0, X0 + 0.15, X1 - 0.15, 0, S, 0, C["inner"], [gap(-6.0), gap(-0.5, 1.4), gap(5.0)])
    inner(H, "G_ParlorKitchen", "z", 0.0, Z0 + 0.15, 1.0, 0, S, 0, C["inner"], [gap(-2.5, 1.6)])
    inner(H, "G_MudStair", "z", -3.0, 1.0, Z1 - 0.15, 0, S, 0, C["inner"], [gap(3.5)])
    inner(H, "G_StairPantry", "z", 1.0, 1.0, Z1 - 0.15, 0, S, 0, C["inner"], [gap(5.0)])
    door_x(H, "Door_Front", 0.0, Z0, 0, 1.2, 0)
    door_x(H, "Door_Back", -6.0, Z1, 0, 1.2, 0)
    door_x(H, "Door_Mudroom", -6.0, 1.0, 0, 1.2, 0)
    door_x(H, "Door_Pantry", 5.0, 1.0, 0, 1.2, 0)
    # upstairs: master | kids in front, sewing | landing | bathroom behind
    inner(H, "U_Mid", "x", 1.0, X0 + 0.15, X1 - 0.15, S, S, 1, C["upper"], [gap(-4.5), gap(-0.5, 1.4), gap(4.5)])
    inner(H, "U_Front", "z", 0.0, Z0 + 0.15, 1.0, S, S, 1, C["upper"])
    inner(H, "U_SewLanding", "z", -3.0, 1.0, Z1 - 0.15, S, S, 1, C["upper"])
    inner(H, "U_LandingBath", "z", 1.0, 1.0, Z1 - 0.15, S, S, 1, C["upper"], [gap(5.0)])
    door_x(H, "Door_Master", -4.5, 1.0, S, 1.2, 1)
    door_x(H, "Door_Kids", 4.5, 1.0, S, 1.2, 1)
    door_z(H, "Door_Bath", 1.0, 5.0, S, 1.2, 1)
    H.box("StairRail", (-1.2, S + 0.5, 3.5), (0.08, 1.0, 4.6), C["wood"], 1, "solid", "rail")
    H.ceiling("Ceiling", 2 * S, X0, X1, Z0, Z1, C["white"])
    H.gable_roof("Roof", X0, X1, Z0, Z1, 2 * S, 3.4, C["roof"], C["wall"])
    H.box("Chimney", (6.0, 2 * S + 2.6, 0.0), (1.0, 3.6, 1.0), rgb("7a4a3a"), 2, "solid", "roof")

    # furniture and lamps
    H.possessable("Quilted Armchair", "box", (-6.5, 0.45, -4.4), (1.0, 0.9, 1.0), rgb("7a4a6a"), True, 0)
    H.possessable("Old Piano", "box", (-8.4, 0.7, -1.0), (0.6, 1.4, 1.8), rgb("3a2416"), False, 0)
    H.table("ParlorTable", (-4.0, 0, -3.0), (1.2, 0.5, 0.8), 0, C["wood"], C["wood"])
    H.light("Oil Lamp", (-4.0, 0.75, -3.0), rgb("ffc070"), 7, 1.3, 0, "cyl", (0, -0.15, 0), (0.15, 0.25, 0.15))
    H.box("Range", (8.4, 0.5, -4.0), (0.8, 1.0, 1.6), rgb("2a2a2f"), 0, "solid", "furniture")
    H.table("FarmTable", (4.5, 0, -2.5), (2.6, 0.8, 1.2), 0, C["wood"], C["wood"])
    H.possessable("Butter Churn", "cyl", (1.0, 0.5, -5.3), (0.4, 0.5, 0.4), rgb("8a6a44"), True, 0)
    H.possessable("Pie Safe", "box", (8.5, 1.0, -0.2), (0.6, 2.0, 1.2), C["wood"], False, 0)
    H.light("Kitchen Lamp", (4.5, 2.9, -2.5), rgb("fff0c8"), 8, 1.2, 0, "cyl", (0, 0.1, 0), (0.5, 0.1, 0.5))
    H.box("Shelves", (8.6, 1.0, 3.5), (0.5, 2.0, 4.0), C["wood"], 0, "solid", "furniture")
    H.possessable("Jar of Pickles", "cyl", (8.6, 2.15, 3.0), (0.2, 0.15, 0.2), rgb("7aa04a"), True, 0)
    H.box("Bench", (-6.0, 0.25, 5.3), (4.0, 0.5, 0.6), C["wood"], 0, "solid", "furniture")
    H.light("Mudroom Bulb", (-6.0, 2.9, 3.5), rgb("ffd08a"), 6, 1.0, 0, "cyl", (0, 0.1, 0), (0.1, 0.2, 0.1))
    H.bed("MasterBed", (-5.5, S, -3.5), 1, C["wood"], rgb("d8c8a0"))
    H.possessable("Hope Chest", "box", (-5.5, S + 0.3, -1.0), (1.2, 0.6, 0.6), C["wood"], True, 1)
    H.light("Master Lamp", (-8.3, S + 0.9, -5.3), rgb("ffd8a0"), 6, 1.1, 1, "cyl", (0, -0.2, 0), (0.2, 0.4, 0.2))
    H.bed("KidBed", (4.5, S, -4.6), 1, C["wood"], rgb("8ab0d8"), size=(1.8, 1.0))
    H.possessable("Toy Chest", "box", (7.5, S + 0.3, -1.0), (1.0, 0.6, 0.6), C["red"], True, 1)
    H.possessable("Rocking Horse", "box", (2.0, S + 0.5, -2.0), (0.4, 1.0, 1.1), rgb("c8a06a"), True, 1)
    H.light("Nightlight", (8.4, S + 0.5, -5.4), rgb("a0c8ff"), 5, 1.0, 1, "cyl", (0, -0.1, 0), (0.12, 0.2, 0.12))
    H.possessable("Sewing Machine", "box", (-6.0, S + 0.85, 5.3), (0.8, 0.5, 0.5), rgb("2a2a2f"), True, 1)
    H.possessable("Dress Form", "capsule", (-8.0, S + 0.9, 3.0), (0.5, 0.9, 0.4), rgb("c8b8a8"), True, 1)
    H.light("Sewing Lamp", (-6.0, S + 2.8, 3.5), rgb("ffe0a0"), 6, 1.0, 1, "cyl", (0, 0.1, 0), (0.3, 0.1, 0.3))
    H.box("Clawfoot Tub", (5.0, S + 0.35, 5.3), (2.0, 0.7, 0.9), C["white"], 1, "solid", "furniture")
    H.light("Landing Lamp", (-1.0, S + 2.8, 3.5), rgb("ffe0a0"), 6, 1.0, 1, "cyl", (0, 0.1, 0), (0.3, 0.1, 0.3))

    # The red barn, with a hayloft over the back half
    H.slab("BarnFloor", 0.05, BX0, BX1, BZ0, BZ1, [], rgb("6a5038"), 9, 0.1, "floor")
    shell(H, "Barn", BX0, BX1, BZ0, BZ1, 0, BH, 9, C["barn"], {
        "S": [(21.0, 4.0, 0, 4.0, "door")],
        "N": [(21.0, 2.0, 0, 2.6, "door"), (21.0, 1.6, 4.0, 5.2, "window")],
        "W": [win(16.0, 1.0, 1.2, 2.2), win(26.0, 1.0, 1.2, 2.2)],
        "E": [win(16.0, 1.0, 1.2, 2.2)],
    }, trim=C["barn_trim"], glass=rgb("ffb35a"))
    H.slab("Hayloft", S, BX0 + 0.15, BX1 - 0.15, LOFT_Z, BZ1 - 0.15, [(16.6, 18.4, 24.6, 26.4)], rgb("7a5a38"), 9, 0.2)
    H.stairs("LoftStairs", 26.2, 27.6, LOFT_Z - 13 * 0.35, 0.05, 13, 1, 9, C["wood"])
    H.box("LoftRail", (21.0, S + 0.5, LOFT_Z), (10.0, 1.0, 0.08), C["wood"], 9, "solid", "rail")
    for i, x in enumerate((16.0, 18.5, 23.5)):
        H.box(f"Stall{i}", (x, 0.7, 17.0), (0.12, 1.4, 4.0), C["wood"], 9, "solid", "furniture")
    H.gable_roof("BarnRoof", BX0, BX1, BZ0, BZ1, BH, 4.2, rgb("3a2e2a"), C["barn"], level=9)
    for i, (x, z) in enumerate(((17.0, 12.0), (25.0, 12.0), (19.0, 28.0), (24.0, 30.5), (16.0, 30.5))):
        H.decor("haybale", (x, 0.1 if z < LOFT_Z else S, z), 90 * (i % 2))
    H.decor("haybale", (16.0, S + 0.6, 30.5), 90)
    H.light("Barn Bulb", (21.0, 4.8, 14.0), rgb("ffd08a"), 10, 1.3, 9, "cyl", (0, 0.3, 0), (0.1, 0.5, 0.1))
    H.light("Hayloft Lantern", (24.0, S + 1.2, 27.0), rgb("ffb35a"), 8, 1.2, 9, "box", (0, -0.15, 0), (0.25, 0.35, 0.25))
    H.possessable("Pitchfork", "box", (14.6, 1.0, 20.0), (0.1, 2.0, 0.3), rgb("8a6a44"), True, 9)
    H.possessable("Milk Can", "cyl", (26.5, 0.45, 12.0), (0.4, 0.45, 0.4), rgb("b0b6c0"), True, 9)
    H.possessable("Tractor", "box", (8.0, 0.9, 18.0), (1.8, 1.8, 3.0), rgb("3a7a3a"), False, 9)
    H.trapdoor("Hayloft Trapdoor", (17.5, S, 25.5), (17.5, 0.25, 25.5))

    # Windmill and water trough
    H.box("WindmillTower", (-26.0, 5.0, 30.0), (1.8, 10.0, 1.8), rgb("8a8f94"), 9, "solid", "windmill")
    H.box("WindmillHub", (-26.0, 10.0, 28.9), (0.6, 0.6, 0.6), rgb("3a3a42"), 9, "solid", "windmill")
    for i in range(4):
        H.box(f"WindmillBlade{i}", (-26.0 + 2.1 * math.sin(math.radians(i * 90 + 20)), 10.0 + 2.1 * math.cos(math.radians(i * 90 + 20)), 28.7),
              (0.5, 4.2, 0.08), rgb("d8d0c0"), 9, "nocollide", "windmill", r=(0, 0, -(i * 90 + 20)))
    H.box("Trough", (-22.0, 0.4, 26.0), (3.0, 0.8, 1.0), rgb("6a6a72"), 9, "solid", "furniture")

    # Corn maze (west field), carved out of a grid with a fixed seed so it never changes
    MX0, MZ0, CELL, NX, NZ = -33.0, -16.0, 3.0, 7, 11
    rng = random.Random(1031)
    seen, walls = set(), set()
    for i in range(NX):
        for j in range(NZ):
            if i + 1 < NX:
                walls.add(((i, j), (i + 1, j)))
            if j + 1 < NZ:
                walls.add(((i, j), (i, j + 1)))
    stack = [(3, 0)]
    seen.add((3, 0))
    while stack:
        ci, cj = stack[-1]
        nbrs = [(ci + di, cj + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if 0 <= ci + di < NX and 0 <= cj + dj < NZ and (ci + di, cj + dj) not in seen]
        if not nbrs:
            stack.pop()
            continue
        n = rng.choice(nbrs)
        walls.discard(tuple(sorted(((ci, cj), n))))
        seen.add(n)
        stack.append(n)
    # open the middle 2x2 into a clearing for the scarecrow
    for w in [(((3, 5), (4, 5))), ((3, 5), (3, 6)), ((3, 6), (4, 6)), ((4, 5), (4, 6))]:
        walls.discard(w)
    k = 0
    for (a, b) in sorted(walls):
        (i0, j0), (i1, j1) = a, b
        if i1 != i0:  # wall between columns: runs along z
            x = MX0 + (i0 + 1) * CELL
            H.box(f"Corn{k}", (x, 1.1, MZ0 + (j0 + 0.5) * CELL), (0.6, 2.2, CELL + 0.6), C["corn"], 9, "solid", "corn")
        else:
            z = MZ0 + (j0 + 1) * CELL
            H.box(f"Corn{k}", (MX0 + (i0 + 0.5) * CELL, 1.1, z), (CELL + 0.6, 2.2, 0.6), C["corn"], 9, "solid", "corn")
        k += 1
    mx1, mz1 = MX0 + NX * CELL, MZ0 + NZ * CELL
    for side, (p, s) in {
        "S1": ((MX0 + 1.5 * CELL, 1.1, MZ0), (3 * CELL, 2.2, 0.6)),
        "S2": ((MX0 + 5.5 * CELL, 1.1, MZ0), (3 * CELL, 2.2, 0.6)),
        "N1": ((MX0 + 1.5 * CELL, 1.1, mz1), (3 * CELL, 2.2, 0.6)),
        "N2": ((MX0 + 5.5 * CELL, 1.1, mz1), (3 * CELL, 2.2, 0.6)),
        "W": ((MX0, 1.1, (MZ0 + mz1) / 2), (0.6, 2.2, NZ * CELL)),
        "E": ((mx1, 1.1, (MZ0 + mz1) / 2), (0.6, 2.2, NZ * CELL)),
    }.items():
        H.box(f"CornEdge{side}", p, s, C["corn"], 9, "solid", "corn")
    for i in range(0, NX * 2):
        for edge_z in (MZ0, mz1):
            x = MX0 + 0.75 + i * 1.5
            if abs(x - (MX0 + 3.5 * CELL)) > 1.6:
                H.decor("corn", (x, 0.6, edge_z), i * 37, 1.1)
    H.decor("scarecrow", (MX0 + 4 * CELL, 0, MZ0 + 6 * CELL), 180)
    H.glow((MX0 + 4 * CELL, 2.0, MZ0 + 6 * CELL), rgb("9dff8a"), 6, 1.0)
    jack_line(H, MX0 + 3.0 * CELL, MZ0 - 1.0, MX0 + 4.0 * CELL, MZ0 - 1.0, 2, 180, 0.8, 1)

    # Pumpkin patch, fence, trees, scarecrows, crows
    path(H, "Patch", 14.0, 30.0, -17.0, 2.0, C["dirt"])
    rng2 = random.Random(7)
    for i in range(22):
        x, z = rng2.uniform(15, 29), rng2.uniform(-16, 1)
        H.decor("jack" if i % 5 == 0 else "pumpkin", (x, 0.04, z), rng2.uniform(0, 360), rng2.uniform(0.7, 1.5))
        if i % 5 == 0:
            H.glow((x, 0.5, z), rgb("ff9a3a"), 4, 0.8)
    H.decor("scarecrow", (22.0, 0.04, -7.0), 200)
    for i, (x, z) in enumerate(((22.6, -7.0), (-8.0, -8.6), (14.2, 31.0))):
        H.decor("crow", (x, 1.5 if i == 0 else 1.0, z), 160 + 30 * i)
    H.picket_fence("Fence", LX0 + 0.3, LX1 - 0.3, LZ0 + 0.3, LZ1 - 0.3, gate=(0.0, 3.0), color=rgb("6b4a2e"))
    for i, (x, z, h) in enumerate(((-12, -14, 7), (10, -15, 6), (31, 35, 8), (-31, 36, 7), (5, 36, 6.5))):
        H.tree(f"Tree{i}", x, z, h, None if i % 2 else rgb("b8622a"))
    H.decor("jack", (-0.9, 0.2, -8.2), 180)
    H.decor("jack", (0.9, 0.2, -8.2), 180)
    H.glow((0, 0.8, -8.2), rgb("ff9a3a"), 5, 1.0)
    H.decor("mailbox", (2.4, 0, LZ0 - 0.6), 180)

    # Halloween on the farm: harvest colours, a lit arch into the corn maze, a hay-bale pumpkin pyramid
    rng = random.Random(23)
    hw.porch_display(H, 0.0, 0.2, -6.3, 180, 2.0, rng=rng)
    hw.string_lights(H, (-9.1, 2.72, -8.75), (-0.1, 2.72, -8.75), 14, 0.3)
    hw.string_lights(H, (0.1, 2.72, -8.75), (9.1, 2.72, -8.75), 14, 0.3)
    hw.string_lights(H, (18.6, 4.4, 9.75), (23.4, 4.4, 9.75), 8, 0.25, colors=("bulb_orange",))
    hw.jack_arch(H, MX0 + 3.5 * CELL, MZ0 - 0.7, 3.0, 3.4, 180, rng=rng)
    for k, (x, y) in enumerate(((-1.1, 0), (0.0, 0), (1.1, 0), (-0.55, 0.6), (0.55, 0.6), (0.0, 1.2))):
        H.decor("haybale", (-6.0 + x, y, -14.0), 0)
    for x, y in ((-1.1, 0.6), (1.1, 0.6), (-0.55, 1.2), (0.55, 1.2), (0.0, 1.8)):
        hw.jack(H, (-6.0 + x, y, -14.3), 180, 0.85, glow=x == 0.0, rng=rng)
    H.decor("skeleton", (6.5, 0.2, -6.8), 190)
    H.decor("cat", (-8.6, 0.2, -8.2), 160)
    for i in range(5):
        H.decor("pumpkin_warty" if i % 2 else "jack_white", (16.0 + i * 2.6, 0.04, -3.0 - (i % 3) * 3.5), i * 60, 1.1)
    H.light("Porch Lantern", (-2.5, 2.5, -6.4), rgb("ffcf7a"), 8, 1.2, 9, "box", (0, -0.15, 0), (0.25, 0.35, 0.25))
    H.light("Yard Light", (12.0, 4.5, 4.0), rgb("ffe0a0"), 12, 1.0, 9, "cyl", (0, -2.2, 0), (0.15, 2.2, 0.15))

    # Rooms
    H.room("Parlor", 0, X0, 0, Z0, 1, 0, S)
    H.room("Farm Kitchen", 0, 0, X1, Z0, 1, 0, S)
    H.room("Mudroom", 0, X0, -3, 1, Z1, 0, S)
    H.room("Stair Hall", 0, -3, 1, 1, Z1, 0, S)
    H.room("Pantry", 0, 1, X1, 1, Z1, 0, S)
    H.room("Master Bedroom", 1, X0, 0, Z0, 1, S, 2 * S)
    H.room("Kids' Room", 1, 0, X1, Z0, 1, S, 2 * S)
    H.room("Sewing Room", 1, X0, -3, 1, Z1, S, 2 * S)
    H.room("Landing", 1, -3, 1, 1, Z1, S, 2 * S)
    H.room("Bathroom", 1, 1, X1, 1, Z1, S, 2 * S)
    H.room("Barn", 9, BX0, BX1, BZ0, BZ1, -1, S - 0.1)
    H.room("Hayloft", 9, BX0, BX1, LOFT_Z, BZ1, S - 0.1, BH + 4)
    H.room("Corn Maze", 9, MX0, mx1, MZ0, mz1, -1, 6)
    H.room("Pumpkin Patch", 9, 14, 30, -17, 2, -1, 6)
    H.room("Windmill", 9, -30, -20, 24, 36, -1, 14)
    H.room("Farmyard", 9, LX0, LX1, LZ0, LZ1, -1, 20)

    # Gameplay
    H.suspect_spot("Groundskeeper", (20.0, 0.05, 14.0), facing(0, -1))
    H.suspect_spot("Heiress", (-5.0, 0, -2.0), facing(1, -1))
    H.suspect_spot("Rival", (MX0 + 3.5 * CELL, 0, MZ0 - 2.5), facing(1, -1))
    H.suspect_spot("Cook", (6.0, 0, -4.4), facing(-1, 0))
    for p in ((-8.3, 0.2, -5.3), (3.0, 0.2, -0.3), (-8.3, 0.2, 2.0), (8.3, 0.2, 5.3), (-8.3, S + 0.2, -0.3), (8.3, S + 0.2, -2.5),
              (-4.0, S + 0.2, 5.3), (0.0, S + 0.2, 5.3), (14.8, 0.2, 31.0), (27.0, S + 0.2, 31.0), (26.8, 0.2, 18.0),
              (MX0 + 0.5 * CELL, 0.2, MZ0 + 10.5 * CELL), (MX0 + 6.5 * CELL, 0.2, MZ0 + 2.5 * CELL), (MX0 + 4 * CELL, 0.2, MZ0 + 6.6 * CELL),
              (-24.0, 0.2, 31.0), (29.0, 0.2, -15.0), (33.0, 0.2, 38.0), (-33.0, 0.2, 38.0)):
        H.clue(p)
    for p in ((MX0 + 1.5 * CELL, 0.25, MZ0 + 8.5 * CELL), (22.0, S + 0.25, 30.0), (-2.0, S + 0.25, -5.0), (28.0, 0.25, 0.0)):
        H.trap_piece(p)
    H.L["trapSite"] = {"p": [6.0, 0.0, -14.0]}
    H.L["solverSpawns"] = [{"p": [-2.25 + i * 1.5, 0.1, LZ0 - 2.5]} for i in range(4)]
    H.L["haunterSpawn"] = {"p": [24.0, S + 1.0, 27.0]}
    H.L["lot"] = {"min": [LX0, LZ0], "max": [LX1, LZ1]}
    return H


# =============================================================================
# Willow Lane Victorian: two storeys and a tower, a wraparound porch, a family plot out back
# =============================================================================
def victorian():
    H = Layout("Willow Lane Victorian", "WillowLaneVictorian", "Victorian",
               "The Ashcombe house: turrets, gingerbread trim and a music box that plays by itself "
               "in the nursery. Large: two floors and a tower, a gazebo and a family plot.")
    H.L["size"] = "Large"
    H.L["floors"] = 2
    H.L["storey"] = STOREY
    C = {"wall": rgb("6b5a7a"), "inner": rgb("8a7a6a"), "upper": rgb("7a6a80"), "trim": rgb("e8e0d0"), "roof": rgb("2c2836"),
         "floor": rgb("5a3a28"), "grass": rgb("2a3e2a"), "path": rgb("7a756c"), "wood": rgb("4a2e1e"), "velvet": rgb("6e1f3f"),
         "white": rgb("ddd6c8"), "stone": rgb("8d8f94"), "iron": rgb("26262b"), "hedge": rgb("1f3d22"), "teal": rgb("2f6a6a")}
    X0, X1, Z0, Z1, S = -10.0, 10.0, -7.0, 7.0, STOREY
    TX0, TX1, TZ0, TZ1 = 10.0, 14.0, -7.0, -3.0  # tower
    LX0, LX1, LZ0, LZ1 = -22.0, 22.0, -18.0, 22.0

    lawn(H, LX0, LX1, LZ0, LZ1, [(X0, X1, Z0, Z1), (TX0, TX1, TZ0, TZ1)], C["grass"])
    stair_hole = (0.5, 2.5, 1.0, 5.6)
    for name, y, lvl in (("Floor", 0.0, 0), ("UpperFloor", S, 1)):
        H.slab(name, y, X0, X1, Z0, Z1, [stair_hole] if lvl else [], C["floor"], lvl, 0.25)
        H.slab(f"Tower{name}", y, TX0, TX1, TZ0, TZ1, [], C["floor"], lvl, 0.25)
    H.stairs("GrandStairs", 0.5, 2.5, 1.0, 0.0, 13, 1, 0, C["wood"])
    H.box("Banister", (0.45, S + 0.5, 3.3), (0.08, 1.0, 4.6), C["wood"], 1, "solid", "rail")
    path(H, "FrontWalk", -1.0, 1.0, LZ0, -9.5, C["path"])
    path(H, "SideWalk", -14.0, -12.5, -9.5, 13.0, C["path"])
    path(H, "GazeboWalk", -12.5, 0.0, 12.2, 13.8, C["path"])
    porch(H, "Porch", X0 - 2.5, TX0, -9.5, Z0, 0.25, C["wood"], C["trim"], C["roof"], 2.9)
    porch(H, "SidePorch", X0 - 2.5, X0, Z0, 2.0, 0.25, C["wood"], C["trim"], C["roof"], 2.9)

    shell(H, "Ground", X0, X1, Z0, Z1, 0.0, S, 0, C["wall"], {
        "S": [gap(0.0, 1.6), win(-6.5, 1.4, 0.6, 2.6), win(6.5, 1.4, 0.6, 2.6)],
        "N": [win(-6.5), gap(6.0), win(-2.0)],
        "W": [gap(-3.5), win(3.5)],
        "E": [(-5.0, 1.8, 0, 2.4, "door"), win(3.5)],
    }, trim=C["trim"])
    shell(H, "Upper", X0, X1, Z0, Z1, S, S, 1, C["wall"], {
        "S": [win(-6.5), win(-2.0, 1.0), win(2.0, 1.0), win(6.5)],
        "N": [win(-6.5), win(-2.0), win(6.5)],
        "W": [win(-3.5), win(3.5)],
        "E": [(-5.0, 1.8, 0, 2.4, "door"), win(3.5)],
    }, trim=C["trim"])
    # The tower: three stacked rooms; the walls shared with the house are already there
    for lvl, y in ((0, 0.0), (1, S)):
        H.wall(f"Tower{lvl}S", "x", TZ0, TX0, TX1 + OUTER / 2, y, S, lvl, C["wall"], OUTER, [win(12.0, 1.2, 0.8, 2.5)], trim=C["trim"])
        H.wall(f"Tower{lvl}N", "x", TZ1, TX0, TX1 + OUTER / 2, y, S, lvl, C["wall"], OUTER, [win(12.0, 1.0)], trim=C["trim"])
        H.wall(f"Tower{lvl}E", "z", TX1, TZ0, TZ1, y, S, lvl, C["wall"], OUTER, [win(-5.0, 1.2, 0.8, 2.5)], trim=C["trim"])
    H.box("TowerTopFloor", (12.0, 2 * S - 0.12, -5.0), (4.3, 0.25, 4.3), C["floor"], 2, "solid", "floor")
    H.wall("TowerTopS", "x", TZ0, TX0 - OUTER / 2, TX1 + OUTER / 2, 2 * S, 2.6, 2, C["wall"], OUTER, [win(12.0, 1.0)], trim=C["trim"])
    H.wall("TowerTopN", "x", TZ1, TX0 - OUTER / 2, TX1 + OUTER / 2, 2 * S, 2.6, 2, C["wall"], OUTER, [win(12.0, 1.0)], trim=C["trim"])
    H.wall("TowerTopE", "z", TX1, TZ0, TZ1, 2 * S, 2.6, 2, C["wall"], OUTER, [win(-5.0, 1.0)], trim=C["trim"])
    H.wall("TowerTopW", "z", TX0, TZ0, TZ1, 2 * S, 2.6, 2, C["wall"], OUTER, [win(-5.0, 1.0)], trim=C["trim"])
    spire_base = 2 * S + 2.6
    for i in range(7):
        w = 5.0 * (1 - i / 7) + 0.3
        H.box(f"Spire{i}", (12.0, spire_base + i * 0.75 + 0.375, -5.0), (w, 0.75, w), C["roof"], 2, "solid", "roof")
    H.box("Finial", (12.0, spire_base + 5.6, -5.0), (0.12, 1.2, 0.12), C["iron"], 2, "solid", "roof")
    H.light("Tower Window", (12.0, 2 * S + 1.5, -5.0), rgb("9dff8a"), 8, 1.2, 2, "cyl", (0, -0.4, 0), (0.15, 0.3, 0.15))

    # ground: parlor | foyer | dining in front, kitchen | foyer | music room behind
    inner(H, "G_W", "z", -3.0, Z0 + 0.15, Z1 - 0.15, 0, S, 0, C["inner"], [gap(-3.5, 1.6), gap(3.5)])
    inner(H, "G_E", "z", 3.0, Z0 + 0.15, Z1 - 0.15, 0, S, 0, C["inner"], [gap(-3.5, 1.6), gap(3.5)])
    inner(H, "G_WestMid", "x", 0.0, X0 + 0.15, -3.0, 0, S, 0, C["inner"], [gap(-6.5)])
    inner(H, "G_EastMid", "x", 0.0, 3.0, X1 - 0.15, 0, S, 0, C["inner"])
    door_x(H, "Door_Front", 0.0, Z0, 0, 1.6, 0)
    door_z(H, "Door_SidePorch", X0, -3.5, 0, 1.2, 0)
    door_x(H, "Door_Back", 6.0, Z1, 0, 1.2, 0)
    door_z(H, "Door_Kitchen", -3.0, 3.5, 0, 1.2, 0)
    door_z(H, "Door_MusicRoom", 3.0, 3.5, 0, 1.2, 0)
    # upstairs: master | hall | guest in front, sewing | hall | nursery behind
    inner(H, "U_W", "z", -3.0, Z0 + 0.15, Z1 - 0.15, S, S, 1, C["upper"], [gap(-3.5), gap(3.5)])
    inner(H, "U_E", "z", 3.0, Z0 + 0.15, Z1 - 0.15, S, S, 1, C["upper"], [gap(-3.5), gap(3.5)])
    inner(H, "U_WestMid", "x", 0.0, X0 + 0.15, -3.0, S, S, 1, C["upper"])
    inner(H, "U_EastMid", "x", 0.0, 3.0, X1 - 0.15, S, S, 1, C["upper"])
    for name, x, z in (("Door_Master", -3.0, -3.5), ("Door_Sewing", -3.0, 3.5), ("Door_Guest", 3.0, -3.5), ("Door_Nursery", 3.0, 3.5)):
        door_z(H, name, x, z, S, 1.2, 1)
    H.ceiling("Ceiling", 2 * S, X0, X1, Z0, Z1, C["white"])
    H.gable_roof("Roof", X0, X1, Z0, Z1, 2 * S, 4.0, C["roof"], C["wall"], overhang=0.6)
    for i, x in enumerate((-6.5, 6.5)):  # front gables with gingerbread trim
        H.box(f"Dormer{i}", (x, 2 * S + 1.3, Z0 - 0.3), (2.4, 2.4, 1.2), C["wall"], 2, "solid", "roof")
        H.box(f"DormerWin{i}", (x, 2 * S + 1.3, Z0 - 0.92), (1.0, 1.2, 0.05), rgb("ffcf7a"), 2, "glass", "roof")
        H.box(f"DormerRoofL{i}", (x - 0.75, 2 * S + 2.75, Z0 - 0.3), (1.8, 0.15, 1.6), C["roof"], 2, "solid", "roof", r=(0, 0, 40))
        H.box(f"DormerRoofR{i}", (x + 0.75, 2 * S + 2.75, Z0 - 0.3), (1.8, 0.15, 1.6), C["roof"], 2, "solid", "roof", r=(0, 0, -40))
    H.box("ChimneyW", (-8.0, 2 * S + 3.0, 2.0), (1.0, 4.4, 1.0), rgb("6a3a2e"), 2, "solid", "roof")
    H.trapdoor("Nursery Trapdoor", (6.5, S, 3.5), (6.0, 0.25, 3.0))

    # furniture
    H.possessable("Velvet Settee", "box", (-6.5, 0.45, -6.0), (2.4, 0.9, 0.9), C["velvet"], True, 0)
    H.possessable("Grandfather Clock", "box", (-9.5, 1.2, -1.0), (0.6, 2.4, 0.8), C["wood"], False, 0)
    H.possessable("Portrait of Great-Aunt Ida", "box", (-9.8, 1.7, -4.5), (0.08, 1.2, 0.9), rgb("8a6a2a"), False, 0)
    H.table("TeaTable", (-6.5, 0, -3.5), (1.0, 0.55, 1.0), 0, C["wood"], C["wood"])
    H.light("Parlor Lamp", (-4.0, 1.5, -6.2), rgb("ffc8a0"), 7, 1.3, 0, "cyl", (0, -0.75, 0), (0.08, 0.75, 0.08))
    H.light("Foyer Chandelier", (0.0, 2.8, -3.0), rgb("ffd28a"), 9, 1.5, 0, "cyl", (0, 0.15, 0), (0.8, 0.1, 0.8))
    H.table("DiningTable", (6.5, 0, -3.5), (3.6, 0.78, 1.4), 0, C["wood"], C["wood"])
    H.light("Candelabra", (6.5, 1.15, -3.5), rgb("ffc070"), 8, 1.4, 0, "cyl", (0, -0.2, 0), (0.25, 0.4, 0.25))
    H.possessable("China Cabinet", "box", (9.5, 1.1, -1.5), (0.6, 2.2, 1.6), rgb("3a2a22"), False, 0)
    H.box("Stove", (-9.4, 0.5, 4.0), (0.8, 1.0, 2.0), rgb("2a2a2f"), 0, "solid", "furniture")
    H.box("KitchenCounter", (-6.5, 0.45, 6.5), (5.5, 0.9, 0.6), C["white"], 0, "solid", "furniture")
    H.possessable("Copper Kettle", "sphere", (-9.4, 1.15, 3.6), (0.35, 0.3, 0.35), rgb("a5612f"), True, 0)
    H.light("Kitchen Lamp", (-6.5, 2.9, 3.5), rgb("fff0c8"), 8, 1.2, 0, "cyl", (0, 0.1, 0), (0.5, 0.1, 0.5))
    H.possessable("Grand Piano", "box", (6.5, 0.6, 4.5), (1.6, 1.2, 2.2), rgb("141418"), False, 0)
    H.possessable("Gramophone", "box", (9.3, 0.6, 1.0), (0.6, 1.2, 0.6), rgb("b08d3c"), True, 0)
    H.light("Music Room Sconce", (9.7, 2.0, 4.0), rgb("ffb0e0"), 7, 1.1, 0, "box", (0.1, 0, 0), (0.15, 0.4, 0.15))
    H.possessable("Telescope", "cyl", (12.0, 1.0, -5.0), (0.2, 1.0, 0.2), rgb("b08d3c"), True, 0)
    H.light("Tower Lamp", (13.4, 1.0, -3.5), rgb("ffe0a0"), 6, 1.0, 0, "cyl", (0, -0.2, 0), (0.15, 0.4, 0.15))
    H.bed("MasterBed", (-6.5, S, -5.0), 1, C["wood"], C["velvet"])
    H.possessable("Vanity Mirror", "box", (-9.6, S + 1.0, -1.5), (0.2, 2.0, 1.0), rgb("c8d8e8"), False, 1)
    H.light("Master Lamp", (-4.0, S + 0.9, -6.4), rgb("ffd8a0"), 6, 1.1, 1, "cyl", (0, -0.2, 0), (0.2, 0.4, 0.2))
    H.bed("GuestBed", (6.5, S, -5.0), 1, C["wood"], C["teal"])
    H.possessable("Steamer Trunk", "box", (8.5, S + 0.35, -1.0), (1.2, 0.7, 0.7), rgb("5a3a28"), True, 1)
    H.light("Guest Lamp", (9.4, S + 0.9, -6.4), rgb("ffd8a0"), 6, 1.0, 1, "cyl", (0, -0.2, 0), (0.2, 0.4, 0.2))
    H.possessable("Antique Crib", "box", (8.5, S + 0.5, 5.8), (1.4, 1.0, 0.8), rgb("e8e0d0"), False, 1)
    H.possessable("Music Box", "box", (4.0, S + 0.15, 6.3), (0.3, 0.3, 0.3), rgb("c86a8a"), True, 1)
    H.possessable("Rocking Horse", "box", (8.6, S + 0.5, 2.0), (0.4, 1.0, 1.1), rgb("c8a06a"), True, 1)
    H.light("Nursery Mobile", (6.5, 2 * S - 0.4, 5.0), rgb("a0c8ff"), 6, 1.1, 1, "cyl", (0, 0.2, 0), (0.4, 0.05, 0.4))
    H.possessable("Dress Form", "capsule", (-9.0, S + 0.9, 6.0), (0.5, 0.9, 0.4), rgb("c8b8a8"), True, 1)
    H.light("Sewing Lamp", (-6.5, S + 2.8, 3.5), rgb("ffe0a0"), 6, 1.0, 1, "cyl", (0, 0.1, 0), (0.3, 0.1, 0.3))
    H.light("Hall Sconce", (-2.7, S + 2.0, -3.5), rgb("ffd28a"), 7, 1.1, 1, "box", (-0.1, 0, 0), (0.15, 0.4, 0.15))
    H.possessable("Spyglass Desk", "box", (12.0, S + 0.4, -6.2), (1.6, 0.8, 0.6), C["wood"], True, 1)
    H.light("Tower Study Lamp", (12.0, S + 1.0, -6.0), rgb("ffe0a0"), 6, 1.0, 1, "cyl", (0, -0.2, 0), (0.15, 0.3, 0.15))
    for i in range(4):  # cobwebs in the attic corners and the tower
        H.decor("cobweb", (X0 + 0.6, 2 * S - 0.05, Z0 + 0.6 + i * 4.3), 45 + 90 * (i % 2), 1.0, 1)

    # Grounds: iron fence, hedges, dead trees, gazebo, family plot
    H.picket_fence("Fence", LX0 + 0.3, LX1 - 0.3, LZ0 + 0.3, LZ1 - 0.3, gate=(0.0, 2.4), color=C["iron"])
    for side in (-1, 1):
        H.box(f"GatePillar{side}", (side * 1.6, 0.9, LZ0 + 0.3), (0.6, 1.8, 0.6), C["stone"], 9, "solid", "fence")
        H.decor("jack", (side * 1.6, 1.8, LZ0 + 0.3), 180, 0.9)
        H.glow((side * 1.6, 2.3, LZ0 + 0.3), rgb("ff9a3a"), 5, 1.0)
        H.box(f"Hedge{side}", (side * 9.0, 0.7, -13.0), (12.0, 1.4, 1.2), C["hedge"], 9, "solid", "hedge")
    for i, (x, z, h) in enumerate(((-17, -12, 7.5), (17, -13, 8), (-18, 8, 7), (18, 16, 7.5), (8, 18, 6))):
        H.tree(f"DeadTree{i}", x, z, h)
        H.decor("jack", (x + 0.8, h * 0.62, z), 180, 0.7)
        H.glow((x + 0.8, h * 0.62 + 0.3, z), rgb("ff9a3a"), 4, 0.8)
        H.decor("crow", (x - 0.6, h * 0.75, z + 0.3), 140)
    # gazebo (the trap site)
    GX, GZ = 0.0, 14.0
    H.box("GazeboFloor", (GX, 0.15, GZ), (5.0, 0.3, 5.0), C["white"], 9, "solid", "floor")
    for i in range(6):
        a = math.radians(i * 60)
        H.box(f"GazeboPost{i}", (GX + 2.2 * math.cos(a), 1.5, GZ + 2.2 * math.sin(a)), (0.15, 2.6, 0.15), C["trim"], 9, "solid", "porch")
    for i in range(5):
        w = 5.4 * (1 - i / 5) + 0.2
        H.box(f"GazeboRoof{i}", (GX, 2.9 + i * 0.3, GZ), (w, 0.3, w), C["teal"], 9, "solid", "roof", r=(0, 45 * (i % 2), 0))
    H.light("Gazebo Lantern", (GX, 2.6, GZ), rgb("ffcf7a"), 8, 1.2, 9, "box", (0, -0.15, 0), (0.25, 0.35, 0.25))
    # family plot
    for i, (x, z) in enumerate(((14, 12), (16, 12), (18, 12), (14, 15), (16, 15), (18, 15.5))):
        grave(H, f"Grave{i}", x, z, C["stone"])
        if i % 2 == 0:
            H.decor("candle", (x + 0.4, 0.0, z - 0.3), 0, 1.2)
            H.glow((x + 0.4, 0.4, z - 0.3), rgb("ffb347"), 3, 0.7)
    H.box("PlotFence", (16.0, 0.4, 10.5), (6.0, 0.8, 0.08), C["iron"], 9, "solid", "fence")
    H.decor("cauldron", (-15.0, 0.0, 17.0), 0)
    H.glow((-15.0, 1.0, 17.0), rgb("9dff8a"), 6, 1.1)
    jack_line(H, -1.6, -17.0, -1.6, -10.0, 5, 90, 0.7)
    jack_line(H, 1.6, -17.0, 1.6, -10.0, 5, -90, 0.7)
    for x in (-11.5, -5.0, 5.0):
        H.decor("jack", (x, 0.25, -9.2), 180, 1.0)
    H.decor("mailbox", (3.0, 0, LZ0 - 0.6), 180)

    # Halloween, Victorian style: purple and orange lights, a jack-o'-lantern tree, something in the tower
    rng = random.Random(31)
    hw.porch_display(H, 0.0, 0.25, -7.3, 180, 2.6, rng=rng)
    hw.string_lights(H, (-12.6, 2.72, -9.75), (-1.2, 2.72, -9.75), 16, 0.28, colors=("bulb_orange", "bulb_purple"))
    hw.string_lights(H, (1.2, 2.72, -9.75), (10.1, 2.72, -9.75), 13, 0.28, colors=("bulb_orange", "bulb_purple"))
    hw.jack_tree(H, -7.0, 17.5, 4.0, rng=rng)
    hw.graves(H, 16.0, 17.6, 3, 1.6, rng=rng)
    H.decor("cat", (16.0, 0.8, 10.5), 180)
    H.decor("ghost_hang", (-16.2, 5.3, -12.0), 160)
    H.glow((-16.2, 4.1, -12.0), rgb("bfe9de"), 4, 0.6)
    H.decor("window_ghost", (12.0, 2 * S, -6.55), 180, 0.95, 2)
    H.glow((12.0, 2 * S + 1.4, -5.6), rgb("ffb35a"), 4, 0.7, 2)
    H.decor("spider", (-8.0, 3.12, -8.6), 200, 1.2)
    H.decor("skeleton", (-11.4, 0.25, -8.4), 140)
    H.light("Porch Lamp", (0.0, 2.6, -7.4), rgb("ffcf7a"), 8, 1.2, 9, "box", (0, 0.15, 0), (0.25, 0.3, 0.25))

    # Rooms
    H.room("Parlor", 0, X0, -3, Z0, 0, 0, S)
    H.room("Foyer", 0, -3, 3, Z0, Z1, 0, S)
    H.room("Dining Room", 0, 3, X1, Z0, 0, 0, S)
    H.room("Kitchen", 0, X0, -3, 0, Z1, 0, S)
    H.room("Music Room", 0, 3, X1, 0, Z1, 0, S)
    H.room("Tower Nook", 0, TX0, TX1, TZ0, TZ1, 0, S)
    H.room("Master Bedroom", 1, X0, -3, Z0, 0, S, 2 * S)
    H.room("Upstairs Hall", 1, -3, 3, Z0, Z1, S, 2 * S)
    H.room("Guest Room", 1, 3, X1, Z0, 0, S, 2 * S)
    H.room("Sewing Room", 1, X0, -3, 0, Z1, S, 2 * S)
    H.room("Nursery", 1, 3, X1, 0, Z1, S, 2 * S)
    H.room("Tower Study", 1, TX0, TX1, TZ0, TZ1, S, 2 * S)
    H.room("Tower Lookout", 2, TX0, TX1, TZ0, TZ1, 2 * S, 2 * S + 3)
    H.room("Gazebo", 9, GX - 2.5, GX + 2.5, GZ - 2.5, GZ + 2.5, -1, 5)
    H.room("Family Plot", 9, 12.5, 19.5, 10.5, 17, -1, 5)
    H.room("Front Garden", 9, LX0, LX1, LZ0, Z0, -1, 20)
    H.room("Back Garden", 9, LX0, LX1, Z0, LZ1, -1, 20)

    # Gameplay
    H.suspect_spot("Groundskeeper", (-14.0, 0, 15.0), facing(1, -0.5))
    H.suspect_spot("Heiress", (-5.0, 0, -4.0), facing(-1, -1))
    H.suspect_spot("Rival", (12.0, 0, -3.8), facing(-1, -1))
    H.suspect_spot("Cook", (-6.5, 0, 5.4), facing(0, -1))
    for p in ((-9.5, 0.2, -6.5), (-1.0, 0.2, 6.5), (9.5, 0.2, -6.5), (-9.5, 0.2, 6.5), (9.5, 0.2, 6.5), (13.5, 0.2, -6.5),
              (-9.5, S + 0.2, -6.5), (-1.5, S + 0.2, -6.5), (9.5, S + 0.2, -3.0), (-9.5, S + 0.2, 3.0), (5.0, S + 0.2, 6.5),
              (13.5, S + 0.2, -3.5), (12.0, 2 * S + 0.2, -5.0), (16.0, 0.2, 16.5), (-20.0, 0.2, 20.0), (20.0, 0.2, -16.0),
              (0.0, 0.5, 14.0), (-12.0, 0.4, -8.0)):
        H.clue(p)
    for p in ((17.0, 0.25, 13.5), (-9.0, S + 0.25, 5.0), (13.0, 0.25, -6.0), (-19.0, 0.25, -15.0)):
        H.trap_piece(p)
    H.L["trapSite"] = {"p": [GX, 0.3, GZ]}
    H.L["solverSpawns"] = [{"p": [-2.25 + i * 1.5, 0.1, LZ0 - 2.5]} for i in range(4)]
    H.L["haunterSpawn"] = {"p": [12.0, 2 * S + 1.0, -5.0]}
    H.L["lot"] = {"min": [LX0, LZ0], "max": [LX1, LZ1]}
    return H


# =============================================================================
# The Hollow Creek Historical Society: the fifth call, where the Mask Keeper is waiting
# =============================================================================
def museum():
    H = Layout("Historical Society", "HistoricalSociety", "Museum",
               "The Hollow Creek Historical Society: a red-brick museum with white columns, a gallery of "
               "folklore masks, a reading room that smells of lavender and old paper, and an archive "
               "upstairs. It may close after Halloween. Large: two floors, a courtyard and a workshop.")
    H.L["size"] = "Large"
    H.L["floors"] = 2
    H.L["storey"] = STOREY
    C = {"wall": rgb("8a3e30"), "inner": rgb("cfc3a8"), "upper": rgb("b8a888"), "trim": rgb("efe8da"), "roof": rgb("3a3640"),
         "floor": rgb("6a4630"), "marble": rgb("d8d2c6"), "grass": rgb("2b402a"), "path": rgb("8f877a"), "wood": rgb("4e3220"),
         "glass": rgb("bfe0e8"), "stone": rgb("9a968e"), "iron": rgb("26262b"), "hedge": rgb("1f3d22"), "green": rgb("2f5a3a"),
         "velvet": rgb("6a1f2a"), "brass": rgb("b08d3c"), "bronze": rgb("6a5a3a"), "paper": rgb("e8dcc0")}
    X0, X1, Z0, Z1, S = -11.0, 11.0, -6.0, 8.0, STOREY
    LX0, LX1, LZ0, LZ1 = -18.0, 18.0, -16.0, 17.0

    lawn(H, LX0, LX1, LZ0, LZ1, [(X0, X1, Z0, Z1)], C["grass"])
    stair_hole = (-2.5, -0.5, 2.0, 6.6)
    H.slab("Floor", 0.0, X0, X1, Z0, Z1, [], C["floor"], 0, 0.25)
    H.box("HallMarble", (0, 0.01, -2.5), (5.8, 0.02, 6.8), C["marble"], 0, "nocollide", "floor")
    H.slab("UpperFloor", S, X0, X1, Z0, Z1, [stair_hole], C["floor"], 1, 0.25)
    H.stairs("Stairs", -2.5, -0.5, 2.0, 0.0, 13, 1, 0, C["wood"])
    H.box("Banister", (-0.45, S + 0.5, 4.3), (0.08, 1.0, 4.6), C["wood"], 1, "solid", "rail")

    # The portico: steps, four white columns and a pediment
    H.box("PorticoFloor", (0.0, 0.125, -7.75), (12.0, 0.25, 3.5), C["marble"], 9, "solid", "floor")
    H.box("PorticoStep", (0.0, 0.06, -9.8), (6.0, 0.12, 0.6), C["marble"], 9, "solid", "floor")
    for i, x in enumerate((-4.5, -1.5, 1.5, 4.5)):
        H.box(f"Column{i}", (x, 0.25 + (2 * S - 0.45) / 2, -8.9), (0.7, (2 * S - 0.45) / 2, 0.7), C["trim"], 9, "solid", "porch", "cyl")
        H.box(f"ColumnCap{i}", (x, 2 * S - 0.1, -8.9), (0.95, 0.2, 0.95), C["trim"], 9, "solid", "porch")
    H.box("Entablature", (0.0, 2 * S + 0.2, -7.9), (12.4, 0.6, 3.9), C["trim"], 2, "solid", "roof")
    for side in (-1, 1):
        H.box(f"Pediment{side}", (side * 3.1, 2 * S + 1.15, -9.6), (6.6, 0.25, 0.6), C["trim"], 2, "solid", "roof", r=(0, 0, -side * 17))
    for i in range(6):
        w = 11.4 * (1 - (i + 0.5) / 6)
        H.box(f"PedimentFill{i}", (0.0, 2 * S + 0.55 + i * 0.28, -9.5), (w, 0.28, 0.2), C["wall"], 2, "solid", "roof")
    H.box("PedimentClock", (0.0, 2 * S + 1.0, -9.62), (0.9, 0.9, 0.05), rgb("f4ecd0"), 2, "glass", "roof")

    shell(H, "Ground", X0, X1, Z0, Z1, 0.0, S, 0, C["wall"], {
        "S": [gap(0.0, 2.0), win(-7.0, 1.6, 0.8, 2.6), win(7.0, 1.6, 0.8, 2.6)],
        "N": [gap(0.0, 1.4), win(-7.0), win(7.0)],
        "W": [win(-2.0), win(4.0)],
        "E": [win(-2.0), win(4.0)],
    }, trim=C["trim"])
    shell(H, "Upper", X0, X1, Z0, Z1, S, S, 1, C["wall"], {
        "S": [win(-7.0, 1.4), win(-4.0, 1.0), win(4.0, 1.0), win(7.0, 1.4)],
        "N": [win(-7.0), win(0.0, 1.0), win(7.0)],
        "W": [win(-2.0), win(4.0)],
        "E": [win(-2.0), win(4.0)],
    }, trim=C["trim"])
    # ground: gallery | hall | gift shop in front, gallery | back hall | curator's office behind
    inner(H, "G_W", "z", -3.0, Z0 + 0.15, Z1 - 0.15, 0, S, 0, C["inner"], [gap(-2.5, 2.4), gap(5.0)])
    inner(H, "G_E", "z", 3.0, Z0 + 0.15, Z1 - 0.15, 0, S, 0, C["inner"], [gap(-2.5, 1.4), gap(5.0)])
    inner(H, "G_Mid", "x", 1.0, -3.0, 3.0, 0, S, 0, C["inner"], [gap(1.2, 1.8)])
    inner(H, "G_EastMid", "x", 1.0, 3.0, X1 - 0.15, 0, S, 0, C["inner"])
    door_x(H, "Door_Front", 0.0, Z0, 0, 2.0, 0)
    door_x(H, "Door_Courtyard", 0.0, Z1, 0, 1.4, 0)
    door_z(H, "Door_GiftShop", 3.0, -2.5, 0, 1.4, 0)
    door_z(H, "Door_Office", 3.0, 5.0, 0, 1.2, 0)
    # upstairs: reading room | landing | archive
    inner(H, "U_W", "z", -3.0, Z0 + 0.15, Z1 - 0.15, S, S, 1, C["upper"], [gap(-2.0, 1.2)])
    inner(H, "U_E", "z", 3.0, Z0 + 0.15, Z1 - 0.15, S, S, 1, C["upper"], [gap(-2.0, 1.2)])
    door_z(H, "Door_ReadingRoom", -3.0, -2.0, S, 1.2, 1)
    door_z(H, "Door_Archive", 3.0, -2.0, S, 1.2, 1)
    H.ceiling("Ceiling", 2 * S, X0, X1, Z0, Z1, rgb("ddd6c8"))
    H.gable_roof("Roof", X0, X1, Z0, Z1, 2 * S, 3.4, C["roof"], C["wall"], overhang=0.6)
    # A little cupola with a weathervane on the ridge
    H.box("Cupola", (0.0, 2 * S + 3.9, 1.0), (2.2, 1.6, 2.2), C["trim"], 2, "solid", "roof")
    H.box("CupolaLight", (0.0, 2 * S + 3.9, -0.12), (1.2, 0.9, 0.05), rgb("ffcf7a"), 2, "glass", "roof")
    for i in range(4):
        w = 2.6 * (1 - i / 4) + 0.2
        H.box(f"CupolaRoof{i}", (0.0, 2 * S + 4.85 + i * 0.3, 1.0), (w, 0.3, w), C["green"], 2, "solid", "roof")
    H.box("Weathervane", (0.0, 2 * S + 6.4, 1.0), (0.08, 1.4, 0.08), C["iron"], 2, "solid", "roof")
    H.box("VaneArrow", (0.0, 2 * S + 6.9, 1.0), (1.2, 0.08, 0.08), C["iron"], 2, "solid", "roof", r=(0, 30, 0))
    H.box("ChimneyE", (8.5, 2 * S + 2.6, 4.0), (1.0, 3.6, 1.0), rgb("6a2e24"), 2, "solid", "roof")

    # The Mask Gallery: four folklore masks under glass, and one empty plinth
    for i, (x, z, mask, mc) in enumerate(((-9.0, -4.0, "sphere", rgb("e0772a")), (-5.0, -4.0, "capsule", rgb("d8e0f0")),
                                         (-9.0, 6.0, "box", rgb("ff9a3a")), (-5.0, 6.0, "cyl", rgb("5a4a3a")))):
        H.box(f"CasePlinth{i}", (x, 0.5, z), (1.2, 1.0, 1.2), C["wood"], 0, "solid", "furniture")
        H.box(f"CaseGlass{i}", (x, 1.45, z), (1.0, 0.9, 1.0), C["glass"], 0, "glass", "furniture")
        H.box(f"CaseMask{i}", (x, 1.35, z), (0.35, 0.4, 0.2), mc, 0, "nocollide", "decor", mask)
    H.box("EmptyPlinth", (-7.0, 0.55, 1.0), (1.4, 1.1, 1.4), C["marble"], 0, "solid", "furniture")
    H.box("EmptyPlinthCard", (-7.0, 1.12, 0.35), (0.5, 0.04, 0.3), C["paper"], 0, "nocollide", "decor", r=(-20, 0, 0))
    H.box("GalleryRope", (-7.0, 0.85, -0.2), (3.0, 0.05, 0.05), C["velvet"], 0, "nocollide", "decor")
    H.possessable("Suit of Armour", "capsule", (-10.4, 1.0, 1.0), (0.6, 1.0, 0.5), rgb("9aa0a8"), False, 0)
    H.possessable("Founder's Portrait", "box", (-10.8, 1.8, -1.5), (0.08, 1.4, 1.0), C["bronze"], False, 0)
    H.possessable("Rope Post", "cyl", (-5.5, 0.5, -0.2), (0.15, 0.5, 0.15), C["brass"], True, 0)
    H.light("Gallery Spotlight", (-7.0, 2.9, 1.0), rgb("fff0d0"), 9, 1.5, 0, "cyl", (0, 0.15, 0), (0.4, 0.15, 0.4))
    H.light("Mask Case Light", (-7.0, 2.9, -4.0), rgb("ffe2b0"), 7, 1.2, 0, "box", (0, 0.1, 0), (0.6, 0.1, 0.2))
    # Entrance hall and back hall
    H.box("ReceptionDesk", (1.8, 0.55, -4.2), (1.0, 1.1, 2.4), C["wood"], 0, "solid", "furniture")
    H.possessable("Visitors' Book", "box", (1.8, 1.15, -4.2), (0.4, 0.06, 0.5), C["velvet"], True, 0)
    H.possessable("Donation Box", "box", (-2.3, 0.6, -5.3), (0.5, 1.2, 0.5), C["wood"], True, 0)
    H.light("Hall Chandelier", (0.0, 2.85, -2.5), rgb("ffd28a"), 9, 1.5, 0, "cyl", (0, 0.15, 0), (0.9, 0.1, 0.9))
    H.possessable("Grandfather Clock", "box", (2.5, 1.2, 7.4), (0.6, 2.4, 0.8), C["wood"], False, 0)
    H.light("Back Hall Sconce", (2.7, 2.0, 4.0), rgb("ffd28a"), 6, 1.0, 0, "box", (0.1, 0, 0), (0.15, 0.4, 0.15))
    # Gift shop and tea corner
    H.box("ShopCounter", (6.0, 0.5, 0.3), (4.0, 1.0, 0.7), C["wood"], 0, "solid", "furniture")
    H.possessable("Postcard Rack", "cyl", (9.8, 0.9, -4.8), (0.5, 0.9, 0.5), rgb("c8a06a"), True, 0)
    H.possessable("Tea Trolley", "box", (5.0, 0.45, -5.0), (1.0, 0.9, 0.6), C["brass"], True, 0)
    H.table("TeaTable", (8.6, 0, -2.4), (1.0, 0.75, 1.0), 0, C["paper"], C["wood"])
    H.light("Shop Lamp", (7.0, 2.85, -2.5), rgb("ffe0b0"), 8, 1.2, 0, "cyl", (0, 0.1, 0), (0.5, 0.1, 0.5))
    # Curator's office
    H.table("CuratorDesk", (7.0, 0, 5.8), (2.0, 0.78, 0.9), 0, C["wood"], C["wood"])
    H.possessable("Typewriter", "box", (7.0, 0.92, 5.8), (0.5, 0.2, 0.4), rgb("2a2a2f"), True, 0)
    H.possessable("Filing Cabinet", "box", (10.5, 0.75, 7.3), (0.6, 1.5, 0.6), rgb("5a6a5a"), False, 0)
    H.box("LoanLedgerShelf", (10.7, 1.2, 3.0), (0.4, 2.4, 2.0), C["wood"], 0, "solid", "furniture")
    H.light("Green Desk Lamp", (7.8, 1.0, 6.0), rgb("c8ffc0"), 6, 1.2, 0, "cyl", (0, -0.15, 0), (0.25, 0.15, 0.25), rgb("2f6a3a"))
    # Upstairs: the reading room (lavender and old paper) and the archive
    H.table("ReadingTable", (-7.0, S, 1.0), (4.0, 0.78, 1.4), 1, C["wood"], C["wood"])
    for i, z in enumerate((-5.5, 7.5)):
        H.box(f"Bookcase{i}", (-7.0, S + 1.2, z), (6.0, 2.4, 0.5), C["wood"], 1, "solid", "furniture")
    H.possessable("Library Ladder", "box", (-9.5, S + 1.3, 6.9), (0.6, 2.6, 0.15), C["brass"], True, 1)
    H.possessable("Globe", "sphere", (-10.0, S + 1.0, -3.0), (0.7, 0.7, 0.7), rgb("3a6a8a"), True, 1)
    H.possessable("Card Catalogue", "box", (-3.6, S + 0.7, 5.0), (0.6, 1.4, 1.6), C["wood"], False, 1)
    H.light("Reading Lamp", (-7.0, S + 1.0, 1.0), rgb("ffe0a0"), 7, 1.2, 1, "cyl", (0, -0.15, 0), (0.3, 0.15, 0.3), rgb("2f6a3a"))
    for i in range(3):
        H.box(f"ArchiveShelf{i}", (7.0, S + 1.1, -3.5 + i * 3.6), (6.0, 2.2, 0.6), rgb("5a5a5e"), 1, "solid", "furniture")
        H.decor("cobweb", (X1 - 0.6, 2 * S - 0.05, -4.5 + i * 4.5), 45 + 90 * (i % 2), 1.0, 1)
    H.possessable("Map Chest", "box", (9.8, S + 0.45, 7.2), (1.4, 0.9, 0.8), C["wood"], True, 1)
    H.possessable("Hatbox Tower", "cyl", (4.0, S + 0.6, 7.2), (0.6, 0.6, 0.6), rgb("8a5a7a"), True, 1)
    H.light("Archive Bulb", (7.0, 2 * S - 0.3, 1.0), rgb("ffd8a0"), 8, 1.0, 1, "cyl", (0, 0.1, 0), (0.15, 0.2, 0.15))
    H.light("Landing Sconce", (2.7, S + 2.0, -3.5), rgb("ffd28a"), 7, 1.1, 1, "box", (0.1, 0, 0), (0.15, 0.4, 0.15))
    H.decor("window_ghost", (7.0, S, Z0 + 0.45), 180, 0.95, 1)
    H.glow((7.0, S + 1.4, Z0 + 1.2), rgb("ffb35a"), 4, 0.7, 1)

    # Grounds: iron fence, the founder's statue, lamps along the walk, the courtyard and its fountain
    H.picket_fence("Fence", LX0 + 0.3, LX1 - 0.3, LZ0 + 0.3, LZ1 - 0.3, gate=(0.0, 3.0), color=C["iron"])
    for side in (-1, 1):
        H.box(f"GatePillar{side}", (side * 1.9, 1.0, LZ0 + 0.3), (0.7, 2.0, 0.7), C["stone"], 9, "solid", "fence")
        H.decor("jack", (side * 1.9, 2.0, LZ0 + 0.3), 180, 0.9)
        H.glow((side * 1.9, 2.5, LZ0 + 0.3), rgb("ff9a3a"), 5, 1.0)
        H.light(f"Walk Lamp {'LR'[side > 0]}", (side * 2.0, 2.9, -12.5), rgb("ffd08a"), 7, 1.1, 9, "cyl", (0, -1.45, 0), (0.12, 1.45, 0.12), C["iron"])
        H.box(f"Hedge{side}", (side * 10.5, 0.7, -12.5), (9.0, 1.4, 1.2), C["hedge"], 9, "solid", "hedge")
    path(H, "FrontWalk", -1.4, 1.4, LZ0, -10.0, C["path"])
    H.box("StatuePlinth", (-8.0, 0.8, -9.5), (1.6, 1.6, 1.6), C["stone"], 9, "solid", "furniture")
    H.box("StatueBody", (-8.0, 2.4, -9.5), (0.7, 0.8, 0.5), C["bronze"], 9, "solid", "decor", "capsule")
    H.box("StatueHead", (-8.0, 3.45, -9.5), (0.4, 0.45, 0.4), C["bronze"], 9, "solid", "decor", "sphere")
    H.box("StatueHat", (-8.0, 3.75, -9.5), (0.5, 0.25, 0.5), C["bronze"], 9, "solid", "decor", "cyl")
    H.box("NoticeBoard", (8.0, 1.2, -10.0), (2.4, 1.4, 0.12), C["wood"], 9, "solid", "furniture")
    H.box("NoticeBoardPoster", (8.0, 1.25, -10.08), (1.6, 0.9, 0.02), C["paper"], 9, "nocollide", "decor")
    H.box("NoticeBoardPost", (8.0, 0.5, -10.0), (0.15, 1.0, 0.15), C["wood"], 9, "solid", "fence")
    for i, (x, z, h) in enumerate(((-15.0, -13.0, 7.0), (15.0, -13.5, 7.5), (-15.5, 14.0, 6.5))):
        H.tree(f"Tree{i}", x, z, h, None if i == 2 else (rgb("c45a24") if i == 0 else rgb("b8862a")))
    H.decor("crow", (-15.5, 4.9, 14.3), 140)
    # courtyard and fountain (the trap site)
    path(H, "CourtyardPaving", -6.0, 6.0, 8.5, 15.5, C["path"])
    H.box("FountainBasin", (0.0, 0.35, 12.0), (3.6, 0.7, 3.6), C["stone"], 9, "solid", "furniture", "cyl")
    H.box("FountainWater", (0.0, 0.66, 12.0), (3.2, 0.04, 3.2), rgb("2d4f6e"), 9, "nocollide", "water", "cyl")
    H.box("FountainColumn", (0.0, 1.2, 12.0), (0.5, 1.0, 0.5), C["stone"], 9, "solid", "furniture", "cyl")
    H.box("FountainBowl", (0.0, 2.2, 12.0), (1.4, 0.25, 1.4), C["stone"], 9, "solid", "furniture", "cyl")
    for side in (-1, 1):
        H.possessable(f"Courtyard Bench {'WE'[side > 0]}", "box", (side * 4.5, 0.4, 12.0), (0.7, 0.8, 2.0), C["wood"], True, 9)
    H.light("Courtyard Lantern", (0.0, 2.7, 9.0), rgb("ffcf7a"), 8, 1.2, 9, "box", (0, -0.15, 0), (0.25, 0.35, 0.25))
    # the restoration workshop (back right)
    WX0, WX1, WZ0, WZ1 = 9.0, 15.0, 10.0, 15.0
    H.slab("WorkshopFloor", 0.05, WX0, WX1, WZ0, WZ1, [], C["wood"], 9, 0.1)
    shell(H, "Workshop", WX0, WX1, WZ0, WZ1, 0, 2.7, 9, rgb("6a5a4a"), {"W": [gap(12.5, 1.2)], "S": [win(12.0, 1.0)]})
    H.box("WorkshopRoof", (12.0, 2.95, 12.5), (6.6, 0.15, 5.6), C["roof"], 9, "solid", "roof", r=(-8, 0, 0))
    door_z(H, "Door_Workshop", WX0, 12.5, 0, 1.2, 9)
    H.table("Workbench", (12.0, 0, 14.2), (4.0, 0.9, 0.8), 9, C["wood"], C["wood"])
    H.possessable("Plaster Mask Mould", "sphere", (11.0, 1.05, 14.2), (0.4, 0.3, 0.3), rgb("e8e4da"), True, 9)
    H.light("Workshop Bulb", (12.0, 2.4, 12.5), rgb("ffd08a"), 6, 1.0, 9, "cyl", (0, 0.1, 0), (0.1, 0.2, 0.1))
    # old founders' graves by the back fence
    for i, (x, z) in enumerate(((-14.0, 9.0), (-12.0, 9.5), (-14.5, 11.5))):
        grave(H, f"Grave{i}", x, z, C["stone"])

    # Halloween, museum style: a jack-o'-lantern arch, lanterns on the steps, lights on the portico
    rng = random.Random(53)
    hw.jack_arch(H, 0.0, LZ0 + 0.3, 3.2, 3.4, 180, rng=rng)
    hw.string_lights(H, (-6.0, 2 * S - 0.35, -9.75), (6.0, 2 * S - 0.35, -9.75), 18, 0.35)
    hw.luminarias(H, (0.0, LZ0 + 1.5), (0.0, -10.4), 1.8, 1.9)
    hw.porch_display(H, 3.5, 0.25, -6.4, 180, 2.2, rng=rng)
    hw.graves(H, -12.5, 12.8, 2, 1.4, rng=rng)
    H.decor("ghost_hang", (15.0, 5.3, -13.5), 170)
    H.glow((15.0, 4.1, -13.5), rgb("bfe9de"), 4, 0.6)
    H.decor("cat", (-8.0, 1.6, -9.0), 190)
    H.decor("skeleton", (5.8, 0.25, -8.6), 160)
    for x in (-3.4, 3.4):
        H.decor("jack", (x, 0.25, -9.3), 180, 1.0)
        H.glow((x, 0.75, -9.3), rgb("ff9a3a"), 5, 1.0)
    H.decor("mailbox", (4.0, 0, LZ0 - 0.6), 180)
    H.light("Portico Lantern", (0.0, 2 * S - 0.6, -8.0), rgb("ffcf7a"), 9, 1.3, 9, "box", (0, 0.15, 0), (0.3, 0.4, 0.3))

    # Rooms
    H.room("Mask Gallery", 0, X0, -3, Z0, Z1, 0, S)
    H.room("Entrance Hall", 0, -3, 3, Z0, 1, 0, S)
    H.room("Back Hall", 0, -3, 3, 1, Z1, 0, S)
    H.room("Gift Shop", 0, 3, X1, Z0, 1, 0, S)
    H.room("Curator's Office", 0, 3, X1, 1, Z1, 0, S)
    H.room("Reading Room", 1, X0, -3, Z0, Z1, S, 2 * S)
    H.room("Landing", 1, -3, 3, Z0, Z1, S, 2 * S)
    H.room("Archive", 1, 3, X1, Z0, Z1, S, 2 * S)
    H.room("Portico", 9, -6, 6, -10, Z0, -1, 2 * S + 1)
    H.room("Courtyard", 9, -6, 6, Z1, 16, -1, 6)
    H.room("Restoration Workshop", 9, WX0, WX1, WZ0, WZ1, -1, 4)
    H.room("Front Lawn", 9, LX0, LX1, LZ0, -10, -1, 20)
    H.room("Museum Grounds", 9, LX0, LX1, -10, LZ1, -1, 20)

    # Gameplay
    H.suspect_spot("Groundskeeper", (6.5, 0, 11.0), facing(-1, -0.4))
    H.suspect_spot("Heiress", (-6.0, 0, -1.6), facing(1, -0.6))
    H.suspect_spot("Rival", (5.6, 0.25, -7.8), facing(-1, -1))
    H.suspect_spot("Cook", (7.5, 0, -3.8), facing(-1, -0.3))
    for p in ((-10.5, 0.2, -5.5), (-2.5, 0.2, -1.0), (10.5, 0.2, -5.5), (-10.5, 0.2, 7.5), (10.5, 0.2, 2.0), (2.5, 0.2, 6.5),
              (-10.5, S + 0.2, -5.5), (-4.0, S + 0.2, 1.0), (10.5, S + 0.2, -5.5), (4.0, S + 0.2, 0.0), (10.5, S + 0.2, 5.0),
              (1.5, S + 0.2, 7.5), (14.0, 0.2, 14.0), (-16.5, 0.2, 15.5), (16.5, 0.2, -14.5), (-4.5, 0.2, 14.5),
              (-12.0, 0.2, -8.0), (0.0, 0.9, 12.0)):
        H.clue(p)
    for p in ((13.5, 0.25, 11.0), (-9.0, S + 0.25, -4.0), (9.5, 0.25, 5.0), (-16.0, 0.25, -14.0)):
        H.trap_piece(p)
    H.L["trapSite"] = {"p": [0.0, 0.3, 12.0]}
    H.L["solverSpawns"] = [{"p": [-2.25 + i * 1.5, 0.1, LZ0 - 2.5]} for i in range(4)]
    H.L["haunterSpawn"] = {"p": [7.0, S + 1.0, 4.5]}
    H.L["lot"] = {"min": [LX0, LZ0], "max": [LX1, LZ1]}
    return H


HOUSES = {"PembertonCottage": cottage, "HollowCreekFarm": farm, "WillowLaneVictorian": victorian,
          "HistoricalSociety": museum}

if __name__ == "__main__":
    for hid, make in HOUSES.items():
        make().save(f"Houses/{hid}.json")
