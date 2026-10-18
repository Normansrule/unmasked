#!/usr/bin/env python3
"""
Designs every character and spooky prop out of simple shapes and writes them to
Assets/Unmasked/Resources/Costumes.json.

Like the manor layout, that one file is the single source of truth:
  - Unity builds the Haunter's villain costumes, the Solvers' outfits, the suspects and the
    Halloween props from it (Editor/TestRoomBuilder.cs, Editor/ManorBuilder.cs).
  - Docs/tools/render3d.py draws the same models for the README.

Coordinates are local to the character: feet at the origin, +z is the way they face.
Shapes and sizes follow make_manor.py: "box" full size; "sphere" full diameter;
"cyl" and "capsule" Unity localScale (height = 2 * y).

Part modes: solid, emissive (glows: e = strength), ghost (see-through and glowing).
Parts with "k": "mask" belong to the mask that flies off at the unmasking.

    python3 Docs/tools/make_costumes.py
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Assets", "Unmasked", "Resources", "Costumes.json")


def rgb(h):
    h = h.lstrip("#")
    return [round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4)]


def part(n, t, p, s, c, m="solid", r=(0, 0, 0), e=1.0, k=""):
    return {"n": n, "t": t, "p": [round(v, 3) for v in p], "s": [round(v, 3) for v in s],
            "r": [round(v, 2) for v in r], "c": c if isinstance(c, list) else rgb(c), "m": m, "e": e, "k": k}


def place(parts, offset=(0, 0, 0), scale=1.0, ry=0.0, k=None, prefix=""):
    """Moves, scales and turns (around y) a group of parts, e.g. a pumpkin into a hand."""
    a = math.radians(ry)
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for q in parts:
        x, y, z = (v * scale for v in q["p"])
        # Unity's y rotation: x' = x cos + z sin, z' = -x sin + z cos
        p = (x * ca + z * sa + offset[0], y + offset[1], -x * sa + z * ca + offset[2])
        out.append(dict(q, n=prefix + q["n"], p=[round(v, 3) for v in p], s=[round(v * scale, 3) for v in q["s"]],
                        r=[q["r"][0], round(q["r"][1] + ry, 2), q["r"][2]], k=q["k"] if k is None else k))
    return out


def limb(n, t, start, direction, length, thickness, c, m="solid", k=""):
    """A capsule or box from start along direction (in the y-z plane, tilted sideways by x)."""
    dx, dy, dz = direction
    norm = math.sqrt(dx * dx + dy * dy + dz * dz)
    dx, dy, dz = dx / norm, dy / norm, dz / norm
    # Unity Euler (rx, 0, rz) applied to +y: first z then x.
    rz = -math.degrees(math.asin(max(-1, min(1, dx))))
    cz = math.cos(math.radians(rz))
    rx = math.degrees(math.atan2(dz, dy)) if cz > 1e-6 else 0.0
    centre = (start[0] + dx * length / 2, start[1] + dy * length / 2, start[2] + dz * length / 2)
    size = (thickness, length / 2, thickness) if t != "box" else (thickness, length, thickness)
    return part(n, t, centre, size, c, m, (rx, 0, rz), k=k)


# ---------------------------------------------------------------------------
# Palette: Halloween night. Deep purples and blues, pumpkin orange, candle gold, wisp green.
# ---------------------------------------------------------------------------
PAL = {
    "pumpkin": "#e8731c", "pumpkin_dark": "#b9520f", "stem": "#4f5a22", "carve": "#ffcf4a", "candle": "#ffb347",
    "night": "#1b1530", "midnight": "#2a2350", "plum": "#4a2a5e", "blood": "#7a0f1f", "bone": "#efe6cf",
    "ghost": "#bfe9de", "wisp": "#9dff8a", "ember": "#ff6a1a", "iron": "#26242c", "straw": "#d6b25a",
    "burlap": "#b8925a", "moss": "#4b5a34", "hay": "#c9a64a",
}
P = {k: rgb(v) for k, v in PAL.items()}

# ---------------------------------------------------------------------------
# Props
# ---------------------------------------------------------------------------


def pumpkin_body(c=P["pumpkin"], dark=P["pumpkin_dark"]):
    return [
        part("Body", "sphere", (0, 0.24, 0), (0.6, 0.46, 0.58), c),
        part("LobeL", "sphere", (-0.13, 0.24, 0), (0.4, 0.44, 0.52), dark),
        part("LobeR", "sphere", (0.13, 0.24, 0), (0.4, 0.44, 0.52), dark),
        part("Stem", "cyl", (0.02, 0.5, 0), (0.07, 0.06, 0.07), P["stem"], r=(0, 0, 14)),
    ]


def carved_face(glow=P["carve"], e=2.4):
    return [
        part("EyeL", "box", (-0.12, 0.31, 0.265), (0.1, 0.1, 0.07), glow, "emissive", (0, 0, 45), e),
        part("EyeR", "box", (0.12, 0.31, 0.265), (0.1, 0.1, 0.07), glow, "emissive", (0, 0, 45), e),
        part("Nose", "box", (0, 0.23, 0.29), (0.06, 0.06, 0.05), glow, "emissive", (0, 0, 45), e),
        part("MouthL", "box", (-0.09, 0.15, 0.27), (0.15, 0.055, 0.07), glow, "emissive", (0, 0, -16), e),
        part("MouthR", "box", (0.09, 0.15, 0.27), (0.15, 0.055, 0.07), glow, "emissive", (0, 0, 16), e),
        part("Tooth", "box", (0, 0.14, 0.295), (0.05, 0.04, 0.03), P["pumpkin"]),
    ]


JACK = pumpkin_body() + carved_face()
PUMPKIN = pumpkin_body() + [part("Leaf", "box", (0.09, 0.47, 0.03), (0.16, 0.015, 0.1), P["stem"], r=(0, 30, -10))]
TURNIP = place(pumpkin_body(rgb("#d9c7d9"), rgb("#8e5f9a")), scale=1.0) + carved_face(rgb("#ff9a3a"), 2.6)

CANDLE = [
    part("Wax", "cyl", (0, 0.11, 0), (0.07, 0.11, 0.07), P["bone"]),
    part("Flame", "sphere", (0, 0.27, 0), (0.05, 0.09, 0.05), P["candle"], "emissive", e=3.0),
]

SCARECROW = [
    part("Post", "cyl", (0, 0.9, -0.05), (0.09, 0.9, 0.09), rgb("#5b4027")),
    part("Crossbar", "box", (0, 1.45, -0.05), (1.5, 0.08, 0.08), rgb("#5b4027")),
    part("Shirt", "box", (0, 1.25, 0), (0.55, 0.65, 0.3), rgb("#6d4a7a")),
    part("Patch", "box", (0.12, 1.3, 0.16), (0.14, 0.14, 0.02), P["pumpkin"]),
    part("SleeveL", "box", (-0.5, 1.45, 0), (0.5, 0.2, 0.22), rgb("#6d4a7a")),
    part("SleeveR", "box", (0.5, 1.45, 0), (0.5, 0.2, 0.22), rgb("#6d4a7a")),
    part("StrawL", "box", (-0.8, 1.42, 0), (0.12, 0.08, 0.14), P["straw"], r=(0, 0, 25)),
    part("StrawR", "box", (0.8, 1.42, 0), (0.12, 0.08, 0.14), P["straw"], r=(0, 0, -25)),
    part("Trousers", "box", (0, 0.78, 0), (0.45, 0.35, 0.26), rgb("#3c4a6a")),
    part("Rope", "box", (0, 0.95, 0), (0.48, 0.04, 0.28), P["straw"]),
] + place(JACK, (0, 1.58, 0), 1.0) + [
    part("HatBrim", "cyl", (0, 2.06, 0), (0.8, 0.015, 0.8), P["straw"], r=(6, 0, -4)),
    part("HatTop", "cyl", (0, 2.18, 0), (0.36, 0.12, 0.36), P["straw"], r=(6, 0, -4)),
]

HAYBALE = [
    part("Bale", "box", (0, 0.3, 0), (1.1, 0.6, 0.65), P["hay"]),
    part("Twine1", "box", (-0.3, 0.3, 0), (0.03, 0.62, 0.67), rgb("#8a6a2a")),
    part("Twine2", "box", (0.3, 0.3, 0), (0.03, 0.62, 0.67), rgb("#8a6a2a")),
]

CAULDRON = [
    part("Pot", "sphere", (0, 0.4, 0), (0.95, 0.72, 0.95), P["iron"]),
    part("Rim", "cyl", (0, 0.77, 0), (0.82, 0.03, 0.82), P["iron"]),
    part("Brew", "cyl", (0, 0.795, 0), (0.72, 0.012, 0.72), P["wisp"], "emissive", e=2.2),
    part("Bubble1", "sphere", (0.12, 0.82, 0.05), (0.14, 0.1, 0.14), P["wisp"], "emissive", e=2.6),
    part("Bubble2", "sphere", (-0.15, 0.82, -0.1), (0.1, 0.07, 0.1), P["wisp"], "emissive", e=2.6),
    part("LegA", "box", (0.3, 0.08, 0.2), (0.07, 0.18, 0.07), P["iron"]),
    part("LegB", "box", (-0.3, 0.08, 0.2), (0.07, 0.18, 0.07), P["iron"]),
    part("LegC", "box", (0, 0.08, -0.35), (0.07, 0.18, 0.07), P["iron"]),
]

CROW = [
    part("Body", "sphere", (0, 0.13, 0), (0.16, 0.16, 0.28), rgb("#121018")),
    part("Head", "sphere", (0, 0.24, 0.11), (0.11, 0.11, 0.11), rgb("#121018")),
    part("Beak", "box", (0, 0.23, 0.19), (0.03, 0.03, 0.08), rgb("#5a4a2a")),
    part("Eye", "sphere", (0.04, 0.26, 0.15), (0.025, 0.025, 0.025), rgb("#ffd23a"), "emissive", e=2.0),
    part("Tail", "box", (0, 0.1, -0.17), (0.1, 0.02, 0.14), rgb("#121018"), r=(-20, 0, 0)),
]


def cobweb():
    """A web strung across a corner: apex down in the corner, threads up to the ceiling."""
    parts = []
    apex = (0, -0.75, 0)
    for i, x in enumerate((-0.6, -0.3, 0, 0.3, 0.6)):
        parts.append(limb(f"Thread{i}", "box", apex, (x, 0.75, 0), math.hypot(x, 0.75), 0.012, P["bone"], "ghost"))
    for ring, f in enumerate((0.35, 0.65)):
        for i in range(4):
            x0, x1 = -0.6 + 0.3 * i, -0.3 + 0.3 * i
            a, b = (x0 * f, -0.75 + 0.75 * f, 0), (x1 * f, -0.75 + 0.75 * f + 0.04, 0)
            d = (b[0] - a[0], b[1] - a[1], 0)
            parts.append(limb(f"Ring{ring}{i}", "box", a, d, math.hypot(d[0], d[1]), 0.01, P["bone"], "ghost"))
    return parts


GRAVE_LANTERN = [
    part("Base", "box", (0, 0.06, 0), (0.22, 0.12, 0.22), P["iron"]),
    part("Glass", "box", (0, 0.25, 0), (0.18, 0.26, 0.18), P["candle"], "emissive", e=1.6),
    part("Cap", "box", (0, 0.42, 0), (0.24, 0.06, 0.24), P["iron"]),
    part("Ring", "cyl", (0, 0.49, 0), (0.06, 0.03, 0.06), P["iron"]),
]

# Town props: the Mystery Club van, street furniture and the cornfield.
VAN_BODY, VAN_STRIPE, VAN_ROOF = rgb("#3fa7a0"), rgb("#e8731c"), rgb("#f3e3b5")
VAN = [
    part("Body", "box", (0, 0.95, 0), (1.96, 1.1, 4.6), VAN_BODY),
    part("Cabin", "box", (0, 1.92, -0.45), (1.9, 0.9, 3.5), VAN_ROOF),
    part("Nose", "box", (0, 1.62, 1.55), (1.9, 0.4, 0.9), VAN_BODY),
    part("Windshield", "box", (0, 1.95, 1.22), (1.7, 0.72, 0.06), rgb("#9fd6ff"), "emissive", (-18, 0, 0), 0.5),
    part("WindowL", "box", (-0.96, 1.95, -0.5), (0.04, 0.55, 2.6), rgb("#9fd6ff"), "emissive", e=0.4),
    part("WindowR", "box", (0.96, 1.95, -0.5), (0.04, 0.55, 2.6), rgb("#9fd6ff"), "emissive", e=0.4),
    part("StripeL", "box", (-0.99, 1.15, 0), (0.03, 0.22, 4.5), VAN_STRIPE),
    part("StripeR", "box", (0.99, 1.15, 0), (0.03, 0.22, 4.5), VAN_STRIPE),
    part("LogoL", "cyl", (-1.0, 0.95, -0.6), (0.6, 0.02, 0.6), rgb("#f6e27a"), r=(0, 0, 90)),
    part("LogoR", "cyl", (1.0, 0.95, -0.6), (0.6, 0.02, 0.6), rgb("#f6e27a"), r=(0, 0, 90)),
    part("Bumper", "box", (0, 0.45, 2.33), (2.0, 0.22, 0.12), rgb("#c9ced9")),
    part("BumperBack", "box", (0, 0.45, -2.33), (2.0, 0.22, 0.12), rgb("#c9ced9")),
    part("HeadlightL", "sphere", (-0.7, 0.95, 2.3), (0.26, 0.26, 0.08), rgb("#fff3c4"), "emissive", e=3.0),
    part("HeadlightR", "sphere", (0.7, 0.95, 2.3), (0.26, 0.26, 0.08), rgb("#fff3c4"), "emissive", e=3.0),
    part("TailL", "box", (-0.8, 1.0, -2.31), (0.2, 0.3, 0.04), rgb("#ff3a3a"), "emissive", e=2.0),
    part("TailR", "box", (0.8, 1.0, -2.31), (0.2, 0.3, 0.04), rgb("#ff3a3a"), "emissive", e=2.0),
    part("Rack", "box", (0, 2.42, -0.6), (1.6, 0.08, 2.4), rgb("#3a3a42")),
    part("Siren", "box", (0, 2.52, 0.4), (0.7, 0.14, 0.25), VAN_STRIPE, "emissive", e=1.6),
] + [
    part(f"Wheel{i}", "cyl", (sx * 0.92, 0.4, sz * 1.5), (0.8, 0.16, 0.8), rgb("#1a1a1f"), r=(0, 0, 90))
    for i, (sx, sz) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1)))
]
STREETLAMP = [
    part("Pole", "cyl", (0, 2.1, 0), (0.12, 2.1, 0.12), P["iron"]),
    part("Foot", "cyl", (0, 0.15, 0), (0.3, 0.15, 0.3), P["iron"]),
    part("Arm", "box", (0, 4.1, 0.35), (0.08, 0.08, 0.8), P["iron"]),
    part("Lamp", "box", (0, 3.95, 0.7), (0.34, 0.36, 0.34), P["candle"], "emissive", e=2.2),
    part("Hood", "cyl", (0, 4.18, 0.7), (0.5, 0.06, 0.5), P["iron"]),
]
MAILBOX = [
    part("Post", "box", (0, 0.5, 0), (0.1, 1.0, 0.1), rgb("#5b4027")),
    part("Box", "box", (0, 1.1, 0.05), (0.26, 0.26, 0.5), rgb("#26242c")),
    part("Flag", "box", (0.15, 1.2, -0.05), (0.02, 0.2, 0.08), rgb("#c83a2a")),
]
CORN = [
    part("Stalk", "cyl", (0, 1.0, 0), (0.06, 1.0, 0.06), rgb("#a99a4a")),
    part("LeafA", "box", (0.18, 1.2, 0), (0.4, 0.03, 0.1), rgb("#8a8a3a"), r=(0, 0, -30)),
    part("LeafB", "box", (-0.18, 1.55, 0.02), (0.4, 0.03, 0.1), rgb("#9a8f40"), r=(0, 20, 30)),
    part("Cob", "capsule", (0.06, 1.35, 0.05), (0.08, 0.14, 0.08), rgb("#e0c060")),
    part("Tassel", "box", (0, 2.05, 0), (0.1, 0.2, 0.1), rgb("#d6b25a")),
]
CALLBOARD = [
    part("LegL", "box", (-0.9, 0.9, 0), (0.08, 1.8, 0.08), rgb("#5b4027")),
    part("LegR", "box", (0.9, 0.9, 0), (0.08, 1.8, 0.08), rgb("#5b4027")),
    part("Board", "box", (0, 1.4, 0), (1.9, 1.1, 0.06), rgb("#8a6a44")),
    part("Map", "box", (-0.3, 1.45, 0.04), (1.0, 0.8, 0.02), rgb("#e8dcb8")),
    part("PinA", "sphere", (-0.5, 1.6, 0.06), (0.06, 0.06, 0.06), rgb("#ff3a3a"), "emissive", e=2.0),
    part("PinB", "sphere", (-0.1, 1.3, 0.06), (0.06, 0.06, 0.06), rgb("#ff3a3a"), "emissive", e=2.0),
    part("NoteA", "box", (0.55, 1.6, 0.04), (0.4, 0.3, 0.02), rgb("#f6e27a")),
    part("NoteB", "box", (0.5, 1.2, 0.04), (0.45, 0.3, 0.02), rgb("#bfe9de")),
    part("Bulb", "sphere", (0, 2.05, 0.1), (0.14, 0.14, 0.14), P["candle"], "emissive", e=2.4),
]
BENCH = [
    part("Seat", "box", (0, 0.45, 0), (1.6, 0.08, 0.45), rgb("#6b4426")),
    part("Back", "box", (0, 0.8, -0.2), (1.6, 0.4, 0.06), rgb("#6b4426"), r=(-10, 0, 0)),
    part("LegL", "box", (-0.7, 0.22, 0), (0.08, 0.44, 0.45), P["iron"]),
    part("LegR", "box", (0.7, 0.22, 0), (0.08, 0.44, 0.45), P["iron"]),
]

# ---------------------------------------------------------------------------
# Nights of the Jack: no two carvings alike, plus the porch and yard dressing of a town that loves
# Halloween but keeps it tasteful (cornstalks, mums, gourds, wreaths, string lights, one ghost).
# ---------------------------------------------------------------------------


def face_z(x, y, cy=0.24, rx=0.3, ry=0.23, rz=0.29):
    """How far forward the pumpkin's skin is at (x, y), so cut-outs sit on the surface."""
    q = 1 - (x / rx) ** 2 - ((y - cy) / ry) ** 2
    return rz * math.sqrt(max(0.08, q)) - 0.004


