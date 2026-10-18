#!/usr/bin/env python3
"""
Story and animation pictures for the README:

  story.png         "Solve the haunting. Unmask the person.": the four cases, what each haunting
                    is covering up, and why each suspect might be wearing the mask (read straight
                    from Assets/Unmasked/Scripts/Mystery/Cases.cs)
  anticipation.gif  the four anticipation tests (a chair leans back before it hops, a lamp pauses
                    and turns to look at you, a suspect swallows before answering, the trap
                    wobbles before it snaps), using the same timings as the game code

    python3 Docs/tools/make_images_story.py
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_images import canvas, circle, finish, line, poly, rect, save_gif, save_png, text, wrap, SS  # noqa: E402
from make_images_cases import CASES, ORDER, read_cases  # noqa: E402

# The storybook palette (Docs/ART_DIRECTION.md)
NIGHT_TEAL = (22, 38, 46)
TEAL = (46, 86, 92)
AMBER = (255, 176, 74)
VIOLET = (168, 120, 230)
PARCHMENT = (240, 226, 196)
SAGE = (150, 172, 128)
WOOD = (132, 84, 52)
INK_DARK = (52, 36, 30)
HOUSE_NAME = {"PembertonCottage": "Pemberton Cottage", "HollowCreekFarm": "Hollow Creek Farm",
              "WillowLaneVictorian": "Willow Lane Victorian", "BlackwoodManor": "Blackwood Manor",
              "HistoricalSociety": "Historical Society"}


def read_story():
    src = open(CASES, encoding="utf-8").read()
    out = {}
    for block in re.split(r"\n\s*new Spec\s*\n", src)[1:]:
        house = re.search(r'HouseId = "(\w+)"', block).group(1)
        visit = re.search(r"Visit = (\d+)", block)
        if visit and int(visit.group(1)) > 1:
            house += "#" + visit.group(1)  # a return visit: Cases.Spec.CaseId
        premise = re.search(r'Premise = "([^"]+)"', block).group(1)
        recovered = re.search(r'Recovered = "([^"]+)"', block).group(1)
        motives = re.findall(r'"([^"]+)"', re.search(r"Motives = new\[\]\s*\{([^}]*)\}", block).group(1))
        out[house] = {"premise": premise, "motives": motives, "recovered": recovered}
    return out


# ---------------------------------------------------------------------------
# story.png

def mask_icon(d, cx, cy, kind):
    if kind == 0:   # Headless Horseman: a pumpkin
        circle(d, (cx, cy), 15, fill=(230, 120, 40))
        rect(d, (cx - 2, cy - 21, cx + 2, cy - 13), fill=(90, 120, 60))
        poly(d, [(cx - 9, cy - 4), (cx - 4, cy - 4), (cx - 6.5, cy - 9)], fill=(255, 220, 120))
        poly(d, [(cx + 4, cy - 4), (cx + 9, cy - 4), (cx + 6.5, cy - 9)], fill=(255, 220, 120))
        rect(d, (cx - 8, cy + 3, cx + 8, cy + 6), fill=(255, 220, 120))
    elif kind == 1:  # Banshee: a veil
        poly(d, [(cx, cy - 20), (cx + 15, cy + 2), (cx + 11, cy + 20), (cx, cy + 14), (cx - 11, cy + 20), (cx - 15, cy + 2)], fill=(200, 210, 235))
        circle(d, (cx - 5, cy - 2), 2.5, fill=(60, 50, 90))
        circle(d, (cx + 5, cy - 2), 2.5, fill=(60, 50, 90))
    elif kind == 2:  # Stingy Jack: an ember lantern
        rect(d, (cx - 9, cy - 12, cx + 9, cy + 14), fill=(70, 60, 50), radius=3)
        rect(d, (cx - 6, cy - 8, cx + 6, cy + 10), fill=AMBER, radius=2)
        line(d, [(cx - 6, cy - 12), (cx, cy - 20), (cx + 6, cy - 12)], (110, 100, 90), 2)
    else:            # Baba Yaga: a crooked broom
        line(d, [(cx - 12, cy + 18), (cx + 10, cy - 18)], WOOD, 3)
        poly(d, [(cx - 12, cy + 18), (cx - 22, cy + 14), (cx - 16, cy + 24), (cx - 6, cy + 26)], fill=(196, 160, 90))


def make_story():
    cases, story = read_cases(), read_story()
    W, CW, CH, PAD, TOP = 960, 466, 262, 10, 150
    rows = (len(ORDER) + 1) // 2
    H = TOP + rows * CH + (rows + 1) * PAD
    img, d = canvas(W, H, NIGHT_TEAL)
    text(d, (W / 2, 34), "Solve the haunting. Unmask the person.", 26, AMBER, anchor="mm")
    text(d, (W / 2, 66), "Hollow Creek's old folklore masks were brought out for the Halloween festival. Whoever wears one",
         13, PARCHMENT, weight="Regular", anchor="mm")
    text(d, (W / 2, 84), "can really haunt a house, and tonight a resident is using one to cover up something ordinary.",
         13, PARCHMENT, weight="Regular", anchor="mm")
    names = ["Headless Horseman", "Banshee", "Stingy Jack", "Baba Yaga"]
    for k in range(4):
        cx = W / 2 + (k - 1.5) * 210
        circle(d, (cx - 40, 118), 24, fill=TEAL)
        mask_icon(d, cx - 40, 118, k)
        text(d, (cx - 10, 118), names[k], 12, PARCHMENT, anchor="lm")
    for k, house in enumerate(ORDER):
        c, s = cases[house], story[house]
        lone = k == len(ORDER) - 1 and k % 2 == 0  # the fifth call sits in the middle
        x0 = PAD + (k % 2) * (CW + PAD) + 4 + ((CW + PAD) // 2 if lone else 0)
        y0 = TOP + PAD + (k // 2) * (CH + PAD)
        rect(d, (x0, y0, x0 + CW, y0 + CH), fill=PARCHMENT, outline=(200, 170, 120), width=2, radius=8)
        rect(d, (x0, y0, x0 + CW, y0 + 6), fill=AMBER, radius=3)
        text(d, (x0 + 14, y0 + 16), c["name"], 17, INK_DARK)
        text(d, (x0 + CW - 14, y0 + 19), HOUSE_NAME[house], 11, (120, 90, 70), weight="Regular", anchor="ra")
        y = y0 + 44
        for ln in wrap(s["premise"], 70)[:3]:
            text(d, (x0 + 14, y), ln, 12, (70, 52, 44), weight="Regular")
            y += 16
        y += 8
        text(d, (x0 + 14, y), "If they're under the mask, it's...", 11, (150, 90, 50))
        y += 18
        for (name, _job, _alibi), motive in zip(c["suspects"], s["motives"]):
            text(d, (x0 + 14, y), name, 11, INK_DARK)
            lines = wrap(motive, 60)[:2]
            for i, ln in enumerate(lines):
                text(d, (x0 + 140, y + i * 14), ln, 11, (80, 64, 56), weight="Regular")
            y += 14 * max(1, len(lines)) + 6
    save_png(finish(img), "story.png")


# ---------------------------------------------------------------------------
# anticipation.gif: same curves as PossessableObject, PossessableLight, PawnAnimator, TrapSite

ANTICIPATION = 0.35       # PossessableObject.Anticipation
FLICKER = 2.5             # PossessableLight.FlickerDuration
WOBBLE = 0.35             # TrapSite.Wobble
LOOP = 4.4
FPS = 20
PW, PH = 240, 270


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def chair_lean(t):
    if t < 0:
        return 0.0
    if t < ANTICIPATION:
        return -12 * smooth(0, 1, t / ANTICIPATION)
    u = t - ANTICIPATION - 0.8
    if u < 0 or u > 1.2:
        return 0.0
    return 7 * math.exp(-4 * u) * math.sin(u * 16)


def lamp_lean(t):
    if t < 0:
        return 0.0
    hold = ANTICIPATION + FLICKER
    if t < ANTICIPATION:
        return 16 * smooth(0, 1, (t / ANTICIPATION - 0.4) / 0.6)
    if t < hold:
        return 16.0
    return 16 * (1 - smooth(0, 1, (t - hold) / 0.9))


def rot(pts, pivot, deg):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    px, py = pivot
    return [(px + (x - px) * ca - (y - py) * sa, py + (x - px) * sa + (y - py) * ca) for x, y in pts]


def solver(d, x, y, jump=0.0, scared=False):
    y -= jump
    rect(d, (x - 11, y - 44, x + 11, y), fill=(80, 130, 200), radius=8)
    circle(d, (x, y - 54), 12, fill=(240, 205, 170))
    if scared:
        circle(d, (x - 4, y - 56), 3, fill=(255, 255, 255))
        circle(d, (x + 4, y - 56), 3, fill=(255, 255, 255))
        circle(d, (x, y - 48), 3, fill=(80, 40, 40))
        text(d, (x, y - 80), "!", 18, AMBER, anchor="mm")
    else:
        circle(d, (x - 4, y - 56), 1.6, fill=(40, 30, 30))
        circle(d, (x + 4, y - 56), 1.6, fill=(40, 30, 30))


def phase_bar(d, x0, y0, which):
    labels = ["anticipation", "action", "recovery"]
    w = (PW - 24) / 3
    for i, lab in enumerate(labels):
        on = i == which
        rect(d, (x0 + 12 + i * w + 2, y0, x0 + 12 + (i + 1) * w - 2, y0 + 18), fill=AMBER if on else (40, 60, 66), radius=9)
        text(d, (x0 + 12 + (i + 0.5) * w, y0 + 9), lab, 10, INK_DARK if on else (150, 170, 170), anchor="mm")


def panel_bg(d, x0, title):
    rect(d, (x0 + 4, 4, x0 + PW - 4, PH - 4), fill=NIGHT_TEAL, outline=(60, 90, 96), width=2, radius=10)
    rect(d, (x0 + 10, 186, x0 + PW - 10, 196), fill=WOOD)  # the floor
    text(d, (x0 + PW / 2, 22), title, 13, PARCHMENT, anchor="mm")


def draw_chair(d, x0, t):
    panel_bg(d, x0, "A chair leans back, then hops")
    start = 0.6
    s = t - start
    lean = chair_lean(s)
    hop = 0.0
    if 0 <= s - ANTICIPATION < 0.5:
        k = (s - ANTICIPATION) / 0.5
        hop = math.sin(k * math.pi) * 46
    shake = 2.5 * math.sin(t * 90) if 0 <= s - ANTICIPATION < 0.8 else 0.0
    squash = smooth(0, 1, s / ANTICIPATION) * 0.08 if 0 <= s < ANTICIPATION else (-0.06 if 0 <= s - ANTICIPATION < 0.15 else 0)
    cx, base = x0 + 90 + shake, 186 - hop
    hy = 1 - squash
    pivot = (cx - 22, base)  # it tips back onto its back legs
    seat = [(cx - 26, base - 34 * hy), (cx + 26, base - 34 * hy), (cx + 26, base - 42 * hy), (cx - 26, base - 42 * hy)]
    back = [(cx - 26, base - 42 * hy), (cx - 18, base - 42 * hy), (cx - 22, base - 96 * hy), (cx - 32, base - 94 * hy)]
    legs = [[(cx - 24, base), (cx - 19, base), (cx - 19, base - 34 * hy), (cx - 24, base - 34 * hy)],
            [(cx + 19, base), (cx + 24, base), (cx + 24, base - 34 * hy), (cx + 19, base - 34 * hy)]]
    glow = 0 <= s < ANTICIPATION + 0.8
    for part in legs + [seat, back]:
        poly(d, rot(part, pivot, lean), fill=(170, 110, 160) if glow else (150, 96, 60))
    if glow:
        circle(d, (cx, base - 60), 6 + 3 * math.sin(t * 12), fill=VIOLET + (90,))
    scared = 0 <= s - ANTICIPATION < 1.2
    solver(d, x0 + 190, 186, jump=14 * math.sin(min(1, max(0, (s - ANTICIPATION) / 0.3)) * math.pi) if scared else 0, scared=scared)
    phase_bar(d, x0, 212, 0 if 0 <= s < ANTICIPATION else 1 if 0 <= s - ANTICIPATION < 0.8 else 2 if 0 <= s - ANTICIPATION - 0.8 < 1.2 else -1)


def draw_lamp(d, x0, t):
    panel_bg(d, x0, "A lamp pauses, then turns to look")
    start = 0.4
    s = t - start
    lean = lamp_lean(s)
    flicker = ANTICIPATION <= s < ANTICIPATION + FLICKER
    lit = not flicker or (int(t * 13) * 7919 % 10) > 4
    cx, base = x0 + 80, 186
    pivot = (cx, base)
    pole = [(cx - 3, base), (cx + 3, base), (cx + 3, base - 110), (cx - 3, base - 110)]
    shade = [(cx - 26, base - 104), (cx + 26, base - 104), (cx + 16, base - 140), (cx - 16, base - 140)]
    if lit:
        bulb = rot([(cx, base - 108)], pivot, lean)[0]
        circle(d, bulb, 46, fill=AMBER + (60,))
        circle(d, bulb, 26, fill=AMBER + (90,))
    rect(d, (cx - 20, base - 6, cx + 20, base), fill=(70, 60, 50), radius=3)
    poly(d, rot(pole, pivot, lean), fill=(90, 80, 70))
    poly(d, rot(shade, pivot, lean), fill=(240, 200, 140) if lit else (120, 100, 80))
    eye = rot([(cx + 8, base - 124)], pivot, lean)[0]
    if 0 <= s < ANTICIPATION + FLICKER:
        circle(d, eye, 3, fill=VIOLET)
    scared = flicker
    solver(d, x0 + 190, 186, jump=0, scared=scared)
    phase = 0 if 0 <= s < ANTICIPATION else 1 if flicker else 2 if 0 <= s - ANTICIPATION - FLICKER < 0.9 else -1
    phase_bar(d, x0, 212, phase)


def draw_suspect(d, x0, t):
    panel_bg(d, x0, "A suspect swallows, then answers")
    start, pause = 0.5, 1.0
    h = t - start
    cx, base = x0 + 80, 186
    settle, gulp = 0.0, 0.0
    if 0 <= h < pause:
        k = h / pause
        settle = smooth(0, 1, min(1, k * 4)) * (1 - smooth(0.8, 1, k))
        gulp = math.exp(-((k - 0.65) / 0.06) ** 2)
    dip = 3 * gulp
    rect(d, (cx - 18, base - 70 + dip, cx + 18, base), fill=(190, 90, 170), radius=10)
    hx, hy = cx - 6 * settle, base - 84 + dip + 6 * settle
    circle(d, (hx, hy), 15, fill=(240, 205, 170))
    ex = -3 - 3 * settle
    eyey = hy - 2 + 4 * settle
    circle(d, (hx + ex - 4, eyey), 2, fill=(40, 30, 30))
    circle(d, (hx + ex + 4, eyey), 2, fill=(40, 30, 30))
    if gulp > 0.3:
        circle(d, (hx + 2, hy + 18), 3, fill=(220, 180, 150))
    solver(d, x0 + 195, 186)
    if 0 <= h < pause:
        rect(d, (cx - 14, base - 128, cx + 30, base - 108), fill=PARCHMENT, radius=9)
        text(d, (cx + 8, base - 119), "." * (1 + int(h * 4) % 3), 14, INK_DARK, anchor="mm")
    elif 0 <= h - pause < 2.4:
        rect(d, (x0 + 18, 40, x0 + PW - 18, 92), fill=PARCHMENT, radius=8)
        text(d, (x0 + PW / 2, 56), "I saw someone by the shed", 11, INK_DARK, weight="Regular", anchor="mm")
        text(d, (x0 + PW / 2, 74), "after dark. With a torch!", 11, INK_DARK, weight="Regular", anchor="mm")
    text(d, (x0 + PW / 2, 252), "Everyone hesitates alike: nerves aren't proof", 10, SAGE, weight="Regular", anchor="mm")
    phase_bar(d, x0, 212, 0 if 0 <= h < pause else 1 if 0 <= h - pause < 2.4 else -1)


def draw_trap(d, x0, t):
    panel_bg(d, x0, "The trap wobbles, then snaps")
    start = 0.9
    w = t - start
    cx, base = x0 + PW / 2, 186
    # The Haunter drifts in from the right and is caught.
    gx = x0 + 200 - 80 * smooth(0, 1, (t - 0.1) / 0.8)
    caught = w >= WOBBLE
    angle, sy, sx = 0.0, 1.0, 1.0
    if 0 <= w < WOBBLE:
        k = w / WOBBLE
        angle = math.sin(w * (30 + 40 * k)) * 9 * k
        sy = 1 + 0.06 * k
    elif 0 <= w - WOBBLE < 0.25:
        snap = 1 - (w - WOBBLE) / 0.25
        sx, sy = 1 + 0.12 * snap, 1 - 0.2 * snap
    if caught:
        gx = cx
    ghost_y = base - 40 + 4 * math.sin(t * 5)
    circle(d, (gx, ghost_y - 20), 18, fill=(200, 215, 240))
    rect(d, (gx - 18, ghost_y - 20, gx + 18, ghost_y + 14), fill=(200, 215, 240))
    circle(d, (gx - 6, ghost_y - 22), 3, fill=(60, 50, 90))
    circle(d, (gx + 6, ghost_y - 22), 3, fill=(60, 50, 90))
    # The cage hangs from a hook and drops when it snaps.
    drop = 0 if w < WOBBLE else min(1, (w - WOBBLE) / 0.12)
    top = 46 + drop * 70
    hw, hh = 42 * sx, 70 * sy
    pivot = (cx, top)
    if drop < 1:
        line(d, [(cx, 30), (cx, top)], (110, 100, 90), 2)
    bars = []
    for i in range(6):
        bx = cx - hw + i * (2 * hw / 5)
        bars.append([(bx - 1.5, top), (bx + 1.5, top), (bx + 1.5, top + hh), (bx - 1.5, top + hh)])
    for b in bars:
        poly(d, rot(b, pivot, angle), fill=AMBER)
    poly(d, rot([(cx - hw - 4, top - 4), (cx + hw + 4, top - 4), (cx + hw + 4, top + 4), (cx - hw - 4, top + 4)], pivot, angle), fill=AMBER)
    if caught and w - WOBBLE < 1.5:
        text(d, (cx, 34), "Got you!", 14, AMBER, anchor="mm")
    phase_bar(d, x0, 212, 0 if 0 <= w < WOBBLE else 1 if 0 <= w - WOBBLE < 0.4 else 2 if 0 <= w - WOBBLE - 0.4 < 1.5 else -1)


def make_anticipation():
    frames = []
    for i in range(int(LOOP * FPS)):
        t = i / FPS
        img, d = canvas(PW * 4, PH, (14, 22, 28))
        draw_chair(d, 0, t)
        draw_lamp(d, PW, t)
        draw_suspect(d, 2 * PW, t)
        draw_trap(d, 3 * PW, t)
        frames.append(finish(img))
    save_gif(frames, "anticipation.gif", 1000 // FPS)
    # A still for places that don't animate: the moment of anticipation in every panel.
    still, d = canvas(PW * 4, PH, (14, 22, 28))
    draw_chair(d, 0, 0.6 + 0.3)
    draw_lamp(d, PW, 0.4 + 0.33)
    draw_suspect(d, 2 * PW, 0.5 + 0.66)
    draw_trap(d, 3 * PW, 0.9 + 0.3)
    save_png(finish(still), "anticipation.png")


# ---------------------------------------------------------------------------
# suspect-board.png: an example board mid-case at Pemberton Cottage (mirrors GameHUD.DrawBoard)

def make_board():
    cases = read_cases()
    c = cases["PembertonCottage"]
    names = [n for n, _j, _a in c["suspects"]]
    W, H = 960, 480
    img, d = canvas(W, H, NIGHT_TEAL)
    rect(d, (16, 16, W - 16, H - 16), fill=PARCHMENT, outline=(200, 170, 120), width=2, radius=10)
    text(d, (36, 34), "SUSPECT BOARD", 20, INK_DARK)
    text(d, (W - 36, 38), c["name"] + "  ·  10:40 PM, dawn at 6:00 AM", 12, (120, 90, 70), weight="Regular", anchor="ra")
    # suspects row
    tags = ["", "YOUR HUNCH", "CLEARED", ""]
    for i, n in enumerate(names):
        x = 36 + i * 224
        rect(d, (x, 68, x + 212, 150), fill=(250, 240, 220), outline=(210, 185, 140), radius=8)
        circle(d, (x + 28, 100), 18, fill=[(110, 150, 70), (190, 90, 170), (90, 110, 160), (220, 160, 90)][i])
        text(d, (x + 54, 86), n, 13, INK_DARK)
        text(d, (x + 54, 104), c["suspects"][i][1], 11, (120, 90, 70), weight="Regular")
        if tags[i]:
            rect(d, (x + 54, 122, x + 54 + len(tags[i]) * 7.5 + 14, 140), fill=AMBER if tags[i] == "YOUR HUNCH" else (190, 180, 170), radius=8)
            text(d, (x + 61, 131), tags[i], 10, INK_DARK, anchor="lm")
        if i == 2:
            line(d, [(x + 50, 95), (x + 200, 95)], (150, 60, 50), 2)
    sections = [
        ("Evidence: what the club found", (70, 110, 70), [
            "[9:15 PM, Kitchen]  Spare key: the spare key from under the flowerpot, left on the rug  (" + c["traits"][4] + ")",
            "[10:05 PM, Pantry]  Gold locket: a gold locket with a tiny photo of the cottage inside  (" + c["traits"][6] + ")",
        ]),
        ("Testimony: what people said", (90, 90, 150), [
            "[9:40 PM]  " + names[3] + " (gossip): \"I saw " + names[1] + " by the garden shed after dark. With a torch!\"",
            "[10:20 PM]  " + names[0] + " (saw the Haunter up close): \"It brushed my sleeve. Afterwards I found " + c["traits"][6].lower() + " on my coat!\"",
        ]),
        ("Deductions: what follows", (170, 90, 40), [
            "Every clue so far fits " + names[1] + " and nobody else (unless one was planted).",
            names[1] + "'s alibi fell apart: they weren't where they said.",
        ]),
    ]
    y = 172
    for title, col, rows in sections:
        rect(d, (36, y, 42, y + 22), fill=col)
        text(d, (52, y + 2), title, 15, INK_DARK)
        y += 30
        for r in rows:
            for k, ln in enumerate(wrap(r, 118)[:2]):
                text(d, (52 + (14 if k else 0), y), ln, 12, (70, 52, 44), weight="Regular")
                y += 17
            y += 6
        y += 14
    text(d, (W / 2, H - 40), "Seen, said and proven stay apart, each with a time and a source. Hunches are yours alone.", 12, (120, 90, 70), anchor="mm")
    save_png(finish(img), "suspect-board.png")


# ---------------------------------------------------------------------------
# case-book.png: the keepsake shelf at HQ (rendered from HollowCreek.json) and the case book

def make_case_book():
    import json
    import numpy as np
    from PIL import Image
    import render3d as r3
    town = json.load(open(os.path.join(r3.ROOT, "Assets", "Unmasked", "Resources", "HollowCreek.json")))
    L = dict(town)
    extra = []
    looks = {  # mirrors TownBuilder.BuildKeepsake
        "PembertonCottage": [("cyl", (0, 0.16, 0), (0.17, 0.24, 0.17), (1.0, 0.68, 0.3), "glass"),
                             ("cyl", (0, 0.02, 0), (0.22, 0.04, 0.22), (0.78, 0.6, 0.25), "solid"),
                             ("cyl", (0, 0.3, 0), (0.2, 0.06, 0.2), (0.78, 0.6, 0.25), "solid")],
        "HollowCreekFarm": [("box", (0, 0.2, 0.05), (0.26, 0.26, 0.02), (0.2, 0.35, 0.8), "solid"),
                            ("box", (-0.05, 0.05, 0.06), (0.05, 0.16, 0.01), (0.2, 0.35, 0.8), "solid"),
                            ("box", (0.05, 0.05, 0.06), (0.05, 0.16, 0.01), (0.2, 0.35, 0.8), "solid")],
        "WillowLaneVictorian": [("box", (0, 0.13, 0.05), (0.18, 0.26, 0.01), (0.78, 0.68, 0.86), "solid")],
        "BlackwoodManor": [("box", (0, 0.12, 0.05), (0.22, 0.24, 0.02), (0.35, 0.2, 0.1), "solid"),
                           ("box", (0, 0.12, 0.035), (0.17, 0.19, 0.01), (0.92, 0.86, 0.7), "solid")],
        "HistoricalSociety": [("box", (0, 0.05, 0.05), (0.05, 0.1, 0.05), (0.85, 0.66, 0.3), "solid"),
                              ("box", (0, 0.13, 0.04), (0.24, 0.12, 0.015), (0.85, 0.66, 0.3), "solid"),
                              ("box", (0, 0.13, 0.03), (0.18, 0.03, 0.016), (0.15, 0.1, 0.08), "solid")],
    }
    for k in town["hq"]["keepsakes"]:
        x, y, z = k["p"]
        for t, o, sz, c, m in looks[k["house"]]:
            extra.append({"n": "k", "t": t, "p": [x + o[0], y + o[1], z + o[2]], "s": list(sz), "r": [0, 0, 0],
                          "c": list(c), "m": m, "l": 0, "g": "decor"})
    L["boxes"] = town["boxes"] + extra
    VW, VH = 560, 420
    cam = r3.Camera((-23.0, 2.1, -70.2), (-23.0, 1.25, -66.4), 46, VW, VH)
    shelf = r3.render(L, cam, r3.layout_mesh(L), fog_density=0.0, ambient=(0.3, 0.26, 0.34))

    W, H = 960, max(460, 96 + 86 * len(ORDER) + 20)
    img, d = canvas(W, H, NIGHT_TEAL)
    img.paste(shelf.resize((VW * SS, VH * SS)), (20 * SS, 20 * SS))
    text(d, (30, 30), "The keepsake shelf at HQ", 13, PARCHMENT)
    x0 = 600
    rect(d, (x0, 20, W - 20, H - 20), fill=PARCHMENT, outline=(200, 170, 120), width=2, radius=8)
    text(d, (x0 + 18, 38), "Case book", 20, INK_DARK)
    text(d, (x0 + 18, 66), "Saved on the host. Solved cases stay solved.", 11, (120, 90, 70), weight="Regular")
    cases, story = read_cases(), read_story()
    y = 96
    for i, house in enumerate(ORDER):
        solved = True
        rect(d, (x0 + 14, y, W - 34, y + 76), fill=(250, 240, 220), outline=(210, 185, 140), radius=6)
        text(d, (x0 + 26, y + 10), cases[house]["name"], 13, INK_DARK)
        text(d, (x0 + 26, y + 28), HOUSE_NAME[house] + ("  ·  the club's first case" if i == 0 else "  ·  the fifth call" if house == "HistoricalSociety" else ""), 10, (120, 90, 70), weight="Regular")
        for k, ln in enumerate(wrap(story[house]["recovered"], 52)[:2]):
            text(d, (x0 + 26, y + 44 + k * 13), ln, 10, (70, 52, 44), weight="Regular")
        if solved:
            rect(d, (W - 104, y + 8, W - 42, y + 26), fill=(170, 90, 40), radius=4)
            text(d, (W - 73, y + 17), "SOLVED", 10, PARCHMENT, anchor="mm")
        y += 86
    save_png(finish(img), "case-book.png")


if __name__ == "__main__":
    make_story()
    make_board()
    make_case_book()
    make_anticipation()
