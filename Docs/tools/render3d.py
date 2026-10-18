#!/usr/bin/env python3
"""
A small software 3D renderer (numpy z-buffer, per-pixel lighting) that draws Blackwood Manor
straight from Assets/Unmasked/Resources/BlackwoodManor.json, the same file Unity builds the level
from. Used by make_images.py for the 3D pictures and animations in the README.

No GPU or Unity needed: python3 + numpy + Pillow.
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

try:
    from scipy.ndimage import uniform_filter as _box_blur
except ImportError:  # scipy is optional: a slower numpy box blur
    def _box_blur(a, size):
        k = size // 2
        p = np.pad(a, k, mode="edge")
        c = np.cumsum(np.cumsum(p, 0), 1)
        c = np.pad(c, ((1, 0), (1, 0)))
        return (c[size:, size:] - c[:-size, size:] - c[size:, :-size] + c[:-size, :-size]) / (size * size)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAYOUT_PATH = os.path.join(ROOT, "Assets", "Unmasked", "Resources", "BlackwoodManor.json")
COSTUMES_PATH = os.path.join(ROOT, "Assets", "Unmasked", "Resources", "Costumes.json")


def load_layout():
    with open(LAYOUT_PATH) as f:
        return json.load(f)


def load_costumes():
    """Villains, outfits and props (written by make_costumes.py), keyed by id."""
    with open(COSTUMES_PATH) as f:
        c = json.load(f)
    for key in ("villains", "props", "suspects", "solvers"):
        c[key] = {item["id"]: item for item in c[key]}
    return c


_COSTUMES = None


def costumes():
    global _COSTUMES
    if _COSTUMES is None:
        _COSTUMES = load_costumes()
    return _COSTUMES


TOWN_PATH = os.path.join(ROOT, "Assets", "Unmasked", "Resources", "HollowCreek.json")
_LIST_KEYS = ("boxes", "doors", "trapdoors", "possessables", "lights", "suspects", "decor", "glows", "clueSpots", "trapPieces")


def shift_layout(L, off):
    """A copy of a house layout moved by off (x, y, z): where it sits in town."""
    ox, oy, oz = off
    out = dict(L)
    for key in _LIST_KEYS:
        items = []
        for item in L.get(key, []):
            item = dict(item)
            item["p"] = [item["p"][0] + ox, item["p"][1] + oy, item["p"][2] + oz]
            if "drop" in item:
                item["drop"] = [item["drop"][0] + ox, item["drop"][1] + oy, item["drop"][2] + oz]
            items.append(item)
        out[key] = items
    return out


def load_town():
    """Hollow Creek and every house on its lot, merged into one layout. Returns (merged, town, houses)."""
    with open(TOWN_PATH) as f:
        town = json.load(f)
    houses = []
    merged = {k: list(town.get(k, [])) for k in _LIST_KEYS}
    merged["name"] = town["name"]
    for lot in town["lots"]:
        with open(os.path.join(ROOT, "Assets", "Unmasked", "Resources", lot["resource"] + ".json")) as f:
            H = shift_layout(json.load(f), lot["offset"])
        for sp in H.get("suspects", []):
            sp["house"] = lot["id"]  # each house's suspects wear that house's outfits
        houses.append((lot, H))
        for k in _LIST_KEYS:
            merged[k] += H.get(k, [])
    return merged, town, houses


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
def euler(rx, ry, rz):
    """Unity's Euler rotation (applied z, then x, then y)."""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


_UNIT_BOX = np.array([[x, y, z] for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)])
_BOX_FACES = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]


def _prism(n, radius_top=1.0, radius_bottom=1.0, y0=-1.0, y1=1.0):
    verts, faces = [], []
    for k in range(n):
        a = 2 * math.pi * k / n
        verts.append([radius_bottom * math.cos(a) * .5, y0 * .5, radius_bottom * math.sin(a) * .5])
    for k in range(n):
        a = 2 * math.pi * k / n
        verts.append([radius_top * math.cos(a) * .5, y1 * .5, radius_top * math.sin(a) * .5])
    for k in range(n):
        j = (k + 1) % n
        faces.append((k, j, n + j, n + k))
    faces.append(tuple(range(n - 1, -1, -1)))
    faces.append(tuple(range(n, 2 * n)))
    return np.array(verts), faces


_CYL = _prism(14, y0=-2, y1=2)  # Unity cylinder: height 2 at scale 1
_PYR = _prism(4, radius_top=0.0, radius_bottom=2 ** 0.5 * 2, y0=0, y1=2)  # Horizon.cs pyramid: base half-size 1 at y 0, apex at y 1


def _capsule(n=12):
    verts, faces = [], []
    rings = [(-1.0, 0.0), (-0.9, 0.62), (-0.7, 0.95), (-0.5, 1.0), (0.5, 1.0), (0.7, 0.95), (0.9, 0.62), (1.0, 0.0)]
    for y, r in rings:
        for k in range(n):
            a = 2 * math.pi * k / n
            verts.append([r * math.cos(a) * .5, y, r * math.sin(a) * .5])
    for i in range(len(rings) - 1):
        for k in range(n):
            j = (k + 1) % n
            faces.append((i * n + k, i * n + j, (i + 1) * n + j, (i + 1) * n + k))
    return np.array(verts), faces


_CAPSULE = _capsule()


def _sphere(seg=10, rings=6):
    verts, faces = [[0, -0.5, 0]], []
    for i in range(1, rings):
        phi = math.pi * i / rings - math.pi / 2
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append([0.5 * math.cos(phi) * math.cos(a), 0.5 * math.sin(phi), 0.5 * math.cos(phi) * math.sin(a)])
    verts.append([0, 0.5, 0])
    top = len(verts) - 1
    for k in range(seg):
        faces.append((0, 1 + (k + 1) % seg, 1 + k))
    for i in range(rings - 2):
        for k in range(seg):
            j = (k + 1) % seg
            a, b = 1 + i * seg, 1 + (i + 1) * seg
            faces.append((a + k, a + j, b + j, b + k))
    last = 1 + (rings - 2) * seg
    for k in range(seg):
        faces.append((last + k, last + (k + 1) % seg, top))
    return np.array(verts), faces


