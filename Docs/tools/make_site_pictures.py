#!/usr/bin/env python3
"""
Pictures of the website (site/) for the README, taken in a real browser.

    python3 Docs/tools/make_site_pictures.py

  site-hero.png, site-hero-dark.png   the front page, light and dark
  site-board.png                      a case played through to the unmasking
  site-phone.png                      phone width, light and dark side by side
  site-strings.gif                    the hero: string runs from two clues to the one suspect they share
  site-play.gif                       searching, crossing off and accusing on the Suspect Board
  site/img/share.png                  the preview picture when someone shares a link to the site

Needs Node and Playwright (npm i playwright); see site_shots.js. Serves site/ on a local port while
it runs. Run make_site_data.py first if the cases changed.
"""
import functools
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Docs", "images")


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Quiet, directory=os.path.join(ROOT, "site"))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


def gif(folder, name, width, hold_last=1800):
    times = json.load(open(os.path.join(folder, "times.json")))
    files = sorted(f for f in os.listdir(folder) if f.endswith(".png"))
    frames, durations = [], []
    for i, f in enumerate(files):
        im = Image.open(os.path.join(folder, f)).convert("RGB")
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        frames.append(im.quantize(colors=160, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
        nxt = times[i + 1] if i + 1 < len(times) else times[i] + hold_last
        durations.append(max(40, nxt - times[i]))
    frames[0].save(os.path.join(OUT, name), save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True, disposal=1)
    print(f"  {name}: {len(frames)} frames, {os.path.getsize(os.path.join(OUT, name)) // 1024} KB")


def main():
    httpd, url = serve()
    tmp = tempfile.mkdtemp(prefix="unmasked-site-")
    try:
        subprocess.run(["node", os.path.join(HERE, "site_shots.js"), url, tmp], check=True)
    finally:
        httpd.shutdown()

    for src, dst, w in (("site-hero.png", "site-hero.png", 1200), ("site-hero-dark.png", "site-hero-dark.png", 1200), ("site-board.png", "site-board.png", 1200)):
        im = Image.open(os.path.join(tmp, src)).convert("RGB")
        im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(os.path.join(OUT, dst), optimize=True)
        print("  " + dst)
    Image.open(os.path.join(tmp, "site-share.png")).convert("RGB").save(os.path.join(ROOT, "site", "img", "share.png"), optimize=True)
    print("  site/img/share.png")
    light, dark = (Image.open(os.path.join(tmp, f"site-phone-{s}.png")).convert("RGB") for s in ("light", "dark"))
    gap = 40
    both = Image.new("RGB", (light.width * 2 + gap, light.height), (136, 128, 118))
    both.paste(light, (0, 0))
    both.paste(dark, (light.width + gap, 0))
    both.resize((both.width // 2, both.height // 2), Image.LANCZOS).save(os.path.join(OUT, "site-phone.png"), optimize=True)
    print("  site-phone.png")
    gif(os.path.join(tmp, "hero"), "site-strings.gif", 640)
    gif(os.path.join(tmp, "board"), "site-play.gif", 720, 2600)


if __name__ == "__main__":
    sys.exit(main())
