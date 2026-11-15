#!/usr/bin/env python3
"""
Round 49: life on the hills that round 48 raised.

The terraces came out bare: plain stone walls, steps with nothing at either end, and a grass bank to
the creek that you could only slide down. This pass dresses them:

  ivy         trailing ivy and moss hanging down the faces of the retaining walls (about half of them)
  lanterns    a lantern post at the top of every flight of steps, lit
  bank steps  three stone stairways down the creek bank from the high town, each with handrails,
              a lantern and a bench at the top looking over the water, and a little wooden landing
              at the bottom where the stairs meet the creek

It runs on the saved layout right after terrain.py (make_town.py calls it) and only adds pieces where
nothing already stands. The same town comes out every build.

    hillside.apply(path)
"""
import json
import math
import zlib

import terrain as tr

IVY = [[0.22, 0.44, 0.17], [0.3, 0.52, 0.2], [0.18, 0.36, 0.15], [0.62, 0.24, 0.12], [0.66, 0.42, 0.13]]   # the last two are autumn ivy
MOSS = [0.3, 0.42, 0.18]
IRON, STONE, CAP = tr.IRON, tr.STONE, tr.CAP
WOOD, WOOD_DARK = [0.42, 0.3, 0.19], [0.3, 0.21, 0.13]
LANTERN = [1.0, 0.8, 0.45]


def _r(*key):
    """a repeatable random number in [0, 1) from a key"""
    return (zlib.crc32(repr(key).encode()) & 0xFFFFFF) / float(0x1000000)


def ground_y(T, x, z):
    """the same answer TownLayout.GroundY gives"""
    t = T["terrain"]
    i, j = math.floor((x - t["x0"]) / t["cell"]), math.floor((z - t["z0"]) / t["cell"])
    if not (0 <= i < t["nx"] and 0 <= j < t["nz"]):
        return 0.0
    c = t["cells"][j * t["nx"] + i]
    if c != "~":
        return t["levels"][t["alphabet"].index(c)]
    R = t["ramps"]
    for r in range(0, len(R), 7):
        x0, x1, z0, z1, ax, h0, h1 = R[r:r + 7]
        if x0 <= x < x1 and z0 <= z < z1:
            u = (x - x0) / (x1 - x0) if ax == 0 else (z - z0) / (z1 - z0)
            return h0 + (h1 - h0) * min(1.0, max(0.0, u))
    return 0.0


class _Space:
    """footprints of everything standing, to keep new pieces clear of it"""

    def __init__(self, boxes):
        self.cells = {}
        for b in boxes:
            if b.get("g") in ("ground",) or b["n"].startswith(("Ground", "Creek", "WorldGround")):
                continue
            lo, hi = tr.aabb(b)
            if hi[1] - lo[1] < 0.15 and b["t"] == "box":   # flat: roads, paths, sidewalks
                continue
            self.add(lo[0], lo[2], hi[0], hi[2], lo[1], hi[1])

    def add(self, x0, z0, x1, z1, y0=-9.0, y1=99.0):
        for gx in range(int(math.floor(x0 / 4)), int(math.floor(x1 / 4)) + 1):
            for gz in range(int(math.floor(z0 / 4)), int(math.floor(z1 / 4)) + 1):
                self.cells.setdefault((gx, gz), []).append((x0, z0, x1, z1, y0, y1))

    def free(self, x0, z0, x1, z1, y0=-9.0, y1=99.0):
        for gx in range(int(math.floor(x0 / 4)), int(math.floor(x1 / 4)) + 1):
            for gz in range(int(math.floor(z0 / 4)), int(math.floor(z1 / 4)) + 1):
                for a, b, c, d, e, f in self.cells.get((gx, gz), ()):
                    if a < x1 and x0 < c and b < z1 and z0 < d and e < y1 and y0 < f:
                        return False
        return True


def _box(name, p, s, c, m="nocollide", g="hillside", t="box", r=(0, 0, 0)):
    return {"n": name, "t": t, "p": [round(v, 3) for v in p], "s": [round(v, 3) for v in s],
            "r": [round(v, 3) for v in r], "c": c, "m": m, "l": 9, "g": g}


