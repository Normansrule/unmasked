#!/usr/bin/env python3
"""
Pictures of the cases for the README, read straight from Assets/Unmasked/Scripts/Mystery/Cases.cs:

  case-files.png         every house's case (title, the four suspects, their alibis and the
clue traits); the house pictures are cropped from
                         house-cards.png (make_images_town.py)
  suspects-by-house.png  the four suspects at each house, in the outfits make_costumes.py gives them
  witness.png            a scare seen up close, and what the witness says when interviewed

    python3 Docs/tools/make_images_cases.py                     # both
    python3 Docs/tools/make_images_cases.py suspects            # just one
"""
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_images import canvas, finish, rect, save_png, text, wrap, INK, MUTED, ORANGE, OUT, SS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASES = os.path.join(ROOT, "Assets", "Unmasked", "Scripts", "Mystery", "Cases.cs")
# Rows of house-cards.png (outside view on the left), by house id
ORDER = ["PembertonCottage", "HollowCreekFarm", "WillowLaneVictorian", "BlackwoodManor", "HistoricalSociety"]
CARD_ROW = {h: i for i, h in enumerate(ORDER)}
SIZE = {"PembertonCottage": "Small, a quick case: 3 accusations, 3 alibi checks, extra clues",
        "HollowCreekFarm": "Medium: the Haunter slips up a little more",
        "WillowLaneVictorian": "Large",
        "BlackwoodManor": "Huge",
        "HistoricalSociety": "Large, the fifth call: it rings once the other four are solved"}


def _house_rooms():
    import json
    res = os.path.join(ROOT, "Assets", "Unmasked", "Resources")
    out = {}
    for h in ORDER:
        path = os.path.join(res, "BlackwoodManor.json" if h == "BlackwoodManor" else os.path.join("Houses", h + ".json"))
        out[h] = {r["n"] for r in json.load(open(path))["rooms"]}
    return out


HOUSE_ROOMS = _house_rooms()


def cs_string(s):
    return s.encode().decode("unicode_escape") if "\\" in s else s


def read_cases():
    src = open(CASES, encoding="utf-8").read()
    out = {}
    for block in re.split(r"\n\s*new Spec\s*\n", src)[1:]:
        house = re.search(r'HouseId = "(\w+)"', block).group(1)
        visit = re.search(r"Visit = (\d+)", block)
        if visit and int(visit.group(1)) > 1:
            house += "#" + visit.group(1)  # a return visit: Cases.Spec.CaseId
        name = re.search(r'CaseName = "([^"]+)"', block).group(1)
        sus = re.findall(r'S\("([^"]+)", "([^"]+)", "(?:[^"\\]|\\.)*",\s*"((?:[^"\\]|\\.)*)", "([^"]*)"\)', block)
        traits = re.search(r"TraitNames = new\[\] \{([^}]*)\}", block).group(1)
        out[house] = {"name": name, "suspects": [(n, j, cs_string(a)) for n, j, a, _ in sus],
                      "rooms": [r for *_, r in sus],
                      "traits": re.findall(r'"([^"]+)"', traits)}
    return out


