"""
Round 42: Hollow Creek becomes a real small town. Twelve one-of-a-kind buildings stand among the
houses (a cinema, a bakery, the school, Town Hall with its clock tower, a hotel, a toy shop, a music
hall, an ice cream parlour, the Gazette, an apothecary, the train depot and a laundromat), and every
one of them has its own haunt to bust.

How a bust plays (Town/HauntBust.cs): walk up and you'll see three faint violet signs of the haunt
around the building (flour footprints, a stopped clock, a sock on the step). Examine all three (E)
and the ghost shows itself. Catch it three times (E when you're close) as it hops away, and it's
busted: the sheet comes off and the haunt turns out to be something silly and sweet. +20 candy, the
building lights up warm, and the Club Book's "Haunt Busters" chapter counts it.

make_town.py calls claim() after cutting the street parcels (it takes twelve good plots near the
middle of town, at most two to a street) and build() after the houses, then saves the list as
HollowCreek.json "haunts".
"""
import math

# id, building name, sign colour, ghost name, ghost colour, blurb, twist,
# three signs (name, what you read), kind of building
HAUNTS = [
    ("cinema", "The Bijou", "ff5a7a", "The Projectionist", "c8d0ff",
     "The late show at the Bijou starts by itself every night at 13 o'clock.",
     "It was Mr. Pomeroy's cat, asleep on the projector button under the dust sheet. The late show is cancelled.",
     [("Flickering poster", "The poster in the frame changes every time you blink. Right now it's a film nobody ever made."),
      ("Torn ticket", "A ticket stub for row Z, seat 13. The Bijou only has twelve rows."),
      ("Spilled popcorn", "A trail of popcorn leads up the steps and stops at the door, as if someone was eating it on the way in.")]),
    ("bakery", "Crumb & Co. Bakery", "ffd08a", "The Flour Phantom", "fff4e0",
     "Every morning the bread is already baked, and nobody has a key.",
     "Under the sheet: a very tidy raccoon in an apron. It's been baking for the bakers. They've hired it.",
     [("Floury footprints", "Small floury footprints go round and round the step. Whoever made them had four feet."),
      ("Risen dough", "A bowl of dough on the sill has risen twice its size and is still going."),
      ("Rolling pin", "A rolling pin, rocking back and forth by itself, very gently.")]),
    ("school", "Hollow Creek School", "ffe08a", "The Hall Monitor", "d8f0ff",
     "The school bell rings at midnight and a stern voice asks for your hall pass.",
     "It was the old janitor's wind-up bell, stuck on a timer since 1962. He's very pleased to have it back.",
     [("Chalk writing", "On the wall, in neat chalk: I WILL NOT HAUNT IN THE HALLS, a hundred times."),
      ("Hall pass", "A wooden hall pass hanging from the door handle. It's warm."),
      ("Ringing bell", "The bell in the little tower swings, but makes no sound until you look away.")]),
    ("townhall", "Town Hall", "ffe7a0", "The Clockwinder", "e8e0c8",
     "The clock on Town Hall has started striking thirteen.",
     "Behind the sheet: Mayor Beaumont's nephew, practising for the Halloween pageant. He also fixed the clock.",
     [("Stopped clock", "The clock face says 13:13. The hands won't move, even when you push them."),
      ("Brass key", "A big brass key on the step, the kind that winds a tower clock."),
      ("Ledger page", "A page from the town ledger: \"Paid to the Clockwinder: one hour, every night, forever.\"")]),
    ("hotel", "The Grand Raven Hotel", "c8a0ff", "The Night Porter", "e0d8ff",
     "Bags carry themselves upstairs at the Grand Raven, and Room 13 is always booked.",
     "It was three crows on a luggage trolley, rolling it about for the shiny buttons. The porter gave them a room.",
     [("Room key 13", "A heavy key with a tag: ROOM 13. The Grand Raven goes from 12 to 14."),
      ("Service bell", "The bell on the stand dings once as you get near, and once more as you leave."),
      ("Lone suitcase", "A suitcase with travel stickers from places that aren't on any map.")]),
    ("toyshop", "Tick-Tock Toys", "8affc8", "The Wind-up Twins", "ffe0f0",
     "The toys in the window rearrange themselves every night into a little parade.",
     "Two toy soldiers, wound up so tight they marched for a week. A turn of the key and they finally sat down.",
     [("Marching soldier", "A tin soldier marches in a circle on the windowsill, then salutes you."),
      ("Jack-in-the-box", "The jack-in-the-box is open. The jack is missing."),
      ("Music box", "A music box plays a tune you almost know, then stops on the wrong note.")]),
    ("musichall", "The Gloaming Music Hall", "ff9ad0", "The Diva", "ffd8f0",
     "A voice sings the last song of the night in the empty Music Hall.",
     "It was Old Nell Thistle, rehearsing in secret for her comeback. She's on next Friday. Bring candy.",
     [("Single rose", "A red rose on the step, still wet with dew. It's October."),
      ("Sheet music", "Sheet music for a song called \"Unmask Me Gently\". Someone has written ENCORE in the margin."),
      ("Spotlight", "A small spotlight points at the door and follows you a little as you move.")]),
    ("creamery", "Moon Pie Creamery", "a0e8ff", "The Sundae Specter", "e8f8ff",
     "The freezer opens by itself and the cherries keep going missing.",
     "A very small ghost-shaped puppy with a sweet tooth, wearing a napkin. The Creamery adopted her.",
     [("Melted drips", "Drips of strawberry ice cream lead to the side wall and go straight up it."),
      ("Cold spot", "Stand here and your breath frosts. Step away and it's a mild October night."),
      ("Cherry stalks", "Thirteen cherry stalks, each tied in a perfect knot.")]),
    ("gazette", "The Hollow Creek Gazette", "e8e8e8", "The Typesetter", "f0f0e8",
     "Tomorrow's headlines are printed tonight, and they keep coming true.",
     "The night editor, an owl named Ink, who sees everything first from the roof. He's been made a reporter.",
     [("Tomorrow's paper", "Tomorrow's Gazette. The headline: MYSTERY CLUB BUSTS GAZETTE GHOST."),
      ("Inky handprints", "Inky prints on the wall. They're not hands, they're feathers."),
      ("Typewriter keys", "Three typewriter keys on the step: B, O and O.")]),
    ("apothecary", "Nightshade Apothecary", "9aff8a", "The Apothecary", "d8ffd0",
     "Green light glows in the jars after closing, and something bubbles.",
     "It was Doc Fennimore's firefly collection, glowing in the jars. She lets them out every night now.",
     [("Bubbling jar", "A jar on the windowsill bubbles. The label says DO NOT BUBBLE."),
      ("Green glow", "The glow in the window pulses like a slow heartbeat."),
      ("Prescription", "A prescription: \"One spoonful of moonlight, before bed.\" Signed with a skull.")]),
    ("depot", "Hollow Creek Depot", "ffb36a", "The Conductor", "f0e8d8",
     "A whistle blows on the platform at midnight, and the last train never arrives.",
     "It was the station master's kettle, whistling on a stove nobody turned off. Tea for everyone.",
     [("Old timetable", "A timetable with one train left: the 12:59 to Nowhere-in-Particular."),
      ("Lantern", "A conductor's lantern, swinging slowly, though there's no wind."),
      ("Ticket punch", "Little punched-out stars all over the bench, as if a whole trainload had their tickets checked.")]),
    ("laundry", "Spin Cycle Laundry", "8ac8ff", "The Sock Thief", "e0f0ff",
     "Every machine in the laundromat runs by itself, and nobody's socks come back in pairs.",
     "A family of mice with a very cosy nest of odd socks. They've been given the lost-and-found box to keep.",
     [("Odd sock", "One stripy sock on the step. Its partner is nowhere to be seen."),
      ("Soap bubbles", "Soap bubbles drift out from under the door and spell something, then pop."),
      ("Spinning drum", "Through the round window: a drum spinning with nothing in it.")]),
]

