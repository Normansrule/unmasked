#!/usr/bin/env python3
"""
README images for round 16: the world beyond Hollow Creek (hills, far towns, landmarks, roads out
of town and the forest, from the "horizon" block of HollowCreek.json that Town/Horizon.cs builds in
Unity), close-ups of the rebuilt characters, and the Mask Keeper story arc.

    python3 Docs/tools/make_images_world.py                 # everything
    python3 Docs/tools/make_images_world.py horizon faces   # just some
"""
import os
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_gif, save_png  # noqa: E402
from make_images_3d import label, title_text  # noqa: E402
from make_images_cases import read_cases  # noqa: E402

_TOWN = None


def town():
    """(merged layout, town json, static mesh with the horizon's near part)."""
    global _TOWN
    if _TOWN is None:
        merged, t, _ = r3.load_town()
        mesh = r3.layout_mesh(merged)
        r3.horizon_mesh(t, mesh)
        _TOWN = (merged, t, mesh)
    return _TOWN


def landmark_labels(img, cam, t):
    d = ImageDraw.Draw(img, "RGBA")
    h = t["horizon"]
    for lm in h["landmarks"]:
        ring = h["rings"][lm["ring"]]
        tall = {"steeple": 52, "lighthouse": 45, "windmill": 31, "watertower": 27}.get(lm["kind"], 26)
        top = r3.ring_height(ring, lm["angle"]) + (tall - 3) * lm["size"] * ring["radius"] / 540
        p = r3._on_ring(cam.pos[0], cam.pos[2], ring["radius"], lm["angle"], top)
        sp = cam.project(p[None, :])[0]
        if sp[2] > 1 and 60 < sp[0] < cam.w - 60:
            label(d, (sp[0], sp[1] - 8), lm["name"], 13, fill=(255, 214, 160))


def make_horizon():
    merged, t, mesh = town()
    W, H = 1600, 640
    cam = r3.Camera((-10, 46, -150), (-20, 20, 260), 62, W, H)
    img = r3.render(merged, cam, mesh, horizon=t, horizon_t=1.0, fog_density=0.0035, moon=False)
    landmark_labels(img, cam, t)
    title_text(img, "Hollow Creek is not alone", "Hills, far-off towns and landmarks in every direction: the night goes on past the edge of town", 0.1)
    save_png(img, "horizon.png")


def make_edge():
    merged, t, mesh = town()
    W, H = 1280, 600
    cam = r3.Camera((6, 7, -70), (0, 14, -400), 55, W, H)
    img = r3.render(merged, cam, mesh, horizon=t, horizon_t=2.0, fog_density=0.004)
    d = ImageDraw.Draw(img, "RGBA")
    road = next(r for r in t["horizon"]["roads"] if r["name"] == "Main Street south")
    sign = cam.project((road["from"][0] - 6, 3.2, road["from"][1] - 14))[0]
    label(d, (sign[0], sign[1] - 18), road["sign"], 14, fill=(255, 220, 160))
    title_text(img, "Roads lead somewhere", "Main Street runs on past the woods towards Ravensford, lamps and all", 0.1)
    save_png(img, "edge-of-town.png")


def make_pan():
    """A slow look round from the HQ roof: hills, lights, the lighthouse beam, the windmill turning."""
    merged, t, mesh = town()
    W, H = 720, 300
    frames = []
    hq = (-24.0, 14.0, -74.0)
    n = 36
    for i in range(n):
        a = r3.np.radians(i * 360 / n)
        target = (hq[0] + r3.np.sin(a) * 100, 10.0, hq[2] + r3.np.cos(a) * 100)
        cam = r3.Camera(hq, target, 60, W, H)
        img = r3.render(merged, cam, mesh, horizon=t, horizon_t=i * 0.5, fog_density=0.004, ss=1)
        landmark_labels(img, cam, t)
        frames.append(img)
        print(f"    pan {i + 1}/{n}", flush=True)
    save_gif(frames, "beyond-town.gif", 160)