def make_case_files(order=None, out="case-files.png", heading="Case files: every house has its own mystery"):
    order = order or ORDER
    cases = read_cases()
    cards = Image.open(os.path.join(OUT, "house-cards.png")).convert("RGB")
    row_h = (cards.height + 8) // len(ORDER)
    CW, CH, PAD, TOP = 440, 540, 14, 50
    rows = (len(order) + 1) // 2
    W, H = 2 * CW + 3 * PAD, TOP + rows * CH + (rows + 1) * PAD
    img, d = canvas(W, H)
    text(d, (W / 2, 26), heading, 20, ORANGE, anchor="mm")
    for k, case_id in enumerate(order):
        house = case_id.split("#")[0]
        c = cases[case_id]
        lone = k == len(order) - 1 and k % 2 == 0  # an odd one out sits in the middle
        x0, y0 = PAD + (k % 2) * (CW + PAD) + (CW // 2 + PAD // 2 if lone else 0), TOP + PAD + (k // 2) * (CH + PAD)
        rect(d, (x0, y0, x0 + CW, y0 + CH), fill=(26, 20, 40), outline=(70, 55, 95), radius=10)
        r = CARD_ROW[house]
        thumb = cards.crop((10, r * row_h + 40, 410, r * row_h + 200)).resize(((CW - 20) * SS, 160 * SS), Image.LANCZOS)
        img.paste(thumb, ((x0 + 10) * SS, (y0 + 10) * SS))
        y = y0 + 182
        text(d, (x0 + 14, y), c["name"], 16, ORANGE)
        y += 22
        text(d, (x0 + 14, y), SIZE[house] if case_id == house else "Return visit: calls once the first case here is solved", 11, MUTED, weight="Regular")
        y += 24
        for (name, job, alibi), room in zip(c["suspects"], c["rooms"]):
            text(d, (x0 + 14, y), name, 13, INK)
            text(d, (x0 + CW - 14, y + 1), job, 11, MUTED, weight="Regular", anchor="ra")
            y += 18
            lines = wrap(alibi, 62)[:2]
            for i, ln in enumerate(lines):
                text(d, (x0 + 22, y), ln, 11, (190, 180, 210), weight="Regular")
                y += 15
            text(d, (x0 + 22, y), "Check it: search the " + room + ("" if room in HOUSE_ROOMS[house] else " (in town)"),
                 10, (255, 190, 110))
            y += 14
            y += 8
        text(d, (x0 + 14, y + 2), "Clues", 12, (255, 220, 70))
        y += 22
        cx = x0 + 14
        for t in c["traits"]:
            w = 9 + len(t) * 6.4
            if cx + w > x0 + CW - 10:
                cx, y = x0 + 14, y + 24
            rect(d, (cx, y, cx + w, y + 19), fill=(60, 44, 80), radius=9)
            text(d, (cx + w / 2, y + 10), t, 10, INK, anchor="mm")
            cx += w + 6
    save_png(finish(img), out)


RETURN_VISITS = [h + "#2" for h in ORDER[:4]]


def make_return_visits():
    make_case_files(RETURN_VISITS, "return-visits.png", "Return visits: every house calls again with a new mystery")


# Something from each house to stand beside its suspects
HOUSE_PROPS = {
    "PembertonCottage": [("pumpkin_stack", (4.0, 0, 0.4), 0, 0.8), ("mums", (-4.0, 0, 0.3), 0, 1.0)],
    "HollowCreekFarm": [("haybale", (4.1, 0, 0.5), 20, 1.0), ("cornstalks", (-4.1, 0, 0.6), 0, 1.0)],
    "WillowLaneVictorian": [("tomb_cross", (4.0, 0, 0.6), -10, 0.9), ("cat", (-3.9, 0, 0.2), 40, 1.0)],
    "BlackwoodManor": [("jack", (4.0, 0, 0.3), -20, 1.0), ("lantern", (-4.0, 0, 0.3), 0, 1.0)],
    "HistoricalSociety": [("bench", (4.1, 0, 0.6), -20, 0.8), ("wall_lantern", (-4.0, 1.4, 0.4), 0, 1.2)],
}


def make_suspects():
    import render3d as r3
    from make_images import font
    from PIL import ImageDraw
    cases = read_cases()
    slots = ["Groundskeeper", "Heiress", "Rival", "Cook"]
    W, RH, TOP = 900, 270, 46
    sheet = Image.new("RGB", (W, TOP + len(ORDER) * RH), (14, 10, 24))
    d = ImageDraw.Draw(sheet)
    d.text((W / 2, 24), "Who you'll meet: the suspects at each house", font=font(19), fill=ORANGE, anchor="mm")
    props = r3.costumes()["props"]
    xs = [-2.7, -0.9, 0.9, 2.7]
    for k, house in enumerate(ORDER):
        m = r3.Mesh()
        m.add_shape("box", (0, -0.05, -1), (14, 0.1, 8), (0, 0, 0), (0.16, 0.2, 0.14), surface=r3.SURFACE_ID["grass"])
        for x, slot in zip(xs, slots):
            m.add_parts(r3.suspect_outfit(slot, house), (x, 0, 0), 180 - x * 4)
        for pid, pos, ry, sc in HOUSE_PROPS[house]:
            m.add_parts(props[pid]["parts"], pos, ry, sc)
        lights = [{"p": [2.4, 2.8, -2.6], "c": [0.8, 0.85, 1.0], "range": 7, "intensity": 1.2},
                  {"p": [-2.4, 2.6, -2.6], "c": [1.0, 0.7, 0.45], "range": 7, "intensity": 1.2},
                  {"p": [0, 0.6, -1.0], "c": [1, 0.55, 0.2], "range": 3, "intensity": 0.8}]
        cam = r3.Camera((0, 1.3, -7.4), (0, 1.0, 0), 30, W, RH)
        img = r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.02,
                        ambient=(0.22, 0.17, 0.3), moon=False)
        dd = ImageDraw.Draw(img, "RGBA")
        c = cases[house]
        dd.rounded_rectangle([8, 8, 16 + len(c["name"]) * 8.4, 34], radius=7, fill=(10, 8, 20, 190))
        dd.text((14, 12), c["name"], font=font(14), fill=(255, 200, 120))
        for x, (name, job, _) in zip(xs, c["suspects"]):
            sx = cam.project((x, 0, 0))[0][0]
            for j, (t, sz, col) in enumerate(((name, 12, INK), (job, 10, MUTED))):
                f = font(sz)
                box = dd.textbbox((sx, RH - 34 + j * 16), t, font=f, anchor="mm")
                dd.rounded_rectangle([box[0] - 5, box[1] - 2, box[2] + 5, box[3] + 2], radius=5, fill=(10, 8, 20, 170))
                dd.text((sx, RH - 34 + j * 16), t, font=f, fill=col, anchor="mm")
        sheet.paste(img, (0, TOP + k * RH))
        print(f"    {house} done")
    save_png(sheet, "suspects-by-house.png")


