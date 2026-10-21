# The full tour

Everything in Unmasked, house by house and system by system. The [README](../README.md) has the
short version: what the game is, how to set it up, and where it stands. Every picture here is drawn
from the game's own level, costume and case files by the scripts in [`Docs/tools`](tools); they're
illustrations, not screenshots from Unity.

**Contents:** [the story](#solve-the-haunting-unmask-the-person) ·
[how a match plays](#how-a-match-plays) · [the villains](#tonights-legends-the-villains) ·
[the town](#hollow-creek-the-town) · [Blackwood Manor](#the-3d-world-blackwood-manor) ·
[the sound](#the-sound) · [how it's built](#how-its-built)

## Solve the haunting. Unmask the person.

Hollow Creek's old folklore masks were brought out for the Halloween festival, and whoever wears
one can really haunt a house. Tonight a resident is using one to cover up something ordinary: a
stolen lantern, a wrecked prize display, a missing ledger. Everyone knows **which mask** is in play;
**who is wearing it** is the case. At the unmasking you find out why they did it. The full story
and art direction is in [`Docs/ART_DIRECTION.md`](ART_DIRECTION.md).

<p align="center"><img src="images/story.png" alt="The five cases, what each haunting covers up, and every suspect's motive" width="860"></p>

Every scare has a beat of warning, the surprise, then a moment to recover. A chair leans back
before it hops, a lamp pauses and turns to look at you, a suspect swallows before answering (guilty
or not), and the trap wobbles before it snaps:

<p align="center"><img src="images/anticipation.gif" alt="Anticipation tests: chair, lamp, suspect, trap" width="900"></p>

Want to look around without GitHub or Unity? The **`Reference renders`** folder has big stills of
every house (outside and roof off) and `gameplay-tour.mp4`, a short tour of a night. They're
drawn from the game's level files by the project's own renderer, not captured in Unity.


## How a match plays

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Setup
    Setup --> Dispatch: 30 s at HQ, pick a call, Haunter picks a legend and secretly a suspect
    Dispatch --> Investigation: the van reaches the house
    Investigation --> Trap: correct accusation
    Investigation --> HaunterWins: dawn, 2 wrong accusations, or all Solvers scared out
    Trap --> Unmasking: trap springs on the costumed Haunter
    Trap --> HaunterWins: Haunter escapes until the timer ends
    Unmasking --> SolversWin
    SolversWin --> [*]
    HaunterWins --> [*]
```

1. **Setup, at HQ.** Everyone picks a side. Solvers pick a role and tonight's call on the call
   board (or get a random one). The Haunter picks tonight's legend (the costume everyone will see)
   and secretly chooses which suspect they really are.
2. **Dispatch.** Pile into the Mystery Club van and drive across town to the house, following the
   map (**M**) and the arrow. A special night may be rolled: Blood Moon, Thunderstorm, Pea-Soup Fog,
   Power Outage or Harvest Festival. The suspects and the Haunter are already there.
3. **Investigation.** Glowing clues are hidden around the house. Each clue points at every suspect
   who shares one of its traits, so you deduce instead of guess. Suspects can be interviewed once;
   the culprit lies.
4. **The Haunter fights back.** Every power costs Ectoplasm, and every scare risks **leaking a real
   clue**. The Haunter can also plant fake clues to frame an innocent.
5. **Accuse.** Once you have 2 clues, accuse from the Suspect Board. Get it wrong and that suspect is
   cleared, but the Haunter powers up. Two wrong guesses and the Haunter wins.
6. **Trap.** Get it right and the Haunter is forced into costume. Grab 3 trap pieces, build the trap
   (Brawn builds twice as fast), and lure the Haunter in.
7. **Unmask!**

<p align="center"><img src="images/unmask.gif" alt="The mask comes off" width="380"></p>

### The Solvers

| Role | Ability |
|---|---|
| **Sleuth** | Clue sense: clues within 9 m pulse on your screen, and the HUD says how close the nearest one is. |
| **Techie** | Ecto-detector beeps near possessed objects, fog and phantoms. The flashlight drains 40% slower. |
| **Brawn** | Builds the trap twice as fast. |
| **Snacker** | Suspects open up more. Interviews point at the real culprit more often. |

Scares fill your **Fear Meter**. At 100% you panic and run screaming. Teammates nearby calm you
faster, and any teammate can calm you with **E**. Panic three times and you flee the house for good.

<p align="center"><img src="images/fear-meter.gif" alt="Fear meter filling and panicking" width="640"></p>

### The Haunter

As a ghost, the Haunter is invisible and isn't even sent to the Solvers' computers. Possess
furniture (**E**) and use its two actions (**LMB/RMB**), or use the five spectral powers, plus
tonight's villain power on **6** or **Q**:

<p align="center"><img src="images/powers.png" alt="Haunter power cards" width="900"></p>

In costume the Haunter is visible and can tag Solvers for big scares, but leaves footprints, and a
flashlight held on the costume stuns them. Nobody playing the Haunter? The **AI Director** haunts the
house instead, using the same tools and leaking clues the same way.

#### The case book

A new club's first call is always **The Missing Harvest Lantern** at Pemberton Cottage, the gentle
intro case. Solve a case and what was taken is put right (the lantern goes back on the mantel in
time for the lantern walk), and a keepsake appears on the shelf at HQ. The host's game remembers
solved cases between sessions, and the call board marks them **SOLVED**.

<p align="center"><img src="images/case-book.png" alt="The keepsake shelf at HQ and the case book" width="860"></p>

#### Another night: back to HQ

When a case ends, the host presses **Next night: back to HQ**. Nobody restarts: the van is back in
the HQ driveway, every house is put back the way it was (lamps on, doors shut, traps packed away),
everyone's fear, batteries and ectoplasm start full, and the call board is waiting for the next call.
The case book carries on, so a club can play through the whole town in one sitting.

#### The Mask Keeper: the story behind every case

None of the culprits took a folklore mask on their own. Each solved case gives the club one clue
about who has been lending the masks out (a museum loan tag, inky fingers and a note on a porch, a
smell of lavender and old paper, a brass key to a back door marked "STAFF ONLY"), and the clues fill
a page in the case book at HQ. Solve all four and every clue points to the same place: a fifth call
appears on the board.

<p align="center"><img src="images/mask-keeper.png" alt="The Mask Keeper: one clue from each case, all pointing the same way" width="860"></p>

#### The fifth call: 1 Founders Way

<p align="center"><img src="images/museum.png" alt="The Hollow Creek Historical Society on Founders Way at night, with the night watchman at the gate" width="900"></p>

The **Hollow Creek Historical Society** stands on its own street, Founders Way, across town from
HQ: a red-brick museum with a white-columned portico, a clock in the pediment and a cupola on the
roof. Its call stays locked on the call board ("solve the other four cases and this one will call")
until the four clues are in. Then the museum's lights are on far too late, and the oldest mask of
all, the **Hollow Creek Mask**, is missing from its case.

<p align="center"><img src="images/mask-gallery.png" alt="Inside the Mask Gallery: four masks under glass, an empty case behind a rope, and the four people who work at the museum" width="900"></p>

It's the biggest case so far: two floors (the Mask Gallery, the Entrance Hall, the Gift Shop, the
Curator's Office, the Reading Room and the Archive), a courtyard with a fountain where the trap
goes, and a Restoration Workshop out back. The suspects are the people who keep the place running:
**Walter Finch**, the night watchman with his keys and lantern; **Edie Wren**, the curator with ink on
her fingers; **Mortimer Vane**, the treasurer who'd sell the building to a collector; and
**Rosa Delgado**, who runs the tea room at the fundraiser. Only two accusations, only two alibi
checks. Unmask the Mask Keeper and the case book closes the story, and a little brass plaque goes on
the keepsake shelf at HQ.

#### The Suspect Board

Press **Tab**. The board keeps what the club **found**, what people **said** and what **follows**
apart, and stamps every clue and statement with the time of night (the night runs 8 PM to dawn at
6 AM) and where it came from. A nervous suspect is character, not proof. Each player can mark
their own **hunch** without changing anyone else's board.

No mouse needed: the arrow keys (or 1 to 4) pick a card, **H** marks a hunch, **X** crosses
someone off or puts them back, **C** checks their alibi and **A** accuses. Accusing takes a second
press of **A** within three seconds, because a wrong name can't be taken back.

<p align="center"><img src="images/suspect-board.png" alt="The Suspect Board: evidence, testimony and deductions, each with a time" width="820"></p>

#### Witnesses

<p align="center"><img src="images/witness.png" alt="The Banshee wails, a suspect jumps, and later tells the club what he noticed" width="860"></p>

Scares spook the suspects too: anyone nearby jumps ("Eek!") and scurries away. A suspect who **saw**
a scare up close becomes a witness, and when the club interviews them they describe a detail of the
Haunter instead of gossiping. Innocent witnesses name one of the culprit's real (shared) traits, which
narrows it to two suspects; the culprit, if it saw its own scare, names someone else's. So every scare
in front of a suspect is a risk for the Haunter.

#### Checking alibis

Every suspect's alibi names a place: a room in the house ("in the Library reading all night") or
somewhere in town ("at the Bookshop until closing"). Stand there, open the Suspect Board (**Tab**) and
press **Check alibi**. Innocent alibis hold up; the culprit's falls apart. You only get two checks a
night (three at the cottage), so choose well, and a town alibi means a drive. The catch: the Haunter
can **fake its alibi** once a night (**H**, 35 ectoplasm) by sneaking into that room first. A broken
alibi is proof; one that holds up might not be.

## Tonight's legends: the villains

<p align="center"><img src="images/villains.png" alt="The Headless Horseman, the Banshee, Stingy Jack and Baba Yaga" width="900"></p>

In setup the Haunter picks one of the festival's folklore masks. Everyone can see which mask is in
play tonight ("Someone took the Headless Horseman mask from the festival and is haunting Blackwood
Manor..."), but nobody knows which suspect is wearing it. Each legend changes how the Haunter plays:

| Villain | From | Signature power (6 or Q) | In costume |
|---|---|---|---|
| 🎃 **The Headless Horseman** | *The Legend of Sleepy Hollow* (1820), the Irish dullahan | **Pumpkin Toss**: a flaming jack-o'-lantern arcs at the nearest Solver in sight and bursts | fastest on foot |
| 👻 **The Banshee** | Irish folklore (*bean sidhe*) | **Wail**: heard through walls, scares everyone near, kills flashlights and lamps | floats |
| 🏮 **Stingy Jack** | The Irish tale of the first jack-o'-lantern | **Wisp Lure**: three will-o'-the-wisps hunt Solvers; flashlights pop them | carries a turnip lantern |
| 🧹 **Baba Yaga** | Slavic folklore | **Hex**: the nearest Solver gets a fear spike and a dying flashlight | flies in her mortar |

At the unmasking, the mask comes off the costume (the Horseman's pumpkin head, the Banshee's shroud,
Jack's grinning mask, Baba Yaga's headscarf) and the suspect underneath is revealed.

<p align="center"><img src="images/villains-turntable.gif" alt="The four villain costumes turning" width="860"></p>

<p align="center"><img src="images/cast.png" alt="The Mystery Club and the four suspects" width="900"></p>

<p align="center"><img src="images/faces.png" alt="Close-ups of the Mystery Club and the Pemberton Cottage suspects with faces, hands and jointed limbs" width="900"></p>

Every character has a proper face, hands with fingers and a thumb, arms that bend at the elbow,
legs with thighs, shins and boots or shoes, a waist, hips, a collar and buttons.

<p align="center"><img src="images/portraits.png" alt="Close-up portraits of the Sleuth, Edie Wren, Mayor Beaumont, Rosa Delgado and Sheriff Calloway after the character pass" width="900"></p>

The character pass in round 21 went over everyone again, up close. Eyes now have a two-tone iris,
lashes and a lower lid. Noses have a bridge, a tip, wings and nostrils, mouths have both lips, and
there's a chin, cheekbones and an inner fold to each ear. Hair frames the face (a crown, the back of
the head, then sideburns, a fringe, side curtains, a fall down the back or curls) instead of sitting
on top like a helmet. Spectacles are wire frames you can see the eyes through. The four fingers are
separate and curl a little, the shoulders slope, trouser legs have a pressed crease and skirts have
pleats.

<p align="center"><img src="images/people-before-after.png" alt="The same five characters before and after the round 21 character pass" width="860"></p>

<p align="center"><img src="images/silhouettes.png" alt="Every character as a flat dark shape: the Mystery Club, the four masks, the townsfolk and the suspects at each house" width="860"></p>

Round 22 added a silhouette check: every character as one flat shape at gameplay size, so hats,
hair, coats and props have to tell people apart without colour or a face. It caught one pair, the
two Pemberton Cottage ladies, so Beatrice Hollis now has a shawl and a walking cane.

<p align="center"><img src="images/builds.png" alt="Nine characters side by side showing different heights and builds" width="900"></p>

Nobody is the same size any more. Each person has their own height and build in `CHARACTERS` in
[`make_costumes.py`](tools/make_costumes.py): the Reverend and Mortimer Vane are tall and thin,
the Brawn and the Mayor are broad, Old Nell and Rosa are short. Builds widen the body but not the
face, so nobody's head gets stretched. The README pictures are rendered with smooth shading now too,
the way Unity draws its spheres and capsules. (These are renders from the project's own software
renderer, not Unity screenshots.)

<p align="center"><img src="images/face-life.gif" alt="A suspect blinks, looks at the camera, then talks" width="300"></p>

And the faces move: everyone blinks every few seconds, glances around and looks at you when you
come close, and a suspect's lips move while they answer your questions
([`Animation/FaceLife.cs`](../Assets/Unmasked/Scripts/Animation/FaceLife.cs)).

The Mystery Club dress for their roles (the Sleuth's deerstalker and magnifier, the Techie's
goggles and antenna backpack, the Brawn's toolbelt, the Snacker's sandwich) and the four suspects
are dressed for their jobs. Every character and prop is built from simple shapes in
[`Docs/tools/make_costumes.py`](tools/make_costumes.py) and saved to
[`Assets/Unmasked/Resources/Costumes.json`](../Assets/Unmasked/Resources/Costumes.json), which Unity and
the README renderer both read.

---

## Hollow Creek: the town

<p align="center"><img src="images/town-map.png" alt="Top-down map of Hollow Creek with every house fully built and pins for HQ and each haunted house" width="760"></p>

Every night starts at **Mystery Club HQ** at the south end of Main Street. A call comes in, the club
piles into the van and drives through town (past the diner, the town square with the Harvest
Festival stalls, the church and its churchyard, over the creek bridge) to tonight's haunted house.
It's a semi-open world: every house is fully built on its own lot all the time, so you can drive
past the others, and the Haunter, the suspects, the clues and the trap only exist at the house the
call is about.

<p align="center"><img src="images/van-drive.gif" alt="Driving the Mystery Club van from HQ to Pemberton Cottage with the waypoint arrow and minimap" width="720"></p>

**The map (M)** works like the phone map in *Schedule I*: a top-down view of the whole town with
each house fully loaded, pins for HQ, every haunted house, the van and your friends. Click a house
for its card: a live 3D view circling the house, its size, floors, rooms and spookiness, a
**Set waypoint** button and, at HQ, **Take this call**. A minimap and a waypoint arrow stay on screen
while you drive.

### Beyond the edge of town

<p align="center"><img src="images/horizon.png" alt="Hollow Creek from above, with forest, far hills, the lights of other towns, the Ravensford church steeple and the Thornbury ruins" width="900"></p>

Hollow Creek sits in a valley, and the world doesn't stop at the town line. Three ridges of hills
ring the horizon in every direction, with the lights of farms and far-off towns scattered across
them and mist lying in the valley. Landmarks stand on the ridges: the **Ravensford church** steeple,
the **Gull Point lighthouse** with its beam sweeping round, **Hatcher's old windmill** turning, the
**Ravensford water tower** with its red light, and the **Thornbury ruins**. The hills follow the
camera, so they always stay on the horizon however far you drive.

<p align="center"><img src="images/edge-of-town.png" alt="Main Street running on out of town past the woods, with street lamps and a sign to Ravensford" width="800"></p>

Closer in, every road carries on past the edge of town with lamps and signposts ("Ravensford 12 mi",
"Gull Point 9 mi", "Thornbury 6 mi", "Old Mill Road"), and a band of pines and autumn trees fills
the gap between the town and the hills. It's all built when the town loads by
[`Town/Horizon.cs`](../Assets/Unmasked/Scripts/Town/Horizon.cs) from the `horizon` block in
[`HollowCreek.json`](../Assets/Unmasked/Resources/HollowCreek.json).

<p align="center"><img src="images/beyond-town.gif" alt="Looking all the way round from the roof of HQ" width="720"></p>

### Someone's always out tonight

<p align="center"><img src="images/living-town.png" alt="Main Street at night with trick-or-treaters on the sidewalk, one group telling a rumour" width="860"></p>

Hollow Creek is out trick-or-treating. Groups of two to four kids (ghosts in sheets, witches,
pumpkins, skeletons, cats, vampires and pirates, each with a glowing candy bucket) walk the
sidewalks of Main Street, Elm Street and Willow Lane, stop now and then to knock, and turn to talk
when you walk up. They pass on the town's gossip (the museum might close, someone borrowed the old
festival masks, a light at the old windmill) and, once a call comes in, rumours about tonight's
house. It's all scenery: rumours are never clues, and the kids are never in anyone's way.

<p align="center"><img src="images/trick-or-treaters.png" alt="The seven trick-or-treater costumes" width="860"></p>

Out past the edge of town, cars come and go on the roads to Ravensford and Thornbury with their
headlights on, and now and then the late train crosses the valley in front of the hills, its
windows lit. Built by [`Town/TownLife.cs`](../Assets/Unmasked/Scripts/Town/TownLife.cs) from the
`life` block in [`HollowCreek.json`](../Assets/Unmasked/Resources/HollowCreek.json).

<p align="center"><img src="images/valley-train.png" alt="Cars on the road out of town and the train crossing the valley" width="860"></p>

### The people of Hollow Creek

<p align="center"><img src="images/townsfolk.png" alt="Mayor Harold Beaumont, Old Nell Thistle, Reverend Amos Gale, Dot Kowalski and Sheriff Ruth Calloway" width="900"></p>

Five grown-ups are out in town tonight, and you can walk up to any of them and press **E** to talk:
**Mayor Harold Beaumont** by the bandstand, **Old Nell Thistle** reading fortunes at her festival
stall, **Reverend Amos Gale** outside the church, **Dot Kowalski** at the diner door, and **Sheriff
Ruth Calloway** keeping watch on the bridge. They turn to face you, their lips move as they talk, and
what they say fills in the town's side of the Mask Keeper story: whose idea it was to lend out the
masks, who meets a collector in the diner's back booth, where the oldest mask came from.

<p align="center"><img src="images/errands.png" alt="Old Nell asks the club to find her cat; Midnight glows among the headstones behind the church" width="900"></p>

Each of them has lost something tonight: the prize pumpkin, Nell's cat Midnight, the sexton's
lantern, Dot's door wreath, the jack-o'-lantern from the sheriff's station steps. Once they've asked,
it shows up somewhere in town with a soft glow, and their pin on the map (**M**) gets a "!". Bring it
back and they put in a word for the club: **one more alibi check**, tonight if you're on a case or
on the next one if you're between calls. Errands carry on from night to night, and the HQ panel
keeps count. Built by [`Town/Townsperson.cs`](../Assets/Unmasked/Scripts/Town/Townsperson.cs) and
[`Town/ErrandItem.cs`](../Assets/Unmasked/Scripts/Town/ErrandItem.cs) from the `folk` block in
[`HollowCreek.json`](../Assets/Unmasked/Resources/HollowCreek.json).

### The Lantern Watch: a costume the town makes for you

<p align="center"><img src="images/lantern-watch.png" alt="The four Solvers wearing the Lantern Watch costume: a sash, a moon charm, a handbell, a tin-can lantern and a tin star, next to the dressing-up trunk" width="900"></p>

Each townsperson also says thank you with something homemade: the Mayor's old festival sash, a
tin moon charm from Old Nell, the Sunday-school handbell, a tin-can lantern from Dot's diner and a
tin star from the sheriff. Three pieces make a costume. Open the **dressing-up trunk at HQ** (E)
between cases to put it on or take it off. While the club wears it, every piece shows on all four
Solvers and **scares hit 7% softer per piece** (21% with three, 35% with all five). The costume is
data in [`make_costumes.py`](tools/make_costumes.py) (`WATCH`), fitted to each Solver's height
and build, and switched on by [`Spooky/WatchCostume.cs`](../Assets/Unmasked/Scripts/Spooky/WatchCostume.cs)
and [`Town/CostumeTrunk.cs`](../Assets/Unmasked/Scripts/Town/CostumeTrunk.cs).

### The street remembers

<p align="center"><img src="images/street-remembers.png" alt="Pemberton Cottage's front yard under a violet light the night its call is open, and the same yard after the case with lanterns, a party table and a thank-you banner" width="900"></p>

Every house shows where its story stands. While its call is open, a violet light pulses over the
front yard. Once its case is in the case book, the neighbours throw a little party that stays for
the rest of the game: paper-bag lanterns up the walk, jack-o'-lanterns at the gate, a party table
and a **THANK YOU, MYSTERY CLUB!** banner. You can see which houses you've helped from the van,
without opening a menu. It reads the same networked case book as the keepsake shelf
([`Town/HouseMood.cs`](../Assets/Unmasked/Scripts/Town/HouseMood.cs), from the `afterglow` block of
each lot in `HollowCreek.json`).

### Saved progress, and starting over

The host's game remembers the case book, every errand (asked, found or done), favours still owed,
costume pieces and whether the club is wearing the costume, so quitting and coming back picks up
the same town. Rewards can't be collected twice: a finished errand stays finished. The host has a
**Start over** button at HQ that wipes it all, and it needs a second press within a few seconds.

### The Club Handbook: hints for your first night

New players get a small card the first time each moment comes up: arriving at HQ, the drive, the
first clue, the Suspect Board, being able to accuse, the first panic, the trap, playing the
Haunter, the townsfolk's errands and closing a case. Each card shows once, and **F1** opens the
handbook with every hint seen so far (and a button to show them all again). The hints live on
each player's own computer, so nothing extra goes over the network
([`UI/Handbook.cs`](../Assets/Unmasked/Scripts/UI/Handbook.cs)).

<p align="center"><img src="images/handbook.gif" alt="Handbook hint cards appearing at HQ, on the drive, at the Suspect Board, during a scare and after a case" width="720"></p>

### The houses

<p align="center"><img src="images/house-sizes.png" alt="The five houses side by side, to scale" width="860"></p>

| House | Size | What's there |
|---|---|---|
| **Pemberton Cottage**, 14 Elm Street | Small: 30 x 26 m lot, 1 floor | A tidy cottage behind a white picket fence: living room, kitchen, bedroom, bathroom, study, a garden shed and a vegetable patch. A quick case. |
| **Hollow Creek Farm**, Old Mill Road | Medium: 70 x 60 m lot, 2 floors | A farmhouse, a red barn with a hayloft trapdoor, a corn maze with a scarecrow in the middle, a windmill and a pumpkin patch. |
| **Willow Lane Victorian**, 3 Willow Lane | Large: 44 x 40 m lot, 2 floors and a tower | A wraparound porch, a music room under a nursery with a trapdoor, a tower lookout, a gazebo (the trap site) and a family plot. |
| **Blackwood Manor**, the end of Main Street | Huge: 88 x 80 m lot, cellar, 2 floors, roof | The big one, over the creek (below). |
| **Historical Society**, 1 Founders Way | Large: 36 x 33 m lot, 2 floors | The fifth call, locked until the other four are solved: a museum with a portico, a Mask Gallery, an Archive, a courtyard fountain and a Restoration Workshop. |

<p align="center"><img src="images/house-cards.png" alt="House cards: each house outside at night and with the roof off, fully furnished" width="830"></p>

### A case for every house

<p align="center"><img src="images/case-files.png" alt="Case files: each house's mystery, its four suspects, their alibis and the clues" width="860"></p>

Every call is its own mystery. The house you drive to decides who the four suspects are, what they
claim they were doing, what they gossip about, and what the clues look like: sawdust and icing sugar
at the cottage, hay seeds and tractor grease at the farm, candle wax and graveyard dirt on Willow Lane.
The rules underneath are the same everywhere (any two true clues name exactly one suspect), so every
case is solvable. Pemberton Cottage is the gentle one: an extra clue hidden at the start, the Haunter
slips up more, and you get three accusations instead of two.

<p align="center"><img src="images/suspects-by-house.png" alt="The four suspects at each house, each in their own outfit" width="860"></p>

Each cast dresses the part: Hank the handyman has his hammer and toolbelt, the Harvest Queen her
crown and sash, Dr. Marlowe carries the music box he keeps trying to buy. The four suspects follow the
club from call to call and change into tonight's cast when a call comes in. While you investigate
they don't stand frozen: they stroll around near their spot, so you'll have to find them.

#### Return visits

<p align="center"><img src="images/return-visits.png" alt="The four return-visit case files: The Lost Love Letters, The Stolen Seed Corn, The Silver Christening Cup and The Vanishing Portrait" width="860"></p>

Solve a house's case and, a night or two later, it calls again with a **new mystery**. It's the same
neighbours in the same outfits, but they have new alibis, new clues, new gossip and new reasons to
wear the mask. At Pemberton Cottage, Mr. Pemberton's old love letters have gone from the desk and the
garden gnomes all face the window. At the farm, the hundred-year-old seed corn is stolen and the
scarecrow turns its head. On Willow Lane, the Ashcombe christening cup is gone and the empty cradle
rocks. At Blackwood Manor, Lady Blackwood's portrait has vanished and the organ in the cellar plays at
midnight. The call board marks them **RETURN VISIT**, and houses with an unsolved case call first, so
there are nine cases in the book now.

All nine cases live in [`Cases.cs`](../Assets/Unmasked/Scripts/Mystery/Cases.cs). A case set on the
`MysteryGameManager` in the Inspector still overrides them.

### Special nights

<p align="center"><img src="images/night-events.png" alt="The same street on a normal night and during each special event" width="900"></p>

| Event | What changes |
|---|---|
| **Blood Moon** | A red moon. Scares hit 25% harder and the Haunter's ectoplasm refills 50% faster. |
| **Thunderstorm** | Rain and lightning flashes. Now and then a lamp in the house blows out. Flashlights drain a bit faster. |
| **Pea-Soup Fog** | Thick fog off the creek: you can barely see past your flashlight. |
| **Power Outage** | Every lamp in the house starts off and flashlights drain 60% faster. |
| **Harvest Festival** | The town is celebrating: Solvers are braver (20% less fear), but dawn comes 20% sooner. |

The town is data too: [`Docs/tools/make_town.py`](tools/make_town.py) writes
[`HollowCreek.json`](../Assets/Unmasked/Resources/HollowCreek.json) and
[`Docs/tools/make_houses.py`](tools/make_houses.py) writes each house into
[`Resources/Houses/`](../Assets/Unmasked/Resources/Houses). **Unmasked > Build Hollow Creek (town)**
builds the whole thing in Unity, and the pictures above are drawn from the same files.

---

## The 3D world: Blackwood Manor

<p align="center"><img src="images/manor-orbit.gif" alt="Orbit around Blackwood Manor at night" width="640"></p>

A two-storey manor with a cellar, eleven rooms and spooky grounds: an iron gate under an arch of
jack-o'-lanterns, a pumpkin trail around the fountain, the groundskeeper's greenhouse, a pumpkin
patch with a scarecrow, a cemetery with candles and a witch's cauldron, a hedge garden and dead
trees hung with jack-o'-lanterns. Walk in through
the front door, take the grand staircase up, or the back-hall stairs down to the cellar. Three
trapdoors drop unlucky Solvers a floor.

<p align="center"><img src="images/manor-walkthrough.gif" alt="Walking from the gate into the manor and up the stairs" width="640"></p>

### The look: Halloween night

<p align="center"><img src="images/pumpkin-trail.gif" alt="A dolly along the jack-o'-lantern trail" width="720"></p>

The whole town is dressed like LA's [Nights of the Jack](https://secretlosangeles.com/nights-of-the-jack/)
trail, but kept to what a town that loves Halloween would really put out: carved pumpkins on every
porch and path, an arch of jack-o'-lanterns here and there, string lights, cornstalks and mums, one
ghost in a tree. The game uses a cel-shaded toon shader with a violet rim light, bloom so every
jack-o'-lantern glows, a purple-and-orange colour grade, ground mist, fireflies and bats.
[Docs/ART_DIRECTION.md](ART_DIRECTION.md) has the references, palette and rules.

<p align="center"><img src="images/nights-of-jack.png" alt="Set pieces around town: a porch display, jack-o'-lantern arches, a jack-o'-lantern tree, string lights on a porch and across Main Street" width="900"></p>

No two jack-o'-lanterns are alike: every one in town picks from seven carvings.

<p align="center"><img src="images/carvings.png" alt="Seven jack-o'-lantern carvings: classic, toothy grin, angry, surprised, wink, tall and ghost white" width="860"></p>

**Detail.** Every wall, roof and lawn has a surface: clapboard siding, shingles, brick, cut stone,
floorboards, grass, asphalt, gravel. They're small greyscale patterns laid over each colour in world
space by the toon shader, so a board is the same size on every wall. Houses get window casings,
shutters, flower boxes full of mums, a stone foundation and fascia boards along the eaves, and every
front door has a harvest wreath.

<p align="center"><img src="images/before-after.png" alt="The cottage and the Victorian before and after the detail pass" width="830"></p>

<p align="center"><img src="images/art-direction.png" alt="Before and after the Halloween look, and the palette" width="900"></p>

<p align="center"><img src="images/manor-cutaway.png" alt="Ground floor with the walls cut away" width="900"></p>

<p align="center"><img src="images/manor-floors.png" alt="Cellar, ground floor and upstairs" width="900"></p>

| Floor | Rooms | Who's there |
|---|---|---|
| Upstairs | Master Bedroom, Guest Room, Portrait Gallery, Servants' Quarters, Upstairs Hall | the Heiress, the Rival |
| Ground floor | Foyer (trap site), Library, Study, Dining Room, Kitchen, Back Hall | the Cook |
| Cellar | Wine cellar, boiler, barrels | trap piece |
| Outside | Gate, pumpkin trail, fountain, greenhouse, pumpkin patch, cemetery, hedge garden | the Groundskeeper |

The HUD tells you which room you're in, and clue announcements say where a clue was found. The ghost
drifts straight through walls and floors; in costume the Haunter has to use doors and stairs like
everyone else.

**One file, three uses.** The whole level is data in
[`Assets/Unmasked/Resources/BlackwoodManor.json`](../Assets/Unmasked/Resources/BlackwoodManor.json),
written by [`Docs/tools/make_manor.py`](tools/make_manor.py). Unity builds the 3D scene from it
(**Unmasked > Build Blackwood Manor (3D)**), the game reads room names from it, and
[`Docs/tools/render3d.py`](tools/render3d.py), a tiny software 3D renderer, draws every manor
picture on this page from it. Characters and Halloween props work the same way with
[`Costumes.json`](../Assets/Unmasked/Resources/Costumes.json) and `make_costumes.py`. To change the
house or the costumes, edit those scripts and run `unmasked world`.

---

## The sound

<p align="center"><img src="images/sounds.png" alt="Spectrograms of every sound in the game, grouped by where it plays" width="860"></p>

The town is no longer silent. Wind and crickets are always there, with rain on Thunderstorm nights
and a low drone under the Blood Moon. Crows and owls call from somewhere nearby, and the Willow Lane
music box plays by itself in the empty nursery. Each legend has a signature sound (the Banshee's wail,
the Horseman's hoofbeats, Stingy Jack's wisps, Baba Yaga's hex), possessed furniture rattles, slams
and buzzes, doors creak, and suspects yelp when they're startled. Your own heartbeat speeds up as
your fear rises. Clues, alibis, the trap and the unmasking each get a sting, and the van's engine
revs with its speed.

Every sound is synthesized by [`Docs/tools/make_sounds.py`](tools/make_sounds.py) (no
recordings, nothing to license) into
[`Resources/Sounds/`](../Assets/Unmasked/Resources/Sounds). Double-click any `.wav` there to hear it.
The game plays them through [`Sfx.cs`](../Assets/Unmasked/Scripts/Spooky/Sfx.cs) and
[`Ambience.cs`](../Assets/Unmasked/Scripts/Spooky/Ambience.cs), which sets itself up, so the scenes
don't need rebuilding.

---

## How it's built

<p align="center"><img src="images/secrets.png" alt="Who knows what over the network" width="860"></p>

```mermaid
flowchart LR
    subgraph Server["Server (host)"]
        GM[MysteryGameManager<br/>phases, rules, timers]
        MS[MysteryServer<br/>culprit, clue truth, fakes]
        AI[AIDirector<br/>plays an empty Haunter slot]
        GM --> MS
        AI --> GM
    end
    subgraph Shared["Replicated to everyone"]
        PL[Phase, timer, suspects,<br/>found clues, interviews]
        PA[PlayerAgent<br/>side, role, panics]
    end
    subgraph Pawns
        SC[SolverController<br/>FearMeter, Flashlight]
        HC[HaunterController<br/>HaunterPowers, Ectoplasm]
    end
    House[House: possessables, doors,<br/>trapdoors, lamps, suspects, trap]
    GM --> PL
    SC -- "Interact RPC" --> GM
    HC -- "Possess / power RPC" --> GM
    GM --> House
```

```mermaid
sequenceDiagram
    participant S as Solver's PC
    participant H as Server
    participant All as Everyone
    S->>H: InteractRpc(clue)
    H->>H: in range? line of sight? not yet found?
    H->>H: look up the clue's truth in MysteryServer
    H->>All: Clues list += {name, description, traits}
    Note over H: whether it was planted is never sent
    H->>All: "Clue found: Muddy boot print"
```

| Folder (`Assets/Unmasked/Scripts`) | What's inside |
|---|---|
| `Core` | Match flow (`MysteryGameManager`), per-player state (`PlayerAgent`), camera, shared types |
| `Solvers` | `SolverController`, `FearMeter`, `Flashlight` |
| `Haunter` | `HaunterController` (possession, costume), `HaunterPowers`, `Ectoplasm`, fog, phantom |
| `Mystery` | Case, suspect and clue data, `Cases` (one case per house), and `MysteryServer` (the secret half) |
| `House` | Possessable furniture and lamps, doors, trapdoors |
| `Traps` | Trap pieces and the trap site |
| `AI` | `AIDirector` and the interviewable `SuspectNPC` |
| `Animation` | `PawnAnimator`: walk bob, panic scramble, ghost float, dizzy stun, mask pop |
| `UI` | Placeholder IMGUI HUD and Suspect Board |
| `Town` | Hollow Creek: `TownLayout` (the town data), `HouseSite` (one house on its lot), `TownDirector`, the `MysteryVan`, the `TownMap` (M, minimap, waypoints) and `NightEventFX` |
| `Editor` | **Build Hollow Creek (town)** and **Build Blackwood Manor (3D)** builders, the small test room, and the player `BuildScript` |

Networking is Netcode for GameObjects (host, join or dedicated server). The van is driven on the
driver's machine (ownership moves to whoever is at the wheel) so it feels instant, and the server
checks arrival at the house. The town, houses, characters, prefabs, materials, sky and
post-processing are generated by **Unmasked > Build Hollow Creek (town)**, so the project needs no
hand-made assets yet. The look uses the built-in render pipeline
with a custom toon shader and the Post Processing package (`com.unity.postprocessing`).

---