_SPHERE = _sphere()
_LOW = (_CYL, _CAPSULE, _SPHERE)
_HIGH = None


class detail:
    """with r3.detail(True): rounder spheres, capsules and cylinders for close-ups (Unity's are smooth)."""

    def __init__(self, on=True):
        self.on = on

    def __enter__(self):
        global _CYL, _CAPSULE, _SPHERE, _HIGH
        if self.on:
            if _HIGH is None:
                _HIGH = (_prism(28, y0=-2, y1=2), _capsule(24), _sphere(24, 14))
            _CYL, _CAPSULE, _SPHERE = _HIGH
        return self

    def __exit__(self, *exc):
        global _CYL, _CAPSULE, _SPHERE
        _CYL, _CAPSULE, _SPHERE = _LOW


# ---------------------------------------------------------------------------
# Surfaces: the same tileable patterns the game's shader uses (make_textures.py)
# ---------------------------------------------------------------------------
SURFACE_NAMES = ["", "siding", "shingle", "shingle_z", "brick", "stone", "planks", "planks_z", "grass", "road", "gravel",
                 "plaster", "bark", "leaf", "water"]
SURFACE_ID = {n: i for i, n in enumerate(SURFACE_NAMES)}
_SURF = None


def surfaces():
    """id -> (mip pyramid, tile metres, strength, swap top) from Assets/Unmasked/Textures/Surfaces."""
    global _SURF
    if _SURF is None:
        _SURF = {}
        folder = os.path.join(ROOT, "Assets", "Unmasked", "Textures", "Surfaces")
        try:
            with open(os.path.join(folder, "surfaces.json")) as f:
                meta = {m["id"]: m for m in json.load(f)["surfaces"]}
        except OSError:
            meta = {}
        for name, m in meta.items():
            if name not in SURFACE_ID:
                continue
            img = np.asarray(Image.open(os.path.join(folder, m["texture"] + ".png")).convert("L"), dtype=float) / 255.0
            mips = [img]
            while mips[-1].shape[0] > 4:
                a = mips[-1]
                mips.append((a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]) / 4)
            _SURF[SURFACE_ID[name]] = (mips, m["tile"], m["strength"], m["swapTop"])
    return _SURF


def apply_surfaces(alb, pos, nor, sid, depth, pixel_angle):
    """Multiplies each pixel's colour by its surface pattern, sampled in world space like the shader."""
    table = surfaces()
    if not table:
        return alb
    out = alb.copy()
    for k in np.unique(sid):
        if k == 0 or k not in table:
            continue
        mips, tile, strength, swap = table[k]
        mask = sid == k
        P, N, D = pos[mask], np.abs(nor[mask]), depth[mask]
        ax = np.argmax(N, axis=1)
        u = np.where(ax == 0, P[:, 2], P[:, 0])
        v = np.where(ax == 1, P[:, 2], P[:, 1])
        if swap:
            u, v = np.where(ax == 1, P[:, 2], u), np.where(ax == 1, P[:, 0], v)
        n0 = mips[0].shape[0]
        footprint = D * pixel_angle / (tile / n0)
        level = np.clip(np.log2(np.maximum(footprint, 1e-6)), 0, len(mips) - 1).astype(int)
        val = np.empty(len(u))
        for lv in np.unique(level):
            sel = level == lv
            tex = mips[lv]
            n = tex.shape[0]
            iu = (np.floor(u[sel] / tile * n).astype(int)) % n
            iv = (np.floor(-v[sel] / tile * n).astype(int)) % n
            val[sel] = tex[iv, iu]
        mult = 1 + strength * (2 * val - 1)
        out[mask] = alb[mask] * mult[:, None]
    return out


class Mesh:
    """Triangles with per-triangle colour, emission, and surface pattern."""

    def __init__(self):
        self.tris, self.cols, self.emit, self.surf, self.vnor = [], [], [], [], []

    def add(self, verts, faces, color, emissive=0.0, surface=0, normals=None):
        """normals: one per vertex for smooth shading (spheres, capsules), else each face is flat."""
        color = np.array(color, dtype=float)
        center = verts.mean(axis=0)
        for f in faces:
            for k in range(1, len(f) - 1):
                idx = [f[0], f[k], f[k + 1]]
                tri = verts[idx]
                # make the winding face outwards
                n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
                if np.dot(n, tri.mean(axis=0) - center) < 0:
                    idx = idx[::-1]
                    tri = verts[idx]
                    n = -n
                if normals is None:
                    vn = np.repeat((n / (np.linalg.norm(n) + 1e-12))[None, :], 3, axis=0)
                else:
                    vn = normals[idx]
                self.tris.append(tri)
                self.vnor.append(vn)
                self.cols.append(color)
                self.emit.append(emissive)
                self.surf.append(surface)

    def add_shape(self, shape, p, s, r=(0, 0, 0), color=(1, 1, 1), emissive=0.0, parent=None, surface=0):
        """parent: (rotation matrix, position, scale) of a group the shape sits in."""
        if shape == "cyl":
            v, f = _CYL
        elif shape == "capsule":
            v, f = _CAPSULE
        elif shape == "sphere":
            v, f = _SPHERE
        elif shape == "pyr":
            v, f = _PYR
        else:
            v, f = _UNIT_BOX, _BOX_FACES
        E = euler(*r)
        verts = (v * np.array(s)) @ E.T + np.array(p)
        normals = None
        if shape in ("sphere", "capsule"):
            local = v.copy()
            if shape == "capsule":  # hemispheres centred at y = +-0.5, straight sides between
                local[:, 1] = v[:, 1] - np.clip(v[:, 1], -0.5, 0.5)
            normals = (local / np.maximum(np.abs(np.array(s, dtype=float)), 1e-4)) @ E.T
        if parent is not None:
            R, pos, scale = parent
            verts = (verts * scale) @ R.T + np.array(pos)
            if normals is not None:
                normals = normals @ R.T
        if normals is not None:
            normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-12
        self.add(verts, f, color, emissive, surface, normals)

    def add_parts(self, parts, pos=(0, 0, 0), ry=0.0, scale=1.0, skip_mask=False, mask_motion=None, tint=None):
        """
        Adds a costume or prop from Costumes.json. mask_motion: (offset, rotation) applied to the
        mask parts, for the unmasking animation.
        """
        R = euler(0, ry, 0)
        for q in parts:
            if q["k"] == "mask" and skip_mask:
                continue
            e = q["e"] if q["m"] == "emissive" else (0.3 * q["e"] if q["m"] == "ghost" else 0.0)
            col = q["c"] if tint is None else tint
            p, r = q["p"], q["r"]
            if q["k"] == "mask" and mask_motion is not None:
                off, rot = mask_motion
                p = [p[i] + off[i] for i in range(3)]
                r = [r[i] + rot[i] for i in range(3)]
            self.add_shape(q["t"], p, q["s"], r, col, e, (R, pos, scale))

    def arrays(self):
        return np.array(self.tris), np.array(self.cols), np.array(self.emit), np.array(self.surf, dtype=int)

    def vertex_normals(self):
        return np.array(self.vnor)


