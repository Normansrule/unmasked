"""
Detail and Halloween dressing shared by every layout (the town, the houses and Blackwood Manor).

finish(L) runs when a layout is saved and adds the detail nobody wants to place by hand:
  - a surface for every box ("sf": siding, shingles, brick, stone, floorboards, grass, asphalt...,
    see make_textures.py), picked from its tag and colour
  - window casings, a crossbar, shutters and flower boxes on the houses
  - a stone foundation along the bottom of outside walls, fascia boards along the eaves
  - no two jack-o'-lanterns alike: plain "jack" props become a mix of carvings
  - big lawns and roads split into tiles, so each tile is only lit by the lamps near it

The rest are set pieces in the spirit of LA's "Nights of the Jack" (an arch of jack-o'-lanterns,
a jack-o'-lantern tree, string lights, luminarias, porch displays), kept tasteful: one or two per
place, not every surface. They work with anything that has decor/glow/box methods.
"""
import math
import random

JACK_KINDS = ["jack", "jack_grin", "jack_scary", "jack_surprised", "jack_wink", "jack_tall", "jack_white"]
JACK_GLOW = [1.0, 0.604, 0.227]
WARM = [1.0, 0.812, 0.478]


def _rgb(h):
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4)]


def _r3(v):
    return [round(x, 3) for x in v]


def _lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def _sat(c):
    return max(c) - min(c)


# =============================================================================
# Surfaces
# =============================================================================
def wall_surface(c):
    if c[0] > c[1] + 0.12 and c[0] > c[2] + 0.12 and _lum(c) < 0.55:
        return "brick"
    if _sat(c) < 0.08 and _lum(c) < 0.62:
        return "stone"
    return "siding"


def surface(b):
    t, g, c, m, s, r = b["t"], b["g"], b["c"], b["m"], b["s"], b["r"]
    if m in ("glass", "emissive", "ghost"):
        return ""
    if t == "sphere" and g in ("tree", "hedge"):
        return "leaf"
    if t != "box":
        return ""
    thin = min(s)
    rotated = abs(r[0]) > 1 or abs(r[2]) > 1
    if g == "roof":
        if rotated and thin <= 0.35:
            return "shingle_z" if abs(r[2]) > abs(r[0]) else "shingle"
        if s[1] <= 0.35:
            return "gravel" if s[0] > 6 and s[2] > 6 else ""
        if min(s[0], s[2]) <= 0.4:          # a gable end: really a wall
            return wall_surface(c)
        if max(s) <= 1.4 and s[1] > 1.0:    # a chimney
            return "brick"
        return "shingle" if _lum(c) < 0.35 else ""
    if g in ("wall", "building", "porchwall"):
        if g == "wall" and thin < 0.25:
            return "plaster"
        return wall_surface(c)
    if g in ("floor", "porch", "stairs", "deck"):
        if c[0] > c[2] + 0.08 and _lum(c) < 0.6 and s[1] <= max(s[0], s[2]):
            return "planks_z" if s[2] > s[0] * 3 else "planks"
        return ""
    if g in ("ground", "patch", "path", "road"):
        if g == "road" and _lum(c) > 0.45:
            return ""                        # lane markings
        if c[1] > c[0] and c[1] > c[2]:
            return "grass"
        if _sat(c) < 0.07:
            return "road" if g == "road" or _lum(c) < 0.32 else "gravel"
        return "gravel"
    if g == "tree":
        return "bark"
    if g == "hedge":
        return "leaf"
    if g in ("grave", "cemetery", "fountain"):
        return "stone"
    if g == "water":
        return "water"
    return ""


# =============================================================================
# Detail that every layout gets when it is saved
# =============================================================================
def _box(L, name, p, s, c, level, mode="solid", tag="trim", r=(0, 0, 0), sf=None):
    b = {"n": name, "t": "box", "p": _r3(p), "s": _r3(s), "r": [round(v, 2) for v in r], "c": c, "m": mode, "l": level, "g": tag}
    if sf is not None:
        b["sf"] = sf
    L["boxes"].append(b)


def _footprints(L):
    """Centre of each level's outside walls (to tell which way a window faces)."""
    out = {}
    for lvl in (0, 1, 2):
        xs = [b["p"][0] for b in L["boxes"] if b["g"] == "wall" and b["l"] == lvl and min(b["s"][0], b["s"][2]) >= 0.25]
        zs = [b["p"][2] for b in L["boxes"] if b["g"] == "wall" and b["l"] == lvl and min(b["s"][0], b["s"][2]) >= 0.25]
        if xs:
            out[lvl] = ((min(xs) + max(xs)) / 2, (min(zs) + max(zs)) / 2)
    return out


