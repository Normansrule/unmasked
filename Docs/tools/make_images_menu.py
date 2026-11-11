#!/usr/bin/env python3
"""
Picture for round 40: the first menu over its painted night (UI/MenuBackdrop.cs).

  print-look.png      round 41: a club camera photo before and after Snapshots.PrintLook (same maths)
  menu-backdrop.png   the same sky, moon, drifting hills, manor window, fog, fireflies and grain the
                      game draws, ported from MenuBackdrop.cs, with the menu panel laid on top

Not captured in Unity: drawn here with the same numbers, so it is labelled "not an engine capture".

    python3 Docs/tools/make_images_menu.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_images import font, save_png  # noqa: E402

W, H = 1600, 900
T = 12.0  # a moment in the drift
INK = (243, 234, 219)
MUTED = (205, 191, 171)
ACCENT = (239, 108, 91)


def smooth(a, b, x):
    x = np.clip((x - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


def sky():
    v = 1 - np.linspace(0, 1, H)[:, None]  # 0 at the bottom of the screen
    low, mid, zen = np.array([0.45, 0.24, 0.2]), np.array([0.16, 0.1, 0.2]), np.array([0.06, 0.05, 0.11])
    a = smooth(0, 1, v / 0.45)[..., None]
    b = smooth(0, 1, (v - 0.45) / 0.55)[..., None]
    c = np.where(v[..., None] < 0.45, low + (mid - low) * a, mid + (zen - mid) * b)
    return np.broadcast_to(c, (H, W, 3)).copy()


def blend(img, mask, color, alpha=1.0):
    m = (mask * alpha)[..., None]
    img[:] = img * (1 - m) + np.array(color) * m


def glow_at(img, cx, cy, size, color, alpha):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (size / 2)
    a = np.clip(1 - d, 0, 1) ** 2
    blend(img, a, color, alpha)


def manor(u):
    x = (u - 0.70) * 1024
    if x < 0 or x > 84:
        return 0
    h = 0.70
    if 8 < x < 76:
        h = max(h, 0.80 - abs(x - 42) / 34 * 0.1)
    if 52 < x < 64:
        h = max(h, 0.92)
    if 50 < x < 66:
        h = max(h, 0.92 + (8 - abs(x - 58)) / 8 * 0.07)
    if 16 < x < 20:
        h = max(h, 0.86)
    return h


def trees(x, w=1024):
    best = 0
    for k in range(7):
        cx = (k * 149 + 60) % w
        dx = abs(x - cx)
        height = 0.78 + (k % 3) * 0.06
        if dx <= 1:
            best = max(best, height)
        elif dx < 11:
            best = max(best, height - 0.03 - dx * 0.026 - (0.02 if (dx + k) % 4 == 0 else 0))
    return best


def hill_top(i, x):
    u = x / 1024 * math.pi * 2
    top = 0.55 + 0.18 * math.sin(u * (2 + i) + i) + 0.09 * math.sin(u * (5 + i * 2) + 1.3 * i) + 0.04 * math.sin(u * 13 + i)
    if i == 1:
        top = max(top, manor(x / 1024))
    if i == 2:
        top = max(top, trees(x))
    return top


def main():
    img = sky()
    m = min(W, H) * 0.16
    mc = (W * 0.74, H * 0.24)
    breathe = 1 + math.sin(T * 0.6) * 0.04
    glow_at(img, *mc, m * 4.4 * breathe, (1, 0.85, 0.6), 0.22)
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt((xx - mc[0]) ** 2 + (yy - mc[1]) ** 2) / (m / 2)
    moon = np.clip((1 - d) * 40, 0, 1)
    blend(img, moon, (1, 0.95, 0.84))
    for cx, cy, r in ((0.3, -0.2, 0.22), (-0.35, 0.25, 0.16), (0.1, 0.45, 0.1)):
        dd = np.sqrt((xx - mc[0] - cx * m / 2) ** 2 + (yy - mc[1] - cy * m / 2) ** 2) / (r * m / 2)
        blend(img, np.clip(1 - dd * dd, 0, 1) * moon, (0.85, 0.8, 0.7), 0.35)

    tints = [(0.20, 0.14, 0.26), (0.12, 0.085, 0.15), (0.055, 0.04, 0.065)]
    speeds, heights = [0.0035, 0.007, 0.013], [0.34, 0.30, 0.24]
    span = W * 1.4
    for i in range(3):
        h = H * heights[i]
        y0 = H - h - (2 - i) * H * 0.07
        u0 = T * speeds[i]
        mask = np.zeros((H, W))
        for sx in range(W):
            tx = ((u0 + sx / span) % 1) * 1024
            top = hill_top(i, int(tx))
            ytop = y0 + h * (1 - top)
            mask[int(max(0, ytop)):, sx] = 1
        blend(img, mask, tints[i])
        if i == 1:
            wx = ((747 / 1024 - u0) % 1) * span
            wy, ws = y0 + h * 0.35, max(3, h / 128 * 6)
            if wx < W:
                glow_at(img, wx, wy, ws * 6, (1, 0.7, 0.35), 0.35)
                img[int(wy - ws / 2):int(wy + ws / 2), int(wx - ws / 2):int(wx + ws / 2)] = (1, 0.8, 0.45)
            fogv = np.clip(np.sin((yy - (y0 + h * 0.35)) / (h * 0.5) * math.pi), 0, 1)
            fogv[(yy < y0 + h * 0.35) | (yy > y0 + h * 0.85)] = 0
            fogu = 0.6 + 0.4 * np.sin(xx / W * 1.6 * 2 * math.pi * 3) * np.sin(xx / W * 1.6 * 2 * math.pi * 7 + 1)
            blend(img, fogv * np.clip(fogu, 0, 1), (0.75, 0.7, 0.85), 0.16)

    for i in range(22):
        a = i * 2.39996
        px = ((0.07 + i * 0.0457 + math.sin(T * 0.13 + a) * 0.03) % 1) * W
        py = H * (0.62 + 0.3 * ((i * 0.618) % 1)) + math.sin(T * (0.4 + i % 5 * 0.07) + a) * 14
        on = min(1, max(0, 0.35 + math.sin(T * (1.1 + i % 3 * 0.4) + a)))
        s = 14 + i % 4 * 3
        glow_at(img, px, py, s, (1, 0.82, 0.42), 0.55 * on)
        img[int(py) - 1:int(py) + 1, int(px) - 1:int(px) + 1] = img[int(py) - 1:int(py) + 1, int(px) - 1:int(px) + 1] * (1 - 0.9 * on) + np.array((1, 0.93, 0.7)) * 0.9 * on

    rng = np.random.default_rng(40)
    g = rng.random((H, W))[..., None]
    img = img * 0.94 + g * 0.06
    dx, dy = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
    vig = np.clip((dx * dx + dy * dy - 0.35) * 0.55, 0, 1)[..., None]
    img = img * (1 - vig)

    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(out, "RGBA")
    # the menu panel, as DrawConnectMenu lays it out
    x, y, pw, ph = 32, 32, 420, 520
    d.rounded_rectangle([x + 4, y + 6, x + pw + 4, y + ph + 6], 6, fill=(0, 0, 0, 90))
    d.rounded_rectangle([x, y, x + pw, y + ph], 6, fill=(22, 18, 14, 242))
    d.text((x + 24, y + 22), "Unmasked", font=font(40, "Black"), fill=INK)
    d.text((x + 24, y + 78), "A Halloween mystery. Play on your own or host for", font=font(15, "Regular"), fill=MUTED)
    d.text((x + 24, y + 98), "friends, or join a friend's game.", font=font(15, "Regular"), fill=MUTED)
    d.rounded_rectangle([x + 24, y + 136, x + pw - 24, y + 178], 5, fill=ACCENT)
    d.text((x + pw / 2, y + 157), "Play (host a game)", font=font(17), fill=(29, 18, 13), anchor="mm")
    d.rounded_rectangle([x + 24, y + 188, x + pw - 24, y + 222], 5, fill=(36, 29, 23))
    d.text((x + pw / 2, y + 205), "Club Book: challenges and wardrobe (120 candy)", font=font(14), fill=INK, anchor="mm")
    d.text((x + 24, y + 248), "Games on your Wi-Fi", font=font(20), fill=INK)
    d.text((x + 24, y + 278), "Looking… When a friend on this Wi-Fi hosts, their", font=font(14, "Regular"), fill=MUTED)
    d.text((x + 24, y + 296), "game shows up here.", font=font(14, "Regular"), fill=MUTED)
    d.text((x + 24, y + 336), "Or type an address", font=font(13, "Regular"), fill=MUTED)
    d.rounded_rectangle([x + 24, y + 356, x + pw - 110, y + 388], 4, fill=(36, 29, 23))
    d.text((x + 36, y + 372), "192.168.1.20", font=font(14, "Regular"), fill=INK, anchor="lm")
    d.rounded_rectangle([x + pw - 100, y + 356, x + pw - 24, y + 388], 4, fill=(36, 29, 23))
    d.text((x + pw - 88, y + 372), "7777", font=font(14, "Regular"), fill=INK, anchor="lm")
    for k, label in enumerate(("Join", "Run a dedicated server")):
        yy0 = y + 400 + k * 44
        d.rounded_rectangle([x + 24, yy0, x + pw - 24, yy0 + 34], 5, fill=(36, 29, 23))
        d.text((x + pw / 2, yy0 + 17), label, font=font(14), fill=INK, anchor="mm")
    d.text((W - 18, H - 16), "Drawn from UI/MenuBackdrop.cs, not an engine capture", font=font(13, "Regular"), fill=(170, 160, 150), anchor="rs")
    save_png(out, "menu-backdrop.png")


BAYER = np.array([0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]).reshape(4, 4)


def print_look(rgb):
    """Snapshots.PrintLook ported: 8 ink steps with 4x4 ordered dither, ink-to-paper, soft corners."""
    h, w, _ = rgb.shape
    yy, xx = np.mgrid[0:h, 0:w]
    d = ((BAYER[yy % 4, xx % 4] + 0.5) / 16 - 0.5)[..., None]
    q = np.round(rgb * 8 + d) / 8
    ink, paper = np.array([0.06, 0.045, 0.06]), np.array([1, 0.96, 0.88])
    c = ink + (paper - ink) * q
    dx, dy = (xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)
    fall = 1 - np.clip((dx * dx + dy * dy - 0.55) * 0.35, 0, 1)
    return np.clip(c * fall[..., None], 0, 1)


def make_print():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    src = Image.open(os.path.join(root, "Reference renders", "21-trick-or-treaters.png")).convert("RGB")
    w, h = src.size
    tw = min(w, round(h * 16 / 9)); th = round(tw * 9 / 16)
    shot = src.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th)).resize((320, 180), Image.BILINEAR)
    before = np.asarray(shot) / 255.0
    after = print_look(before)
    out = Image.new("RGB", (2 * 640 + 3 * 24, 360 + 120), (22, 18, 14))
    d = ImageDraw.Draw(out)
    d.text((24, 20), "Club camera photos, printed", font=font(28), fill=INK)
    for i, (img, cap) in enumerate(((before, "Before: the raw screen"), (after, "After: ink steps, dot pattern, cream paper"))):
        im = Image.fromarray((img * 255).astype(np.uint8)).resize((640, 360), Image.NEAREST)
        x = 24 + i * (640 + 24)
        out.paste(im, (x, 66))
        d.text((x, 66 + 366), cap, font=font(15, "Regular"), fill=MUTED)
    d.text((out.width - 18, out.height - 14), "Drawn from Snapshots.PrintLook over a Reference render, not an engine capture", font=font(12, "Regular"), fill=(160, 150, 140), anchor="rs")
    save_png(out, "print-look.png")


if __name__ == "__main__":
    which = set(sys.argv[1:])
    if not which or "menu" in which:
        main()
    if not which or "print" in which:
        make_print()