def suspect_outfit(slot, house=None):
    """What a suspect slot wears at a house (make_costumes.py HOUSE_SUSPECTS), else the Blackwood cast's outfit."""
    outfits = costumes()["suspects"]
    return outfits.get(f"{house}.{slot}", outfits[slot])["parts"]


def layout_mesh(L, levels=None, cut_level=None, cut_height=1.3, roof=True, doors=True, grounds=True, window_glow=0.9, extra=None):
    """
    Builds the manor mesh. levels: which levels to include (None = all). cut_level: walls on that
    level are cut down to cut_height, dollhouse style, so you can see into the rooms.
    """
    m = Mesh()
    for b in L["boxes"]:
        lvl = b["l"]
        if levels is not None and lvl not in levels:
            continue
        if not roof and b["g"] in ("roof", "ceiling"):
            continue
        if not grounds and lvl == 9 and b["g"] not in ("ground",):
            continue
        p, s = list(b["p"]), list(b["s"])
        if cut_level is not None and lvl == cut_level and b["g"] in ("wall", "trim"):
            base = {-1: -3.5, 0: 0.0, 1: L.get("storey", 3.5)}.get(lvl, 0.0)
            top = min(p[1] + s[1] / 2, base + cut_height)
            bottom = p[1] - s[1] / 2
            if top <= bottom:
                continue
            p[1], s[1] = (top + bottom) / 2, top - bottom
        emissive = window_glow if b["m"] == "glass" else 0.0
        m.add_shape(b["t"], p, s, b["r"], b["c"], emissive, surface=SURFACE_ID.get(b.get("sf", ""), 0))
    for item in L["possessables"]:
        if levels is None or item["l"] in levels:
            m.add_shape(item["t"], item["p"], item["s"], (0, 0, 0), item["c"])
    for lt in L["lights"]:
        if levels is None or lt["l"] in levels:
            fp = [lt["p"][i] + lt["fo"][i] for i in range(3)]
            m.add_shape(lt["ft"], fp, lt["fs"], (0, 0, 0), lt["fc"])
            m.add_shape("box", lt["p"], (0.18, 0.18, 0.18), (0, 0, 0), lt["c"], 1.5)
    if doors:
        for d in L["doors"]:
            if levels is not None and d["l"] not in levels:
                continue
            if cut_level is not None and d["l"] == cut_level:
                continue  # leave doorways open in cutaways
            R = euler(0, d["ry"], 0)
            local = np.array([0, d["h"] / 2, d["w"] / 2])
            p = np.array(d["p"]) + R @ local
            m.add_shape("box", p, (0.1, d["h"], d["w"]), (0, d["ry"], 0), (0.42, 0.25, 0.13))
            if d["n"] == "Door_Front":  # a harvest wreath on every front door (ManorBuilder does the same)
                wp = np.array(d["p"]) + R @ np.array([0.09, 1.6, d["w"] / 2])
                m.add_parts(costumes()["props"]["wreath"]["parts"], wp, d["ry"] + 90, 0.8)
    for t in L["trapdoors"]:
        if levels is None or (0 if t["p"][1] < 1 else 1) in levels:
            m.add_shape("box", (t["p"][0], t["p"][1] + 0.02, t["p"][2]), (1.8, 0.04, 1.8), (0, 0, 0), (0.35, 0.2, 0.1))
    for sp in L["suspects"]:
        lvl = -1 if sp["p"][1] < -1 else (1 if sp["p"][1] > 2 else 0)
        if levels is None or lvl in levels or (lvl == 0 and 9 in levels and abs(sp["p"][0]) > 17):
            m.add_parts(suspect_outfit(sp["id"], sp.get("house") or L.get("id")), sp["p"], sp.get("ry", 180))
    props = costumes()["props"]
    for d in L.get("decor", []):
        if levels is not None and d["l"] not in levels:
            continue
        if cut_level is not None and d["l"] == cut_level and d["k"] == "cobweb":
            continue
        m.add_parts(props[d["k"]]["parts"], d["p"], d["ry"], d["sc"])
    if extra:
        for e in extra:
            m.add_shape(*e)
    return m


def all_lights(L, levels=None):
    """Possessable lamps plus the decorative glows (jack-o'-lanterns, candles, wisps)."""
    out = [lt for lt in L["lights"] if levels is None or lt["l"] in levels]
    out += [g for g in L.get("glows", []) if levels is None or g["l"] in levels]
    return out


