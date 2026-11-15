#!/usr/bin/env python3
"""
Round 48: hills and level changes for Hollow Creek.

The town used to sit on one flat sheet. This pass lifts it onto three terraces that climb north from
Elm Street and drop to the creek:

  level 0      Elm Street, Pine Street and everything south of them
  level 2.4 m  from just north of Pine Street up to Willow Lane and Chapel Lane
  level 4.8 m  the high town round Orchard Road and Willow Heights
  a grass bank falls from the high town to the creek, and Main Street crosses it on a raised bridge

Main Street and Ash Street climb between the terraces on ramps cut into the hill, so they run as sunken
streets with stone walls on both sides; near the creek Main Street runs out on an embankment to the
bridge. Every building, yard and lot sits at the height of the street it faces, so doors, paths and
driveways meet the sidewalk flush, and a stone retaining wall rises wherever two levels meet. Flights of
steps climb from the sunken streets to the terraces, and iron railings guard the high edges.

It runs on the saved layout (after dressing has added its plinths and props) and lifts every box and every
position in the JSON. It also writes a "terrain" block so the game can ask for the ground height
anywhere (TownLayout.GroundY).

    terrain.apply(path)      # called from make_town.py after T.save
"""
import json
import math
import re

import numpy as np

H1, H2 = 2.4, 4.8          # the two terraces above Elm Street
BRIDGE = 2.2               # the bridge deck's lift over the creek
X0, Z0, NX, NZ = -171, -12, 302, 228   # 1 m cells over the town
TOWN_X = (-170, 130)       # the town's own ground; past it the world ground stays at 0
RISE, TREAD = 0.16, 0.32   # stair steps: under the player's 0.3 m step limit
STONE, CAP, IRON = [0.42, 0.4, 0.37], [0.56, 0.54, 0.5], [0.11, 0.1, 0.12]

# Ramps, first match wins: (name, x0, x1, z0, z1, axis, h0, h1). h0 is at the low end of the axis.
RAMPS = [
    ("Main Street rise", -6.2, 6.2, 57, 79, "z", 0.0, H1),
    ("Ash Street rise", 34.2, 45.8, 57, 81, "z", 0.0, H1),
    ("Main Street hill", -6.2, 6.2, 119, 141, "z", H1, H2),
    ("Main Street down to the bridge", -6.2, 6.2, 165, 178, "z", H2, BRIDGE),
    ("Hollow Creek Bridge", -6.2, 6.2, 178, 192, "z", BRIDGE, BRIDGE),
    ("Main Street off the bridge", -6.2, 6.2, 192, 206, "z", BRIDGE, 0.0),
    ("West edge, middle", -170, -158, 57, 119, "x", 0.0, H1),
    ("West edge, high", -170, -158, 119, 171, "x", 0.0, H2),
    ("East edge, middle", 118, 130, 57, 119, "x", H1, 0.0),
    ("East edge, high", 118, 130, 119, 171, "x", H2, 0.0),
    ("Creek bank", -170, 130, 171, 179, "z", H2, 0.0),
]
BRIDGE_RAMP = 4            # its cells keep the old ground under the deck: the creek runs there


def base(x, z):
    if not (TOWN_X[0] <= x < TOWN_X[1]):
        return 0.0
    if z < 57:
        return 0.0
    if z < 119:
        return H1
    if z < 171:
        return H2
    return 0.0


def ramp_at(x, z):
    for i, (_, x0, x1, z0, z1, *_r) in enumerate(RAMPS):
        if x0 <= x < x1 and z0 <= z < z1:
            return i
    return -1


def ramp_h(i, x, z):
    _, x0, x1, z0, z1, axis, h0, h1 = RAMPS[i]
    t = (z - z0) / (z1 - z0) if axis == "z" else (x - x0) / (x1 - x0)
    return h0 + (h1 - h0) * min(1.0, max(0.0, t))


def ramp_slope(i):
    """dh/dx, dh/dz"""
    _, x0, x1, z0, z1, axis, h0, h1 = RAMPS[i]
    return ((h1 - h0) / (x1 - x0), 0.0) if axis == "x" else (0.0, (h1 - h0) / (z1 - z0))


def natural(x, z):
    """the hill without any building's claim: ramps, then terraces"""
    i = ramp_at(x, z)
    return ramp_h(i, x, z) if i >= 0 else base(x, z)


# ---------------------------------------------------------------------------
def _euler(r):
    rx, ry, rz = map(math.radians, r)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


def aabb(b):
    p, s = np.array(b["p"], float), np.array(b["s"], float)
    r = b.get("r", [0, 0, 0])
    if b["t"] == "sphere":
        s = np.array([s[0], s[1], s[2]])
    elif b["t"] in ("cyl", "rcyl", "capsule"):
        s = np.array([s[0], s[1] * 2 if b["t"] != "rcyl" else s[1] * 2, s[2]]) if b["t"] == "capsule" else np.array([s[0], s[1] * 2, s[2]])
    if any(abs(v) > 1e-6 for v in r):
        half = np.abs(_euler(r)) @ (s / 2)
    else:
        half = s / 2
    return p - half, p + half


