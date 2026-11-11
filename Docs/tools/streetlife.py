"""
Round 44: street life. Hollow Creek's streets had lamps and sidewalks and not much else, so the
grass verge beyond every sidewalk now gets what a real small town has along its kerbs: autumn
street trees with leaf piles under them, red fire hydrants, blue post boxes, green bins, benches,
newspaper boxes, and at the corners a signpost with the street's name.

It only places a thing where nothing else stands (no building, path, fence, road, lamp or prop
within reach), and it's seeded from the piece names, so every build of the town is the same.

    import streetlife; streetlife.build(T, rgb)    # from make_town.py, after the regions
"""
import math
import zlib

SPACING = 13.0   # metres between spots along a sidewalk
VERGE = 1.15     # metres from the sidewalk's outer edge to the middle of a spot
CLEAR = 1.4      # nothing else may stand this close to a spot's middle
KEEP_OUT = ("ground", "patch")  # tags that are fine to stand on

LEAVES = ("d8641e", "c8401e", "e0a028", "b8521a", "9a3a18")


def _roll(*key):
    return zlib.crc32("|".join(str(k) for k in key).encode()) % 1000


def _blocked(boxes, decor, x, z, r_any=CLEAR):
    for b in boxes:
        if b["g"] in KEEP_OUT or b.get("l", 9) != 9:
            continue
        (px, py, pz), (sx, sy, sz) = b["p"], b["s"]
        r = 0.3 if b["g"] == "road" else r_any  # stand right beside a sidewalk, never on a road
        if py - sy / 2 > 4.0:  # high things (roof eaves, string lights) don't block the ground
            continue
        if abs(b["r"][1]) % 180 > 1:  # a turned piece: use its bounding circle
            h = math.hypot(sx, sz) / 2
            if math.hypot(px - x, pz - z) < h + r:
                return True
            continue
        if abs(px - x) < sx / 2 + r and abs(pz - z) < sz / 2 + r:
            return True
    return any(math.hypot(d["p"][0] - x, d["p"][2] - z) < r_any + 0.8 for d in decor if d.get("l", 9) == 9)