def window_trim(L, trim, shutter, house):
    names = {b["n"]: b for b in L["boxes"]}
    centres = _footprints(L) if house else {}
    added = 0
    for b in list(L["boxes"]):
        is_house_pane = b["m"] == "glass" and b["g"] == "wall" and "_glass" in b["n"]
        is_shop_pane = b["g"] == "window"
        if not (is_house_pane or is_shop_pane) or abs(b["r"][1]) > 1:
            continue
        sx, sy, sz = b["s"]
        along_x = sx >= sz
        w, h = (sx if along_x else sz), sy
        if w < 0.5 or h < 0.5:
            continue
        x, y, z = b["p"]
        lvl = b["l"]
        col = trim
        depth = 0.16
        if is_house_pane:
            mull = names.get(b["n"].replace("_glass", "_mullion"))
            if mull:
                depth = (mull["s"][2] if along_x else mull["s"][0]) + 0.02
                col = mull["c"]

        def put(n, u, v, su, sv, sd, c=col, off=0.0, mode="solid"):
            if along_x:
                _box(L, f"{b['n']}_{n}", (x + u, y + v, z + off), (su, sv, sd), c, lvl, mode)
            else:
                _box(L, f"{b['n']}_{n}", (x + off, y + v, z + u), (sd, sv, su), c, lvl, mode)

        put("Head", 0, h / 2 + 0.07, w + 0.3, 0.14, depth + 0.04, mode="nocollide")
        put("CasingL", -(w / 2 + 0.05), 0, 0.1, h, depth, mode="nocollide")
        put("CasingR", w / 2 + 0.05, 0, 0.1, h, depth, mode="nocollide")
        put("Rail", 0, h * 0.08, w, 0.05, depth - 0.02, mode="nocollide")
        if is_shop_pane:
            put("Sill", 0, -h / 2 - 0.05, w + 0.2, 0.08, depth + 0.06, mode="nocollide")
        added += 4

        # Shutters and a flower box, on the outside of the house
        if house and is_house_pane and lvl in centres and w >= 0.9:
            cx, cz = centres[lvl]
            out = (1 if z > cz else -1) if along_x else (1 if x > cx else -1)
            face = depth / 2 + 0.05
            sw = min(0.5, w * 0.4)
            for side in (-1, 1):
                put(f"Shutter{side}", side * (w / 2 + 0.1 + sw / 2), 0, sw, h * 0.98, 0.05, shutter, out * face, "nocollide")
                for k in range(3):
                    put(f"Slat{side}{k}", side * (w / 2 + 0.1 + sw / 2), -h * 0.3 + k * h * 0.3, sw * 0.8, 0.03, 0.03,
                        [v * 0.75 for v in shutter], out * (face + 0.03), "nocollide")
            if lvl == 0 and y - h / 2 > 0.6 and along_x and out < 0:
                put("Planter", 0, -h / 2 - 0.2, w + 0.1, 0.26, 0.3, _rgb("5a3a24"), out * (depth / 2 + 0.17), "nocollide")
                L["boxes"][-1]["sf"] = "planks"
                for k, colr in enumerate((_rgb("b8461e"), _rgb("d8a03a"), _rgb("8a2a3a"))):
                    u = (k - 1) * (w / 3)
                    if along_x:
                        p = (x + u, y - h / 2 - 0.02, z + out * (depth / 2 + 0.17))
                    else:
                        p = (x + out * (depth / 2 + 0.17), y - h / 2 - 0.02, z + u)
                    L["boxes"].append({"n": f"{b['n']}_Mum{k}", "t": "sphere", "p": _r3(p), "s": [w / 3.2, 0.24, 0.28], "r": [0, 0, 0],
                                       "c": colr, "m": "nocollide", "l": lvl, "g": "decor"})
            added += 8
    return added


