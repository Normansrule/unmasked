#!/usr/bin/env python3
"""
README images for round 21: closer looks at the people of Hollow Creek after the character pass
(make_costumes.py face/hand/hair/person), and how their heights and builds now differ.

    python3 Docs/tools/make_images_people.py                         # everything
    python3 Docs/tools/make_images_people.py portraits builds        # just some
    python3 Docs/tools/make_images_people.py before OLD_COSTUMES.json  # before/after against an older Costumes.json
"""
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402
from make_images_3d import label, title_text  # noqa: E402

PORTRAITS = [("solvers", "Sleuth", "Sleuth", "Mystery Club"),
             ("suspects", "HistoricalSociety.Heiress", "Edie Wren", "curator"),
             ("suspects", "Folk.Mayor", "Harold Beaumont", "the mayor"),
             ("suspects", "HistoricalSociety.Cook", "Rosa Delgado", "baker"),
             ("suspects", "Folk.Sheriff", "Ruth Calloway", "the sheriff")]

LIGHTS = [{"p": [-1.6, 2.3, 2.2], "c": [1.0, 0.74, 0.5], "range": 6, "intensity": 1.5},
          {"p": [1.8, 2.1, 1.8], "c": [0.7, 0.78, 1.0], "range": 6, "intensity": 1.0},
          {"p": [0.0, 2.6, -1.5], "c": [1.0, 0.6, 0.3], "range": 5, "intensity": 0.9}]


def load(path):
    with open(path) as f:
        c = json.load(f)
    for key in ("suspects", "solvers"):
        c[key] = {item["id"]: item for item in c[key]}
    return c


def head_of(parts):
    """Where the head sits after a character's height scaling (the part named Head)."""
    h = next((q for q in parts if q["n"] == "Head"), None)
    return h["p"][1] if h else 1.78


def portrait(c, group, cid, W=300, H=360, ry=14):
    parts = c[group][cid]["parts"]
    y = head_of(parts)
    m = r3.Mesh()
    m.add_parts(parts, (0, 0, 0), ry)
    cam = r3.Camera((0, y + 0.06, 1.85), (0, y - 0.1, 0), 26, W, H)
    lights = [dict(L, p=[L["p"][0], L["p"][1] + y - 1.78, L["p"][2]]) for L in LIGHTS]
    return r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.0, ambient=(0.26, 0.21, 0.31), moon=False)


def portrait_row(c, W=300, H=360):
    row = Image.new("RGB", (W * len(PORTRAITS), H))
    for i, (group, cid, _, _) in enumerate(PORTRAITS):
        row.paste(portrait(c, group, cid, W, H), (i * W, 0))
    return row


def caption(img, y0, W):
    d = ImageDraw.Draw(img, "RGBA")
    for i, (_, _, name, job) in enumerate(PORTRAITS):
        cx = i * W + W // 2
        label(d, (cx, y0), name, 14)
        d.text((cx, y0 + 21), job, font=font(12, "Medium"), fill=(200, 190, 225), anchor="mm")


def make_portraits():
    with r3.detail(True):
        row = portrait_row(r3.costumes())
    W = 300
    img = Image.new("RGB", (row.width, row.height + 140), (24, 18, 30))
    img.paste(row, (0, 90))
    caption(img, row.height + 108, W)
    title_text(img, "Faces you can read", "Two-tone eyes with lashes, a nose with a bridge and nostrils, both lips, real hair and fingers", 0.07)
    save_png(img, "portraits.png")


