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
  hud-refresh.png       the interface in the UITheme look (and hud-board.png, the Suspect Board)
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

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_images import OUT, ROOT, ease  # noqa: E402

# The Case Book: the same tokens as Assets/Unmasked/Scripts/UI/UITheme.cs and the website's dark
# mode (site/styles.css). Warm dark paper, a corkboard, evidence-tag red as the one accent, green for
# done, violet for the Haunter only.
INK = (243, 234, 219)
MUTED = (205, 191, 171)
FAINT = (162, 147, 127)
ACCENT = (239, 108, 91)
GREEN = (130, 207, 159)
HAUNT = (172, 153, 242)
GROUND = (22, 18, 14)
SURFACE = (36, 29, 23)
RAISED = (46, 38, 30)
CORK = (59, 44, 32)
TAGWASH = (62, 34, 28)
ON_ACCENT = (29, 18, 13)

# Fraunces for names and headings, Atkinson Hyperlegible for reading: the game's own font files.
FONTS = os.path.join(ROOT, "Assets", "Unmasked", "Resources", "Fonts")
_font_cache = {}


def font(size, weight="Bold"):
    """Heavy weights are set in Fraunces (display cut at 26 and up), the rest in Atkinson Hyperlegible."""
    if weight in ("Black", "ExtraBold") or (weight == "Bold" and size >= 18):
        name = "Fraunces-Display.ttf" if size >= 26 else "Fraunces-Title.ttf"
    else:
        name = "Atkinson-Bold.ttf" if weight in ("Bold", "SemiBold") else "Atkinson-Regular.ttf"
    key = (name, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(os.path.join(FONTS, name), size)
    return _font_cache[key]


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
    ("The Club Handbook", "First-time hints for new players, and an animated README", "handbook.gif"),
    ("The design pass", "One look for every panel: colour, type, spacing and calm motion", "hud-refresh.png"),
    ("The Case Book", "A corkboard look for the game, and a website with a playable Suspect Board", "hud-board.png"),
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


def fit(im, w, h, bg=GROUND):
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


TRACKER_THEMES = {
    # Case Book paper by day and the same desk under a lamp: the README shows the one that matches
    # the reader's GitHub theme (a <picture> with a prefers-color-scheme source).
    "light": {"bg": "#fffaf1", "edge": "#d6c9b3", "ink": "#221c16", "muted": "#554a3e", "faint": "#72655a", "track": "#ebe1cf",
              "bar": "#554a3e", "done": "#2b6b45", "accent": "#ae2f26", "on_accent": "#fff6ef"},
    "dark": {"bg": "#16120e", "edge": "#3d332a", "ink": "#f3eadb", "muted": "#cdbfab", "faint": "#a2937f", "track": "#2e261e",
             "bar": "#cdbfab", "done": "#82cf9f", "accent": "#ef6c5b", "on_accent": "#1d120d"},
}


def svg_fonts(text):
    """The game's own fonts, cut down to the characters this picture uses and embedded, so the
    SVG looks the same wherever it's shown (an SVG in an <img> can't load web fonts)."""
    import base64
    import io
    from fontTools import subset
    from fontTools.ttLib import TTFont
    css = []
    for family, file_, weight in (("Fraunces", "Fraunces-Display.ttf", 700), ("Atkinson", "Atkinson-Regular.ttf", 400), ("Atkinson", "Atkinson-Bold.ttf", 700)):
        f = TTFont(os.path.join(FONTS, file_))
        sub = subset.Subsetter(subset.Options())
        sub.populate(text=text + "0123456789%·,. ")
        sub.subset(f)
        f.flavor = "woff2"
        buf = io.BytesIO()
        f.save(buf)
        css.append(f"@font-face{{font-family:{family};font-weight:{weight};src:url(data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}) format('woff2')}}")
    return "".join(css)


def make_tracker():
    for theme in TRACKER_THEMES:
        make_tracker_theme(theme)


def make_tracker_theme(theme):
    c = TRACKER_THEMES[theme]
    rows = read_progress()
    counts = project_counts()
    done = sum(r[1] for r in rows)
    total = sum(r[2] for r in rows)
    W = 900
    top = 214
    rh = 27
    H = top + rh * len(rows) + 64
    bar_x, bar_w = 380, 400
    body = []
    a = body.append
    a(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="4" fill="{c["bg"]}" stroke="{c["edge"]}"/>')
    a('<text x="28" y="54" class="h" font-size="30">Where Unmasked is right now</text>')
    a(f'<text x="28" y="80" class="m" font-size="14">Round {len(ROUNDS)}. Read from Docs/PROGRESS.md every time the pictures are rebuilt.</text>')

    # The numbers, set large in the serif: no boxes, just figures and what they count.
    stats = [(str(len(ROUNDS)), "build rounds"), (str(counts["scripts"]), "C# scripts"), (f'{counts["lines"]:,}', "lines of C#"),
             ("5", "houses"), (str(counts["cases"]), "solvable cases"), ("0", "compile errors"), ("0", "Unity playtests")]
    sw = (W - 56) / len(stats)
    for i, (num, lab) in enumerate(stats):
        x = 28 + i * sw
        warn = lab == "Unity playtests"
        a(f'<g class="pop" style="animation-delay:{0.1 + i * 0.05:.2f}s">'
          f'<text x="{x:.1f}" y="128" class="n" font-size="28"{f" style=\"fill:{c['accent']}\"" if warn else ""}>{num}</text>'
          f'<text x="{x:.1f}" y="148" class="m" font-size="12">{lab}</text></g>')

    # Overall: the one red bar.
    frac = done / max(1, total)
    a('<text x="28" y="182" class="b" font-size="15">Overall</text>')
    a(f'<text x="{W - 28}" y="182" text-anchor="end" class="m" font-size="13">{done} of {total} tasks ticked ({round(frac * 100)}%)</text>')
    a(f'<rect x="28" y="192" width="{W - 56}" height="8" rx="4" fill="{c["track"]}"/>')
    a(f'<rect x="28" y="192" width="{(W - 56) * frac:.1f}" height="8" rx="4" fill="{c["accent"]}">{grow((W - 56) * frac, 0.4, 0.9)}</rect>')

    # One bar per milestone, filling in turn.
    for i, (name, d, t) in enumerate(rows):
        y = top + 14 + i * rh
        delay = 0.6 + i * 0.04
        f = d / max(1, t)
        short = re.sub(r"^Milestone \d+: ", "", name)
        if len(short) > 44:
            short = short[:42] + "…"
        a(f'<text x="28" y="{y + 12}" class="{"b" if d == t else "m"}" font-size="13">{escape(short)}</text>')
        a(f'<rect x="{bar_x}" y="{y + 4}" width="{bar_w}" height="6" rx="3" fill="{c["track"]}"/>')
        fill = c["done"] if d == t else c["bar"]
        a(f'<rect x="{bar_x}" y="{y + 4}" width="{bar_w * f:.1f}" height="6" rx="3" fill="{fill}">{grow(bar_w * f, delay, 0.7)}</rect>')
        mark = "done" if d == t else f"{d} of {t}"
        col = c["done"] if d == t else c["muted"] if d else c["faint"]
        a(f'<text x="{W - 28}" y="{y + 12}" text-anchor="end" font-size="14" class="n" style="fill:{col}">{mark}</text>')

    y = top + rh * len(rows) + 34
    a(f'<text x="28" y="{y}" class="b" font-size="14">Next: open it in Unity for the first time.</text>')
    a(f'<text x="28" y="{y + 20}" class="m" font-size="12">Everything compiles against Unity\'s libraries, but nothing has been played in the editor yet. Green: done.</text>')

    text = re.sub(r"<[^>]+>", " ", "".join(body))
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            "<style>" + svg_fonts(text) +
            f".h{{font-family:Fraunces,Georgia,serif;font-weight:700;fill:{c['ink']}}}"
            f".n{{font-family:Fraunces,Georgia,serif;font-weight:700;fill:{c['ink']}}}"
            f".b{{font-family:Atkinson,Segoe UI,sans-serif;font-weight:700;fill:{c['ink']}}}"
            f".m{{font-family:Atkinson,Segoe UI,sans-serif;font-weight:400;fill:{c['muted']}}}"
            ".pop{animation:pop .5s cubic-bezier(.23,1,.32,1) backwards}"
            "@keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
            "@media (prefers-reduced-motion: reduce){.pop{animation:none}}"
            "</style>")
    name = "progress-tracker.svg" if theme == "dark" else "progress-tracker-light.svg"
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "".join(body) + "</svg>")
    print(f"  {name}: {len(rows)} milestones, {done}/{total} tasks, {os.path.getsize(path) // 1024} KB")


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
    img = Image.new("RGB", (W, H), GROUND)
    pw, ph = 560, 315
    img.paste(pic, (24, 24))
    d = ImageDraw.Draw(img, "RGBA")
    x0 = 24 + pw + 28
    d.text((x0, 30), f"Round {n + 1} of {len(ROUNDS)}", font=font(16, "Bold"), fill=ACCENT)
    # Wrap the title and the line to the text column.
    y = 60
    for text_, size, weight, fill in ((title, 30, "Black", INK), (blurb, 16, "Medium", MUTED)):
        words, cur = text_.split(), ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if d.textlength(trial, font=font(size, weight)) > W - x0 - 24:
                d.text((x0, y), cur, font=font(size, weight), fill=fill)
                y += size + 8
                cur = w_
            else:
                cur = trial
        d.text((x0, y), cur, font=font(size, weight), fill=fill)
        y += size + 18
    if n == len(ROUNDS) - 1:
        d.text((x0, y), "This is where the game is now.", font=font(15, "Bold"), fill=INK)
    return img


