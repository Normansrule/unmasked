#!/usr/bin/env python3
"""
Bring free CC0 models and sounds into the game (round 40).

Drop downloaded packs (zips or folders) into "Unmasked Game/Incoming", for example Kenney's
Halloween Kit or the OpenGameArt CC0 sounds library, then run:

    python3 tools/import_incoming.py           # shows what it would do
    python3 tools/import_incoming.py --apply   # copies the files in

What it does:
  * unzips any .zip in Incoming/ (into Incoming/_unzipped/<name>/)
  * only takes files from a pack whose licence file says CC0 / public domain (Kenney packs ship
    a License.txt that does), or a pack it knows (KNOWN below, e.g. Arno Faure's Free SFX Package,
    CC BY 4.0, credited in CREDITS.md). A pack without either is listed and skipped; if you
    checked its page yourself, add  --trust "<folder name>"  or  --trust "<folder name>=<licence>"
    to take it anyway.
  * matches sounds to the game's own sound names by keywords in the file name (door + slam ->
    door_slam, crow, owl, thunder, footsteps...) and copies the best match for each to
    Assets/Unmasked/Resources/Sounds/CC0/<name>.<ext>. Sfx.cs plays those in place of the
    built-in synthesized ones; delete the file to get the old sound back.
  * matches .fbx/.obj models to decor props (pumpkin, jack-o'-lantern, gravestones, cauldron,
    crow, scarecrow, lantern, haybale, candle, skeleton, bench...) and copies them to
    Assets/Unmasked/Resources/Models/CC0/<prop>.<ext>. When the town is built
    (Unmasked > Build Hollow Creek), ManorBuilder uses the model instead of the shape-built prop,
    scaled to the same height.
  * writes Assets/Unmasked/Resources/CC0/CREDITS.md: every file used, where it came from and
    its licence. CC0 needs no credit (CC BY packs do, and get it there); saying thanks keeps things traceable.

Nothing is sent anywhere and nothing outside Incoming/ and those three folders is touched.
"""
import argparse
import os
import re
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCOMING = os.path.join(ROOT, "Incoming")
RES = os.path.join(ROOT, "Assets", "Unmasked", "Resources")
SOUND_OUT = os.path.join(RES, "Sounds", "CC0")
MODEL_OUT = os.path.join(RES, "Models", "CC0")
CREDITS = os.path.join(RES, "CC0", "CREDITS.md")

SOUND_EXT = (".wav", ".ogg", ".mp3")
MODEL_EXT = (".fbx", ".obj")

# game sound name -> (words that must all appear, words that score extra). Order is priority.
SOUNDS = {
    "door_slam": (["door"], ["slam", "close", "shut", "bang"]),
    "creak": (["creak"], ["door", "wood", "floor"]),
    "knock": (["knock"], ["door", "wood"]),
    "crow": (["crow"], ["caw", "bird"]),
    "owl": (["owl"], ["hoot"]),
    "thunder": (["thunder"], ["storm"]),
    "rain": (["rain"], ["loop"]),
    "wind": (["wind"], ["howl", "loop"]),
    "crickets": (["cricket"], ["night"]),
    "heartbeat": (["heart"], ["beat"]),
    "ghost_moan": (["ghost"], ["moan", "breath", "voice"]),
    "banshee_wail": (["scream"], ["female", "wail"]),
    "eek": (["scream"], ["short", "eek"]),
    "hoofbeats": (["horse"], ["gallop", "hoof"]),
    "rattle": (["chain"], ["rattle"]),
    "whoosh": (["whoosh"], ["swish", "swing"]),
    "clue_chime": (["chime"], ["bell", "ui", "pickup"]),
    "wisp_chime": (["magic"], ["sparkle", "chime", "spell"]),
    "music_box": (["music", "box"], []),
    "van_engine": (["engine"], ["car", "idle", "loop"]),
    "power_down": (["power"], ["down", "off"]),
    "trap_sting": (["sting"], ["horror", "hit"]),
    "pumpkin_burst": (["squish"], ["splat", "burst"]),
    "buzz": (["buzz"], ["electric", "hum"]),
    "hex": (["spell"], ["curse", "dark"]),
    "drone": (["drone"], ["ambient", "dark", "loop"]),
}

# decor prop id -> (words that must all appear, words that score extra)
MODELS = {
    "jack": (["pumpkin", "carv"], ["lantern", "face"]),
    "jack_grin": (["pumpkin", "carv"], ["grin", "smile"]),
    "jack_scary": (["pumpkin", "carv"], ["scary", "evil"]),
    "pumpkin": (["pumpkin"], ["plain", "orange", "small"]),
    "pumpkin_stack": (["pumpkin"], ["stack", "pile", "group"]),
    "tomb_cross": (["grave"], ["cross"]),
    "tomb_round": (["grave"], ["round", "stone", "tomb"]),
    "cauldron": (["cauldron"], ["pot"]),
    "crow": (["crow"], ["bird", "raven"]),
    "scarecrow": (["scarecrow"], []),
    "lantern": (["lantern"], ["hanging", "light"]),
    "haybale": (["hay"], ["bale"]),
    "candle": (["candle"], ["single", "lit"]),
    "skeleton": (["skeleton"], ["body"]),
    "bench": (["bench"], ["wood"]),
    "streetlamp": (["lamp"], ["street", "post"]),
    "trunk": (["chest"], ["trunk", "wood"]),
    "cat": (["cat"], ["black"]),
    "spider": (["spider"], []),
}

# packs whose licence is on their web page rather than in the download: folder-name pattern -> licence
KNOWN = {
    r"free.?sfx": "CC BY 4.0, Free SFX Package by Arno Faure (arnofaure.github.io/free-sfx), thank you",
}