def make_before(old_path):
    with r3.detail(True):
        before = portrait_row(load(old_path), 260, 300)
        after = portrait_row(r3.costumes(), 260, 300)
    W = 260
    img = Image.new("RGB", (before.width, before.height * 2 + 210), (24, 18, 30))
    d = ImageDraw.Draw(img, "RGBA")
    img.paste(before, (0, 110))
    img.paste(after, (0, 110 + before.height + 40))
    d.text((18, 96), "BEFORE (round 20)", font=font(15, "Bold"), fill=(200, 190, 225), anchor="ls")
    d.text((18, 110 + before.height + 34), "AFTER (round 21)", font=font(15, "Bold"), fill=(255, 196, 110), anchor="ls")
    caption(img, 110 + before.height * 2 + 62, W)
    title_text(img, "The character pass", "Same people, same clothes: new faces, hair, hands and bodies", 0.06)
    save_png(img, "people-before-after.png")


def make_builds():
    """Everyone at one house plus the townsfolk, feet on the same line, to show heights and builds."""
    c = r3.costumes()
    ids = [("solvers", "Sleuth"), ("solvers", "Brawn"), ("suspects", "Folk.Mayor"), ("suspects", "Folk.Fortune"),
           ("suspects", "HistoricalSociety.Groundskeeper"), ("suspects", "HistoricalSociety.Heiress"),
           ("suspects", "HistoricalSociety.Rival"), ("suspects", "Folk.Diner"), ("solvers", "Snacker")]
    W, H = 1600, 620
    with r3.detail(True):
        img = _builds_image(c, ids, W, H)
    d = ImageDraw.Draw(img, "RGBA")
    xs = [((len(ids) - 1) / 2 - i) * 0.95 for i in range(len(ids))]
    cam = r3.Camera((0, 1.3, 8.4), (0, 1.1, 0), 30, W, H)
    for x, (g, cid) in zip(xs, ids):
        p = cam.project((x, 0.0, 0.5))[0]
        name = cid.split(".")[-1] if g == "solvers" else BUILD_NAMES.get(cid, cid)
        label(d, (p[0], min(H - 30, p[1] + 6)), name, 13)
    img = img.crop((0, 0, W, 510))  # the floor below the labels is empty
    title_text(img, "Tall, short, broad and slight", "Every character now has their own height and build", 0.09)
    save_png(img, "builds.png")


def _builds_image(c, ids, W, H):
    m = r3.Mesh()
    m.add_shape("box", (0, -0.1, 0), (40, 0.2, 24), (0, 0, 0), (0.12, 0.09, 0.13))
    xs = [((len(ids) - 1) / 2 - i) * 0.95 for i in range(len(ids))]
    for x, (g, cid) in zip(xs, ids):
        m.add_parts(c[g][cid]["parts"], (x, 0, 0), -6 if x > 0 else 6)
    # height lines every half metre
    for h in (1.5, 2.0):
        m.add_shape("box", (0, h, -0.6), (9.5, 0.01, 0.01), (0, 0, 0), (0.4, 0.34, 0.5), 0.5)
    lights = [{"p": [-3.0, 2.8, 2.6], "c": [1.0, 0.72, 0.45], "range": 9, "intensity": 1.4},
              {"p": [3.0, 2.8, 2.6], "c": [0.75, 0.8, 1.0], "range": 9, "intensity": 1.3},
              {"p": [0.0, 1.0, 1.8], "c": [1.0, 0.55, 0.25], "range": 4, "intensity": 0.8}]
    cam = r3.Camera((0, 1.3, 8.4), (0, 1.1, 0), 30, W, H)
    return r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.0, ambient=(0.24, 0.19, 0.3), moon=False)


BUILD_NAMES = {"Folk.Mayor": "Mayor Beaumont", "Folk.Fortune": "Old Nell", "Folk.Diner": "Dot",
               "HistoricalSociety.Groundskeeper": "Walter Finch", "HistoricalSociety.Heiress": "Edie Wren",
               "HistoricalSociety.Rival": "Mortimer Vane"}

if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["before"]:
        make_before(args[1])
        sys.exit()
    jobs = {"portraits": make_portraits, "builds": make_builds}
    for name in args or list(jobs):
        print("making", name, flush=True)
        jobs[name]()