class Cells:
    def __init__(self):
        self.h = np.zeros((NX, NZ))
        self.ramp = np.full((NX, NZ), -1, int)
        self.claim = np.full((NX, NZ), -1, int)
        self.road = np.zeros((NX, NZ), bool)
        self.notch = np.zeros((NX, NZ), bool)
        for i in range(NX):
            x = X0 + i + 0.5
            for j in range(NZ):
                z = Z0 + j + 0.5
                k = ramp_at(x, z)
                self.ramp[i, j] = k
                self.h[i, j] = ramp_h(k, x, z) if k >= 0 else base(x, z)

    @staticmethod
    def idx(x, z):
        return int(math.floor(x - X0)), int(math.floor(z - Z0))

    def inside(self, i, j):
        return 0 <= i < NX and 0 <= j < NZ

    def rect(self, x0, z0, x1, z1):
        i0, j0 = self.idx(x0 + 0.01, z0 + 0.01)
        i1, j1 = self.idx(x1 - 0.01, z1 - 0.01)
        return max(0, i0), max(0, j0), min(NX - 1, i1), min(NZ - 1, j1)

    def at(self, x, z):
        """height of the ground surface at a point (exact on ramps)"""
        i, j = self.idx(x, z)
        if not self.inside(i, j):
            return 0.0
        k = self.ramp[i, j]
        if k >= 0 and self.claim[i, j] < 0:
            return ramp_h(k, x, z)
        return float(self.h[i, j])

    def claim_rect(self, gid, x0, z0, x1, z1, height):
        i0, j0, i1, j1 = self.rect(x0, z0, x1, z1)
        if i1 < i0 or j1 < j0:
            return
        sub = self.ramp[i0:i1 + 1, j0:j1 + 1]
        free = sub < 0
        self.h[i0:i1 + 1, j0:j1 + 1][free] = height
        self.claim[i0:i1 + 1, j0:j1 + 1][free] = gid


# ---------------------------------------------------------------------------
KEY = [
    (re.compile(r"^(?:Home|Yard|Garden)(\d+)"), "Home{}"),
    (re.compile(r"^House(\d+)"), "House{}"),
    (re.compile(r"^Haunt([A-Z][a-z]+)"), "Haunt{}"),
    (re.compile(r"^(?:Church|Steeple|Cross|Headstone)"), "Church"),
    (re.compile(r"^FireStation"), "FireStation"),
    (re.compile(r"^Library"), "Library"),
    (re.compile(r"^FoundersPark(?!Tree)"), "FoundersPark"),
]
LOOSE = re.compile(r"(Trunk|Canopy|Leaf|Leaves|Wire|^Street|^Wood|^Grove|Tree|Lamp|Post\d|Bench|Sign)")


def key_of(name):
    for rx, fmt in KEY:
        m = rx.match(name)
        if m:
            return fmt.format(*m.groups())
    return None


def is_flat(b, lo, hi):
    r = b.get("r", [0, 0, 0])
    return b["t"] == "box" and hi[1] <= 0.36 and lo[1] >= -0.45 and abs(r[0]) < 1 and abs(r[2]) < 1


