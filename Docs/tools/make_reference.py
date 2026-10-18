#!/usr/bin/env python3
"""
Reference renders of the game as it stands, for looking at outside GitHub: big stills of every
house (outside, and roof off) and a gameplay tour video stitched from the README animations with
title cards. Everything goes to "Reference renders/". These are drawn by the project's own software
renderer from the same level files Unity builds from; they are not captures from the Unity editor.

    python3 Docs/tools/make_reference.py            # stills, copies of README pictures, and the video
    python3 Docs/tools/make_reference.py video      # just the video (needs ffmpeg)
"""
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font  # noqa: E402
from make_images_town import CARD_VIEWS, LOTS, house_layout  # noqa: E402

ROOT = r3.ROOT
OUT = os.path.join(ROOT, "Reference renders")
IMAGES = os.path.join(ROOT, "Docs", "images")
W, H = 1280, 720
ORDER = ["PembertonCottage", "HollowCreekFarm", "WillowLaneVictorian", "BlackwoodManor", "HistoricalSociety"]
# Houses added after the numbered copies below start their stills at this number
START = {"HistoricalSociety": 24}
NOTE = "Render from the game's level files, not a Unity capture"


def caption(img, title, sub):
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, H - 64, W, H], fill=(10, 8, 20, 190))
    d.text((24, H - 54), title, font=font(26, "Black"), fill=(255, 196, 110))
    d.text((24, H - 22), sub, font=font(14, "Medium"), fill=(220, 214, 236))
    d.text((W - 16, 14), NOTE, font=font(12, "Medium"), fill=(255, 255, 255, 150), anchor="ra")
    return img


def make_stills():
    os.makedirs(OUT, exist_ok=True)
    n = 1
    town = r3.load_town()[1]
    for lid in ORDER:
        n = START.get(lid, n)
        lot, L, v = LOTS[lid], house_layout(lid), CARD_VIEWS[lid]
        cam = r3.Camera(v["out"][0], v["out"][1], 50, W, H)
        img = r3.render(L, cam, r3.layout_mesh(L), horizon=town)
        name = f"{n:02d}-{lid}-outside.png"
        caption(img, lot["name"], f"{lot['street']}: the house from the street").save(os.path.join(OUT, name))
        print(" ", name, flush=True)
        n += 1
        cam = r3.Camera(v["cut"][0], v["cut"][1], 45, W, H)
        mesh = r3.layout_mesh(L, roof=False, cut_level=v["cut_level"], cut_height=1.2)
        img = r3.render(L, cam, mesh, fog_density=0.004, ambient=(0.2, 0.17, 0.3))
        name = f"{n:02d}-{lid}-inside.png"
        caption(img, lot["name"] + ", roof off", "Rooms, furniture the Haunter can possess, clue spots and suspects").save(os.path.join(OUT, name))
        print(" ", name, flush=True)
        n += 1


# (gif in Docs/images, title, one line on what you're seeing)
TOUR = [
    ("hero.gif", "UNMASKED", "Hollow Creek on Halloween night. Solve the haunting. Unmask the person."),
    ("van-drive.gif", "1. Take the call", "The club drives the van from HQ across town to tonight's house."),
    ("manor-walkthrough.gif", "2. Explore the house", "Flashlights on: rooms, possessable furniture, clue spots."),
    ("match-3d.gif", "3. A whole match", "Solvers hunt clues and interview suspects while the Haunter scares them."),
    ("fear-meter.gif", "4. Scares", "Every scare fills a Solver's fear meter; too much and they flee for a moment."),
    ("anticipation.gif", "5. Anticipation", "A beat of warning before every scare, and a moment to recover after."),
    ("unmask.gif", "6. Unmask the person", "Trap the Haunter, pull off the mask, learn why they did it."),
    ("villains-turntable.gif", "The masks", "The Headless Horseman, the Banshee, Stingy Jack and Baba Yaga."),
    ("beyond-town.gif", "Beyond the edge of town", "Hills, far-off lights and landmarks all the way round Hollow Creek."),
    ("face-life.gif", "Faces that live", "Everyone blinks, glances at you, and talks when they answer."),
]

