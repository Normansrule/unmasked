#!/usr/bin/env python3
"""
Pictures for rounds 31 and 32: how worldgen.py grows the town (worldgen.png), a mockup of the Club
Book page (club-book.png) and trick-or-treat on the new streets (trick-or-treat.png). Drawn from the
generator's own data, not captured in Unity.

    python3 Docs/tools/make_world_pictures.py
"""
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_images import font, save_png  # noqa: E402
import worldgen as wg  # noqa: E402
import make_town as mt  # noqa: E402  (building the town is quick and seeded)

BG = (22, 18, 14)
SHEET = (36, 29, 23)
INK = (243, 234, 219)
MUTED = (205, 191, 171)
FAINT = (162, 147, 127)
ACCENT = (239, 108, 91)
GOOD = (130, 207, 159)
LANTERN = (255, 200, 107)


def grid_image(a, size):
    pal = np.array([[34, 52, 30], [120, 112, 128], [70, 68, 80], [45, 80, 120], [92, 80, 40], [232, 150, 70]], dtype=np.uint8)
    img = Image.fromarray(pal[a[::-1]])
    return img.resize(size, Image.NEAREST)


def panel(img, x, y, w, h, title, sub):
    d = ImageDraw.Draw(img)
    d.text((x, y), title, font=font(22, "Bold"), fill=INK)
    d.text((x, y + 30), sub, font=font(14, "Medium"), fill=MUTED)


