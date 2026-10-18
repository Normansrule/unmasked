#!/usr/bin/env python3
"""
The animated pieces at the top of the README that show where the game is right now.

    python3 Docs/tools/make_readme_anim.py            # everything
    python3 Docs/tools/make_readme_anim.py tracker    # just some: tracker rounds loop cast handbook

  README.md table       the text tracker between the tracker markers (same numbers as the SVG)
  progress-tracker.svg  milestone bars that fill in, read from Docs/PROGRESS.md, plus project counts
  rounds.gif            every build round so far, one card each, with a timeline along the bottom
  night-loop.gif        one night from HQ to the unmasking, cut from the other README animations
  cast-turntable.gif    six of the town's people turning on a stage (rendered by render3d.py)
  handbook.gif          the first-time hint cards (UI/Handbook.cs) over the moments they appear

Illustrations of the design, not in-engine captures. Run make_images*.py first: rounds.gif and
night-loop.gif are cut from their pictures.
"""
import glob
import math
import os
import re
import shutil
import subprocess
import sys
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_images import OUT, ROOT, font, ease  # noqa: E402

INK = (240, 234, 250)
MUTED = (178, 168, 206)
AMBER = (255, 178, 64)
GREEN = (110, 214, 140)
VIOLET = (168, 110, 240)
NIGHT = (18, 13, 30)

