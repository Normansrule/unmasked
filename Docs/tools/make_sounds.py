#!/usr/bin/env python3
"""
Every sound in the game, synthesized from scratch (no recordings, nothing to license):
the night ambience (wind, crickets, rain), the villains' signature sounds (the Banshee's wail,
the Horseman's hoofbeats, Stingy Jack's wisps, Baba Yaga's hex), possessed furniture, thunder,
the van's engine, suspects' yelps, clue chimes and the unmasking fanfare.

Writes Assets/Unmasked/Resources/Sounds/<name>.wav (22 kHz mono). The game loads them by name
(Scripts/Spooky/Sfx.cs). Loops are made seamless by filtering in the frequency domain, which
wraps around.

    python3 Docs/tools/make_sounds.py
"""
import json
import os
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "Assets", "Unmasked", "Resources", "Sounds")
SR = 22050
RNG = np.random.default_rng(1031)


def t_axis(sec):
    return np.arange(int(sec * SR)) / SR


def noise(sec):
    return RNG.standard_normal(int(sec * SR))


def band(x, lo=0.0, hi=None, soft=0.15):
    """Band-pass in the frequency domain (circular, so loops stay seamless)."""
    f = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    hi = hi or SR / 2
    w = 1 / (1 + np.exp(-(freqs - lo) / max(lo * soft, 1))) if lo > 0 else np.ones_like(freqs)
    w *= 1 / (1 + np.exp((freqs - hi) / max(hi * soft, 1)))
    return np.fft.irfft(f * w, len(x))


def pink(sec):
    f = np.fft.rfft(noise(sec))
    freqs = np.fft.rfftfreq(int(sec * SR), 1 / SR)
    f[1:] /= np.sqrt(freqs[1:])
    f[0] = 0
    return np.fft.irfft(f, int(sec * SR))


def env(n, attack=0.01, release=0.2, sec=None):
    """Linear attack, exponential-ish release over n samples."""
    t = np.arange(n) / SR
    total = n / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    r = np.clip((total - t) / max(release, 1e-4), 0, 1) ** 2
    return a * r


def decay(n, rate):
    return np.exp(-np.arange(n) / SR * rate)


def sweep(f0, f1, sec, curve=1.0):
    """Phase of a sine sweeping f0 -> f1."""
    t = t_axis(sec)
    u = (t / sec) ** curve
    freq = f0 + (f1 - f0) * u
    return 2 * np.pi * np.cumsum(freq) / SR


def saw(phase):
    return 2 * ((phase / (2 * np.pi)) % 1.0) - 1


def norm(x, peak=0.9):
    m = np.abs(x).max()
    return x / m * peak if m > 0 else x


def place(total_sec, events):
    """Mix (start_sec, signal) events into one buffer."""
    out = np.zeros(int(total_sec * SR))
    for start, sig in events:
        i = int(start * SR)
        j = min(len(out), i + len(sig))
        out[i:j] += sig[: j - i]
    return out


def bell(freq, sec, partials=((1, 1), (2.76, 0.4), (5.4, 0.2), (8.9, 0.08)), rate=3.0):
    t = t_axis(sec)
    x = sum(a * np.sin(2 * np.pi * freq * k * t) * decay(len(t), rate * (1 + k * 0.4)) for k, a in partials)
    return x * env(len(t), 0.003, 0.05)


# ---------------------------------------------------------------------------
# Ambience (loops)
# ---------------------------------------------------------------------------
def wind():
    sec = 12
    x = pink(sec)
    t = t_axis(sec)
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * t / sec * 2 + 1) * np.sin(2 * np.pi * t / sec * 3)
    low = band(x, 80, 700) * gust
    howl = band(noise(sec), 300, 520, 0.05) * (0.5 + 0.5 * np.sin(2 * np.pi * t / sec * 1)) * 0.6
    return norm(low + howl, 0.5)


def crickets():
    sec = 8
    out = np.zeros(int(sec * SR))
    for k in range(3):  # three crickets, each with its own rhythm and pitch
        f = 4300 + k * 350
        period = 0.9 + k * 0.23
        start = RNG.uniform(0, period)
        while start < sec - 0.2:
            for c in range(3):
                n = int(0.018 * SR)
                tt = np.arange(n) / SR
                chirp = np.sin(2 * np.pi * f * tt) * np.sin(np.pi * tt / tt[-1]) * (0.6 if k else 1)
                i = int((start + c * 0.04) * SR) % len(out)
                out[i:i + n] += chirp[: len(out) - i]
            start += period
    return norm(out, 0.22)