# ---------------------------------------------------------------------------
def ivy(T, out):
    """ivy hanging down the low face of about half the retaining walls"""
    n = 0
    for b in [b for b in T["boxes"] if b.get("g") == "wall" and b["n"].startswith("TerraceWall") and "Cap" not in b["n"]]:
        (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
        along_z = sx < sz            # the wall runs along z, its faces look along x
        L = sz if along_z else sx
        top = py + sy / 2 - 0.12     # the terrace's edge (the cap sits above)
        # pick walls in patches about 4 m long, so the short pieces along a ramp share one choice
        line = round(px if along_z else pz, 1)
        patch = math.floor((pz if along_z else px) / 4)
        if L < 0.9 or _r("ivy", line, patch) > 0.5:
            continue
        # which face is the low one
        a = ground_y(T, px - 0.8, pz) if along_z else ground_y(T, px, pz - 0.8)
        c = ground_y(T, px + 0.8, pz) if along_z else ground_y(T, px, pz + 0.8)
        low, side = (a, -1) if a < c else (c, 1)
        drop = top - low
        if drop < 0.6:
            continue
        face = (px if along_z else pz) + side * 0.17
        k = max(2, int(L / 0.7))
        for q in range(k):
            u = (q + 0.5) / k - 0.5 + (_r("u", b["n"], q) - 0.5) * 0.5 / k
            hang = drop * (0.35 + 0.6 * _r("len", b["n"], q))
            w = 0.25 + 0.3 * _r("w", b["n"], q)
            col = IVY[int(_r("col", b["n"], q) * len(IVY))]
            a_ = (pz if along_z else px) + u * L
            y = top - hang / 2
            if along_z:
                out.append(_box(f"HillIvy{n}", (face, y, a_), (0.05, hang, w), col, t="rbox"))
            else:
                out.append(_box(f"HillIvy{n}", (a_, y, face), (w, hang, 0.05), col, t="rbox"))
            n += 1
        # a soft mossy roll along the top, where the ivy starts
        if along_z:
            out.append(_box(f"HillIvy{n}", (face, top - 0.06, pz), (0.12, 0.16, L * 0.9), MOSS, t="rbox"))
        else:
            out.append(_box(f"HillIvy{n}", (px, top - 0.06, face), (L * 0.9, 0.16, 0.12), MOSS, t="rbox"))
        n += 1
    return n


def lantern_post(T, out, name, x, z, y, h=1.9):
    out.append(_box(f"{name}Post", (x, y + h / 2, z), (0.09, h, 0.09), IRON, m="solid"))
    out.append(_box(f"{name}Base", (x, y + 0.08, z), (0.2, 0.16, 0.2), IRON, m="solid"))
    out.append(_box(f"{name}Glass", (x, y + h + 0.16, z), (0.2, 0.26, 0.2), LANTERN, m="emissive"))
    out.append(_box(f"{name}Cap", (x, y + h + 0.33, z), (0.3, 0.07, 0.3), IRON))
    T["glows"].append({"p": [round(x, 2), round(y + h + 0.1, 2), round(z, 2)], "c": [1.0, 0.82, 0.5], "range": 7,
                       "intensity": 0.9, "l": 9})


def stair_lanterns(T, out, space):
    """a lit lantern post beside the top step of every flight"""
    flights = {}
    for b in T["boxes"]:
        if b.get("g") == "stairs" and b["n"].startswith("TerraceStep") and "Rail" not in b["n"]:
            q, t = b["n"][len("TerraceStep"):].split("_")
            flights.setdefault(int(q), []).append((int(t), b))
    n = 0
    for q, steps in sorted(flights.items()):
        steps.sort()
        first, last = steps[0][1], steps[-1][1]
        dx = 1 if last["p"][0] > first["p"][0] else -1
        top = last["p"][1] + last["s"][1] / 2
        x = last["p"][0] + dx * (last["s"][0] / 2 + 0.45)
        for zz in (last["p"][2] - last["s"][2] / 2 - 0.45, last["p"][2] + last["s"][2] / 2 + 0.45):
            if not space.free(x - 0.2, zz - 0.2, x + 0.2, zz + 0.2, top, top + 2.4):
                continue
            lantern_post(T, out, f"HillLantern{n}", x, zz, ground_y(T, x, zz))
            space.add(x - 0.2, zz - 0.2, x + 0.2, zz + 0.2)
            n += 1
            break
    return n


# ---------------------------------------------------------------------------
BANK = ("Creek bank",)
WANT_X = (-100.0, -40.0, 30.0)   # roughly where the three stairways go
W = 1.8


def bank_steps(T, out, space):
    """stone stairways down the creek bank from the high town to a wooden landing on the water"""
    bank = next(r for r in tr.RAMPS if r[0] == "Creek bank")
    _, bx0, bx1, z0, z1, _, h0, h1 = bank
    n_steps = int(round((h0 - h1) / tr.RISE))           # 30 steps of 0.16 m
    tread = (z1 - z0) / n_steps
    used = []
    made = 0
    for want in WANT_X:
        spot = None
        for d in range(0, 40):
            for sg in (1, -1):
                x = want + sg * d
                if any(abs(x - u) < 20 for u in used):
                    continue
                # the bank must be open bank here, the terrace above it free to walk to, the creek edge clear
                ok = all(tr.ramp_at(xx, zz) == tr.RAMPS.index(bank) for xx in (x - W, x, x + W) for zz in (z0 + 0.3, z1 - 0.3))
                ok = ok and all(abs(ground_y(T, xx, zz) - h0) < 0.01 for xx in (x - W, x + W) for zz in (z0 - 6, z0 - 0.5))
                ok = ok and space.free(x - W - 1.2, z0 - 6, x + W + 1.2, z1 + 3.5)
                if ok:
                    spot = x
                    break
            if spot is not None:
                break
        if spot is None:
            continue
        used.append(spot)
        x = spot
        name = f"BankSteps{made}"
        for t in range(n_steps):
            za, zb = z0 + t * tread, z0 + (t + 1) * tread
            top = h0 - tr.RISE * t                       # each tread meets the bank at its back edge
            bottom = (h0 - (h0 - h1) * (zb - z0) / (z1 - z0)) - 0.35
            out.append(_box(f"{name}_{t}", (x, (top + bottom) / 2, (za + zb) / 2), (W, top - bottom, zb - za),
                            CAP if t % 2 else STONE, m="solid", g="stairs"))
        # side curbs and iron handrails down both sides
        ang = math.degrees(math.atan2(h0 - h1, z1 - z0))
        length = math.hypot(z1 - z0, h0 - h1)
        for sx in (-1, 1):
            cx = x + sx * (W / 2 + 0.12)
            out.append(_box(f"{name}Curb{sx}", (cx, (h0 + h1) / 2 + 0.05, (z0 + z1) / 2), (0.24, 0.3, length), STONE,
                            m="solid", g="stairs", r=(ang, 0, 0)))
            out.append(_box(f"{name}Rail{sx}", (cx, (h0 + h1) / 2 + 0.95, (z0 + z1) / 2), (0.05, 0.05, length), IRON,
                            m="solid", g="rail", r=(ang, 0, 0)))
            for k, zz in enumerate((z0 + 0.1, (z0 + z1) / 2, z1 - 0.1)):
                gy = h0 - (h0 - h1) * (zz - z0) / (z1 - z0)
                out.append(_box(f"{name}RailPost{sx}_{k}", (cx, gy + 0.5, zz), (0.06, 1.0, 0.06), IRON, m="solid", g="rail"))
        # a lantern and a bench at the top, looking out over the creek
        lantern_post(T, out, f"{name}Lantern", x + W / 2 + 0.6, z0 - 0.6, h0)
        bx = x - W / 2 - 1.5
        bz = z0 - 1.0
        out.append(_box(f"{name}BenchSeat", (bx, h0 + 0.44, bz), (1.6, 0.07, 0.42), WOOD, m="solid", g="bench", t="rbox"))
        out.append(_box(f"{name}BenchBack", (bx, h0 + 0.72, bz - 0.22), (1.6, 0.36, 0.06), WOOD, m="solid", g="bench", t="rbox",
                        r=(-12, 0, 0)))
        for lx in (-0.68, 0.68):
            out.append(_box(f"{name}BenchLeg{lx:+.0f}", (bx + lx, h0 + 0.21, bz), (0.07, 0.42, 0.38), IRON, m="solid", g="bench"))
        # the landing: a little wooden jetty over the water at the foot of the steps
        dz0, dz1 = z1, z1 + 3.2
        out.append(_box(f"{name}Landing", (x, 0.14, (dz0 + dz1) / 2), (2.4, 0.12, dz1 - dz0), WOOD, m="solid", g="dock"))
        for k in range(4):
            out.append(_box(f"{name}Plank{k}", (x, 0.205, dz0 + 0.4 + k * 0.8), (2.4, 0.01, 0.06), WOOD_DARK, g="dock"))
        for px in (x - 1.1, x + 1.1):
            for pz in (dz0 + 0.2, dz1 - 0.15):
                out.append(_box(f"{name}Piling{px - x:+.0f}{pz - dz0:.0f}", (px, 0.05, pz), (0.16, 0.9, 0.16), WOOD_DARK,
                                m="solid", g="dock", t="cyl", r=(0, 0, 0)) | {"s": [0.16, 0.45, 0.16]})
        space.add(x - W - 1.2, z0 - 2, x + W + 1.2, z1 + 3.5)
        made += 1
    return made


# ---------------------------------------------------------------------------
def apply(path):
    with open(path) as f:
        T = json.load(f)
    space = _Space(T["boxes"])
    out = []
    counts = {"ivy pieces": ivy(T, out)}
    counts["stair lanterns"] = stair_lanterns(T, out, space)
    counts["bank stairways"] = bank_steps(T, out, space)
    names = {b["n"] for b in T["boxes"]}
    assert not any(b["n"] in names for b in out), "a hillside piece reuses a name"
    T["boxes"].extend(out)
    counts["pieces"] = len(out)
    with open(path, "w") as f:
        json.dump(T, f, separators=(",", ":"))
    return counts


if __name__ == "__main__":
    import os
    import sys
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "..", "Assets", "Unmasked", "Resources", "HollowCreek.json")
    print("  hillside:", ", ".join(f"{v} {k}" for k, v in apply(p).items()))
