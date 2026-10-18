#!/usr/bin/env python3
"""
Checks that every case in Assets/Unmasked/Scripts/Mystery/Cases.cs can actually be solved, without
opening Unity. For each case it checks:

  * the deduction works: with the trait table in Cases.cs, any two of the culprit's three traits
    point at exactly one suspect, for every possible culprit (so two true clues always settle it);
  * every list is complete: 4 suspects, 4 motives, 8 trait names, 8 clues with different ids;
  * every alibi can be checked: the alibi room is a real room in that house or in town
    (MysteryGameManager.HandleAlibiCheck needs a Solver standing in a room with that name);
  * case ids are unique and every return visit has a first case before it.

    python3 tools/casecheck/casecheck.py        # prints a table; exit code 1 if anything fails
"""
import itertools
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASES = os.path.join(ROOT, "Assets", "Unmasked", "Scripts", "Mystery", "Cases.cs")
RES = os.path.join(ROOT, "Assets", "Unmasked", "Resources")

STR = r'"((?:[^"\\]|\\.)*)"'


def strings(text):
    return [m.replace('\\"', '"') for m in re.findall(STR, text)]


def slot_traits(src):
    """The SlotTraits table: which Trait flags each slot has, as sets of names."""
    block = re.search(r"SlotTraits\s*=\s*\{(.*?)\};", src, re.S).group(1)
    rows = [re.findall(r"Trait\.(\w+)", line) for line in block.split("\n") if "Trait." in line]
    bits = re.findall(r"Trait\.(\w+)", re.search(r"Bits\s*=\s*\{(.*?)\};", src, re.S).group(1))
    return [set(r) for r in rows], bits


def specs(src):
    body = src[src.index("public static readonly Spec[] All"):]
    out = []
    for block in re.split(r"\n\s*new Spec\s*\n", body)[1:]:
        get = lambda key: (re.search(key + r'\s*=\s*' + STR, block) or [None, None])[1]
        visit = re.search(r"Visit\s*=\s*(\d+)", block)
        suspects = [strings(m) for m in re.findall(r"\bS\((.*?)\),?\s*\n", block, re.S)]
        clues = [strings(m) for m in re.findall(r"\bC\((.*?)\),?\s*\n", block, re.S)]
        trait_names = strings(re.search(r"TraitNames\s*=\s*new\[\]\s*\{(.*?)\}", block, re.S).group(1))
        motives = re.search(r"Motives\s*=\s*new\[\]\s*\{(.*?)\n\s*\}", block, re.S)
        out.append({
            "house": get("HouseId"), "name": get("CaseName"), "visit": int(visit.group(1)) if visit else 1,
            "suspects": suspects, "clues": clues, "traits": trait_names,
            "motives": strings(motives.group(1)) if motives else [],
        })
    return out


def rooms_of(house):
    path = os.path.join(RES, "BlackwoodManor.json" if house == "BlackwoodManor" else os.path.join("Houses", house + ".json"))
    with open(path) as f:
        return {r["n"] for r in json.load(f).get("rooms", [])}


def main():
    src = open(CASES, encoding="utf-8").read()
    table, bits = slot_traits(src)
    with open(os.path.join(RES, "HollowCreek.json")) as f:
        town_rooms = {r["n"] for r in json.load(f)["rooms"]}

    problems = []
    # The deduction, once for the shared trait table (every case uses it).
    for culprit, traits in enumerate(table):
        for pair in itertools.combinations(sorted(traits), 2):
            matches = [i for i, t in enumerate(table) if set(pair) <= t]
            if matches != [culprit]:
                problems.append(f"trait table: {pair} matches slots {matches}, not just slot {culprit}")
    deduction_ok = not problems

    rows, seen = [], set()
    for c in specs(src):
        cid = c["house"] + ("" if c["visit"] <= 1 else f"#{c['visit']}")
        bad = []
        if cid in seen:
            bad.append("duplicate case id")
        seen.add(cid)
        if c["visit"] > 1 and c["house"] not in seen:
            bad.append("return visit listed before its first case")
        if len(c["suspects"]) != 4:
            bad.append(f"{len(c['suspects'])} suspects")
        if len(c["motives"]) != 4:
            bad.append(f"{len(c['motives'])} motives")
        if len(c["traits"]) != len(bits):
            bad.append(f"{len(c['traits'])} trait names")
        if len(c["clues"]) != len(bits) or len({cl[0] for cl in c["clues"]}) != len(c["clues"]):
            bad.append("clues missing or ids repeated")
        rooms = rooms_of(c["house"]) | town_rooms
        unreachable = [s[4] for s in c["suspects"] if len(s) >= 5 and s[4] not in rooms]
        if unreachable:
            bad.append("alibi rooms not found: " + ", ".join(unreachable))
        rows.append((cid, c["name"], "ok" if not bad else "; ".join(bad)))
        problems += [f"{cid}: {b}" for b in bad]

    print(f"Trait table: {'any two of a culprit' + chr(39) + 's traits name exactly one suspect' if deduction_ok else 'BROKEN'}")
    w = max(len(r[0]) for r in rows)
    for cid, name, result in rows:
        print(f"  {cid:<{w}}  {name:<34} {result}")
    print(f"{len(rows)} cases, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