def cut(n, x, y, w, h, glow, e=2.4, rz=0.0, shape="box", cy=0.24, rx=0.3, ry=0.23, rzz=0.29):
    z = face_z(x, y, cy, rx, ry, rzz)
    if shape == "round":
        return part(n, "cyl", (x, y, z), (w, 0.03, h), glow, "emissive", (90, 0, 0), e)
    return part(n, "box", (x, y, z), (w, h, 0.07), glow, "emissive", (0, 0, rz), e)


GLOW = P["carve"]
JACK_GRIN = pumpkin_body() + [
    cut("EyeL", -0.12, 0.31, 0.12, 0.09, GLOW, rz=0), cut("EyeR", 0.12, 0.31, 0.12, 0.09, GLOW, rz=0),
    part("BrowL", "box", (-0.12, 0.345, face_z(-0.12, 0.345) + 0.01), (0.13, 0.03, 0.06), P["pumpkin"], r=(0, 0, 12)),
    part("BrowR", "box", (0.12, 0.345, face_z(0.12, 0.345) + 0.01), (0.13, 0.03, 0.06), P["pumpkin"], r=(0, 0, -12)),
    cut("Nose", 0, 0.24, 0.05, 0.05, GLOW, rz=45),
] + [cut(f"Grin{i}", i * 0.055, 0.15 + 0.011 * i * i, 0.045, 0.06 - 0.006 * abs(i), GLOW, rz=-8 * i) for i in range(-3, 4)]

JACK_SCARY = pumpkin_body(rgb("#d9611a"), rgb("#a4440c")) + [
    cut("EyeL", -0.12, 0.31, 0.14, 0.05, GLOW, 2.8, rz=-22), cut("EyeR", 0.12, 0.31, 0.14, 0.05, GLOW, 2.8, rz=22),
    cut("Nose", 0, 0.245, 0.04, 0.07, GLOW, 2.8),
] + [cut(f"Fang{i}", i * 0.05, 0.155 + (0.02 if i % 2 else -0.0), 0.05, 0.05, GLOW, 2.8, rz=45) for i in range(-3, 4)]

JACK_SURPRISED = pumpkin_body(rgb("#ee8a2a"), rgb("#c0621a")) + [
    cut("EyeL", -0.11, 0.31, 0.1, 0.1, GLOW, shape="round"), cut("EyeR", 0.11, 0.31, 0.1, 0.1, GLOW, shape="round"),
    cut("PupilL", -0.11, 0.30, 0.035, 0.035, P["pumpkin_dark"], 0.0, shape="round"),
    cut("Mouth", 0, 0.16, 0.1, 0.12, GLOW, shape="round"),
]

JACK_WINK = pumpkin_body() + [
    cut("EyeL", -0.12, 0.31, 0.1, 0.1, GLOW, rz=45), cut("Wink", 0.12, 0.305, 0.12, 0.025, GLOW, rz=-8),
    cut("Nose", 0, 0.235, 0.05, 0.05, GLOW, rz=45),
    cut("Smile0", -0.1, 0.165, 0.09, 0.045, GLOW, rz=-24), cut("Smile1", 0, 0.145, 0.11, 0.045, GLOW),
    cut("Smile2", 0.1, 0.165, 0.09, 0.045, GLOW, rz=24),
]


def tall_pumpkin(c, dark):
    return [
        part("Body", "sphere", (0, 0.34, 0), (0.5, 0.66, 0.5), c),
        part("LobeL", "sphere", (-0.1, 0.34, 0), (0.32, 0.64, 0.44), dark),
        part("LobeR", "sphere", (0.1, 0.34, 0), (0.32, 0.64, 0.44), dark),
        part("Stem", "cyl", (0.0, 0.7, 0), (0.06, 0.07, 0.06), P["stem"], r=(0, 0, -10)),
    ]


TALL = dict(cy=0.34, rx=0.25, ry=0.33, rzz=0.25)
JACK_TALL = tall_pumpkin(rgb("#e07a24"), rgb("#b85a14")) + [
    cut("EyeL", -0.09, 0.45, 0.08, 0.13, GLOW, rz=0, **TALL), cut("EyeR", 0.09, 0.45, 0.08, 0.13, GLOW, rz=0, **TALL),
    cut("Mouth", 0, 0.22, 0.07, 0.14, GLOW, shape="round", **TALL),
]
JACK_WHITE = pumpkin_body(rgb("#e9e4d6"), rgb("#c8c0ae")) + carved_face(rgb("#ffb05a"), 2.6)

PUMPKIN_WARTY = pumpkin_body(rgb("#6f8a3a"), rgb("#55702c")) + [
    part(f"Wart{i}", "sphere", (0.22 * math.cos(i * 1.9), 0.18 + 0.04 * (i % 3), 0.22 * math.sin(i * 1.9)), (0.06, 0.05, 0.06), rgb("#8a9a4a"))
    for i in range(6)]

PUMPKIN_STACK = (place(PUMPKIN, (0, 0, 0), 1.25, 20) + place(pumpkin_body(rgb("#e9e4d6"), rgb("#c8c0ae")), (0.02, 0.56, 0), 0.95, -15, prefix="Mid")
                 + place(JACK_GRIN, (0, 1.0, 0.0), 0.75, 0, prefix="Top"))

GOURDS = [
    part("Gourd0", "sphere", (-0.14, 0.09, 0.02), (0.2, 0.17, 0.2), rgb("#e9e4d6")),
    part("Gourd1", "sphere", (0.1, 0.08, 0.08), (0.17, 0.15, 0.17), rgb("#d8b23a")),
    part("Gourd1b", "capsule", (0.1, 0.18, 0.08), (0.08, 0.08, 0.08), rgb("#d8b23a")),
    part("Gourd2", "sphere", (0.02, 0.08, -0.13), (0.2, 0.15, 0.2), rgb("#5a7a32")),
    part("Gourd2s", "box", (0.02, 0.08, -0.13), (0.04, 0.155, 0.205), rgb("#d8c88a")),
    part("Gourd3", "sphere", (0.18, 0.07, -0.08), (0.13, 0.12, 0.13), P["pumpkin"]),
]

MUMS = [
    part("Pot", "cyl", (0, 0.2, 0), (0.46, 0.2, 0.46), rgb("#9a5a3a")),
    part("Rim", "cyl", (0, 0.39, 0), (0.5, 0.03, 0.5), rgb("#8a4a2e")),
    part("Bloom", "sphere", (0, 0.55, 0), (0.62, 0.42, 0.62), rgb("#b8461e")),
    part("BloomTop", "sphere", (0.05, 0.68, 0.03), (0.4, 0.26, 0.4), rgb("#d2662a")),
    part("Leaves", "sphere", (0, 0.44, 0), (0.6, 0.18, 0.6), rgb("#3a4a26")),
]
MUMS_PURPLE = [dict(q, c=rgb("#6a2a6e") if q["n"] == "Bloom" else (rgb("#8a3a8a") if q["n"] == "BloomTop" else q["c"])) for q in MUMS]

CORNSTALKS = [
    part(f"Stalk{i}", "box", (0.09 * math.cos(i * 1.05), 1.05, 0.09 * math.sin(i * 1.05)), (0.06, 2.1, 0.06),
         rgb("#c8aa62") if i % 2 else rgb("#b0925a"), r=(6 * math.sin(i * 1.05), 0, -6 * math.cos(i * 1.05)))
    for i in range(6)
] + [
    part(f"Husk{i}", "box", (0.22 * math.cos(i * 1.6), 1.9 + 0.12 * (i % 3), 0.22 * math.sin(i * 1.6)), (0.42, 0.03, 0.1),
         rgb("#d6bc72"), r=(0, -math.degrees(i * 1.6), -35 + 15 * (i % 3)))
    for i in range(5)
] + [part("Tie", "cyl", (0, 0.8, 0), (0.3, 0.05, 0.3), rgb("#7a2a1a"))]

WREATH = [
    part(f"Leaf{i}", "sphere", (0.3 * math.cos(i * math.pi / 7), 0.3 * math.sin(i * math.pi / 7), 0), (0.17, 0.17, 0.1),
         [rgb("#d8661c"), rgb("#9a2a1a"), rgb("#c8962a"), rgb("#6a3a1a")][i % 4])
    for i in range(14)
] + [
    part("MiniPumpkinA", "sphere", (-0.18, -0.22, 0.05), (0.12, 0.1, 0.1), P["pumpkin"]),
    part("MiniPumpkinB", "sphere", (0.22, 0.16, 0.05), (0.1, 0.09, 0.09), rgb("#e9e4d6")),
    part("BowL", "box", (-0.07, -0.3, 0.06), (0.14, 0.08, 0.03), rgb("#151018"), r=(0, 0, 25)),
    part("BowR", "box", (0.07, -0.3, 0.06), (0.14, 0.08, 0.03), rgb("#151018"), r=(0, 0, -25)),
]

GHOST_HANG = [
    part("Thread", "box", (0, -0.3, 0), (0.015, 0.6, 0.015), P["bone"]),
    part("Head", "sphere", (0, -0.82, 0), (0.42, 0.44, 0.42), P["ghost"], "ghost", e=1.6),
    part("Body", "capsule", (0, -1.2, 0), (0.5, 0.42, 0.46), P["ghost"], "ghost", e=1.6),
] + [
    part(f"Hem{i}", "sphere", (0.24 * math.cos(i * 1.257), -1.56 - 0.05 * (i % 2), 0.22 * math.sin(i * 1.257)), (0.2, 0.22, 0.2), P["ghost"], "ghost", e=1.6)
    for i in range(5)
] + [
    part("ArmL", "capsule", (-0.3, -1.05, 0.05), (0.12, 0.2, 0.12), P["ghost"], "ghost", (0, 0, -55), 1.6),
    part("ArmR", "capsule", (0.3, -1.05, 0.05), (0.12, 0.2, 0.12), P["ghost"], "ghost", (0, 0, 55), 1.6),
    part("EyeL", "sphere", (-0.08, -0.8, 0.19), (0.07, 0.1, 0.04), rgb("#120c16")),
    part("EyeR", "sphere", (0.08, -0.8, 0.19), (0.07, 0.1, 0.04), rgb("#120c16")),
    part("Mouth", "sphere", (0, -0.93, 0.19), (0.07, 0.09, 0.04), rgb("#120c16")),
]

BONE = P["bone"]
SKELETON = [
    part("Pelvis", "box", (0, 0.18, -0.05), (0.3, 0.14, 0.18), BONE),
    part("Skull", "sphere", (0, 0.98, -0.02), (0.24, 0.27, 0.27), BONE, r=(-12, 0, 8)),
    part("Jaw", "box", (0, 0.86, 0.06), (0.15, 0.06, 0.1), BONE, r=(-12, 0, 8)),
    part("SocketL", "sphere", (-0.055, 1.0, 0.1), (0.07, 0.07, 0.05), rgb("#141016")),
    part("SocketR", "sphere", (0.055, 1.0, 0.1), (0.07, 0.07, 0.05), rgb("#141016")),
] + [part(f"Spine{i}", "box", (0, 0.3 + i * 0.1, -0.08 + 0.01 * i), (0.06, 0.07, 0.06), BONE) for i in range(5)] + [
    part(f"Rib{i}", "capsule", (0, 0.5 + i * 0.075, -0.02), (0.06, 0.14 - 0.015 * i, 0.06), BONE, r=(0, 0, 90)) for i in range(4)
] + [
    limb("ArmUL", "capsule", (-0.17, 0.74, -0.05), (-0.25, -1, 0.35), 0.32, 0.045, BONE),
    limb("ArmUR", "capsule", (0.17, 0.74, -0.05), (0.25, -1, 0.35), 0.32, 0.045, BONE),
    limb("ArmLL", "capsule", (-0.25, 0.45, 0.06), (0.1, -0.4, 1), 0.3, 0.04, BONE),
    limb("ArmLR", "capsule", (0.25, 0.45, 0.06), (-0.1, -0.4, 1), 0.3, 0.04, BONE),
    limb("ThighL", "capsule", (-0.1, 0.2, 0.0), (0, 0.2, 1), 0.42, 0.06, BONE),
    limb("ThighR", "capsule", (0.1, 0.2, 0.0), (0, 0.2, 1), 0.42, 0.06, BONE),
    limb("ShinL", "capsule", (-0.1, 0.28, 0.41), (0, -1, 0.15), 0.3, 0.05, BONE),
    limb("ShinR", "capsule", (0.1, 0.28, 0.41), (0, -1, 0.15), 0.3, 0.05, BONE),
] + place(JACK, (0.0, 0.0, 0.62), 0.6, 0, prefix="Lap")

