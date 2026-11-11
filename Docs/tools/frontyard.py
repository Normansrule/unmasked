"""
Round 47: front gardens. The 23 trick-or-treat homes had a lawn, a path, a box hedge or a fence and two
pumpkins, so from the sidewalk every front yard read as an empty green sheet. This adds what a lived-in
autumn front garden has, all of it in front of the house where players walk past:

  - window boxes of mums and trailing ivy under every front window (both floors)
  - rounded foundation shrubs along the front wall, a few in autumn red
  - a border of flowers down both sides of the front path, with low stone edging
  - a soft clipped crown on top of every box hedge, so hedges stop reading as green bricks
  - a rocking chair (and on wide porches a little side table with a lantern) on the porch
  - in about half the yards, a raked pile of leaves with the rake still leaning in it

It never moves or removes anything: a piece goes in only where no solid piece, path or prop already is,
and every choice is seeded from the house name, so every build of the town is the same.

    import frontyard; frontyard.build(T, rgb)    # from make_town.py, after streetlife
"""
import math
import re
import zlib

LEAF = ("d8641e", "c8401e", "e0a028", "b8521a", "9a3a18")
SHRUB = ("2c4a2a", "355a30", "2a4630", "3a5a34", "8a2a22")   # the last is a burning bush in October
FLOWERS = ("e08a2a", "c84a2a", "e8c040", "7a3a8a", "b0306a", "f0e0c0")
IVY = "3a6a32"
PLANTER = ("5a3a26", "7a2e22", "2e3e4a", "e6e0d0")
STONE = "8e877c"
CELL = 4.0   # spatial hash cell for the clearance test


def _roll(*key):
    return zlib.crc32("|".join(str(k) for k in key).encode()) % 1000


