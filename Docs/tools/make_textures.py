#!/usr/bin/env python3
"""
Surface detail for every house, street and yard: clapboard siding, roof shingles, brick, stone,
floorboards, grass, asphalt, gravel, wallpaper, bark, leaves and water.

Each surface is a small tileable greyscale pattern (mid-grey = no change) that the game's
ToonSpooky shader multiplies over a box's flat colour, mapped in world space so a 20 m wall and a
1 m wall get boards of the same size. render3d.py uses the same images for the README pictures.
layoutlib.surfaces() picks a surface for each box from its tag and colour ("sf" in the JSON).

Writes Assets/Unmasked/Textures/Surfaces/<name>.png and surfaces.json (tile size in metres and how
strong the pattern is).

    python3 Docs/tools/make_textures.py
"""
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Assets", "Unmasked", "Textures", "Surfaces")
N = 256

# name: (tile size in metres, strength 0..1, top-down projection swaps x and z)
SURFACES = {
    "siding": (1.6, 0.85, False),
    "shingle": (2.0, 0.95, False),
    "shingle_z": (2.0, 0.95, True),
    "brick": (1.0, 0.8, False),
    "stone": (2.4, 0.85, False),
    "planks": (2.0, 0.7, False),
    "planks_z": (2.0, 0.7, True),
    "grass": (3.0, 0.75, False),
    "road": (4.0, 0.6, False),
    "gravel": (2.0, 0.7, False),
    "plaster": (1.2, 0.35, False),
    "bark": (1.0, 0.8, False),
    "leaf": (1.5, 0.8, False),
    "water": (3.0, 0.6, False),
}


def noise(rng, scale, n=N):
    """Tileable smooth noise: random values low-pass filtered in frequency space, scaled to -1..1."""
    f = np.fft.fft2(rng.standard_normal((n, n)))
    ky, kx = np.meshgrid(np.fft.fftfreq(n), np.fft.fftfreq(n), indexing="ij")
    k = np.sqrt(kx ** 2 + ky ** 2) * n
    f *= np.exp(-(k / scale) ** 2)
    out = np.real(np.fft.ifft2(f))
    return out / (np.abs(out).max() + 1e-9)


def fbm(rng, scales=(4, 10, 28, 70), weights=(0.5, 0.28, 0.15, 0.07)):
    return sum(w * noise(rng, s) for s, w in zip(scales, weights))


def rows(n_rows):
    v = np.arange(N)[:, None].repeat(N, axis=1)
    h = N / n_rows
    return (v / h).astype(int), (v % h) / h  # row index, position inside the row (0 top, 1 bottom)


def siding(rng):
    idx, t = rows(8)
    img = 0.52 + 0.06 * (1 - t)                       # each board catches light at the top
    img = np.where(t > 0.86, 0.26, img)               # shadow line under the board above
    img = np.where(t < 0.06, 0.64, img)
    u = np.arange(N)[None, :].repeat(N, axis=0)
    for r in range(8):                                 # butt joints
        for x in rng.choice(N, 1):
            img[(idx == r) & (np.abs(u - x) < 1)] = 0.32
    grain = noise(rng, 60)
    streak = noise(np.random.default_rng(rng.integers(1e9)), 6)[:, :1].repeat(N, axis=1)
    return img + 0.035 * grain + 0.03 * streak