TOMB_ROUND = [
    part("Slab", "box", (0, 0.4, 0), (0.62, 0.8, 0.14), rgb("#7a7d82")),
    part("Top", "cyl", (0, 0.8, 0), (0.62, 0.07, 0.62), rgb("#7a7d82"), r=(90, 0, 0)),
    part("Plate", "box", (0, 0.55, 0.072), (0.36, 0.22, 0.01), rgb("#55585e")),
    part("Moss", "box", (-0.12, 0.08, 0.06), (0.4, 0.16, 0.04), rgb("#3e5030")),
    part("Mound", "sphere", (0, 0.0, 0.55), (0.75, 0.16, 1.2), rgb("#3a2e24")),
]
TOMB_CROSS = [
    part("Base", "box", (0, 0.12, 0), (0.5, 0.24, 0.3), rgb("#6a6d72")),
    part("Post", "box", (0, 0.72, 0), (0.14, 1.0, 0.12), rgb("#7f8288")),
    part("Arm", "box", (0, 0.92, 0), (0.56, 0.13, 0.12), rgb("#7f8288")),
    part("Moss", "box", (0.08, 0.2, 0.11), (0.3, 0.12, 0.04), rgb("#3e5030")),
]

CAT = [
    part("Body", "sphere", (0, 0.17, -0.02), (0.22, 0.3, 0.26), rgb("#101014")),
    part("Head", "sphere", (0, 0.38, 0.04), (0.17, 0.15, 0.15), rgb("#101014")),
    part("EarL", "box", (-0.05, 0.47, 0.04), (0.05, 0.08, 0.03), rgb("#101014"), r=(0, 0, 15)),
    part("EarR", "box", (0.05, 0.47, 0.04), (0.05, 0.08, 0.03), rgb("#101014"), r=(0, 0, -15)),
    part("EyeL", "sphere", (-0.035, 0.39, 0.11), (0.035, 0.03, 0.02), rgb("#e8ff4a"), "emissive", e=3.0),
    part("EyeR", "sphere", (0.035, 0.39, 0.11), (0.035, 0.03, 0.02), rgb("#e8ff4a"), "emissive", e=3.0),
    limb("Tail", "capsule", (0.06, 0.05, -0.14), (0.6, 0.6, -0.3), 0.3, 0.035, rgb("#101014")),
]

LUMINARIA = [
    part("Bag", "box", (0, 0.16, 0), (0.2, 0.32, 0.14), rgb("#e8c890"), "emissive", e=0.9),
    part("Fold", "box", (0, 0.31, 0), (0.21, 0.03, 0.15), rgb("#c8a870")),
    part("Bat", "box", (0, 0.18, 0.071), (0.1, 0.04, 0.005), rgb("#2a1a10")),
]

SPIDER = [
    part("Body", "sphere", (0, 0, -0.12), (0.5, 0.36, 0.6), rgb("#121016")),
    part("Head", "sphere", (0, 0, 0.22), (0.26, 0.22, 0.24), rgb("#121016")),
    part("EyeL", "sphere", (-0.05, 0.05, 0.33), (0.05, 0.05, 0.03), rgb("#ff3a2a"), "emissive", e=2.5),
    part("EyeR", "sphere", (0.05, 0.05, 0.33), (0.05, 0.05, 0.03), rgb("#ff3a2a"), "emissive", e=2.5),
] + [
    limb(f"Leg{s}{i}", "box", (s * 0.12, 0.0, 0.1 - i * 0.1), (s * 1.0, 0.7, 0.4 - i * 0.35), 0.45, 0.035, rgb("#121016"))
    for s in (-1, 1) for i in range(4)
] + [
    limb(f"Foot{s}{i}", "box", (s * (0.12 + 0.45 * 0.78), 0.3, 0.1 - i * 0.1 + 0.45 * (0.4 - i * 0.35) / 1.3), (s * 0.5, -1, 0), 0.45, 0.03, rgb("#121016"))
    for s in (-1, 1) for i in range(4)
]


def bulb(c):
    return [
        part("Socket", "cyl", (0, 0.04, 0), (0.05, 0.03, 0.05), rgb("#1a1a1a")),
        part("Bulb", "sphere", (0, -0.04, 0), (0.09, 0.12, 0.09), c, "emissive", e=3.0),
    ]


WALL_LANTERN = [
    part("Plate", "box", (0, 0, -0.04), (0.16, 0.36, 0.03), P["iron"]),
    part("Arm", "box", (0, 0.1, 0.06), (0.04, 0.04, 0.18), P["iron"]),
    part("Glass", "box", (0, -0.02, 0.15), (0.18, 0.26, 0.18), rgb("#ffcf7a"), "emissive", e=2.2),
    part("Cap", "box", (0, 0.14, 0.15), (0.24, 0.06, 0.24), P["iron"]),
    part("Base", "box", (0, -0.17, 0.15), (0.2, 0.04, 0.2), P["iron"]),
]

# A shadowy figure seen through a lit window (it faces +z; stand it just inside the glass).
WINDOW_GHOST = [
    part("Head", "sphere", (0, 1.62, 0), (0.28, 0.32, 0.12), rgb("#140e18")),
    part("Shoulders", "capsule", (0, 1.25, 0), (0.5, 0.35, 0.12), rgb("#140e18"), r=(0, 0, 90)),
    part("Body", "box", (0, 0.9, 0), (0.46, 0.8, 0.1), rgb("#140e18")),
]

JACK_KINDS = ["jack", "jack_grin", "jack_scary", "jack_surprised", "jack_wink", "jack_tall", "jack_white"]


# Round 22: the street remembers (a party table and a thank-you banner in a solved house's yard),
# the HQ dressing-up trunk, and the Lantern Watch costume pieces the townsfolk give the club.
TIN = rgb("#a8a8b4")
BRASS = rgb("#c8963a")
PARTY_TABLE = [
    part("Top", "box", (0, 0.74, 0), (1.5, 0.05, 0.8), rgb("#7a5230")),
    part("Cloth", "box", (0, 0.77, 0), (1.56, 0.02, 0.86), rgb("#e07a2a")),
    part("ClothHem", "box", (0, 0.66, 0.43), (1.56, 0.2, 0.01), rgb("#c0601a")),
] + [part("Leg" + str(i), "box", (x, 0.37, z), (0.06, 0.74, 0.06), rgb("#5a3a20"))
     for i, (x, z) in enumerate(((-0.68, -0.34), (0.68, -0.34), (-0.68, 0.34), (0.68, 0.34)))] + [
    part("PiePlate", "cyl", (-0.35, 0.795, 0.05), (0.36, 0.01, 0.36), rgb("#efe6d6")),
    part("Pie", "cyl", (-0.35, 0.82, 0.05), (0.3, 0.035, 0.3), rgb("#d08a3a")),
    part("PieTop", "cyl", (-0.35, 0.842, 0.05), (0.24, 0.01, 0.24), rgb("#b0602a")),
    part("Jug", "cyl", (0.15, 0.88, -0.1), (0.13, 0.11, 0.13), rgb("#6a8ab0")),
    part("JugHandle", "box", (0.23, 0.9, -0.1), (0.03, 0.1, 0.03), rgb("#6a8ab0")),
] + [part("Cup" + str(i), "cyl", (0.35 + i * 0.14, 0.82, 0.18), (0.07, 0.05, 0.07), rgb(c))
     for i, c in enumerate(("#e8c040", "#7aa04a", "#b05a8a"))] + [
    part("Candy", "cyl", (0.45, 0.8, -0.18), (0.3, 0.03, 0.3), rgb("#3a2a4a")),
    part("CandyA", "sphere", (0.4, 0.83, -0.15), (0.06, 0.05, 0.06), rgb("#ff6a3a")),
    part("CandyB", "sphere", (0.5, 0.83, -0.2), (0.06, 0.05, 0.06), rgb("#ffd040")),
    part("CandyC", "sphere", (0.46, 0.83, -0.12), (0.06, 0.05, 0.06), rgb("#9a5aff")),
    part("Candle", "cyl", (-0.05, 0.85, -0.2), (0.05, 0.08, 0.05), P["bone"]),
    part("Flame", "sphere", (-0.05, 0.96, -0.2), (0.04, 0.06, 0.04), P["candle"], "emissive", e=2.0),
]


def banner(width=5.2):
    """Two posts either side of a gate, a cloth across the top (the words go on in Unity) and bulbs."""
    hw = width / 2
    out = [part("PostL", "box", (-hw, 1.3, 0), (0.12, 2.6, 0.12), rgb("#5a3a20")),
           part("PostR", "box", (hw, 1.3, 0), (0.12, 2.6, 0.12), rgb("#5a3a20")),
           part("Cloth", "box", (0, 2.3, 0), (width - 0.3, 0.55, 0.02), rgb("#efe0c0")),
           part("ClothEdgeTop", "box", (0, 2.58, 0), (width - 0.3, 0.05, 0.03), rgb("#e07a2a")),
           part("ClothEdgeLow", "box", (0, 2.02, 0), (width - 0.3, 0.05, 0.03), rgb("#e07a2a"))]
    cols = ["#ff8a1a", "#ffd040", "#b05aff", "#7aff5a"]
    n = 11
    for i in range(n):
        t = i / (n - 1)
        x = -hw + t * width
        y = 2.0 - 0.28 * math.sin(math.pi * t) - 0.05
        out.append(part("Bulb" + str(i), "sphere", (x, y, 0.08), (0.08, 0.1, 0.08), rgb(cols[i % 4]), "emissive", e=1.6))
    return out


TRUNK = [
    part("Box", "box", (0, 0.32, 0), (1.1, 0.6, 0.6), rgb("#6a3a24")),
    part("Lid", "box", (0, 0.66, -0.02), (1.14, 0.1, 0.64), rgb("#7a4a2a")),
    part("BandL", "box", (-0.35, 0.36, 0), (0.06, 0.7, 0.62), BRASS),
    part("BandR", "box", (0.35, 0.36, 0), (0.06, 0.7, 0.62), BRASS),
    part("Clasp", "box", (0, 0.55, 0.31), (0.1, 0.12, 0.03), BRASS),
    part("Sleeve", "capsule", (0.2, 0.72, 0.2), (0.1, 0.22, 0.1), rgb("#e8b040"), r=(0, 0, 80)),
    part("Hat", "cyl", (-0.3, 0.75, 0.05), (0.3, 0.05, 0.3), rgb("#2a2a3a")),
    part("HatTop", "cyl", (-0.3, 0.86, 0.05), (0.18, 0.1, 0.18), rgb("#2a2a3a")),
    part("Star", "box", (0.05, 0.74, 0.28), (0.1, 0.1, 0.01), TIN, r=(0, 0, 45)),
    part("Sign", "box", (0, 0.36, 0.305), (0.5, 0.16, 0.01), rgb("#efe0c0")),
]

# One group of parts per piece, named Watch<Piece>..., worn over any outfit (head at 1.78, hands at 0.93).
WATCH = {
    "Sash": [part("WatchSash", "box", (0, 1.22, 0.185), (0.11, 0.78, 0.02), rgb("#e8b040"), r=(0, 0, -34)),
             part("WatchSashBack", "box", (0, 1.22, -0.18), (0.11, 0.78, 0.02), rgb("#d09a30"), r=(0, 0, 34)),
             part("WatchSashKnot", "sphere", (0.2, 0.93, 0.15), (0.12, 0.1, 0.06), rgb("#d09a30"))],
    "Charm": [part("WatchCharmString", "cyl", (0, 1.53, 0.0), (0.25, 0.006, 0.23), rgb("#3a2a1a")),
              part("WatchCharmCord", "box", (0, 1.47, 0.16), (0.006, 0.12, 0.006), rgb("#3a2a1a")),
              part("WatchCharm", "cyl", (0, 1.4, 0.19), (0.08, 0.008, 0.08), rgb("#e8e8f0"), "emissive", r=(90, 0, 0), e=0.5),
              part("WatchCharmBite", "cyl", (0.025, 1.41, 0.195), (0.065, 0.008, 0.065), rgb("#3a3a50"), r=(90, 0, 0))],
    "Bell": [part("WatchBell", "sphere", (-0.25, 0.86, 0.13), (0.08, 0.1, 0.08), BRASS),
             part("WatchBellRim", "cyl", (-0.25, 0.82, 0.13), (0.1, 0.01, 0.1), BRASS),
             part("WatchBellHandle", "cyl", (-0.25, 0.95, 0.13), (0.025, 0.04, 0.025), rgb("#5a3a20"))],
    "Lantern": [part("WatchLantern", "cyl", (0.27, 0.84, 0.12), (0.11, 0.08, 0.11), TIN),
                part("WatchLanternGlow", "cyl", (0.27, 0.84, 0.12), (0.115, 0.03, 0.115), rgb("#ffcf7a"), "emissive", e=1.8),
                part("WatchLanternHandle", "box", (0.27, 0.95, 0.12), (0.1, 0.012, 0.012), TIN)],
    "Badge": [part("WatchBadge", "box", (-0.12, 1.36, 0.19), (0.075, 0.075, 0.012), TIN, "emissive", e=0.3),
              part("WatchBadgeB", "box", (-0.12, 1.36, 0.19), (0.075, 0.075, 0.012), TIN, "emissive", r=(0, 0, 45), e=0.3)],
}

PROPS = {
    "jack": {"parts": JACK, "glow": rgb("#ff9a3a"), "glowY": 0.25},
    "pumpkin": {"parts": PUMPKIN},
    "turnip": {"parts": TURNIP, "glow": rgb("#ffa040"), "glowY": 0.25},
    "candle": {"parts": CANDLE, "glow": P["candle"], "glowY": 0.3},
    "scarecrow": {"parts": SCARECROW, "glow": rgb("#ff9a3a"), "glowY": 1.85},
    "haybale": {"parts": HAYBALE},
    "cauldron": {"parts": CAULDRON, "glow": P["wisp"], "glowY": 1.0},
    "crow": {"parts": CROW},
    "cobweb": {"parts": cobweb()},
    "lantern": {"parts": GRAVE_LANTERN, "glow": P["candle"], "glowY": 0.3},
    "van": {"parts": VAN},
    "streetlamp": {"parts": STREETLAMP, "glow": rgb("#ffcf7a"), "glowY": 3.9},
    "mailbox": {"parts": MAILBOX},
    "corn": {"parts": CORN},
    "callboard": {"parts": CALLBOARD, "glow": P["candle"], "glowY": 2.1},
    "bench": {"parts": BENCH},
    "jack_grin": {"parts": JACK_GRIN, "glow": rgb("#ff9a3a"), "glowY": 0.25},
    "jack_scary": {"parts": JACK_SCARY, "glow": rgb("#ff7a2a"), "glowY": 0.25},
    "jack_surprised": {"parts": JACK_SURPRISED, "glow": rgb("#ffa040"), "glowY": 0.25},
    "jack_wink": {"parts": JACK_WINK, "glow": rgb("#ff9a3a"), "glowY": 0.25},
    "jack_tall": {"parts": JACK_TALL, "glow": rgb("#ff9a3a"), "glowY": 0.35},
    "jack_white": {"parts": JACK_WHITE, "glow": rgb("#ffb05a"), "glowY": 0.25},
    "pumpkin_warty": {"parts": PUMPKIN_WARTY},
    "pumpkin_stack": {"parts": PUMPKIN_STACK, "glow": rgb("#ff9a3a"), "glowY": 1.2},
    "gourds": {"parts": GOURDS},
    "mums": {"parts": MUMS},
    "mums_purple": {"parts": MUMS_PURPLE},
    "cornstalks": {"parts": CORNSTALKS},
    "wreath": {"parts": WREATH},
    "ghost_hang": {"parts": GHOST_HANG, "glow": P["ghost"], "glowY": -1.1},
    "skeleton": {"parts": SKELETON},
    "tomb_round": {"parts": TOMB_ROUND},
    "tomb_cross": {"parts": TOMB_CROSS},
    "cat": {"parts": CAT},
    "luminaria": {"parts": LUMINARIA, "glow": P["candle"], "glowY": 0.2},
    "spider": {"parts": SPIDER},
    "bulb_orange": {"parts": bulb(rgb("#ff8a1a"))},
    "bulb_purple": {"parts": bulb(rgb("#b05aff"))},
    "bulb_green": {"parts": bulb(rgb("#7aff5a"))},
    "wall_lantern": {"parts": WALL_LANTERN, "glow": rgb("#ffcf7a"), "glowY": 0.0},
    "window_ghost": {"parts": WINDOW_GHOST},
    "party_table": {"parts": PARTY_TABLE, "glow": P["candle"], "glowY": 1.0},
    "banner": {"parts": banner()},
    "trunk": {"parts": TRUNK},
}