# ---------------------------------------------------------------------------
# Camera and rasterizer
# ---------------------------------------------------------------------------
class Camera:
    def __init__(self, pos, target, fov=50.0, width=800, height=450, ortho=None):
        self.pos, self.target = np.array(pos, float), np.array(target, float)
        self.fov, self.w, self.h, self.ortho = fov, width, height, ortho
        f = self.target - self.pos
        self.f = f / np.linalg.norm(f)
        r = np.cross([0, 1, 0], self.f)
        self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.f, self.r)
        self.focal = (height / 2) / math.tan(math.radians(fov) / 2)

    def to_view(self, P):
        d = P - self.pos
        return np.stack([d @ self.r, d @ self.u, d @ self.f], axis=-1)

    def project(self, P):
        v = self.to_view(np.atleast_2d(np.array(P, float)))
        if self.ortho:
            scale = self.h / self.ortho
            sx = self.w / 2 + v[:, 0] * scale
            sy = self.h / 2 - v[:, 1] * scale
        else:
            z = np.maximum(v[:, 2], 1e-3)
            sx = self.w / 2 + v[:, 0] / z * self.focal
            sy = self.h / 2 - v[:, 1] / z * self.focal
        return np.stack([sx, sy, v[:, 2]], axis=-1)


def _corner_normals(orig, N, T):
    """Normals at the corners of T (a piece of triangle orig) by barycentric weights."""
    a, b, c = orig
    v0, v1 = b - a, c - a
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    den = d00 * d11 - d01 * d01 + 1e-12
    out = []
    for p in T:
        v2 = p - a
        d20, d21 = v2 @ v0, v2 @ v1
        wb = (d11 * d20 - d01 * d21) / den
        wc = (d00 * d21 - d01 * d20) / den
        out.append((1 - wb - wc) * N[0] + wb * N[1] + wc * N[2])
    return np.array(out)


def _clip_near(T, V, near):
    """Clips one triangle against the near plane. Returns a list of (world, view) triangles."""
    poly = list(zip(T, V))
    out = []
    for i in range(len(poly)):
        (pa, va), (pb, vb) = poly[i], poly[(i + 1) % len(poly)]
        ina, inb = va[2] >= near, vb[2] >= near
        if ina:
            out.append((pa, va))
        if ina != inb:
            t = (near - va[2]) / (vb[2] - va[2])
            out.append((pa + (pb - pa) * t, va + (vb - va) * t))
    return [(np.array([out[0][0], out[k][0], out[k + 1][0]]), np.array([out[0][1], out[k][1], out[k + 1][1]]))
            for k in range(1, len(out) - 1)]


def empty_gbuffer(W, H):
    return [np.full((H, W), np.inf), np.zeros((H, W, 3)), np.zeros((H, W, 3)), np.zeros((H, W, 3)), np.zeros((H, W)),
            np.zeros((H, W), dtype=int)]