def shingle(rng):
    idx, t = rows(8)
    u = np.arange(N)[None, :].repeat(N, axis=0)
    tab_w = N / 8
    col = ((u + (idx % 2) * tab_w / 2) // tab_w).astype(int) % 8
    tone = rng.uniform(0.4, 0.62, (8, 8))
    img = tone[idx, col]
    img = img - 0.12 * t                               # tabs darken towards their lower edge
    edge = ((u + (idx % 2) * tab_w / 2) % tab_w)
    img = np.where(edge < 2, 0.2, img)
    img = np.where(t > 0.88, 0.16, img)                # shadow under the row above
    return img + 0.05 * noise(rng, 70)


def brick(rng):
    idx, t = rows(16)
    u = np.arange(N)[None, :].repeat(N, axis=0)
    bw = N / 4
    off = (idx % 2) * bw / 2
    col = ((u + off) // bw).astype(int) % 4
    tone = rng.uniform(0.38, 0.58, (16, 4))
    img = tone[idx, col] + 0.05 * noise(rng, 50)
    mortar = (t > 0.84) | (((u + off) % bw) < 2.5)
    return np.where(mortar, 0.74, img - 0.05 * t)


def stone(rng):
    img = np.zeros((N, N))
    y = 0
    heights = []
    while y < N:
        h = int(rng.integers(26, 42))
        if N - y - h < 26:
            h = N - y
        heights.append((y, h))
        y += h
    u = np.arange(N)
    for y0, h in heights:
        cuts = [0]
        while cuts[-1] < N:
            cuts.append(cuts[-1] + int(rng.integers(40, 92)))
        cuts[-1] = N
        shift = int(rng.integers(0, N))
        for a, b in zip(cuts, cuts[1:]):
            tone = rng.uniform(0.38, 0.6)
            cols = (u[a:b] + shift) % N
            block = np.full((h, len(cols)), tone)
            yy = np.arange(h)[:, None] / h
            xx = (np.arange(len(cols))[None, :] + 0.5) / len(cols)
            block += 0.08 * (0.5 - yy)                     # lit from above
            block = np.where((yy > 0.92) | (xx < 0.03) | (xx > 0.97), 0.22, block)
            img[y0:y0 + h][:, cols] = block
    return img + 0.06 * fbm(rng)


def planks(rng):
    idx, t = rows(12)
    u = np.arange(N)[None, :].repeat(N, axis=0)
    tone = rng.uniform(0.44, 0.58, 12)
    img = tone[idx]
    streak = np.stack([noise(np.random.default_rng(int(rng.integers(1e9))), 40)[0] for _ in range(12)])  # grain along each board
    img = img + 0.07 * streak[idx, (u * 3) % N]
    for r in range(12):
        for x in rng.choice(N, 2, replace=False):
            img[(idx == r) & (np.abs(u - x) < 1)] = 0.26
    return np.where(t > 0.9, 0.24, img)


def grass(rng):
    img = 0.5 + 0.12 * fbm(rng)
    speck = rng.random((N, N))
    img = np.where(speck > 0.985, img + 0.14, img)
    img = np.where(speck < 0.02, img - 0.14, img)
    return img


def road(rng):
    img = 0.5 + 0.06 * fbm(rng) + 0.06 * (rng.random((N, N)) - 0.5)
    for _ in range(5):                                   # cracks
        x, y = rng.uniform(0, N, 2)
        a = rng.uniform(0, 2 * np.pi)
        for _ in range(int(rng.integers(40, 120))):
            a += rng.normal(0, 0.35)
            x, y = (x + np.cos(a)) % N, (y + np.sin(a)) % N
            img[int(y), int(x)] = 0.25
    return img


def gravel(rng):
    img = 0.5 + 0.08 * fbm(rng)
    for _ in range(900):
        x, y = rng.integers(0, N, 2)
        r = int(rng.integers(1, 4))
        tone = rng.uniform(0.32, 0.72)
        ys, xs = np.ogrid[-r:r + 1, -r:r + 1]
        mask = xs ** 2 + ys ** 2 <= r * r
        img[(y + ys) % N, (x + xs) % N] = np.where(mask, tone, img[(y + ys) % N, (x + xs) % N])
    return img


def plaster(rng):
    u = np.arange(N)[None, :].repeat(N, axis=0)
    v = np.arange(N)[:, None].repeat(N, axis=1)
    img = 0.5 + 0.05 * ((u // 32) % 2) + 0.03 * fbm(rng)        # wallpaper stripes
    dots = ((u % 32) - 16) ** 2 + ((v % 32) - 16) ** 2 < 9
    return np.where(dots, img + 0.07, img)


def bark(rng):
    streaks = noise(rng, 50)[0]
    img = 0.5 + 0.2 * streaks[None, :].repeat(N, axis=0) + 0.06 * noise(rng, 24)
    return img


def leaf(rng):
    img = 0.5 + 0.2 * noise(rng, 18) + 0.1 * noise(rng, 50)
    return np.where(rng.random((N, N)) > 0.97, img + 0.15, img)


def water(rng):
    n = noise(rng, 12)
    v = np.arange(N)[:, None].repeat(N, axis=1)
    return 0.5 + 0.12 * np.sin(v / N * 2 * np.pi * 10 + n * 4) + 0.05 * noise(rng, 40)


MAKERS = {"siding": siding, "shingle": shingle, "brick": brick, "stone": stone, "planks": planks, "grass": grass,
          "road": road, "gravel": gravel, "plaster": plaster, "bark": bark, "leaf": leaf, "water": water}


def pattern(name):
    """The pattern as a float array (mean about 0.5), shared with render3d.py."""
    base = name[:-2] if name.endswith("_z") else name
    rng = np.random.default_rng(sum(map(ord, base)) * 7919)
    img = MAKERS[base](rng)
    img = img - img.mean() + 0.5
    return np.clip(img, 0.05, 0.95)


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    for name, (tile, strength, swap) in SURFACES.items():
        if name.endswith("_z"):
            meta[name] = {"texture": name[:-2], "tile": tile, "strength": strength, "swapTop": swap}
            continue
        img = pattern(name)
        Image.fromarray((img * 255).astype(np.uint8), "L").convert("RGB").save(os.path.join(OUT, f"{name}.png"))
        meta[name] = {"texture": name, "tile": tile, "strength": strength, "swapTop": swap}
    with open(os.path.join(OUT, "surfaces.json"), "w") as f:
        json.dump({"surfaces": [dict(id=k, **v) for k, v in meta.items()]}, f, indent=1)
    print(f"Wrote {len(meta)} surfaces to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