# ---------------------------------------------------------------------------
# Villains: the Haunter's costumes. Every one is a legend; the culprit is still one of the suspects.
# ---------------------------------------------------------------------------


def legs(c, boots, width=0.14, top=0.9):
    """Thighs and shins with a slight knee, and shoes with a sole, a rounded toe and a heel."""
    knee = top * 0.5
    sole = [round(v * 0.45, 3) for v in boots]
    out = []
    for side, x in (("L", -width), ("R", width)):
        out += [
            limb("Thigh" + side, "capsule", (x, top, 0), (x * 0.08, -1, 0.03), top - knee + 0.04, 0.22, c),
            limb("Shin" + side, "capsule", (x * 1.03, knee + 0.04, 0.015), (0, -1, -0.04), knee - 0.1, 0.19, c),
            part("Boot" + side, "box", (x, 0.1, 0.03), (0.2, 0.16, 0.28), boots),
            part("Toe" + side, "sphere", (x, 0.08, 0.17), (0.2, 0.14, 0.16), boots),
            part("Sole" + side, "box", (x, 0.015, 0.06), (0.21, 0.03, 0.36), sole),
            part("Heel" + side, "box", (x, 0.04, -0.1), (0.19, 0.06, 0.08), sole),
        ]
    return out


COAT = rgb("#1d2238")
HORSEMAN = legs(rgb("#17151d"), rgb("#2a1d14")) + [
    part("Coat", "capsule", (0, 1.12, 0), (0.66, 0.52, 0.5), COAT),
    part("CoatTails", "box", (0, 0.72, -0.08), (0.62, 0.5, 0.42), COAT),
    part("Belt", "box", (0, 0.95, 0), (0.62, 0.07, 0.48), rgb("#3a2a1a")),
    part("Buckle", "box", (0, 0.95, 0.245), (0.1, 0.08, 0.02), rgb("#b08d3c")),
    part("Shoulders", "box", (0, 1.55, 0), (0.84, 0.18, 0.44), COAT),
    part("Cape", "box", (0, 1.02, -0.29), (0.9, 1.3, 0.05), P["blood"], r=(8, 0, 0)),
    part("CapeLining", "box", (0, 1.02, -0.26), (0.84, 1.26, 0.02), rgb("#2a0810"), r=(8, 0, 0)),
    part("Collar", "box", (0, 1.68, -0.1), (0.52, 0.2, 0.28), COAT),
    part("NeckFlame", "sphere", (0, 1.8, 0.02), (0.26, 0.22, 0.26), P["ember"], "emissive", e=3.0),
    part("NeckFlameTip", "sphere", (0, 1.96, 0.02), (0.13, 0.2, 0.13), P["carve"], "emissive", e=3.2),
    limb("ArmL", "capsule", (-0.44, 1.55, 0), (-0.1, 0.65, 0.75), 0.62, 0.18, COAT),
    limb("ArmR", "capsule", (0.44, 1.55, 0), (0.05, -0.8, 0.6), 0.6, 0.18, COAT),
    part("GloveL", "sphere", (-0.5, 1.95, 0.46), (0.14, 0.14, 0.14), rgb("#2a1d14")),
    part("GloveR", "sphere", (0.47, 1.08, 0.36), (0.14, 0.14, 0.14), rgb("#2a1d14")),
    limb("Blade", "box", (0.47, 1.08, 0.36), (0, 0.5, 0.87), 1.05, 0.05, rgb("#c9ced9")),
    part("Hilt", "box", (0.47, 1.08, 0.36), (0.24, 0.05, 0.05), rgb("#b08d3c")),
] + place(JACK, (-0.5, 1.98, 0.5), 0.78, k="mask", prefix="Head")

GHOST_GOWN = P["ghost"]
BANSHEE = [
    part("Gown", "cyl", (0, 0.62, 0), (0.78, 0.36, 0.78), GHOST_GOWN, "ghost", e=0.6),
    part("Torso", "capsule", (0, 1.18, 0), (0.5, 0.42, 0.42), GHOST_GOWN, "ghost", e=0.6),
] + [
    part(f"Tatter{i}", "box", (math.sin(a) * 0.33, 0.3, math.cos(a) * 0.33), (0.16, 0.42, 0.03), GHOST_GOWN, "ghost",
         (12, math.degrees(a), 0), 0.6)
    for i, a in enumerate(i * math.pi / 4 for i in range(8))
] + [
    part("Face", "sphere", (0, 1.76, 0.02), (0.3, 0.36, 0.3), rgb("#e4efe9")),
    part("Hair", "box", (0, 1.42, -0.13), (0.44, 0.95, 0.12), rgb("#e8e8f2")),
    part("HairTop", "sphere", (0, 1.83, -0.05), (0.38, 0.34, 0.36), rgb("#e8e8f2")),
    part("EyeL", "sphere", (-0.07, 1.8, 0.15), (0.07, 0.05, 0.04), rgb("#7ffcff"), "emissive", e=3.0),
    part("EyeR", "sphere", (0.07, 1.8, 0.15), (0.07, 0.05, 0.04), rgb("#7ffcff"), "emissive", e=3.0),
    part("Wail", "sphere", (0, 1.65, 0.15), (0.08, 0.13, 0.04), rgb("#14081a")),
    limb("ArmL", "capsule", (-0.25, 1.48, 0.02), (-0.9, 0.35, 0.3), 0.62, 0.13, GHOST_GOWN, "ghost"),
    limb("ArmR", "capsule", (0.25, 1.48, 0.02), (0.9, 0.35, 0.3), 0.62, 0.13, GHOST_GOWN, "ghost"),
    part("HandL", "sphere", (-0.79, 1.7, 0.2), (0.11, 0.11, 0.11), rgb("#e4efe9")),
    part("HandR", "sphere", (0.79, 1.7, 0.2), (0.11, 0.11, 0.11), rgb("#e4efe9")),
    part("Shroud", "box", (0, 1.98, -0.03), (0.46, 0.14, 0.44), rgb("#8fbfb4"), "ghost", e=0.5, k="mask"),
    part("ShroudL", "box", (-0.21, 1.74, -0.03), (0.06, 0.44, 0.44), rgb("#8fbfb4"), "ghost", e=0.5, k="mask"),
    part("ShroudR", "box", (0.21, 1.74, -0.03), (0.06, 0.44, 0.44), rgb("#8fbfb4"), "ghost", e=0.5, k="mask"),
]

JACK_COAT = rgb("#3b2a46")
STINGY_JACK = legs(rgb("#2d2420"), rgb("#1c1410"), 0.12) + [
    part("Coat", "capsule", (0, 1.1, 0), (0.56, 0.55, 0.42), JACK_COAT),
    part("CoatHem", "box", (0, 0.68, 0), (0.6, 0.3, 0.44), JACK_COAT),
    part("PatchA", "box", (-0.14, 1.2, 0.21), (0.14, 0.14, 0.02), rgb("#5a7a3a")),
    part("PatchB", "box", (0.12, 0.8, 0.225), (0.12, 0.1, 0.02), P["pumpkin"]),
    part("Scarf", "box", (0, 1.58, 0.02), (0.44, 0.12, 0.38), P["pumpkin"]),
    part("ScarfTail", "box", (0.12, 1.38, 0.2), (0.1, 0.36, 0.04), P["pumpkin"], r=(0, 0, -10)),
    part("Head", "sphere", (0, 1.83, 0), (0.34, 0.36, 0.34), rgb("#a8b88a")),
    limb("ArmL", "capsule", (-0.34, 1.55, 0), (-0.25, -0.95, 0.1), 0.62, 0.16, JACK_COAT),
    limb("ArmR", "capsule", (0.34, 1.55, 0), (0.2, -0.45, 0.85), 0.55, 0.16, JACK_COAT),
    part("Staff", "cyl", (0.47, 1.25, 0.47), (0.05, 0.95, 0.05), rgb("#5b4027")),
    part("HatBrim", "cyl", (0, 2.02, 0), (0.76, 0.015, 0.76), rgb("#221a26"), r=(0, 0, -8), k="mask"),
    part("HatCrown", "cyl", (0.02, 2.17, 0), (0.32, 0.14, 0.32), rgb("#221a26"), r=(0, 0, -8), k="mask"),
    part("HatBand", "cyl", (0.01, 2.08, 0), (0.33, 0.03, 0.33), P["pumpkin"], r=(0, 0, -8), k="mask"),
    part("Grin", "box", (0, 1.83, 0.16), (0.3, 0.27, 0.05), P["bone"], k="mask"),
    part("EyeL", "box", (-0.07, 1.88, 0.19), (0.06, 0.04, 0.02), P["ember"], "emissive", e=3.0, k="mask"),
    part("EyeR", "box", (0.07, 1.88, 0.19), (0.06, 0.04, 0.02), P["ember"], "emissive", e=3.0, k="mask"),
    part("Smile", "box", (0, 1.76, 0.19), (0.18, 0.03, 0.02), P["ember"], "emissive", e=3.0, k="mask"),
] + place(TURNIP, (0.47, 2.2, 0.47), 0.5, prefix="Lantern")

CRONE = rgb("#8a9a7a")
BABA_YAGA = [
    part("Mortar", "cyl", (0, 0.45, 0), (0.86, 0.45, 0.86), rgb("#5a4634")),
    part("MortarBand", "cyl", (0, 0.65, 0), (0.88, 0.04, 0.88), P["iron"]),
    part("MortarRim", "cyl", (0, 0.89, 0), (0.92, 0.03, 0.92), rgb("#3d2e22")),
    part("Body", "capsule", (0, 1.12, 0.03), (0.5, 0.4, 0.45), rgb("#3a3d2a"), r=(18, 0, 0)),
    part("Shawl", "box", (0, 1.4, 0.06), (0.62, 0.22, 0.46), rgb("#7a2626"), r=(18, 0, 0)),
    part("ShawlTrim", "box", (0, 1.3, 0.3), (0.5, 0.06, 0.03), P["carve"], r=(18, 0, 0)),
    part("Face", "sphere", (0, 1.62, 0.22), (0.27, 0.3, 0.27), CRONE),
    part("Nose", "box", (0, 1.6, 0.38), (0.05, 0.06, 0.15), CRONE, r=(18, 0, 0)),
    part("Wart", "sphere", (0.02, 1.62, 0.44), (0.03, 0.03, 0.03), rgb("#5a6a4a")),
    part("EyeL", "sphere", (-0.06, 1.67, 0.33), (0.05, 0.04, 0.03), rgb("#c8ff5a"), "emissive", e=3.0),
    part("EyeR", "sphere", (0.06, 1.67, 0.33), (0.05, 0.04, 0.03), rgb("#c8ff5a"), "emissive", e=3.0),
    limb("ArmR", "capsule", (0.3, 1.38, 0.1), (0.4, -0.2, 0.9), 0.48, 0.14, rgb("#3a3d2a")),
    limb("Pestle", "capsule", (0.6, 0.6, 0.0), (0.15, 1.0, 0.45), 1.5, 0.09, rgb("#7a5a3a")),
    part("Hand", "sphere", (0.48, 1.3, 0.33), (0.1, 0.1, 0.1), CRONE),
    part("Headscarf", "sphere", (0, 1.7, 0.18), (0.34, 0.3, 0.34), rgb("#6e2a52"), k="mask"),
    part("ScarfKnot", "box", (0, 1.52, 0.05), (0.12, 0.1, 0.08), rgb("#6e2a52"), k="mask"),
    part("ScarfDots", "box", (0, 1.82, 0.2), (0.22, 0.03, 0.2), P["carve"], k="mask"),
    part("HairL", "box", (-0.14, 1.52, 0.2), (0.04, 0.22, 0.06), rgb("#bdbdbd")),
    part("HairR", "box", (0.14, 1.52, 0.2), (0.04, 0.22, 0.06), rgb("#bdbdbd")),
]

VILLAINS = [
    {"id": "HeadlessHorseman", "name": "The Headless Horseman", "origin": "Sleepy Hollow, New York (1820)",
     "legend": "A Hessian trooper who lost his head to a cannonball. He rides at night looking for it, "
               "and throws a flaming jack-o'-lantern in its place.",
     "power": "Pumpkin Toss", "powerBlurb": "hurl a flaming jack-o'-lantern that bursts in a ring of fear",
     "speed": 1.2, "hover": 0.0, "glow": P["ember"], "mask": [-0.5, 1.98, 0.5], "parts": HORSEMAN},
    {"id": "Banshee", "name": "The Banshee", "origin": "Irish folklore (bean sidhe)",
     "legend": "A pale spirit whose wail foretells a death in the family. Hearing it means trouble.",
     "power": "Wail", "powerBlurb": "a scream heard through walls: big fear, flashlights knocked out",
     "speed": 1.0, "hover": 0.25, "glow": rgb("#7ffcff"), "mask": [0, 1.85, 0], "parts": BANSHEE},
    {"id": "StingyJack", "name": "Stingy Jack", "origin": "Irish folk tale, the first jack-o'-lantern",
     "legend": "He tricked the Devil twice, so neither Heaven nor Hell would have him. He wanders with "
               "a coal in a carved turnip: the will-o'-the-wisp.",
     "power": "Wisp Lure", "powerBlurb": "three wisps drift out and hunt Solvers; a flashlight pops them",
     "speed": 1.05, "hover": 0.0, "glow": rgb("#ffa040"), "mask": [0, 1.95, 0.05], "parts": STINGY_JACK},
    {"id": "BabaYaga", "name": "Baba Yaga", "origin": "Slavic folklore",
     "legend": "The bony-legged witch of the deep woods. She flies in a mortar, steers with a pestle "
               "and curses anyone who wanders too close to her hut.",
     "power": "Hex", "powerBlurb": "curse the nearest Solver: fear spikes and their flashlight drains",
     "speed": 1.1, "hover": 0.3, "glow": rgb("#c8ff5a"), "mask": [0, 1.7, 0.15], "parts": BABA_YAGA},
]

