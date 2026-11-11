"""
Round 45: one smooth skin for each person, instead of a stack of separate capsules and spheres.

The body's own parts (torso, shoulders, arms, legs, neck, head, jaw, cheeks, ears, skirt tiers) are
melted together with a smooth union of their distance fields, and the result is meshed with
surface nets. Joints flow into each other the way a real arm meets a shoulder, so a person stops
looking like a stack of toy pieces. Clothes keep their colours: every bit of the skin takes the
colour of the part it's closest to. Spooky/SmoothBody.cs does exactly the same in the game.

Round 46: the nose grows out of the face, the palm and thumb are one piece (fingers stay separate),
and hair is one soft mass. Each limb is meshed on its own grid, and the head, hair and hands get a
grid twice as fine, so a nose or a knuckle keeps its shape. Eyes, brows, mouths, fingers, shoes and
accessories still sit on top as their own parts.

    import smoothbody; v, n, f, c = smoothbody.build(parts)    # verts, normals, faces, face colours
"""
import math
import re

import numpy as np

CELL = 0.012  # grid spacing in metres (SmoothBody.Cell)
BODY = re.compile(r"^(Chest|ShoulderLine|Shoulders|Waist|Hips|Belly|Neck|Head|Jaw|Chin|Cheek[LR]|Ear[LR]|"
                  r"Shoulder[LR]|UpperArm[LR]|Elbow[LR]|Forearm[LR]|Wrist[LR]|Thigh[LR]|Shin[LR]|Ankle[LR]|"
                  r"\w+Tier\d|Nose|NoseBridge|NoseWing[LR]|Hand[LR](?:Knuckles|Thumb)?|"
                  r"Hair(?:Crown|Back|Front|Long|Fall|Sweep|Part|Curtain[LR]|Temple[LR]|Strand[LR]|Tuft\d|Flyaway)|"
                  r"Fringe|Sideburn[LR]|SideHair[LR]|Bun|Updo|Bouffant|Ponytail|Braid|Curls?|Curl[LR\d]+)$")
HEAD = re.compile(r"^(Head|Jaw|Chin|Cheek[LR]|Ear[LR])$")
NOSE = re.compile(r"^(Nose|NoseBridge|NoseWing[LR])$")
HAND = re.compile(r"^Hand([LR])(?:Knuckles|Thumb)?$")
HAIR = re.compile(r"^(Hair\w*|Fringe|Sideburn[LR]|SideHair[LR]|Bun|Updo|Bouffant|Ponytail|Braid|Curls?|Curl[LR\d]+)$")
K_HEAD, K_BODY, K_SKIRT = 0.04, 0.042, 0.07  # how far the smooth union melts shapes together
K_NOSE, K_HAND, K_HAIR = 0.012, 0.008, 0.03   # round 46: a nose grown out of the face, one-piece hands, soft hair


def body_parts(parts):
    """The parts that become the smooth skin (only for people: needs a head and a chest or waist)."""
    out = [q for q in parts if BODY.match(q["n"]) and q["t"] in ("sphere", "capsule", "cyl", "rcyl") and q["m"] == "solid" and q.get("k", "") != "mask"
           and min(abs(v) for v in q["s"]) >= 0.03]  # thin flat bits (blush) stay on top as paint
    names = {q["n"] for q in out}
    return out if "Head" in names and ({"Chest", "Waist", "Shoulders"} & names) else []


def blend_k(name):
    if NOSE.match(name):
        return K_NOSE
    if HAND.match(name):
        return K_HAND
    if HAIR.match(name):
        return K_HAIR
    return K_HEAD if HEAD.match(name) else K_SKIRT if "Tier" in name else K_BODY


def euler(rx, ry, rz):
    """Unity's Euler rotation (z, then x, then y), as in render3d."""
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Ry @ Rx @ Rz


def _ell(P, r):
    """Approximate distance from points P to an ellipsoid (or ellipse) with radii r, centred at 0."""
    k0 = np.linalg.norm(P / r, axis=1)
    k1 = np.linalg.norm(P / (r * r), axis=1)
    return np.where(k1 > 1e-9, k0 * (k0 - 1.0) / np.maximum(k1, 1e-9), -r.min())