def rasterize(cam, mesh, base=None):
    """
    Returns G-buffers: depth, world position, normal, albedo, emission, surface id (all H x W).
    base: G-buffers to draw on top of (a copy is made), e.g. the static level rendered once.
    """
    W, H = cam.w, cam.h
    if base is None:
        depth, pos, nor, alb, emi, sid = empty_gbuffer(W, H)
    else:
        depth, pos, nor, alb, emi, sid = [b.copy() for b in base]
    if not mesh.tris:
        return depth, pos, nor, alb, emi, sid
    tris, cols, emit, surf = mesh.arrays()
    vnor = mesh.vertex_normals()
    smooth = np.abs(vnor - vnor[:, :1]).max(axis=(1, 2)) > 1e-6
    near = 0.15

    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-12
    centers = tris.mean(axis=1)
    if cam.ortho:
        facing = normals @ cam.f < 0
    else:
        facing = np.einsum("ij,ij->i", normals, centers - cam.pos) < 0
    view = cam.to_view(tris.reshape(-1, 3)).reshape(-1, 3, 3)
    keep = facing & (view[:, :, 2].max(axis=1) > near)
    jobs = []
    for idx in np.nonzero(keep)[0]:
        if (view[idx][:, 2] < near).any():
            jobs += [(idx, T, V, True) for T, V in _clip_near(tris[idx], view[idx], near)]
        else:
            jobs.append((idx, tris[idx], view[idx], False))
    for idx, T, V, clipped in jobs:
        if cam.ortho:
            scale = H / cam.ortho
            sx = W / 2 + V[:, 0] * scale
            sy = H / 2 - V[:, 1] * scale
        else:
            sx = W / 2 + V[:, 0] / V[:, 2] * cam.focal
            sy = H / 2 - V[:, 1] / V[:, 2] * cam.focal
        x0, x1 = int(max(0, math.floor(sx.min()))), int(min(W - 1, math.ceil(sx.max())))
        y0, y1 = int(max(0, math.floor(sy.min()))), int(min(H - 1, math.ceil(sy.max())))
        if x0 > x1 or y0 > y1:
            continue
        area = (sx[1] - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (sy[1] - sy[0])
        if abs(area) < 1e-9:
            continue
        xs = np.arange(x0, x1 + 1) + 0.5
        ys = np.arange(y0, y1 + 1)[:, None] + 0.5
        w0 = ((sx[1] - xs) * (sy[2] - ys) - (sx[2] - xs) * (sy[1] - ys)) / area
        w1 = ((sx[2] - xs) * (sy[0] - ys) - (sx[0] - xs) * (sy[2] - ys)) / area
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        if cam.ortho:
            z = w0 * V[0, 2] + w1 * V[1, 2] + w2 * V[2, 2]
            P = w0[..., None] * T[0] + w1[..., None] * T[1] + w2[..., None] * T[2]
        else:
            iz = w0 / V[0, 2] + w1 / V[1, 2] + w2 / V[2, 2]
            z = 1 / iz
            P = (w0[..., None] * T[0] / V[0, 2] + w1[..., None] * T[1] / V[1, 2] + w2[..., None] * T[2] / V[2, 2]) * z[..., None]
        sub = depth[y0:y1 + 1, x0:x1 + 1]
        win = inside & (z < sub)
        if not win.any():
            continue
        sub[win] = z[win]
        pos[y0:y1 + 1, x0:x1 + 1][win] = P[win]
        if smooth[idx]:
            # the clipped triangle T has its own corners: weights back onto the original triangle
            N = vnor[idx]
            if clipped:
                N = _corner_normals(tris[idx], N, T)
            nn = w0[win][:, None] * N[0] + w1[win][:, None] * N[1] + w2[win][:, None] * N[2]
            nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12
            nor[y0:y1 + 1, x0:x1 + 1][win] = nn
        else:
            nor[y0:y1 + 1, x0:x1 + 1][win] = normals[idx]
        alb[y0:y1 + 1, x0:x1 + 1][win] = cols[idx]
        emi[y0:y1 + 1, x0:x1 + 1][win] = emit[idx]
        sid[y0:y1 + 1, x0:x1 + 1][win] = surf[idx]
    return depth, pos, nor, alb, emi, sid


# ---------------------------------------------------------------------------
# Shading
# ---------------------------------------------------------------------------
def sky(W, H, seed=4, moon=None):
    """Halloween night sky: deep indigo fading to a plum and ember horizon, stars. moon: (x, y, radius)."""
    y = np.linspace(0, 1, H)[:, None, None]
    top, mid, bottom = np.array([0.02, 0.015, 0.07]), np.array([0.10, 0.05, 0.20]), np.array([0.30, 0.12, 0.20])
    img = np.where(y < 0.6, top + (mid - top) * (y / 0.6), mid + (bottom - mid) * ((y - 0.6) / 0.4))
    img = np.repeat(img, W, axis=1)
    rng = np.random.default_rng(seed)
    for _ in range(W * H // 2500):
        sx, sy = rng.integers(0, W), rng.integers(0, int(H * 0.6))
        img[sy, sx] = rng.uniform(0.5, 1.0)
    if moon:
        mx, my, mr = moon
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
        halo = np.clip(1 - d / (mr * 4), 0, 1) ** 2 * 0.35
        img = img + halo[..., None] * np.array([0.6, 0.65, 0.9])
        disc = np.clip(mr + 1 - d, 0, 1)[..., None]
        img = img * (1 - disc) + disc * np.array([0.98, 0.96, 0.88])
    return img


def toon(x, bands=3):
    """Cel-shading: light falls off in soft steps instead of a smooth gradient (like the Unity shader)."""
    b = x * bands
    return (np.floor(b) + np.clip((b - np.floor(b) - 0.4) / 0.2, 0, 1)) / bands


def shade(gbuf, lights, cam, moon_dir=(0.37, -0.77, 0.52), ambient=(0.10, 0.08, 0.17), moon=(0.34, 0.30, 0.60),
          fog=(0.10, 0.05, 0.15), fog_density=0.012, light_boost=1.0, background=None, cel=True,
          rim=(0.42, 0.30, 0.75), rim_strength=0.35, ao=0.5, textures=True):
    depth, pos, nor, alb, emi, sid = gbuf
    H, W = depth.shape
    hit = np.isfinite(depth)
    if textures:
        pixel_angle = (cam.ortho / H) if cam.ortho else 1.0 / cam.focal
        dist_for_mip = np.where(hit, 1.0 if cam.ortho else depth, 0)
        alb = apply_surfaces(alb, pos, nor, sid, dist_for_mip, pixel_angle)
    md = -np.array(moon_dir) / np.linalg.norm(moon_dir)
    lam = np.clip(nor @ md, 0, 1)
    if cel:
        lam = toon(lam)
    lam = lam[..., None]
    up = np.clip(nor[..., 1:2], 0, 1)
    color = alb * (np.array(ambient) * (0.7 + 0.6 * up) + np.array(moon) * lam)
    if not hit.any():
        lights = []
    for lt in lights:
        lp = np.array(lt["p"], float)
        rng = lt["range"]
        # only touch the pixels this light can reach: its sphere's box on screen
        x0, x1, y0, y1 = 0, W, 0, H
        v = cam.to_view(lp[None, :])[0]
        if cam.ortho:
            sc = H / cam.ortho
            cx, cy, rad = W / 2 + v[0] * sc, H / 2 - v[1] * sc, rng * sc
            x0, x1, y0, y1 = int(cx - rad) - 1, int(cx + rad) + 2, int(cy - rad) - 1, int(cy + rad) + 2
        elif v[2] > rng:
            cx, cy = W / 2 + v[0] / v[2] * cam.focal, H / 2 - v[1] / v[2] * cam.focal
            rad = rng * cam.focal / (v[2] - rng) * 1.05
            x0, x1, y0, y1 = int(cx - rad) - 1, int(cx + rad) + 2, int(cy - rad) - 1, int(cy + rad) + 2
        elif v[2] < -rng:
            continue
        x0, x1, y0, y1 = max(0, x0), min(W, x1), max(0, y0), min(H, y1)
        if x0 >= x1 or y0 >= y1:
            continue
        sub = (slice(y0, y1), slice(x0, x1))
        d = lp - pos[sub]
        dist = np.linalg.norm(d, axis=-1) + 1e-6
        near = hit[sub] & (dist < rng)
        if not near.any():
            continue
        ndl = np.clip(np.einsum("hwc,hwc->hw", nor[sub], d) / dist, 0, 1)
        att = np.clip(1 - dist / rng, 0, 1) ** 2
        k = ndl * att * near
        if cel:
            k = toon(np.clip(k * 1.4, 0, 1), 4) / 1.4
        color[sub] += alb[sub] * (np.array(lt["c"]) * lt["intensity"] * light_boost * 1.6)[None, None, :] * k[..., None]
    if rim_strength:
        view = cam.pos - pos
        view /= np.linalg.norm(view, axis=-1, keepdims=True) + 1e-6
        fres = (1 - np.clip(np.einsum("hwc,hwc->hw", nor, view), 0, 1)) ** 3
        color += np.array(rim) * (rim_strength * fres)[..., None] * (0.4 + 0.6 * alb)
    if ao:
        # Screen-space ambient occlusion: pixels farther away than their neighbours sit in a corner or crease.
        dd = np.where(hit, depth, 1e4)
        size = max(5, int(W / 90) | 1)
        blurred = _box_blur(dd, size)
        rel = (dd - blurred) / np.maximum(dd, 1e-3)
        occl = np.clip(rel * 30, 0, 1) * ao
        color = color * (1 - occl[..., None])
    color += alb * emi[..., None]
    if fog_density:
        f = 1 - np.exp(-np.where(hit, depth, 0) * fog_density)
        color = color * (1 - f[..., None]) + np.array(fog) * f[..., None]
    bg = background if background is not None else sky(W, H)
    out = np.where(hit[..., None], color, bg)
    return np.clip(out, 0, 1)


def to_image(arr, glow=True):
    img = Image.fromarray((np.clip(arr, 0, 1) ** (1 / 1.15) * 255).astype(np.uint8))
    if glow:
        bright = img.point(lambda v: max(0, v - 170) * 3).filter(ImageFilter.GaussianBlur(radius=max(2, img.width // 200)))
        img = Image.fromarray(np.clip(np.asarray(img, dtype=np.int32) + np.asarray(bright, dtype=np.int32) // 2, 0, 255).astype(np.uint8))
    return img


def big_camera(cam, ss=2):
    return Camera(cam.pos, cam.target, cam.fov, cam.w * ss, cam.h * ss, cam.ortho)


MOON_DIR = (-0.45, 0.32, 1.0)


def render(L, cam, mesh, ss=2, base=None, overlay=None, moon=True, extra_mesh=None, moon_color=None, horizon=None, horizon_t=0.0, **shade_args):
    """
    base: cached G-buffers of the static scene (from rasterize(big_camera(cam), ...)).
    extra_mesh: moving things drawn on top (bats, characters).
    moon: draw the moon disc in the sky. moon_color: the moonlight's colour (shade's "moon").
    horizon: the town (HollowCreek.json) whose far hills, lights and landmarks to paint behind the scene.
    """
    if moon_color is not None:
        shade_args["moon"] = moon_color
    big = big_camera(cam, ss)
    gbuf = rasterize(big, mesh, base)
    if extra_mesh is not None:
        gbuf = rasterize(big, extra_mesh, gbuf)
    if "background" not in shade_args:
        disc = None
        if moon:
            d = np.array(MOON_DIR) / np.linalg.norm(MOON_DIR)
            sp = big.project(big.pos + d * 1000)[0]
            if sp[2] > 0:
                disc = (sp[0], sp[1], 0.045 * big.h)
        shade_args["background"] = sky(big.w, big.h, moon=disc)
        if horizon is not None:
            shade_args["background"] = horizon_sky(shade_args["background"], big, horizon, horizon_t)
    lights = shade_args.pop("lights", None)
    if lights is None:
        lights = all_lights(L)
    arr = shade(gbuf, lights, big, **shade_args)
    img = to_image(arr)
    if overlay:
        overlay(img, big)
    return img.resize((cam.w, cam.h), Image.LANCZOS)


def draw_moon(img, cam, direction=(-0.45, 0.35, 1.0), radius=26):
    """Paints the moon in screen space where the sky shows (cheap but looks right)."""
    d = np.array(direction, float)
    p = cam.pos + d / np.linalg.norm(d) * 500
    s = cam.project(p)[0]
    if s[2] <= 0:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    x, y = s[0], s[1]
    for k, a in ((3.0, 25), (2.0, 45)):
        dr.ellipse([x - radius * k, y - radius * k, x + radius * k, y + radius * k], fill=(200, 210, 255, a))
    dr.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(250, 246, 225, 255))
    layer = layer.filter(ImageFilter.GaussianBlur(1))
    base = img.convert("RGBA")
    # Only show the moon over sky-coloured (dark, bluish) pixels: a rough occlusion test.
    arr = np.asarray(base).astype(np.int32)
    skyish = (arr[..., 2] > arr[..., 0]) & (arr[..., :3].sum(axis=-1) < 160)
    la = np.asarray(layer).copy()
    la[..., 3] = la[..., 3] * skyish
    return Image.alpha_composite(base, Image.fromarray(la)).convert("RGB")


# ---------------------------------------------------------------------------
# Beyond the edge of town (the same data and maths as Assets/Unmasked/Scripts/Town/Horizon.cs)
# ---------------------------------------------------------------------------
class Lcg:
    """The same tiny random number generator as Horizon.cs, so lights and trees land in the same places."""

    def __init__(self, seed):
        self.state = (seed * 2654435761 + 1) & 0xFFFFFFFF

    def next(self):
        self.state = (self.state * 1664525 + 1013904223) & 0xFFFFFFFF
        return (self.state >> 8) / 16777216.0

    def range(self, a, b):
        return a + (b - a) * self.next()


def ring_height(ring, angle_deg):
    h, w = ring["base"], ring["waves"]
    for i in range(0, len(w) - 2, 3):
        h += w[i] * np.sin(w[i + 1] * np.radians(angle_deg) + w[i + 2])
    return h


def _on_ring(cx, cz, radius, angle_deg, y):
    a = np.radians(angle_deg)
    return np.stack([cx + np.sin(a) * radius, np.broadcast_to(y, np.shape(a)), cz + np.cos(a) * radius], axis=-1)


def _near_road(h, x, z, margin):
    for r in h.get("roads", []):
        a, b = np.array(r["from"], float), np.array(r["to"], float)
        ab, p = b - a, np.array([x, z])
        t = np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1)
        if np.linalg.norm(p - (a + ab * t)) < h["roadWidth"] / 2 + margin:
            return True
    return False


def horizon_mesh(town, m=None):
    """The near, solid part: road extensions with lamps and signposts, the forest band and the far fields."""
    h = town["horizon"]
    m = m or Mesh()
    road, dash, pole, bulb = (0.13, 0.12, 0.13), (0.75, 0.68, 0.45), (0.12, 0.1, 0.1), (1.0, 0.8, 0.45)
    for r in h.get("roads", []):
        a, b = np.array(r["from"], float), np.array(r["to"], float)
        d = b - a
        length = float(np.linalg.norm(d))
        ry = math.degrees(math.atan2(d[0], d[1]))
        mid = (a + b) / 2
        m.add_shape("box", (mid[0], -0.02, mid[1]), (h["roadWidth"], 0.04, length), (0, ry, 0), road)
        u = d / length
        side = np.array([u[1], -u[0]])
        for k in range(int(length // 8)):
            c = a + u * (k * 8 + 4)
            m.add_shape("box", (c[0], 0.01, c[1]), (0.2, 0.02, 3.0), (0, ry, 0), dash)
        for k in range(1, int(length // h["lampEvery"])):
            c = a + u * k * h["lampEvery"] + side * (h["roadWidth"] / 2 + 0.8) * (1 if k % 2 else -1)
            m.add_shape("box", (c[0], 2.3, c[1]), (0.18, 4.6, 0.18), (0, 0, 0), pole)
            m.add_shape("box", (c[0], 4.7, c[1]), (0.5, 0.35, 0.5), (0, 0, 0), bulb, 1.6)
        if r.get("sign"):
            c = a + u * 14 + side * (h["roadWidth"] / 2 + 2)
            m.add_shape("box", (c[0], 1.2, c[1]), (0.18, 2.4, 0.18), (0, 0, 0), (0.3, 0.2, 0.12))
            m.add_shape("box", (c[0], 2.3, c[1]), (2.8, 0.7, 0.1), (0, ry, 0), (0.85, 0.75, 0.55))
    f = h.get("forest")
    if f:
        rng = Lcg(f["seed"])
        x0, z0, x1, z1 = f["town"]
        crowns = [(0.12, 0.2, 0.14), (0.55, 0.27, 0.1), (0.4, 0.12, 0.1)]
        placed = 0
        for _ in range(f["count"] * 3):
            if placed >= f["count"]:
                break
            x = rng.range(x0 - f["outer"], x1 + f["outer"])
            z = rng.range(z0 - f["outer"], z1 + f["outer"])
            dx = max(x0 - f["inner"] - x, 0.0, x - (x1 + f["inner"]))
            dz = max(z0 - f["inner"] - z, 0.0, z - (z1 + f["inner"]))
            kind, height = rng.next(), rng.range(9.0, 18.0)
            if dx <= 0 and dz <= 0:
                continue
            if _near_road(h, x, z, 9.0):
                continue
            m.add_shape("box", (x, height * 0.2, z), (0.5, height * 0.4, 0.5), (0, 0, 0), (0.22, 0.15, 0.1))
            col = crowns[0 if kind < 0.55 else 1 if kind < 0.82 else 2]
            m.add_shape("pyr", (x, height * 0.25, z), (height * 0.32, height * 0.55, height * 0.32), (0, 45, 0), col)
            m.add_shape("pyr", (x, height * 0.55, z), (height * 0.24, height * 0.45, height * 0.24), (0, 45, 0), col)
            placed += 1
    r = max(ring["radius"] for ring in h["rings"])
    m.add_shape("box", (0, -0.09, 100), (2 * r, 0.04, 2 * r), (0, 0, 0), (0.15, 0.2, 0.12))
    return m


def horizon_sky(bg, cam, town, t=0.0):
    """
    Paints the far horizon onto a sky background (float HxWx3): hill ridges, valley mist, far lights
    and the landmarks, all centred on the camera like Horizon.cs's FarHorizon. Returns a new array.
    """
    h = town["horizon"]
    H, W = bg.shape[:2]
    out = bg.copy()
    cx, cz = cam.pos[0], cam.pos[2]
    mist = np.array([0.17, 0.12, 0.24])
    xs = np.arange(W)
    yy = np.arange(H)[:, None]
    angles = np.arange(0, 360, 0.25)

    def column_curve(points):
        sp = cam.project(points)
        ok = sp[:, 2] > 1
        if ok.sum() < 2:
            return None
        sx, sy = sp[ok, 0], sp[ok, 1]
        order = np.argsort(sx)
        sx, sy = sx[order], sy[order]
        if sx[0] > 0 or sx[-1] < W:
            return None
        return np.interp(xs, sx, sy)

    for ring in h["rings"]:
        heights = ring_height(ring, angles)
        ridge = column_curve(_on_ring(cx, cz, ring["radius"], angles, heights))
        foot = column_curve(_on_ring(cx, cz, ring["radius"], angles, np.full_like(angles, -8.0)))
        if ridge is None or foot is None:
            continue
        top = np.array(ring["color"])
        k = np.clip((yy - ridge[None, :]) / np.maximum(foot - ridge, 1)[None, :], 0, 1)
        col = top[None, None, :] * (1 - 0.65 * k[..., None]) + mist[None, None, :] * 0.65 * k[..., None]
        inside = (yy >= ridge[None, :])[..., None]
        # a soft edge along the ridge line
        edge = np.clip(yy - ridge[None, :] + 1, 0, 1)[..., None]
        out = np.where(inside, col, out * (1 - edge) + col * edge)
    # valley mist in front of the ridges
    inner = h["rings"][-1]["radius"] - 15
    low = column_curve(_on_ring(cx, cz, inner, angles, np.full_like(angles, -8.0)))
    high = column_curve(_on_ring(cx, cz, inner, angles, np.full_like(angles, 26.0)))
    if low is not None and high is not None:
        k = np.clip((yy - high[None, :]) / np.maximum(low - high, 1)[None, :], 0, 1) * 0.85
        out = out * (1 - k[..., None]) + mist * k[..., None]
    img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")
    scale_px = cam.focal
    # far lights
    lt = h.get("lights")
    if lt:
        rng = Lcg(lt["seed"])
        cols = [lt["colors"][i:i + 3] for i in range(0, len(lt["colors"]), 3)]
        tw = Lcg(int(t * 4) + 11)
        for _ in range(lt["count"]):
            a = rng.range(0, 360)
            ring = h["rings"][min(len(h["rings"]) - 1, int(rng.next() * len(h["rings"])))]
            y = ring_height(ring, a) * rng.range(0.15, 0.8)
            size = rng.range(1.0, 2.4) * ring["radius"] / 540
            c = cols[int(rng.next() * len(cols)) % len(cols)]
            p = _on_ring(cx, cz, ring["radius"] - 2, a, y)
            sp = cam.project(p[None, :])[0]
            if sp[2] <= 1:
                continue
            rad = max(0.8, size * 0.5 * scale_px / sp[2])
            alpha = 90 if tw.next() < 0.08 else 255
            rgb = tuple(int(v * 255) for v in c)
            d.ellipse([sp[0] - rad * 2.5, sp[1] - rad * 2.5, sp[0] + rad * 2.5, sp[1] + rad * 2.5], fill=rgb + (alpha // 8,))
            d.rectangle([sp[0] - rad, sp[1] - rad, sp[0] + rad, sp[1] + rad], fill=rgb + (alpha,))
    # landmarks: simple silhouettes, sized by distance
    for lm in h.get("landmarks", []):
        ring = h["rings"][max(0, min(lm["ring"], len(h["rings"]) - 1))]
        s = lm["size"] * ring["radius"] / 540
        ground = ring_height(ring, lm["angle"]) - 3 * s
        base = _on_ring(cx, cz, ring["radius"] - 4, lm["angle"], ground)
        sp = cam.project(base[None, :])[0]
        if sp[2] <= 1 or not (-200 < sp[0] < W + 200):
            continue
        u = s * scale_px / sp[2]  # pixels per landmark unit
        bx, by = sp[0], sp[1]
        dark = tuple(int(v * 0.8 * 255) for v in ring["color"]) + (255,)
        lit = (255, 204, 115, 255)

        def box(x, y, w, hh, c=dark):
            d.rectangle([bx + (x - w / 2) * u, by - (y + hh / 2) * u, bx + (x + w / 2) * u, by - (y - hh / 2) * u], fill=c)

        def tri(x, y, half, hh, c=dark):
            d.polygon([(bx + (x - half) * u, by - y * u), (bx + (x + half) * u, by - y * u), (bx + x * u, by - (y + hh) * u)], fill=c)

        k = lm["kind"]
        if k == "steeple":
            box(0, 9, 14, 18); box(0, 26, 6, 16); tri(0, 34, 3, 18)
            box(0, 27, 2, 3, lit); box(-3.5, 8, 2, 4, lit); box(3.5, 8, 2, 4, lit)
        elif k == "lighthouse":
            box(0, 18, 7, 36); box(0, 38, 5, 4, lit); tri(0, 40, 2.6, 5)
            ang = math.radians((t * 40) % 360)
            reach = 90 * abs(math.sin(ang)) + 10
            dirx = 1 if math.cos(ang) > 0 else -1
            d.polygon([(bx, by - 37.4 * u), (bx, by - 38.6 * u), (bx + dirx * reach * u, by - 43 * u), (bx + dirx * reach * u, by - 33 * u)],
                      fill=(255, 235, 180, 70))
        elif k == "windmill":
            box(0, 9, 9, 18); tri(0, 18, 4.5, 6); box(0, 6, 1.6, 2.2, lit)
            hub = (bx, by - 17 * u)
            for i in range(4):
                a = math.radians(i * 90 + t * 12)
                ca, sa = math.cos(a), math.sin(a)
                pts = [(-0.8, 0), (0.8, 0), (1.6, 13), (-0.4, 13)]
                d.polygon([(hub[0] + (px * ca - py * sa) * u, hub[1] - (px * sa + py * ca) * u) for px, py in pts], fill=dark)
        elif k == "watertower":
            for x in (-3.5, 3.5):
                box(x, 8, 0.8, 16)
            box(0, 20, 11, 8); tri(0, 24, 5.5, 3); box(0, 24.6, 0.8, 0.8, (255, 64, 50, 255))
        else:
            box(-10, 8, 8, 16); box(10, 11, 9, 22); box(0, 5, 14, 10)
            for i in range(4):
                box(6.6 + i * 2.2, 23, 1.2, 2.4)
            box(10, 14, 1.4, 2.4, lit)
    tr = town.get("life", {}).get("train")
    if tr:
        angle = train_angle(tr, t)
        if angle is not None:
            step = 2.0 * 540 / tr["radius"]
            span = step * 0.88
            body, window = (18, 15, 26, 255), (255, 209, 128, 255)
            for i in range(tr["cars"]):
                a0 = angle - i * step
                a1 = a0 - span
                k = 1.7  # TownLife.TrainScale
                y0, y1 = tr["y"], tr["y"] + (5.2 if i == 0 else 4.4) * k

                def q(r, aa, ab, ya, yb, col):
                    pts = _on_ring(cx, cz, r, np.array([aa, ab, ab, aa]), np.array([ya, ya, yb, yb]))
                    sp = cam.project(pts)
                    if (sp[:, 2] > 1).all():
                        d.polygon([(x, y) for x, y, _ in sp], fill=col)

                q(tr["radius"], a0, a1, y0, y1, body)
                if i == 0:
                    q(tr["radius"] - 0.5, a0 - 0.08, a0 - 0.28, y0 + 2.2 * k, y0 + 3.4 * k, (255, 242, 204, 255))
                    q(tr["radius"], a0 - span * 0.3, a0 - span * 0.3 - 0.25, y1, y1 + 2 * k, body)
                    continue
                for w in range(4):
                    wa = a0 - span * (0.12 + w * 0.22)
                    col = (115, 94, 58, 255) if w == (i * 7) % 5 else window
                    q(tr["radius"] - 0.5, wa, wa - span * 0.13, y0 + 1.6 * k, y0 + 3.3 * k, col)
    return np.asarray(img, dtype=float) / 255.0


def train_angle(tr, t):
    """Where the front of the train is at time t (TownLife.UpdateTrain), or None between trains."""
    span = abs(tr["to"] - tr["from"]) + tr["cars"] * 2.2
    cycle = span / max(0.1, tr["speed"]) + 25
    k = (t % cycle) * tr["speed"]
    if k > span:
        return None
    return tr["from"] + k * (1 if tr["to"] >= tr["from"] else -1)