W, D = 13.0, 12.0  # building footprint along the street and into the plot


def _row(du0, du1, dv, y, sv, sy, hexc, n, mode="solid", shape="box"):
    """n equal pieces between du0 and du1 (for seat rows, shelves, machines)."""
    step = (du1 - du0) / n
    return [(du0 + step * (k + 0.5), dv, y, step * 0.85, sv, sy, hexc, mode, shape) for k in range(n)]


# What stands inside each haunt, in the building's own frame: du along the street from its middle,
# dv into the building from the front wall (the room runs dv 0.25..11.75, du -6.25..6.25), y the centre.
# Keep the aisle from the door (|du| < 1.2) and the ghost's last hiding spot (du 0, dv 8) clear.
S, NC, E = "solid", "nocollide", "emissive"
INSIDE = {
    "cinema": [(0, 11.6, 2.0, 9.0, 0.08, 2.6, "fff0d0", E, "box")]
              + _row(-5.6, -1.6, 3.0, 0.45, 0.6, 0.9, "8a1a2a", 4) + _row(1.6, 5.6, 3.0, 0.45, 0.6, 0.9, "8a1a2a", 4)
              + _row(-5.6, -1.6, 4.6, 0.45, 0.6, 0.9, "8a1a2a", 4) + _row(1.6, 5.6, 4.6, 0.45, 0.6, 0.9, "8a1a2a", 4)
              + _row(-5.6, -1.6, 6.2, 0.45, 0.6, 0.9, "8a1a2a", 4) + _row(1.6, 5.6, 6.2, 0.45, 0.6, 0.9, "8a1a2a", 4)
              + [(-5.2, 1.0, 0.6, 1.4, 0.8, 1.2, "c8a040", S, "box"), (-5.2, 1.0, 1.35, 0.5, 0.5, 0.4, "fff4c0", E, "sphere")],
    "bakery": [(-3.6, 3.0, 0.5, 4.6, 0.9, 1.0, "c8a070", S, "box"), (-3.6, 3.0, 1.06, 4.6, 0.95, 0.08, "f0e8d8", S, "box"),
               (-3.0, 11.2, 1.2, 3.2, 1.0, 2.4, "3a3a3a", S, "box"), (-3.0, 10.68, 1.0, 1.4, 0.06, 0.8, "ff8a3a", E, "box"),
               (4.6, 6.0, 1.0, 1.2, 2.6, 2.0, "8a5a3a", S, "box"),
               (4.2, 10.4, 0.35, 0.7, 0.7, 0.7, "e8dcc0", NC, "sphere"), (5.0, 10.8, 0.35, 0.7, 0.7, 0.7, "e8dcc0", NC, "sphere"),
               (-3.6, 3.0, 1.2, 0.6, 0.35, 0.3, "d89a4a", NC, "capsule"), (-2.4, 3.0, 1.2, 0.6, 0.35, 0.3, "d89a4a", NC, "capsule")],
    "school": [(0, 11.65, 1.8, 6.0, 0.08, 1.4, "1e3a2a", S, "box"), (0, 10.2, 0.4, 2.0, 0.9, 0.8, "8a5a3a", S, "box")]
              + _row(-5.6, -1.6, 3.0, 0.38, 0.7, 0.75, "b08a5a", 2) + _row(1.6, 5.6, 3.0, 0.38, 0.7, 0.75, "b08a5a", 2)
              + _row(-5.6, -1.6, 5.0, 0.38, 0.7, 0.75, "b08a5a", 2) + _row(1.6, 5.6, 5.0, 0.38, 0.7, 0.75, "b08a5a", 2)
              + [(5.6, 11.0, 2.6, 0.5, 0.5, 0.5, "fff0c0", E, "sphere")],
    "townhall": [(0, 10.6, 0.5, 7.0, 1.0, 1.0, "5a3a2a", S, "box"), (5.4, 11.2, 1.3, 0.8, 0.5, 2.6, "3a2418", S, "box"),
                 (5.4, 10.92, 2.1, 0.5, 0.06, 0.5, "f0e8c8", E, "cyl"), (-5.6, 11.4, 1.6, 0.9, 0.2, 1.4, "6a2a3a", S, "box")]
                 + _row(-5.6, -1.6, 4.0, 0.45, 0.6, 0.9, "6a4a2a", 3) + _row(1.6, 5.6, 4.0, 0.45, 0.6, 0.9, "6a4a2a", 3),
    "hotel": [(-3.8, 6.0, 0.6, 3.6, 1.0, 1.2, "6a2a3a", S, "box"), (-3.8, 6.0, 1.24, 3.6, 1.05, 0.08, "c8a040", S, "box"),
              (-3.8, 7.0, 1.6, 0.25, 0.25, 0.25, "ffd890", E, "sphere"), (-5.6, 11.5, 1.8, 2.0, 0.1, 1.2, "3a2418", S, "box"),
              (3.6, 3.4, 0.7, 1.4, 0.8, 1.0, "c8a040", S, "box"), (3.4, 3.4, 1.4, 0.8, 0.6, 0.5, "8a3a2a", NC, "box"),
              (4.8, 10.0, 0.9, 2.2, 3.0, 1.8, "4a3a5a", S, "box")],
    "toyshop": _row(-6.0, 6.0, 11.45, 1.3, 0.5, 2.6, "e8b0c8", 3)
               + [(-5.8, 6.0, 1.0, 0.5, 6.0, 2.0, "e8b0c8", S, "box"), (4.2, 4.0, 0.6, 1.4, 0.4, 1.2, "c88a4a", S, "box"),
                  (4.2, 4.0, 1.4, 0.5, 0.9, 0.5, "f0e8d8", NC, "sphere"), (-3.0, 3.5, 0.4, 0.8, 0.8, 0.8, "4a8ad0", NC, "sphere"),
                  (2.6, 9.6, 0.4, 0.3, 0.3, 0.8, "c83a3a", NC, "cyl"), (3.2, 9.6, 0.4, 0.3, 0.3, 0.8, "c83a3a", NC, "cyl")],
    "musichall": [(0, 10.6, 0.4, 11.4, 2.2, 0.8, "4a2a1a", S, "box"), (-5.4, 10.6, 2.1, 1.0, 2.0, 2.6, "8a1a2a", S, "box"),
                  (5.4, 10.6, 2.1, 1.0, 2.0, 2.6, "8a1a2a", S, "box"), (-3.4, 10.4, 1.3, 1.8, 1.0, 1.0, "1a1a1a", S, "box"),
                  (0, 10.0, 1.4, 0.25, 0.25, 1.2, "c8c8c8", NC, "cyl")]
                  + _row(-5.6, -1.6, 3.5, 0.45, 0.6, 0.9, "6a2a3a", 4) + _row(1.6, 5.6, 3.5, 0.45, 0.6, 0.9, "6a2a3a", 4)
                  + _row(-5.6, -1.6, 5.2, 0.45, 0.6, 0.9, "6a2a3a", 4) + _row(1.6, 5.6, 5.2, 0.45, 0.6, 0.9, "6a2a3a", 4),
    "creamery": [(-3.4, 4.0, 0.5, 4.6, 1.0, 1.0, "f0d0e0", S, "box"), (-3.4, 4.0, 1.2, 4.4, 0.9, 0.4, "8ae0f0", E, "box"),
                 (3.0, 3.2, 0.45, 0.5, 0.5, 0.9, "c8c8d0", S, "cyl"), (4.4, 3.2, 0.45, 0.5, 0.5, 0.9, "c8c8d0", S, "cyl"),
                 (3.0, 3.2, 0.95, 0.7, 0.7, 0.12, "e05a7a", S, "cyl"), (4.4, 3.2, 0.95, 0.7, 0.7, 0.12, "e05a7a", S, "cyl"),
                 (5.4, 10.8, 1.2, 0.9, 0.9, 1.2, "e8b070", S, "cyl"), (5.4, 10.8, 2.2, 1.1, 1.1, 1.0, "fff0f4", NC, "sphere"),
                 (5.4, 10.8, 2.8, 0.25, 0.25, 0.25, "d02a3a", NC, "sphere")],
    "gazette": [(4.2, 8.0, 1.2, 3.0, 2.0, 2.4, "2a2a2a", S, "box"), (4.2, 6.9, 1.6, 2.4, 0.1, 0.4, "f0ece0", E, "box"),
                (-4.4, 3.6, 0.38, 1.6, 0.8, 0.75, "8a6a4a", S, "box"), (-4.4, 6.0, 0.38, 1.6, 0.8, 0.75, "8a6a4a", S, "box"),
                (-5.4, 10.8, 0.5, 1.2, 0.9, 1.0, "f0ece0", NC, "box"), (-3.8, 10.8, 0.35, 1.2, 0.9, 0.7, "f0ece0", NC, "box")],
    "apothecary": _row(-6.0, 6.0, 11.45, 1.3, 0.4, 2.6, "3a2418", 3)
                  + _row(-5.6, 5.6, 11.2, 1.4, 0.2, 0.2, "7aff9a", 8, E, "sphere") + _row(-5.6, 5.6, 11.2, 2.2, 0.2, 0.2, "b07aff", 8, E, "sphere")
                  + [(-3.6, 5.0, 0.5, 4.0, 0.9, 1.0, "2a4a3a", S, "box"), (-3.6, 5.0, 1.2, 0.5, 0.5, 0.4, "7aff9a", E, "sphere"),
                     (4.6, 4.0, 0.6, 1.0, 1.0, 1.2, "4a3a2a", S, "cyl")],
    "depot": [(-5.6, 6.0, 1.3, 0.3, 8.0, 2.6, "6a4a2a", S, "box"), (-5.42, 6.0, 1.6, 0.06, 1.4, 0.7, "ffd890", E, "box"),
              (0, 11.6, 2.6, 0.9, 0.08, 0.9, "f0e8c8", E, "cyl")]
              + _row(1.8, 5.8, 4.0, 0.3, 0.6, 0.6, "8a5a3a", 2) + _row(1.8, 5.8, 6.0, 0.3, 0.6, 0.6, "8a5a3a", 2)
              + [(4.4, 10.4, 0.4, 1.2, 0.8, 0.8, "6a3a2a", NC, "box"), (4.4, 10.4, 1.0, 0.8, 0.6, 0.5, "3a5a6a", NC, "box")],
    "laundry": _row(1.0, 11.0, 0, 0.55, 1.0, 1.1, "e8f0f0", 6)  # washers along the left wall (du/dv swapped below)
               + [(4.6, 6.0, 0.45, 1.6, 4.0, 0.9, "c8b090", S, "box"), (4.6, 5.0, 1.0, 0.6, 0.4, 0.2, "e05a6a", NC, "box"),
                  (4.6, 7.0, 1.0, 0.6, 0.4, 0.2, "6a8ae0", NC, "box")],
}
# The laundry's washers line the left wall: turn that row from along-the-street into along-the-wall.
INSIDE["laundry"] = [(-5.6, du, y, sv, su, sy, c, m, sh) for (du, dv, y, su, sv, sy, c, m, sh) in INSIDE["laundry"][:6]] \
    + [(-5.08, du, 0.6, 0.06, 0.6, 0.6, "8ac8ff", E, "box") for (du, *_r) in INSIDE["laundry"][:6]] + INSIDE["laundry"][6:]