def part_sdf(q, P):
    """Signed distance (approximate, in metres) from points P (N x 3) to one part. Stretched shapes are
    measured in their own stretched space, so a flat disc or a long thin arm still gets true distances."""
    R = euler(*q["r"])
    s = np.maximum(np.abs(np.array(q["s"], float)), 1e-4)
    L = (P - np.array(q["p"], float)) @ R  # into the part's own axes, still in metres
    t = q["t"]
    if t == "sphere":
        return _ell(L, 0.5 * s)
    if t == "capsule":  # Unity's capsule: half-spheres centred at y = +-0.5 of a 2-tall shape
        y = np.clip(L[:, 1] / s[1], -0.5, 0.5) * s[1]
        Q = L.copy()
        Q[:, 1] -= y
        return _ell(Q, 0.5 * s)
    # cylinder: radius 0.5, y from -1 to 1
    a = _ell(L[:, [0, 2]], 0.5 * s[[0, 2]])
    b = np.abs(L[:, 1]) - s[1]
    return np.minimum(np.maximum(a, b), 0) + np.sqrt(np.maximum(a, 0) ** 2 + np.maximum(b, 0) ** 2)


def part_bounds(q):
    """World-space box round a part (its rotated unit shape's corners)."""
    R = euler(*q["r"])
    s = np.abs(np.array(q["s"], float))
    hy = 1.0 if q["t"] in ("capsule", "cyl", "rcyl") else 0.5
    corners = np.array([[x, y, z] for x in (-0.5, 0.5) for y in (-hy, hy) for z in (-0.5, 0.5)]) * s
    w = corners @ R.T + np.array(q["p"], float)
    return w.min(axis=0), w.max(axis=0)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b + (a - b) * h - k * h * (1.0 - h)


def groups(name):
    """Which limbs a part belongs to. Parts only melt into parts of the same limb, so a hand resting on
    a hip or an arm hanging by a skirt stays separate, while the shoulder still flows into the chest."""
    side = name[-1] if name[-1] in "LR" and not name.endswith("Tier") else ""
    hand = HAND.match(name)
    if hand:
        return ["hand" + hand.group(1)]
    if HAIR.match(name):
        return ["hair"]
    if NOSE.match(name):
        return ["head"]
    if re.match(r"^(Shoulder|UpperArm|Elbow|Forearm|Wrist)[LR]$", name):
        return ["arm" + side]
    if re.match(r"^(Thigh|Shin|Ankle)[LR]$", name):
        return ["leg" + side]
    if "Tier" in name:
        return ["skirt"]
    if HEAD.match(name):
        return ["head"]
    if name == "Neck":
        return ["head", "torso"]
    if name in ("Chest", "ShoulderLine", "Shoulders"):
        return ["torso", "armL", "armR"]
    if name in ("Hips", "Waist"):
        return ["torso", "legL", "legR"]
    return ["torso"]


FINE = ("head", "hair", "handL", "handR")  # small, detailed limbs get a grid twice as fine (round 46)


def cell_for(group):
    return CELL / 2 if group in FINE else CELL


def field(parts, cell, group):
    """The smooth-union field of one limb (group), on its own grid round just that limb's parts."""
    mine = [q for q in parts if group in groups(q["n"])]
    lo = np.min([part_bounds(q)[0] for q in mine], axis=0) - 0.08
    hi = np.max([part_bounds(q)[1] for q in mine], axis=0) + 0.08
    n = np.ceil((hi - lo) / cell).astype(int) + 1
    F = np.full(n, 1.0)
    for q in mine:  # each part only touches the cells near it
        k = blend_k(q["n"])
        a, b = part_bounds(q)
        i0 = np.maximum(np.floor((a - k - 0.03 - lo) / cell).astype(int), 0)
        i1 = np.minimum(np.ceil((b + k + 0.03 - lo) / cell).astype(int) + 1, n)
        gx, gy, gz = (lo[i] + cell * np.arange(i0[i], i1[i]) for i in range(3))
        X, Y, Z = np.meshgrid(gx, gy, gz, indexing="ij")
        P = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
        d = part_sdf(q, P).reshape(X.shape)
        sub = F[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]]
        F[i0[0]:i1[0], i0[1]:i1[1], i0[2]:i1[2]] = smin(d, sub, k)
    return F, lo


def trilinear(G, x):
    """G (nx, ny, nz, c) sampled at fractional grid coordinates x (N x 3)."""
    hi = np.array(G.shape[:3]) - 2
    i = np.clip(np.floor(x).astype(int), 0, hi)
    f = np.clip(x - i, 0, 1)
    out = 0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[:, 0] if dx else 1 - f[:, 0]) * (f[:, 1] if dy else 1 - f[:, 1]) * (f[:, 2] if dz else 1 - f[:, 2])
                out = out + G[i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz] * w[:, None]
    return out