# ---------------------------------------------------------------------------
# Suspects and the Mystery Club
# ---------------------------------------------------------------------------
SKIN = [rgb("#f1c9a5"), rgb("#c58c63"), rgb("#8d5a3b"), rgb("#e8b48f")]


def shade(c, k):
    return [round(min(1.0, v * k), 3) for v in c]


def mix(a, b, t):
    return [round(x + (y - x) * t, 3) for x, y in zip(a, b)]


def face(skin, y=1.78, eyes=rgb("#3a2a1e")):
    """
    Eyes with whites, a two-tone iris, lids, lashes and a lower lid; brows; a nose with a bridge, a
    tip, wings and nostrils; both lips (only "Lips", the lower one, moves when talking); a chin and
    cheekbones; ears with an inner fold. FaceLife.cs looks for Lid*, Lash*, Eye*, Iris*, Pupil*,
    Glint*, Brow* and Lips by name.
    """
    brow = shade(skin, 0.42)
    lip = mix(shade(skin, 0.82), [0.72, 0.36, 0.36], 0.45 if skin[0] > 0.8 else 0.22)
    blush = mix(skin, [0.95, 0.55, 0.5], 0.07)
    out = [
        part("Jaw", "sphere", (0, y - 0.095, 0.025), (0.27, 0.19, 0.26), skin),
        part("Chin", "sphere", (0, y - 0.158, 0.1), (0.105, 0.07, 0.075), shade(skin, 0.99)),
        part("NoseBridge", "capsule", (0, y + 0.012, 0.16), (0.034, 0.05, 0.03), shade(skin, 0.97), r=(-14, 0, 0)),
        part("Nose", "sphere", (0, y - 0.03, 0.174), (0.042, 0.038, 0.042), shade(skin, 0.97)),
        part("NoseWingL", "sphere", (-0.022, y - 0.04, 0.163), (0.03, 0.028, 0.03), shade(skin, 0.93)),
        part("NoseWingR", "sphere", (0.022, y - 0.04, 0.163), (0.03, 0.028, 0.03), shade(skin, 0.93)),
        part("NostrilL", "sphere", (-0.013, y - 0.052, 0.178), (0.012, 0.007, 0.01), shade(skin, 0.45)),
        part("NostrilR", "sphere", (0.013, y - 0.052, 0.178), (0.012, 0.007, 0.01), shade(skin, 0.45)),
        part("Mouth", "capsule", (0, y - 0.091, 0.148), (0.012, 0.042, 0.012), shade(skin, 0.35), r=(0, 0, 90)),
        part("LipTop", "capsule", (0, y - 0.085, 0.151), (0.011, 0.043, 0.018), shade(lip, 0.88), r=(0, 0, 90)),
        part("Lips", "capsule", (0, y - 0.098, 0.149), (0.017, 0.038, 0.022), lip, r=(0, 0, 90)),
        part("CheekL", "sphere", (-0.085, y - 0.04, 0.112), (0.08, 0.055, 0.045), blush),
        part("CheekR", "sphere", (0.085, y - 0.04, 0.112), (0.08, 0.055, 0.045), blush),
    ]
    for side, x in (("L", -1), ("R", 1)):
        out += [
            part("Ear" + side, "sphere", (x * 0.162, y - 0.005, -0.005), (0.04, 0.08, 0.05), shade(skin, 0.95), r=(0, x * 18, 0)),
            part("EarInner" + side, "sphere", (x * 0.176, y - 0.005, 0.003), (0.012, 0.05, 0.028), shade(skin, 0.75), r=(0, x * 18, 0)),
        ]
    for side, x in (("L", -0.062), ("R", 0.062)):
        out += [
            part("EyeWhite" + side, "sphere", (x, y + 0.026, 0.14), (0.064, 0.044, 0.036), rgb("#f2ece2")),
            part("Eye" + side, "sphere", (x, y + 0.025, 0.154), (0.034, 0.036, 0.014), shade(eyes, 0.8)),
            part("Iris" + side, "sphere", (x, y + 0.023, 0.158), (0.025, 0.026, 0.01), shade(eyes, 1.45)),
            part("Pupil" + side, "sphere", (x, y + 0.025, 0.161), (0.014, 0.015, 0.008), rgb("#0d0a10")),
            part("Glint" + side, "sphere", (x + 0.008, y + 0.034, 0.164), (0.007, 0.007, 0.004), rgb("#ffffff"), "emissive", e=0.8),
            part("Lid" + side, "sphere", (x, y + 0.058, 0.133), (0.07, 0.024, 0.042), shade(skin, 0.9)),
            part("Lash" + side, "capsule", (x, y + 0.05, 0.152), (0.008, 0.035, 0.008), rgb("#1a1214"), r=(0, 0, 90 + (6 if x < 0 else -6))),
            part("LidLow" + side, "capsule", (x, y + 0.006, 0.148), (0.01, 0.03, 0.012), shade(skin, 0.93), r=(0, 0, 90)),
            part("Brow" + side, "capsule", (x * 1.05, y + 0.087, 0.15), (0.016, 0.046, 0.018), brow, r=(0, 0, 90 + (-7 if x < 0 else 7))),
        ]
    return out


def hand(n, at, skin, side):
    """A palm, four separate fingers that curl a little, knuckles and a thumb."""
    x, y, z = at
    sx = -1 if side == "L" else 1
    out = [part(n, "sphere", (x, y, z), (0.07, 0.1, 0.088), skin),
           part(n + "Knuckles", "capsule", (x + sx * 0.004, y - 0.045, z + 0.004), (0.05, 0.04, 0.05), shade(skin, 0.96), r=(90, 0, 0))]
    for i, (dz, ln) in enumerate(((0.03, 0.075), (0.01, 0.085), (-0.01, 0.08), (-0.028, 0.065))):
        out.append(limb(n + "Finger" + str(i + 1), "capsule", (x + sx * 0.002, y - 0.05, z + dz), (-sx * 0.12, -1, 0.06), ln, 0.022, skin))
    out.append(limb(n + "Thumb", "capsule", (x - sx * 0.02, y - 0.015, z + 0.035), (-sx * 0.3, -0.9, 0.35), 0.06, 0.028, skin))
    return out


def person(top, bottom, skin, shoes=rgb("#2a1d14"), dress=False):
    """
    A resident of Hollow Creek: sloping shoulders, a chest that narrows to the waist, hips, a neck,
    a face with real features, two-part arms with elbows and hands with fingers, creased trousers
    or a skirt and proper shoes. Accessories in SUSPECTS / HOUSE_SUSPECTS sit on top (the head is
    centred at y 1.78, hands at y 0.93), then CHARACTERS gives each person hair, a height and a build.
    """
    collar = shade(top, 0.8)
    seam = shade(top, 0.82)
    base = [
        part("Chest", "capsule", (0, 1.3, 0), (0.52, 0.25, 0.34), top),
        part("ShoulderLine", "capsule", (0, 1.45, -0.01), (0.15, 0.27, 0.27), top, r=(0, 0, 90)),
        part("Waist", "capsule", (0, 1.07, 0), (0.43, 0.19, 0.3), shade(top, 0.96)),
        part("Hips", "capsule", (0, 0.92, 0), (0.46, 0.14, 0.32), bottom if not dress else top),
        part("Collar", "cyl", (0, 1.54, 0), (0.19, 0.03, 0.17), collar),
        part("CollarPointL", "box", (-0.05, 1.51, 0.085), (0.07, 0.05, 0.015), collar, r=(-20, 0, 32)),
        part("CollarPointR", "box", (0.05, 1.51, 0.085), (0.07, 0.05, 0.015), collar, r=(-20, 0, -32)),
        part("Placket", "box", (0, 1.24, 0.168), (0.03, 0.42, 0.01), seam),
        part("ButtonA", "sphere", (0, 1.38, 0.172), (0.025, 0.025, 0.015), shade(top, 0.55)),
        part("ButtonB", "sphere", (0, 1.24, 0.172), (0.025, 0.025, 0.015), shade(top, 0.55)),
        part("ButtonC", "sphere", (0, 1.1, 0.152), (0.025, 0.025, 0.015), shade(top, 0.55)),
        part("Neck", "cyl", (0, 1.585, -0.01), (0.12, 0.075, 0.12), shade(skin, 0.92)),
        part("NeckShadow", "sphere", (0, 1.63, 0.0), (0.13, 0.05, 0.12), shade(skin, 0.8)),
        part("Head", "sphere", (0, 1.78, 0), (0.32, 0.37, 0.33), skin),
    ] + face(skin)
    for side, sx in (("L", -1), ("R", 1)):
        shoulder, elbow, wrist = (sx * 0.27, 1.45, 0), (sx * 0.36, 1.2, -0.02), (sx * 0.44, 0.99, 0.03)
        base += [
            part("Shoulder" + side, "sphere", (shoulder[0], 1.43, 0), (0.14, 0.13, 0.14), top),
            limb("UpperArm" + side, "capsule", shoulder, tuple(e - s for e, s in zip(elbow, shoulder)), 0.29, 0.13, top),
            part("Elbow" + side, "sphere", elbow, (0.115, 0.115, 0.115), shade(top, 0.97)),
            limb("Forearm" + side, "capsule", elbow, tuple(w - e for w, e in zip(wrist, elbow)), 0.24, 0.115, top),
            part("Cuff" + side, "cyl", (wrist[0], wrist[1] + 0.02, wrist[2]), (0.115, 0.02, 0.115), collar),
            part("Wrist" + side, "cyl", (wrist[0], wrist[1] - 0.015, wrist[2]), (0.07, 0.02, 0.07), shade(skin, 0.95)),
        ] + hand("Hand" + side, (sx * 0.45, 0.93, 0.03), skin, side)
    if dress:
        base += [part("Skirt", "cyl", (0, 0.62, 0), (0.6, 0.32, 0.58), bottom),
                 part("SkirtFlare", "cyl", (0, 0.36, 0), (0.7, 0.07, 0.66), shade(bottom, 0.92)),
                 part("Hem", "cyl", (0, 0.29, 0), (0.71, 0.015, 0.67), shade(bottom, 0.7))]
        for i in range(6):  # pleats: darker folds down the skirt
            a = math.radians(i * 60 + 30)
            base.append(part("Pleat" + str(i + 1), "box", (math.sin(a) * 0.3, 0.6, math.cos(a) * 0.29), (0.02, 0.58, 0.02), shade(bottom, 0.78), r=(0, i * 60 + 30, 0)))
        for side, sx in (("L", -1), ("R", 1)):
            base += [limb("Ankle" + side, "capsule", (sx * 0.1, 0.3, 0), (0, -1, 0), 0.22, 0.09, skin),
                     part("Shoe" + side, "box", (sx * 0.1, 0.045, 0.04), (0.12, 0.08, 0.22), shoes),
                     part("ShoeToe" + side, "sphere", (sx * 0.1, 0.045, 0.14), (0.12, 0.08, 0.09), shoes),
                     part("ShoeHeel" + side, "box", (sx * 0.1, 0.03, -0.06), (0.06, 0.06, 0.05), shade(shoes, 0.6))]
    else:
        base += [part("Belt", "cyl", (0, 0.98, 0), (0.47, 0.03, 0.33), shade(bottom, 0.5)),
                 part("BeltBuckle", "box", (0, 0.98, 0.165), (0.06, 0.045, 0.02), rgb("#b8a060")),
                 part("Fly", "box", (0, 0.88, 0.16), (0.02, 0.12, 0.01), shade(bottom, 0.75))]
        base += legs(bottom, shoes, 0.12, 0.88)
        for side, x in (("L", -0.12), ("R", 0.12)):  # pressed creases down the front of each leg
            base += [limb("Crease" + side, "box", (x, 0.86, 0.105), (x * 0.08, -1, 0.0), 0.4, 0.01, shade(bottom, 0.78)),
                     limb("ShinCrease" + side, "box", (x * 1.03, 0.46, 0.105), (0, -1, -0.04), 0.3, 0.01, shade(bottom, 0.78))]
    return base


def spectacles(c, y=1.805, z=0.165, round_rims=False):
    """Wire spectacles you can see the eyes through: a rim above and below each eye, the sides,
    a bridge and arms back to the ears."""
    out = [part("SpecBridge", "box", (0, y + 0.005, z + 0.005), (0.04, 0.01, 0.01), c)]
    for side, x in (("L", -0.062), ("R", 0.062)):
        out += [part("RimTop" + side, "box", (x, y + 0.032, z), (0.085, 0.01, 0.01), c),
                part("RimLow" + side, "box", (x, y - 0.026, z - 0.004), (0.08, 0.01, 0.01), c),
                part("RimOut" + side, "box", (x * 1.66, y + 0.003, z - 0.006), (0.01, 0.06, 0.01), c),
                part("RimIn" + side, "box", (x * 0.36, y + 0.003, z), (0.01, 0.055, 0.01), c),
                part("SpecArm" + side, "box", (x * 2.6, y + 0.01, z - 0.09), (0.008, 0.008, 0.18), c)]
    return out


def hair(style, c, y=1.78):
    """Hair that frames the face instead of a helmet: a crown, the back of the head, and per style
    sideburns, a fringe, side curtains or a fall down the back."""
    if style == "none":
        return []
    dark = shade(c, 0.8)
    out = []
    if style != "bald":
        out += [part("HairCrown", "sphere", (0, y + 0.115, -0.035), (0.35, 0.24, 0.36), c),
                part("HairBack", "sphere", (0, y + 0.02, -0.07), (0.345, 0.32, 0.3), dark)]
    if style in ("short", "parted", "bald"):
        out += [part("SideburnL", "capsule", (-0.152, y + 0.01, 0.045), (0.022, 0.045, 0.03), dark),
                part("SideburnR", "capsule", (0.152, y + 0.01, 0.045), (0.022, 0.045, 0.03), dark)]
    if style == "bald":
        out += [part("HairRing", "sphere", (0, y - 0.0, -0.075), (0.34, 0.14, 0.28), c)]
    if style == "parted":
        out += [part("HairSweep", "capsule", (0.03, y + 0.13, 0.11), (0.06, 0.13, 0.07), c, r=(0, 0, 70)),
                part("HairPart", "box", (-0.06, y + 0.19, 0.06), (0.008, 0.01, 0.16), shade(c, 0.6), r=(-25, 0, 0))]
    if style in ("short",):
        out += [part("Fringe", "capsule", (0, y + 0.12, 0.115), (0.07, 0.12, 0.06), c, r=(0, 0, 90))]
    if style in ("bob", "long", "updo"):
        out += [part("HairFront", "capsule", (0, y + 0.13, 0.1), (0.08, 0.13, 0.07), c, r=(0, 0, 90))]
        for side, x in (("L", -1), ("R", 1)):
            out.append(part("HairTemple" + side, "sphere", (x * 0.13, y + 0.08, 0.06), (0.11, 0.13, 0.12), c))
    if style in ("bob", "long"):
        for side, x in (("L", -1), ("R", 1)):
            out.append(part("HairCurtain" + side, "capsule", (x * 0.158, y - 0.05 if style == "bob" else y - 0.12, -0.0),
                            (0.07, 0.12 if style == "bob" else 0.2, 0.15), c, r=(0, 0, x * -4)))
    if style == "long":
        out.append(part("HairFall", "capsule", (0, y - 0.22, -0.12), (0.3, 0.26, 0.11), dark))
    if style == "curly":
        out += [part("HairBack", "sphere", (0, y + 0.0, -0.07), (0.35, 0.34, 0.3), dark)]
        for i, (cx, cy, cz) in enumerate(((-0.12, 0.13, 0.05), (0.0, 0.17, 0.07), (0.12, 0.13, 0.05), (-0.15, 0.03, 0.0),
                                          (0.15, 0.03, 0.0), (-0.07, 0.2, -0.05), (0.07, 0.2, -0.05), (0, 0.15, -0.12))):
            out.append(part("Curl" + str(i + 1), "sphere", (cx, y + cy, cz), (0.14, 0.13, 0.14), shade(c, 1.0 if i % 2 else 0.9)))
    return out