class _Space:
    """What's already standing, hashed by position, so a new piece can ask whether its spot is free."""

    def __init__(self, boxes, decor):
        self.grid = {}
        for b in boxes:
            if b["g"] in ("ground", "patch") or b.get("l", 9) != 9:
                continue
            (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
            if b["t"] in ("cyl", "rcyl", "capsule"):
                sy *= 2
            if any(abs(a) > 0.01 for a in b["r"]):  # a turned piece: the box round its turned corners
                sx, sy, sz = _turned(sx, sy, sz, b["r"])
            self.add((px - sx / 2, px + sx / 2, py - sy / 2, py + sy / 2, pz - sz / 2, pz + sz / 2))
        for d in decor:
            x, y, z = d["p"]
            r = 0.45 * d.get("sc", 1.0)
            self.add((x - r, x + r, y, y + 1.2, z - r, z + r))

    def add(self, e):
        for i in range(int(math.floor(e[0] / CELL)), int(math.floor(e[1] / CELL)) + 1):
            for k in range(int(math.floor(e[4] / CELL)), int(math.floor(e[5] / CELL)) + 1):
                self.grid.setdefault((i, k), []).append(e)

    def free(self, e, pad=0.0):
        for i in range(int(math.floor(e[0] / CELL)), int(math.floor(e[1] / CELL)) + 1):
            for k in range(int(math.floor(e[4] / CELL)), int(math.floor(e[5] / CELL)) + 1):
                for o in self.grid.get((i, k), ()):
                    if (e[0] < o[1] - pad and o[0] < e[1] - pad and e[2] < o[3] - pad and o[2] < e[3] - pad
                            and e[4] < o[5] - pad and o[4] < e[5] - pad):
                        return False
        return True


def _turned(sx, sy, sz, euler):
    """Size of the upright box round a box turned by Unity Euler angles (z, then x, then y)."""
    ax, ay, az = (math.radians(a) for a in euler)
    cx, sx_, cy, sy_, cz, sz_ = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    rz = ((cz, -sz_, 0), (sz_, cz, 0), (0, 0, 1))
    rx = ((1, 0, 0), (0, cx, -sx_), (0, sx_, cx))
    ry = ((cy, 0, sy_), (0, 1, 0), (-sy_, 0, cy))

    def mul(a, b):
        return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    m = mul(ry, mul(rx, rz))
    h = (sx / 2, sy / 2, sz / 2)
    return tuple(2 * sum(abs(m[i][j]) * h[j] for j in range(3)) for i in range(3))


def _ext(p, s):
    return (p[0] - s[0] / 2, p[0] + s[0] / 2, p[1] - s[1] / 2, p[1] + s[1] / 2, p[2] - s[2] / 2, p[2] + s[2] / 2)


class _Home:
    """One house in a local frame: u runs along the front wall, v runs out from it towards the street."""

    def __init__(self, k, body, door):
        self.k = k
        (bx, _, bz), (sx, _, sz) = body["p"], body["s"]
        dx, dz = door["p"][0] - bx, door["p"][2] - bz
        if abs(dx) / sx > abs(dz) / sz:   # the door is on an east or west wall
            self.along_x = False
            self.out = (1 if dx > 0 else -1, 0)
            self.wall = bx + self.out[0] * sx / 2
            self.uc, self.half = bz, sz / 2
            self.face = "E" if dx > 0 else "W"
        else:
            self.along_x = True
            self.out = (0, 1 if dz > 0 else -1)
            self.wall = bz + self.out[1] * sz / 2
            self.uc, self.half = bx, sx / 2
            self.face = "N" if dz > 0 else "S"
        self.ry = {"N": 0, "S": 180, "E": 90, "W": -90}[self.face]

    def P(self, u, v, y=0.0):
        """local (u along the wall, v out from it) -> world (x, y, z)"""
        if self.along_x:
            return (u, y, self.wall + self.out[1] * v)
        return (self.wall + self.out[0] * v, y, u)

    def S(self, su, sy, sv):
        """local size -> world size"""
        return (su, sy, sv) if self.along_x else (sv, sy, su)


def _put(T, space, name, p, s, color, mode="nocollide", tag="decor", shape="box", r=(0, 0, 0), check=True):
    e = _ext(p, s if shape not in ("cyl", "rcyl", "capsule") else (s[0], s[1] * 2, s[2]))
    if check and not space.free(e):
        return False
    T.box(name, p, s, color, 9, mode, tag, shape, r)
    space.add(e)
    return True


def build(T, rgb):
    boxes, decor = T.L["boxes"], T.L["decor"]
    by = {b["n"]: b for b in boxes}
    space = _Space(boxes, decor)
    counts = {"window boxes": 0, "shrubs": 0, "border flowers": 0, "hedge crowns": 0, "rocking chairs": 0, "leaf piles": 0, "wheelbarrows": 0, "path lights": 0}
    homes = sorted(int(m.group(1)) for n in by for m in [re.match(r"^Home(\d+)Body$", n)] if m)
    for k in homes:
        body, door = by[f"Home{k}Body"], by.get(f"Home{k}Door")
        if door is None:
            continue
        H = _Home(k, body, door)
        n0 = f"Garden{k}"

        # 1. hedge crowns: a rounded, slightly wider cap on every box hedge, so it looks clipped, not cut
        for part in range(2):
            hb = by.get(f"Home{k}Hedge{part}")
            if not hb:
                continue
            (hx, hy, hz), (sx, sy, sz) = hb["p"], hb["s"]
            top = hy + sy / 2
            T.box(f"{n0}HedgeCrown{part}", (hx, top + 0.1, hz), (sx + 0.06, 0.28, sz + 0.1), rgb("335530"), 9, "nocollide", "hedge", "rbox")
            counts["hedge crowns"] += 1
            # a few soft bumps along the crown, so it isn't a perfect bar
            length = max(sx, sz)
            n = max(2, int(length / 1.3))
            for i in range(n):
                f = (i + 0.5) / n - 0.5
                bx, bz = (hx + f * length, hz) if sx > sz else (hx, hz + f * length)
                w = min(sx, sz) * 0.9
                T.box(f"{n0}HedgeBump{part}_{i}", (bx, top + 0.2, bz), (w + 0.1, 0.32, w + 0.1),
                      rgb(("2f5030", "38603a", "2c4a2a")[_roll(k, part, i) % 3]), 9, "nocollide", "hedge", "sphere")

        # 2. window boxes under every front window
        face_re = re.compile(rf"^Home{k}Win{H.face}(\d)(\d)$")
        for n in sorted(by):
            m = face_re.match(n)
            if not m:
                continue
            win = by[n]   # dressing.window_trim later hangs a sill 0.09 below the glass; the box goes under it
            (wsx, wsy, wsz), (px, py, pz) = win["s"], win["p"]
            length = ((wsx if H.along_x else wsz) + 0.2) * 0.92
            u = px if H.along_x else pz
            y = py - wsy / 2 - 0.09 - 0.13
            p = H.P(u, 0.13, y)
            tag = m.group(1) + m.group(2)
            pc = rgb(PLANTER[_roll(k, "planter") % len(PLANTER)])
            if not _put(T, space, f"{n0}WinBox{tag}", p, H.S(length, 0.22, 0.24), pc, "nocollide", "decor"):
                continue
            counts["window boxes"] += 1
            n_fl = max(3, int(length / 0.28))
            for i in range(n_fl):
                f = (i + 0.5) / n_fl - 0.5
                r = _roll(k, tag, i)
                col = rgb(FLOWERS[r % len(FLOWERS)]) if r % 4 else rgb(IVY)
                fp = H.P(u + f * length * 0.92, 0.13 + (r % 3 - 1) * 0.03, y + 0.15 + (r % 5) * 0.01)
                T.box(f"{n0}WinBox{tag}Bloom{i}", fp, (0.2, 0.17, 0.2), col, 9, "nocollide", "decor", "sphere")
            # ivy trailing over the front lip
            for i in range(2):
                f = (-0.3, 0.25)[i]
                ip = H.P(u + f * length, 0.26, y - 0.12)
                T.box(f"{n0}WinBox{tag}Ivy{i}", ip, H.S(0.14, 0.3, 0.08), rgb(IVY), 9, "nocollide", "decor", "rbox")

        # 3. foundation shrubs along the front wall, wherever the porch, steps and path leave room
        step = 1.15
        n_sh = int(2 * H.half / step)
        for i in range(n_sh):
            u = H.uc - H.half + (i + 0.5) * (2 * H.half / n_sh)
            r = _roll(k, "shrub", i)
            if r % 7 == 0:
                continue  # leave the odd gap, as real gardens do
            h = 0.65 + (r % 5) * 0.06
            w = 0.8 + (r % 3) * 0.1
            col = rgb(SHRUB[4] if r % 9 == 1 else SHRUB[r % 4])
            for v in (0.62, 2.78):  # against the wall, or where a porch covers it, along the porch's front edge
                if _put(T, space, f"{n0}Shrub{i}", H.P(u, v, h / 2), (w, h, w), col, "solid", "hedge", "sphere"):
                    break
            else:
                continue
            counts["shrubs"] += 1
            if r % 3 == 0:  # some shrubs have a smaller one tucked in front
                q = H.P(u + 0.35, v + 0.43, 0.22)
                _put(T, space, f"{n0}Shrub{i}b", q, (0.5, 0.44, 0.5), rgb(SHRUB[(r // 3) % 4]), "nocollide", "hedge", "sphere")

        # 4. flowers down both sides of the front path, with low stone edging
        path = by.get(f"Home{k}Path")
        if path:
            (ppx, _, ppz), (psx, _, psz) = path["p"], path["s"]
            if H.along_x:
                pu, vmid, plen = ppx, (ppz - H.wall) * H.out[1], psz
            else:
                pu, vmid, plen = ppz, (ppx - H.wall) * H.out[0], psx
            for side in (-1, 1):
                eu = pu + side * 0.72
                edge_p = H.P(eu, vmid, 0.04)
                _put(T, space, f"{n0}Edging{'LR'[side > 0]}", edge_p, H.S(0.1, 0.08, plen - 0.4), rgb(STONE), "nocollide", "trim", check=False)
                n_f = max(1, int((plen - 0.8) / 0.9))
                for i in range(n_f):
                    v = vmid - plen / 2 + 0.6 + i * ((plen - 1.2) / max(1, n_f - 1) if n_f > 1 else 0)
                    r = _roll(k, "border", side, i)
                    fp = H.P(pu + side * 1.05, v, 0.16)
                    col = rgb(FLOWERS[r % len(FLOWERS)])
                    if _put(T, space, f"{n0}Border{'LR'[side > 0]}{i}", fp, (0.42, 0.3, 0.42), col, "nocollide", "decor", "sphere"):
                        T.box(f"{n0}Border{'LR'[side > 0]}{i}Leaves", H.P(pu + side * 1.05, v, 0.06), (0.5, 0.12, 0.5), rgb("2f4f2a"), 9, "nocollide", "decor", "sphere")
                        counts["border flowers"] += 1

            # two little lantern stakes where the path meets the sidewalk, so the garden reads at night
            for side in (-1, 1):
                lp = H.P(pu + side * 0.95, vmid + plen / 2 - 0.35, 0.3)
                if _put(T, space, f"{n0}PathLight{'LR'[side > 0]}", lp, (0.06, 0.6, 0.06), rgb("2a2622"), "nocollide", "decor"):
                    T.box(f"{n0}PathLight{'LR'[side > 0]}Lamp", (lp[0], 0.66, lp[2]), (0.16, 0.18, 0.16), rgb("ffd27a"), 9, "nocollide", "decor")
                    T.box(f"{n0}PathLight{'LR'[side > 0]}Cap", (lp[0], 0.78, lp[2]), (0.22, 0.05, 0.22), rgb("2a2622"), 9, "nocollide", "decor")
                    T.glow((lp[0], 0.7, lp[2]), rgb("ffb35a"), 3.5, 0.6)
                    counts["path lights"] += 1

        # 5. a rocking chair at the quiet end of the porch
        porch = by.get(f"Home{k}Porch")
        if porch:
            (qx, qy, qz), (qsx, qsy, qsz) = porch["p"], porch["s"]
            top = qy + qsy / 2
            qu, qhalf = (qx, qsx / 2) if H.along_x else (qz, qsz / 2)
            qv = ((qz - H.wall) * H.out[1]) if H.along_x else ((qx - H.wall) * H.out[0])
            side = 1 if _roll(k, "rock") % 2 else -1
            cu = qu + side * (qhalf - 0.55)
            if abs(cu - H.uc) > 1.3:   # well clear of the door
                wood = rgb(("4a3424", "e6e0d0", "2e3e2a", "6a2a22")[_roll(k, "wood") % 4])
                seat = H.P(cu, qv - 0.15, top + 0.45)
                if _put(T, space, f"{n0}Rocker", seat, H.S(0.55, 0.06, 0.5), wood, "solid", "furniture"):
                    cv = qv - 0.15
                    T.box(f"{n0}RockerBack", H.P(cu, cv - 0.24, top + 0.85), H.S(0.55, 0.75, 0.06), wood, 9, "nocollide", "furniture")
                    for s in (-1, 1):
                        T.box(f"{n0}RockerArm{'LR'[s > 0]}", H.P(cu + s * 0.27, cv, top + 0.68), H.S(0.05, 0.05, 0.5), wood, 9, "nocollide", "furniture")
                        T.box(f"{n0}RockerLegF{'LR'[s > 0]}", H.P(cu + s * 0.24, cv + 0.2, top + 0.24), (0.05, 0.42, 0.05), wood, 9, "nocollide", "furniture")
                        T.box(f"{n0}RockerLegB{'LR'[s > 0]}", H.P(cu + s * 0.24, cv - 0.2, top + 0.24), (0.05, 0.42, 0.05), wood, 9, "nocollide", "furniture")
                        T.box(f"{n0}RockerRail{'LR'[s > 0]}", H.P(cu + s * 0.24, cv, top + 0.04), H.S(0.05, 0.05, 0.75), wood, 9, "nocollide", "furniture", "rbox")
                    T.box(f"{n0}RockerCushion", H.P(cu, cv, top + 0.5), H.S(0.5, 0.06, 0.45),
                          rgb(("8a2a22", "c87a2a", "3a4a6a", "6a4a7a")[_roll(k, "cush") % 4]), 9, "nocollide", "decor", "rbox")
                    T.box(f"{n0}RockerThrow", H.P(cu + 0.1, cv - 0.2, top + 0.78), H.S(0.3, 0.5, 0.05),
                          rgb(("d8a040", "6a7a4a", "a04a3a")[_roll(k, "throw") % 3]), 9, "nocollide", "decor", "rbox")
                    counts["rocking chairs"] += 1
                    # on a wide porch, a little table with a lantern beside the chair
                    tu = cu - side * 0.6
                    if 2 * qhalf > 3.2 and abs(tu - H.uc) > 1.1:
                        if _put(T, space, f"{n0}PorchTable", H.P(tu, cv, top + 0.25), (0.4, 0.5, 0.4), wood, "solid", "furniture"):
                            T.box(f"{n0}PorchLantern", H.P(tu, cv, top + 0.62), (0.16, 0.22, 0.16), rgb("ffcf7a"), 9, "nocollide", "decor")
                            T.box(f"{n0}PorchLanternCap", H.P(tu, cv, top + 0.76), (0.2, 0.05, 0.2), rgb("2a2622"), 9, "nocollide", "decor")
                            T.glow(H.P(tu, cv, top + 0.75), rgb("ffb35a"), 3, 0.5)

        # 6. a pile of raked leaves on the lawn, the rake still leaning in it
        r = _roll(k, "leaves")
        if r % 2 == 0:
            for tries in range(6):
                u = H.uc + (H.half - 1.0) * (1 if (r + tries) % 2 else -1)
                v = 2.6 + (tries // 2) * 0.8
                p = H.P(u, v, 0.18)
                col = rgb(LEAF[r % len(LEAF)])
                if _put(T, space, f"{n0}LeafPile", p, (1.5, 0.5, 1.3), col, "nocollide", "decor", "sphere"):
                    for i in range(4):
                        rr = _roll(k, "leaf", i)
                        a = rr / 1000 * 2 * math.pi
                        T.box(f"{n0}LeafPile{i}", (p[0] + math.cos(a) * 0.55, 0.3, p[2] + math.sin(a) * 0.45), (0.7, 0.32, 0.6),
                              rgb(LEAF[rr % len(LEAF)]), 9, "nocollide", "decor", "sphere")
                    for i in range(6):  # strays the wind took
                        rr = _roll(k, "stray", i)
                        a = rr / 1000 * 2 * math.pi
                        d = 1.1 + (rr % 7) * 0.15
                        T.box(f"{n0}Leaf{i}", (p[0] + math.cos(a) * d, 0.02, p[2] + math.sin(a) * d), (0.16, 0.02, 0.12),
                              rgb(LEAF[rr % len(LEAF)]), 9, "nocollide", "decor", "box", (0, rr % 180, 0))
                    # the rake: a handle leaning into the pile, and its fan of tines
                    hp = (p[0] + 0.55, 0.75, p[2] + 0.1)
                    T.box(f"{n0}RakeHandle", hp, (0.04, 1.6, 0.04), rgb("8a6a44"), 9, "nocollide", "decor", "box", (0, 0, 35))
                    T.box(f"{n0}RakeHead", (p[0] + 0.05, 0.36, p[2] + 0.1), (0.1, 0.06, 0.5), rgb("4a4a4a"), 9, "nocollide", "decor", "box", (0, 0, 35))
                    counts["leaf piles"] += 1
                    break
        else:
            # the other half: a wheelbarrow of pumpkins brought in from the patch
            for tries in range(6):
                side = 1 if (r + tries) % 2 else -1
                u = H.uc + side * (H.half - 1.0)
                v = 2.6 + (tries // 2) * 0.8
                p = H.P(u, v, 0.45)
                tray = H.S(0.7, 0.3, 1.0)
                if not _put(T, space, f"{n0}Barrow", p, tray, rgb(("6a2a22", "2e4a5a", "4a5a2a")[r % 3]), "solid", "decor"):
                    continue
                wv = v + 0.6   # the wheel at the street end, the handles back towards the house
                T.box(f"{n0}BarrowWheel", H.P(u, wv, 0.2), H.S(0.08, 0.4, 0.4), rgb("2a2622"), 9, "nocollide", "decor")
                for s_ in (-1, 1):
                    T.box(f"{n0}BarrowHandle{'LR'[s_ > 0]}", H.P(u + s_ * 0.28, v - 0.75, 0.42), H.S(0.05, 0.05, 0.7), rgb("8a6a44"), 9, "nocollide", "decor")
                    T.box(f"{n0}BarrowLeg{'LR'[s_ > 0]}", H.P(u + s_ * 0.25, v - 0.35, 0.15), (0.05, 0.3, 0.05), rgb("2a2622"), 9, "nocollide", "decor")
                for i in range(3):
                    rr = _roll(k, "barrow", i)
                    q = H.P(u + (i - 1) * 0.2, v + (i % 2) * 0.15 - 0.1, 0.68)
                    T.box(f"{n0}BarrowPumpkin{i}", q, (0.32, 0.26, 0.32), rgb(("e07a1e", "d8641e", "e8a040")[rr % 3]), 9, "nocollide", "decor", "sphere")
                    T.box(f"{n0}BarrowPumpkin{i}Stem", (q[0], 0.84, q[2]), (0.04, 0.08, 0.04), rgb("4a5a2a"), 9, "nocollide", "decor")
                counts["wheelbarrows"] += 1
                break
    return counts
