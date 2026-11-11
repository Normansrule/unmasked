#!/usr/bin/env python3
"""
The data behind the website's Suspect Board and progress page, taken from the game itself so the
site can never drift from what's in Unity.

    python3 Docs/tools/make_site_data.py      # writes site/data/game.json

  cases     every case in Assets/Unmasked/Scripts/Mystery/Cases.cs: premise, suspects with their
            alibis, motives and traits, and the eight clues (read with tools/casecheck's parser)
  houses    the five lots in Resources/HollowCreek.json: name, street, size, blurb
  legends   the four folklore masks in Resources/Costumes.json: legend, origin, power
  club      the Club Book in Assets/Unmasked/Scripts/Core/ClubBook.cs: challenge chapters and the
            wardrobe (earned with candy, never bought), plus the town's landmarks and lanterns
  rounds    the build log from make_readme_anim.py, plus milestone progress from Docs/PROGRESS.md
  portraits site/img/legend-<id>.jpg, each legend cut from Docs/images/villains.png (needs Pillow)
  screens   site/img/world-map.jpg and site/img/menu.jpg for the device frames, from Docs/images
            world-map.png and menu-backdrop.png (needs Pillow)

Run it whenever Cases.cs, PROGRESS.md or the round list changes. The site is plain files in site/,
published by .github/workflows/pages.yml.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools", "casecheck"))
import casecheck  # noqa: E402

RES = os.path.join(ROOT, "Assets", "Unmasked", "Resources")
STR = casecheck.STR


def field(block, key):
    m = re.search(key + r"\s*=\s*" + STR, block)
    return m.group(1).replace('\\"', '"') if m else ""


def blocks(src):
    body = src[src.index("public static readonly Spec[] All"):]
    return re.split(r"\n\s*new Spec\s*\n", body)[1:]


def read_rounds_and_progress():
    """ROUNDS and the milestone table, without importing the picture tools (no Pillow needed)."""
    text = open(os.path.join(HERE, "make_readme_anim.py"), encoding="utf-8").read()
    rounds_src = re.search(r"^ROUNDS = \[(.*?)^\]", text, re.S | re.M).group(1)
    rounds = [{"title": t, "line": l} for t, l, _ in re.findall(r'\(\s*' + STR + r',\s*' + STR + r',\s*' + STR + r'\s*\)', rounds_src)]
    milestones, cur = [], None
    for line in open(os.path.join(ROOT, "Docs", "PROGRESS.md"), encoding="utf-8"):
        m = re.match(r"^## (.+)", line)
        if m:
            cur = {"name": m.group(1).strip(), "done": 0, "total": 0}
            milestones.append(cur)
        t = re.match(r"^\s*- \[([ x])\]", line)
        if t and cur:
            cur["total"] += 1
            cur["done"] += t.group(1) == "x"
    return rounds, [m for m in milestones if m["total"]]


def legend_portraits(legends):
    """Each legend's portrait for the site, cut from the villains line-up. Skipped without Pillow."""
    try:
        from PIL import Image
    except ImportError:
        print("  legend portraits skipped (pip install pillow)")
        return
    lineup = Image.open(os.path.join(ROOT, "Docs", "images", "villains.png")).convert("RGB")
    centres = {"HeadlessHorseman": 150, "Banshee": 450, "StingyJack": 748, "BabaYaga": 1042}
    for l in legends:
        cx = centres.get(l["id"])
        if cx is None:
            continue
        x0 = max(0, cx - 150)
        crop = lineup.crop((x0, 150, x0 + 300, 470)).resize((450, 480), Image.LANCZOS)
        crop.save(os.path.join(ROOT, "site", "img", f"legend-{l['id']}.jpg"), quality=86, optimize=True, progressive=True)