def rain():
    sec = 8
    hiss = band(noise(sec), 1500, 9000) * 0.5
    drops = np.zeros(int(sec * SR))
    for _ in range(900):
        i = RNG.integers(0, len(drops) - 200)
        drops[i:i + 200] += RNG.uniform(0.2, 1) * np.sin(2 * np.pi * RNG.uniform(2000, 5000) * np.arange(200) / SR) * decay(200, 300)
    return norm(hiss + band(drops, 800), 0.45)


def drone():
    """Blood moon: a low, uneasy hum."""
    sec = 10
    t = t_axis(sec)
    x = np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 58.3 * t) + 0.3 * np.sin(2 * np.pi * 82.5 * t)
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * t / sec * 2)
    return norm(x + 0.3 * band(pink(sec), 40, 200), 0.4)


def heartbeat():
    """One beat (lub-dub); the game repeats it faster as fear rises."""
    sec = 0.8

    def thump(f, s):
        tt = t_axis(s)
        return np.sin(2 * np.pi * f * tt * (1 - 0.3 * tt / s)) * decay(len(tt), 18) * env(len(tt), 0.005, 0.05)
    return norm(place(sec, [(0, thump(55, 0.25)), (0.22, 0.7 * thump(48, 0.25))]), 0.9)


def van_engine():
    """Idle loop; the game raises the pitch with speed. 1 s = whole number of cycles so it loops."""
    sec = 1.0
    t = t_axis(sec)
    f = 36.0
    x = 0.6 * saw(2 * np.pi * f * t) + 0.3 * saw(2 * np.pi * 2 * f * t) + 0.2 * np.sin(2 * np.pi * 3 * f * t)
    x *= 0.8 + 0.2 * np.sin(2 * np.pi * f / 2 * t) ** 2  # firing pulses
    x = band(x, 0, 900) + 0.15 * band(noise(sec), 100, 600)
    return norm(x, 0.6)


def music_box():
    """The Willow Lane nursery's music box: a slow, slightly detuned lullaby (loops)."""
    notes = [76, 79, 81, 79, 76, 74, 72, 74, 76, 76, 74, None, 72, 76, 79, 74]
    step = 0.42
    sec = step * len(notes)
    events = []
    for k, n in enumerate(notes):
        if n is None:
            continue
        f = 440 * 2 ** ((n - 69) / 12) * (1 + 0.004 * np.sin(k))
        events.append((k * step, bell(f, 1.2, rate=2.2)))
    x = place(sec + 1.2, events)
    tail = x[int(sec * SR):]
    x = x[: int(sec * SR)]
    x[: len(tail)] += tail  # wrap the last notes' ring into the start
    return norm(x, 0.5)


# ---------------------------------------------------------------------------
# One-shots
# ---------------------------------------------------------------------------
def thunder():
    sec = 4.5
    n = int(sec * SR)
    rumble = band(pink(sec), 20, 260) * (decay(n, 0.9) * (0.6 + 0.4 * np.abs(np.sin(np.linspace(0, 9, n)))))
    crack = band(noise(sec), 600, 6000) * decay(n, 14) * 0.8
    return norm((rumble + crack) * env(n, 0.02, 0.8), 0.95)


def crow():
    def caw(s):
        ph = sweep(620, 430, s, 0.6)
        x = saw(ph) * 0.6 + band(noise(s), 800, 2500) * 0.5
        x = band(x, 400, 3200)
        return x * env(len(x), 0.01, 0.12)
    return norm(place(1.3, [(0, caw(0.32)), (0.45, caw(0.3)), (0.88, 0.8 * caw(0.28))]), 0.8)


def owl():
    def hoo(s, f):
        tt = t_axis(s)
        x = np.sin(2 * np.pi * f * tt * (1 - 0.06 * tt / s)) + 0.1 * band(noise(s), 200, 900)
        return x * env(len(tt), 0.08, 0.25)
    return norm(place(1.8, [(0, hoo(0.35, 390)), (0.5, hoo(0.18, 400)), (0.75, hoo(0.6, 370))]), 0.6)


def rattle():
    sec = 0.9
    out = np.zeros(int(sec * SR))
    k = 0.0
    while k < sec - 0.05:
        click = band(noise(0.03), 900, 5000) * decay(int(0.03 * SR), 160)
        i = int(k * SR)
        out[i:i + len(click)] += click * RNG.uniform(0.4, 1)
        k += RNG.uniform(0.025, 0.07)
    return norm(out * env(len(out), 0.01, 0.2), 0.8)


