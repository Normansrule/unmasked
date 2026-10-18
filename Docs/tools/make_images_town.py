#!/usr/bin/env python3
"""
Pictures and animations of Hollow Creek for the README, rendered from the same files Unity builds
the town from (Resources/HollowCreek.json, Resources/Houses/*.json, Resources/BlackwoodManor.json).

    python3 Docs/tools/make_images_town.py            # everything
    python3 Docs/tools/make_images_town.py map drive  # just some: map houses sizes drive events

Illustrations of the design, not in-engine captures.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_gif, save_png, ease, lerp  # noqa: E402
from make_images_3d import label, flicker, timed, INK, MUTED  # noqa: E402

MERGED, TOWN, HOUSES = r3.load_town()
LOTS = {lot["id"]: lot for lot in TOWN["lots"]}
ORANGE, CYAN, RED, YELLOW = (255, 150, 60), (90, 235, 225), (255, 90, 80), (255, 225, 110)
SIZE_COL = {"Small": (140, 220, 140), "Medium": (250, 210, 110), "Large": (255, 150, 70), "Huge": (255, 90, 90)}


def near(lights, pos, r):
    p = np.array(pos)
    return [lt for lt in lights if np.linalg.norm(np.array(lt["p"]) - p) < r + lt["range"]]


def town_mesh(house_roofs=True):
    """The whole town. house_roofs=False lifts the roofs off the four haunted houses (map view)."""
    if house_roofs:
        return r3.layout_mesh(MERGED)
    L = dict(MERGED)
    house_boxes = [b for _, H in HOUSES for b in H["boxes"]]
    keep = {id(b) for b in house_boxes if b["g"] in ("roof", "ceiling")}
    L["boxes"] = [b for b in MERGED["boxes"] if id(b) not in keep]
    return r3.layout_mesh(L)


def stars(img, seed=5, n=60):
    d = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.uniform(0, img.width), rng.uniform(0, img.height * 0.4)
        d.point((x, y), fill=(255, 255, 255, rng.randint(60, 200)))


# ---------------------------------------------------------------------------
# The town map, Schedule I style: the whole town top-down, every house fully built, with pins
# ---------------------------------------------------------------------------
@timed("map")
def make_map():
    X0, X1, Z0, Z1 = -150.0, 110.0, -102.0, 292.0
    W = 900
    H = int(W * (Z1 - Z0) / (X1 - X0))
    cx, cz = (X0 + X1) / 2, (Z0 + Z1) / 2
    cam = r3.Camera((cx, 300, cz - 0.001), (cx, 0, cz), width=W, height=H, ortho=Z1 - Z0)
    mesh = town_mesh(house_roofs=False)
    img = r3.render(MERGED, cam, mesh, moon=False, fog_density=0, ambient=(0.30, 0.27, 0.42), rim_strength=0,
                    moon_dir=(0.3, -0.9, 0.35), light_boost=0.8, background=np.zeros((H * 2, W * 2, 3)) + np.array([0.05, 0.04, 0.09]))
    # cool, map-like grade
    arr = np.asarray(img).astype(np.float32)
    arr = arr * np.array([0.92, 0.96, 1.1]) + np.array([4, 6, 14])
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, "RGBA")

    def P(x, z):
        p = cam.project((x, 0, z))[0]
        return p[0], p[1]

    # The van's route to tonight's call (Willow Lane Victorian)
    route = [(-10, -76), (0, -74), (0, 106), (60, 106), (60, 112)]
    pts = [P(*q) for q in route]
    for a, b in zip(pts, pts[1:]):
        n = int(math.dist(a, b) / 9)
        for i in range(n):
            if i % 2 == 0:
                f0, f1 = i / n, (i + 1) / n
                d.line([(lerp(a[0], b[0], f0), lerp(a[1], b[1], f0)), (lerp(a[0], b[0], f1), lerp(a[1], b[1], f1))], fill=YELLOW + (230,), width=4)

    # Street names
    def street(text, x, z, angle=0):
        f = font(15, "Bold")
        tw = d.textbbox((0, 0), text, font=f)[2]
        layer = Image.new("RGBA", (tw + 16, 26), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.text((8, 3), text, font=f, fill=(225, 220, 240, 235), stroke_width=3, stroke_fill=(10, 8, 20, 220))
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
        px, py = P(x, z)
        img.paste(layer, (int(px - layer.width / 2), int(py - layer.height / 2)), layer)

    street("MAIN STREET", 9.5, 60, 90)
    street("ELM STREET", -30, -9, 0)
    street("WILLOW LANE", 30, 98, 0)
    street("~ Hollow Creek ~", -105, TOWN["creekZ"], 0)
    street("Town Square", -23, -40, 0)
    street("Church", -26, 50, 0)
    d = ImageDraw.Draw(img, "RGBA")

    # Pins
    def pin(x, z, color, title, sub, dy=-34, big=True):
        px, py = P(x, z)
        r = 11 if big else 8
        d.ellipse([px - r - 3, py - r - 3, px + r + 3, py + r + 3], fill=(10, 8, 20, 220))
        d.ellipse([px - r, py - r, px + r, py + r], fill=color + (255,))
        d.ellipse([px - 4, py - 4, px + 4, py + 4], fill=(20, 14, 30, 255))
        label(d, (px, py + dy), title, 15, INK)
        if sub:
            label(d, (px, py + dy + 21), sub, 12, color)

    hq = TOWN["hq"]["spawns"][0]["p"]
    pin(-23, -74, CYAN, "Mystery Club HQ", "you start here", -36)
    for lid, lot in LOTS.items():
        c = lot["center"]
        tonight = lid == "WillowLaneVictorian"
        (x0, z0), (x1, z1) = lot["lot"]["min"], lot["lot"]["max"]
        a, b = P(x0, z1), P(x1, z0)
        d.rectangle([a[0], a[1], b[0], b[1]], outline=(SIZE_COL[lot["size"]] + (200,)), width=2)
        dy = -(b[1] - a[1]) / 2 - 30 if lid != "HollowCreekFarm" else -(b[1] - a[1]) / 2 - 30
        pin(c[0], c[2], RED if tonight else ORANGE, lot["name"],
            f"{lot['size']} · {lot['floors']} floor{'s' if lot['floors'] > 1 else ''}" + ("  ·  TONIGHT'S CALL" if tonight else ""), dy)

    # Van
    vx, vz = hq[0] + 15, hq[2] - 6
    px, py = P(-10, -76)
    d.rounded_rectangle([px - 9, py - 6, px + 9, py + 6], radius=3, fill=CYAN + (255,), outline=(10, 8, 20, 255), width=2)

    # Townsfolk (Town/Townsperson.cs), with a "!" for an errand they're waiting on
    PINK = (255, 190, 215)
    for i, f in enumerate(TOWN.get("folk", [])):
        px, py = P(f["p"][0], f["p"][2])
        d.rectangle([px - 6, py - 6, px + 6, py + 6], fill=(10, 8, 20, 230))
        d.rectangle([px - 4, py - 4, px + 4, py + 4], fill=PINK + (255,))
        right = f["id"] in ("Mayor", "Diner", "Sheriff")
        text = f["name"] + (" !" if i % 2 == 0 else "")
        w = d.textlength(text, font=font(11)) / 2 + 14
        label(d, (px + w if right else px - w, py), text, 11, PINK)

    # Title, legend, compass, scale
    d.rounded_rectangle([14, 14, 330, 92], radius=12, fill=(12, 10, 24, 225))
    d.text((30, 22), "HOLLOW CREEK", font=font(30, "Black"), fill=(255, 236, 200))
    d.text((31, 62), "Town map (press M in game)", font=font(14, "Bold"), fill=MUTED)
    lx, ly = 14, H - 200
    d.rounded_rectangle([lx, ly, lx + 300, ly + 186], radius=12, fill=(12, 10, 24, 225))
    items = [(CYAN, "Mystery Club HQ (start)"), (ORANGE, "Haunted house (click for its card)"), (RED, "Tonight's call"),
             (YELLOW, "Waypoint route for the van"), ((255, 190, 215), "Townsfolk (! = waiting on an errand)")]
    for i, (col, txt) in enumerate(items):
        y = ly + 18 + i * 24
        if col == YELLOW:
            d.line([(lx + 14, y), (lx + 34, y)], fill=col, width=4)
        else:
            d.ellipse([lx + 16, y - 7, lx + 30, y + 7], fill=col)
        d.text((lx + 44, y), txt, font=font(13, "Bold"), fill=INK, anchor="lm")
    y = ly + 18 + 5 * 24
    for i, (size, col) in enumerate(SIZE_COL.items()):
        d.rectangle([lx + 16 + i * 70, y - 6, lx + 28 + i * 70, y + 6], outline=col, width=2)
        d.text((lx + 34 + i * 70, y), size, font=font(12, "Bold"), fill=col, anchor="lm")
    d.text((lx + 16, y + 24), "Lots are drawn to scale. Roofs off: every room is built.", font=font(11, "Medium"), fill=MUTED, anchor="lm")
    # compass
    cxp, cyp = W - 46, 50
    d.ellipse([cxp - 26, cyp - 26, cxp + 26, cyp + 26], fill=(12, 10, 24, 225))
    d.polygon([(cxp, cyp - 20), (cxp - 8, cyp + 6), (cxp + 8, cyp + 6)], fill=(255, 120, 90))
    d.text((cxp, cyp + 14), "N", font=font(12, "Bold"), fill=INK, anchor="mm")
    # scale bar
    a, b = P(X1 - 70, Z0 + 10), P(X1 - 20, Z0 + 10)
    d.rounded_rectangle([a[0] - 10, a[1] - 22, b[0] + 10, a[1] + 10], radius=6, fill=(12, 10, 24, 200))
    d.line([a, b], fill=INK, width=3)
    d.text(((a[0] + b[0]) / 2, a[1] - 11), "50 m", font=font(12, "Bold"), fill=INK, anchor="mm")
    save_png(img, "town-map.png")


# ---------------------------------------------------------------------------
# House cards: each house outside at night, and "fully loaded" with the roof off
# ---------------------------------------------------------------------------
CARD_VIEWS = {
    "PembertonCottage": {"out": ((16, 9, -22), (0, 1.6, 0)), "cut": ((10, 24, -18), (0, 0, 0)), "cut_level": 0},
    "HollowCreekFarm": {"out": ((26, 14, -33), (-3, 2, 4)), "cut": ((14, 40, -32), (-2, 0, 8)), "cut_level": 1},
    "WillowLaneVictorian": {"out": ((24, 12, -30), (1, 4, 0)), "cut": ((12, 30, -24), (2, 0, 0)), "cut_level": 1},
    "BlackwoodManor": {"out": ((30, 18, -52), (0, 5, -4)), "cut": ((16, 36, -30), (0, 0, 0)), "cut_level": 1},
    "HistoricalSociety": {"out": ((24, 12, -38), (0, 4, 0)), "cut": ((14, 36, -28), (0, 0, 2)), "cut_level": 0},
}
CARD_HOUSES = list(CARD_VIEWS)


def house_layout(lid):
    import json
    with open(os.path.join(r3.ROOT, "Assets", "Unmasked", "Resources", LOTS[lid]["resource"] + ".json")) as f:
        return json.load(f)


@timed("houses")
def make_houses():
    VW, VH = 400, 250
    rows = []
    for lid in CARD_HOUSES:
        lot, H, v = LOTS[lid], house_layout(lid), CARD_VIEWS[lid]
        out_cam = r3.Camera(v["out"][0], v["out"][1], 50, VW, VH)
        outside = r3.render(H, out_cam, r3.layout_mesh(H))
        cut_level = v["cut_level"]
        levels = None
        cut_cam = r3.Camera(v["cut"][0], v["cut"][1], 45, VW, VH)
        cut_mesh = r3.layout_mesh(H, roof=False, cut_level=cut_level, cut_height=1.2)
        inside = r3.render(H, cut_cam, cut_mesh, fog_density=0.004, ambient=(0.2, 0.17, 0.3))
        d = ImageDraw.Draw(inside, "RGBA")
        storey = H.get("storey", 3.5)
        for room in H["rooms"]:
            if room["l"] != cut_level:
                continue
            mn, mx = room["min"], room["max"]
            p = cut_cam.project(((mn[0] + mx[0]) / 2, (cut_level * storey if cut_level >= 0 else 0) + 1.6, (mn[2] + mx[2]) / 2))[0]
            if p[2] > 0 and 0 < p[0] < VW and 0 < p[1] < VH:
                label(d, (p[0], p[1]), room["n"], 11)

        card = Image.new("RGB", (2 * VW + 30, VH + 110), (16, 13, 30))
        card.paste(outside, (10, 10))
        card.paste(inside, (VW + 20, 10))
        d = ImageDraw.Draw(card, "RGBA")
        col = SIZE_COL[lot["size"]]
        d.text((14, VH + 20), lot["name"], font=font(22, "Black"), fill=(255, 236, 200))
        badge = f"{lot['size'].upper()}"
        bx = 14 + d.textbbox((0, 0), lot["name"], font=font(22, "Black"))[2] + 14
        bw = d.textbbox((0, 0), badge, font=font(12, "Bold"))[2] + 16
        d.rounded_rectangle([bx, VH + 24, bx + bw, VH + 44], radius=8, fill=col + (255,))
        d.text((bx + bw / 2, VH + 34), badge, font=font(12, "Bold"), fill=(20, 14, 30), anchor="mm")
        (x0, z0), (x1, z1) = lot["lot"]["min"], lot["lot"]["max"]
        dots = "●" * lot["difficulty"] + "○" * max(0, 5 - lot["difficulty"])
        facts = f"{lot['street']}  ·  {lot['floors']} floor{'s' if lot['floors'] > 1 else ''}  ·  {lot['rooms']} rooms  ·  lot {x1 - x0:.0f} x {z1 - z0:.0f} m  ·  spookiness {dots}"
        d.text((14, VH + 52), facts, font=font(13, "Bold"), fill=col)
        blurb = H.get("blurb") or lot["blurb"]
        import textwrap
        for i, line in enumerate(textwrap.wrap(blurb, 118)[:2]):
            d.text((14, VH + 72 + i * 17), line, font=font(12, "Medium"), fill=MUTED)
        d.text((VW + 10 - 6, 16), "outside", font=font(11, "Bold"), fill=INK, anchor="ra")
        d.text((2 * VW + 20 - 6, 16), "roof off: fully loaded", font=font(11, "Bold"), fill=INK, anchor="ra")
        rows.append(card)
    sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows) + 8 * (len(rows) - 1)), (8, 6, 16))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + 8
    save_png(sheet, "house-cards.png")


# ---------------------------------------------------------------------------
# Sizes side by side, to scale
# ---------------------------------------------------------------------------
@timed("sizes")
def make_sizes():
    PX = 3.0  # pixels per metre
    tiles = []
    for lid in CARD_HOUSES:
        lot, H = LOTS[lid], house_layout(lid)
        (x0, z0), (x1, z1) = lot["lot"]["min"], lot["lot"]["max"]
        ox, oz = lot["offset"][0], lot["offset"][2]
        lx0, lx1, lz0, lz1 = x0 - ox, x1 - ox, z0 - oz, z1 - oz
        w, h = int((lx1 - lx0) * PX), int((lz1 - lz0) * PX)
        cam = r3.Camera(((lx0 + lx1) / 2, 200, (lz0 + lz1) / 2 - 0.001), ((lx0 + lx1) / 2, 0, (lz0 + lz1) / 2), width=w, height=h, ortho=lz1 - lz0)
        img = r3.render(H, cam, r3.layout_mesh(H), moon=False, fog_density=0, ambient=(0.3, 0.27, 0.42), rim_strength=0,
                        moon_dir=(0.3, -0.9, 0.35), background=np.zeros((h * 2, w * 2, 3)) + np.array([0.05, 0.04, 0.09]))
        tiles.append((lot, img))
    pad, top, bottom = 24, 76, 64
    cols = [max(img.width, 150) for _, img in tiles]
    W = sum(cols) + pad * (len(tiles) + 1)
    Hh = max(t[1].height for t in tiles) + top + bottom
    sheet = Image.new("RGB", (W, Hh), (14, 12, 28))
    d = ImageDraw.Draw(sheet, "RGBA")
    d.text((pad, 16), "Every house is a different size", font=font(22, "Black"), fill=(255, 236, 200))
    d.text((pad, 46), "Top-down, drawn to the same scale (3 px per metre). From a quick case to a long night.", font=font(13, "Bold"), fill=MUTED)
    x = pad
    for (lot, img), cw in zip(tiles, cols):
        y = Hh - bottom - img.height
        sheet.paste(img, (x, y))
        col = SIZE_COL[lot["size"]]
        d.rectangle([x - 1, y - 1, x + img.width, y + img.height], outline=col, width=2)
        (x0, z0), (x1, z1) = lot["lot"]["min"], lot["lot"]["max"]
        d.text((x, Hh - bottom + 8), lot["name"], font=font(13, "Black"), fill=INK)
        d.text((x, Hh - bottom + 27), f"{lot['size']}  ·  {x1 - x0:.0f} x {z1 - z0:.0f} m", font=font(12, "Bold"), fill=col)
        d.text((x, Hh - bottom + 45), f"{lot['rooms']} rooms, {lot['floors']} floor{'s' if lot['floors'] > 1 else ''}", font=font(11, "Medium"), fill=MUTED)
        x += cw + pad
    save_png(sheet, "house-sizes.png")


# ---------------------------------------------------------------------------
# Driving the van from HQ to a call
# ---------------------------------------------------------------------------
def spline(points, n):
    """Points along a smooth path through the given (x, z) points, evenly spaced by distance."""
    P = [np.array(p, float) for p in points]
    P = [P[0] - (P[1] - P[0])] + P + [P[-1] + (P[-1] - P[-2])]
    dense = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, 40, endpoint=False):
            t2, t3 = t * t, t * t * t
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    dense.append(P[-2])
    seg = np.cumsum([0] + [np.linalg.norm(dense[i + 1] - dense[i]) for i in range(len(dense) - 1)])
    out = []
    for k in range(n):
        s = ease(k / (n - 1)) * seg[-1]
        i = min(np.searchsorted(seg, s), len(dense) - 1)
        j = max(i - 1, 0)
        a = dense[j] if seg[i] == seg[j] else dense[j] + (dense[i] - dense[j]) * ((s - seg[j]) / (seg[i] - seg[j]))
        out.append(a)
    return out


@timed("drive")
def make_drive():
    W, H, n = 640, 340, 56
    route = [(-10, -76), (-4, -75), (2, -68), (2, -30), (2, -6), (8, 2), (30, 2), (55, 2), (68, 4), (70, 8.5)]
    path = spline(route, n)
    mesh = town_mesh()
    van = C3_PROPS["van"]["parts"]
    lights_all = r3.all_lights(MERGED)
    frames = []
    cottage = LOTS["PembertonCottage"]
    for k, p in enumerate(path):
        t = k * 0.1
        q = path[min(k + 2, n - 1)] - path[max(k - 2, 0)]
        heading = math.atan2(q[0], q[1]) if np.linalg.norm(q) > 0.05 else frames_heading[-1]
        frames_heading.append(heading)
        fwd = np.array([math.sin(heading), 0, math.cos(heading)])
        pos = np.array([p[0], 0.05, p[1]])
        f_end = max(0.0, (k - (n - 12)) / 11)  # swing round to look at the house at the end
        cam_pos = pos - fwd * lerp(9.5, 6, f_end) + np.array([0, lerp(3.6, 4.5, f_end), 0]) + np.array([-lerp(0, 9, f_end), 0, 0])
        target = pos + fwd * lerp(7, 2, f_end) + np.array([0, 1.4, 0])
        target = target * (1 - f_end) + np.array([70, 3, 24]) * f_end
        cam = r3.Camera(cam_pos, target, 55, W, H)
        dyn = r3.Mesh()
        dyn.add_parts(van, pos, math.degrees(heading))
        lights = flicker(near(lights_all, cam_pos, 70), t)
        lights += [{"p": list(pos + fwd * 3.2 + np.array([0, 1.0, 0])), "c": [1, 0.93, 0.75], "range": 18, "intensity": 1.6}]
        img = r3.render(MERGED, cam, mesh, extra_mesh=dyn, lights=lights)
        # HUD, like the game
        d = ImageDraw.Draw(img, "RGBA")
        remaining = max(0, 150 - int(k * 2.2))
        d.rounded_rectangle([W / 2 - 230, 6, W / 2 + 230, 30], radius=6, fill=(14, 12, 28, 200))
        d.text((W / 2, 18), f"Call from Pemberton Cottage! Drive there ({remaining // 60}:{remaining % 60:02d})", font=font(13, "Bold"), fill=INK, anchor="mm")
        dist = math.dist((pos[0], pos[2]), (cottage["arrival"][0], cottage["arrival"][2]))
        if dist > 6:
            to = math.atan2(cottage["arrival"][0] - pos[0], cottage["arrival"][2] - pos[2])
            cam_yaw = math.atan2(target[0] - cam_pos[0], target[2] - cam_pos[2])
            a = to - cam_yaw
            cx, cy = W / 2, 52
            tip = (cx + 14 * math.sin(a), cy - 14 * math.cos(a))
            left = (cx + 9 * math.sin(a - 2.4), cy - 9 * math.cos(a - 2.4))
            right = (cx + 9 * math.sin(a + 2.4), cy - 9 * math.cos(a + 2.4))
            d.polygon([tip, left, right], fill=YELLOW + (255,))
            d.text((cx, 76), f"Pemberton Cottage  {dist:.0f} m", font=font(12, "Bold"), fill=YELLOW, anchor="mm",
                   stroke_width=2, stroke_fill=(14, 12, 28))
        speed = 0 if k in (0, n - 1) else np.linalg.norm(path[min(k + 1, n - 1)] - path[k]) / 0.1 * 3.6 * 0.35
        d.rounded_rectangle([8, H - 56, 250, H - 8], radius=6, fill=(14, 12, 28, 200))
        d.text((18, H - 46), f"Driving  {speed:.0f} km/h", font=font(13, "Bold"), fill=INK)
        d.text((18, H - 26), "[W/S] gas  [A/D] steer  [E] get out", font=font(11, "Medium"), fill=MUTED)
        minimap(img, pos, heading)
        frames.append(img)
    frames += [frames[-1]] * 10
    save_gif(frames, "van-drive.gif", 100)


MINI = None


def minimap(img, pos, heading):
    """A little top-down map in the corner, like the in-game minimap."""
    global MINI
    if MINI is None:
        path = os.path.join(r3.ROOT, "Docs", "images", "town-map.png")
        MINI = Image.open(path).convert("RGB") if os.path.exists(path) else None
    if MINI is None:
        return
    X0, X1, Z0, Z1 = -150.0, 110.0, -102.0, 292.0
    span = 110
    u = (pos[0] - X0) / (X1 - X0) * MINI.width
    v = (Z1 - pos[2]) / (Z1 - Z0) * MINI.height
    half = span / (X1 - X0) * MINI.width / 2
    crop = MINI.crop((int(u - half), int(v - half), int(u + half), int(v + half))).resize((110, 110))
    x, y = img.width - 120, 10
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([x - 3, y - 3, x + 113, y + 113], fill=(10, 8, 20, 230))
    img.paste(crop, (x, y))
    cx, cy = x + 55, y + 55
    tip = (cx + 7 * math.sin(heading), cy - 7 * math.cos(heading))
    d.polygon([tip, (cx + 5 * math.sin(heading - 2.5), cy - 5 * math.cos(heading - 2.5)),
               (cx + 5 * math.sin(heading + 2.5), cy - 5 * math.cos(heading + 2.5))], fill=(255, 255, 255, 255))
    d.text((x + 55, y + 122), "[M] map", font=font(10, "Bold"), fill=INK, anchor="mm")


frames_heading = [math.pi / 2]
C3_PROPS = r3.costumes()["props"]


# ---------------------------------------------------------------------------
# Special events: the same street on six different nights
# ---------------------------------------------------------------------------
@timed("events")
def make_events():
    W, H = 320, 200
    vic = LOTS["WillowLaneVictorian"]
    ox, oz = vic["offset"][0], vic["offset"][2]
    cam_pos, target = (ox - 14, 3.2, oz - 33), (ox + 1, 5, oz - 2)
    mesh = town_mesh()
    base_lights = near(r3.all_lights(MERGED), cam_pos, 60)
    events = [("Normal night", "", {}), ("Blood Moon", "scares hit harder, ecto refills fast", "blood"),
              ("Thunderstorm", "lightning, rain, lamps blow out", "storm"), ("Pea-Soup Fog", "you can barely see", "fog"),
              ("Power Outage", "every lamp starts off", "dark"), ("Harvest Festival", "braver Solvers, shorter night", "fest")]
    tiles = []
    for name, blurb, kind in events:
        cam = r3.Camera(cam_pos, target, 52, W, H)
        big = r3.big_camera(cam, 2)
        sky = r3.sky(big.w, big.h)
        args = {}
        lights = base_lights
        if kind == "blood":
            sky = sky * np.array([1.6, 0.45, 0.45])
            args = dict(moon_color=(0.8, 0.14, 0.12), fog=(0.24, 0.04, 0.06), ambient=(0.16, 0.05, 0.07))
        elif kind == "storm":
            sky = sky * 0.7 + np.array([0.25, 0.27, 0.35])
            args = dict(moon_color=(0.9, 0.95, 1.3), ambient=(0.3, 0.32, 0.42), fog=(0.18, 0.18, 0.24), fog_density=0.02)
        elif kind == "fog":
            sky = sky * 0.3 + np.array([0.28, 0.33, 0.29])
            args = dict(fog=(0.32, 0.38, 0.33), fog_density=0.07)
        elif kind == "dark":
            lights = [lt for lt in base_lights if "n" not in lt]
            args = dict(ambient=(0.05, 0.04, 0.09), moon_color=(0.2, 0.18, 0.36))
        elif kind == "fest":
            lights = base_lights + [{"p": [ox - 6 + 4 * i, 3.0, oz - 20], "c": [[1, 0.6, 0.2], [0.7, 0.4, 1], [0.6, 1, 0.5]][i % 3],
                                     "range": 9, "intensity": 1.3} for i in range(5)]
            args = dict(ambient=(0.18, 0.11, 0.12), fog=(0.2, 0.09, 0.08))
        if kind == "dark" and "dark_mesh" not in locals():
            dark_mesh = r3.layout_mesh(MERGED, window_glow=0.08)
        img = r3.render(MERGED, cam, dark_mesh if kind == "dark" else mesh, lights=lights, background=np.clip(sky, 0, 1), **args)
        d = ImageDraw.Draw(img, "RGBA")
        if kind == "storm":
            rng = random.Random(3)
            for _ in range(260):
                x, y = rng.uniform(0, W), rng.uniform(-20, H)
                d.line([(x, y), (x - 3, y + 14)], fill=(200, 215, 255, 90), width=1)
            d.line([(70, 0), (82, 30), (74, 34), (90, 70)], fill=(240, 245, 255, 230), width=2)
        if kind == "fest":
            for i in range(9):
                x = 20 + i * 34
                d.ellipse([x - 3, 22 + 8 * math.sin(i), x + 3, 28 + 8 * math.sin(i)], fill=[(255, 160, 60), (180, 110, 255), (150, 255, 120)][i % 3] + (255,))
        d.rounded_rectangle([6, H - 46, W - 6, H - 6], radius=8, fill=(12, 10, 24, 210))
        d.text((16, H - 38), name, font=font(15, "Black"), fill=(255, 236, 200))
        d.text((16, H - 19), blurb or "the usual spooky night", font=font(11, "Medium"), fill=MUTED)
        tiles.append(img)
    sheet = Image.new("RGB", (3 * W + 4 * 8, 2 * H + 3 * 8), (8, 6, 16))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, (8 + (i % 3) * (W + 8), 8 + (i // 3) * (H + 8)))
    save_png(sheet, "night-events.png")


JOBS = {"map": make_map, "houses": make_houses, "sizes": make_sizes, "drive": make_drive, "events": make_events}

if __name__ == "__main__":
    picks = sys.argv[1:] or list(JOBS)
    for name in picks:
        print(f"rendering {name}...")
        JOBS[name]()
