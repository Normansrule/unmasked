"""
Building blocks for house layouts (the JSON files Unity builds the houses from).

Same format as BlackwoodManor.json (see make_manor.py): units are metres, y is up, +z is north,
positions are centres, rotations are Unity Euler angles. "box" sizes are full sizes; "cyl" and
"capsule" sizes are Unity localScale (height = 2 * y).

Each house is built in its own local space with the front door facing the road (-z). The town
(make_town.py) places every house on its lot.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESOURCES = os.path.join(ROOT, "Assets", "Unmasked", "Resources")

STEP_RISE, STEP_RUN = 0.25, 0.35
DOOR_H, WIN_LO, WIN_HI = 2.3, 1.0, 2.3


def rgb(h):
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4)]


def r3(v):
    return [round(x, 3) for x in v]


def facing(dx, dz):
    return math.degrees(math.atan2(dx, dz))


class Layout:
    def __init__(self, name, house_id, style, blurb):
        self.L = {
            "name": name, "id": house_id, "style": style, "blurb": blurb,
            "boxes": [], "doors": [], "trapdoors": [], "possessables": [], "lights": [], "suspects": [],
            "clueSpots": [], "trapPieces": [], "trapSite": None, "solverSpawns": [], "haunterSpawn": None,
            "rooms": [], "decor": [], "glows": [], "bounds": None, "floors": 1,
        }

    # -- primitives -------------------------------------------------------
    def box(self, name, p, s, color, level, mode="solid", tag="", shape="box", r=(0, 0, 0)):
        self.L["boxes"].append({"n": name, "t": shape, "p": r3(p), "s": r3(s), "r": [round(v, 2) for v in r],
                                "c": color, "m": mode, "l": level, "g": tag})

    def wall(self, name, axis, fixed, a0, a1, y0, h, level, color, thickness, openings=(), tag="wall", glass=None, trim=None):
        """axis 'x': runs along x at z=fixed; 'z': runs along z at x=fixed. openings: (centre, width, bottom, top, kind)."""
        glass = glass or rgb("ffcf7a")
        trim = trim or rgb("3b2f2a")

        def put(n, lo, hi, b_lo, b_hi, col=color, mode="solid", t=thickness):
            if hi - lo < 0.01 or b_hi - b_lo < 0.01:
                return
            mid, length = (lo + hi) / 2, hi - lo
            y, hh = y0 + (b_lo + b_hi) / 2, b_hi - b_lo
            if axis == "x":
                self.box(n, (mid, y, fixed), (length, hh, t), col, level, mode, tag)
            else:
                self.box(n, (fixed, y, mid), (t, hh, length), col, level, mode, tag)

        cur = a0
        for i, (c, w, lo, hi, kind) in enumerate(sorted(openings, key=lambda o: o[0])):
            put(f"{name}_seg{i}", cur, c - w / 2, 0, h)
            put(f"{name}_below{i}", c - w / 2, c + w / 2, 0, lo)
            put(f"{name}_above{i}", c - w / 2, c + w / 2, hi, h)
            if kind == "window":
                put(f"{name}_glass{i}", c - w / 2, c + w / 2, lo, hi, glass, "glass", 0.06)
                put(f"{name}_mullion{i}", c - 0.04, c + 0.04, lo, hi, trim, "solid", thickness + 0.04)
                put(f"{name}_sill{i}", c - w / 2 - 0.08, c + w / 2 + 0.08, lo - 0.08, lo, trim, "solid", thickness + 0.12)
            cur = c + w / 2
        put(f"{name}_end", cur, a1, 0, h)

    def slab(self, name, y_top, x0, x1, z0, z1, holes, color, level, thickness=0.25, tag="floor"):
        xs = sorted({x0, x1, *[v for h in holes for v in (h[0], h[1]) if x0 < v < x1]})
        zs = sorted({z0, z1, *[v for h in holes for v in (h[2], h[3]) if z0 < v < z1]})
        n = 0
        for i in range(len(xs) - 1):
            j = 0
            while j < len(zs) - 1:
                def solid(jj):
                    cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[jj] + zs[jj + 1]) / 2
                    return not any(h[0] < cx < h[1] and h[2] < cz < h[3] for h in holes)
                if not solid(j):
                    j += 1
                    continue
                k = j
                while k + 1 < len(zs) - 1 and solid(k + 1):
                    k += 1
                self.box(f"{name}_{n}", ((xs[i] + xs[i + 1]) / 2, y_top - thickness / 2, (zs[j] + zs[k + 1]) / 2),
                         (xs[i + 1] - xs[i], thickness, zs[k + 1] - zs[j]), color, level, "solid", tag)
                n += 1
                j = k + 1

    def stairs(self, name, x0, x1, z_start, y_base, steps, direction, level, color):
        """Straight stairs climbing along z (direction +1 or -1)."""
        for k in range(1, steps + 1):
            z_lo = z_start + (k - 1) * STEP_RUN * direction
            zc = z_lo + STEP_RUN * direction / 2
            top = y_base + k * STEP_RISE
            self.box(f"{name}{k}", ((x0 + x1) / 2, (y_base + top) / 2, zc), (x1 - x0, top - y_base, STEP_RUN), color, level, "solid", "stairs")

    def gable_roof(self, name, x0, x1, z0, z1, base, ridge, color, wall_color, level=2, overhang=0.5, tag="roof"):
        """A gable roof with the ridge along x, and stepped gable ends filling the triangles."""
        half = (z1 - z0) / 2 + overhang
        zc = (z0 + z1) / 2
        slope = math.hypot(half, ridge)
        ang = math.degrees(math.atan2(ridge, half))
        w = x1 - x0 + 2 * overhang
        xc = (x0 + x1) / 2
        self.box(f"{name}S", (xc, base + ridge / 2, zc - half / 2), (w, 0.25, slope), color, level, "solid", tag, r=(-ang, 0, 0))
        self.box(f"{name}N", (xc, base + ridge / 2, zc + half / 2), (w, 0.25, slope), color, level, "solid", tag, r=(ang, 0, 0))
        self.box(f"{name}Ridge", (xc, base + ridge + 0.05, zc), (w + 0.1, 0.2, 0.3), rgb("3b2f2a"), level, "solid", tag)
        steps = 8
        for i in range(steps):
            hw = (z1 - z0) / 2 * (1 - (i + 0.5) / steps)
            for side, x in (("W", x0), ("E", x1)):
                self.box(f"{name}Gable{side}{i}", (x, base + (i + 0.5) * ridge / steps, zc), (0.3, ridge / steps, 2 * hw),
                         wall_color, level, "solid", tag)

    def ceiling(self, name, y, x0, x1, z0, z1, color, level=2):
        self.box(name, ((x0 + x1) / 2, y + 0.1, (z0 + z1) / 2), (x1 - x0 + 0.4, 0.2, z1 - z0 + 0.4), color, level, "solid", "ceiling")

    def picket_fence(self, name, x0, x1, z0, z1, gate=(0, 1.6), color=None, level=9):
        color = color or rgb("efe9df")
        for side, (a0, a1, fixed, axis) in {"S": (x0, x1, z0, "x"), "N": (x0, x1, z1, "x"),
                                             "W": (z0, z1, x0, "z"), "E": (z0, z1, x1, "z")}.items():
            n = max(1, int((a1 - a0) / 0.5))
            for i in range(n + 1):
                a = a0 + i * (a1 - a0) / n
                if side == "S" and abs(a - gate[0]) < gate[1] / 2:
                    continue
                pos = (a, 0.5, fixed) if axis == "x" else (fixed, 0.5, a)
                self.box(f"{name}{side}{i}", pos, (0.09, 1.0, 0.09), color, level, "solid", "fence")
            for k, y in enumerate((0.3, 0.75)):
                if side == "S":
                    for part, (b0, b1) in enumerate(((a0, gate[0] - gate[1] / 2), (gate[0] + gate[1] / 2, a1))):
                        if b1 - b0 > 0.1:
                            self.box(f"{name}Rail{side}{k}{part}", ((b0 + b1) / 2, y, fixed), (b1 - b0, 0.06, 0.04), color, level, "nocollide", "fence")
                else:
                    mid, length = (a0 + a1) / 2, a1 - a0
                    pos, size = ((mid, y, fixed), (length, 0.06, 0.04)) if axis == "x" else ((fixed, y, mid), (0.04, 0.06, length))
                    self.box(f"{name}Rail{side}{k}", pos, size, color, level, "nocollide", "fence")

    def tree(self, name, x, z, h, leaves=None, level=9):
        """leaves=None: a bare, spooky tree. Otherwise a round autumn canopy of that colour."""
        bark = rgb("3a2c22")
        self.box(f"{name}Trunk", (x, h / 2, z), (0.5, h, 0.5), bark, level, "solid", "tree")
        if leaves:
            self.box(f"{name}Canopy", (x, h * 0.95, z), (h * 0.7, h * 0.55, h * 0.7), leaves, level, "nocollide", "tree", "sphere")
            self.box(f"{name}Canopy2", (x + h * 0.15, h * 0.8, z - h * 0.1), (h * 0.5, h * 0.4, h * 0.5), leaves, level, "nocollide", "tree", "sphere")
        else:
            for k, (ry, rz, y) in enumerate(((20, 40, 0.6), (140, 35, 0.75), (260, 45, 0.85))):
                length = h * 0.45
                ux, uy = -math.sin(math.radians(rz)), math.cos(math.radians(rz))
                dx, dz = ux * math.cos(math.radians(ry)), -ux * math.sin(math.radians(ry))
                self.box(f"{name}Branch{k}", (x + dx * length / 2, h * y + uy * length / 2, z + dz * length / 2), (0.2, length, 0.2),
                         bark, level, "nocollide", "tree", r=(0, ry, rz))

    # -- gameplay ---------------------------------------------------------
    def room(self, name, level, x0, x1, z0, z1, y0, y1):
        self.L["rooms"].append({"n": name, "l": level, "min": [x0, y0, z0], "max": [x1, y1, z1]})

    def possessable(self, name, shape, p, s, color, physics, level):
        self.L["possessables"].append({"n": name, "t": shape, "p": r3(p), "s": r3(s), "c": color, "phys": physics, "l": level})

    def light(self, name, p, color, rng, intensity, level, fixture_shape="cyl", fixture_offset=(0, -0.4, 0),
              fixture_size=(0.25, 0.8, 0.25), fixture_color=None):
        self.L["lights"].append({"n": name, "p": r3(p), "c": color, "range": rng, "intensity": intensity, "l": level,
                                 "ft": fixture_shape, "fo": list(fixture_offset), "fs": list(fixture_size),
                                 "fc": fixture_color or rgb("b08d3c")})

    def door(self, p, rot_y, width, level, name):
        self.L["doors"].append({"n": name, "p": r3(p), "ry": rot_y, "w": width, "h": DOOR_H, "l": level})

    def trapdoor(self, name, p, drop):
        self.L["trapdoors"].append({"n": name, "p": r3(p), "drop": r3(drop)})

    def suspect_spot(self, sid, p, ry=180):
        """Where a suspect waits when the call is at this house (the four suspects travel house to house)."""
        self.L["suspects"].append({"id": sid, "p": r3(p), "c": [1, 1, 1], "ry": ry})

    def clue(self, p):
        self.L["clueSpots"].append({"p": r3(p)})

    def trap_piece(self, p):
        self.L["trapPieces"].append({"p": r3(p)})

    def decor(self, kind, p, ry=0.0, sc=1.0, level=9):
        self.L["decor"].append({"k": kind, "p": r3(p), "ry": round(ry, 1), "sc": round(sc, 3), "l": level})

    def glow(self, p, color, rng, intensity, level=9):
        self.L["glows"].append({"p": r3(p), "c": color, "range": rng, "intensity": intensity, "l": level})

    # -- furniture --------------------------------------------------------
    def table(self, name, p, size, level, color, leg_color):
        x, y, z = p
        sx, h, sz = size
        self.box(name, (x, y + h - 0.05, z), (sx, 0.1, sz), color, level, "solid", "furniture")
        for dx in (-1, 1):
            for dz in (-1, 1):
                self.box(f"{name}_leg{dx}{dz}", (x + dx * (sx / 2 - 0.08), y + (h - 0.1) / 2, z + dz * (sz / 2 - 0.08)),
                         (0.08, h - 0.1, 0.08), leg_color, level, "solid", "furniture")

    def bed(self, name, p, level, frame, sheet, along_x=True, size=(2.0, 1.4)):
        x, y, z = p
        sx, sz = size if along_x else (size[1], size[0])
        self.box(name, (x, y + 0.25, z), (sx, 0.5, sz), frame, level, "solid", "furniture")
        self.box(f"{name}_sheet", (x, y + 0.55, z), (sx * 0.95, 0.12, sz * 0.95), sheet, level, "nocollide", "decor")
        hx, hz = (x - sx / 2, z) if along_x else (x, z + sz / 2)
        self.box(f"{name}_head", (hx, y + 0.65, hz), (0.12 if along_x else sx, 1.3, sz if along_x else 0.12), frame, level, "solid", "furniture")

    def save(self, filename, house=True):
        import dressing
        dressing.finish(self.L, house)
        xs = [b["p"][0] for b in self.L["boxes"]]
        zs = [b["p"][2] for b in self.L["boxes"]]
        self.L["bounds"] = {"min": [round(min(xs) - 1, 1), -4, round(min(zs) - 1, 1)], "max": [round(max(xs) + 1, 1), 30, round(max(zs) + 1, 1)]}
        path = os.path.join(RESOURCES, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.L, f, separators=(",", ":"))
        print(f"Wrote {os.path.relpath(path, ROOT)}: {len(self.L['boxes'])} boxes, {len(self.L['rooms'])} rooms, "
              f"{len(self.L['possessables'])} possessables, {len(self.L['decor'])} props")
        return path