def make_faces():
    """Close-ups of the rebuilt characters: faces, hands, real proportions."""
    c = r3.costumes()
    cases = read_cases()
    row = [("solvers", "Sleuth", "Sleuth", "Mystery Club"), ("solvers", "Techie", "Techie", "Mystery Club"),
           ("solvers", "Brawn", "Brawn", "Mystery Club"), ("solvers", "Snacker", "Snacker", "Mystery Club")]
    names = cases["PembertonCottage"]["suspects"]
    for slot, (name, job, _) in zip(["Groundskeeper", "Heiress", "Rival", "Cook"], names):
        row.append(("suspects", "PembertonCottage." + slot, name, job))
    W, H = 1600, 600
    m = r3.Mesh()
    m.add_shape("box", (0, -0.1, 0), (40, 0.2, 24), (0, 0, 0), (0.12, 0.09, 0.13))
    xs = [(3.5 - i) * 1.05 for i in range(len(row))]  # this camera looks down -z, so +x is on the left
    for x, (group, cid, _, _) in zip(xs, row):
        m.add_parts(c[group][cid]["parts"], (x, 0, 0), -8 if x > 0 else 8)
    lights = [{"p": [-3.0, 2.6, 2.4], "c": [1.0, 0.72, 0.45], "range": 8, "intensity": 1.4},
              {"p": [3.0, 2.6, 2.4], "c": [0.75, 0.8, 1.0], "range": 8, "intensity": 1.3},
              {"p": [0.0, 1.0, 1.6], "c": [1.0, 0.55, 0.25], "range": 4, "intensity": 0.8}]
    cam = r3.Camera((0, 1.5, 6.6), (0, 1.05, 0), 28, W, H)
    img = r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.0, ambient=(0.24, 0.19, 0.3), moon=False)
    d = ImageDraw.Draw(img, "RGBA")
    for x, (_, _, name, job) in zip(xs, row):
        p = cam.project((x, 0.0, 0.5))[0]
        label(d, (p[0], min(H - 40, p[1] + 6)), name, 13)
        d.text((p[0], min(H - 40, p[1] + 6) + 20), job, font=font(11, "Medium"), fill=(190, 180, 215), anchor="mm")
    title_text(img, "Characters, rebuilt", "Faces with eyes, brows, noses and ears; hands with fingers; jointed arms and legs; boots and shoes", 0.09)
    save_png(img, "faces.png")


def make_arc():
    """The Mask Keeper: one clue per solved case, all pointing the same way."""
    src = open(os.path.join(r3.ROOT, "Assets", "Unmasked", "Scripts", "Mystery", "Cases.cs"), encoding="utf-8").read()
    arcs = {}
    for block in re.split(r"\n\s*new Spec\s*\n", src)[1:]:
        house = re.search(r'HouseId = "(\w+)"', block).group(1)
        clue = re.search(r'ArcClue = "((?:[^"\\]|\\.)*)"', block)
        if clue and house not in arcs:  # return visits have no Mask Keeper clue
            arcs[house] = clue.group(1).replace('\\"', '"')
    question = re.search(r'ArcQuestion =\s*"((?:[^"\\]|\\.)*)"', src).group(1)
    names = {k: v["name"] for k, v in read_cases().items()}
    order = ["PembertonCottage", "HollowCreekFarm", "WillowLaneVictorian", "BlackwoodManor"]
    W, H = 1400, 500
    img = Image.new("RGB", (W, H), (24, 18, 30))
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(30 + 30 * k), int(20 + 12 * k), int(40 + 10 * k)))
    d.text((W / 2, 50), "The Mask Keeper", font=font(46, "Black"), fill=(255, 196, 110), anchor="mm")
    d.text((W / 2, 96), question, font=font(16, "Medium"), fill=(225, 215, 240), anchor="mm")
    cw, gap = 310, 26
    x0 = (W - 4 * cw - 3 * gap) / 2
    for i, house in enumerate(order):
        x = x0 + i * (cw + gap)
        d.rounded_rectangle([x, 140, x + cw, 350], radius=14, fill=(246, 234, 206), outline=(150, 110, 70), width=3)
        d.text((x + cw / 2, 168), f"Case {i + 1}", font=font(14, "Bold"), fill=(150, 90, 50), anchor="mm")
        d.text((x + cw / 2, 194), names[house], font=font(17, "Black"), fill=(60, 40, 30), anchor="mm")
        lines, cur = [], ""
        for word in arcs[house].split():
            if d.textlength(cur + " " + word, font=font(15, "Medium")) > cw - 40:
                lines.append(cur)
                cur = word
            else:
                cur = (cur + " " + word).strip()
        lines.append(cur)
        for j, ln in enumerate(lines):
            d.text((x + 20, 228 + j * 24), ln, font=font(15, "Medium"), fill=(70, 50, 40))
        # a thread of red string from each card to the reveal, like a detective's wall
        d.line([(x + cw / 2, 350), (W / 2, 410)], fill=(200, 50, 50), width=3)
        d.ellipse([x + cw / 2 - 6, 344, x + cw / 2 + 6, 356], fill=(200, 50, 50))
    d.rounded_rectangle([W / 2 - 330, 396, W / 2 + 330, 476], radius=14, fill=(40, 26, 50), outline=(255, 196, 110), width=2)
    d.text((W / 2, 420), "Case 5: The Mask Keeper, 1 Founders Way", font=font(20, "Black"), fill=(255, 220, 160), anchor="mm")
    d.text((W / 2, 452), "Locked on the call board until the other four are solved. Then the Historical Society calls.",
           font=font(14, "Medium"), fill=(210, 200, 230), anchor="mm")
    save_png(img, "mask-keeper.png")


JOBS = {"horizon": make_horizon, "edge": make_edge, "faces": make_faces, "arc": make_arc, "pan": make_pan}

if __name__ == "__main__":
    for job in sys.argv[1:] or list(JOBS):
        print(f"  {job}...", flush=True)
        JOBS[job]()