# The newest round is the last entry. Each round: title, one line, and the README picture that
# shows it best (cropped to fit the card).
ROUNDS = [
    ("The match", "Solvers, the Haunter, clues, the Suspect Board, traps and the unmasking", "suspect-board.png"),
    ("Play without a full lobby", "AI Director, Solver roles, animation, downloads and the terminal tool", "powers.png"),
    ("Blackwood Manor in 3D", "Four floors and the grounds, built from one layout file", "manor-cutaway.png"),
    ("Tonight's legends", "Headless Horseman, Banshee, Stingy Jack, Baba Yaga and their powers", "villains.png"),
    ("Hollow Creek", "A town with HQ, the van, five houses of different sizes and a map", "town-map.png"),
    ("Halloween night", "Window trims, carved jacks, string lights and surface patterns everywhere", "nights-of-jack.png"),
    ("A case for every house", "Each house has its own suspects, clues and gossip", "case-files.png"),
    ("Dressed for each house", "Every house's suspects get their own outfits and stroll around", "suspects-by-house.png"),
    ("Witnesses", "Suspects jump at scares, and whoever saw it can tell you something", "witness.png"),
    ("Alibis", "Check where a suspect says they were; the Haunter can fake one", "secrets.png"),
    ("The sound", "28 generated sounds: wind, crows, hoofbeats, the van, a music box", "sounds.png"),
    ("First open in Unity", "The project sets itself up and builds the town on first open", "controls.png"),
    ("Storybook direction", "Why each mask is worn, motives, and a beat before every scare", "story.png"),
    ("Reference renders", "Big stills of every house and a tour video, plus a timed Suspect Board", "house-cards.png"),
    ("The case book", "Solved cases are saved; keepsakes fill the shelf at HQ", "case-book.png"),
    ("A bigger world", "Hills, far lights, roads out of town and landmarks on the horizon", "horizon.png"),
    ("A living town", "Trick-or-treaters with rumours, cars and a train in the valley", "living-town.png"),
    ("The fifth call", "The Historical Society unlocks after the first four cases", "museum.png"),
    ("The people of Hollow Creek", "Five townsfolk with errands that earn favours", "townsfolk.png"),
    ("Return visits", "Every house calls again with a second case", "return-visits.png"),
    ("The character pass", "Faces with lashes and lips, real hands, hair, heights and builds", "portraits.png"),
    ("A town that remembers", "The Lantern Watch costume, party yards, saved errands, a case checker", "lantern-watch.png"),
    ("The Club Handbook", "First-time hints for new players, and this animated README", "handbook.gif"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def save_gif(frames, durations, name, colors=200):
    """Like make_images.save_gif, but every frame keeps its own duration (holds on the cards)."""
    path = os.path.join(OUT, name)
    picks = frames[:: max(1, len(frames) // 16)]
    sheet = Image.new("RGB", (frames[0].width, frames[0].height * len(picks)))
    for i, f in enumerate(picks):
        sheet.paste(f, (0, i * f.height))
    base = sheet.quantize(colors=colors, method=Image.MEDIANCUT)
    pal = [f.quantize(palette=base, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durations, loop=0, optimize=False)
    if shutil.which("convert"):
        subprocess.run(["convert", path, "-layers", "Optimize", path], check=False)
    print(f"  {name}: {len(frames)} frames, {os.path.getsize(path) // 1024} KB")


def image(name):
    return Image.open(os.path.join(OUT, name))


def first_frame(name):
    im = image(name)
    im.seek(0)
    return im.convert("RGB")


def gif_frames(name, step=1, limit=None):
    im = image(name)
    out = []
    for i in range(0, getattr(im, "n_frames", 1), step):
        im.seek(i)
        out.append(im.convert("RGB"))
        if limit and len(out) >= limit:
            break
    return out


def cover(im, w, h, top=True):
    """Scale to fill w x h and crop. Tall pictures keep their top, where the title is."""
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x = (im.width - w) // 2
    y = 0 if top else (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def fit(im, w, h, bg=NIGHT):
    """Scale to fit inside w x h, centred on a background (wide pictures stay whole)."""
    s = min(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    out = Image.new("RGB", (w, h), bg)
    out.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return out


def picture(name, w, h):
    im = first_frame(name) if name.endswith(".gif") else image(name).convert("RGB")
    if im.height > im.width * 0.9:
        return cover(im, w, h, top=True)
    if im.width / im.height > (w / h) * 1.35:
        return fit(im, w, h)
    return cover(im, w, h, top=False)


def vignette(img, strength=0.55):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    for i in range(24):
        a = int(255 * strength * (1 - i / 24) ** 2)
        d.rectangle([i * w // 80, i * h // 80, w - i * w // 80, h - i * h // 80], outline=a, width=max(1, w // 80))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(dark, img, mask)


def fade(a, b, t):
    return Image.blend(a, b, ease(t))


# ---------------------------------------------------------------------------
# The progress tracker (SVG: GitHub shows its animation in the README)
# ---------------------------------------------------------------------------
def read_progress():
    """Milestones and their ticked/total task counts from Docs/PROGRESS.md."""
    rows, cur = [], None
    with open(os.path.join(ROOT, "Docs", "PROGRESS.md"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^## (.+)", line)
            if m:
                cur = [m.group(1).strip(), 0, 0]
                rows.append(cur)
            elif cur and re.match(r"^\s*- \[[ x]\]", line):
                cur[2] += 1
                cur[1] += "[x]" in line
    return rows


def project_counts():
    scripts = glob.glob(os.path.join(ROOT, "Assets", "**", "*.cs"), recursive=True)
    lines = sum(sum(1 for _ in open(p, encoding="utf-8", errors="ignore")) for p in scripts)
    cases = len(re.findall(r"new Spec\b|new\(\)\s*\{\s*HouseId", open(os.path.join(ROOT, "Assets", "Unmasked", "Scripts", "Mystery", "Cases.cs"), encoding="utf-8").read()))
    return {"scripts": len(scripts), "lines": lines, "cases": cases}


def rgb(c):
    return "#%02x%02x%02x" % c


def grow(width, delay, dur):
    """SMIL that grows a bar from 0 after a delay. The rect's own width is the end value, so a
    viewer that doesn't animate still shows the finished bar."""
    total = delay + dur
    k = delay / total
    return (f'<animate attributeName="width" values="0;0;{width:.1f}" keyTimes="0;{k:.3f};1" dur="{total:.2f}s" '
            f'fill="freeze" calcMode="spline" keySplines="0 0 1 1;0.2 0.7 0.3 1"/>')


def make_tracker():
    rows = read_progress()
    counts = project_counts()
    done = sum(r[1] for r in rows)
    total = sum(r[2] for r in rows)
    W = 900
    top = 236
    rh = 27
    H = top + rh * len(rows) + 92
    bar_x, bar_w = 360, 410
    out = []
    a = out.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Inter, Segoe UI, Helvetica, Arial, sans-serif">')
    a("<defs>"
      '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d1433"/><stop offset="1" stop-color="#120c1f"/></linearGradient>'
      '<linearGradient id="done" x1="0" x2="1"><stop offset="0" stop-color="#ff9a3c"/><stop offset="1" stop-color="#ffd46a"/></linearGradient>'
      '<linearGradient id="full" x1="0" x2="1"><stop offset="0" stop-color="#5fcf8a"/><stop offset="1" stop-color="#a6f0b8"/></linearGradient>'
      '<radialGradient id="glow"><stop offset="0" stop-color="#ffb347" stop-opacity="0.9"/><stop offset="1" stop-color="#ffb347" stop-opacity="0"/></radialGradient>'
      "</defs>")
    a("<style>"
      ".t{fill:#f0eafa;font-weight:700}.m{fill:#b2a8ce;font-weight:500}.n{fill:#f0eafa;font-weight:800}"
      ".pop{animation:pop .6s ease-out backwards}"
      "@keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
      ".blink{animation:blink 1.6s ease-in-out infinite}@keyframes blink{50%{opacity:.25}}"
      ".flick{animation:flick 3.2s steps(1) infinite}@keyframes flick{0%{opacity:1}46%{opacity:.7}48%{opacity:1}83%{opacity:.82}85%{opacity:1}}"
      "</style>")
    a(f'<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>')
    a(f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="17" fill="none" stroke="#3a2a5c" stroke-width="2"/>')

    # Header: a little jack-o'-lantern that flickers, the title and the round.
    a('<g class="flick" transform="translate(48 50)">'
      '<circle r="30" fill="url(#glow)"/>'
      '<ellipse rx="19" ry="16" fill="#ff8a24"/><rect x="-3" y="-23" width="6" height="8" rx="2" fill="#5c7a3a"/>'
      '<path d="M-10 -5 l5 -6 l5 6z M0 -5 l5 -6 l5 6z" fill="#3a1606" transform="translate(-2.5 0)"/>'
      '<path d="M-11 4 q11 9 22 0 l-3 5 q-8 5 -16 0z" fill="#3a1606"/></g>')
    a(f'<text x="92" y="44" class="t" font-size="26">Where UNMASKED is right now</text>')
    a(f'<text x="92" y="68" class="m" font-size="14">Round {len(ROUNDS)} · read from Docs/PROGRESS.md each time the pictures are rebuilt</text>')

    # Count tiles that pop in one after another.
    tiles = [(str(len(ROUNDS)), "build rounds"), (str(counts["scripts"]), "C# scripts"), (f'{counts["lines"]:,}', "lines of C#"),
             ("5", "houses"), (str(counts["cases"]), "solvable cases"), ("0", "compile errors"), ("0", "Unity playtests")]
    tw = (W - 48 - 6 * 10) / len(tiles)
    for i, (num, lab) in enumerate(tiles):
        x = 24 + i * (tw + 10)
        warn = lab == "Unity playtests"
        stroke = "#ffb347" if warn else "#4a3870"
        a(f'<g class="pop" style="animation-delay:{0.15 + i * 0.12:.2f}s">'
          f'<rect x="{x:.1f}" y="92" width="{tw:.1f}" height="62" rx="10" fill="#241a3d" stroke="{stroke}" stroke-width="1.5"/>'
          f'<text x="{x + tw / 2:.1f}" y="124" text-anchor="middle" class="n" font-size="22"{" fill=\"#ffb347\"" if warn else ""}>{num}</text>'
          f'<text x="{x + tw / 2:.1f}" y="144" text-anchor="middle" class="m" font-size="11">{lab}</text></g>')

    # Overall bar.
    frac = done / max(1, total)
    a(f'<text x="24" y="186" class="t" font-size="15">Overall</text>')
    a(f'<text x="{W - 24}" y="186" text-anchor="end" class="m" font-size="13">{done} of {total} tasks ticked</text>')
    a(f'<rect x="24" y="196" width="{W - 48}" height="16" rx="8" fill="#2c2148"/>')
    a(f'<rect x="24" y="196" width="{(W - 48) * frac:.1f}" height="16" rx="8" fill="url(#done)">{grow((W - 48) * frac, 0.9, 1.6)}</rect>')
    a(f'<text x="{24 + (W - 48) * frac - 8:.1f}" y="209" text-anchor="end" class="n pop" font-size="11" fill="#3a1606" style="animation-delay:2.4s">{round(frac * 100)}%</text>')

    # One bar per milestone, filling in turn.
    for i, (name, d, t) in enumerate(rows):
        y = top + i * rh
        delay = 1.2 + i * 0.09
        f = d / max(1, t)
        short = re.sub(r"^Milestone (\d+): ", r"\1 · ", name)
        if len(short) > 46:
            short = short[:44] + "…"
        a(f'<text x="24" y="{y + 15}" class="m" font-size="13">{escape(short)}</text>')
        a(f'<rect x="{bar_x}" y="{y + 4}" width="{bar_w}" height="13" rx="6.5" fill="#2c2148"/>')
        fill = "url(#full)" if d == t else "url(#done)"
        a(f'<rect x="{bar_x}" y="{y + 4}" width="{bar_w * f:.1f}" height="13" rx="6.5" fill="{fill}">{grow(bar_w * f, delay, 0.9)}</rect>')
        mark = "✓" if d == t else f"{d}/{t}"
        col = "#a6f0b8" if d == t else "#ffd46a" if d else "#b2a8ce"
        a(f'<text x="{W - 24}" y="{y + 15}" text-anchor="end" font-size="13" font-weight="700" fill="{col}" class="pop" style="animation-delay:{delay + 0.6:.2f}s">{mark}</text>')

    # Footer: what is next, with a blinking marker.
    y = top + rh * len(rows) + 22
    a(f'<rect x="24" y="{y}" width="{W - 48}" height="50" rx="10" fill="#2a1d18" stroke="#ffb347" stroke-width="1.5"/>')
    a(f'<circle cx="46" cy="{y + 25}" r="7" fill="#ffb347" class="blink"/>')
    a(f'<text x="64" y="{y + 21}" class="t" font-size="14">Next: open it in Unity for the first time</text>')
    a(f'<text x="64" y="{y + 39}" class="m" font-size="12">Everything compiles against Unity\'s libraries, but nothing has been played in the editor yet. Green = milestone done, amber = in progress.</text>')
    a("</svg>")
    path = os.path.join(OUT, "progress-tracker.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"  progress-tracker.svg: {len(rows)} milestones, {done}/{total} tasks, {os.path.getsize(path) // 1024} KB")


def read_tasks():
    """Every milestone with its tasks: [(name, [(done, text), ...]), ...]."""
    out = []
    with open(os.path.join(ROOT, "Docs", "PROGRESS.md"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^## (.+)", line)
            if m:
                out.append((m.group(1).strip(), []))
            t = re.match(r"^\s*- \[([ x])\] (.+)", line)
            if t and out:
                out[-1][1].append((t.group(1) == "x", t.group(2).strip()))
    return out


def text_bar(f, n=12):
    k = round(f * n)
    return "█" * k + "░" * (n - k)


def make_readme_table():
    """The text tracker in README.md between the tracker markers (works with images off too)."""
    rows = read_tasks()
    done = sum(d for _, ts in rows for d, _ in ts)
    total = sum(len(ts) for _, ts in rows)
    finished = sum(1 for _, ts in rows if ts and all(d for d, _ in ts))
    started = sum(1 for _, ts in rows if any(d for d, _ in ts) and not all(d for d, _ in ts))
    lines = ["<!-- tracker:start (written by Docs/tools/make_readme_anim.py from Docs/PROGRESS.md) -->",
             "",
             f"**Overall: `{text_bar(done / total, 24)}` {round(100 * done / total)}%**, {done} of {total} tasks. "
             f"{finished} milestones done, {started} in progress, {len(rows) - finished - started} not started. "
             "Built means the code and data exist and compile; **nothing has been played in Unity yet**.",
             "",
             "| Milestone | Progress | Tasks | State | Played in Unity |",
             "|---|---|---|---|---|"]
    for name, ts in rows:
        d = sum(x for x, _ in ts)
        f = d / max(1, len(ts))
        state = "✅ Built, compiles" if d == len(ts) else "🟡 In progress" if d else "⬜ Not started"
        lines.append(f"| {name} | `{text_bar(f)}` {round(100 * f)}% | {d}/{len(ts)} | {state} | Not yet |")
    lines += ["", "<details><summary><b>What's left</b> (every unticked task)</summary>", ""]
    for name, ts in rows:
        left = [t for x, t in ts if not x]
        if left:
            lines.append(f"- **{name}**: " + "; ".join(left))
    lines += ["", "</details>", "", "<!-- tracker:end -->"]
    path = os.path.join(ROOT, "README.md")
    with open(path, encoding="utf-8") as f:
        readme = f.read()
    block = "\n".join(lines)
    new = re.sub(r"<!-- tracker:start.*?<!-- tracker:end -->", lambda _: block, readme, flags=re.S)
    if new == readme and "<!-- tracker:start" not in readme:
        print("  README.md has no tracker markers; nothing written")
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)
    print(f"  README.md tracker: {len(rows)} milestones, {done}/{total} tasks")


# ---------------------------------------------------------------------------
# rounds.gif: one card per round with the timeline along the bottom
# ---------------------------------------------------------------------------
def rounds_card(n, pic, W, H):
    title, blurb, _ = ROUNDS[n]
    img = Image.new("RGB", (W, H), NIGHT)
    pw, ph = 560, 315
    img.paste(vignette(pic, 0.35), (24, 24))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([22, 22, 24 + pw + 1, 24 + ph + 1], radius=6, outline=(90, 66, 140), width=2)
    x0 = 24 + pw + 26
    d.text((x0, 34), "ROUND", font=font(15, "Bold"), fill=MUTED)
    d.text((x0, 52), f"{n + 1}", font=font(64, "Black"), fill=AMBER)
    d.text((x0 + 4 + d.textlength(f"{n + 1}", font=font(64, "Black")) + 10, 92), f"of {len(ROUNDS)}", font=font(16, "Medium"), fill=MUTED)
    # Wrap the title and the line to the text column.
    y = 138
    for text_, size, weight, fill in ((title, 24, "Black", INK), (blurb, 15, "Medium", MUTED)):
        words, cur = text_.split(), ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if d.textlength(trial, font=font(size, weight)) > W - x0 - 22:
                d.text((x0, y), cur, font=font(size, weight), fill=fill)
                y += size + 7
                cur = w_
            else:
                cur = trial
        d.text((x0, y), cur, font=font(size, weight), fill=fill)
        y += size + 16
    if n == len(ROUNDS) - 1:
        d.rounded_rectangle([x0, y, x0 + 128, y + 26], radius=13, fill=(255, 178, 64, 255))
        d.text((x0 + 64, y + 13), "YOU ARE HERE", font=font(12, "Black"), fill=(40, 18, 6), anchor="mm")
    return img


def timeline(img, n, t, W, H):
    """The strip along the bottom: a dot per round, lit up to round n, the current one glowing."""
    d = ImageDraw.Draw(img, "RGBA")
    y = H - 34
    x0, x1 = 40, W - 40
    step = (x1 - x0) / (len(ROUNDS) - 1)
    d.line([(x0, y), (x1, y)], fill=(60, 46, 92), width=4)
    d.line([(x0, y), (x0 + step * n, y)], fill=AMBER, width=4)
    for i in range(len(ROUNDS)):
        x = x0 + step * i
        if i < n:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=AMBER)
        elif i == n:
            r = 9 + 3 * math.sin(t * math.tau)
            d.ellipse([x - r - 5, y - r - 5, x + r + 5, y + r + 5], fill=(255, 178, 64, 60))
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(255, 210, 120), outline=(255, 255, 255), width=2)
        else:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(40, 30, 64), outline=(90, 70, 130), width=2)
        if i % 2 == 0 or i == len(ROUNDS) - 1:
            d.text((x, y + 18), str(i + 1), font=font(10, "Bold"), fill=INK if i <= n else MUTED, anchor="mm")


def make_rounds():
    W, H = 960, 410
    frames, durations = [], []
    cards = [rounds_card(i, picture(r[2], 560, 315), W, H) for i, r in enumerate(ROUNDS)]
    for i, card in enumerate(cards):
        # Hold on the card while its dot pulses, then a quick cross-fade into the next one.
        for k in range(4):
            f = card.copy()
            timeline(f, i, k / 4, W, H)
            frames.append(f)
            durations.append(650 if i < len(cards) - 1 else 900)
        if i < len(cards) - 1:
            for k in (1, 2):
                f = fade(card, cards[i + 1], k / 3)
                timeline(f, i, 0, W, H)
                frames.append(f)
                durations.append(70)
    save_gif(frames, durations, "rounds.gif", colors=220)


# ---------------------------------------------------------------------------
# night-loop.gif: one night, cut from the other animations
# ---------------------------------------------------------------------------
STEPS = [
    ("1", "At HQ, take a call", "The case book and the call board", ("still", "case-book.png")),
    ("2", "Drive the van across town", "M opens the map; follow the arrow", ("gif", "van-drive.gif")),
    ("3", "Search the house", "Flashlights on, every house is different", ("gif", "manor-walkthrough.gif")),
    ("4", "Find clues, cross off suspects", "Tab opens the Suspect Board", ("still", "suspect-board.png")),
    ("5", "Survive the Haunter", "Chairs hop, lamps turn, pumpkins fly", ("gif", "anticipation.gif")),
    ("6", "Name them, trap them", "Right suspect: build the trap and spring it", ("gif", "match-3d.gif")),
    ("7", "Pull off the mask", "And find out why they did it", ("gif", "unmask.gif")),
    ("8", "The street remembers", "The yard throws a party for the club", ("still", "street-remembers.png")),
]


def step_frames(kind, name, W, H, count):
    if kind == "gif":
        src = gif_frames(name)
        if name == "match-3d.gif":
            src = src[len(src) // 2: len(src) * 5 // 6]  # the trap and the catch
        idx = [int(i * len(src) / count) for i in range(count)]
        return [picture_from(src[i], W, H) for i in idx]
    base = picture(name, W + 60, H + 34)
    out = []
    for i in range(count):
        t = i / max(1, count - 1)  # a slow pan across the still
        x, y = int(60 * t), int(34 * (1 - t) * 0.5)
        out.append(base.crop((x, y, x + W, y + H)))
    return out


def picture_from(im, w, h):
    if im.width / im.height > (w / h) * 1.35:
        return fit(im, w, h)
    return cover(im, w, h, top=False)


def caption_bar(img, n, title, sub, t):
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, H - 68, W, H], fill=(14, 9, 24, 225))
    slide = int(18 * (1 - ease(min(1, t * 3))))
    d.ellipse([16, H - 56, 60, H - 12], fill=AMBER)
    d.text((38, H - 34), n, font=font(22, "Black"), fill=(40, 18, 6), anchor="mm")
    d.text((74 + slide, H - 58), title, font=font(21, "Black"), fill=INK)
    d.text((74 + slide, H - 30), sub, font=font(14, "Medium"), fill=MUTED)
    # Eight pips on the right: where in the night we are.
    for i in range(len(STEPS)):
        x = W - 24 - (len(STEPS) - 1 - i) * 18
        lit = i < int(n)
        d.ellipse([x - 5, H - 39, x + 5, H - 29], fill=AMBER if lit else (60, 46, 92))
    d.text((W - 12, 14), "illustration from the game's files, not an engine capture", font=font(10, "Medium"), fill=(200, 190, 225, 200), anchor="ra")


def make_loop():
    W, H = 720, 405
    frames, durations = [], []
    clips = [step_frames(kind, name, W, H, 16) for _, _, _, (kind, name) in STEPS]
    for s, ((n, title, sub, _), clip) in enumerate(zip(STEPS, clips)):
        for i, f in enumerate(clip):
            f = f.copy()
            if i < 2 and s > 0:
                f = fade(clips[s - 1][-1], f, (i + 1) / 3)
            caption_bar(f, n, title, sub, i / len(clip))
            frames.append(f)
            durations.append(150)
        durations[-1] = 700
    save_gif(frames, durations, "night-loop.gif", colors=230)


# ---------------------------------------------------------------------------
# cast-turntable.gif: the round 21 people, turning
# ---------------------------------------------------------------------------
CAST = [("solvers", "Sleuth", "Sleuth"), ("suspects", "Folk.Mayor", "Harold Beaumont"), ("suspects", "HistoricalSociety.Heiress", "Edie Wren"),
        ("suspects", "Folk.Fortune", "Old Nell"), ("suspects", "HistoricalSociety.Cook", "Rosa Delgado"), ("solvers", "Brawn", "Brawn")]


def make_cast():
    import render3d as r3
    from make_images_3d import label
    from make_images_people import load  # noqa: F401  (same loader the portraits use)
    c = r3.costumes()
    for key in ("suspects", "solvers"):
        if isinstance(c[key], list):
            c[key] = {item["id"]: item for item in c[key]}
    W, H, n = 900, 380, 24
    xs = [3.75, 2.25, 0.75, -0.75, -2.25, -3.75]  # +x is screen-left looking down -z
    frames = []
    for i in range(n):
        ry = 360 * i / n
        m = r3.Mesh()
        m.add_shape("box", (0, -0.1, 0), (30, 0.2, 14), (0, 0, 0), (0.12, 0.08, 0.13))
        for x, (group, cid, _) in zip(xs, CAST):
            m.add_shape("cyl", (x, 0.04, 0), (1.25, 0.04, 1.25), (0, 0, 0), (0.27, 0.18, 0.31))
            m.add_parts(c[group][cid]["parts"], (x, 0.08, 0), ry)
        lights = [{"p": [-3, 3.2, 3.5], "c": [1.0, 0.74, 0.5], "range": 11, "intensity": 1.4},
                  {"p": [3.2, 3.0, 3.0], "c": [0.7, 0.78, 1.0], "range": 11, "intensity": 1.0},
                  {"p": [0, 2.2, -2.5], "c": [1.0, 0.55, 0.25], "range": 8, "intensity": 1.2}]
        cam = r3.Camera((0, 1.5, 8.4), (0, 1.0, 0), 32, W, H)
        img = r3.render({"lights": [], "glows": []}, cam, m, lights=lights, fog_density=0.0, ambient=(0.24, 0.19, 0.3), moon=False)
        d = ImageDraw.Draw(img, "RGBA")
        for x, (_, _, name) in zip(xs, CAST):
            p = cam.project((x, -0.1, 0.9))[0]
            label(d, (p[0], min(H - 16, p[1] + 4)), name, 13)
        d.text((12, 12), "The people of Hollow Creek", font=font(18, "Black"), fill=INK)
        d.text((12, 36), "rendered from Costumes.json by the project's own renderer", font=font(11, "Medium"), fill=MUTED)
        frames.append(img)
        print(f"    cast frame {i + 1}/{n}", flush=True)
    save_gif(frames, [110] * n, "cast-turntable.gif", colors=220)


# ---------------------------------------------------------------------------
# handbook.gif: the first-time hint cards over the moments they show up
# ---------------------------------------------------------------------------
HINTS = [  # same words as UI/Handbook.cs
    ("Mystery Club HQ", "Every night starts here. The host picks a call on the call board, then the club drives out in the van.", "case-book.png"),
    ("On the way", "Whoever sits in the driver's seat steers with WASD. M opens the town map; follow the arrow to tonight's house.", "van-drive.gif"),
    ("The Suspect Board", "You found a clue. Press Tab to see who it fits, and cross off anyone it rules out.", "suspect-board.png"),
    ("Scared!", "Stay near a teammate to calm down. Three panics and you are out for the night.", "anticipation.gif"),
    ("Case closed", "That house throws a party now, and the town remembers. Back at HQ, the next call is waiting.", "street-remembers.png"),
]


def hint_card(img, title, text_, t):
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    rise = int(40 * (1 - ease(min(1, t))))
    alpha = int(235 * ease(min(1, t)))
    x0, y0 = W // 2 - 270, H - 138 + rise
    d.rounded_rectangle([x0, y0, x0 + 540, y0 + 104], radius=8, fill=(20, 14, 34, alpha), outline=(255, 178, 64, alpha), width=2)
    d.text((x0 + 14, y0 + 10), "Handbook: " + title, font=font(16, "Black"), fill=INK + (alpha,))
    words, cur, y = text_.split(), "", y0 + 36
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if d.textlength(trial, font=font(13, "Medium")) > 510:
            d.text((x0 + 14, y), cur, font=font(13, "Medium"), fill=INK + (alpha,))
            y, cur = y + 18, w_
        else:
            cur = trial
    d.text((x0 + 14, y), cur, font=font(13, "Medium"), fill=INK + (alpha,))
    d.text((x0 + 14, y0 + 84), "F1: the whole handbook", font=font(11, "Medium"), fill=MUTED + (alpha,))
    d.rounded_rectangle([x0 + 448, y0 + 10, x0 + 528, y0 + 34], radius=4, fill=(70, 56, 104, alpha))
    d.text((x0 + 488, y0 + 22), "Got it", font=font(12, "Bold"), fill=INK + (alpha,), anchor="mm")


def make_handbook():
    W, H = 720, 405
    frames, durations = [], []
    for title, text_, bg in HINTS:
        if bg.endswith(".gif"):
            src = gif_frames(bg)
            base = [picture_from(src[int(i * len(src) / 10)], W, H) for i in range(10)]
        else:
            base = step_frames("still", bg, W, H, 10)
        for i, f in enumerate(base):
            f = ImageEnhance.Brightness(f).enhance(0.8)
            hint_card(f, title, text_, (i + 1) / 4)
            d = ImageDraw.Draw(f, "RGBA")
            d.text((W - 12, 12), "illustration of UI/Handbook.cs, not an engine capture", font=font(10, "Medium"), fill=(220, 210, 240, 210), anchor="ra")
            frames.append(f)
            durations.append(160)
        durations[-1] = 1500
    save_gif(frames, durations, "handbook.gif", colors=220)


JOBS = {"tracker": make_tracker, "table": make_readme_table, "handbook": make_handbook, "rounds": make_rounds, "loop": make_loop, "cast": make_cast}

if __name__ == "__main__":
    for job in sys.argv[1:] or list(JOBS):
        print(job)
        JOBS[job]()