# Which existing parts a hair style replaces (the old one-sphere hair).
HAIR_REPLACES = {"Hair"}


def fit(parts, height=1.0, build=1.0):
    """
    A person's height (everything scales) and build (the body gets wider and deeper; the head
    and what's on it only follow the height, so faces don't stretch).
    """
    out = []
    for q in parts:
        x, y, z = q["p"]
        w = 1.0 if y >= 1.56 else build
        sx, sy, sz = q["s"]
        out.append(dict(q, p=[round(x * height * w, 3), round(y * height, 3), round(z * height * w, 3)],
                        s=[round(sx * height * w, 3), round(sy * height, 3), round(sz * height * w, 3)]))
    return out


def finish(cid, parts):
    """Applies CHARACTERS[cid]: hair (replacing a plain "Hair" sphere, keeping buns and braids), height, build."""
    spec = CHARACTERS.get(cid)
    if spec is None:
        return parts
    height, build, style, colour = spec
    old = next((q for q in parts if q["n"] in HAIR_REPLACES), None)
    if colour is None:
        colour = old["c"] if old else rgb("#3a2414")
    elif isinstance(colour, str):
        colour = rgb(colour)
    if style != "keep":
        parts = [q for q in parts if q["n"] not in HAIR_REPLACES]
        parts = parts[:1] + hair(style, colour) + parts[1:]  # under hats and buns, which come later
    return fit(parts, height, build)


# height, build, hair style (short, parted, bald, bob, long, updo, curly, none, keep), hair colour (None = the old Hair's)
CHARACTERS = {
    "Groundskeeper": (0.97, 1.05, "bald", "#cfcfcf"),
    "Heiress": (1.0, 0.93, "updo", None),
    "Rival": (1.05, 0.95, "short", "#2a1a14"),
    "Cook": (0.95, 1.12, "short", "#1a1410"),
    "PembertonCottage.Groundskeeper": (1.02, 1.1, "short", "#6b4426"),
    "PembertonCottage.Heiress": (0.97, 0.94, "updo", None),
    "PembertonCottage.Rival": (1.04, 0.96, "parted", None),
    "PembertonCottage.Cook": (0.93, 1.07, "none", None),
    "HollowCreekFarm.Groundskeeper": (1.04, 1.08, "short", "#7a5a3a"),
    "HollowCreekFarm.Heiress": (0.96, 0.95, "long", None),
    "HollowCreekFarm.Rival": (1.0, 1.0, "short", "#3a2a1a"),
    "HollowCreekFarm.Cook": (0.94, 1.08, "updo", None),
    "WillowLaneVictorian.Groundskeeper": (0.96, 1.02, "short", "#5a4030"),
    "WillowLaneVictorian.Heiress": (0.99, 0.93, "long", None),
    "WillowLaneVictorian.Rival": (1.06, 0.97, "bald", None),
    "WillowLaneVictorian.Cook": (0.95, 1.0, "updo", None),
    "HistoricalSociety.Groundskeeper": (1.0, 1.06, "short", "#a8a8ac"),
    "HistoricalSociety.Heiress": (0.94, 0.94, "updo", None),
    "HistoricalSociety.Rival": (1.06, 0.92, "parted", None),
    "HistoricalSociety.Cook": (0.93, 1.06, "curly", None),
    "Folk.Mayor": (0.98, 1.12, "bald", "#b8b8bc"),
    "Folk.Fortune": (0.9, 1.0, "updo", None),
    "Folk.Reverend": (1.07, 0.92, "bald", None),
    "Folk.Diner": (0.96, 1.04, "none", None),
    "Folk.Sheriff": (1.03, 1.0, "updo", None),
    "Sleuth": (1.0, 1.0, "short", "#6b4426"),
    "Techie": (0.97, 0.94, "none", None),
    "Brawn": (1.08, 1.14, "short", "#1a1410"),
    "Snacker": (0.95, 1.03, "parted", None),
}


SUSPECTS = {
    "Groundskeeper": person(rgb("#5f7a3a"), rgb("#4a5a3a"), SKIN[3], rgb("#3a2a1a")) + [
        part("Overalls", "box", (0, 1.05, 0.02), (0.5, 0.42, 0.42), rgb("#3d5a8a")),
        part("Beard", "sphere", (0, 1.66, 0.12), (0.26, 0.2, 0.14), rgb("#cfcfcf")),
        part("HatBrim", "cyl", (0, 1.98, 0), (0.62, 0.015, 0.62), P["straw"]),
        part("HatTop", "cyl", (0, 2.07, 0), (0.32, 0.09, 0.32), P["straw"]),
        part("Shears", "box", (0.5, 0.75, 0.1), (0.04, 0.45, 0.06), rgb("#9a9aa6")),
    ],
    "Heiress": person(rgb("#9a3a8a"), rgb("#be5aaa"), SKIN[0], rgb("#3a1a3a"), dress=True) + [
        part("Hair", "sphere", (0, 1.84, -0.04), (0.38, 0.36, 0.38), rgb("#2a1a14")),
        part("Bun", "sphere", (0, 1.98, -0.12), (0.18, 0.18, 0.18), rgb("#2a1a14")),
        part("Pearls", "cyl", (0, 1.55, 0.02), (0.3, 0.02, 0.3), P["bone"]),
        part("Tiara", "box", (0, 2.0, 0.08), (0.2, 0.05, 0.03), rgb("#e8d68a"), "emissive", e=0.8),
    ],
    "Rival": person(rgb("#283258"), rgb("#1e2440"), SKIN[1], rgb("#111111")) + [
        part("Shirt", "box", (0, 1.38, 0.18), (0.14, 0.3, 0.04), P["bone"]),
        part("Tie", "box", (0, 1.34, 0.205), (0.06, 0.24, 0.02), rgb("#8a2a2a")),
        part("HatBrim", "cyl", (0, 1.96, 0), (0.48, 0.015, 0.48), rgb("#111111")),
        part("HatTop", "cyl", (0, 2.14, 0), (0.32, 0.18, 0.32), rgb("#111111")),
        part("Monocle", "cyl", (0.07, 1.81, 0.17), (0.09, 0.005, 0.09), rgb("#e8c96a"), r=(90, 0, 0)),
        part("Mustache", "box", (0, 1.72, 0.16), (0.16, 0.03, 0.03), rgb("#2a1a14")),
    ],
    "Cook": person(rgb("#ebebdc"), rgb("#4a4a5a"), SKIN[2], rgb("#2a2a2a")) + [
        part("Apron", "box", (0, 1.0, 0.2), (0.44, 0.7, 0.03), rgb("#f6f6ef")),
        part("ChefHat", "cyl", (0, 2.06, 0), (0.32, 0.14, 0.32), rgb("#ffffff")),
        part("ChefPuff", "sphere", (0, 2.22, 0), (0.42, 0.22, 0.42), rgb("#ffffff")),
        part("Spoon", "box", (0.5, 1.05, 0.15), (0.04, 0.5, 0.05), rgb("#8a6a4a"), r=(20, 0, 0)),
        part("Flour", "sphere", (-0.2, 1.1, 0.2), (0.1, 0.1, 0.03), rgb("#ffffff")),
    ],
}

