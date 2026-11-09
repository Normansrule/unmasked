#!/usr/bin/env python3
"""
Fills in Hollow Creek around the hand-placed landmarks (make_town.py calls build()).

The hand-made part of the town is the important stuff: HQ, the five haunted lots, Main Street's shops,
the square and the church. Around it the town used to be grass. This module grows the rest of the
town as a pipeline, the way Azgaar's Fantasy Map Generator separates settings, generators, world data
and the renderer:

  1. Occupancy grid    : every box, prop and lot already in the town is stamped onto a 1 m grid,
                         so nothing new is ever built on top of something old.
  2. Side streets      : a few more streets, each checked against the grid first, so the town has
                         blocks instead of one long cross.
  3. Parcels           : both sides of every street are cut into house plots (like 3DWorld's city
                         plots): a house with a porch, a path, a mailbox and a hedge or fence.
  4. Yards             : each plot's yard is dressed with a small Wave Function Collapse solver
                         (mxgmn/WaveFunctionCollapse's "simple tiled" model): tiles such as lawn,
                         stepping stones, flower beds, a pumpkin patch, a shed or a tree, with rules
                         for which tiles may sit next to each other. The house and its path are
                         fixed before the solver runs, the way WFC is usually steered.
  5. Landmarks         : the biggest empty spaces left get a place to visit: a corn maze (carved
                         like a dungeon: rooms joined by doors, as in BenPyton/ProceduralDungeon), an
                         orchard, a pumpkin farm, the old cemetery, the mill pond, a scout camp, a
                         hay field. Props are scattered with spacing rules, the way infinigen places
                         assets with constraints instead of at random.
  6. Districts         : every part of town gets a name (Downtown, Mill Fields, Orchard Hill...),
                         so "where am I?" always has an answer.
  7. Lost lanterns     : collectibles hidden in yards and landmarks (Town/LostLantern.cs).

These are ideas taken from those projects; the code here is written from scratch, in plain Python,
with a fixed seed so every machine builds the same town.
"""
import math
import random

import numpy as np

from layoutlib import rgb

# Grid codes
FREE, SOLID, ROAD, WATER, KEEP, NEW = 0, 1, 2, 3, 4, 5

ROAD_W = 8.0
SETBACK = ROAD_W / 2 + 2.6  # road half-width, sidewalk and a little verge


class Grid:
    """A 1 m occupancy grid over the town, seen from above."""

    def __init__(self, x0, x1, z0, z1):
        self.x0, self.z0 = x0, z0
        self.w, self.h = int(x1 - x0), int(z1 - z0)
        self.a = np.zeros((self.h, self.w), dtype=np.uint8)

    def _idx(self, x0, x1, z0, z1):
        i0 = max(0, int(math.floor(x0 - self.x0)))
        i1 = min(self.w, int(math.ceil(x1 - self.x0)))
        j0 = max(0, int(math.floor(z0 - self.z0)))
        j1 = min(self.h, int(math.ceil(z1 - self.z0)))
        return i0, i1, j0, j1

    def mark(self, x0, x1, z0, z1, code, only_free=False):
        i0, i1, j0, j1 = self._idx(x0, x1, z0, z1)
        if i1 <= i0 or j1 <= j0:
            return
        if only_free:
            sub = self.a[j0:j1, i0:i1]
            sub[sub == FREE] = code
        else:
            self.a[j0:j1, i0:i1] = code

    def free(self, x0, x1, z0, z1):
        if x0 < self.x0 or z0 < self.z0 or x1 > self.x0 + self.w or z1 > self.z0 + self.h:
            return False
        i0, i1, j0, j1 = self._idx(x0, x1, z0, z1)
        return not self.a[j0:j1, i0:i1].any()

    def largest_free_rect(self, min_side=16):
        """The biggest empty rectangle (maximal-rectangle-in-histogram), as (x0, x1, z0, z1) or None."""
        heights = np.zeros(self.w, dtype=np.int32)
        best, best_area = None, 0
        for j in range(self.h):
            row = self.a[j]
            heights = np.where(row == FREE, heights + 1, 0)
            stack = []
            for i in range(self.w + 1):
                hgt = heights[i] if i < self.w else 0
                start = i
                while stack and stack[-1][1] >= hgt:
                    s, sh = stack.pop()
                    width = i - s
                    if sh >= min_side and width >= min_side and sh * width > best_area:
                        best_area = sh * width
                        best = (s, i, j - sh + 1, j + 1)
                    start = s
                stack.append((start, hgt))
        if best is None:
            return None
        i0, i1, j0, j1 = best
        return (self.x0 + i0, self.x0 + i1, self.z0 + j0, self.z0 + j1)


def rotated_half_extents(size, euler):
    """Half-size on x and z of a box turned by Unity Euler angles (z, then x, then y)."""
    rx, ry, rz = (math.radians(v) for v in euler)
    cz, sz_ = math.cos(rz), math.sin(rz)
    cx, sx_ = math.cos(rx), math.sin(rx)
    cy, sy_ = math.cos(ry), math.sin(ry)
    Rz = np.array([[cz, -sz_, 0], [sz_, cz, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cx, -sx_], [0, sx_, cx]])
    Ry = np.array([[cy, 0, sy_], [0, 1, 0], [-sy_, 0, cy]])
    R = Ry @ Rx @ Rz
    h = np.abs(R) @ (np.array(size) / 2)
    return h[0], h[2]


def stamp_existing(grid, L, lots, keep_rooms, road_rooms):
    """Everything already in the town goes on the grid."""
    for b in L["boxes"]:
        g = b["g"]
        if g == "ground":
            continue
        (x, _, z), (sx, sy, sz) = b["p"], b["s"]
        if any(abs(v) > 1 for v in b["r"]):
            hx, hz = rotated_half_extents((sx, sy, sz), b["r"])
        else:
            hx, hz = sx / 2, sz / 2
        code = WATER if g == "water" else ROAD if g == "road" else SOLID
        if g == "tree" and "Canopy" in b["n"]:
            continue  # canopies hang over things; the trunk is what's in the way
        grid.mark(x - hx, x + hx, z - hz, z + hz, code)
    for d in L["decor"]:
        x, _, z = d["p"]
        grid.mark(x - 0.8, x + 0.8, z - 0.8, z + 0.8, SOLID)
    for lot in lots:
        (x0, z0), (x1, z1) = lot["lot"]["min"], lot["lot"]["max"]
        grid.mark(x0 - 3, x1 + 3, z0 - 3, z1 + 3, KEEP)
    for r in L["rooms"]:
        if r["n"] in keep_rooms:
            grid.mark(r["min"][0], r["max"][0], r["min"][2], r["max"][2], KEEP)
        elif r["n"] in road_rooms:
            grid.mark(r["min"][0], r["max"][0], r["min"][2], r["max"][2], ROAD, only_free=True)