def creak():
    sec = 1.4
    t = t_axis(sec)
    f = 170 + 90 * np.sin(2 * np.pi * 0.7 * t) + 25 * np.sin(2 * np.pi * 7 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    pulses = (np.sin(ph) > 0.92).astype(float)  # stick-slip: a train of little clicks
    x = band(pulses, 200, 2500)
    return norm(x * env(len(t), 0.05, 0.3), 0.7)


def door_slam():
    sec = 1.0
    n = int(sec * SR)
    tt = t_axis(sec)
    boom = np.sin(2 * np.pi * 70 * tt * (1 - 0.4 * tt)) * decay(n, 9)
    hit = band(noise(sec), 200, 3000) * decay(n, 40)
    rattle_tail = band(noise(sec), 1500, 5000) * decay(n, 12) * 0.15
    return norm(boom + hit + rattle_tail, 0.95)


def whoosh():
    sec = 0.9
    x = noise(sec)
    n = len(x)
    out = np.zeros(n)
    # sweep a band upward in a few overlapping chunks
    for k, (lo, hi) in enumerate([(200, 600), (400, 1200), (800, 2400), (1500, 4000)]):
        seg = band(x, lo, hi) * np.exp(-((np.arange(n) / n - (0.2 + k * 0.18)) / 0.14) ** 2)
        out += seg
    return norm(out, 0.7)


def buzz():
    """A light flickering: mains hum that cuts in and out."""
    sec = 1.2
    t = t_axis(sec)
    hum = np.sign(np.sin(2 * np.pi * 120 * t)) * 0.4 + np.sin(2 * np.pi * 240 * t) * 0.3
    gate = (np.sin(2 * np.pi * 9 * t + 3 * np.sin(2 * np.pi * 2.3 * t)) > -0.2).astype(float)
    return norm(band(hum * gate, 0, 3000) * env(len(t), 0.01, 0.1), 0.45)


def power_down():
    sec = 1.3
    ph = sweep(420, 35, sec, 0.5)
    x = np.sin(ph) + 0.3 * saw(ph)
    return norm(band(x, 0, 2000) * env(len(x), 0.005, 0.3), 0.7)


def banshee_wail():
    sec = 3.0
    t = t_axis(sec)
    u = t / sec
    f = 520 + 600 * np.sin(np.pi * np.clip(u * 1.3, 0, 1)) ** 2 - 150 * u
    f *= 1 + 0.03 * np.sin(2 * np.pi * 6 * t)  # vibrato
    ph = 2 * np.pi * np.cumsum(f) / SR
    voice = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)
    breath = band(noise(sec), 900, 4000) * 0.25
    x = (voice + breath) * env(len(t), 0.4, 1.2)
    # a ghostly echo
    d = int(0.21 * SR)
    x[d:] += 0.35 * x[:-d]
    return norm(x, 0.9)


def hoofbeats():
    """The Headless Horseman's gallop: three-beat groups, getting closer."""
    sec = 2.4
    events = []
    k, gain = 0.0, 0.35
    while k < sec - 0.2:
        for off in (0.0, 0.09, 0.19):
            s = 0.12
            tt = t_axis(s)
            thud = np.sin(2 * np.pi * 95 * tt * (1 - tt * 2)) * decay(len(tt), 35) + band(noise(s), 300, 2000) * decay(len(tt), 60) * 0.5
            events.append((k + off, thud * gain))
        k += 0.42
        gain = min(1.0, gain + 0.12)
    return norm(place(sec, events), 0.9)