def timeline(img, n, t, W, H):
    """The strip along the bottom: a dot per round, lit up to round n, the current one glowing."""
    d = ImageDraw.Draw(img, "RGBA")
    y = H - 34
    x0, x1 = 40, W - 40
    step = (x1 - x0) / (len(ROUNDS) - 1)
    d.line([(x0, y), (x1, y)], fill=RAISED, width=4)
    d.line([(x0, y), (x0 + step * n, y)], fill=ACCENT, width=4)
    for i in range(len(ROUNDS)):
        x = x0 + step * i
        if i < n:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=ACCENT)
        elif i == n:
            r = 8 + 2 * math.sin(t * math.tau)
            d.ellipse([x - r, y - r, x + r, y + r], fill=ACCENT)
        else:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=RAISED)
        if i % 3 == 0 or i == len(ROUNDS) - 1:
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
    d.rectangle([0, H - 72, W, H], fill=GROUND + (235,))
    # The words arrive with a short ease-out, like the in-game cards.
    slide = int(10 * (1 - ease(min(1, t * 4))))
    d.text((20 + slide, H - 62), title, font=font(22, "Black"), fill=INK)
    d.text((20 + slide, H - 32), sub, font=font(14, "Medium"), fill=MUTED)
    # Where in the night we are: a dot per step, the ones done in amber.
    for i in range(len(STEPS)):
        x = W - 22 - (len(STEPS) - 1 - i) * 16
        d.ellipse([x - 4, H - 40, x + 4, H - 32], fill=ACCENT if i < int(n) else RAISED)
    d.text((W - 12, 12), "illustration from the game's files, not an engine capture", font=font(11, "Medium"), fill=(225, 216, 204, 210), anchor="ra")


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
    k = ease(min(1, t))
    rise = int(12 * (1 - k))
    alpha = int(240 * k)
    x0, w = W // 2 - 270, 540
    lines, cur = [], ""
    for w_ in text_.split():
        trial = (cur + " " + w_).strip()
        if d.textlength(trial, font=font(14, "Medium")) > w - 32:
            lines.append(cur)
            cur = w_
        else:
            cur = trial
    lines.append(cur)
    h = 44 + 20 * len(lines) + 30
    y0 = H - 40 - h + rise
    # A note pinned up for you (Handbook.cs): a sheet with a shadow and a red pin at the top.
    d.rectangle([x0 + 1, y0 + 3, x0 + w + 1, y0 + h + 3], fill=(0, 0, 0, int(alpha * 0.4)))
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=SURFACE + (alpha,))
    d.ellipse([x0 + w // 2 - 7, y0 - 5, x0 + w // 2 + 7, y0 + 9], fill=ACCENT + (alpha,))
    d.text((x0 + 16, y0 + 12), title, font=font(18, "Black"), fill=INK + (alpha,))
    for i, line_ in enumerate(lines):
        d.text((x0 + 16, y0 + 42 + 20 * i), line_, font=font(14, "Medium"), fill=INK + (alpha,))
    d.text((x0 + 16, y0 + h - 24), "F1 opens the whole handbook", font=font(12, "Medium"), fill=MUTED + (alpha,))
    d.rectangle([x0 + w - 100, y0 + 10, x0 + w - 16, y0 + 38], fill=RAISED + (alpha,))
    d.text((x0 + w - 58, y0 + 24), "Got it", font=font(13, "Bold"), fill=INK + (alpha,), anchor="mm")


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
            hint_card(f, title, text_, (i + 1) / 2)
            d = ImageDraw.Draw(f, "RGBA")
            d.text((W - 12, 12), "illustration of UI/Handbook.cs, not an engine capture", font=font(10, "Medium"), fill=(220, 210, 240, 210), anchor="ra")
            frames.append(f)
            durations.append(160)
        durations[-1] = 1500
    save_gif(frames, durations, "handbook.gif", colors=220)


# ---------------------------------------------------------------------------
# hud-refresh.png / hud-board.png: the interface drawn from the UITheme tokens
# ---------------------------------------------------------------------------
def ui_canvas(bg_name, darken=0.7, ss=2):
    """A 1280 x 720 frame (what a 720p screen shows at UITheme scale 0.8) over a darkened render,
    drawn at twice the size and scaled down at the end so string and pins come out smooth."""
    bg = Image.open(os.path.join(ROOT, "Reference renders", bg_name)).convert("RGB")
    # The renders carry a caption at the top and bottom: crop them off.
    bg = bg.crop((0, 40, bg.width, bg.height - 72)).resize((1280 * ss, 720 * ss), Image.LANCZOS)
    return ImageEnhance.Brightness(bg).enhance(darken)


class UI:
    """Draws in UITheme points (scale 0.8, as on a 720p screen), supersampled."""
    SS = 2
    K = 0.8 * SS
    W, H = 1280 / 0.8, 720 / 0.8

    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")

    def box(self, x, y, w, h, fill=GROUND + (242,)):
        k = self.K
        self.d.rectangle([x * k, y * k, (x + w) * k, (y + h) * k], fill=fill)

    def f(self, size, weight):
        return font(round(size * self.K * 1.02), weight)

    def text(self, x, y, s, size=15, weight="Medium", fill=INK, anchor="la"):
        self.d.text((x * self.K, y * self.K), s, font=self.f(size, weight), fill=fill, anchor=anchor)

    def width(self, s, size=15, weight="Medium"):
        return self.d.textlength(s, font=self.f(size, weight)) / self.K

    def wrap(self, s, size, weight, w):
        lines, cur = [], ""
        for word in s.split():
            trial = (cur + " " + word).strip()
            if cur and self.width(trial, size, weight) > w:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        return lines + ([cur] if cur else [])

    def para(self, x, y, s, size, weight, fill, w, lead=1.4):
        lines = self.wrap(s, size, weight, w)
        for i, line in enumerate(lines):
            self.text(x, y + i * size * lead, line, size, weight, fill)
        return len(lines) * size * lead

    def meter(self, x, y, w, frac, fill):
        self.box(x, y, w, 8, RAISED + (255,))
        self.box(x, y, w * frac, 8, fill + (255,))

    def pin(self, x, y, size=14, fill=ACCENT):
        k, r = self.K, size / 2
        self.d.ellipse([(x - r + 1) * k, (y - r + 2) * k, (x + r + 1) * k, (y + r + 2) * k], fill=(0, 0, 0, 90))
        self.d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=fill + (255,))
        self.d.ellipse([(x - r * 0.45) * k, (y - r * 0.6) * k, (x - r * 0.05) * k, (y - r * 0.2) * k], fill=(255, 255, 255, 70))

    def string(self, a, b, alpha=230, width=2.0):
        """UITheme.RedString: a quadratic sag from pin to pin."""
        length = math.dist(a, b)
        c = ((a[0] + b[0]) / 2, max(a[1], b[1]) + min(40, length * 0.12))
        pts = []
        for i in range(25):
            t = i / 24
            pts.append((((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0]) * self.K,
                        ((1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]) * self.K))
        self.d.line(pts, fill=ACCENT + (alpha,), width=round(width * self.K), joint="curve")

    def cork(self, x, y, w, h):
        self.box(x, y, w, h, CORK + (250,))
        k = self.K
        noise = Image.effect_noise((round(w * k), round(h * k)), 40).point(lambda v: max(0, min(255, (v - 128) * 3 + 128)))
        dark = Image.new("RGBA", noise.size, (0, 0, 0, 0))
        dark.putalpha(noise.point(lambda v: max(0, 128 - v) // 3))
        self.img.paste(Image.new("RGB", noise.size, (0, 0, 0)), (round(x * k), round(y * k)), dark)

    def done(self, name, note):
        img = self.img.resize((1280, 720), Image.LANCZOS)
        label_mock(img, note)
        img.save(os.path.join(OUT, name), optimize=True)
        print("  " + name)


def label_mock(img, text_):
    d = ImageDraw.Draw(img, "RGBA")
    d.text((img.width - 10, img.height - 8), text_, font=font(11, "Medium"), fill=(225, 216, 204, 200), anchor="rb")


MOCK_NOTE = "mockup drawn from UITheme.cs tokens at 720p, not an engine capture"


def make_hud():
    # The play view: phase bar, minimap, your panel, a toast and a hint card pinned up.
    img = ui_canvas("01-PembertonCottage-outside.png", 0.72)
    ui = UI(img)
    W, H, E = ui.W, ui.H, 16
    bw = 680
    bx = W / 2 - bw / 2
    ui.box(bx, E, bw, 82)
    ui.text(bx + 16, E + 8, "Investigation · 10:40 PM", 19, "Bold")
    ui.text(bx + bw - 16, E + 8, "7:42", 19, "Bold", INK, "ra")
    ui.text(bx + 16, E + 38, "Mask in play: the Headless Horseman. Who is wearing it?", 13, "Medium", MUTED)
    ui.text(bx + 16, E + 57, "Clues 2 (accuse at 2) · Accusations 2 · Alibi checks 1", 13, "Medium", MUTED)
    # Minimap, top right.
    town = Image.open(os.path.join(OUT, "town-map.png")).convert("RGB")
    side = round(190 * ui.K)
    mini = town.crop((220, 520, 520, 820)).resize((side, side))
    img.paste(mini, (round((W - E - 190) * ui.K), round(E * ui.K)))
    ui.pin(W - E - 95, E + 95, 10, ACCENT)
    ui.text(W - E - 95, E + 198, "Pemberton Cottage", 13, "Medium", MUTED, "ma")
    ui.text(W - E - 95, E + 216, "M opens the map", 13, "Medium", MUTED, "ma")
    # Your panel, bottom left.
    py = H - E - 200
    ui.box(E, py, 340, 200)
    ui.text(E + 16, py + 10, "Sleuth", 19, "Bold")
    ui.text(E + 16 + ui.width("Sleuth", 19, "Bold"), py + 10, "  ·  Kitchen", 19, "Bold", MUTED)
    fear = tuple(round(MUTED[i] + (ACCENT[i] - MUTED[i]) * 0.62) for i in range(3))
    for j, (lab, frac, col, note) in enumerate((("Fear", 0.62, fear, "62%"), ("Battery", 0.8, INK, "80%"))):
        y = py + 50 + j * 28
        ui.text(E + 16, y, lab, 15, "Medium", MUTED)
        ui.meter(E + 84, y + 7, 180, frac, col)
        ui.text(E + 276, y, note, 15, "Medium")
    ui.text(E + 16, py + 108, "Panics 1 of 3", 13, "Medium", MUTED)
    ui.text(E + 16, py + 130, "Clue sense: something is 4 m away", 15)
    ui.text(E + 16, py + 160, "E", 19, "SemiBold")
    ui.text(E + 40, py + 158, "Look at the gold locket", 19, "Bold")
    # A toast, bottom right.
    tw, th = 380, 58
    ui.box(W - E - tw, H - E - 36 - th, tw, th)
    ui.text(W - E - tw + 14, H - E - 36 - th + 10, "Clue found in the Parlour: a gold locket", 15)
    ui.text(W - E - tw + 14, H - E - 36 - th + 31, "Fits Daisy Pemberton and Leonard Crisp", 15, "Medium", MUTED)
    # A hint card, bottom centre: a note pinned up for you.
    cw, ch = 560, 118
    cx, cy = W / 2 - cw / 2, H - 44 - ch
    ui.box(cx + 1, cy + 3, cw, ch, (0, 0, 0, 100))
    ui.box(cx, cy, cw, ch, SURFACE + (255,))
    ui.pin(cx + cw / 2, cy + 2)
    ui.text(cx + 16, cy + 12, "The Suspect Board", 19, "Bold")
    ui.para(cx + 16, cy + 42, "You found a clue. Press Tab to see who it fits, and cross off anyone it rules out.", 15, "Medium", INK, cw - 140)
    ui.text(cx + 16, cy + ch - 26, "F1 opens the whole handbook", 13, "Medium", MUTED)
    ui.box(cx + cw - 104, cy + 10, 88, 30, RAISED + (255,))
    ui.text(cx + cw - 60, cy + 25, "Got it", 14, "SemiBold", INK, "mm")
    ui.box(W / 2 - 2, H / 2 - 2, 4, 4, (255, 255, 255, 220))
    ui.done("hud-refresh.png", MOCK_NOTE)

    # The Suspect Board, laid out the way GameHUD.DrawBoard does it.
    img = ui_canvas("02-PembertonCottage-inside.png", 0.5)
    ui = UI(img)
    ui.box(0, 0, W, H, (0, 0, 0, 184))
    pw = min(1120, W - 64)
    px, py, pad = W / 2 - pw / 2, 32, 24
    ui.cork(px, py, pw, H - 64)
    ui.text(px + pad, py + 14, "Suspect Board", 30, "Black")
    ui.text(px + pw - pad, py + 26, "Arrows pick a card · H hunch · X cross off · C alibi · A accuse · Tab closes", 13, "Medium", MUTED, "ra")
    ui.text(px + pad, py + 64, "Every clue so far fits Daisy Pemberton and nobody else (unless one was planted).", 15, "Medium", MUTED)
    top = py + 96 + 8
    clues = [("Spare key", "8:40 PM, Hallway", 4), ("Gold locket", "9:15 PM, Parlour", 6)]
    tags = [(px + pad + i * (236 + 24) + 14, top + 31) for i in range(len(clues))]
    inner = pw - 2 * pad - 14
    cw = (inner - 3 * 24) / 4
    ctop = top + 62 + 48
    cards = [(px + pad + i * (cw + 24), ctop, cw, 372) for i in range(4)]
    suspects = SUSPECTS_MOCK
    # String first, so the paper covers it and it comes out at the pins.
    for (tx, ty), (_, _, trait) in zip(tags, clues):
        for (x, y, w_, _), s in zip(cards, suspects):
            if trait in s[5]:
                ui.string((tx, ty), (x + w_ / 2, y + 2), 80 if s[7] else 235)
    for i, (name, stamp, _) in enumerate(clues):
        x = px + pad + i * (236 + 24)
        ui.box(x, top, 236, 62, TAGWASH + (255,))
        ui.pin(x + 14, top + 31, 12, ACCENT)
        ui.pin(x + 14, top + 31, 7, CORK)
        ui.text(x + 30, top + 8, name, 19, "Bold")
        ui.text(x + 30, top + 36, stamp, 13, "Medium", MUTED)

    ny = ctop + 372 + 32
    for i, (rect, suspect) in enumerate(zip(cards, suspects)):
        if i == 1:  # the card picked with the arrow keys: UITheme.Outline, 3 points out, 2 thick
            x, y, w_, h_ = rect
            for bx, by, bw, bh in ((x - 5, y - 5, w_ + 10, 2), (x - 5, y + h_ + 3, w_ + 10, 2), (x - 5, y - 5, 2, h_ + 10), (x + w_ + 3, y - 5, 2, h_ + 10)):
                ui.box(bx, by, bw, bh, INK + (255,))
        draw_mock_card(ui, rect, suspect)
    ui.box(px + pad, ny, inner, H - 32 - ny - 12, SURFACE + (255,))
    ui.text(px + pad + 16, ny + 16, "What people said", 15, "SemiBold")
    ui.text(px + pad + 16, ny + 38, "9:02 PM  Hank Moody (saw the Haunter up close): \"Whoever it was had pink glitter all down one sleeve.\"", 15)
    ui.done("hud-board.png", MOCK_NOTE)


# The Missing Harvest Lantern, two clues in: Daisy fits both, Beatrice's alibi held and she's crossed off.
# (name, job, bio, alibi, alibi held, which of the two clues fit, your hunch, crossed off)
SUSPECTS_MOCK = [
    ("Hank Moody", "Handyman", "Has been 'fixing' Mrs. Pemberton's shed since June and charges by the hour.",
     "Says he was fixing the lock on the Garden Shed, then went home with a sore back.", False, {4}, False, False),
    ("Daisy Pemberton", "Granddaughter", "Wants the cottage for herself, and Grandma won't move out while the teapot behaves.",
     "Claims she was at the Diner in town with friends all evening.", False, {4, 6}, True, False),
    ("Leonard Crisp", "Estate agent", "Already has a buyer lined up for a 'charming, slightly haunted' cottage.",
     "Insists he was showing a house on Elm Street.", False, {6}, False, False),
    ("Beatrice Hollis", "Next-door neighbour", "Runs the bake-off club and has wanted that prize-winning garden for years.",
     "Says she was icing cupcakes in Mrs. Pemberton's Kitchen, as a favour.", True, set(), False, True),
]


def draw_mock_card(ui, rect, suspect):
    """One pinned suspect card, as GameHUD.DrawSuspectCard draws it."""
    x, y, w_, h_ = rect
    name, job, bio, alibi, held, fits, hunch, crossed = suspect
    ui.box(x + 1, y + 3, w_, h_, (0, 0, 0, 90))
    ui.box(x, y, w_, h_, SURFACE + (255,))
    tx, tw_ = x + 16, w_ - 32
    ui.text(tx, y + 14, name, 20, "Bold", FAINT if crossed else INK)
    if crossed:  # UITheme.Struck: a real red line through the name
        k = ui.K
        ui.d.rectangle([(tx - 2) * k, (y + 27) * k, (tx + ui.width(name, 20, "Bold") + 2) * k, (y + 29.5) * k], fill=ACCENT)
    ui.text(tx, y + 44, job, 13, "Medium", MUTED)
    yy = y + 72
    yy += ui.para(tx, yy, bio, 13 if crossed else 15, "Medium", MUTED, tw_) + 8
    yy += ui.para(tx, yy, "8:00 PM, on arrival: " + alibi, 15, "Medium", INK, tw_)
    if held:
        ui.text(tx, yy, "It holds up.", 15, "Medium", GREEN)
        yy += 21
    yy += 8
    line = {2: "Fits every clue", 0: "Fits none of the clues"}.get(len(fits), "Fits 1 of 2 clues")
    ui.text(tx, yy, line + (" · your hunch" if hunch else ""), 15, "SemiBold", ACCENT)
    by = y + h_ - 16 - 30 * 2 - 8
    half = (tw_ - 8) / 2
    for j, lab in enumerate(("Drop hunch" if hunch else "Hunch", "Put back" if crossed else "Cross off")):
        ui.box(tx + j * (half + 8), by, half, 30, RAISED + (255,))
        ui.text(tx + j * (half + 8) + half / 2, by + 15, lab, 14, "SemiBold", INK, "mm")
    ui.box(tx, by + 38, tw_, 30, RAISED + (255,))
    ui.text(tx + tw_ / 2, by + 53, "Accuse", 14, "SemiBold", FAINT if crossed else ACCENT, "mm")
    ui.pin(x + w_ / 2, y + 2)


JOBS = {"hud": make_hud, "tracker": make_tracker, "table": make_readme_table, "handbook": make_handbook, "rounds": make_rounds, "loop": make_loop, "cast": make_cast}

if __name__ == "__main__":
    for job in sys.argv[1:] or list(JOBS):
        print(job)
        JOBS[job]()