def foundations(L, color):
    added = 0
    for b in list(L["boxes"]):
        if b["m"] != "solid" or abs(b["r"][1]) > 1 or abs(b["r"][0]) > 1 or abs(b["r"][2]) > 1:
            continue
        x, y, z = b["p"]
        sx, sy, sz = b["s"]
        bottom = y - sy / 2
        if b["g"] == "wall" and b["l"] in (0, 9) and min(sx, sz) >= 0.25 and abs(bottom) < 0.06 and sy >= 0.9:
            if sx >= sz:
                _box(L, b["n"] + "_Plinth", (x, 0.25, z), (sx, 0.5, sz + 0.1), color, b["l"], "nocollide", "trim", sf="stone")
            else:
                _box(L, b["n"] + "_Plinth", (x, 0.25, z), (sx + 0.1, 0.5, sz), color, b["l"], "nocollide", "trim", sf="stone")
            added += 1
        elif b["g"] == "building" and abs(bottom) < 0.06 and sy >= 2:
            _box(L, b["n"] + "_Plinth", (x, 0.3, z), (sx + 0.14, 0.6, sz + 0.14), color, b["l"], "nocollide", "trim", sf="stone")
            _box(L, b["n"] + "_Cornice", (x, y + sy / 2 - 0.15, z), (sx + 0.24, 0.3, sz + 0.24), [v * 0.8 for v in b["c"]], b["l"],
                 "nocollide", "trim")
            added += 2
    return added


def fascia(L, color):
    from math import cos, sin, radians
    added = 0
    for b in list(L["boxes"]):
        if b["g"] != "roof" or b["t"] != "box" or min(b["s"]) > 0.35:
            continue
        rx, ry, rz = b["r"]
        if abs(ry) > 1 or not (8 < abs(rx) < 80 or 8 < abs(rz) < 80):
            continue
        x, y, z = b["p"]
        sx, _, sz = b["s"]
        if abs(rx) > abs(rz):
            if sx < 1.5:
                continue
            # local +z end is at y + sin(rx)*... (Unity: positive rx tips +z down)
            dy, dz = -sin(radians(rx)) * sz / 2, cos(radians(rx)) * sz / 2
            ez, ey = (z + dz, y + dy) if dy < 0 else (z - dz, y - dy)
            _box(L, b["n"] + "_Fascia", (x, ey - 0.1, ez), (sx, 0.26, 0.07), color, b["l"], "nocollide", "trim")
        else:
            if sz < 1.5:
                continue
            dy, dx = sin(radians(rz)) * sx / 2, cos(radians(rz)) * sx / 2
            ex, ey = (x + dx, y + dy) if dy < 0 else (x - dx, y - dy)
            _box(L, b["n"] + "_Fascia", (ex, ey - 0.1, z), (0.07, 0.26, sz), color, b["l"], "nocollide", "trim")
        added += 1
    return added


def tile_ground(L, size=16.0):
    out = []
    for b in L["boxes"]:
        sx, sy, sz = b["s"]
        if b["g"] in ("ground", "road") and b["t"] == "box" and b["r"] == [0, 0, 0] and (sx > size * 1.5 or sz > size * 1.5):
            nx, nz = max(1, round(sx / size)), max(1, round(sz / size))
            x0, z0 = b["p"][0] - sx / 2, b["p"][2] - sz / 2
            for i in range(nx):
                for j in range(nz):
                    t = dict(b, n=f"{b['n']}_{i}_{j}", p=_r3((x0 + (i + 0.5) * sx / nx, b["p"][1], z0 + (j + 0.5) * sz / nz)),
                             s=_r3((sx / nx, sy, sz / nz)))
                    out.append(t)
        else:
            out.append(b)
    L["boxes"] = out


def vary_jacks(L):
    """Every jack-o'-lantern gets its own carving (the same one each time the script runs)."""
    for d in L.get("decor", []):
        if d["k"] == "jack":
            h = int(abs(d["p"][0] * 73.1 + d["p"][2] * 37.7 + d["p"][1] * 11.3) * 10) % 100
            if h >= 34:
                d["k"] = JACK_KINDS[1 + h % (len(JACK_KINDS) - 1)]


def finish(L, house=True):
    """Detail every layout gets when saved. house: add shutters and flower boxes."""
    trim = L.get("trim") or _rgb("efe6d2")
    shutter = L.get("shutter") or _rgb("2f4a3a")
    counts = {
        "window trim": window_trim(L, trim, shutter, house),
        "foundations": foundations(L, L.get("foundation") or _rgb("5a5048")),
        "fascia": fascia(L, trim),
    }
    tile_ground(L)
    vary_jacks(L)
    for b in L["boxes"]:
        if "sf" not in b:
            sf = surface(b)
            if sf:
                b["sf"] = sf
    n = sum(1 for b in L["boxes"] if b.get("sf"))
    print(f"  detail: {counts['window trim']} window pieces, {counts['foundations']} foundation pieces, {counts['fascia']} fascia boards, "
          f"{n} textured boxes")