def make_worldgen():
    W = mt.WORLD
    PW, PH = 400, 546
    img = Image.new("RGB", (4 * PW + 5 * 24, PH + 190), BG)
    d = ImageDraw.Draw(img)
    stages = [("1  What's already there", "Every box and prop stamped on a 1 m grid", W.snapshots["stamped"]),
              ("2  Streets and plots", "New streets, then a plot wherever it fits", W.snapshots["parcels"]),
              ("3  Landmarks", "The biggest gaps left get a place to visit", W.grid.a)]
    for i, (t, sub, a) in enumerate(stages):
        x = 24 + i * (PW + 24)
        panel(img, x, 20, PW, PH, t, sub)
        img.paste(grid_image(a, (PW, PH)), (x, 80))
    # 4: a yard solved by Wave Function Collapse
    x = 24 + 3 * (PW + 24)
    panel(img, x, 20, PW, PH, "4  A yard, by WFC", "Tiles that may sit side by side; house fixed first")
    rng = random.Random(7)
    cols, rows = 8, 10
    fixed = {(i, j): "house" for i in range(2, 6) for j in range(3, 7)}
    fixed.update({(4, j): "walk" for j in range(0, 3)})
    tiles = wg.wfc(cols, rows, fixed, rng)
    col = {"lawn": (52, 78, 44), "stone": (138, 132, 122), "bed": (170, 90, 160), "patch": (226, 120, 40), "tree": (192, 74, 42),
           "shed": (110, 130, 150), "grave": (160, 160, 168), "hay": (210, 180, 90), "spook": (172, 153, 242), "house": (60, 50, 70),
           "walk": (120, 116, 108)}
    cell = 48
    ox, oy = x + (PW - cols * cell) // 2, 80
    for (i, j), t in tiles.items():
        r = [ox + i * cell, oy + (rows - 1 - j) * cell, ox + (i + 1) * cell - 2, oy + (rows - j) * cell - 2]
        d.rectangle(r, fill=col[t])
    d.text((ox + 2 * cell + 8, oy + (rows - 6) * cell + 70), "house", font=font(16, "Bold"), fill=INK)
    ly = oy + rows * cell + 12
    for k, t in enumerate(["lawn", "stone", "bed", "patch", "tree", "shed", "grave", "hay", "spook", "walk"]):
        lx = x + (k % 5) * 80
        yy = ly + (k // 5) * 24
        d.rectangle([lx, yy + 3, lx + 14, yy + 17], fill=col[t])
        d.text((lx + 20, yy + 2), t, font=font(13, "Medium"), fill=MUTED)
    # key for the grids
    ky = 80 + PH + 18
    keys = [((34, 52, 30), "open grass"), ((120, 112, 128), "built"), ((70, 68, 80), "street"), ((45, 80, 120), "creek"),
            ((92, 80, 40), "kept clear: lots, woods, the square"), ((232, 150, 70), "new: plots and landmarks")]
    for k, (c, t) in enumerate([((34, 52, 30), "open grass"), ((120, 112, 128), "built"), ((70, 68, 80), "street"), ((45, 80, 120), "creek"),
                                ((92, 80, 40), "kept clear: lots, woods, the square"), ((232, 150, 70), "new: plots and landmarks")]):
        kx = 24 + sum(int(d.textlength(t2, font=font(14, "Medium"))) + 60 for _, t2 in keys[:k])
        d.rectangle([kx, ky + 2, kx + 16, ky + 18], fill=c)
        d.text((kx + 24, ky + 1), t, font=font(14, "Medium"), fill=MUTED)
    s = W.stats
    d.text((24, ky + 34), f"{len(mt.T.L.get('newRoads', []))} new streets · {s['houses']} houses, each with a WFC yard · {len(W.features)} landmarks · "
                          f"{len(mt.T.L['collectibles'])} lost lanterns · seeded, so every computer builds the same town",
           font=font(15, "Bold"), fill=INK)
    d.text((24, ky + 60), "Illustration drawn from Docs/tools/worldgen.py's own grid, not an engine capture.", font=font(13, "Medium"), fill=FAINT)
    save_png(img, "worldgen.png")


def make_club_book():
    w, h = 980, 800
    img = Image.new("RGB", (w, h), (8, 6, 5))
    d = ImageDraw.Draw(img, "RGBA")
    # a dimmed night behind the page
    rng = random.Random(3)
    for _ in range(120):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        d.ellipse([x, y, x + 2, y + 2], fill=(255, 220, 160, rng.randint(20, 70)))
    px0, py0, px1, py1 = 70, 24, w - 70, h - 24
    d.rectangle([px0, py0, px1, py1], fill=(22, 18, 14, 245))
    d.text((px0 + 28, py0 + 22), "Club Book", font=font(36, "Black"), fill=INK)
    d.text((px1 - 190, py0 + 34), "385", font=font(26, "Black"), fill=ACCENT)
    d.text((px1 - 128, py0 + 38), "candy", font=font(22, "Bold"), fill=INK)
    d.text((px0 + 28, py0 + 76), "11 of 34 challenges · 3 of 17 looks · 7 of 24 lanterns. Candy is earned by playing; nothing here costs money.",
           font=font(14, "Medium"), fill=MUTED)
    tabs = ["Challenges", "Wardrobe", "Lost lanterns", "Places"]
    tx = px0 + 28
    for i, t in enumerate(tabs):
        tw = 170
        d.rectangle([tx, py0 + 108, tx + tw - 8, py0 + 144], fill=(70, 58, 46) if i == 0 else (36, 29, 23), outline=(61, 51, 42))
        d.text((tx + (tw - 8) / 2, py0 + 126), t, font=font(15, "Bold"), fill=INK, anchor="mm")
        tx += tw
    y = py0 + 166
    d.text((px0 + 28, y), "House calls", font=font(22, "Bold"), fill=INK)
    d.text((px0 + 200, y + 5), "2/5", font=font(16, "Bold"), fill=FAINT)
    d.text((px0 + 28, y + 30), "One case at every house in town. Press Play to make it tonight's call.", font=font(13, "Medium"), fill=FAINT)
    rows = [("Pemberton Cottage", "Solve the case at 14 Elm Street.", 40, True, None),
            ("Hollow Creek Farm", "Solve the case out on Old Mill Road.", 50, True, None),
            ("Willow Lane Victorian", "Solve the case at 3 Willow Lane.", 60, False, "Play"),
            ("Blackwood Manor", "Solve the case past the creek: the longest night.", 80, False, "Play")]
    y += 58
    for title, text, reward, done, btn in rows:
        d.rectangle([px0 + 28, y, px1 - 28, y + 60], fill=SHEET)
        d.text((px0 + 44, y + 10), title, font=font(16, "Bold"), fill=INK)
        if done:
            tw = d.textlength(title, font=font(16, "Bold"))
            d.text((px0 + 44 + tw, y + 10), "  · done", font=font(16, "Bold"), fill=GOOD)
        d.text((px0 + 44, y + 34), text, font=font(13, "Medium"), fill=MUTED)
        d.text((px1 - 190, y + 10), "Earned" if done else f"+{reward} candy", font=font(15, "Bold"), fill=GOOD if done else INK)
        if btn:
            d.rectangle([px1 - 190, y + 30, px1 - 44, y + 54], fill=ACCENT)
            d.text((px1 - 117, y + 42), btn, font=font(14, "Bold"), fill=(29, 18, 13), anchor="mm")
        y += 68
    y += 10
    d.text((px0 + 28, y), "Around town", font=font(22, "Bold"), fill=INK)
    d.text((px0 + 210, y + 5), "1/6", font=font(16, "Bold"), fill=FAINT)
    y += 40
    for title, text, reward, prog, goal in (("Sights of Hollow Creek", "Visit all eight landmarks: the maze, the cemetery, the pond and the rest.", 60, 3, 8),
                                            ("Lamplighter", "Find six lost lanterns.", 50, 7, 6)):
        done = prog >= goal
        d.rectangle([px0 + 28, y, px1 - 28, y + 74], fill=SHEET)
        d.text((px0 + 44, y + 10), title, font=font(16, "Bold"), fill=INK)
        d.text((px0 + 44, y + 34), text, font=font(13, "Medium"), fill=MUTED)
        if not done:
            bx0, bx1 = px0 + 44, px1 - 220
            d.rectangle([bx0, y + 56, bx1, y + 62], fill=(46, 38, 30))
            d.rectangle([bx0, y + 56, bx0 + (bx1 - bx0) * prog / goal, y + 62], fill=ACCENT)
        d.text((px1 - 190, y + 10), "Earned" if done else f"+{reward} candy", font=font(15, "Bold"), fill=GOOD if done else INK)
        y += 82
    # footer
    d.text((px0 + 28, py1 - 40), "[x] Suggest a break after three nights in a row", font=font(14, "Medium"), fill=MUTED)
    d.rectangle([px1 - 150, py1 - 48, px1 - 28, py1 - 16], fill=ACCENT)
    d.text((px1 - 89, py1 - 32), "Close", font=font(14, "Bold"), fill=(29, 18, 13), anchor="mm")
    d.text((w / 2, h - 10), "Mockup of the in-game page (K), not an engine capture", font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "club-book.png")


def answers_tonight(home, night, heard=()):
    """Doorstep.AnswersTonight, the same sums as the C# (32-bit ints that wrap)."""
    if home["tale"] >= 0 and home["tale"] not in heard:
        return True
    wrap = lambda v: (v + 2 ** 31) % 2 ** 32 - 2 ** 31
    x = wrap(night * 7919)
    for ch in home["id"]:
        x = wrap(x * 31 + ord(ch))
    x = wrap(x ^ (x >> 13))
    return (x & 0x7fffffff) % 10 < 7


def wrap_text(d, text, f, width):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if d.textlength(trial, font=f) > width and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


def tales_from_cs():
    import re
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Assets", "Unmasked", "Scripts", "Town", "Tales.cs"), encoding="utf-8").read()
    out = []
    for t in re.finditer(r'T\("([^"]*)",\s*((?:"[^"]*"\s*\+?\s*)+)\)', src):
        out.append((t.group(1), "".join(re.findall(r'"([^"]*)"', t.group(2)))))
    return out


def make_doors():
    homes = mt.T.L["homes"]
    tales = tales_from_cs()
    night, heard = 3, {0, 2, 5}
    base = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "images", "town-map.png")).convert("RGB")
    X0, X1, Z0, Z1 = -158.0, 118.0, -104.0, 294.0
    MW = base.width
    MH = int(MW * (Z1 - Z0) / (X1 - X0))
    town = base.crop((0, 0, MW, MH))
    k = 0.72
    town = town.resize((int(MW * k), int(MH * k)), Image.LANCZOS)
    W, H = 1500, town.height + 190
    img = Image.new("RGB", (W, H), BG)
    img.paste(town, (24, 90))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((24, 24), "Trick or treat", font=font(34, "Black"), fill=INK)
    d.text((24, 64), "Every door on the new streets, on a night after three stories have been heard", font=font(15, "Medium"), fill=MUTED)

    def P(x, z):
        return 24 + (x - X0) / (X1 - X0) * MW * k, 90 + (Z1 - z) / (Z1 - Z0) * MH * k

    lit = dark = story = 0
    for h in homes:
        x, z = P(h["door"][0], h["door"][2])
        if h["tale"] >= 0 and h["tale"] not in heard:
            d.ellipse([x - 9, z - 9, x + 9, z + 9], outline=(172, 153, 242, 255), width=3)
            story += 1
        if answers_tonight(h, night, heard):
            d.ellipse([x - 7, z - 7, x + 7, z + 7], fill=(255, 190, 90, 70))
            d.ellipse([x - 4, z - 4, x + 4, z + 4], fill=LANTERN)
            lit += 1
        else:
            d.ellipse([x - 4, z - 4, x + 4, z + 4], fill=(90, 84, 78), outline=(30, 26, 22))
            dark += 1
    ky = 90 + town.height + 16
    kx = 24
    for c, ring, t in ((LANTERN, None, f"porch light on: {lit}"), ((90, 84, 78), None, f"out tonight: {dark}"),
                       (None, (172, 153, 242), f"a story not heard yet: {story} (always home)")):
        if c:
            d.ellipse([kx, ky + 4, kx + 12, ky + 16], fill=c)
        else:
            d.ellipse([kx - 2, ky + 2, kx + 14, ky + 18], outline=ring, width=3)
        d.text((kx + 22, ky + 1), t, font=font(14, "Medium"), fill=MUTED)
        kx += int(d.textlength(t, font=font(14, "Medium"))) + 52
    d.text((24, ky + 30), "Which families are home changes every night. Each door gives one treat a night.", font=font(13, "Medium"), fill=FAINT)

    # Right: one knock, then the Stories tab
    rx = 24 + town.width + 40
    rw = W - rx - 24
    home = next(h for h in homes if h["tale"] == 1)
    tale = tales[1]
    d.text((rx, 96), f"Knock knock: {home['family']}, {home['address']}", font=font(20, "Bold"), fill=INK)
    # a porch: door, light, bowl
    py = 136
    d.rectangle([rx, py, rx + rw, py + 250], fill=(28, 22, 30))
    for i in range(40):
        d.ellipse([rx + 120 - i * 3, py + 50 - i * 2, rx + 120 + i * 3, py + 50 + i * 2], fill=(255, 180, 90, max(0, 30 - i)))
    d.rectangle([rx + 150, py + 60, rx + 230, py + 250], fill=(70, 40, 30))
    d.polygon([(rx + 150, py + 60), (rx + 172, py + 66), (rx + 172, py + 250), (rx + 150, py + 250)], fill=(255, 196, 120))
    d.ellipse([rx + 112, py + 42, rx + 128, py + 58], fill=LANTERN)
    d.ellipse([rx + 158, py + 150, rx + 206, py + 170], fill=(232, 115, 28))
    for j, c in enumerate([(160, 80, 190), (255, 210, 120), (160, 80, 190)]):
        d.ellipse([rx + 166 + j * 12, py + 146, rx + 176 + j * 12, py + 156], fill=c)
    d.rectangle([rx + 100, py + 236, rx + 280, py + 250], fill=(106, 90, 72))
    # the bubble
    bx0, bx1 = rx + 300, rx + rw - 14
    text = f"Oh, the Mystery Club! Here, have a handful. Have you heard about {tale[0][0].lower() + tale[0][1:]}? {tale[1]}"
    lines = wrap_text(d, text, font(14, "Medium"), bx1 - bx0 - 28)
    bh = 24 + 20 * len(lines)
    d.rounded_rectangle([bx0, py + 14, bx1, py + 14 + bh], 10, fill=(243, 234, 219, 245))
    d.polygon([(bx0, py + 70), (bx0 - 16, py + 84), (bx0, py + 90)], fill=(243, 234, 219, 245))
    for i, line in enumerate(lines):
        d.text((bx0 + 14, py + 26 + i * 20), line, font=font(14, "Medium"), fill=(40, 30, 24))
    d.text((rx, py + 262), "+5 candy for a new door, +3 after that, +10 for a story", font=font(14, "Bold"), fill=GOOD)

    sy = py + 310
    d.rectangle([rx, sy, rx + rw, 90 + town.height], fill=SHEET)
    d.text((rx + 20, sy + 16), "Club Book: Stories", font=font(22, "Black"), fill=INK)
    d.text((rx + 20, sy + 48), f"{len(heard) + 1} of {len(tales)} heard", font=font(14, "Medium"), fill=MUTED)
    yy = sy + 80
    have = sorted(heard | {1})
    for i, (title, body) in enumerate(tales):
        if yy > 90 + town.height - 50:
            d.text((rx + 20, yy), f"... {len(tales) - i} more", font=font(14, "Medium"), fill=FAINT)
            break
        if i in have:
            d.text((rx + 20, yy), f"{i + 1}. {title}", font=font(15, "Bold"), fill=INK)
            first = wrap_text(d, body, font(13, "Medium"), rw - 40)[:2]
            for j, line in enumerate(first):
                d.text((rx + 20, yy + 22 + j * 18), (line.rstrip(".") + "..." if j == len(first) - 1 else line), font=font(13, "Medium"), fill=MUTED)
            yy += 22 + 18 * len(first) + 12
        else:
            teller = next(h for h in homes if h["tale"] == i)
            d.text((rx + 20, yy), f"{i + 1}. Not heard yet", font=font(15, "Bold"), fill=FAINT)
            d.text((rx + 20, yy + 20), f"Someone on {teller['street']} knows this one.", font=font(13, "Medium"), fill=FAINT)
            yy += 48
    d.text((W / 2, H - 22), "Drawn from HollowCreek.json and Town/Tales.cs, not an engine capture", font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "trick-or-treat.png")


if __name__ == "__main__":
    import sys as _sys
    if "doors" in _sys.argv[1:]:
        make_doors()
    else:
        make_worldgen()
        make_club_book()
        make_doors()
