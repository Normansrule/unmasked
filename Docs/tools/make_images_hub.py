#!/usr/bin/env python3
"""
README images for round 22, from the inspiration-pack round: the street remembers (a house the
night its call is open, and the same yard once its case is solved: Town/HouseMood.cs), the Lantern
Watch costume the townsfolk's gifts add up to (Town/CostumeTrunk.cs, Spooky/WatchCostume.cs), and a
silhouette check of every character at gameplay size.

    python3 Docs/tools/make_images_hub.py                    # everything
    python3 Docs/tools/make_images_hub.py street watch       # just some
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_3d import label, title_text  # noqa: E402

_TOWN = None


def town():
    global _TOWN
    if _TOWN is None:
        merged, t, _ = r3.load_town()
        merged["suspects"] = []  # the suspects wait in the square until a call comes in
        mesh = r3.layout_mesh(merged)
        r3.horizon_mesh(t, mesh)
        _TOWN = (merged, t, mesh)
    return _TOWN


def afterglow_mesh(lot):
    """The front-yard party from the lot's "afterglow" block, and its lights (as TownBuilder builds them)."""
    props = r3.costumes()["props"]
    a = lot["afterglow"]
    m = r3.Mesh()
    lights = []
    for it in a["items"]:
        prop = props[it["k"]]
        m.add_parts(prop["parts"], it["p"], it["ry"], it.get("sc", 1.0))
        if prop.get("glow"):
            lights.append({"p": [it["p"][0], prop["glowY"] * it.get("sc", 1.0) + 0.1, it["p"][2]], "c": prop["glow"], "range": 3.5, "intensity": 0.9})
    bx, by, bz = a["banner"]
    m.add_parts(props["banner"]["parts"], (bx, by, bz), 0, 1.0)
    lights.append({"p": [bx, 2.6, bz - 1.5], "c": [1.0, 0.78, 0.45], "range": 9, "intensity": 1.4})
    return m, lights


def make_street():
    """Pemberton Cottage's front yard: the night the call is open, and after the case is solved."""
    merged, t, mesh = town()
    lot = next(l for l in t["lots"] if l["id"] == "PembertonCottage")
    gx, _, gz = lot["arrival"]
    near = [lt for lt in r3.all_lights(merged) if np.hypot(lt["p"][0] - gx, lt["p"][2] - gz) < 40]
    VW, VH = 760, 470
    eye, target = (gx - 7.5, 3.4, gz - 9.5), (gx + 0.5, 1.6, gz + 4.0)
    cam = r3.Camera(eye, target, 55, VW, VH)

    hx, hy, hz = lot["afterglow"]["haunt"]
    haunt = [{"p": [hx, hy, hz], "c": [0.62, 0.32, 1.0], "range": 14, "intensity": 2.2}]
    a = r3.render(merged, cam, mesh, lights=near + haunt, horizon=t, horizon_t=1.0, fog_density=0.02,
                  light_boost=1.1, ambient=(0.16, 0.12, 0.26))
    party, glow = afterglow_mesh(lot)
    b = r3.render(merged, cam, mesh, extra_mesh=party, lights=near + glow, horizon=t, horizon_t=1.0, fog_density=0.008,
                  light_boost=1.2, ambient=(0.22, 0.17, 0.28))
    # the banner's words, where TownBuilder puts the TextMesh
    bx, _, bz = lot["afterglow"]["banner"]
    p = cam.project((bx, 2.3, bz - 0.03))[0]
    d = ImageDraw.Draw(b, "RGBA")
    d.text((p[0], p[1]), lot["afterglow"]["bannerText"], font=font(max(9, int(780 / p[2] / 10)), "Black"), fill=(140, 56, 20), anchor="mm")

    W, H = 2 * VW + 30, VH + 150
    img = Image.new("RGB", (W, H), (16, 12, 26))
    img.paste(a, (10, 120))
    img.paste(b, (VW + 20, 120))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((W / 2, 36), "The street remembers", font=font(34, "Black"), fill=(255, 200, 120), anchor="mm")
    d.text((W / 2, 76), "Solve a house's case and its yard stays lit for the rest of the game: no popup needed to see what changed.",
           font=font(15, "Medium"), fill=(225, 215, 240), anchor="mm")
    d.text((20, 100), "Tonight's call: a violet light pulses over the yard", font=font(14, "Bold"), fill=(205, 170, 255))
    d.text((VW + 30, 100), "Case closed: lanterns, a party table and a thank-you banner", font=font(14, "Bold"), fill=(255, 220, 160))
    save_png(img, "street-remembers.png")


PIECES = ["Sash", "Charm", "Bell", "Lantern", "Badge"]