# =============================================================================
# Wave Function Collapse, simple tiled model
# =============================================================================
# Tiles a yard can be made of. weight: how common. Each tile lists the tiles allowed next to it
# (the rule is symmetric, checked both ways). "house" and "walk" are fixed by the plot first.
YARD_TILES = {
    "lawn":   {"w": 7.0, "ok": {"lawn", "stone", "bed", "patch", "tree", "shed", "grave", "hay", "spook", "house", "walk"}},
    "stone":  {"w": 0.8, "ok": {"lawn", "stone", "bed", "patch", "shed", "walk", "house"}},
    "bed":    {"w": 1.2, "ok": {"lawn", "stone", "bed", "house", "walk", "tree"}},
    "patch":  {"w": 1.0, "ok": {"lawn", "stone", "patch", "hay"}},
    "tree":   {"w": 0.9, "ok": {"lawn", "bed", "spook", "grave"}},
    "shed":   {"w": 0.25, "ok": {"lawn", "stone"}},
    "grave":  {"w": 0.35, "ok": {"lawn", "grave", "tree", "spook"}},
    "hay":    {"w": 0.4, "ok": {"lawn", "patch"}},
    "spook":  {"w": 0.45, "ok": {"lawn", "tree", "grave"}},
    "house":  {"w": 0.0, "ok": {"lawn", "stone", "bed", "house", "walk"}},
    "walk":   {"w": 0.0, "ok": {"lawn", "stone", "bed", "walk", "house"}},
}
NAMES = list(YARD_TILES)
COMPAT = {a: {b for b in NAMES if b in YARD_TILES[a]["ok"] and a in YARD_TILES[b]["ok"]} for a in NAMES}


def wfc(cols, rows, fixed, rng, tries=12):
    """Solve a cols x rows yard. fixed: {(i, j): tile}. Returns {(i, j): tile}.

    Lowest-entropy cell first, weighted random pick, then propagate the neighbour rules until
    nothing changes; on a contradiction start again with the next random seed."""
    open_tiles = [t for t in NAMES if YARD_TILES[t]["w"] > 0]
    for _ in range(tries):
        cells = {(i, j): set(open_tiles) for i in range(cols) for j in range(rows)}
        for k, t in fixed.items():
            if k in cells:
                cells[k] = {t}

        def propagate(stack):
            while stack:
                c = stack.pop()
                i, j = c
                allowed = set().union(*(COMPAT[t] for t in cells[c]))
                for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                    if n not in cells:
                        continue
                    before = cells[n]
                    after = before & allowed
                    if not after:
                        return False
                    if after != before:
                        cells[n] = after
                        stack.append(n)
            return True

        if not propagate(list(fixed)):
            continue
        ok = True
        while True:
            undecided = [(len(v) + rng.random() * 0.1, k) for k, v in cells.items() if len(v) > 1]
            if not undecided:
                break
            _, c = min(undecided)
            options = sorted(cells[c])
            weights = [YARD_TILES[t]["w"] for t in options]
            cells[c] = {rng.choices(options, weights)[0]}
            if not propagate([c]):
                ok = False
                break
        if ok:
            return {k: next(iter(v)) for k, v in cells.items()}
    return {k: fixed.get(k, "lawn") for k in ((i, j) for i in range(cols) for j in range(rows))}


# =============================================================================
# The town around the landmarks
# =============================================================================
WALLS = ["7a8a9a", "c8a06a", "9a7aa0", "a0b08a", "d0c0a0", "8a9aa0", "b07a6a", "7a9a8a", "a08a6a", "6a7a9a",
         "8a6a6a", "9a9a7a", "c49a7a", "6f8a74", "b8a46a", "8c6f8f", "5f7486", "a87a5a", "d8ccb0", "7d6b8a"]
ROOFS = ["3a2e2a", "2e2a3a", "4a2e2a", "5a2a2a", "2a3a4a", "3a3a2a", "4a3a5a"]
TRIMS = ["efe6d2", "e8dcc8", "f2ede0", "d8cdb8"]
LEAVES = ["c04a2a", "d0662a", "b8862a", "a83a24", "c89a3a", "8a4a2a"]

# The families of the new streets (Town/Doorstep.cs): who opens the door when you knock.
FAMILIES = ["the Abernathys", "the Bellweathers", "the Calloways", "the Dunmores", "the Ellsworths", "the Finches",
            "the Galloways", "the Hartleys", "the Iveses", "the Jessamines", "the Kittredges", "the Larkins",
            "the Merriweathers", "the Nightingales", "the Oakleys", "the Pruitts", "the Quills", "the Rowans",
            "the Sorensens", "the Thistlewoods", "the Underhills", "the Vances", "the Whitlocks", "the Yardleys",
            "the Ashcrofts", "the Brambles", "the Coopers", "the Delacroixes", "the Emberlys", "the Fairweathers",
            "the Goodwins", "the Hollises", "the Inglewoods", "the Juniper sisters", "the Kemps", "the Lindqvists",
            "the Mallorys", "the Norths", "the Okafors", "the Penhallows", "the Ramirezes", "the Sutcliffes",
            "the Tanakas", "the Wexfords"]

PARCEL_STYLES = {  # name: (house width range, depth range, height, porch, roof)
    "cottage":    ((7.5, 9.5), (7.0, 8.0), 3.4, "small", "gable"),
    "bungalow":   ((9.0, 11.0), (7.5, 9.0), 3.6, "wide", "gable"),
    "farmhouse":  ((9.5, 11.5), (8.0, 9.5), 6.2, "wide", "gable"),
    "foursquare": ((8.5, 10.0), (8.5, 10.0), 6.4, "small", "hip"),
    "saltbox":    ((9.0, 10.5), (7.5, 8.5), 5.0, "none", "gable"),
}