LICENCE_NAMES = re.compile(r"(licen[cs]e|copying|readme)[^/]*\.(txt|md)$", re.I)
CC0_WORDS = re.compile(r"\bCC0\b|creative ?commons zero|public domain|CC-?0", re.I)


SPELLINGS = {"woosh": "whoosh", "swoosh": "whoosh"}


def words(path):
    name = os.path.splitext(os.path.basename(path))[0].lower()
    parent = os.path.basename(os.path.dirname(path)).lower()
    w = set(re.split(r"[^a-z0-9]+", name + " " + parent)) - {""}
    return w | {SPELLINGS[x] for x in w if x in SPELLINGS}


def best(table, files, used):
    """For each key, the file with every required word and the most extra words (shortest name breaks ties)."""
    picks = {}
    for key, (need, extra) in table.items():
        cands = []
        for f in files:
            if f in used:
                continue
            w = words(f)
            if all(any(x.startswith(n) for x in w) for n in need):
                score = sum(any(x.startswith(e) for x in w) for e in extra)
                cands.append((-score, len(os.path.basename(f)), f))
        if cands:
            f = sorted(cands)[0][2]
            picks[key] = f
            used.add(f)
    return picks


def packs():
    """Top-level packs in Incoming/: folders, plus zips unzipped into _unzipped/."""
    out = []
    if not os.path.isdir(INCOMING):
        return out
    unz = os.path.join(INCOMING, "_unzipped")
    for entry in sorted(os.listdir(INCOMING)):
        full = os.path.join(INCOMING, entry)
        if entry.startswith("_") or entry.startswith("."):
            continue
        if entry.lower().endswith(".zip"):
            dest = os.path.join(unz, os.path.splitext(entry)[0])
            if not os.path.isdir(dest):
                with zipfile.ZipFile(full) as z:
                    for m in z.namelist():  # no paths that climb out of the folder
                        if m.startswith("/") or ".." in m.split("/"):
                            raise SystemExit(f"{entry}: refusing a zip with an unsafe path ({m})")
                    z.extractall(dest)
            out.append(dest)
        elif os.path.isdir(full):
            out.append(full)
    return out


def licence_of(pack):
    for d, _, files in os.walk(pack):
        for f in files:
            if LICENCE_NAMES.search(f):
                try:
                    text = open(os.path.join(d, f), encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                if CC0_WORDS.search(text):
                    return "CC0 (" + os.path.relpath(os.path.join(d, f), pack) + ")"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="copy the files (default: just show the plan)")
    ap.add_argument("--trust", action="append", default=[], help='a pack you checked yourself: "<folder name>" (CC0) or "<folder name>=<licence>"')
    a = ap.parse_args()

    found = packs()
    if not found:
        print(f"Nothing in {INCOMING}. Put downloaded packs (zips or folders) there and run this again.")
        return 0
    trusted = dict((t.split("=", 1) + ["CC0"])[:2] for t in a.trust)
    sounds, models, source = [], [], {}
    for pack in found:
        name = os.path.basename(pack)
        known = next((l for pat, l in KNOWN.items() if re.search(pat, name, re.I)), None)
        lic = licence_of(pack) or known or (f"{trusted[name]} (you checked it: --trust)" if name in trusted else None)
        if not lic:
            print(f"  skipped {name}: no licence file saying CC0. Check its page, then add --trust \"{name}\".")
            continue
        n = 0
        for d, _, files in os.walk(pack):
            for f in files:
                full = os.path.join(d, f)
                if f.lower().endswith(SOUND_EXT):
                    sounds.append(full); n += 1
                elif f.lower().endswith(MODEL_EXT):
                    models.append(full); n += 1
                source[full] = (name, lic)
        print(f"  {name}: {lic}, {n} sounds and models")

    used = set()
    s_pick = best(SOUNDS, sounds, used)
    m_pick = best(MODELS, models, used)
    print(f"\nSounds ({len(s_pick)} of {len(SOUNDS)} matched):")
    for k, f in s_pick.items():
        print(f"  {k:14s} <- {os.path.relpath(f, INCOMING)}")
    print(f"\nModels ({len(m_pick)} of {len(MODELS)} matched):")
    for k, f in m_pick.items():
        print(f"  {k:14s} <- {os.path.relpath(f, INCOMING)}")
    if not a.apply:
        print("\nNothing copied yet. Run again with --apply to bring these in.")
        return 0

    rows = []
    for out_dir, picks, kind in ((SOUND_OUT, s_pick, "sound"), (MODEL_OUT, m_pick, "model")):
        os.makedirs(out_dir, exist_ok=True)
        for k, f in picks.items():
            ext = os.path.splitext(f)[1].lower()
            for old in os.listdir(out_dir):  # one file per name
                if os.path.splitext(old)[0] == k and not old.endswith(".meta"):
                    os.remove(os.path.join(out_dir, old))
            shutil.copy2(f, os.path.join(out_dir, k + ext))
            pack, lic = source[f]
            rows.append(f"| {kind} | `{k}` | {pack} / `{os.path.relpath(f, os.path.join(INCOMING))}` | {lic} |")
    os.makedirs(os.path.dirname(CREDITS), exist_ok=True)
    with open(CREDITS, "w", encoding="utf-8") as fh:
        fh.write("# Free assets in the game\n\nBrought in by `tools/import_incoming.py`. Thanks to everyone who gives their work away.\n\n")
        fh.write("| Kind | Used as | From | Licence |\n|---|---|---|---|\n" + "\n".join(rows) + "\n")
    print(f"\nCopied {len(rows)} files. Credits: {os.path.relpath(CREDITS, ROOT)}. Rebuild the town in Unity to see the models.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