def device_screens():
    """The pictures shown inside the site's laptop and tablet frames. Skipped without Pillow."""
    try:
        from PIL import Image
    except ImportError:
        print("  device screens skipped (pip install pillow)")
        return
    # the laptop shows the menu (16:10, cropped); the tablet shows the whole world map (4:3, the
    # square map centred on its own dark edge colour so nothing at the borders is cut off)
    for src, dst, aspect, size, fit in (("menu-backdrop.png", "menu.jpg", 16 / 10, (1280, 800), False),
                                        ("world-map.png", "world-map.jpg", 4 / 3, (1200, 900), True)):
        path = os.path.join(ROOT, "Docs", "images", src)
        if not os.path.exists(path):
            print(f"  {dst} skipped ({src} not made yet)")
            continue
        im = Image.open(path).convert("RGB")
        w, h = im.size
        if fit:
            canvas = Image.new("RGB", (round(h * aspect), h), im.getpixel((2, 2)))
            canvas.paste(im, ((canvas.width - w) // 2, 0))
            im = canvas
        else:
            tw, th = (w, round(w / aspect)) if h >= w / aspect else (round(h * aspect), h)
            im = im.crop((0, (h - th) // 2, tw, (h - th) // 2 + th))  # keep the left edge: the menu panel lives there
        im.resize(size, Image.LANCZOS).save(os.path.join(ROOT, "site", "img", dst), quality=84, optimize=True, progressive=True)


def read_club():
    """Challenge chapters and wardrobe looks from ClubBook.cs, and the town's places from HollowCreek.json."""
    src = open(os.path.join(ROOT, "Assets", "Unmasked", "Scripts", "Core", "ClubBook.cs"), encoding="utf-8").read()
    chapters = []
    for m in re.finditer(r'new\(\) \{ Name = ' + STR + r', Blurb = ' + STR + r', Items = new\[\](.*?)\}\},', src, re.S):
        items = []
        for c in re.finditer(r'C\(' + STR + r', ' + STR + r', ' + STR + r', ([^,]+), (\d+),(.*?)\),?\n', m.group(3)):
            house = re.search(r'\), "(\w+)"$', c.group(6).strip())
            items.append({"id": c.group(1), "title": c.group(2), "text": c.group(3), "reward": int(c.group(5)),
                          "house": house.group(1) if house else None})
        chapters.append({"name": m.group(1), "blurb": m.group(2), "items": items})
    wardrobe = [{"id": w.group(1), "name": w.group(2), "slot": w.group(3), "price": int(w.group(4)), "a": "#" + w.group(5), "b": "#" + w.group(6),
                 "blurb": w.group(7)}
                for w in re.finditer(r'W\(' + STR + r', ' + STR + r', ' + STR + r', (\d+), ' + STR + r', ' + STR + r', ' + STR + r'\)', src)]
    # Gift(W(...), "how to earn it"): given in play, never sold (the lamplighter's cap)
    for g in re.finditer(r'Gift\(W\(' + STR + r'.*?\),\s*' + STR + r'\)', src, re.S):
        for w in wardrobe:
            if w["id"] == g.group(1):
                w["gift"] = g.group(2)
    town = json.load(open(os.path.join(RES, "HollowCreek.json"), encoding="utf-8"))
    # The Stories of Hollow Creek (Town/Tales.cs): T("title", "text" + "text" ...)
    tales_src = open(os.path.join(ROOT, "Assets", "Unmasked", "Scripts", "Town", "Tales.cs"), encoding="utf-8").read()
    tales = []
    for t in re.finditer(r'T\(' + STR + r',\s*((?:' + STR + r'\s*\+?\s*)+)\)', tales_src):
        text = "".join(m.group(1) for m in re.finditer(STR, t.group(2)))
        tales.append({"title": t.group(1), "text": text})
    homes = town.get("homes", [])
    return {"chapters": chapters, "wardrobe": wardrobe, "tales": tales, "doors": len(homes),
            "families": [h["family"] for h in homes[:3]],
            "landmarks": [{"name": l["n"], "district": l["district"]} for l in town.get("landmarks", [])],
            "lanterns": len(town.get("collectibles", [])), "streets": len(town.get("roads", [])),
            "districts": [d["n"] for d in town.get("districts", [])]}


def main():
    src = open(casecheck.CASES, encoding="utf-8").read()
    table, bits = casecheck.slot_traits(src)
    slot_bits = [sorted(bits.index(t) for t in row) for row in table]

    houses = {}
    for lot in json.load(open(os.path.join(RES, "HollowCreek.json"), encoding="utf-8"))["lots"]:
        houses[lot["id"]] = {k: lot.get(k) for k in ("id", "name", "street", "size", "floors", "difficulty", "blurb")}
    houses.setdefault("BlackwoodManor", {"id": "BlackwoodManor", "name": "Blackwood Manor"})

    cases = []
    for parsed, block in zip(casecheck.specs(src), blocks(src)):
        cid = parsed["house"] + ("" if parsed["visit"] <= 1 else f"#{parsed['visit']}")
        cases.append({
            "id": cid,
            "house": parsed["house"],
            "houseName": houses.get(parsed["house"], {}).get("name", parsed["house"]),
            "visit": parsed["visit"],
            "name": parsed["name"],
            "premise": field(block, "Premise"),
            "recovered": field(block, "Recovered"),
            "traits": parsed["traits"],
            "suspects": [
                {"name": s[0], "job": s[1], "bio": s[2], "alibi": s[3], "alibiRoom": s[4] if len(s) > 4 else "",
                 "motive": parsed["motives"][i] if i < len(parsed["motives"]) else "", "traits": slot_bits[i]}
                for i, s in enumerate(parsed["suspects"])
            ],
            "clues": [{"id": c[0], "name": c[1], "description": c[2], "trait": i} for i, c in enumerate(parsed["clues"])],
        })

    legends = [{k: v.get(k) for k in ("id", "name", "origin", "legend", "power", "powerBlurb")}
               for v in json.load(open(os.path.join(RES, "Costumes.json"), encoding="utf-8"))["villains"]]
    rounds, milestones = read_rounds_and_progress()

    club = read_club()
    out = {"cases": cases, "houses": list(houses.values()), "legends": legends, "club": club, "rounds": rounds, "milestones": milestones}
    path = os.path.join(ROOT, "site", "data", "game.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    legend_portraits(legends)
    device_screens()
    print(f"  club: {len(club['chapters'])} chapters, {sum(len(c['items']) for c in club['chapters'])} challenges, "
          f"{len(club['wardrobe'])} looks, {len(club['landmarks'])} landmarks")
    print(f"{path}: {len(cases)} cases, {len(houses)} houses, {len(legends)} legends, {len(rounds)} rounds, {len(milestones)} milestones")


if __name__ == "__main__":
    main()
