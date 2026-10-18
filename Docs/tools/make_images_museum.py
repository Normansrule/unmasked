#!/usr/bin/env python3
"""
README images for round 18: the fifth call. The Hollow Creek Historical Society on Founders Way
(Houses/HistoricalSociety.json, placed by HollowCreek.json), its Mask Gallery with the empty case,
and the four people who work there (make_costumes.py HOUSE_SUSPECTS "HistoricalSociety.*").

    python3 Docs/tools/make_images_museum.py                 # everything
    python3 Docs/tools/make_images_museum.py street gallery  # just some
"""
import math
import os
import sys

import numpy as np
from PIL import ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import save_png  # noqa: E402
from make_images_3d import label, title_text  # noqa: E402
from make_images_cases import read_cases  # noqa: E402
from make_images_town import house_layout  # noqa: E402

HOUSE = "HistoricalSociety"
SLOTS = ["Groundskeeper", "Heiress", "Rival", "Cook"]


def facing(at, cam):
    """Yaw (degrees) that turns an outfit, which faces +z, towards the camera."""
    return math.degrees(math.atan2(cam[0] - at[0], cam[2] - at[2]))


def make_street():
    """The museum from Founders Way at night, with the rest of the world behind it."""
    merged, t, _ = r3.load_town()
    off = next(lot["offset"] for lot in t["lots"] if lot["id"] == HOUSE)
    mesh = r3.layout_mesh(merged)
    r3.horizon_mesh(t, mesh)
    W, H = 1400, 640
    eye = (off[0] - 16, 3.2, -86.5)
    cam = r3.Camera(eye, (off[0] + 1, 4.5, off[2] - 2), 56, W, H)
    p = np.array(eye)
    lights = [lt for lt in r3.all_lights(merged) if np.linalg.norm(np.array(lt["p"]) - p) < 70 + lt["range"]]
    # Walter Finch on his rounds by the gate
    who = r3.Mesh()
    at = (off[0] - 5.5, 0, off[2] - 15.0)
    who.add_parts(r3.suspect_outfit("Groundskeeper", HOUSE), at, facing(at, eye))
    img = r3.render(merged, cam, mesh, extra_mesh=who, lights=lights, horizon=t, horizon_t=1.5,
                    fog_density=0.006, light_boost=1.2, ambient=(0.2, 0.16, 0.3))
    d = ImageDraw.Draw(img, "RGBA")
    sp = cam.project((at[0], 2.4, at[2]))[0]
    label(d, (sp[0], sp[1] - 10), "Walter Finch, night watchman", 13)
    title_text(img, "The fifth call: 1 Founders Way",
               "The Hollow Creek Historical Society. Its lights are on far too late tonight.", 0.1)
    save_png(img, "museum.png")


def make_gallery():
    """Inside the Mask Gallery: four masks under glass and one empty case, with the people who work here."""
    L = dict(house_layout(HOUSE))
    # The renderer has no see-through glass (glass boxes glow like lit windows), so draw each case's
    # brass frame and leave the panes out; Unity's glass material shows the mask through them.
    boxes = []
    for bx in L["boxes"]:
        if not bx["n"].startswith("CaseGlass"):
            boxes.append(bx)
            continue
        (x, y, z), (sx, sy, sz) = bx["p"], bx["s"]
        brass = [0.78, 0.6, 0.28]
        for cx in (-1, 1):
            for cz in (-1, 1):
                boxes.append(dict(bx, n="CasePost", p=[x + cx * sx / 2, y, z + cz * sz / 2], s=[0.04, sy, 0.04], c=brass, m="solid"))
        boxes.append(dict(bx, n="CaseLid", p=[x, y + sy / 2, z], s=[sx + 0.04, 0.04, sz + 0.04], c=brass, m="solid"))
    L["boxes"] = boxes
    L["suspects"] = []  # placed below, where the picture can see them
    mesh = r3.layout_mesh(L)
    W, H = 1400, 700
    eye = (-3.5, 1.9, -3.2)
    cam = r3.Camera(eye, (-8.4, 1.0, 2.4), 70, W, H)
    names = read_cases()[HOUSE]["suspects"]
    who = r3.Mesh()
    spots = [(-8.9, 0, 3.4), (-5.6, 0, 1.9), (-4.4, 0, 4.6), (-9.7, 0, -1.0)]
    for slot, at in zip(SLOTS, spots):
        who.add_parts(r3.suspect_outfit(slot, HOUSE), at, facing(at, eye))
    img = r3.render(L, cam, mesh, extra_mesh=who, fog_density=0.0, light_boost=1.15, ambient=(0.24, 0.2, 0.3), moon=False)
    d = ImageDraw.Draw(img, "RGBA")
    for (name, job, _), at in zip(names, spots):
        sp = cam.project((at[0], 2.25, at[2]))[0]
        if sp[2] > 0:
            label(d, (sp[0], sp[1] - 12), f"{name}, {job.lower()}", 13)
    sp = cam.project((-7.0, 1.3, 1.0))[0]
    label(d, (sp[0], sp[1] - 4), "The Hollow Creek Mask: gone", 14, fill=(255, 200, 120))
    title_text(img, "The Mask Gallery", "Four folklore masks back under glass, and the oldest of all missing from its case", 0.1)
    save_png(img, "mask-gallery.png")


JOBS = {"street": make_street, "gallery": make_gallery}

if __name__ == "__main__":
    for job in sys.argv[1:] or list(JOBS):
        print(f"  {job}...", flush=True)
        JOBS[job]()