def surface_nets(F, lo, cell):
    inside = F < 0
    nx, ny, nz = F.shape
    acc = np.zeros((nx - 1, ny - 1, nz - 1, 3))
    cnt = np.zeros((nx - 1, ny - 1, nz - 1))
    for ax in range(3):
        a = [slice(None)] * 3
        b = [slice(None)] * 3
        a[ax], b[ax] = slice(0, -1), slice(1, None)
        f0, f1 = F[tuple(a)], F[tuple(b)]
        cross = inside[tuple(a)] != inside[tuple(b)]
        t = np.where(cross, f0 / np.where(f0 - f1 == 0, 1e-9, f0 - f1), 0.0)
        idx = np.indices(f0.shape).astype(float)
        pos = np.stack([idx[0], idx[1], idx[2]], axis=-1)
        pos[..., ax] += t
        pos *= cross[..., None]
        # each edge touches the (up to) 4 cells round it
        others = [o for o in range(3) if o != ax]
        for du in (0, 1):
            for dv in (0, 1):
                src = [slice(None)] * 3
                dst = [slice(None)] * 3
                for o, dd in zip(others, (du, dv)):
                    size = F.shape[o] - 1
                    src[o] = slice(dd, dd + size)
                    dst[o] = slice(0, size)
                acc[tuple(dst)] += pos[tuple(src)]
                cnt[tuple(dst)] += cross[tuple(src)]
    has = cnt > 0
    vid = -np.ones(cnt.shape, int)
    vid[has] = np.arange(has.sum())
    verts = acc[has] / cnt[has][:, None] * cell + lo
    faces = []
    for ax in range(3):
        a = [slice(None)] * 3
        b = [slice(None)] * 3
        a[ax], b[ax] = slice(0, -1), slice(1, None)
        cross = inside[tuple(a)] != inside[tuple(b)]
        flip = inside[tuple(a)]
        o1, o2 = [o for o in range(3) if o != ax]
        e = np.argwhere(cross)
        e = e[(e[:, o1] > 0) & (e[:, o2] > 0) & (e[:, o1] < F.shape[o1] - 1) & (e[:, o2] < F.shape[o2] - 1)]
        for c in e:
            def cellat(d1, d2):
                cc = list(c)
                cc[o1] -= d1
                cc[o2] -= d2
                return vid[tuple(cc)]
            quad = [cellat(1, 1), cellat(0, 1), cellat(0, 0), cellat(1, 0)]
            if min(quad) < 0:
                continue
            if (ax == 1) ^ bool(flip[tuple(c)]):
                quad = quad[::-1]
            faces.append(quad)
    return verts, np.array(faces, int).reshape(-1, 4)


def soften(F):
    """A 1-2-1 blur along each axis, so normals don't ripple with the grid."""
    for ax in range(3):
        P = np.pad(F, [(1, 1) if a == ax else (0, 0) for a in range(3)], mode="edge")
        sl = lambda i: tuple(slice(i, i + F.shape[ax]) if a == ax else slice(None) for a in range(3))  # noqa: E731
        F = (P[sl(0)] + 2 * P[sl(1)] + P[sl(2)]) / 4
    return F


def build(parts, cell=CELL):
    """(verts, vertex normals, triangles, triangle colours, body parts, owners) of the smooth skin, or None
    if not a person. Each limb is meshed on its own grid and the limbs overlap where they meet."""
    body = body_parts(parts)
    if not body:
        return None
    V, N, T = [], [], []
    base = 0
    for g in sorted({g for q in body for g in groups(q["n"])}):
        c = cell_for(g) * cell / CELL
        F, lo = field(body, c, g)
        verts, quads = surface_nets(F, lo, c)
        if len(quads) == 0:
            continue
        tris = np.concatenate([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]])
        gr = np.stack(np.gradient(soften(F)), axis=-1)  # vertex normals from the (gently blurred) field's slope
        nrm = trilinear(gr, (verts - lo) / c)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        fn = np.cross(verts[tris[:, 1]] - verts[tris[:, 0]], verts[tris[:, 2]] - verts[tris[:, 0]])
        wrong = np.einsum("ij,ij->i", fn, nrm[tris].mean(axis=1)) < 0  # face the way the normals do
        tris[wrong] = tris[wrong][:, ::-1]
        V.append(verts)
        N.append(nrm)
        T.append(tris + base)
        base += len(verts)
    verts, nrm, tris = np.concatenate(V), np.concatenate(N), np.concatenate(T)
    # each triangle takes the colour of the part nearest its middle
    mid = verts[tris].mean(axis=1)
    D = np.stack([part_sdf(q, mid) for q in body], axis=1)
    owner = D.argmin(axis=1)
    cols = np.array([body[i]["c"] for i in owner], float)
    return verts, nrm, tris, cols, body, owner