def claim(parcels, n=12, centre=(0.0, -20.0)):
    """Take n good parcels near the middle of town (wide and deep enough), at most two per street."""
    ok = [p for p in parcels if (p["rect"][1] - p["rect"][0] if p["axis"] == "x" else p["rect"][3] - p["rect"][2]) >= 14.0
          and (p["rect"][3] - p["rect"][2] if p["axis"] == "x" else p["rect"][1] - p["rect"][0]) >= 16.0]

    def dist(p):
        x0, x1, z0, z1 = p["rect"]
        return math.hypot((x0 + x1) / 2 - centre[0], (z0 + z1) / 2 - centre[1])

    picked, per_street = [], {}
    for p in sorted(ok, key=dist):
        if per_street.get(p["street"], 0) >= 2:
            continue
        picked.append(p)
        per_street[p["street"]] = per_street.get(p["street"], 0) + 1
        if len(picked) == n:
            break
    for p in picked:
        parcels.remove(p)
    return picked


def build(T, C, rgb, building, sites):
    out = []
    for k, (site, h) in enumerate(zip(sites, HAUNTS)):
        out.append(_one(T, C, rgb, building, site, h, k))
    return out


def _one(T, C, rgb, building, parcel, haunt, k):
    hid, name, sign_hex, ghost, ghost_hex, blurb, twist, signs = haunt
    x0, x1, z0, z1 = parcel["rect"]
    axis, side = parcel["axis"], parcel["side"]
    if axis == "x":
        u0, u1 = x0, x1
        front_v = z0 if side > 0 else z1
    else:
        u0, u1 = z0, z1
        front_v = x0 if side > 0 else x1
    uc = (u0 + u1) / 2
    vf = 4.5  # front wall, metres back from the plot's front line

    def P(u, v):
        w = front_v + side * v
        return (u, w) if axis == "x" else (w, u)

    def rect(ua, ub, va, vb):
        (xa, za), (xb, zb) = P(ua, va), P(ub, vb)
        return min(xa, xb), max(xa, xb), min(za, zb), max(za, zb)

    def at(u, v, y=0.0):
        x, z = P(u, v)
        return (x, y, z)

    def size(su, sv, sy):  # a size given along the street / into the plot
        return (su, sy, sv) if axis == "x" else (sv, sy, su)

    door = {("x", 1): "S", ("x", -1): "N", ("z", 1): "W", ("z", -1): "E"}[(axis, side)]
    ry = {"S": 180, "N": 0, "W": -90, "E": 90}[door]
    sign = rgb(sign_hex)
    n = f"Haunt{hid.capitalize()}"
    bx0, bx1, bz0, bz1 = rect(uc - W / 2, uc + W / 2, vf, vf + D)
    box = T.box

    # ---- the building itself: each one a different silhouette ----
    if hid == "cinema":
        building(n, bx0, bx1, bz0, bz1, 7.5, rgb("5a2a3a"), rgb("1e1620"), door, gable=False, sign=(name, sign))
        box(n + "Marquee", at(uc, vf - 1.2, 3.4), size(9.0, 2.4, 0.5), rgb("2a1a24"), 9, "solid", "roof")
        box(n + "MarqueeFace", at(uc, vf - 2.42, 3.4), size(8.6, 0.06, 0.8), rgb("fff0c0"), 9, "emissive", "sign")
        for i in range(14):  # bulbs round the marquee
            box(f"{n}Bulb{i}", at(uc - 4.2 + i * 0.65, vf - 2.45, 3.9), (0.16, 0.16, 0.16), rgb("ffe7a0"), 9, "emissive", "sign", shape="sphere")
        box(n + "Blade", at(uc + W / 2 - 0.4, vf - 0.5, 6.2), size(0.3, 1.0, 5.0), sign, 9, "emissive", "sign")
        T.glow(at(uc, vf - 3.5, 3.0), rgb("ffd08a"), 9, 1.0)
    elif hid == "bakery":
        building(n, bx0, bx1, bz0, bz1, 4.6, rgb("e8c8a0"), rgb("8a3a2a"), door, sign=(name, sign))
        for i in range(8):  # striped awning
            box(f"{n}Awning{i}", at(uc - 5.25 + i * 1.5, vf - 0.9, 2.9), size(1.5, 1.8, 0.12), rgb("c8303a") if i % 2 else rgb("fff4e0"), 9, "solid", "roof", r=(0, 0, 0))
        box(n + "Loaf", at(uc, vf - 0.3, 5.9), size(2.4, 0.9, 1.0), rgb("c88a4a"), 9, "solid", "sign", shape="sphere")
        box(n + "Chimney", at(uc + 4.0, vf + 8.0, 6.0), (1.0, 3.0, 1.0), C["brick"], 9, "solid", "roof")
    elif hid == "school":
        building(n, bx0, bx1, bz0, bz1, 6.4, rgb("a0503a"), rgb("2a2a3a"), door, gable=False, sign=(name, sign))
        box(n + "Belfry", at(uc, vf + 3.0, 8.0), (2.6, 3.0, 2.6), rgb("e8e0d0"), 9, "solid", "building")
        box(n + "BelfryRoof", at(uc, vf + 3.0, 10.0), (3.2, 1.0, 3.2), rgb("2a2a3a"), 9, "solid", "roof")
        box(n + "Bell", at(uc, vf + 3.0, 8.4), (1.0, 1.0, 1.0), rgb("c8a040"), 9, "solid", "sign", shape="sphere")
        box(n + "Flagpole", at(uc - 5.5, vf - 2.5, 4.0), (0.12, 8.0, 0.12), rgb("c8c8d0"), 9, "solid", "decor", shape="cyl")
        box(n + "Flag", at(uc - 5.0, vf - 2.5, 7.4), size(1.0, 0.04, 0.7), rgb("ffe08a"), 9, "nocollide", "decor")
    elif hid == "townhall":
        building(n, bx0, bx1, bz0, bz1, 7.0, rgb("d8d0c0"), rgb("3a3a48"), door, gable=False, sign=(name, sign))
        box(n + "Tower", at(uc, vf + 2.0, 10.0), (3.4, 6.0, 3.4), rgb("d8d0c0"), 9, "solid", "building")
        for i in range(4):
            s = 3.8 * (1 - i / 4)
            box(f"{n}Spire{i}", at(uc, vf + 2.0, 13.4 + i * 0.7), (s, 0.7, s), rgb("3a5a4a"), 9, "solid", "roof")
        box(n + "Clock", at(uc, vf + 0.25, 11.0), size(2.4, 0.12, 2.4), rgb("fff4d8"), 9, "emissive", "sign", shape="cyl",
            r=(90, 0, 0) if axis == "x" else (0, 0, 90))
        for i in range(4):  # columns at the door
            box(f"{n}Column{i}", at(uc - 3.0 + i * 2.0, vf - 1.2, 2.5), (0.5, 5.0, 0.5), rgb("efe8dc"), 9, "solid", "porch", shape="cyl")
        box(n + "Portico", at(uc, vf - 1.2, 5.2), size(7.6, 2.6, 0.4), rgb("efe8dc"), 9, "solid", "roof")
        T.glow(at(uc, vf - 1.0, 11.0), rgb("fff4d8"), 10, 0.9)
    elif hid == "hotel":
        building(n, bx0, bx1, bz0, bz1, 10.0, rgb("3a3a5a"), rgb("1e1e2a"), door, gable=False, sign=(name, sign))
        box(n + "Canopy", at(uc, vf - 1.8, 3.0), size(3.4, 3.6, 0.2), rgb("6a2a4a"), 9, "solid", "roof")
        for i in (-1, 1):
            box(f"{n}CanopyPost{i}", at(uc + i * 1.5, vf - 3.4, 1.5), (0.14, 3.0, 0.14), rgb("c8a040"), 9, "solid", "porch", shape="cyl")
        box(n + "RoofSign", at(uc, vf + 1.0, 11.4), size(8.0, 0.2, 1.4), sign, 9, "emissive", "sign")
        box(n + "Raven", at(uc + 4.5, vf + 1.0, 10.9), (0.7, 0.6, 0.9), rgb("16141c"), 9, "solid", "decor", shape="sphere")
    elif hid == "toyshop":
        building(n, bx0, bx1, bz0, bz1, 5.0, rgb("f0c8d8"), rgb("4a8ad0"), door, sign=(name, sign))
        tx, _, tz = at(uc - W / 2 - 0.6, vf - 0.6)  # on the corner, outside the walk-in room
        box(n + "Turret", (tx, 3.5, tz), (3.0, 7.0, 3.0), rgb("f8e8a0"), 9, "solid", "building", shape="cyl")
        for i in range(4):
            s = 3.4 * (1 - i / 4)
            box(f"{n}TurretCap{i}", (tx, 7.3 + i * 0.6, tz), (s, 0.6, s), rgb("e05a6a"), 9, "solid", "roof", shape="cyl")
        box(n + "Top", at(uc + 2.0, vf + 6.0, 7.6), (1.6, 1.2, 1.6), rgb("8affc8"), 9, "solid", "sign", shape="sphere")
        box(n + "TopSpindle", at(uc + 2.0, vf + 6.0, 8.5), (0.15, 0.7, 0.15), rgb("e05a6a"), 9, "solid", "sign", shape="cyl")
    elif hid == "musichall":
        building(n, bx0, bx1, bz0, bz1, 8.0, rgb("6a3a5a"), rgb("2a1a2a"), door, gable=False, sign=(name, sign))
        for i in range(5):  # a stepped arch over the entrance
            w = 5.0 - i * 0.9
            box(f"{n}Arch{i}", at(uc, vf - 0.3, 3.0 + i * 0.45), size(w, 0.6, 0.45), rgb("e8c8a0"), 9, "solid", "porch")
        for i in (-1, 1):
            box(f"{n}LampPost{i}", at(uc + i * 3.4, vf - 1.2, 1.6), (0.2, 3.2, 0.2), rgb("2a2a30"), 9, "solid", "porch", shape="cyl")
            box(f"{n}Lamp{i}", at(uc + i * 3.4, vf - 1.2, 3.4), (0.5, 0.5, 0.5), rgb("ffd8f0"), 9, "emissive", "sign", shape="sphere")
        box(n + "Star", at(uc, vf - 0.1, 7.0), size(1.4, 0.15, 1.4), rgb("ffe7a0"), 9, "emissive", "sign", r=(0, 0, 45) if axis == "x" else (45, 0, 0))
    elif hid == "creamery":
        building(n, bx0, bx1, bz0, bz1, 4.2, rgb("f8e0e8"), rgb("8ad0e0"), door, sign=(name, sign))
        cx, _, cz = at(uc + 3.5, vf + 4.0)
        for i in range(5):  # a giant cone on the roof
            box(f"{n}Cone{i}", (cx, 5.6 + i * 0.5, cz), (0.6 + i * 0.4, 0.5, 0.6 + i * 0.4), rgb("d8a060"), 9, "solid", "sign", shape="cyl")
        box(n + "Scoop", (cx, 8.6, cz), (2.4, 2.0, 2.4), rgb("ffb0c8"), 9, "solid", "sign", shape="sphere")
        box(n + "Cherry", (cx, 9.8, cz), (0.5, 0.5, 0.5), rgb("e0282e"), 9, "solid", "sign", shape="sphere")
        for i in range(8):
            box(f"{n}Awning{i}", at(uc - 5.25 + i * 1.5, vf - 0.8, 2.7), size(1.5, 1.6, 0.12), rgb("a0e8ff") if i % 2 else rgb("fff4f8"), 9, "solid", "roof")
    elif hid == "gazette":
        building(n, bx0, bx1, bz0, bz1, 6.2, rgb("8a8a80"), rgb("2a2a2a"), door, gable=False, sign=(name, sign))
        box(n + "PressStack", at(uc - 4.0, vf + 8.5, 8.0), (1.4, 4.0, 1.4), C["brick"], 9, "solid", "roof", shape="cyl")
        box(n + "Owl", at(uc + 3.0, vf + 0.5, 6.9), (0.6, 0.8, 0.6), rgb("8a6a4a"), 9, "solid", "decor", shape="sphere")
        box(n + "Bundle", at(uc + 2.5, vf - 0.8, 0.3), size(1.0, 0.7, 0.6), rgb("efe8dc"), 9, "solid", "decor")
    elif hid == "apothecary":
        building(n, bx0, bx1, bz0, bz1, 5.2, rgb("2a4a3a"), rgb("1a2a22"), door, sign=(name, sign))
        box(n + "Bay", at(uc - 3.0, vf - 0.8, 1.6), size(2.4, 1.6, 2.2), rgb("2a4a3a"), 9, "solid", "building")
        for i in range(3):
            box(f"{n}Jar{i}", at(uc - 3.8 + i * 0.8, vf - 1.65, 2.0), (0.45, 0.7, 0.45), rgb("9aff8a"), 9, "emissive", "sign", shape="cyl")
        T.glow(at(uc - 3.0, vf - 2.5, 2.0), rgb("9aff8a"), 6, 0.8)
        box(n + "Mortar", at(uc, vf - 0.2, 4.6), (1.0, 0.7, 1.0), rgb("c8c0b0"), 9, "solid", "sign", shape="cyl")
    elif hid == "depot":
        building(n, bx0, bx1, bz0, bz1, 5.0, rgb("8a5a3a"), rgb("3a2a22"), door, sign=(name, sign))
        box(n + "PlatformRoof", at(uc, vf - 2.0, 3.6), size(W + 2.0, 4.0, 0.25), rgb("3a2a22"), 9, "solid", "roof")
        for i in range(4):
            box(f"{n}PlatformPost{i}", at(uc - W / 2 + i * W / 3, vf - 3.7, 1.8), (0.2, 3.6, 0.2), rgb("6a4a2a"), 9, "solid", "porch", shape="cyl")
        box(n + "StationClock", at(uc, vf - 3.8, 3.0), size(0.9, 0.12, 0.9), rgb("fff4d8"), 9, "emissive", "sign", shape="cyl",
            r=(90, 0, 0) if axis == "x" else (0, 0, 90))
        box(n + "Bench", at(uc + 3.0, vf - 1.2, 0.45), size(2.4, 0.5, 0.9), rgb("6a4a2a"), 9, "solid", "decor")
    else:  # laundry
        building(n, bx0, bx1, bz0, bz1, 4.4, rgb("d0e8f0"), rgb("4a6a8a"), door, gable=False, sign=(name, sign))
        for i in range(4):  # round porthole windows
            box(f"{n}Porthole{i}", at(uc - 5.0 + i * 1.6 + (3.2 if i > 1 else 0), vf - 0.06, 1.7), size(1.1, 0.08, 1.1), rgb("8ac8ff"), 9, "emissive", "window",
                shape="cyl", r=(90, 0, 0) if axis == "x" else (0, 0, 90))
        box(n + "Sock", at(uc, vf - 0.2, 5.3), size(0.8, 0.2, 1.4), rgb("e05a6a"), 9, "solid", "sign")
    T.room(name, 9, bx0 - 1, bx1 + 1, bz0 - 1, bz1 + 1, -1, 16)

    # ---- inside (round 43): a walk-in ground floor dressed for its haunt; the last chase ends in here ----
    for i, (du, dv, y, su, sv, sy, hexc, mode, shape) in enumerate(INSIDE[hid]):
        box(f"{n}In{i}", at(uc + du, vf + dv, y), size(su, sv, sy), rgb(hexc), 9, mode, "decor", shape=shape)
    T.glow(at(uc, vf + 5.0, 3.0), rgb("ffcf8a"), 11, 0.9)
    T.glow(at(uc, vf + 8.0, 1.8), rgb(ghost_hex), 6, 0.7)

    # ---- the haunt: three signs round the front, the ghost's three hiding spots, and the plaque ----
    sign_spots = [at(uc - W / 2 + 1.2, vf - 1.6, 0.0), at(uc + W / 2 - 1.2, vf - 1.6, 0.0), at(uc + W / 2 + 0.9, vf + D * 0.5, 0.0)]
    hide = [at(uc, vf - 3.0, 1.6), at(uc - W / 2 - 0.9, vf + 2.0, 1.6), at(uc, vf + 8.0, 1.5)]  # the last one indoors
    return {
        "id": hid, "n": name, "ghost": ghost, "blurb": blurb, "twist": twist, "street": parcel["street"],
        "c": [round(v, 3) for v in rgb(ghost_hex)],
        "signs": [{"n": sn, "lore": sl, "p": [round(v, 2) for v in p]} for (sn, sl), p in zip(signs, sign_spots)],
        "hide": [round(v, 2) for p in hide for v in p],  # flat x,y,z triples (JsonUtility can't read nested lists)
        "door": [round(v, 2) for v in at(uc, vf - 0.2, 0.0)], "ry": ry,
        "min": [bx0, bz0], "max": [bx1, bz1],
    }