class TownGen:
    def __init__(self, T, building, street_lamps, road, lots, C, bounds, seed=31):
        self.T, self.building, self.street_lamps, self.road = T, building, street_lamps, road
        self.lots, self.C = lots, C
        self.rng = random.Random(seed)
        self.tx0, self.tx1, self.tz0, self.tz1 = bounds
        self.grid = Grid(*bounds)
        self.streets = []      # (name, axis, fixed, a0, a1): what the parcels line
        self.parcels = []
        self.features = []
        self.lanterns = []     # (name, where, (x, y, z))
        self.stats = {"houses": 0, "yards": 0, "props": 0}
        self.homes = []        # doors to knock on (Town/Doorstep.cs), filled by build_house
        self.snapshots = {}    # the grid at each stage, for the README picture

    # -- 1. occupancy ---------------------------------------------------------------------------
    def stamp(self, keep_rooms, road_rooms):
        stamp_existing(self.grid, self.T.L, self.lots, keep_rooms, road_rooms)
        g = self.grid
        # the edge of the woods and the creek banks stay wild
        g.mark(self.tx0, self.tx0 + 16, self.tz0, self.tz1, KEEP)
        g.mark(self.tx1 - 14, self.tx1, self.tz0, self.tz1, KEEP)
        g.mark(self.tx0, self.tx1, self.tz0, self.tz0 + 12, KEEP)
        g.mark(self.tx0, self.tx1, self.tz1 - 10, self.tz1, KEEP)

    def keep_spot(self, x, z, r=3.0):
        self.grid.mark(x - r, x + r, z - r, z + r, KEEP)

    # -- 2. side streets ------------------------------------------------------------------------
    def add_street(self, name, x0, z0, x1, z1, lamps=True, walk=True):
        """A new street, if its corridor is clear. Trees in the way are felled; anything else stops it."""
        along_x = abs(x1 - x0) > abs(z1 - z0)
        half = ROAD_W / 2 + 1.9
        rx0, rx1 = (min(x0, x1), max(x0, x1)) if along_x else (x0 - half, x0 + half)
        rz0, rz1 = (z0 - half, z0 + half) if along_x else (min(z0, z1), max(z0, z1))
        L = self.T.L
        felled = [b for b in L["boxes"] if b["g"] == "tree" and rx0 - 1 < b["p"][0] < rx1 + 1 and rz0 - 1 < b["p"][2] < rz1 + 1]
        trunks = {b["n"].replace("Trunk", "") for b in felled if b["n"].endswith("Trunk")}
        gone = [b for b in L["boxes"] if b["g"] == "tree" and any(b["n"].startswith(t) for t in trunks)]
        L["boxes"] = [b for b in L["boxes"] if not (b["g"] == "tree" and any(b["n"].startswith(t) for t in trunks))]
        for b in gone:
            (x, _, z), (sx, sy, sz) = b["p"], b["s"]
            hx, hz = rotated_half_extents((sx, sy, sz), b["r"])
            self.grid.mark(x - hx, x + hx, z - hz, z + hz, FREE)
        # street lamps standing where the new street meets an old one come down
        lamps = [d for d in L["decor"] if d["k"] == "streetlamp" and rx0 - 1 < d["p"][0] < rx1 + 1 and rz0 - 1 < d["p"][2] < rz1 + 1]
        for d in lamps:
            L["decor"].remove(d)
            L["glows"] = [gl for gl in L["glows"] if math.dist((gl["p"][0], gl["p"][2]), (d["p"][0], d["p"][2])) > 1.5]
            self.grid.mark(d["p"][0] - 0.8, d["p"][0] + 0.8, d["p"][2] - 0.8, d["p"][2] + 0.8, FREE)
        # what's left in the corridor, other than road it joins
        i0, i1, j0, j1 = self.grid._idx(rx0, rx1, rz0, rz1)
        sub = self.grid.a[j0:j1, i0:i1]
        blocked = int(((sub == SOLID) | (sub == KEEP)).sum())
        if blocked > 6:
            print(f"  worldgen: skipped {name} ({blocked} m² in the way)")
            return False
        self.road(name, x0, z0, x1, z1)
        self.grid.mark(rx0, rx1, rz0, rz1, ROAD)
        if lamps:
            self.street_lamps(name.replace(" ", "") + "Lamps", x0, z0, x1, z1, 26.0)
        if walk:
            L["life"]["walks"].append({"name": name, "from": [x0, z0], "to": [x1, z1], "side": ROAD_W / 2 + 0.9})
        self.T.L.setdefault("newRoads", []).append(name)
        return True

    def end_cap(self, name, x, z, r=7.0):
        """A turning circle at a dead end."""
        self.T.box(f"{name}Turn", (x, -0.035, z), (r * 2, 0.1, r * 2), self.C["road"], 9, "solid", "road", "cyl")
        self.grid.mark(x - r - 1, x + r + 1, z - r - 1, z + r + 1, ROAD)

    # -- 3. parcels -----------------------------------------------------------------------------
    def line_street(self, name, axis, fixed, a0, a1, sides=(-1, 1)):
        self.streets.append((name, axis, fixed, a0, a1, sides))

    def cut_parcels(self):
        rng = self.rng
        for name, axis, fixed, a0, a1, sides in self.streets:
            for side in sides:
                a = a0 + 2
                while a < a1 - 10:
                    placed = False
                    for width, depth in ((rng.uniform(15, 18), rng.uniform(20, 24)), (rng.uniform(14, 16), rng.uniform(16, 19)),
                                         (13.0, 14.5)):
                        front = fixed + side * SETBACK
                        back = front + side * depth
                        if axis == "x":  # street runs along x; plots stack in z
                            rect = (a, a + width, min(front, back), max(front, back))
                        else:
                            rect = (min(front, back), max(front, back), a, a + width)
                        if self.grid.free(rect[0] - 0.5, rect[1] + 0.5, rect[2] - 0.5, rect[3] + 0.5):
                            self.grid.mark(*rect, NEW)
                            self.parcels.append({"street": name, "axis": axis, "side": side, "rect": rect})
                            a += width + rng.uniform(1.0, 3.5)
                            placed = True
                            break
                    if not placed:
                        a += 1.5

    def build_parcels(self):
        for k, p in enumerate(self.parcels):
            self.build_house(k, p)

    def build_house(self, k, parcel):
        T, rng, C = self.T, self.rng, self.C
        x0, x1, z0, z1 = parcel["rect"]
        axis, side = parcel["axis"], parcel["side"]
        style = rng.choice(list(PARCEL_STYLES))
        (wr, dr, h, porch, roof) = PARCEL_STYLES[style]
        hw, hd = rng.uniform(*wr), rng.uniform(*dr)
        wall, roofc, trim = rgb(rng.choice(WALLS)), rgb(rng.choice(ROOFS)), rgb(rng.choice(TRIMS))
        # local frame: u runs along the street, v runs from the street into the plot
        if axis == "x":
            u0, u1 = x0, x1
            front_v = z0 if side > 0 else z1
        else:
            u0, u1 = z0, z1
            front_v = x0 if side > 0 else x1
        depth = abs((z1 - z0) if axis == "x" else (x1 - x0))
        width = u1 - u0
        uc = (u0 + u1) / 2 + rng.uniform(-1.2, 1.2)
        v_front = rng.uniform(5.5, 7.0)  # front of house, metres back from the plot's front line

        def P(u, v):  # local (u along street, v into plot) -> world (x, z)
            w = front_v + side * v
            return (u, w) if axis == "x" else (w, u)

        def rect(ua, ub, va, vb):
            (xa, za), (xb, zb) = P(ua, va), P(ub, vb)
            return min(xa, xb), max(xa, xb), min(za, zb), max(za, zb)

        bx0, bx1, bz0, bz1 = rect(uc - hw / 2, uc + hw / 2, v_front, v_front + hd)
        door = {("x", 1): "S", ("x", -1): "N", ("z", 1): "W", ("z", -1): "E"}[(axis, side)]
        name = f"Home{k}"
        # windows on the front and the sides you see from the street (nobody looks at the back)
        sides = door + {"S": "WE", "N": "WE", "W": "SN", "E": "SN"}[door]
        if roof == "hip":
            self.building(name, bx0, bx1, bz0, bz1, h, wall, roofc, door, gable=False, win_sides=sides)
            for i in range(3):  # a stepped hip roof over the flat one
                s = 1 - (i + 1) / 4
                T.box(f"{name}Hip{i}", ((bx0 + bx1) / 2, h + 0.6 + i * 0.5, (bz0 + bz1) / 2),
                      ((bx1 - bx0) * s + 0.4, 0.5, (bz1 - bz0) * s + 0.4), roofc, 9, "solid", "roof")
        else:
            self.building(name, bx0, bx1, bz0, bz1, h, wall, roofc, door, win_sides=sides)
        # chimney
        cu = uc + (hw / 2 - 1.0) * rng.choice((-1, 1))
        cx, cz = P(cu, v_front + hd * 0.6)
        T.box(f"{name}Chimney", (cx, h + 1.4, cz), (0.9, 2.8, 0.9), self.C["brick"], 9, "solid", "roof")
        # porch: a deck across the front with posts and a little roof
        door_u = uc
        if porch != "none":
            pw = hw * (0.95 if porch == "wide" else 0.5)
            pd = 2.2
            px0, px1, pz0, pz1 = rect(door_u - pw / 2, door_u + pw / 2, v_front - pd, v_front)
            T.box(f"{name}Porch", ((px0 + px1) / 2, 0.2, (pz0 + pz1) / 2), (px1 - px0, 0.4, pz1 - pz0), rgb("6a5a48"), 9, "solid", "porch")
            T.box(f"{name}PorchRoof", ((px0 + px1) / 2, 2.75, (pz0 + pz1) / 2), (px1 - px0 + 0.3, 0.18, pz1 - pz0 + 0.3), roofc, 9, "solid", "roof")
            n = 4 if porch == "wide" else 2
            for i in range(n):
                pu = door_u - pw / 2 + 0.2 + i * (pw - 0.4) / (n - 1)
                px, pz = P(pu, v_front - pd + 0.2)
                T.box(f"{name}Post{i}", (px, 1.55, pz), (0.16, 2.3, 0.16), trim, 9, "solid", "porch")
            sx, sz = P(door_u, v_front - pd - 0.35)
            T.box(f"{name}Step", (sx, 0.1, sz), (1.6, 0.2, 0.7) if axis == "x" else (0.7, 0.2, 1.6), rgb("6a5a48"), 9, "solid", "porch")
            v_step = v_front - pd - 0.7
        else:
            v_step = v_front - 0.4
        # path from the step to the sidewalk, and the mailbox at the end of it
        pa, pb = P(door_u, 0), P(door_u, v_step)
        T.box(f"{name}Path", ((pa[0] + pb[0]) / 2, -0.02, (pa[1] + pb[1]) / 2),
              (1.3, 0.1, abs(pb[1] - pa[1])) if axis == "x" else (abs(pb[0] - pa[0]), 0.1, 1.3), rgb("7a746c"), 9, "solid", "road")
        mx, mz = P(door_u + 1.6, 0.6)
        ry = {"S": 180, "N": 0, "W": -90, "E": 90}[door]
        T.decor("mailbox", (mx, 0, mz), ry)
        # the front boundary: a hedge, a picket fence, or nothing
        edge = rng.random()
        gap = 1.0
        for part, (ua, ub) in enumerate(((u0 + 0.5, door_u - gap), (door_u + gap, u1 - 0.5))):
            if ub - ua < 1.0:
                continue
            fx0, fx1, fz0, fz1 = rect(ua, ub, 0.3, 0.9)
            if edge < 0.45:
                T.box(f"{name}Hedge{part}", ((fx0 + fx1) / 2, 0.45, (fz0 + fz1) / 2), (fx1 - fx0, 0.9, fz1 - fz0), rgb("2c4a2a"), 9, "solid", "hedge")
            elif edge < 0.85:
                cxp, czp = (fx0 + fx1) / 2, (fz0 + fz1) / 2
                long = (fx1 - fx0, 0.08, 0.05) if axis == "x" else (0.05, 0.08, fz1 - fz0)
                for yy in (0.35, 0.75):
                    T.box(f"{name}Rail{part}{yy}", (cxp, yy, czp), long, trim, 9, "solid", "fence")
                n = max(2, int((ub - ua) / 2.0) + 1)
                for i in range(n):
                    qx, qz = P(ua + i * (ub - ua) / (n - 1), 0.6)
                    T.box(f"{name}FencePost{part}{i}", (qx, 0.5, qz), (0.12, 1.0, 0.12), trim, 9, "solid", "fence")
        # Halloween on the porch
        jx, jz = P(door_u - 1.2, v_step + 0.3)
        T.decor(rng.choice(["jack", "jack_grin", "jack_scary", "jack_wink", "jack_tall"]), (jx, 0.2, jz), ry, 0.8)
        jx, jz = P(door_u + 1.2, v_step + 0.3)
        T.decor(rng.choice(["pumpkin", "gourds", "mums", "mums_purple", "pumpkin_stack"]), (jx, 0.2, jz), ry, 0.8)
        if k % 4 == 0:
            gx, gz = P(door_u, v_step)
            T.glow((gx, 0.8, gz), rgb("ff9a3a"), 5, 0.7)
        # the front door, for trick-or-treat: where to stand, which way it faces, where the porch light hangs
        out = {"S": (0, -1), "N": (0, 1), "W": (-1, 0), "E": (1, 0)}[door]
        dx, dz = P(door_u, v_front)
        lx, lz = P(door_u + 0.75, v_front)
        floor = 0.4 if porch != "none" else 0.2
        self.homes.append({"k": k, "u": door_u, "side": side, "street": parcel["street"], "style": style,
                           "door": [round(dx + out[0] * 0.08, 2), floor, round(dz + out[1] * 0.08, 2)],
                           "ry": ry, "light": [round(lx + out[0] * 0.14, 2), round(floor + 2.05, 2), round(lz + out[1] * 0.14, 2)]})
        self.stats["houses"] += 1
        self.dress_yard(k, parcel, P, (u0, u1), depth, (uc - hw / 2, uc + hw / 2, v_front - (2.4 if porch != "none" else 0.5), v_front + hd), door_u)

    def finish_homes(self, tales=12):
        """House numbers (odd on one side of the street, even on the other), a family at every door
        and the twelve Stories of Hollow Creek spread over the streets. Uses its own random numbers
        so the town itself comes out exactly the same."""
        rng = random.Random(1032)
        families = rng.sample(FAMILIES, len(self.homes))
        out = []
        for street in sorted({h["street"] for h in self.homes}):
            on = sorted((h for h in self.homes if h["street"] == street), key=lambda h: h["u"])
            # the old streets already have 1 Founders Way, 3 Willow Lane and 14 Elm Street: start past them
            odd, even = (21, 22) if street in ("Main Street", "Elm Street", "Willow Lane", "Founders Way") else (1, 2)
            for h in on:
                if h["side"] > 0:
                    h["number"], odd = odd, odd + 2
                else:
                    h["number"], even = even, even + 2
        for i, h in enumerate(sorted(self.homes, key=lambda h: h["k"])):
            out.append({"id": f"H{i + 1:02d}", "family": families[i], "address": f"{h['number']} {h['street']}",
                        "street": h["street"], "style": h["style"], "door": h["door"], "ry": h["ry"], "light": h["light"], "tale": -1})
        # one tale per street first, then the rest, so the stories pull you all over town
        order, seen = [], set()
        for h in out:
            if h["street"] not in seen:
                seen.add(h["street"]); order.append(h)
        order += rng.sample([h for h in out if h not in order], len(out) - len(order))
        for t, h in enumerate(order[:tales]):
            h["tale"] = t
        return out


    # -- 4. yards -------------------------------------------------------------------------------
    def dress_yard(self, k, parcel, P, urange, depth, house, door_u):
        T, rng = self.T, self.rng
        cell = 2.0
        u0, u1 = urange
        cols, rows = int((u1 - u0) // cell), int((depth - 1.2) // cell)
        hu0, hu1, hv0, hv1 = house
        fixed = {}
        for i in range(cols):
            for j in range(rows):
                cu, cv = u0 + (i + 0.5) * cell, 1.2 + (j + 0.5) * cell
                if hu0 - 0.8 <= cu <= hu1 + 0.8 and hv0 - 0.8 <= cv <= hv1 + 0.8:
                    fixed[(i, j)] = "house"
                elif abs(cu - door_u) < cell * 0.75 and cv < hv0:
                    fixed[(i, j)] = "walk"
        tiles = wfc(cols, rows, fixed, rng)
        sheds = 0
        name = f"Yard{k}"
        spots = []
        for (i, j), t in sorted(tiles.items()):
            cu, cv = u0 + (i + 0.5) * cell, 1.2 + (j + 0.5) * cell
            x, z = P(cu + rng.uniform(-0.3, 0.3), cv + rng.uniform(-0.3, 0.3))
            if t == "stone":
                T.box(f"{name}Stone{i}_{j}", (x, -0.01, z), (0.8, 0.06, 0.8), rgb("8a847a"), 9, "nocollide", "road", r=(0, rng.uniform(0, 45), 0))
            elif t == "bed":
                T.decor(rng.choice(["mums", "mums_purple", "gourds"]), (x, 0, z), rng.uniform(0, 360), 0.9)
            elif t == "patch":
                T.box(f"{name}Soil{i}_{j}", (x, -0.005, z), (1.9, 0.05, 1.9), rgb("3a2a1e"), 9, "nocollide", "road")
                for q in range(2):
                    T.decor(rng.choice(["pumpkin", "pumpkin", "pumpkin_warty", "turnip"]),
                            (x + rng.uniform(-0.6, 0.6), 0, z + rng.uniform(-0.6, 0.6)), rng.uniform(0, 360), rng.uniform(0.7, 1.0))
            elif t == "tree":
                T.tree(f"{name}Tree{i}_{j}", x, z, rng.uniform(5, 7.5), rgb(rng.choice(LEAVES)) if rng.random() < 0.6 else None)
                spots.append((x, z))
            elif t == "shed" and sheds == 0 and cv > hv1 - 2:
                sheds += 1
                T.box(f"{name}Shed", (x, 1.1, z), (1.9, 2.2, 1.9), rgb(rng.choice(WALLS)), 9, "solid", "building")
                T.box(f"{name}ShedRoof", (x, 2.3, z), (2.2, 0.2, 2.2), rgb(rng.choice(ROOFS)), 9, "solid", "roof", r=(0, 0, 8))
                spots.append((x, z))
            elif t == "grave":
                T.decor(rng.choice(["tomb_round", "tomb_cross"]), (x, 0, z), rng.uniform(-15, 15), 0.9)
            elif t == "hay":
                T.decor("haybale", (x, 0, z), rng.uniform(0, 90))
                if rng.random() < 0.5:
                    T.decor("scarecrow", (x + 0.9, 0, z), rng.uniform(150, 210))
            elif t == "spook":
                T.decor(rng.choice(["skeleton", "cauldron", "crow", "cat", "spider", "ghost_hang"]), (x, 0, z), rng.uniform(0, 360))
                spots.append((x, z))
        self.stats["yards"] += 1
        parcel["spots"] = spots

    # -- 5. landmarks ---------------------------------------------------------------------------
    def landmark(self, name, kind, room_name, x0, x1, z0, z1, district):
        T = self.T
        fn = getattr(self, "lm_" + kind)
        lantern = fn(name, x0, x1, z0, z1)
        T.room(room_name, 9, x0, x1, z0, z1, -1, 12)
        self.grid.mark(x0, x1, z0, z1, NEW)
        self.features.append({"kind": kind, "name": room_name, "rect": [x0, x1, z0, z1], "district": district})
        if lantern:
            self.lanterns.append((room_name, lantern))

    def lm_maze(self, name, x0, x1, z0, z1):
        """A corn maze: rooms (3 m cells) joined by doorways, carved by a seeded depth-first walk."""
        T, rng = self.T, self.rng
        cell = 3.0
        n = int(min(x1 - x0, z1 - z0) // cell)
        n = min(n, 11) - (1 - min(n, 11) % 2)
        ox, oz = (x0 + x1) / 2 - n * cell / 2, (z0 + z1) / 2 - n * cell / 2
        open_e = [[False] * n for _ in range(n)]  # wall to the east of (i, j) is open
        open_n = [[False] * n for _ in range(n)]
        seen = [[False] * n for _ in range(n)]
        stack = [(n // 2, n // 2)]
        seen[n // 2][n // 2] = True
        while stack:
            i, j = stack[-1]
            nbrs = [(a, b) for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)) if 0 <= a < n and 0 <= b < n and not seen[a][b]]
            if not nbrs:
                stack.pop()
                continue
            a, b = rng.choice(nbrs)
            if a != i:
                open_e[min(a, i)][j] = True
            else:
                open_n[i][min(b, j)] = True
            seen[a][b] = True
            stack.append((a, b))
        corn = rgb("8a7a3a")
        hgt = 2.4
        # merge wall runs into long boxes: horizontal walls (between rows), then vertical
        for j in range(n + 1):
            run = None
            for i in range(n + 1):
                wall = i < n and (j == 0 or j == n or not open_n[i][j - 1])
                if j == 0 and i == n // 2:
                    wall = False  # the way in, from the south
                if j == n and i == n // 2 + 2 and n > 4:
                    wall = False  # the way out
                if wall and run is None:
                    run = i
                if not wall and run is not None:
                    a0, a1 = ox + run * cell, ox + i * cell
                    T.box(f"{name}H{j}_{run}", ((a0 + a1) / 2, hgt / 2, oz + j * cell), (a1 - a0 + 0.4, hgt, 0.5), corn, 9, "solid", "hedge")
                    run = None
        for i in range(n + 1):
            run = None
            for j in range(n + 1):
                wall = j < n and (i == 0 or i == n or not open_e[i - 1][j])
                if wall and run is None:
                    run = j
                if not wall and run is not None:
                    a0, a1 = oz + run * cell, oz + j * cell
                    T.box(f"{name}V{i}_{run}", (ox + i * cell, hgt / 2, (a0 + a1) / 2), (0.5, hgt, a1 - a0 + 0.4), corn, 9, "solid", "hedge")
                    run = None
        cx, cz = ox + n * cell / 2, oz + n * cell / 2
        T.decor("scarecrow", (cx, 0, cz + 0.6), 180)
        T.glow((cx, 1.2, cz), rgb("ffb347"), 6, 0.9)
        T.decor("haybale", (ox + n * cell / 2 - 2.5, 0, oz - 1.5), 0)
        T.decor("callboard", (ox + n * cell / 2 + 2.6, 0, oz - 1.4), 180)
        for q in range(6):
            T.decor("cornstalks", (ox - 0.8 + rng.uniform(-0.2, 0.2), 0, oz + q * n * cell / 5), rng.uniform(0, 360))
        self.stats["props"] += 10
        return (cx - 1.0, 0.0, cz - 0.6)

    def lm_orchard(self, name, x0, x1, z0, z1):
        T, rng = self.T, self.rng
        spacing = 6.0
        k = 0
        x = x0 + 3
        while x < x1 - 2:
            z = z0 + 3 + (k % 2) * 1.5
            while z < z1 - 2:
                T.tree(f"{name}T{k}", x + rng.uniform(-0.4, 0.4), z, rng.uniform(4.5, 5.5), rgb(rng.choice(["8a2a1e", "a83a24", "6a7a2a", "b8862a"])))
                if rng.random() < 0.25:
                    T.decor("trunk", (x + 1.4, 0, z + 0.4), rng.uniform(0, 90), 0.7)  # apple crates
                z += spacing
                k += 1
            x += spacing
        # cider stand at the front
        cx, cz = (x0 + x1) / 2, z0 - 0.5
        T.box(f"{name}Stand", (cx, 0.6, cz + 1.5), (3.0, 1.2, 1.2), rgb("6a4a2a"), 9, "solid", "furniture")
        T.box(f"{name}StandRoof", (cx, 2.4, cz + 1.5), (3.4, 0.2, 1.8), rgb("8a2a2a"), 9, "solid", "roof", r=(-10, 0, 0))
        for i, dx in enumerate((-1.3, 1.3)):
            T.box(f"{name}StandPost{i}", (cx + dx, 1.5, cz + 1.0), (0.12, 1.8, 0.12), rgb("6a4a2a"), 9, "solid", "furniture")
        T.decor("lantern", (cx, 1.2, cz + 1.5), 0, 0.8)
        T.glow((cx, 1.8, cz + 1.0), rgb("ffcf7a"), 6, 0.9)
        return (x1 - 4.5, 0.0, z1 - 4.0)

    def lm_farm(self, name, x0, x1, z0, z1):
        T, rng = self.T, self.rng
        rows = int((z1 - z0 - 4) // 2.5)
        for r in range(rows):
            z = z0 + 3 + r * 2.5
            T.box(f"{name}Row{r}", ((x0 + x1) / 2, -0.005, z), (x1 - x0 - 4, 0.05, 1.3), rgb("3a2a1e"), 9, "nocollide", "road")
            x = x0 + 3
            while x < x1 - 3:
                if rng.random() < 0.55:
                    T.decor(rng.choice(["pumpkin", "pumpkin", "pumpkin_warty", "jack_white"]), (x, 0, z + rng.uniform(-0.3, 0.3)),
                            rng.uniform(0, 360), rng.uniform(0.8, 1.3))
                x += rng.uniform(1.6, 2.6)
        T.decor("scarecrow", ((x0 + x1) / 2, 0, (z0 + z1) / 2), 180, 1.2)
        for i in range(4):
            T.decor("haybale", (x0 + 1.5, 0, z0 + 2 + i * 1.4), 90)
        T.decor("pumpkin_stack", (x1 - 2, 0, z0 + 1.2), 180)
        T.decor("crow", ((x0 + x1) / 2 + 0.3, 1.9, (z0 + z1) / 2), 0)
        T.glow(((x0 + x1) / 2, 1.5, z0 + 1), rgb("ff9a3a"), 8, 0.8)
        return (x1 - 3.0, 0.0, z1 - 2.5)

    def lm_cemetery(self, name, x0, x1, z0, z1):
        T, rng = self.T, self.rng
        iron = self.C["iron"]
        gate = (x0 + x1) / 2
        for side, (a, b, fixed, ax) in {"S": (x0, x1, z0, "x"), "N": (x0, x1, z1, "x"), "W": (z0, z1, x0, "z"), "E": (z0, z1, x1, "z")}.items():
            parts = [(a, gate - 1.4), (gate + 1.4, b)] if side == "S" else [(a, b)]
            for q, (pa, pb) in enumerate(parts):
                m = (pa + pb) / 2
                for yy in (0.15, 1.55):
                    p = (m, yy, fixed) if ax == "x" else (fixed, yy, m)
                    s = (pb - pa, 0.08, 0.08) if ax == "x" else (0.08, 0.08, pb - pa)
                    T.box(f"{name}Rail{side}{q}{yy}", p, s, iron, 9, "solid", "fence")
                n = max(2, int((pb - pa) / 1.2))
                for i in range(n + 1):
                    v = pa + i * (pb - pa) / n
                    p = (v, 0.85, fixed) if ax == "x" else (fixed, 0.85, v)
                    T.box(f"{name}Bar{side}{q}{i}", p, (0.05, 1.7, 0.05), iron, 9, "nocollide", "fence")
        for side in (-1, 1):
            T.box(f"{name}GatePost{side}", (gate + side * 1.5, 1.1, z0), (0.35, 2.2, 0.35), self.C["stone"], 9, "solid", "fence")
        T.box(f"{name}Arch", (gate, 2.35, z0), (3.4, 0.25, 0.25), iron, 9, "solid", "fence")
        k = 0
        for gz in np.arange(z0 + 3, z1 - 3, 2.6):
            for gx in np.arange(x0 + 2.5, x1 - 2, 2.2):
                if abs(gx - gate) < 1.6 or rng.random() < 0.25:
                    continue
                if rng.random() < 0.5:
                    T.box(f"{name}Stone{k}", (gx, 0.45, gz), (0.7, 0.9, 0.18), self.C["stone"], 9, "solid", "grave", r=(rng.uniform(-6, 6), 0, rng.uniform(-6, 6)))
                else:
                    T.decor(rng.choice(["tomb_round", "tomb_cross"]), (gx, 0, gz), rng.uniform(-10, 10))
                k += 1
        # the crypt at the back
        cx, cz = gate, z1 - 4.5
        T.box(f"{name}Crypt", (cx, 1.6, cz), (5.0, 3.2, 4.0), self.C["stone"], 9, "solid", "building")
        T.gable_roof(f"{name}CryptRoof", cx - 2.5, cx + 2.5, cz - 2, cz + 2, 3.2, 1.4, rgb("4a4a52"), self.C["stone"], level=9, overhang=0.3)
        T.box(f"{name}CryptDoor", (cx, 1.1, cz - 2.03), (1.4, 2.2, 0.08), rgb("2a2a2e"), 9, "solid", "door")
        T.decor("candle", (cx - 1.0, 0, cz - 2.6), 0, 1.2)
        T.decor("candle", (cx + 1.0, 0, cz - 2.6), 0, 1.2)
        T.decor("crow", (cx, 4.7, cz), 180)
        T.glow((cx, 0.8, cz - 3.0), rgb("8affb0"), 7, 0.9)  # a green wisp at the crypt door
        T.tree(f"{name}Yew", x0 + 3, z1 - 3, 8.0, None)
        T.tree(f"{name}Yew2", x1 - 3, z1 - 3, 7.0, None)
        return (cx + 1.8, 0.0, cz - 2.8)

    def lm_pond(self, name, x0, x1, z0, z1):
        T, rng = self.T, self.rng
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        rx, rz = (x1 - x0) / 2 - 5, (z1 - z0) / 2 - 5
        T.box(f"{name}Water", (cx, -0.03, cz), (rx * 2, 0.06, rz * 2), self.C["water"], 9, "nocollide", "water", "cyl")
        # a loop path around it, as 16 straight slabs
        for i in range(16):
            a0, a1 = i / 16 * math.tau, (i + 1) / 16 * math.tau
            px = cx + (rx + 2) * (math.cos(a0) + math.cos(a1)) / 2
            pz = cz + (rz + 2) * (math.sin(a0) + math.sin(a1)) / 2
            seg = math.hypot((rx + 2) * (math.cos(a1) - math.cos(a0)), (rz + 2) * (math.sin(a1) - math.sin(a0)))
            ang = -math.degrees(math.atan2(math.sin(a1) * (rz + 2) - math.sin(a0) * (rz + 2), math.cos(a1) * (rx + 2) - math.cos(a0) * (rx + 2)))
            T.box(f"{name}Path{i}", (px, -0.02, pz), (seg + 0.3, 0.08, 1.4), rgb("7a746c"), 9, "solid", "road", r=(0, ang, 0))
        # dock
        T.box(f"{name}Dock", (cx, 0.15, cz - rz + 2.5), (1.8, 0.2, 5.0), self.C["wood"], 9, "solid", "porch")
        for i, d in enumerate((-0.8, 0.8)):
            T.box(f"{name}DockPost{i}", (cx + d, 0.4, cz - rz + 4.8), (0.18, 1.0, 0.18), self.C["wood"], 9, "solid", "porch")
        # benches and lamps round the edge, and the old mill wheel
        for i, a in enumerate((0.6, 2.2, 3.6, 5.2)):
            bx, bz = cx + (rx + 3.6) * math.cos(a), cz + (rz + 3.6) * math.sin(a)
            T.decor("bench", (bx, 0, bz), math.degrees(math.atan2(cx - bx, cz - bz)))
        for i, a in enumerate((1.4, 4.4)):
            lx, lz = cx + (rx + 3.2) * math.cos(a), cz + (rz + 3.2) * math.sin(a)
            T.decor("streetlamp", (lx, 0, lz), 0)
            T.glow((lx, 3.6, lz), rgb("ffcf7a"), 11, 1.0)
        mx, mz = cx + rx + 1.0, cz
        T.box(f"{name}Mill", (mx + 3.2, 2.4, mz), (4.4, 4.8, 5.0), rgb("8a7a6a"), 9, "solid", "building")
        T.gable_roof(f"{name}MillRoof", mx + 1.0, mx + 5.4, mz - 2.5, mz + 2.5, 4.8, 2.0, rgb("3a2e2a"), rgb("8a7a6a"), level=9, overhang=0.3)
        T.box(f"{name}Wheel", (mx + 0.6, 1.6, mz), (3.6, 0.3, 3.6), self.C["wood"], 9, "solid", "decor", "cyl", r=(0, 0, 90))
        for i in range(4):
            T.box(f"{name}Paddle{i}", (mx + 0.6, 1.6, mz), (0.5, 4.0, 0.12), self.C["wood"], 9, "nocollide", "decor", r=(i * 45, 0, 0))
        T.tree(f"{name}Willow", cx - rx - 2, cz + rz - 1, 8.0, rgb("8a9a3a"))
        T.decor("luminaria", (cx - 0.6, 0.25, cz - rz + 4.6), 0)
        T.decor("luminaria", (cx + 0.6, 0.25, cz - rz + 4.6), 0)
        return (cx, 0.25, cz - rz + 4.3)

    def lm_camp(self, name, x0, x1, z0, z1):
        T, rng = self.T, self.rng
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        T.box(f"{name}Clearing", (cx, -0.01, cz), (min(x1 - x0, z1 - z0) - 2, 0.04, min(x1 - x0, z1 - z0) - 2), rgb("4a3c2a"), 9, "nocollide", "road", "cyl")
        T.box(f"{name}FirePit", (cx, 0.15, cz), (1.6, 0.3, 1.6), self.C["stone"], 9, "solid", "decor", "cyl")
        for i in range(3):
            T.box(f"{name}FireLog{i}", (cx, 0.35, cz), (0.18, 1.2, 0.18), self.C["wood"], 9, "nocollide", "decor", "cyl", r=(70, i * 60, 0))
        T.glow((cx, 0.9, cz), rgb("ff7a2a"), 10, 1.4)
        for i in range(5):  # log seats round the fire
            a = i / 5 * math.tau
            T.box(f"{name}Seat{i}", (cx + 3.2 * math.cos(a), 0.25, cz + 3.2 * math.sin(a)), (0.5, 1.6, 0.5), self.C["wood"], 9, "solid", "furniture", "cyl",
                  r=(90, -math.degrees(a), 0))
        for i, a in enumerate((0.9, 2.6, 4.3)):  # tents
            tx, tz = cx + 7 * math.cos(a), cz + 7 * math.sin(a)
            ry = -math.degrees(a) + 90
            col = rgb(["2f6a6a", "e8731c", "6a2a8a"][i])
            for s in (-1, 1):
                T.box(f"{name}Tent{i}{s}", (tx + s * 0.55 * math.cos(math.radians(ry)), 0.75, tz - s * 0.55 * math.sin(math.radians(ry))),
                      (1.6, 0.06, 2.4), col, 9, "solid", "decor", r=(0, ry, s * 55))
        T.decor("cauldron", (cx + 1.6, 0, cz - 1.2), 0, 0.8)
        T.decor("lantern", (cx - 2.0, 0, cz + 1.0), 0)
        T.decor("callboard", (cx, 0, z0 + 1.5), 180)
        return (cx + 7 * math.cos(2.6) + 1.2, 0.0, cz + 7 * math.sin(2.6))

    def lm_hayfield(self, name, x0, x1, z0, z1):
        T, rng = self.T, self.rng
        for i, x in enumerate(np.arange(x0 + 4, x1 - 3, 6.5)):
            for j, z in enumerate(np.arange(z0 + 4, z1 - 3, 7.0)):
                if rng.random() < 0.7:
                    T.decor("haybale", (x + rng.uniform(-1, 1), 0, z + rng.uniform(-1, 1)), rng.uniform(0, 180), 1.2)
        # the hayride wagon, parked for the night
        wx, wz = (x0 + x1) / 2, z0 + 4
        T.box(f"{name}Wagon", (wx, 0.9, wz), (2.4, 0.5, 4.6), self.C["wood"], 9, "solid", "furniture")
        for s in (-1, 1):
            T.box(f"{name}WagonSide{s}", (wx + s * 1.15, 1.35, wz), (0.1, 0.5, 4.6), self.C["wood"], 9, "solid", "furniture")
            for e in (-1, 1):
                T.box(f"{name}Wheel{s}{e}", (wx + s * 1.3, 0.55, wz + e * 1.5), (1.1, 0.1, 1.1), rgb("2a2a2e"), 9, "solid", "decor", "cyl", r=(0, 0, 90))
        T.decor("haybale", (wx, 1.15, wz - 0.8), 90, 0.9)
        T.decor("haybale", (wx, 1.15, wz + 1.0), 90, 0.9)
        T.decor("jack_tall", (wx + 0.5, 1.15, wz + 2.0), 180, 0.7)
        T.glow((wx, 2.0, wz), rgb("ffb347"), 7, 0.8)
        return (x1 - 4, 0.0, z1 - 4)

    def lm_park(self, name, x0, x1, z0, z1):
        T, rng = self.T, self.rng
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        T.box(f"{name}PathX", (cx, -0.02, cz), (x1 - x0 - 2, 0.08, 1.6), rgb("7a746c"), 9, "solid", "road")
        T.box(f"{name}PathZ", (cx, -0.02, cz), (1.6, 0.08, z1 - z0 - 2), rgb("7a746c"), 9, "solid", "road")
        T.box(f"{name}Fountain", (cx, 0.35, cz), (4.0, 0.7, 4.0), self.C["stone"], 9, "solid", "decor", "cyl")
        T.box(f"{name}FountainWater", (cx, 0.62, cz), (3.4, 0.05, 3.4), self.C["water"], 9, "nocollide", "water", "cyl")
        T.box(f"{name}FountainTop", (cx, 1.2, cz), (0.6, 1.0, 0.6), self.C["stone"], 9, "solid", "decor", "cyl")
        for i, (dx, dz) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
            T.tree(f"{name}Tree{i}", cx + dx * (x1 - x0) / 3.2, cz + dz * (z1 - z0) / 3.2, 7.0, rgb(rng.choice(LEAVES)))
            T.decor("bench", (cx + dx * 3.6, 0, cz + dz * 1.6), 0 if dz < 0 else 180)
        T.decor("streetlamp", (cx + 2.5, 0, cz + 3.0), 0)
        T.glow((cx + 2.5, 3.6, cz + 3.0), rgb("ffcf7a"), 11, 1.0)
        T.decor("pumpkin_stack", (cx - 2.6, 0, cz - 2.6), 30)
        return (cx + (x1 - x0) / 3.2 + 1.0, 0.0, cz - (z1 - z0) / 3.2)

    def place_landmarks(self, plan, district_of):
        """plan: [(kind, room name)], placed in the biggest free rectangles, largest first."""
        for kind, room in plan:
            r = self.grid.largest_free_rect(min_side=20)
            if r is None:
                print(f"  worldgen: no room left for {room}")
                break
            x0, x1, z0, z1 = r
            # keep landmarks compact: at most 38 m a side, centred in the space
            mx = min(38, x1 - x0) / 2
            mz = min(38, z1 - z0) / 2
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            rect = (round(cx - mx + 1), round(cx + mx - 1), round(cz - mz + 1), round(cz + mz - 1))
            self.landmark(room.replace(" ", "").replace("'", ""), kind, room, *rect, district_of(cx, cz))

    # -- 7. lost lanterns -----------------------------------------------------------------------
    def hide_lanterns(self, extra, total=24):
        """One in every landmark, the fixed ones from make_town, then the rest in back yards."""
        out = []
        for where, p in self.lanterns:
            out.append((where, p))
        out += extra
        yards = [p for p in self.parcels if p.get("spots")]
        self.rng.shuffle(yards)
        for p in yards:
            if len(out) >= total:
                break
            x, z = self.rng.choice(p["spots"])
            out.append((f"a back yard on {p['street']}", (round(x + 1.4, 2), 0.0, round(z + 0.8, 2))))
        return [{"id": f"L{i + 1:02d}", "where": w, "p": [round(v, 2) for v in self.clear_spot(p)]} for i, (w, p) in enumerate(out[:total])]

    def clear_spot(self, p, pad=0.6):
        """p, or the nearest point around it (spiralling out to 3 m) that isn't inside a wall, a stone or a tent."""
        x, y, z = p
        solid = [b for b in self.T.L["boxes"] if b["m"] == "solid" and b["g"] not in ("ground", "road", "water", "floor", "porch")
                 and b["p"][1] - b["s"][1] / 2 < 1.5 and abs(b["p"][0] - x) < 8 and abs(b["p"][2] - z) < 8]

        def clear(px, pz):
            for b in solid:
                hx, hz = rotated_half_extents(b["s"], b["r"])
                if abs(px - b["p"][0]) < hx + pad and abs(pz - b["p"][2]) < hz + pad:
                    return False
            return True
        for r in np.arange(0.0, 3.01, 0.25):
            for k in range(max(1, int(r * 8))):
                a = k / max(1, int(r * 8)) * math.tau
                if clear(x + r * math.cos(a), z + r * math.sin(a)):
                    return (x + r * math.cos(a), y, z + r * math.sin(a))
        return p
