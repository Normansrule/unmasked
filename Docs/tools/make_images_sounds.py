#!/usr/bin/env python3
"""
sounds.png for the README: every sound in the game as a spectrogram (time left to right, pitch
bottom to top), labelled with where it plays. Drawn from the same synthesis as make_sounds.py.

    python3 Docs/tools/make_images_sounds.py
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_sounds as ms  # noqa: E402
from make_images import font, save_png, INK, MUTED, ORANGE  # noqa: E402

GROUPS = [
    ("The night around you", ["wind", "crickets", "rain", "drone", "crow", "owl", "thunder", "heartbeat"]),
    ("Tonight's legends", ["banshee_wail", "hoofbeats", "pumpkin_burst", "wisp_chime", "hex", "ghost_moan"]),
    ("The house", ["rattle", "whoosh", "door_slam", "creak", "buzz", "power_down", "music_box"]),
    ("The mystery", ["eek", "clue_chime", "alibi_holds", "alibi_broken", "trap_sting", "unmask", "van_engine"]),
]


def spectrogram(x, w, h):
    n, hop = 512, max(1, len(x) // w)
    frames = [x[i:i + n] * np.hanning(n) for i in range(0, max(1, len(x) - n), hop)][:w]
    if not frames:
        frames = [np.pad(x, (0, n - len(x))) * np.hanning(n)]
    S = np.abs(np.fft.rfft(np.array(frames), axis=1)).T  # freq x time
    # log-frequency rows from 40 Hz to 10 kHz
    freqs = np.fft.rfftfreq(n, 1 / ms.SR)
    rows = np.geomspace(40, 10000, h)
    idx = np.clip(np.searchsorted(freqs, rows), 0, len(freqs) - 1)
    S = 20 * np.log10(S[idx] + 1e-6)
    S = np.clip((S - (S.max() - 60)) / 60, 0, 1)[::-1]
    img = Image.fromarray((S * 255).astype(np.uint8), "L").resize((w, h), Image.BILINEAR)
    a = np.asarray(img) / 255.0
    # night palette: black -> purple -> orange -> pale yellow
    stops = np.array([[14, 10, 24], [80, 30, 120], [230, 110, 40], [255, 230, 160]], float)
    pos = a * (len(stops) - 1)
    lo = np.floor(pos).astype(int).clip(0, len(stops) - 2)
    f = (pos - lo)[..., None]
    rgb = stops[lo] * (1 - f) + stops[lo + 1] * f
    return Image.fromarray(rgb.astype(np.uint8), "RGB")


def main():
    sounds = ms.render_all()
    CW, SH, COLS, PAD = 214, 64, 4, 10
    rows_needed = sum(-(-len(g) // COLS) for _, g in GROUPS)
    H = 50 + len(GROUPS) * 30 + rows_needed * (SH + 46) + PAD
    W = COLS * CW + (COLS + 1) * PAD
    sheet = Image.new("RGB", (W, H), (14, 10, 24))
    d = ImageDraw.Draw(sheet)
    d.text((W / 2, 24), "Every sound in the game, made from scratch", font=font(19), fill=ORANGE, anchor="mm")
    y = 50
    for title, names in GROUPS:
        d.text((PAD, y + 6), title, font=font(14), fill=(255, 200, 120))
        y += 30
        for k, name in enumerate(names):
            x0 = PAD + (k % COLS) * (CW + PAD)
            if k and k % COLS == 0:
                y += SH + 46
            loop = ms.SOUNDS[name][1]
            sheet.paste(spectrogram(sounds[name], CW, SH), (x0, y))
            d.rectangle([x0, y, x0 + CW - 1, y + SH - 1], outline=(70, 55, 95))
            d.text((x0, y + SH + 4), name.replace("_", " ") + ("  (loop)" if loop else f"  {len(sounds[name]) / ms.SR:.1f}s"),
                   font=font(12), fill=INK)
            d.text((x0, y + SH + 21), ms.SOUNDS[name][2][:34], font=font(10, "Medium"), fill=MUTED)
        y += SH + 46
    save_png(sheet, "sounds.png")


if __name__ == "__main__":
    main()