# README pictures copied in as they are: (file in Docs/images, name in Reference renders)
COPIES = [
    ("town-map.png", "09-town-map.png"), ("story.png", "10-story.png"), ("suspect-board.png", "11-suspect-board.png"),
    ("case-files.png", "12-case-files.png"), ("suspects-by-house.png", "13-suspects-by-house.png"),
    ("villains.png", "14-villains.png"), ("case-book.png", "15-case-book.png"), ("horizon.png", "16-horizon.png"),
    ("edge-of-town.png", "17-edge-of-town.png"), ("faces.png", "18-characters.png"), ("mask-keeper.png", "19-mask-keeper.png"),
    ("living-town.png", "20-living-town.png"), ("trick-or-treaters.png", "21-trick-or-treaters.png"),
    ("valley-train.png", "22-valley-train.png"), ("face-life.gif", "23-face-life.gif"),
    ("museum.png", "26-museum.png"), ("mask-gallery.png", "27-mask-gallery.png"),
    ("townsfolk.png", "28-townsfolk.png"), ("errands.png", "29-errands.png"),
    ("return-visits.png", "30-return-visits.png"),
    ("portraits.png", "31-portraits.png"), ("people-before-after.png", "32-people-before-after.png"),
    ("builds.png", "33-heights-and-builds.png"),
    ("street-remembers.png", "34-street-remembers.png"), ("lantern-watch.png", "35-lantern-watch.png"),
    ("silhouettes.png", "36-silhouettes.png"),
    ("rounds.gif", "37-every-round.gif"), ("cast-turntable.gif", "38-cast-turntable.gif"),
]


def copy_pictures():
    os.makedirs(OUT, exist_ok=True)
    for src, dst in COPIES:
        if os.path.exists(os.path.join(IMAGES, src)):
            shutil.copyfile(os.path.join(IMAGES, src), os.path.join(OUT, dst))
            print(" ", dst, flush=True)


def title_card(path, title, sub):
    img = Image.new("RGB", (W, H), (14, 22, 28))
    d = ImageDraw.Draw(img)
    d.text((W / 2, H / 2 - 30), title, font=font(56, "Black"), fill=(255, 176, 74), anchor="mm")
    d.text((W / 2, H / 2 + 34), sub, font=font(22, "Medium"), fill=(240, 226, 196), anchor="mm")
    d.text((W / 2, H - 30), NOTE, font=font(14, "Medium"), fill=(130, 150, 150), anchor="mm")
    img.save(path)


def make_video():
    if not shutil.which("ffmpeg"):
        print("  ffmpeg not found: skipping the video")
        return
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp()
    fit = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0e161c,fps=25,format=yuv420p,setsar=1"
    parts = []
    for i, (gif, title, sub) in enumerate(TOUR):
        src = os.path.join(IMAGES, gif)
        if not os.path.exists(src):
            continue
        card = os.path.join(tmp, f"card{i}.png")
        title_card(card, title, sub)
        a, b = os.path.join(tmp, f"{i}a.mp4"), os.path.join(tmp, f"{i}b.mp4")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-t", "2.5", "-i", card, "-vf", fit, b], check=True)
        # Play each animation through twice (at least 6 seconds).
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "1", "-i", src, "-t", "14", "-vf", fit, a], check=True)
        parts += [b, a]
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    out = os.path.join(OUT, "gameplay-tour.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c:v", "libx264", "-crf", "23", "-preset", "medium", "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp)
    print(f"  gameplay-tour.mp4: {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    what = sys.argv[1:] or ["stills", "copies", "video"]
    if "stills" in what:
        make_stills()
    if "copies" in what:
        copy_pictures()
    if "video" in what:
        make_video()