def make_watch():
    """The four Solvers in the full Lantern Watch costume, the trunk, and who gave which piece."""
    c = r3.costumes()
    t = r3.load_town()[1]
    watch = {w["id"]: w["parts"] for w in c["watch"]}
    roles = ["Sleuth", "Techie", "Brawn", "Snacker"]
    W, H = 1500, 640
    m = r3.Mesh()
    m.add_shape("box", (0, -0.1, 0), (40, 0.2, 24), (0, 0, 0), (0.12, 0.09, 0.13))
    xs = [(1.5 - i) * 1.25 + 0.6 for i in range(4)]
    for x, role in zip(xs, roles):
        parts = c["solvers"][role]["parts"] + [q for piece in PIECES for q in watch[f"{role}.{piece}"]]
        m.add_parts(parts, (x, 0, 0), -10 if x > 0.6 else 10)
    m.add_parts(c["props"]["trunk"]["parts"], (-4.0, 0, 0.3), -25, 1.3)
    lights = [{"p": [-3.0, 2.8, 2.6], "c": [1.0, 0.72, 0.45], "range": 9, "intensity": 1.4},
              {"p": [3.0, 2.8, 2.6], "c": [0.75, 0.8, 1.0], "range": 9, "intensity": 1.2},
              {"p": [0.0, 1.0, 1.8], "c": [1.0, 0.6, 0.3], "range": 5, "intensity": 0.9}]
    cam = r3.Camera((0, 1.55, 8.4), (0, 1.1, 0), 31, W, H)
    img = r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.0, ambient=(0.24, 0.19, 0.3), moon=False)
    d = ImageDraw.Draw(img, "RGBA")
    for x, role in zip(xs, roles):
        p = cam.project((x, 0.0, 0.5))[0]
        label(d, (p[0], min(H - 40, p[1] + 6)), role, 14)
    p = cam.project((-4.0, 0.0, 0.8))[0]
    label(d, (p[0], min(H - 40, p[1] + 6)), "The trunk at HQ", 14)
    # who gives which piece
    y = H - 145
    d.rounded_rectangle([20, y - 12, 315, y + 132], radius=10, fill=(20, 14, 30, 220))
    d.text((34, y - 2), "Thank-you gifts (one per errand)", font=font(14, "Bold"), fill=(255, 200, 120))
    for i, f in enumerate(t["folk"]):
        d.text((34, y + 22 + i * 21), f"{f['name']}: {f['pieceName']}", font=font(13, "Medium"), fill=(230, 220, 245))
    title_text(img, "The Lantern Watch", "Three gifts from the townsfolk make a costume. Wear it and scares hit 7% softer per piece.", 0.08)
    save_png(img, "lantern-watch.png")


def make_silhouettes():
    """Every character as a flat shape at gameplay size: can you tell who's who without colour or a face?"""
    c = r3.costumes()
    t = r3.load_town()[1]
    names = {f"Folk.{f['id']}": f["name"].split()[-1] for f in t["folk"]}
    rows = [("The Mystery Club", [("solvers", r, r) for r in ["Sleuth", "Techie", "Brawn", "Snacker"]]),
            ("The Haunter's masks", [("villains", v, c["villains"][v]["name"].replace("The ", "")) for v in c["villains"]]),
            ("Townsfolk", [("suspects", k, n) for k, n in names.items()])]
    houses = ["PembertonCottage", "HollowCreekFarm", "WillowLaneVictorian", "HistoricalSociety"]
    lot_names = {l["id"]: l["name"] for l in t["lots"]}
    rows += [(lot_names[h], [("suspects", f"{h}.{s}", s) for s in ["Groundskeeper", "Heiress", "Rival", "Cook"]]) for h in houses]
    rows.append(("Blackwood Manor", [("suspects", s, s) for s in ["Groundskeeper", "Heiress", "Rival", "Cook"]]))
    cell_w, cell_h, pad = 150, 230, 40
    cols = max(len(r[1]) for r in rows)
    per_row = 2  # two groups side by side
    groups = len(rows)
    gw = cols * cell_w + 30
    W = per_row * gw + 40
    H = 120 + ((groups + 1) // 2) * (cell_h + 44)
    img = Image.new("RGB", (W, H), (236, 226, 206))
    d = ImageDraw.Draw(img, "RGBA")
    for gi, (title, members) in enumerate(rows):
        gx0 = 20 + (gi % 2) * gw
        gy0 = 110 + (gi // 2) * (cell_h + 44)
        d.text((gx0 + 6, gy0), title, font=font(15, "Bold"), fill=(60, 40, 50))
        for i, (group, cid, name) in enumerate(members):
            parts = c[group][cid]["parts"]
            m = r3.Mesh()
            m.add_parts(parts, (0, 0, 0), 0)
            cam = r3.Camera((0, 1.2, 9.0), (0, 1.15, 0), 18, cell_w, cell_h - 30)
            gbuf = r3.rasterize(r3.big_camera(cam, 2), m)
            mask = np.isfinite(gbuf[0]) & (gbuf[0] < 1e8)
            sil = Image.fromarray((mask * 255).astype(np.uint8)).resize((cell_w, cell_h - 30), Image.LANCZOS)
            ink = Image.new("RGB", sil.size, (38, 24, 44))
            img.paste(ink, (gx0 + i * cell_w, gy0 + 22), sil)
            d.text((gx0 + i * cell_w + cell_w / 2, gy0 + cell_h + 4), name, font=font(12, "Medium"), fill=(70, 50, 60), anchor="mm")
    d.text((W / 2, 40), "Silhouette check", font=font(32, "Black"), fill=(60, 30, 50), anchor="mm")
    d.text((W / 2, 76), "Every character as one flat shape at the size you see them in play: hats, hair, coats and props should tell them apart",
           font=font(14, "Medium"), fill=(90, 70, 80), anchor="mm")
    save_png(img, "silhouettes.png")


JOBS = {"street": make_street, "watch": make_watch, "silhouettes": make_silhouettes}

if __name__ == "__main__":
    for job in sys.argv[1:] or list(JOBS):
        print(f"  {job}...", flush=True)
        JOBS[job]()