# Each house's case has its own cast in the same four slots (Cases.cs). Blackwood Manor's are the
# SUSPECTS above; these are the other three houses'. Ids are "<HouseId>.<slot>".
GOLD = rgb("#e8c96a")
HOUSE_SUSPECTS = {
    # Pemberton Cottage: The Rattling Teapot
    "PembertonCottage.Groundskeeper": person(rgb("#9a3a2a"), rgb("#3a4a6a"), SKIN[0], rgb("#4a3020")) + [  # Hank Moody, handyman
        part("FlannelL", "box", (-0.12, 1.3, 0.2), (0.12, 0.3, 0.02), rgb("#5a1e18")),
        part("FlannelR", "box", (0.12, 1.3, 0.2), (0.12, 0.3, 0.02), rgb("#5a1e18")),
        part("Cap", "sphere", (0, 1.92, 0), (0.36, 0.2, 0.36), rgb("#d8a83a")),
        part("CapBill", "box", (0, 1.9, 0.2), (0.26, 0.03, 0.16), rgb("#d8a83a")),
        part("Mustache", "box", (0, 1.72, 0.16), (0.18, 0.04, 0.03), rgb("#6b4426")),
        part("Toolbelt", "box", (0, 0.92, 0), (0.56, 0.08, 0.44), rgb("#6b4426")),
        part("HammerHandle", "box", (0.5, 0.82, 0.12), (0.04, 0.34, 0.04), rgb("#8a6a4a")),
        part("HammerHead", "box", (0.5, 1.0, 0.12), (0.14, 0.06, 0.06), rgb("#7a7a86")),
        part("Sawdust", "sphere", (-0.15, 0.6, 0.12), (0.12, 0.06, 0.04), rgb("#d8b880")),
    ],
    "PembertonCottage.Heiress": person(rgb("#e0b84a"), rgb("#3a8a8a"), SKIN[1], rgb("#7a2a3a"), dress=True) + [  # Daisy Pemberton
        part("Hair", "sphere", (0, 1.84, -0.04), (0.38, 0.36, 0.38), rgb("#d8b060")),
        part("Ponytail", "capsule", (0, 1.62, -0.2), (0.12, 0.2, 0.12), rgb("#d8b060"), r=(20, 0, 0)),
        part("HairClip", "box", (0.14, 1.94, 0.1), (0.08, 0.04, 0.03), rgb("#ff7ad8"), "emissive", e=1.2),
        part("Locket", "sphere", (0, 1.5, 0.2), (0.06, 0.07, 0.03), GOLD, "emissive", e=0.6),
        part("Ticket", "box", (-0.47, 0.98, 0.12), (0.14, 0.08, 0.01), rgb("#e05a3a")),
    ],
    "PembertonCottage.Rival": person(rgb("#6a6a72"), rgb("#55555c"), SKIN[3], rgb("#2a1a14")) + [  # Leonard Crisp, estate agent
        part("Shirt", "box", (0, 1.38, 0.18), (0.14, 0.3, 0.04), P["bone"]),
        part("BowTie", "box", (0, 1.52, 0.21), (0.14, 0.05, 0.02), rgb("#2a6a9a")),
        part("Hair", "sphere", (0, 1.9, -0.02), (0.36, 0.18, 0.36), rgb("#2a1a10")),  # slick with pomade
        part("Clipboard", "box", (-0.48, 1.05, 0.18), (0.24, 0.32, 0.02), rgb("#8a6a4a"), r=(-15, 0, 0)),
        part("Paper", "box", (-0.48, 1.04, 0.195), (0.2, 0.26, 0.005), rgb("#ffffff"), r=(-15, 0, 0)),
        part("SoldSign", "box", (0.52, 1.25, 0.1), (0.04, 0.3, 0.3), rgb("#c03030")),
    ],
    "PembertonCottage.Cook": person(rgb("#8a6aa8"), rgb("#5a3a4a"), SKIN[2], rgb("#2a2a2a"), dress=True) + [  # Beatrice Hollis
        part("Curls", "sphere", (0, 1.9, -0.02), (0.4, 0.26, 0.4), rgb("#cfcfd8")),
        part("CurlL", "sphere", (-0.16, 1.8, -0.02), (0.16, 0.18, 0.16), rgb("#cfcfd8")),
        part("CurlR", "sphere", (0.16, 1.8, -0.02), (0.16, 0.18, 0.16), rgb("#cfcfd8")),
    ] + spectacles(rgb("#3a2a4a")) + [
        part("Cane", "cyl", (-0.47, 0.47, 0.08), (0.04, 0.46, 0.04), rgb("#5a3a20")),  # a walking cane: her silhouette
        part("CaneHandle", "capsule", (-0.43, 0.95, 0.08), (0.04, 0.06, 0.04), rgb("#5a3a20"), r=(0, 0, 90)),
        part("Shawl", "sphere", (0, 1.42, -0.02), (0.6, 0.26, 0.44), rgb("#c8b8d8")),
        part("CupcakeBase", "cyl", (0.47, 1.05, 0.12), (0.14, 0.06, 0.14), rgb("#c89a5a")),
        part("CupcakeIcing", "sphere", (0.47, 1.13, 0.12), (0.16, 0.1, 0.16), rgb("#ffb0d0")),
        part("Brooch", "sphere", (-0.12, 1.45, 0.2), (0.06, 0.06, 0.02), P["pumpkin"], "emissive", e=0.5),
    ],
    # Hollow Creek Farm: The Hayloft Horror
    "HollowCreekFarm.Groundskeeper": person(rgb("#a83a2a"), rgb("#3d5a8a"), SKIN[1], rgb("#3a2a1a")) + [  # Abel Hatcher, farmer
        part("Bib", "box", (0, 1.2, 0.19), (0.34, 0.34, 0.03), rgb("#3d5a8a")),
        part("StrapL", "box", (-0.14, 1.45, 0.19), (0.05, 0.25, 0.02), rgb("#3d5a8a")),
        part("StrapR", "box", (0.14, 1.45, 0.19), (0.05, 0.25, 0.02), rgb("#3d5a8a")),
        part("HatBrim", "cyl", (0, 1.98, 0), (0.62, 0.015, 0.62), P["straw"]),
        part("HatTop", "cyl", (0, 2.07, 0), (0.32, 0.09, 0.32), P["straw"]),
        part("Hay", "box", (0, 1.7, 0.18), (0.02, 0.01, 0.12), P["hay"], r=(0, 25, 0)),
        part("Pitchfork", "cyl", (0.5, 1.0, 0.1), (0.04, 0.85, 0.04), rgb("#8a6a4a")),
        part("Tines", "box", (0.5, 1.9, 0.1), (0.2, 0.16, 0.02), rgb("#9a9aa6")),
    ],
    "HollowCreekFarm.Heiress": person(rgb("#d8731c"), rgb("#e88a2a"), SKIN[0], rgb("#5a2a14"), dress=True) + [  # Clementine, Harvest Queen
        part("Hair", "sphere", (0, 1.82, -0.05), (0.4, 0.4, 0.38), rgb("#a8441c")),
        part("Crown", "cyl", (0, 2.0, 0), (0.24, 0.07, 0.24), GOLD, "emissive", e=0.9),
        part("Sash", "box", (0, 1.25, 0.2), (0.12, 0.6, 0.02), P["bone"], r=(0, 0, 35)),
        part("Bouquet", "sphere", (-0.47, 1.0, 0.16), (0.2, 0.18, 0.2), rgb("#c8452a")),
        part("Glitter", "sphere", (0.1, 1.4, 0.21), (0.05, 0.05, 0.01), rgb("#ffe08a"), "emissive", e=1.4),
    ],
    "HollowCreekFarm.Rival": person(rgb("#8a7050"), rgb("#3a3a40"), SKIN[3], rgb("#111111")) + [  # Silas Crane, land developer
        part("Trench", "box", (0, 0.95, 0), (0.6, 0.7, 0.44), rgb("#8a7050")),
        part("Collar", "box", (0, 1.55, 0.05), (0.42, 0.1, 0.36), rgb("#6a5438")),
        part("HatBrim", "cyl", (0, 1.97, 0), (0.5, 0.015, 0.5), rgb("#2a2420")),
        part("HatTop", "cyl", (0, 2.06, 0), (0.32, 0.09, 0.32), rgb("#2a2420")),
        part("Band", "cyl", (0, 2.0, 0), (0.33, 0.02, 0.33), rgb("#8a2a2a")),
        part("Briefcase", "box", (0.5, 0.7, 0.05), (0.08, 0.3, 0.4), rgb("#3a2414")),
        part("Plans", "cyl", (-0.47, 1.0, 0.12), (0.08, 0.25, 0.08), rgb("#cfe0f0"), r=(60, 0, 0)),
    ],
    "HollowCreekFarm.Cook": person(rgb("#b8443a"), rgb("#b8443a"), SKIN[2], rgb("#2a2a2a"), dress=True) + [  # Ma Jessup, pie stand
        part("Gingham", "box", (0, 1.2, 0.205), (0.4, 0.3, 0.01), rgb("#f0e0d8")),
        part("Apron", "box", (0, 0.8, 0.36), (0.44, 0.5, 0.02), rgb("#f6f6ef")),
        part("Bun", "sphere", (0, 1.95, -0.1), (0.2, 0.2, 0.2), rgb("#e8e8e8")),
        part("Hair", "sphere", (0, 1.84, -0.04), (0.37, 0.32, 0.37), rgb("#e8e8e8")),
        part("PieTin", "cyl", (0.47, 1.05, 0.15), (0.3, 0.03, 0.3), rgb("#b0b0b8")),
        part("Pie", "cyl", (0.47, 1.08, 0.15), (0.27, 0.04, 0.27), rgb("#d89a4a")),
    ],
    # Willow Lane Victorian: The Music Box
    "WillowLaneVictorian.Groundskeeper": person(rgb("#3a3a30"), rgb("#2a2a24"), SKIN[2], rgb("#2a1d14")) + [  # Ezra Cole, caretaker
        part("Scarf", "capsule", (0, 1.56, 0.0), (0.12, 0.2, 0.12), rgb("#5a2a2a"), r=(0, 0, 90)), part("ScarfWrap", "cyl", (0, 1.55, 0), (0.33, 0.05, 0.3), rgb("#5a2a2a")), part("ScarfTail", "capsule", (0.08, 1.4, 0.17), (0.08, 0.16, 0.04), rgb("#5a2a2a"), r=(0, 0, -8)),
        part("FlatCap", "sphere", (0, 1.93, 0.02), (0.38, 0.16, 0.4), rgb("#4a4a3a")),
        part("CapBill", "box", (0, 1.9, 0.19), (0.3, 0.03, 0.1), rgb("#4a4a3a")),
        part("RakeHandle", "cyl", (0.5, 1.0, 0.1), (0.04, 0.85, 0.04), rgb("#8a6a4a")),
        part("RakeHead", "box", (0.5, 1.86, 0.1), (0.36, 0.05, 0.05), rgb("#7a7a86")),
        part("Lantern", "cyl", (-0.47, 0.8, 0.1), (0.14, 0.12, 0.14), rgb("#ffcf7a"), "emissive", e=1.6),
    ],
    "WillowLaneVictorian.Heiress": person(rgb("#2a1a2a"), rgb("#2a1a2a"), SKIN[0], rgb("#111111"), dress=True) + [  # Lavinia Ashcombe
        part("Hair", "sphere", (0, 1.88, -0.04), (0.36, 0.3, 0.36), rgb("#b8b0c0")),
        part("Updo", "sphere", (0, 2.02, -0.04), (0.22, 0.2, 0.22), rgb("#b8b0c0")),
        part("Shawl", "box", (0, 1.5, 0), (0.62, 0.14, 0.44), rgb("#5a3a6a")),
        part("HighCollar", "cyl", (0, 1.62, 0), (0.24, 0.06, 0.24), rgb("#2a1a2a")),
        part("Brooch", "sphere", (0, 1.56, 0.17), (0.07, 0.07, 0.02), rgb("#b47aff"), "emissive", e=1.2),
        part("Candle", "cyl", (0.47, 1.1, 0.12), (0.06, 0.12, 0.06), P["bone"]),
        part("Flame", "sphere", (0.47, 1.26, 0.12), (0.05, 0.08, 0.05), P["candle"], "emissive", e=2.0),
    ],
    "WillowLaneVictorian.Rival": person(rgb("#4a5a3a"), rgb("#3a3a30"), SKIN[3], rgb("#2a1a14")) + [  # Dr. Felix Marlowe, collector
        part("Waistcoat", "box", (0, 1.25, 0.19), (0.3, 0.36, 0.02), rgb("#7a2a2a")),
        part("WatchChain", "box", (0.06, 1.18, 0.205), (0.14, 0.015, 0.01), GOLD, r=(0, 0, -15)),
    ] + spectacles(GOLD) + [
        part("Beard", "sphere", (0, 1.65, 0.12), (0.2, 0.16, 0.12), rgb("#6a6a6a")),
        part("Hair", "sphere", (0, 1.9, -0.04), (0.36, 0.2, 0.36), rgb("#6a6a6a")),
        part("Pipe", "box", (0.06, 1.7, 0.22), (0.03, 0.03, 0.12), rgb("#3a2414")),
        part("MusicBox", "box", (-0.47, 1.0, 0.15), (0.24, 0.16, 0.18), rgb("#6b4426")),
        part("MusicBoxLid", "box", (-0.47, 1.1, 0.08), (0.24, 0.02, 0.18), rgb("#8a5a34"), r=(-50, 0, 0)),
    ],
    "WillowLaneVictorian.Cook": person(rgb("#1e1e26"), rgb("#1e1e26"), SKIN[1], rgb("#111111"), dress=True) + [  # Agnes Pratt, housekeeper
        part("Apron", "box", (0, 0.9, 0.36), (0.44, 0.6, 0.02), rgb("#f6f6ef")),
        part("Bib", "box", (0, 1.3, 0.2), (0.26, 0.26, 0.02), rgb("#f6f6ef")),
        part("Hair", "sphere", (0, 1.86, -0.04), (0.36, 0.3, 0.36), rgb("#3a2a1a")),
        part("MaidCap", "box", (0, 1.98, 0.02), (0.26, 0.06, 0.2), rgb("#ffffff")),
        part("KeyRing", "cyl", (-0.25, 0.9, 0.2), (0.12, 0.01, 0.12), GOLD, r=(90, 0, 0)),
        part("Key", "box", (-0.25, 0.8, 0.21), (0.03, 0.12, 0.01), GOLD),
        part("Duster", "sphere", (0.47, 1.15, 0.15), (0.16, 0.22, 0.16), rgb("#e8a0b0")),
    ],
    # Historical Society: The Mask Keeper (the fifth call)
    "HistoricalSociety.Groundskeeper": person(rgb("#2a3550"), rgb("#232a3e"), SKIN[3], rgb("#141414")) + [  # Walter Finch, night watchman
        part("CoatTails", "cyl", (0, 0.74, 0), (0.56, 0.2, 0.4), rgb("#263048")),
        part("Belt", "cyl", (0, 0.98, 0), (0.48, 0.04, 0.34), rgb("#14161e")),
        part("BeltBuckle", "box", (0, 0.98, 0.17), (0.08, 0.06, 0.02), GOLD),
        part("BrassBtnA", "sphere", (-0.09, 1.36, 0.18), (0.04, 0.04, 0.02), GOLD, "emissive", e=0.5),
        part("BrassBtnB", "sphere", (0.09, 1.36, 0.18), (0.04, 0.04, 0.02), GOLD, "emissive", e=0.5),
        part("BrassBtnC", "sphere", (-0.08, 1.18, 0.17), (0.04, 0.04, 0.02), GOLD, "emissive", e=0.5),
        part("BrassBtnD", "sphere", (0.08, 1.18, 0.17), (0.04, 0.04, 0.02), GOLD, "emissive", e=0.5),
        part("Cap", "cyl", (0, 1.98, 0), (0.36, 0.1, 0.38), rgb("#1e2638")),
        part("CapBand", "cyl", (0, 1.94, 0), (0.37, 0.03, 0.39), rgb("#0e1220")),
        part("CapBill", "box", (0, 1.92, 0.19), (0.28, 0.025, 0.12), rgb("#0e0e12"), r=(12, 0, 0)),
        part("CapBadge", "sphere", (0, 2.0, 0.19), (0.07, 0.07, 0.02), GOLD, "emissive", e=0.7),
        part("Mustache", "box", (0, 1.72, 0.16), (0.2, 0.035, 0.03), rgb("#8a8a8a")),
        part("KeyRing", "cyl", (0.28, 0.88, 0.2), (0.14, 0.012, 0.14), GOLD, r=(90, 0, 0)),
        part("KeyA", "box", (0.25, 0.78, 0.21), (0.03, 0.13, 0.01), GOLD),
        part("KeyB", "box", (0.31, 0.79, 0.21), (0.03, 0.11, 0.01), GOLD, r=(0, 0, 12)),
        part("Lantern", "cyl", (-0.47, 0.78, 0.1), (0.15, 0.14, 0.15), rgb("#ffd88a"), "emissive", e=1.8),
        part("LanternCap", "cyl", (-0.47, 0.88, 0.1), (0.12, 0.03, 0.12), rgb("#2a2a2a")),
        part("LanternHandle", "box", (-0.47, 0.94, 0.1), (0.02, 0.06, 0.12), rgb("#2a2a2a")),
    ],
    "HistoricalSociety.Heiress": person(rgb("#8a5a3a"), rgb("#4a3a50"), SKIN[1], rgb("#3a2414"), dress=True) + [  # Edie Wren, curator
        part("Blouse", "box", (0, 1.36, 0.18), (0.14, 0.3, 0.02), rgb("#efe6d6")),
        part("CardiganEdgeL", "box", (-0.085, 1.28, 0.18), (0.03, 0.42, 0.02), rgb("#6a4228")),
        part("CardiganEdgeR", "box", (0.085, 1.28, 0.18), (0.03, 0.42, 0.02), rgb("#6a4228")),
        part("Hair", "sphere", (0, 1.84, -0.04), (0.38, 0.34, 0.38), rgb("#2a1a14")),
        part("Bun", "sphere", (0, 1.92, -0.18), (0.18, 0.18, 0.18), rgb("#2a1a14")),
        part("Pencil", "box", (0.05, 1.98, -0.16), (0.02, 0.02, 0.24), rgb("#e8c040"), r=(0, 30, 0)),
    ] + spectacles(rgb("#3a2a1a")) + [
        part("Chain", "box", (0, 1.5, 0.19), (0.24, 0.012, 0.01), GOLD),
        part("InkL", "sphere", (-0.47, 0.88, 0.07), (0.06, 0.05, 0.03), rgb("#1a2440")),
        part("InkR", "sphere", (0.48, 0.87, 0.07), (0.05, 0.05, 0.03), rgb("#1a2440")),
        part("Catalogue", "box", (-0.48, 1.02, 0.14), (0.06, 0.3, 0.22), rgb("#5a2a2a")),
        part("CatalogueLabel", "box", (-0.448, 1.04, 0.14), (0.005, 0.08, 0.14), rgb("#efe6d6")),
    ],
    "HistoricalSociety.Rival": person(rgb("#3a3046"), rgb("#2e2838"), SKIN[0], rgb("#111111")) + [  # Mortimer Vane, treasurer
        part("Shirt", "box", (0, 1.38, 0.18), (0.14, 0.3, 0.04), P["bone"]),
        part("Cravat", "box", (0, 1.48, 0.21), (0.1, 0.12, 0.03), rgb("#7a1a2a")),
        part("Waistcoat", "box", (0, 1.22, 0.19), (0.32, 0.32, 0.02), rgb("#5a4a2a")),
        part("WatchChain", "box", (0.06, 1.16, 0.205), (0.16, 0.015, 0.01), GOLD, r=(0, 0, -15)),
        part("Hair", "sphere", (0, 1.88, -0.06), (0.34, 0.18, 0.34), rgb("#c8c8cc")),  # receding
        part("SideburnL", "sphere", (-0.155, 1.77, -0.03), (0.06, 0.13, 0.12), rgb("#c8c8cc")),
        part("SideburnR", "sphere", (0.155, 1.77, -0.03), (0.06, 0.13, 0.12), rgb("#c8c8cc")),
        part("PinceNez", "box", (0, 1.81, 0.17), (0.2, 0.035, 0.01), GOLD),
        part("Ledger", "box", (-0.48, 1.0, 0.14), (0.08, 0.36, 0.28), rgb("#2a3a2a")),
        part("LedgerPages", "box", (-0.44, 1.0, 0.14), (0.01, 0.33, 0.26), rgb("#efe6d6")),
        part("FountainPen", "box", (0.47, 1.0, 0.16), (0.03, 0.16, 0.03), rgb("#111111"), r=(20, 0, 0)),
        part("PenNib", "box", (0.47, 0.91, 0.19), (0.015, 0.03, 0.015), GOLD, r=(20, 0, 0)),
    ],
    "HistoricalSociety.Cook": person(rgb("#c86a5a"), rgb("#7a3a4a"), SKIN[2], rgb("#3a1a14"), dress=True) + [  # Rosa Delgado, tea room volunteer
        part("Apron", "box", (0, 0.86, 0.36), (0.44, 0.52, 0.02), rgb("#f6efe6")),
        part("Bib", "box", (0, 1.28, 0.2), (0.26, 0.24, 0.02), rgb("#f6efe6")),
        part("Frill", "box", (0, 0.6, 0.37), (0.46, 0.04, 0.02), rgb("#f0b8c0")),
        part("Hair", "sphere", (0, 1.85, -0.05), (0.4, 0.38, 0.4), rgb("#1a1210")),
        part("CurlL", "sphere", (-0.18, 1.7, -0.04), (0.16, 0.24, 0.16), rgb("#1a1210")),
        part("CurlR", "sphere", (0.18, 1.7, -0.04), (0.16, 0.24, 0.16), rgb("#1a1210")),
        part("Flower", "sphere", (0.16, 1.98, 0.08), (0.1, 0.1, 0.06), rgb("#e8504a"), "emissive", e=0.4),
        part("Earring", "sphere", (-0.17, 1.7, 0.02), (0.035, 0.035, 0.035), GOLD, "emissive", e=0.6),
        part("CakeStand", "cyl", (0.47, 0.98, 0.15), (0.3, 0.02, 0.3), rgb("#e8e8f0")),
        part("Cake", "cyl", (0.47, 1.06, 0.15), (0.24, 0.13, 0.24), rgb("#f0d6a8")),
        part("CakeIcing", "cyl", (0.47, 1.13, 0.15), (0.25, 0.03, 0.25), rgb("#ffb0c8")),
        part("Cherry", "sphere", (0.47, 1.17, 0.15), (0.05, 0.05, 0.05), rgb("#c01a2a")),
        part("RaffleTickets", "box", (-0.47, 1.0, 0.14), (0.14, 0.08, 0.01), rgb("#e8d040")),
    ],
}