# =============================================================================
# Halloween set pieces (call these from the level scripts)
# =============================================================================
def _rot(dx, dz, ry):
    a = math.radians(ry)
    return dx * math.cos(a) + dz * math.sin(a), -dx * math.sin(a) + dz * math.cos(a)


def jack(H, p, ry=180.0, sc=1.0, level=9, glow=True, kind=None, rng=None):
    rng = rng or random
    H.decor(kind or rng.choice(JACK_KINDS), p, ry, sc, level)
    if glow:
        H.glow((p[0], p[1] + 0.45 * sc, p[2]), JACK_GLOW, 3.5 + 1.5 * sc, 0.8, level)


def string_lights(H, a, b, n=14, sag=0.35, level=9, colors=("bulb_orange", "bulb_purple", "bulb_orange", "bulb_green"), glow_every=5):
    """A sagging string of coloured bulbs from a to b (the wire too)."""
    pts = []
    for i in range(n):
        f = (i + 0.5) / n
        x = a[0] + (b[0] - a[0]) * f
        z = a[2] + (b[2] - a[2]) * f
        y = a[1] + (b[1] - a[1]) * f - sag * 4 * f * (1 - f)
        pts.append((x, y, z))
        H.decor(colors[i % len(colors)], (x, y - 0.03, z), 0, 1.0, level)
        if i % glow_every == glow_every // 2:
            c = {"bulb_orange": [1, 0.55, 0.15], "bulb_purple": [0.7, 0.4, 1], "bulb_green": [0.5, 1, 0.4]}[colors[i % len(colors)]]
            H.glow((x, y - 0.2, z), c, 3.0, 0.45, level)
    ends = [a] + pts + [b]
    for i in range(len(ends) - 1):
        p, q = ends[i], ends[i + 1]
        dx, dy, dz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
        length = math.sqrt(dx * dx + dy * dy + dz * dz)
        if length < 1e-3:
            continue
        ry = math.degrees(math.atan2(dx, dz))
        rx = -math.degrees(math.asin(max(-1, min(1, dy / length))))
        H.box(f"Wire{len(H.L['boxes'])}", ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.03, (p[2] + q[2]) / 2), (0.02, 0.02, length),
              [0.08, 0.08, 0.08], level, "nocollide", "decor", r=(rx, ry, 0))


def jack_arch(H, cx, cz, width=3.6, height=3.4, ry=0.0, level=9, rng=None, frame=(0.15, 0.14, 0.17)):
    """An arch of jack-o'-lanterns over a path, like the trail entrance at Nights of the Jack."""
    rng = rng or random.Random(int(cx * 13 + cz * 7))
    frame = list(frame)
    r = width / 2
    rise = height - r
    for side in (-1, 1):
        x, z = _rot(side * r, 0, ry)
        H.box(f"ArchPost{side}_{len(H.L['boxes'])}", (cx + x, rise / 2, cz + z), (0.14, rise, 0.14), frame, level, "solid", "decor")
    seg = 12
    for k in range(seg):
        a0, a1 = math.pi * k / seg, math.pi * (k + 1) / seg
        u0, v0 = -r * math.cos(a0), rise + r * math.sin(a0)
        u1, v1 = -r * math.cos(a1), rise + r * math.sin(a1)
        um, vm = (u0 + u1) / 2, (v0 + v1) / 2
        x, z = _rot(um, 0, ry)
        tilt = math.degrees(math.atan2(v1 - v0, u1 - u0))
        H.box(f"ArchRib{k}_{len(H.L['boxes'])}", (cx + x, vm, cz + z), (math.hypot(u1 - u0, v1 - v0) + 0.04, 0.12, 0.12), frame, level,
              "nocollide", "decor", r=(0, ry, tilt))
    count = max(9, int(math.pi * r / 0.42))
    for k in range(count):
        a = math.pi * k / (count - 1)
        u, v = -(r + 0.05) * math.cos(a), rise + (r + 0.05) * math.sin(a)
        x, z = _rot(u, 0.1, ry)
        H.decor(rng.choice(JACK_KINDS), (cx + x, v - 0.22, cz + z), ry, 0.62 + 0.12 * (k % 2), level)
    for k in range(4):  # two stacks of jacks at the feet of the arch
        for side in (-1, 1):
            x, z = _rot(side * (r + 0.45), 0, ry)
            H.decor(rng.choice(JACK_KINDS), (cx + x, k * 0.45, cz + z), ry + rng.uniform(-20, 20), 0.85 - 0.08 * k, level)
    for u, v in ((-r, rise), (0, height), (r, rise)):
        x, z = _rot(u, 0.6, ry)
        H.glow((cx + x, v - 0.2, cz + z), JACK_GLOW, 6, 1.0, level)
    x, z = _rot(0, 0, ry)
    H.glow((cx, 0.8, cz), JACK_GLOW, 5, 0.9, level)