def _tree(T, rgb, n, x, z, k):
    h = 2.6 + (k % 7) * 0.15
    T.box(n + "Trunk", (x, h / 2, z), (0.32, h, 0.32), rgb("4a3222"), 9, "solid", "tree", shape="cyl")
    T.box(n + "Root", (x, 0.08, z), (0.6, 0.16, 0.6), rgb("3e2a1c"), 9, "nocollide", "tree", shape="cyl")
    leaf = LEAVES[k % len(LEAVES)]
    leaf2 = LEAVES[(k // 5) % len(LEAVES)]
    for i, (dx, dy, dz, s) in enumerate(((0, 0.9, 0, 2.6), (0.7, 0.4, 0.3, 1.8), (-0.6, 0.5, -0.4, 1.9), (0.1, 1.6, -0.2, 1.7))):
        c = leaf if i % 2 == 0 else leaf2
        T.box(f"{n}Crown{i}", (x + dx, h + dy, z + dz), (s, s * 0.85, s), rgb(c), 9, "nocollide", "tree", shape="sphere")
    for i in range(5):  # a scatter of fallen leaves round the foot
        a = math.radians(k * 37 + i * 72)
        d = 0.55 + (k + i * 13) % 5 * 0.12
        T.box(f"{n}Leaves{i}", (x + math.cos(a) * d, 0.03, z + math.sin(a) * d), (0.5, 0.06, 0.36), rgb(LEAVES[(k + i) % len(LEAVES)]), 9, "nocollide", "decor", shape="sphere")


def _hydrant(T, rgb, n, x, z, ry):
    red, cap = rgb("c8302a"), rgb("e8d8b0")
    T.box(n + "Body", (x, 0.35, z), (0.3, 0.35, 0.3), red, 9, "solid", "decor", shape="rcyl")
    T.box(n + "Top", (x, 0.74, z), (0.3, 0.16, 0.3), red, 9, "nocollide", "decor", shape="sphere")
    T.box(n + "Cap", (x, 0.86, z), (0.1, 0.05, 0.1), cap, 9, "nocollide", "decor", shape="cyl")
    a = math.radians(ry)
    for s in (-1, 1):
        T.box(f"{n}Nozzle{s}", (x + math.cos(a) * s * 0.19, 0.5, z - math.sin(a) * s * 0.19), (0.12, 0.12, 0.12), cap, 9, "nocollide", "decor", shape="sphere")


def _postbox(T, rgb, n, x, z, ry):
    blue = rgb("2a4a8a")
    s = (0.5, 0.75, 0.45) if ry % 180 == 0 else (0.45, 0.75, 0.5)
    T.box(n + "Box", (x, 0.62, z), s, blue, 9, "solid", "decor", shape="rbox")
    T.box(n + "Lid", (x, 1.02, z), (0.5, 0.2, 0.5), blue, 9, "nocollide", "decor", shape="sphere")
    T.box(n + "Leg", (x, 0.13, z), (0.08, 0.26, 0.08), rgb("1a2a4a"), 9, "nocollide", "decor", shape="cyl")
    T.box(n + "Slot", (x, 0.86, z), (0.3, 0.03, 0.3), rgb("e8e0c8"), 9, "nocollide", "decor", shape="cyl")


def _bin(T, rgb, n, x, z):
    T.box(n + "Can", (x, 0.45, z), (0.5, 0.45, 0.5), rgb("3a5a3a"), 9, "solid", "decor", shape="rcyl")
    T.box(n + "Lid", (x, 0.93, z), (0.56, 0.05, 0.56), rgb("2a4a2a"), 9, "nocollide", "decor", shape="rcyl")
    T.box(n + "Handle", (x, 1.0, z), (0.12, 0.06, 0.12), rgb("2a4a2a"), 9, "nocollide", "decor", shape="sphere")


def _paper(T, rgb, n, x, z):
    T.box(n + "Box", (x, 0.55, z), (0.45, 0.5, 0.4), rgb("d8b030"), 9, "solid", "decor", shape="rbox")
    T.box(n + "Window", (x, 0.75, z), (0.47, 0.18, 0.3), rgb("f0e8c0"), 9, "emissive", "sign")
    T.box(n + "Legs", (x, 0.15, z), (0.3, 0.3, 0.3), rgb("4a4a4a"), 9, "nocollide", "decor")


def _signpost(T, rgb, n, x, z, street, along_x):
    T.box(n + "Pole", (x, 1.4, z), (0.09, 2.8, 0.09), rgb("2a2a2a"), 9, "solid", "decor", shape="cyl")
    T.box(n + "Ball", (x, 2.86, z), (0.14, 0.14, 0.14), rgb("c8a040"), 9, "nocollide", "decor", shape="sphere")
    s = (1.3, 0.24, 0.05) if along_x else (0.05, 0.24, 1.3)
    T.box(n + "Plate", (x, 2.55, z), s, rgb("2a5a3a"), 9, "solid", "sign")


def build(T, rgb):
    boxes = T.L["boxes"]
    decor = T.L["decor"]
    roads = {}
    for b in boxes:
        if b["g"] == "road" and "Walk" not in b["n"]:
            roads.setdefault(b["n"], []).append(b)
    walks = [b for b in boxes if "Walk" in b["n"] and b["g"] == "road" and b["n"].split("Walk")[1][:1] in "LR"]
    counts = {"tree": 0, "hydrant": 0, "postbox": 0, "bin": 0, "paper": 0, "sign": 0}
    signed = set()
    for wi, w in enumerate(walks):
        street, rest = w["n"].split("Walk", 1)
        side = rest[0]
        (px, _, pz), (sx, _, sz) = w["p"], w["s"]
        along_x = sx > sz
        length = sx if along_x else sz
        if length < 8.0:
            continue
        # outward = away from the road: which side of its road this sidewalk sits on
        width = sz if along_x else sx
        near = roads.get(street)
        if not near:
            continue
        road = min(near, key=lambda r: math.hypot(r["p"][0] - px, r["p"][2] - pz))
        out = (1 if pz > road["p"][2] else -1) if along_x else (1 if px > road["p"][0] else -1)
        n_spots = max(1, int(length // SPACING))
        for i in range(n_spots):
            f = (i + 0.5) / n_spots - 0.5
            off = width / 2 + VERGE
            if along_x:
                x, z = px + f * length, pz + out * off
                ry = 0 if out > 0 else 180
            else:
                x, z = px + out * off, pz + f * length
                ry = 90 if out > 0 else -90
            k = _roll(w["n"], i)
            kind = "tree" if k < 640 else "hydrant" if k < 720 else "postbox" if k < 790 else "bin" if k < 870 else "paper" if k < 910 else None
            if kind is None:
                continue
            r = CLEAR + (0.8 if kind == "tree" else 0.0)
            if _blocked(boxes, decor, x, z, r):
                continue
            n = f"Street{street.replace(' ', '')}{side}{wi}S{i}"
            if kind == "tree":
                _tree(T, rgb, n, x, z, k)
            elif kind == "hydrant":
                _hydrant(T, rgb, n, x, z, ry)
            elif kind == "postbox":
                _postbox(T, rgb, n, x, z, ry)
            elif kind == "bin":
                _bin(T, rgb, n, x, z)
            else:
                _paper(T, rgb, n, x, z)
            counts[kind] += 1
        # a street-name sign at the first corner of each side of each street
        key = (street, side)
        if key not in signed:
            for a in (1.0, 3.0, 5.0, -1.0, -3.0, -5.0):  # near either end of the sidewalk, wherever there's room
                d = -length / 2 + a if a > 0 else length / 2 + a
                if along_x:
                    x, z = px + d, pz + out * (width / 2 + 0.5)
                else:
                    x, z = px + out * (width / 2 + 0.5), pz + d
                if not _blocked(boxes, decor, x, z, 0.6):
                    _signpost(T, rgb, f"Street{street.replace(' ', '')}{side}Sign", x, z, street, along_x)
                    signed.add(key)
                    counts["sign"] += 1
                    break
    return counts
