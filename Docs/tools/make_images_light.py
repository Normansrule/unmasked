#!/usr/bin/env python3
"""
Pictures for round 33's storybook lighting pass (lighting-pass.png): one view down Chapel Lane drawn
four ways, with the same numbers the game uses (Editor/SpookyLook.cs, Spooky/StoryLight.cs and the
ToonSpooky shader's _Story* globals):

  1. the old look (violet everywhere: ambient, fog, rims)
  2. the storybook night: teal shadows and mist, amber windows and lamps
  3. a haunting: violet creeps into the rims, the mist and the grade
  4. the unmasking: the mist lifts and everything goes gold

Drawn by Docs/tools/render3d.py, not captured in Unity.

    python3 Docs/tools/make_images_light.py
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render3d as r3  # noqa: E402
from make_images import font, save_png  # noqa: E402

BG = (22, 18, 14)
INK = (243, 234, 219)
MUTED = (205, 191, 171)
FAINT = (162, 147, 127)


def make_lighting_pass():
    merged, town, _ = r3.load_town()
    mesh = r3.layout_mesh(merged)
    PW, PH = 720, 405
    cam = r3.Camera((-26, 2.4, 111.5), (-120, 2.2, 104), 58, PW, PH)
    base = r3.rasterize(r3.big_camera(cam), mesh)
    sb = r3.STORYBOOK
    panels = [
        ("Before", "Round 32's lighting: violet ambient, fog and rims everywhere",
         r3.render(merged, cam, mesh, base=base, fog_density=0.012), None),
        ("The storybook night", "Teal shadows and creek mist; warm windows and porch lamps",
         r3.render(merged, cam, mesh, base=base, fog_density=0.006, **sb), dict(haunt=0.0)),
        ("A haunting", "Violet only now: rims, mist and grade, as fear rises",
         r3.render(merged, cam, mesh, base=base, fog_density=0.006, haunt=0.8, **sb), dict(haunt=0.8)),
        ("The unmasking", "The mist lifts and the whole street goes gold",
         r3.render(merged, cam, mesh, base=base, fog_density=0.004, light_boost=1.25,
                   **{**sb, "mist": sb["mist"][:4] + (sb["mist"][4] * 0.4,)}), dict(gold=0.9)),
    ]
    gap, top = 24, 92
    W = 2 * PW + 3 * gap
    H = top + 2 * (PH + 64) + 40
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((gap, 22), "The storybook lighting pass", font=font(34, "Black"), fill=INK)
    d.text((gap, 62), "Amber is welcome, teal is the night, violet is a haunting and nothing else. One view down Chapel Lane, four moods.",
           font=font(15, "Medium"), fill=MUTED)
    for i, (title, sub, pic, grade) in enumerate(panels):
        if grade is not None:
            pic = r3.story_grade(pic, **grade)
        x = gap + (i % 2) * (PW + gap)
        y = top + (i // 2) * (PH + 64)
        img.paste(pic, (x, y))
        d.text((x, y + PH + 8), f"{i + 1}  {title}", font=font(18, "Bold"), fill=INK)
        d.text((x, y + PH + 34), sub, font=font(14, "Medium"), fill=MUTED)
    d.text((W / 2, H - 20), "Drawn by Docs/tools/render3d.py with the game's own lighting numbers, not an engine capture",
           font=font(12, "Medium"), fill=FAINT, anchor="mm")
    save_png(img, "lighting-pass.png")


if __name__ == "__main__":
    make_lighting_pass()