def jack_tree(H, x, z, height=4.2, level=9, rng=None):
    """A cone of jack-o'-lanterns around a pole, the trail's signature centrepiece."""
    rng = rng or random.Random(int(x * 31 + z * 17))
    H.box(f"JackTreePole{len(H.L['boxes'])}", (x, height / 2, z), (0.16, height, 0.16), [0.12, 0.1, 0.12], level, "solid", "decor")
    rings = int(height / 0.55)
    for i in range(rings):
        y = i * 0.55
        rad = 1.6 * (1 - i / rings) + 0.15
        n = max(1, int(2 * math.pi * rad / 0.55))
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * (i % 2)) / n
            px, pz = x + rad * math.sin(a), z + rad * math.cos(a)
            H.decor(rng.choice(JACK_KINDS), (px, y, pz), math.degrees(a), 0.6, level)
    H.decor("jack_grin", (x, rings * 0.55, z), 180, 0.8, level)
    for y in (0.8, 2.2, 3.6):
        if y < height:
            H.glow((x, y, z), JACK_GLOW, 6.5, 1.1, level)


def luminarias(H, a, b, spacing=1.6, offset=1.2, level=9, glow_every=3):
    """Paper-bag candles along both sides of a path from a to b (x, z)."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dz)
    if length < 0.1:
        return
    ux, uz = dx / length, dz / length
    n = int(length / spacing) + 1
    for i in range(n):
        for side in (-1, 1):
            x = a[0] + ux * i * spacing - uz * offset * side
            z = a[1] + uz * i * spacing + ux * offset * side
            H.decor("luminaria", (x, 0.02, z), math.degrees(math.atan2(-side * uz, side * ux)), 1.0, level)
            if i % glow_every == 0 and side == 1:
                H.glow((x, 0.35, z), [1.0, 0.75, 0.4], 3.0, 0.6, level)


def porch_display(H, x, y, z, ry=180.0, width=2.6, level=9, rng=None):
    """Either side of a front door: cornstalks, mums, a pumpkin stack and a jack with gourds."""
    rng = rng or random.Random(int(x * 11 + z * 5))

    def at(u, v):
        dx, dz = _rot(u, v, ry)
        return (x + dx, y, z + dz)

    H.decor("cornstalks", at(-width / 2 - 0.3, 0.2), ry, 1.0, level)
    H.decor("cornstalks", at(width / 2 + 0.3, 0.2), ry, 1.0, level)
    H.decor("pumpkin_stack", at(-width / 2 + 0.2, 0.55), ry + 10, 0.85, level)
    H.decor("mums", at(-width / 2 - 0.25, 0.75), ry, 0.9, level)
    H.decor(rng.choice(JACK_KINDS), at(width / 2 - 0.1, 0.5), ry - 10, 1.0, level)
    H.decor("gourds", at(width / 2 + 0.35, 0.8), ry, 1.4, level)
    H.decor("mums_purple", at(width / 2 + 0.35, 0.2), ry, 0.8, level)
    H.decor("pumpkin", at(width / 2 - 0.55, 0.85), ry + 40, 0.7, level)
    p = at(0, 0.6)
    H.glow((p[0], y + 0.9, p[2]), JACK_GLOW, 5, 1.0, level)


def wreath(H, door_centre, ry, level=0):
    """A harvest wreath on a door. door_centre: (x, y, z) of the outside of the door; ry faces outwards."""
    x, y, z = door_centre
    H.decor("wreath", (x, y + 1.55, z), ry, 1.0, level)


def graves(H, x, z, n=5, spread=3.0, level=9, rng=None):
    rng = rng or random.Random(int(x * 3 + z * 19))
    for i in range(n):
        gx, gz = x + rng.uniform(-spread, spread), z + rng.uniform(-spread / 2, spread / 2)
        H.decor(rng.choice(["tomb_round", "tomb_cross", "tomb_round"]), (gx, 0.0, gz), 180 + rng.uniform(-12, 12), rng.uniform(0.85, 1.1), level)
        if i % 2 == 0:
            H.decor("candle", (gx + 0.35, 0.0, gz - 0.35), 0, 1.1, level)
            H.glow((gx + 0.35, 0.35, gz - 0.35), [1.0, 0.7, 0.28], 2.5, 0.6, level)
