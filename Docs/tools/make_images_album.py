#!/usr/bin/env python3
"""
Picture for round 37's club camera (snapshots.png): a snapshot developing on its instant-photo
card in the corner of the screen, and the Club Book's Snapshots album with ten of its twelve frames
filled. The landmark photos are real renders of HollowCreek.json from where a player might stand;
the rest are crops of this round's other pictures. A mockup, not an engine capture.

    python3 Docs/tools/make_images_album.py
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import OUT, font, save_png  # noqa: E402

BG = (22, 18, 14)
INK = (243, 234, 219)
MUTED = (205, 191, 171)
FAINT = (162, 147, 127)
RAISED = (36, 29, 23)
CREAM = (245, 237, 219)
TW, TH = 320, 180


def landmark_photos(merged, mesh, town, base_cache={}):
    out = {}
    for i, l in enumerate(town["landmarks"]):
        cx, cz = (l["min"][0] + l["max"][0]) / 2, (l["min"][1] + l["max"][1]) / 2
        a = math.radians(200 + i * 37)
        cam = r3.Camera((cx + math.sin(a) * 22, 3.2, cz + math.cos(a) * 22), (cx, 1.2, cz), 55, TW, TH)
        pic = r3.render(merged, cam, mesh, ss=1, fog_density=0.006, **r3.STORYBOOK)
        out["place:" + l["n"]] = r3.story_grade(pic)
    return out


def crop(name, box):
    im = Image.open(os.path.join(OUT, name)).convert("RGB").crop(box)
    return im.resize((TW, TH), Image.LANCZOS)


def polaroid(photo, caption, w=300, tilt=-3):
    h = int(w * TH / TW)
    card = Image.new("RGBA", (w + 24, h + 64), CREAM + (255,))
    card.paste(photo.resize((w, h), Image.LANCZOS), (12, 12))
    ImageDraw.Draw(card).text((12, h + 22), caption, font=font(15, "Bold"), fill=(29, 18, 13))
    return card.rotate(-tilt, expand=True, resample=Image.BICUBIC)


def make_album():
    merged, town_mesh, _ = r3.load_town()
    town = json.load(open(r3.TOWN_PATH))
    mesh = r3.layout_mesh(merged)
    photos = landmark_photos(merged, mesh, town)
    photos["wisp"] = crop("wisp.png", (300, 200, 1220, 650))
    photos["hooks"] = crop("hook-board.png", (1112, 92, 1632, 472))
    photos["porch"] = crop("carving.png", (300, 880, 1000, 1090))
    del photos["place:Hayride Field"]  # left empty, to show a frame still to fill
    sights = [("place:" + l["n"], l["n"], "somewhere in " + l["district"]) for l in town["landmarks"]]
    sights += [("neighbour", "A neighbour", "anyone you know in town, up close"), ("wisp", "A will-o'-the-wisp", "a light over the creek"),
               ("hooks", "The Hook Board", "outside the Historical Society"), ("porch", "Your porch", "carve a jack-o'-lantern first")]

    W, H = 1640, 1050
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((32, 22), "The club camera", font=font(34, "Black"), fill=INK)
    d.text((32, 62), "Press P for a snapshot: a flash, a click, and an instant photo develops in the corner. Get one of twelve sights in the middle and it goes in the album.",
           font=font(15, "Medium"), fill=MUTED)

    # Left: the game view with a fresh snapshot sliding in.
    view = Image.open(os.path.join(OUT, "wisp.png")).convert("RGB").crop((24, 92, 1224, 652)).resize((760, 355), Image.LANCZOS)
    img.paste(view, (32, 110))
    shot = photos["place:Old Hollow Cemetery"]
    p = polaroid(shot, "Old Hollow Cemetery", 220)
    img.paste(p, (32 + 760 - p.width - 14, 110 + 355 - p.height - 10), p)
    d.text((32, 476), "1  A snapshot develops from white on its card, then slides away", font=font(16, "Bold"), fill=INK)
    d.text((32, 500), "Neighbours in the frame turn and smile first; suspects look startled, all alike.", font=font(14, "Medium"), fill=MUTED)

    # Right: the Snapshots tab.
    x0, y0 = 830, 110
    page = (x0, y0, W - 32, H - 84)
    d.rectangle(page, fill=RAISED)
    d.text((x0 + 24, y0 + 18), "Club Book", font=font(30, "Black"), fill=INK)
    tabs = ["Challenges", "Wardrobe", "Stories", "Lost lanterns", "Places", "Snapshots"]
    tx = x0 + 24
    for t in tabs:
        tw = d.textlength(t, font=font(13, "Bold")) + 22
        d.rectangle((tx, y0 + 64, tx + tw, y0 + 90), fill=(239, 108, 91) if t == "Snapshots" else (46, 38, 30))
        d.text((tx + 11, y0 + 70), t, font=font(13, "Bold"), fill=(29, 18, 13) if t == "Snapshots" else INK)
        tx += tw + 6
    cw, ch = 236, int(236 * TH / TW)
    for i, (sid, name, hint) in enumerate(sights):
        col, row = i % 3, i // 3
        cx, cy = x0 + 24 + col * (cw + 18), y0 + 110 + row * (ch + 50)
        d.rectangle((cx, cy, cx + cw, cy + ch), fill=CREAM)
        inner = (cx + 6, cy + 6, cx + cw - 6, cy + ch - 6)
        if sid in photos:
            img.paste(photos[sid].resize((inner[2] - inner[0], inner[3] - inner[1]), Image.LANCZOS), inner[:2])
            d.text((cx, cy + ch + 6), name, font=font(14, "Bold"), fill=INK)
        else:
            d.rectangle(inner, fill=(46, 38, 30))
            d.text(((inner[0] + inner[2]) / 2, (inner[1] + inner[3]) / 2), "?", font=font(30, "Black"), fill=FAINT, anchor="mm")
            d.text((cx, cy + ch + 6), name, font=font(14, "Bold"), fill=FAINT)
            d.text((cx, cy + ch + 24), hint, font=font(11, "Medium"), fill=FAINT)
    d.text((x0, H - 72), "2  The Snapshots tab: ten of twelve frames filled", font=font(16, "Bold"), fill=INK)
    d.text((W / 2, H - 20), "A mockup drawn by Docs/tools/render3d.py and PIL, not an engine capture",
           font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "snapshots.png")


if __name__ == "__main__":
    make_album()