# The grown-ups out in town tonight (HollowCreek.json "folk", Town/Townsperson.cs). Ids are "Folk.<id>".
FOLK = {
    "Folk.Mayor": person(rgb("#2a4a3a"), rgb("#5a5a62"), SKIN[0], rgb("#141414")) + [  # Mayor Harold Beaumont
        part("Belly", "sphere", (0, 1.12, 0.06), (0.5, 0.42, 0.42), rgb("#2a4a3a")),
        part("Waistcoat", "sphere", (0, 1.14, 0.1), (0.36, 0.34, 0.36), rgb("#d8a83a")),
        part("TailL", "box", (-0.14, 0.72, -0.12), (0.18, 0.36, 0.04), rgb("#22402f"), r=(-8, 0, 0)),
        part("TailR", "box", (0.14, 0.72, -0.12), (0.18, 0.36, 0.04), rgb("#22402f"), r=(-8, 0, 0)),
        part("Sash", "box", (0, 1.24, 0.26), (0.12, 0.66, 0.02), rgb("#b02a2a"), r=(0, 0, 34)),
        part("ChainOfOffice", "cyl", (0, 1.47, 0.08), (0.34, 0.02, 0.32), GOLD, "emissive", e=0.4),
        part("Medallion", "sphere", (0, 1.38, 0.24), (0.09, 0.09, 0.03), GOLD, "emissive", e=0.7),
        part("HatBrim", "cyl", (0, 1.97, 0), (0.46, 0.015, 0.46), rgb("#141414")),
        part("TopHat", "cyl", (0, 2.17, 0), (0.3, 0.2, 0.3), rgb("#141414")),
        part("HatBand", "cyl", (0, 2.02, 0), (0.31, 0.03, 0.31), rgb("#e0772a")),
        part("Mustache", "capsule", (0, 1.72, 0.16), (0.05, 0.12, 0.04), rgb("#b8b8bc"), r=(0, 0, 90)),
        part("SideHairL", "sphere", (-0.16, 1.8, -0.03), (0.06, 0.12, 0.14), rgb("#b8b8bc")),
        part("SideHairR", "sphere", (0.16, 1.8, -0.03), (0.06, 0.12, 0.14), rgb("#b8b8bc")),
        part("Rosette", "sphere", (-0.17, 1.38, 0.2), (0.1, 0.1, 0.03), rgb("#e0772a")),
    ],
    "Folk.Fortune": person(rgb("#5a2a6a"), rgb("#8a2a3a"), SKIN[1], rgb("#2a1a14"), dress=True) + [  # Old Nell Thistle
        part("Shawl", "sphere", (0, 1.42, 0), (0.62, 0.3, 0.46), rgb("#3a6a6a")),
        part("ShawlFringe", "cyl", (0, 1.28, 0), (0.6, 0.04, 0.44), rgb("#e8c96a")),
        part("Hair", "sphere", (0, 1.8, -0.06), (0.38, 0.4, 0.38), rgb("#d8d4dc")),
        part("HairLong", "capsule", (0, 1.52, -0.16), (0.3, 0.28, 0.14), rgb("#d8d4dc")),
        part("Headscarf", "sphere", (0, 1.9, -0.02), (0.38, 0.22, 0.38), rgb("#8a1a3a")),
        part("ScarfKnot", "sphere", (0.14, 1.86, -0.18), (0.1, 0.1, 0.1), rgb("#8a1a3a")),
        part("CoinA", "sphere", (-0.12, 1.86, 0.16), (0.04, 0.04, 0.01), GOLD, "emissive", e=0.6),
        part("CoinB", "sphere", (0, 1.85, 0.18), (0.04, 0.04, 0.01), GOLD, "emissive", e=0.6),
        part("CoinC", "sphere", (0.12, 1.86, 0.16), (0.04, 0.04, 0.01), GOLD, "emissive", e=0.6),
        part("HoopL", "cyl", (-0.17, 1.66, 0.0), (0.08, 0.008, 0.08), GOLD, r=(0, 0, 90)),
        part("HoopR", "cyl", (0.17, 1.66, 0.0), (0.08, 0.008, 0.08), GOLD, r=(0, 0, 90)),
        part("CrystalBall", "sphere", (0.47, 1.06, 0.18), (0.2, 0.2, 0.2), rgb("#9fd8ff"), "emissive", e=1.1),
        part("BallStand", "cyl", (0.47, 0.94, 0.18), (0.14, 0.04, 0.14), GOLD),
        part("Cards", "box", (-0.47, 1.0, 0.16), (0.1, 0.14, 0.02), rgb("#efe6d6"), r=(0, 0, 12)),
        part("Bangles", "cyl", (-0.46, 1.03, 0.03), (0.15, 0.04, 0.15), GOLD),
    ],
    "Folk.Reverend": person(rgb("#16161c"), rgb("#16161c"), SKIN[2], rgb("#0e0e0e")) + [  # Reverend Amos Gale
        part("CoatLong", "cyl", (0, 0.72, 0), (0.56, 0.24, 0.42), rgb("#121218")),
        part("ClericalCollar", "cyl", (0, 1.555, 0), (0.31, 0.04, 0.27), rgb("#f4f4f0")),
        part("CollarTab", "box", (0, 1.53, 0.15), (0.06, 0.05, 0.02), rgb("#f4f4f0")),
        part("Hair", "sphere", (0, 1.9, -0.05), (0.36, 0.18, 0.36), rgb("#9a9aa0")),
        part("Beard", "sphere", (0, 1.66, 0.11), (0.22, 0.18, 0.14), rgb("#9a9aa0")),
    ] + spectacles(rgb("#c8c8d0")) + [
        part("Bible", "box", (-0.48, 1.0, 0.15), (0.06, 0.3, 0.22), rgb("#2a1a14")),
        part("BibleCross", "box", (-0.445, 1.02, 0.15), (0.005, 0.14, 0.03), GOLD),
        part("Candle", "cyl", (0.47, 1.06, 0.12), (0.06, 0.14, 0.06), P["bone"]),
        part("CandleFlame", "sphere", (0.47, 1.22, 0.12), (0.05, 0.08, 0.05), P["candle"], "emissive", e=2.0),
    ],
    "Folk.Diner": person(rgb("#e88aa8"), rgb("#e88aa8"), SKIN[0], rgb("#7a1a2a"), dress=True) + [  # Dot Kowalski
        part("Apron", "box", (0, 0.86, 0.36), (0.42, 0.46, 0.02), rgb("#ffffff")),
        part("ApronBib", "box", (0, 1.28, 0.2), (0.24, 0.24, 0.02), rgb("#ffffff")),
        part("Collar", "cyl", (0, 1.54, 0), (0.33, 0.04, 0.29), rgb("#ffffff")),
        part("NameBadge", "box", (-0.14, 1.42, 0.21), (0.12, 0.05, 0.01), rgb("#f0d040")),
        part("Bouffant", "sphere", (0, 1.95, -0.04), (0.42, 0.34, 0.42), rgb("#b8401c")),
        part("HairBack", "sphere", (0, 1.8, -0.12), (0.38, 0.32, 0.3), rgb("#b8401c")),
        part("Bandana", "cyl", (0, 1.98, 0), (0.43, 0.06, 0.43), rgb("#d02a3a")),
        part("BandanaBow", "sphere", (0, 2.08, -0.12), (0.16, 0.08, 0.08), rgb("#d02a3a")),
        part("Pencil", "box", (0.16, 1.82, -0.04), (0.02, 0.02, 0.18), rgb("#e8c040"), r=(0, 70, 0)),
        part("CoffeePot", "cyl", (0.47, 1.0, 0.16), (0.16, 0.18, 0.16), rgb("#c8c8d0")),
        part("PotHandle", "box", (0.47, 1.02, 0.02), (0.03, 0.14, 0.06), rgb("#2a2a2a")),
        part("Coffee", "cyl", (0.47, 0.92, 0.16), (0.15, 0.08, 0.15), rgb("#3a2414")),
        part("Steam", "sphere", (0.47, 1.26, 0.18), (0.08, 0.14, 0.08), rgb("#e8e8f0"), "ghost", e=0.6),
    ],
    "Folk.Sheriff": person(rgb("#b89a6a"), rgb("#5a4030"), SKIN[3], rgb("#3a2414")) + [  # Sheriff Ruth Calloway
        part("PocketL", "box", (-0.12, 1.36, 0.19), (0.12, 0.1, 0.02), rgb("#a08658")),
        part("PocketR", "box", (0.12, 1.36, 0.19), (0.12, 0.1, 0.02), rgb("#a08658")),
        part("Badge", "sphere", (-0.12, 1.42, 0.21), (0.08, 0.08, 0.02), GOLD, "emissive", e=1.0),
        part("Tie", "box", (0, 1.38, 0.2), (0.06, 0.26, 0.02), rgb("#3a2414")),
        part("Belt", "cyl", (0, 0.98, 0), (0.5, 0.05, 0.36), rgb("#2a1a10")),
        part("Buckle", "box", (0, 0.98, 0.18), (0.09, 0.06, 0.02), rgb("#c8c8d0")),
        part("Holster", "box", (0.3, 0.86, 0.04), (0.08, 0.2, 0.12), rgb("#2a1a10")),
        part("Hair", "sphere", (0, 1.8, -0.08), (0.38, 0.36, 0.36), rgb("#3a2414")),
        part("Braid", "capsule", (0, 1.5, -0.2), (0.1, 0.24, 0.1), rgb("#3a2414")),
        part("HatBrim", "cyl", (0, 1.97, 0), (0.62, 0.015, 0.62), rgb("#8a6a3a")),
        part("HatCrown", "cyl", (0, 2.07, 0), (0.32, 0.1, 0.32), rgb("#8a6a3a")),
        part("HatDent", "box", (0, 2.17, 0), (0.06, 0.02, 0.26), rgb("#6a4e2a")),
        part("HatBand", "cyl", (0, 2.0, 0), (0.33, 0.025, 0.33), rgb("#3a2414")),
        part("Flashlight", "cyl", (-0.47, 0.94, 0.2), (0.08, 0.18, 0.08), rgb("#2a2a2a"), r=(70, 0, 0)),
        part("FlashlightLens", "cyl", (-0.47, 0.98, 0.29), (0.08, 0.01, 0.08), rgb("#fff0c0"), "emissive", r=(70, 0, 0), e=1.6),
    ],
}

SOLVERS = {
    "Sleuth": person(rgb("#3e7a4a"), rgb("#5a4a3a"), SKIN[0]) + [
        part("Deerstalker", "sphere", (0, 1.94, 0), (0.38, 0.22, 0.4), rgb("#a07a4a")),
        part("Brim", "box", (0, 1.9, 0.12), (0.22, 0.03, 0.18), rgb("#a07a4a")),
        part("Magnifier", "cyl", (0.52, 1.0, 0.15), (0.16, 0.01, 0.16), rgb("#9fd8ff"), "emissive", (90, 0, 0), 0.6),
        part("Scarf", "capsule", (0, 1.56, 0.0), (0.12, 0.2, 0.12), P["pumpkin"], r=(0, 0, 90)), part("ScarfWrap", "cyl", (0, 1.55, 0), (0.33, 0.05, 0.3), P["pumpkin"]), part("ScarfTail", "capsule", (0.08, 1.4, 0.17), (0.08, 0.16, 0.04), P["pumpkin"], r=(0, 0, -8)),
    ],
    "Techie": person(rgb("#2f5a9a"), rgb("#2a2a3a"), SKIN[1]) + [
        part("Hood", "sphere", (0, 1.84, -0.06), (0.4, 0.36, 0.38), rgb("#2f5a9a")),
        part("GoggleStrap", "cyl", (0, 1.9, 0.0), (0.345, 0.03, 0.35), rgb("#2a2a34"), r=(-12, 0, 0)),
        part("GoggleL", "cyl", (-0.065, 1.925, 0.15), (0.085, 0.03, 0.085), rgb("#8affff"), "emissive", r=(68, 0, 0), e=1.4),
        part("GoggleR", "cyl", (0.065, 1.925, 0.15), (0.085, 0.03, 0.085), rgb("#8affff"), "emissive", r=(68, 0, 0), e=1.4),
        part("GoggleRimL", "cyl", (-0.065, 1.922, 0.14), (0.1, 0.03, 0.1), rgb("#5a5a6a"), r=(68, 0, 0)),
        part("GoggleRimR", "cyl", (0.065, 1.922, 0.14), (0.1, 0.03, 0.1), rgb("#5a5a6a"), r=(68, 0, 0)),
        part("Backpack", "box", (0, 1.2, -0.27), (0.4, 0.5, 0.18), rgb("#5a5a6a")),
        part("Antenna", "cyl", (0.14, 1.6, -0.3), (0.02, 0.2, 0.02), rgb("#d0d0d0")),
        part("AntennaTip", "sphere", (0.14, 1.82, -0.3), (0.06, 0.06, 0.06), rgb("#ff3a3a"), "emissive", e=2.0),
    ],
    "Brawn": person(rgb("#a83232"), rgb("#2a3a5a"), SKIN[2]) + [
        part("Shoulders", "capsule", (0, 1.45, 0), (0.24, 0.36, 0.38), rgb("#a83232"), r=(0, 0, 90)),
        part("Chest2", "sphere", (0, 1.32, 0.04), (0.6, 0.4, 0.38), rgb("#a83232")),
        part("Cap", "sphere", (0, 1.92, 0), (0.36, 0.2, 0.36), rgb("#2a2a2a")),
        part("CapBill", "box", (0, 1.9, 0.2), (0.26, 0.03, 0.16), rgb("#2a2a2a")),
        part("Toolbelt", "box", (0, 0.92, 0), (0.56, 0.08, 0.44), rgb("#6b4426")),
        part("Wrench", "box", (0.25, 0.86, 0.2), (0.05, 0.22, 0.04), rgb("#9a9aa6")),
    ],
    "Snacker": person(rgb("#d8b23a"), rgb("#5a3a2a"), SKIN[3]) + [
        part("Hair", "sphere", (0, 1.88, -0.03), (0.38, 0.28, 0.38), rgb("#6b4426")),
        part("SnackBag", "box", (-0.45, 0.95, 0.2), (0.26, 0.32, 0.12), rgb("#e05a3a")),
        part("Sandwich", "box", (0.47, 1.0, 0.2), (0.24, 0.12, 0.2), rgb("#e8c87a")),
        part("Lettuce", "box", (0.47, 1.0, 0.2), (0.26, 0.03, 0.22), rgb("#6ac24a")),
    ],
}

data = {
    "palette": PAL,
    "villains": VILLAINS,
    "props": [dict(id=k, **v) for k, v in PROPS.items()],
    "suspects": [{"id": k, "parts": finish(k, v)} for k, v in {**SUSPECTS, **HOUSE_SUSPECTS, **FOLK}.items()],
    "solvers": [{"id": k, "parts": finish(k, v)} for k, v in SOLVERS.items()],
    # The Lantern Watch pieces for each Solver, at that Solver's height and build: "<Role>.<Piece>"
    "watch": [{"id": f"{role}.{piece}", "parts": fit(parts, *CHARACTERS[role][:2])} for role in SOLVERS for piece, parts in WATCH.items()],
}

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    n = sum(len(v["parts"]) for v in VILLAINS)
    print(f"Wrote {OUT}: {len(VILLAINS)} villains ({n} parts), {len(PROPS)} props, {len(SUSPECTS) + len(HOUSE_SUSPECTS)} suspect outfits, {len(FOLK)} townsfolk, "
          f"{len(SOLVERS)} solver outfits, {os.path.getsize(OUT) // 1024} KB")