def make_witness():
    """The Banshee wails at the cottage; Hank jumps, and later tells the club what he noticed."""
    import render3d as r3
    from make_images import font
    from PIL import ImageDraw
    W, H = 900, 380
    C = r3.costumes()
    m = r3.Mesh()
    m.add_shape("box", (0, -0.05, 0), (16, 0.1, 10), (0, 0, 0), (0.16, 0.2, 0.14), surface=r3.SURFACE_ID["grass"])
    m.add_parts(C["villains"]["Banshee"]["parts"], (2.2, 0.25, 0.6), 220)
    m.add_parts(r3.suspect_outfit("Groundskeeper", "PembertonCottage"), (-0.2, 0.3, 0), 140)  # mid-hop
    m.add_parts(r3.suspect_outfit("Heiress", "PembertonCottage"), (-3.6, 0, 1.6), 160)
    m.add_parts(C["solvers"]["Sleuth"]["parts"], (-2.2, 0, -1.4), 200)
    for pid, pos, ry, sc in [("pumpkin_stack", (4.6, 0, 2.4), 0, 0.8), ("jack_scary", (0.9, 0, 1.8), 30, 1.2),
                             ("mums", (-5.0, 0, 2.6), 0, 1.0), ("tomb_round", (3.8, 0, -0.6), -20, 0.9)]:
        m.add_parts(C["props"][pid]["parts"], pos, ry, sc)
    lights = [{"p": [2.2, 1.6, 0.0], "c": [0.5, 1.0, 1.0], "range": 5, "intensity": 1.8},
              {"p": [-2.0, 2.6, -2.4], "c": [1.0, 0.75, 0.5], "range": 7, "intensity": 1.0},
              {"p": [0.9, 0.4, 1.8], "c": [1, 0.55, 0.2], "range": 3, "intensity": 1.0}]
    cam = r3.Camera((0.2, 2.0, -7.2), (0, 1.1, 0.4), 40, W, H)
    img = r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.025,
                    ambient=(0.2, 0.16, 0.3), moon=False)
    d = ImageDraw.Draw(img, "RGBA")

    def bubble(anchor, lines, fill=(10, 8, 20, 210), col=INK, size=13):
        f = font(size)
        w = max(d.textlength(t, font=f) for t in lines) + 20
        h = len(lines) * (size + 5) + 12
        x, y = anchor
        d.rounded_rectangle([x - w / 2, y - h, x + w / 2, y], radius=9, fill=fill)
        d.polygon([(x - 8, y), (x + 8, y), (x, y + 10)], fill=fill)
        for i, t in enumerate(lines):
            d.text((x, y - h + 8 + i * (size + 5)), t, font=f, fill=col, anchor="ma")

    hx, hy, _ = cam.project((-0.2, 2.5, 0))[0]
    bubble((hx, hy), ["Eek!"], col=(255, 200, 120), size=16)
    bx, by, _ = cam.project((2.2, 2.6, 0.6))[0]
    bubble((bx, by), ["The Banshee wails"], col=(170, 240, 255))
    d.rounded_rectangle([12, H - 74, 470, H - 12], radius=10, fill=(10, 8, 20, 215))
    d.text((24, H - 66), "Later, on the Suspect Board:", font=font(12), fill=MUTED)
    d.text((24, H - 46), "Hank Moody: \"It rushed right past me in the dark!", font=font(13), fill=INK)
    d.text((24, H - 28), "I'm sure I noticed potting soil.\"", font=font(13), fill=INK)
    d.rounded_rectangle([12, 12, 352, 92], radius=10, fill=(10, 8, 20, 200))
    for i, (t, c) in enumerate([("Scares make suspects jump and scurry away.", INK),
                                ("A suspect who saw it up close is a witness:", INK),
                                ("innocents name a real detail of the culprit,", (150, 230, 150)),
                                ("the culprit names someone else's.", (255, 150, 150))]):
        d.text((24, 20 + i * 17), t, font=font(12), fill=c)
    save_png(img, "witness.png")


JOBS = {"cases": make_case_files, "returns": make_return_visits, "suspects": make_suspects, "witness": make_witness}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(JOBS):
        JOBS[name]()