def pumpkin_burst():
    sec = 1.4
    n = int(sec * SR)
    pop = band(noise(sec), 100, 1800) * decay(n, 10)
    crackle = np.zeros(n)
    for _ in range(80):
        i = RNG.integers(0, n // 2)
        crackle[i:i + 60] += RNG.uniform(-1, 1) * decay(60, 200)[: n - i]
    whomp = np.sin(2 * np.pi * 60 * t_axis(sec)) * decay(n, 7)
    return norm(pop + 0.6 * band(crackle, 1500) + whomp, 0.95)


def wisp_chime():
    events = [(k * 0.13, bell(f, 1.3, rate=2.5) * 0.7) for k, f in enumerate([1318.5, 1567.98, 1975.5, 2349.3])]
    x = place(2.0, events)
    shimmer = band(noise(2.0), 5000, 9000) * decay(int(2.0 * SR), 2) * 0.05
    return norm(x + shimmer, 0.6)


def hex_zap():
    sec = 1.2
    ph = sweep(900, 120, sec, 0.7)
    x = saw(ph) * (0.6 + 0.4 * np.sin(2 * np.pi * 22 * t_axis(sec)))
    x = band(x, 80, 3000) + band(noise(sec), 2000, 6000) * decay(int(sec * SR), 6) * 0.4
    return norm(x * env(len(x), 0.005, 0.3), 0.8)


def ghost_moan():
    sec = 2.2
    t = t_axis(sec)
    f = 175 + 40 * np.sin(np.pi * t / sec) + 4 * np.sin(2 * np.pi * 5 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.4 * band(noise(sec), 250, 700)
    return norm(x * env(len(t), 0.5, 0.8), 0.7)


def eek():
    sec = 0.32
    ph = sweep(850, 1700, sec, 0.5)
    x = np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.15 * band(noise(sec), 2000, 5000)
    return norm(x * env(len(x), 0.01, 0.12), 0.6)


def chord(midis, sec, wave=np.sin, rate=1.5, attack=0.01):
    t = t_axis(sec)
    x = sum(wave(2 * np.pi * 440 * 2 ** ((m - 69) / 12) * t) for m in midis)
    return x * decay(len(t), rate) * env(len(t), attack, 0.2)


def soft_square(ph):
    return np.tanh(3 * np.sin(ph))


def clue_chime():
    return norm(place(1.4, [(0, bell(880, 1.0)), (0.12, bell(1318.5, 1.2))]), 0.6)


def alibi_holds():
    return norm(place(1.2, [(0, bell(659.3, 0.9)), (0.15, bell(987.8, 1.0))]), 0.5)


def alibi_broken():
    x = chord([58, 59, 65], 1.5, soft_square, rate=2.2)
    return norm(band(x, 0, 2500), 0.7)


def trap_sting():
    sec = 1.8
    x = chord([45, 52, 57, 60, 64], sec, soft_square, rate=1.2, attack=0.005)
    x *= 0.75 + 0.25 * np.sin(2 * np.pi * 11 * t_axis(sec))
    return norm(band(x, 0, 3000), 0.8)


def unmask_fanfare():
    notes = [(0.0, 60), (0.12, 64), (0.24, 67), (0.36, 72)]
    events = [(s, chord([m], 0.5, soft_square, rate=3) * 0.6) for s, m in notes]
    events.append((0.5, chord([60, 64, 67, 72], 1.4, soft_square, rate=1.4)))
    return norm(band(place(2.0, events), 0, 3500), 0.8)


SOUNDS = {
    # name: (maker, loop, where it plays)
    "wind": (wind, True, "always, outdoors and in"),
    "crickets": (crickets, True, "always, quietly"),
    "rain": (rain, True, "Thunderstorm nights"),
    "drone": (drone, True, "Blood Moon nights"),
    "music_box": (music_box, True, "Willow Lane's nursery"),
    "van_engine": (van_engine, True, "the Mystery Van (pitch follows speed)"),
    "heartbeat": (heartbeat, False, "your own heart, faster as fear rises"),
    "thunder": (thunder, False, "lightning strikes"),
    "crow": (crow, False, "now and then, somewhere nearby"),
    "owl": (owl, False, "now and then, somewhere nearby"),
    "rattle": (rattle, False, "possessed: Rattle"),
    "whoosh": (whoosh, False, "possessed: Launch, the Haunter popping out"),
    "door_slam": (door_slam, False, "possessed: Slam, doors"),
    "creak": (creak, False, "doors opening"),
    "buzz": (buzz, False, "possessed: Flicker"),
    "power_down": (power_down, False, "possessed: Cut Power"),
    "banshee_wail": (banshee_wail, False, "the Banshee's Wail"),
    "hoofbeats": (hoofbeats, False, "the Horseman's Pumpkin Toss"),
    "pumpkin_burst": (pumpkin_burst, False, "a flaming jack-o'-lantern landing"),
    "wisp_chime": (wisp_chime, False, "Stingy Jack's Wisp Lure"),
    "hex": (hex_zap, False, "Baba Yaga's Hex"),
    "ghost_moan": (ghost_moan, False, "a Phantom Illusion"),
    "eek": (eek, False, "a startled suspect"),
    "clue_chime": (clue_chime, False, "a clue found"),
    "alibi_holds": (alibi_holds, False, "an alibi that checks out"),
    "alibi_broken": (alibi_broken, False, "an alibi that falls apart"),
    "trap_sting": (trap_sting, False, "the culprit named: build the trap!"),
    "unmask": (unmask_fanfare, False, "the unmasking"),
}


def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32000).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def render_all():
    """{name: samples}, for make_images_sounds.py."""
    return {name: maker() for name, (maker, _, _) in SOUNDS.items()}


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for name, (maker, loop, where) in SOUNDS.items():
        x = maker()
        path = os.path.join(OUT, name + ".wav")
        write_wav(path, x)
        total += os.path.getsize(path)
    with open(os.path.join(OUT, "sounds.json"), "w") as f:
        json.dump({"sounds": [{"id": k, "loop": v[1], "where": v[2]} for k, v in SOUNDS.items()]}, f, indent=1)
    print(f"Wrote {len(SOUNDS)} sounds to {os.path.relpath(OUT, ROOT)} ({total // 1024} KB)")


if __name__ == "__main__":
    main()