class _UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def join(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[b] = a


def _box(name, p, s, c, m="solid", g="terrain", r=(0, 0, 0)):
    return {"n": name, "t": "box", "p": [round(v, 3) for v in p], "s": [round(v, 3) for v in s],
            "r": [round(v, 3) for v in r], "c": c, "m": m, "l": 9, "g": g}


def _in_grid(x, z):
    return X0 <= x < X0 + NX and Z0 <= z < Z0 + NZ


# ---------------------------------------------------------------------------
def apply(path):
    with open(path) as f:
        T = json.load(f)
    boxes = T["boxes"]
    C = Cells()
    report = {}

    # Road cells: the streets and sidewalks, so railings and stairs know which side is public.
    roads = tuple(T.get("roads", []))
    for b in boxes:
        if b["n"].startswith(roads) or b["n"].startswith("Drive_"):
            lo, hi = aabb(b)
            i0, j0, i1, j1 = C.rect(lo[0], lo[2], hi[0], hi[2])
            C.road[i0:i1 + 1, j0:j1 + 1] = True

    # ---- groups: buildings with their yards, gardens and props move as one -------------------------------
    ext = [aabb(b) for b in boxes]
    cand = [k for k, b in enumerate(boxes)
            if _in_grid(b["p"][0], b["p"][2]) and not b["n"].startswith(("Ground_", "Creek"))
            and b.get("g") != "terrain"]
    uf = _UF(len(boxes))
    first = {}
    for k in cand:
        key = key_of(boxes[k]["n"])
        if key:
            if key in first:
                uf.join(first[key], k)
            else:
                first[key] = k
    # touching standing pieces join too (a porch on a house, a fence round its yard)
    standing = [k for k in cand if not is_flat(boxes[k], *ext[k]) and not LOOSE.search(boxes[k]["n"])
                and ext[k][0][1] < 0.6]
    grid = {}
    for k in standing:
        lo, hi = ext[k]
        for gx in range(int(lo[0] // 8), int(hi[0] // 8) + 1):
            for gz in range(int(lo[2] // 8), int(hi[2] // 8) + 1):
                grid.setdefault((gx, gz), []).append(k)
    for cell in grid.values():
        for a in range(len(cell)):
            la, ha = ext[cell[a]]
            for b2 in range(a + 1, len(cell)):
                lb, hb = ext[cell[b2]]
                if (la[0] < hb[0] - 0.02 and lb[0] < ha[0] - 0.02 and la[2] < hb[2] - 0.02 and lb[2] < ha[2] - 0.02):
                    uf.join(cell[a], cell[b2])
    members = {}
    for k in cand:
        if key_of(boxes[k]["n"]) or k in set(standing):
            members.setdefault(uf.find(k), []).append(k)
    groups = []
    for root, ks in members.items():
        if len(ks) < 3:
            continue
        lo = np.min([ext[k][0] for k in ks], axis=0)
        hi = np.max([ext[k][1] for k in ks], axis=0)
        names = [boxes[k]["n"] for k in ks]
        groups.append({"ks": ks, "lo": lo, "hi": hi, "names": names, "key": key_of(names[0]) or names[0]})

    # ---- each group's height: the street in front of its door ---------------------------------------
    doors = []   # (x, z) of every door we know
    for h in T.get("homes", []):
        doors.append(h["door"])
    for h in T.get("haunts", []):
        doors.append(h["door"])
    for b in boxes:
        if re.search(r"(House\d+|Church|Home\d+)Door$", b["n"]):
            doors.append(b["p"])

    def front_height(g, door):
        cx, cz = (g["lo"][0] + g["hi"][0]) / 2, (g["lo"][2] + g["hi"][2]) / 2
        dx, dz = door[0] - cx, door[2] - cz
        w, d = g["hi"][0] - g["lo"][0], g["hi"][2] - g["lo"][2]
        if abs(dx) / max(w, 1) > abs(dz) / max(d, 1):
            ox, oz = (1 if dx > 0 else -1), 0
        else:
            ox, oz = 0, (1 if dz > 0 else -1)
        x, z = door[0], door[2]
        for _ in range(60):   # out of the group's yard, then one more metre
            if not (g["lo"][0] - 0.05 <= x <= g["hi"][0] + 0.05 and g["lo"][2] - 0.05 <= z <= g["hi"][2] + 0.05):
                break
            x, z = x + ox * 0.5, z + oz * 0.5
        return natural(x + ox, z + oz), (x + ox, z + oz)

    rx, rz = np.nonzero(C.road)
    road_pts = np.stack([X0 + rx + 0.5, Z0 + rz + 0.5], axis=1)

    def street_height(g, door):
        """the nearest street or driveway to the door, outside the group's own yard"""
        lo, hi = g["lo"], g["hi"]
        outside = ~((road_pts[:, 0] > lo[0]) & (road_pts[:, 0] < hi[0]) & (road_pts[:, 1] > lo[2]) & (road_pts[:, 1] < hi[2]))
        pts = road_pts[outside]
        d2 = (pts[:, 0] - door[0]) ** 2 + (pts[:, 1] - door[2]) ** 2
        q = int(np.argmin(d2))
        if d2[q] > 30 ** 2:
            return front_height(g, door)
        x, z = float(pts[q, 0]), float(pts[q, 1])
        return natural(x, z), (x, z)

    for g in groups:
        ds = [d for d in doors if g["lo"][0] - 1 <= d[0] <= g["hi"][0] + 1 and g["lo"][2] - 1 <= d[2] <= g["hi"][2] + 1]
        if ds:
            g["h"], g["front"] = street_height(g, ds[0])
            k = ramp_at(*g["front"])
            if k >= 0 and k != BRIDGE_RAMP:
                # a building beside a sloping street keeps to its terrace; steps climb to its door
                cx, cz = (g["lo"][0] + g["hi"][0]) / 2, (g["lo"][2] + g["hi"][2]) / 2
                g["h"] = base(cx, cz)
                g["stair"] = (k, ds[0])
        else:
            cx, cz = (g["lo"][0] + g["hi"][0]) / 2, (g["lo"][2] + g["hi"][2]) / 2
            g["h"], g["front"] = natural(cx, cz), (cx, cz)
        g["h"] = round(g["h"], 3)

    # lots: the house is built at its offset, so lift the offset to the street at its arrival point
    lots = []
    for lot in T.get("lots", []):
        a = lot["arrival"]
        h = round(natural(a[0], a[2]), 3)
        lots.append((lot, h))

    # claims, biggest first so a small building inside a park keeps its own
    order = sorted(range(len(groups)), key=lambda i: -(groups[i]["hi"][0] - groups[i]["lo"][0]) * (groups[i]["hi"][2] - groups[i]["lo"][2]))
    gid = 0
    for lot, h in lots:
        (x0, z0), (x1, z1) = lot["lot"]["min"], lot["lot"]["max"]
        C.claim_rect(10000 + gid, x0, z0, x1, z1, h)
        gid += 1
    for i in order:
        g = groups[i]
        lo, hi = g["lo"], g["hi"]
        C.claim_rect(i, lo[0] - 0.2, lo[2] - 0.2, hi[0] + 0.2, hi[2] + 0.2, g["h"])

    # ---- stairs: notches cut into a terrace beside a sunken street ---------------------------------
    stairs = plan_stairs(C, boxes, ext, cand, [g["stair"] for g in groups if "stair" in g])

    # ---- lift everything ---------------------------------------------------------------------------
    in_group = {}
    for i, g in enumerate(groups):
        for k in g["ks"]:
            in_group[k] = i
    out, lifted, split = [], 0, 0
    for k, b in enumerate(boxes):
        x, z = b["p"][0], b["p"][2]
        n = b["n"]
        if n.startswith("Ground_") and _in_grid(x, z):
            continue           # rebuilt below
        if not _in_grid(x, z) or n.startswith("Creek"):
            out.append(b)
            continue
        if k in in_group:
            dy = groups[in_group[k]]["h"]
            if dy:
                b["p"][1] = round(b["p"][1] + dy, 3)
                lifted += 1
            out.append(b)
            continue
        lo, hi = ext[k]
        if is_flat(b, lo, hi):
            pieces = drape(C, b, lo, hi)
            split += len(pieces) - 1
            lifted += 1
            out.extend(pieces)
            continue
        dy = C.at(x, z)
        if dy:
            b["p"][1] = round(b["p"][1] + dy, 3)
            lifted += 1
        out.append(b)

    # ---- new ground, walls, railings, stairs, the bridge's stone feet --------------------------------
    grass = next((b["c"] for b in boxes if b["n"].startswith("Ground_")), [0.153, 0.224, 0.122])
    ground = build_ground(C, grass)
    walls, rails = build_walls(C)
    steps = build_stairs(C, stairs)
    bridge = build_bridge()
    out.extend(ground + walls + rails + steps + bridge)
    T["boxes"] = out

    # ---- every position in the JSON ----------------------------------------------------------------
    lift_points(T, C, lots)

    T["terrain"] = encode(C)
    report.update({"lifted": lifted, "split": split, "groups": len(groups), "ground": len(ground),
                   "walls": len(walls), "railings": len(rails), "stairs": len(stairs), "steps": len(steps),
                   "bridge": len(bridge)})
    with open(path, "w") as f:
        json.dump(T, f, separators=(",", ":"))
    return report, groups, C


# ---------------------------------------------------------------------------
def drape(C, b, lo, hi):
    """lay a flat piece (road, sidewalk, path) on the ground, splitting it where the ground changes"""
    r = b.get("r", [0, 0, 0])
    ry = r[1] % 180
    axis_aligned = min(ry, 180 - ry) < 1 or abs(ry - 90) < 1
    xs = np.arange(math.floor(lo[0]), math.ceil(hi[0])) + 0.5
    zs = np.arange(math.floor(lo[2]), math.ceil(hi[2])) + 0.5
    xs = xs[(xs > lo[0] - 0.5) & (xs < hi[0] + 0.5)] if len(xs) else np.array([b["p"][0]])
    zs = zs[(zs > lo[2] - 0.5) & (zs < hi[2] + 0.5)] if len(zs) else np.array([b["p"][2]])
    hs = [C.at(min(max(x, lo[0]), hi[0]), min(max(z, lo[2]), hi[2])) for x in xs for z in zs]
    if max(hs) - min(hs) < 0.02 or not axis_aligned:
        dy = C.at(b["p"][0], b["p"][2])
        b["p"][1] = round(b["p"][1] + dy, 3)
        i, j = C.idx(b["p"][0], b["p"][2])
        k = C.ramp[i, j] if C.inside(i, j) else -1
        if k >= 0 and C.claim[i, j] < 0 and axis_aligned:
            sx, sz = ramp_slope(k)
            b["r"] = [round(-math.degrees(math.atan(sz)), 3), 0, round(math.degrees(math.atan(sx)), 3)]
            if abs(ry - 90) < 1:
                b["s"] = [b["s"][2], b["s"][1], b["s"][0]]
        return [b]
    # split along the longer side into 1 m slices, then merge slices that lie on one plane
    s = list(b["s"])
    if abs(ry - 90) < 1:
        s = [s[2], s[1], s[0]]
    along_x = (hi[0] - lo[0]) >= (hi[2] - lo[2])
    a0, a1 = (lo[0], hi[0]) if along_x else (lo[2], hi[2])
    n = max(1, int(math.ceil(a1 - a0 - 1e-6)))
    cuts = [a0 + (a1 - a0) * t / n for t in range(n + 1)]
    sl = []
    for t in range(n):
        m = (cuts[t] + cuts[t + 1]) / 2
        x, z = (m, b["p"][2]) if along_x else (b["p"][0], m)
        i, j = C.idx(x, z)
        k = C.ramp[i, j] if C.inside(i, j) and C.claim[i, j] < 0 else -1
        sl.append([cuts[t], cuts[t + 1], k, C.at(x, z)])
    runs = []
    for a, bb, k, h in sl:
        if runs:
            ra = runs[-1]
            if (k < 0 and ra[2] < 0 and abs(ra[3] - h) < 0.01) or (k >= 0 and ra[2] == k):
                ra[1] = bb
                continue
        runs.append([a, bb, k, h])
    out = []
    for q, (a, bb, k, h) in enumerate(runs):
        c = dict(b)
        m = (a + bb) / 2
        L = bb - a
        x, z = (m, b["p"][2]) if along_x else (b["p"][0], m)
        if along_x:
            c["p"] = [m, b["p"][1], b["p"][2]]
            c["s"] = [L, s[1], s[2]]
        else:
            c["p"] = [b["p"][0], b["p"][1], m]
            c["s"] = [s[0], s[1], L]
        rx = rz = 0.0
        if k >= 0:
            sx, sz = ramp_slope(k)
            h = ramp_h(k, x, z)
            rx, rz = -math.degrees(math.atan(sz)), math.degrees(math.atan(sx))
            if (along_x and sx) or (not along_x and sz):     # tilted along its length: stretch to the slope
                L2 = L * math.sqrt(1 + (sx if along_x else sz) ** 2)
                c["s"] = [L2, s[1], s[2]] if along_x else [s[0], s[1], L2]
        c["p"] = [round(c["p"][0], 3), round(c["p"][1] + h, 3), round(c["p"][2], 3)]
        c["s"] = [round(v, 3) for v in c["s"]]
        c["r"] = [round(rx, 3), 0, round(rz, 3)]
        if len(runs) > 1:
            c["n"] = f"{b['n']}~{q}"
        out.append(c)
    return out


# ---------------------------------------------------------------------------
def _rects(mask):
    """greedy rectangles over a boolean mask -> (i0, j0, i1, j1) inclusive"""
    mask = mask.copy()
    out = []
    nx, nz = mask.shape
    for i in range(nx):
        j = 0
        while j < nz:
            if not mask[i, j]:
                j += 1
                continue
            j1 = j
            while j1 + 1 < nz and mask[i, j1 + 1]:
                j1 += 1
            i1 = i
            while i1 + 1 < nx and mask[i1 + 1, j:j1 + 1].all():
                i1 += 1
            mask[i:i1 + 1, j:j1 + 1] = False
            out.append((i, j, i1, j1))
            j = j1 + 1
    return out


def build_ground(C, grass):
    """thick solid blocks for every flat level, tilted slabs over the ramps; the old tiles are gone"""
    out = []
    bottom = -0.52
    flat = (C.ramp < 0) | (C.claim >= 0)
    hq = np.round(C.h, 2)
    levels = sorted(set(hq[flat].tolist()))
    for lv in levels:
        for i0, j0, i1, j1 in _rects(flat & (hq == lv)):
            x0, z0, x1, z1 = X0 + i0, Z0 + j0, X0 + i1 + 1, Z0 + j1 + 1
            top = lv - 0.02
            out.append(_box(f"Ground_{len(out)}", ((x0 + x1) / 2, (top + bottom) / 2, (z0 + z1) / 2),
                            (x1 - x0, top - bottom, z1 - z0), grass, g="ground"))
    # ramps: one tilted slab per ramp over its own cells, plus stepped fill under it
    for k, (name, rx0, rx1, rz0, rz1, axis, h0, h1) in enumerate(RAMPS):
        own = (C.ramp == k) & (C.claim < 0)
        if not own.any():
            continue
        for i0, j0, i1, j1 in _rects(own):
            x0, z0, x1, z1 = X0 + i0, Z0 + j0, X0 + i1 + 1, Z0 + j1 + 1
            if k == BRIDGE_RAMP:   # the creek and its banks keep their ground under the deck
                out.append(_box(f"Ground_{len(out)}", ((x0 + x1) / 2, (-0.02 + bottom) / 2, (z0 + z1) / 2),
                                (x1 - x0, -0.02 - bottom, z1 - z0), grass, g="ground"))
                continue
            sx, sz = ramp_slope(k)
            ha = ramp_h(k, x0, z0)
            hb = ramp_h(k, x1, z1)
            th = 0.6
            if axis == "z":
                L = math.hypot(z1 - z0, hb - ha)
                ang = math.atan2(hb - ha, z1 - z0)
                cy = (ha + hb) / 2 - 0.02 - th / 2 * math.cos(ang)
                out.append(_box(f"Ground_{len(out)}", ((x0 + x1) / 2, cy, (z0 + z1) / 2), (x1 - x0, th, L), grass,
                                g="ground", r=(-math.degrees(ang), 0, 0)))
            else:
                L = math.hypot(x1 - x0, hb - ha)
                ang = math.atan2(hb - ha, x1 - x0)
                cy = (ha + hb) / 2 - 0.02 - th / 2 * math.cos(ang)
                out.append(_box(f"Ground_{len(out)}", ((x0 + x1) / 2, cy, (z0 + z1) / 2), (L, th, z1 - z0), grass,
                                g="ground", r=(0, 0, math.degrees(ang))))
            # fill: 2 m steps that stay just under the slab
            span = (z0, z1) if axis == "z" else (x0, x1)
            a = span[0]
            while a < span[1] - 1e-6:
                bnd = min(span[1], a + 2)
                lo_h = min(ramp_h(k, a, a) if axis == "x" else ramp_h(k, x0, a),
                           ramp_h(k, bnd, bnd) if axis == "x" else ramp_h(k, x0, bnd)) - 0.45
                if lo_h > bottom + 0.05:
                    if axis == "z":
                        out.append(_box(f"Ground_{len(out)}", ((x0 + x1) / 2, (lo_h + bottom) / 2, (a + bnd) / 2),
                                        (x1 - x0, lo_h - bottom, bnd - a), grass, g="ground"))
                    else:
                        out.append(_box(f"Ground_{len(out)}", ((a + bnd) / 2, (lo_h + bottom) / 2, (z0 + z1) / 2),
                                        (bnd - a, lo_h - bottom, z1 - z0), grass, g="ground"))
                a = bnd
    return out


def _edge_h(C, i, j, x0, z0, x1, z1):
    """the surface height of cell (i, j) along one of its edges: (min, max)"""
    k = C.ramp[i, j]
    if k >= 0 and C.claim[i, j] < 0:
        a, b = ramp_h(k, x0, z0), ramp_h(k, x1, z1)
        return min(a, b), max(a, b)
    return float(C.h[i, j]), float(C.h[i, j])


def build_walls(C):
    """a stone face on the high side wherever two neighbouring cells differ, railings on public drops"""
    segs = []   # (axis, line, a0, a1, lo, hi, high_side, public)
    for i in range(NX):
        for j in range(NZ):
            for di, dj in ((1, 0), (0, 1)):
                i2, j2 = i + di, j + dj
                if not C.inside(i2, j2):
                    continue
                ka, kb = C.ramp[i, j], C.ramp[i2, j2]
                if ka == kb and ka >= 0 and C.claim[i, j] < 0 and C.claim[i2, j2] < 0:
                    continue
                if BRIDGE_RAMP in (ka, kb):
                    continue
                if di:   # edge at x = X0 + i + 1, from z0 to z1
                    x = X0 + i + 1
                    e = (x, Z0 + j, x, Z0 + j + 1)
                else:
                    z = Z0 + j + 1
                    e = (X0 + i, z, X0 + i + 1, z)
                la, ha = _edge_h(C, i, j, *e)
                lb, hb = _edge_h(C, i2, j2, *e)
                if max(ha, hb) - min(la, lb) < 0.15 or abs((la + ha) - (lb + hb)) / 2 < 0.15:
                    continue
                high_b = (lb + hb) > (la + ha)
                lo, hi = (min(la, ha), max(lb, hb)) if high_b else (min(lb, hb), max(la, ha))
                hi_cell, lo_cell = ((i2, j2), (i, j)) if high_b else ((i, j), (i2, j2))
                public = (C.road[lo_cell] or C.ramp[lo_cell] >= 0 or C.road[hi_cell] or C.ramp[hi_cell] >= 0) \
                    and C.claim[hi_cell] < 0 and not C.notch[hi_cell]
                if di:
                    segs.append(("x", e[0], e[1], e[3], lo, hi, 1 if high_b else -1, public))
                else:
                    segs.append(("z", e[1], e[0], e[2], lo, hi, 1 if high_b else -1, public))
    # merge runs along each line with the same heights and side
    segs.sort(key=lambda s: (s[0], s[1], s[6], s[2]))
    merged = []
    for s in segs:
        if merged:
            m = merged[-1]
            if m[0] == s[0] and m[1] == s[1] and m[6] == s[6] and abs(m[3] - s[2]) < 1e-6 \
                    and abs(m[4] - s[4]) < 0.03 and abs(m[5] - s[5]) < 0.03 and m[7] == s[7]:
                m[3] = s[3]
                continue
        merged.append(list(s))
    walls, rails = [], []
    th = 0.3
    for axis, line, a0, a1, lo, hi, side, public in merged:
        y0, y1 = lo - 0.35, hi + 0.12
        L = a1 - a0
        off = line + side * th / 2   # inside the high cell
        if axis == "x":
            p, s = (off, (y0 + y1) / 2, (a0 + a1) / 2), (th, y1 - y0, L)
            cp, cs = (off, y1 + 0.04, (a0 + a1) / 2), (th + 0.12, 0.08, L)
        else:
            p, s = ((a0 + a1) / 2, (y0 + y1) / 2, off), (L, y1 - y0, th)
            cp, cs = ((a0 + a1) / 2, y1 + 0.04, off), (L, 0.08, th + 0.12)
        walls.append(_box(f"TerraceWall{len(walls)}", p, s, STONE, g="wall"))
        walls.append(_box(f"TerraceWallCap{len(walls)}", cp, cs, CAP, g="wall"))
        if public and hi - lo >= 0.9:
            rails.extend(_railing(axis, line + side * 0.2, a0, a1, hi + 0.16, len(rails)))
    return walls, rails


def _railing(axis, line, a0, a1, y, n):
    out = []
    L = a1 - a0
    k = max(1, int(round(L / 2)))
    for t in range(k + 1):
        a = a0 + L * t / k
        p = (line, y + 0.5, a) if axis == "x" else (a, y + 0.5, line)
        out.append(_box(f"TerraceRailPost{n + len(out)}", p, (0.07, 1.0, 0.07), IRON, g="rail"))
    for hy in (0.95, 0.5):
        p = (line, y + hy, (a0 + a1) / 2) if axis == "x" else ((a0 + a1) / 2, y + hy, line)
        s = (0.05, 0.05, L) if axis == "x" else (L, 0.05, 0.05)
        out.append(_box(f"TerraceRail{n + len(out)}", p, s, IRON, g="rail"))
    return out


# ---------------------------------------------------------------------------
def plan_stairs(C, boxes, ext, cand, doors):
    """flights of steps from a sunken street's sidewalk up to the terrace beside it: one to every door that
    looks onto a sloping street, and one halfway up each side of every rise that has none"""
    taken = []
    for k in cand:
        lo, hi = ext[k]
        if hi[1] > 0.2 and not boxes[k]["n"].startswith("Ground_"):
            taken.append((lo[0], lo[2], hi[0], hi[2]))

    def free(x0, z0, x1, z1):
        return not any(a < x1 and x0 < c and b < z1 and z0 < d for a, b, c, d in taken)

    want = []
    for k, door in doors:
        _, rx0, rx1, rz0, rz1, *_ = RAMPS[k]
        side = 1 if door[0] > (rx0 + rx1) / 2 else -1
        want.append((k, side, min(max(door[2], rz0 + 1.5), rz1 - 1.5), True))
    for k, (name, rx0, rx1, rz0, rz1, axis, h0, h1) in enumerate(RAMPS):
        if axis != "z" or h0 == h1 or k == BRIDGE_RAMP or rx1 - rx0 > 20:
            continue
        for side in (-1, 1):
            if not any(w[0] == k and w[1] == side for w in want):
                want.append((k, side, (rz0 + rz1) / 2, False))
    plans = []
    w = 1.8
    for k, side, zm, exact in want:
        _, rx0, rx1, rz0, rz1, *_ = RAMPS[k]
        edge = rx1 if side > 0 else rx0
        reach = 4 if exact else 10
        tries = [0] + [d * sg for d in range(1, reach + 1) for sg in (1, -1)]
        for dz in tries:
            z0, z1 = zm + dz - w / 2, zm + dz + w / 2
            if z0 < rz0 + 0.5 or z1 > rz1 - 0.5:
                continue
            low = ramp_h(k, edge, (z0 + z1) / 2)
            i, j = C.idx(edge + side * 0.5, (z0 + z1) / 2)
            if not C.inside(i, j) or C.notch[i, j]:
                continue
            # the terrace the steps climb to: the first cell past the notch
            n = 1
            high = None
            for _ in range(3):
                run = n * TREAD
                far = edge + side * run
                fi, fj = C.idx(far + side * 1.2, (z0 + z1) / 2)
                if not C.inside(fi, fj):
                    break
                high = float(C.h[fi, fj])
                n = max(1, int(math.ceil((high - low) / RISE)))
            if high is None or high - low < 0.45:
                continue
            run = n * TREAD
            x0, x1 = (edge, edge + run) if side > 0 else (edge - run, edge)
            ni0, nj0, ni1, nj1 = C.rect(min(x0, x1), z0, max(x0, x1), z1)
            ni0, ni1 = (ni0, ni1) if side > 0 else (ni0, ni1)
            box = C.claim[ni0:ni1 + 1, nj0:nj1 + 1]
            if (box >= 0).any() or C.notch[ni0:ni1 + 1, nj0:nj1 + 1].any() or (C.ramp[ni0:ni1 + 1, nj0:nj1 + 1] >= 0).any():
                continue
            if not free(X0 + ni0, Z0 + nj0 - 0.2, X0 + ni1 + 1, Z0 + nj1 + 1.2):
                continue
            C.h[ni0:ni1 + 1, nj0:nj1 + 1] = round(low, 3)
            C.notch[ni0:ni1 + 1, nj0:nj1 + 1] = True
            C.claim[ni0:ni1 + 1, nj0:nj1 + 1] = 20000 + len(plans)
            plans.append({"dir": side, "edge": edge, "low": low, "high": high, "n": n, "cells": (ni0, nj0, ni1, nj1)})
            break
    return plans


def build_stairs(C, plans):
    out = []
    for q, s in enumerate(plans):
        rise = (s["high"] - s["low"]) / s["n"]
        ni0, nj0, ni1, nj1 = s["cells"]
        far = (X0 + ni1 + 1) if s["dir"] > 0 else (X0 + ni0)
        for t in range(s["n"]):
            a = s["edge"] + s["dir"] * t * TREAD
            b = far if t == s["n"] - 1 else s["edge"] + s["dir"] * (t + 1) * TREAD
            top = s["low"] + rise * (t + 1)
            x0, x1 = min(a, b), max(a, b)
            # each step a block from the notch floor up to its tread; the notch spans the whole cells
            z0, z1 = Z0 + nj0, Z0 + nj1 + 1
            out.append(_box(f"TerraceStep{q}_{t}", ((x0 + x1) / 2, (top + s["low"] - 0.3) / 2, (z0 + z1) / 2),
                            (x1 - x0, top - s["low"] + 0.3, z1 - z0), CAP if t % 2 else STONE, g="stairs"))
        # handrails up both sides
        L = abs(far - s["edge"])
        ang = math.degrees(math.atan2(s["high"] - s["low"], L))
        for zz in (Z0 + nj0 + 0.15, Z0 + nj1 + 1 - 0.15):
            mid = (s["edge"] + far) / 2
            y = (s["low"] + s["high"]) / 2 + 0.95
            out.append(_box(f"TerraceStepRail{q}_{zz:.0f}", (mid, y, zz), (math.hypot(L, s["high"] - s["low"]), 0.05, 0.05),
                            IRON, g="rail", r=(0, 0, ang * s["dir"])))
    return out


def build_bridge():
    """stone abutments and two piers under the raised deck"""
    out = []
    top = BRIDGE + 0.12 - 0.15 - 0.02
    for z0, z1 in ((175.5, 180.0), (190.0, 194.5)):
        out.append(_box(f"BridgeAbutment{len(out)}", (0, (top - 0.6) / 2, (z0 + z1) / 2), (10.6, top + 0.6, z1 - z0), STONE, g="bridge"))
    for x in (-3.4, 3.4):
        out.append(_box(f"BridgePier{len(out)}", (x, (top - 0.6) / 2, 185.0), (1.2, top + 0.6, 1.6), STONE, g="bridge"))
        out.append(_box(f"BridgePierCap{len(out)}", (x, top - 0.08, 185.0), (1.5, 0.16, 1.9), CAP, g="bridge"))
    for x in (-5.15, 5.15):   # stone parapet faces down the abutment ends
        for z0, z1 in ((175.5, 180.0), (190.0, 194.5)):
            out.append(_box(f"BridgeWing{len(out)}", (x, top / 2, (z0 + z1) / 2), (0.3, top + 0.2, z1 - z0), CAP, g="bridge"))
    return out


# ---------------------------------------------------------------------------
POINT_KEYS = {"p", "door", "light", "itemP", "banner", "haunt"}
SKIP = {"boxes", "horizon", "life", "districts", "landmarks", "regions", "world", "bounds", "rooms", "terrain", "lots"}


def lift_points(T, C, lots):
    def lift(v):
        if isinstance(v, list) and len(v) == 3 and all(isinstance(a, (int, float)) for a in v) and _in_grid(v[0], v[2]):
            v[1] = round(v[1] + C.at(v[0], v[2]), 3)

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in POINT_KEYS:
                    lift(v)
                elif k == "hide" and isinstance(v, list):
                    for q in range(0, len(v) - 2, 3):
                        if _in_grid(v[q], v[q + 2]):
                            v[q + 1] = round(v[q + 1] + C.at(v[q], v[q + 2]), 3)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for k, v in T.items():
        if k not in SKIP:
            walk(v)
    for lot, h in lots:
        lot["offset"][1] = round(lot["offset"][1] + h, 3)
        lot["center"][1] = round(lot["center"][1] + h, 3)
        lot["arrival"][1] = round(lot["arrival"][1] + h, 3)
        walk(lot.get("afterglow", {}))
    for r in T.get("rooms", []):
        x0, _, z0 = r["min"]
        x1, _, z1 = r["max"]
        i0, j0, i1, j1 = C.rect(max(x0, X0), max(z0, Z0), min(x1, X0 + NX), min(z1, Z0 + NZ))
        if i1 >= i0 and j1 >= j0:
            top = float(C.h[i0:i1 + 1, j0:j1 + 1].max())
            if top:
                r["max"][1] = round(r["max"][1] + top, 2)


def encode(C):
    """the ground for the game: a level index per cell ('.' = level 0), '~' where a ramp sets the height"""
    flat = (C.ramp < 0) | (C.claim >= 0)
    hq = np.round(C.h, 2)
    levels = sorted(set(hq[flat].tolist()) | {0.0})
    levels.remove(0.0)
    levels = [0.0] + levels
    alphabet = ".ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    assert len(levels) <= len(alphabet), len(levels)
    rows = []
    for j in range(NZ):          # z-major: row j holds every x
        row = []
        for i in range(NX):
            row.append("~" if not flat[i, j] else alphabet[levels.index(float(hq[i, j]))])
        rows.append("".join(row))
    ramps = []
    for name, x0, x1, z0, z1, axis, h0, h1 in RAMPS:
        ramps += [x0, x1, z0, z1, 0 if axis == "x" else 1, h0, h1]
    return {"x0": X0, "z0": Z0, "nx": NX, "nz": NZ, "cell": 1.0, "levels": levels, "cells": "".join(rows), "ramps": ramps,
            "alphabet": alphabet}


if __name__ == "__main__":
    import os
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "Assets", "Unmasked", "Resources", "HollowCreek.json")
    rep, _, _ = apply(p)
    print("  terrain:", ", ".join(f"{v} {k}" for k, v in rep.items()))
