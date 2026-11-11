# UNMASKED progress

`unmasked status` reads this file. Tick a box by changing `[ ]` to `[x]`.

<!-- progress:start -->
## Milestone 1: Core
- [x] Unity 6 project with Netcode for GameObjects (host, join, dedicated server)
- [x] Solver: movement, interaction, flashlight with battery
- [x] Fear Meter: scares, panic flee, teammates calm you, scared out after 3 panics
- [x] Haunter: spectral flight, invisible to Solvers on the wire, object possession
- [x] Server-only mystery: secret culprit, seeded clues, leaks, fake clues, interviews

## Milestone 2: Haunter toolkit
- [x] Five powers: Slam Doors, Fog, Trapdoor, Phantom Illusion, Costume Chase
- [x] Costume form: tagging, footprints, flashlight stun
- [x] Possessable furniture and lamps

## Milestone 3: Solve it
- [x] Suspect Board (Tab), cross off, accuse
- [x] Trap phase: collect pieces, build, spring
- [x] Unmasking sequence and end screens

## Milestone 4: Play without a full lobby
- [x] AI Director haunts the house when nobody plays the Haunter
- [x] Solver roles: Sleuth clue sense, Techie ecto-detector, Brawn builder, Snacker interviews
- [x] Procedural animations: walk bob, panic scramble, ghost float, dizzy stun, mask flies off
- [x] AI Haunter wears the costume and dodges the trap
- [x] It finds its way through doorways, takes the bait only when nobody guards the trap, and can smell it and back off
- [ ] Watch the stand-in in Unity and tune how often it backs off

## Milestone 5: The 3D world
- [x] Blackwood Manor: cellar, ground floor, upstairs, roof (11 rooms)
- [x] Grounds: gate, fountain, greenhouse, cemetery and crypt, hedge garden, dead trees
- [x] Real stairs (grand staircase, cellar stairs) and trapdoors that drop you a floor
- [x] One layout file builds the Unity level and draws the README renders
- [x] Room names on the HUD and in clue announcements
- [x] Ghost drifts through walls and floors; the costume has to use doors and stairs
- [ ] Real 3D models and textures for the manor
- [ ] Baked lighting and occlusion culling for speed

## Milestone 6: Halloween night
- [x] Four folklore villains as Haunter costumes: Headless Horseman, Banshee, Stingy Jack, Baba Yaga
- [x] Signature villain powers (6 or Q): Pumpkin Toss, Wail, Wisp Lure, Hex (the AI Director uses them too)
- [x] Costume picker in setup; tonight's legend shown to everyone, the suspect under it stays secret
- [x] Dressed characters: Mystery Club outfits per role, four suspects, all from one costume file
- [x] Toon shader with violet rim light, post-processing (bloom, vignette, colour grade, AO, grain)
- [x] Jack-o'-lantern trail and arch, pumpkin patch with scarecrow, candles, cobwebs, cauldron, crows
- [x] Ground mist, embers, fireflies, bats circling the roof, flickering jack-o'-lantern lights
- [x] Spooky audio: wind, crickets, rain, crows, owls, thunder, the Banshee's wail, the Horseman's hoofbeats, the music box, heartbeat
- [ ] Hand-made models to replace the shape-built characters

## Milestone 7: Hollow Creek, the town
- [x] A semi-open 3D town: Main Street, Elm Street, Willow Lane, shops, town square, church, creek and bridge
- [x] Mystery Club HQ where every night starts, with a call board to pick tonight's call
- [x] Three new haunted houses that differ in size: Pemberton Cottage (small), Hollow Creek Farm (medium), Willow Lane Victorian (large), plus Blackwood Manor (huge)
- [x] Dispatch phase: drive the Mystery Club van to the call; the case starts when you reach the house
- [x] Drivable van (driver owns it while driving), passengers ride along
- [x] Town map on M (Schedule I style) with every house fully loaded, house cards with a live 3D preview, waypoints, minimap and arrow
- [x] Special nights: Blood Moon, Thunderstorm, Pea-Soup Fog, Power Outage, Harvest Festival
- [x] Van engine sound that revs with speed
- [ ] Sitting and steering animations
- [ ] More houses and calls that chain into a bigger case

## Milestone 8: The Nights of the Jack look
- [x] Surface patterns on every wall, roof and lawn (siding, shingles, brick, stone, floorboards, grass, asphalt)
- [x] House detail: window casings, shutters, flower boxes, stone foundations, fascia boards, door wreaths
- [x] Seven jack-o'-lantern carvings, so no two are alike
- [x] Halloween set pieces: jack-o'-lantern arches and trees, string lights, porch displays, luminarias
- [x] Yard dressing: tombstones, a sheet ghost, a skeleton, black cats, a spider, a figure in a window
- [ ] Check the look in Unity and tune light counts for frame rate

## Milestone 9: A case for every house
- [x] Each house has its own case: four suspects with names, jobs, bios and alibis, eight clues and its own gossip
- [x] The case loads when a call is picked (or a random call comes in), before the culprit is locked in
- [x] Suspect Board shows each house's clue names (sawdust, hay seeds, candle wax...)
- [x] Pemberton Cottage is the easy case: extra clue, more slip-ups, three accusations
- [x] Suspects dressed for each house (16 outfits); they change when a call comes in
- [x] Suspects stroll around near their spot during the investigation, without walking through walls
- [x] Suspects jump and scurry away from scares
- [x] Witnesses: a suspect who saw a scare up close describes a detail of the Haunter (the culprit lies)
- [x] Alibis name a room in the house or a place in town; Solvers search it to check (2 a night, 3 at the cottage)
- [x] The Haunter can fake its alibi once a night (H), and the AI Director sometimes does too
- [ ] A short search animation and a clue-style prop in the alibi room

## Milestone 10: Storybook direction
- [x] Story and art direction written down (Docs/ART_DIRECTION.md)
- [x] Folklore masks: the mask is announced, the wearer is the case
- [x] Each case covers up an ordinary wrongdoing (Harvest Lantern, prize display, recital, ledger)
- [x] Every suspect has a motive, revealed at the unmasking
- [x] Possessed furniture leans back before it acts and wobbles after
- [x] Lamps pause, then turn to look at the nearest Solver
- [x] Suspects hesitate before answering, guilty or not
- [x] The trap wobbles before it snaps
- [x] A new club's first call is always the Harvest Lantern at Pemberton Cottage
- [x] Statements on arrival are stamped 8:00 PM on the board
- [x] Solving a case puts things right (the lantern is back on the mantel) and leaves a keepsake on the HQ shelf
- [x] Case book: solved cases are saved on the host and marked SOLVED on the call board
- [ ] First playable slice played start to finish in Unity
- [x] Next night without restarting: back to HQ for another call
- [x] Suspect Board: evidence, testimony and deductions, each with a source and a time of night
- [x] Hunches: each player pins their own suspicions without changing anyone else's board
- [x] Night clock (8 PM to dawn at 6 AM) on the top bar
- [x] Reference renders folder: house stills and a gameplay tour video
- [x] Storybook lighting pass (amber, teal, violet), the whole town at once (round 33)
- [ ] Original van look with keepsakes from solved cases

## Milestone 11: A bigger world
- [x] Hills on three ridges round the whole horizon, with valley mist, following the camera
- [x] Far-off lights of farms and towns that twinkle
- [x] Landmarks on the ridges: church steeple, lighthouse with a sweeping beam, turning windmill, water tower, castle ruins
- [x] Roads carry on out of town with lamps and signposts to the neighbouring towns
- [x] A forest of pines and autumn trees between the town and the hills
- [x] Characters rebuilt: faces, hands with fingers, jointed arms and legs, boots and shoes, dresses that flare
- [x] The Mask Keeper: a clue in every case about who lent out the masks, and a finale when all four are solved
- [ ] Check the horizon in Unity (draw order, fog, far clip) and tune it
- [x] A fifth call: the Historical Society, where the Mask Keeper is waiting (Milestone 13)

## Milestone 12: A living town
- [x] Trick-or-treaters in seven costumes walk every street, stop to knock and turn to talk to you
- [x] Town gossip and rumours about tonight's call (flavour, never clues)
- [x] Cars with headlights and tail lights on the roads out of town
- [x] A train with lit windows crossing the valley
- [x] Faces blink, glance at whoever is close, and suspects' lips move when they answer
- [ ] Check the crowd and the train in Unity and tune counts for frame rate

## Milestone 13: The fifth call
- [x] The Hollow Creek Historical Society: a two-floor museum with a portico, Mask Gallery, Archive, courtyard fountain and workshop
- [x] Founders Way, a new street with lamps, sidewalks and trick-or-treaters, and driveways to every house
- [x] The Mask Keeper case: four new suspects, alibis, clues, gossip, rumours and motives
- [x] The call stays locked on the call board until the other four cases are solved, then it's the next call
- [x] The finale and epilogue in the case book, and a brass plaque keepsake at HQ
- [x] Outfits for the museum staff: watchman, curator, treasurer, tea room volunteer
- [ ] Playtest the whole arc in Unity, five calls in one sitting

## Milestone 14: The people of Hollow Creek
- [x] Five townsfolk around town: the mayor, a fortune teller, the minister, the diner owner and the sheriff
- [x] They turn to face you, talk with moving lips, and tell the town's side of the Mask Keeper story
- [x] Errands: each has lost something in town; it appears with a glow once they've asked
- [x] Bring it back for a favour: one more alibi check, tonight or on the next case
- [x] Townsfolk pins on the map, with "!" for an open errand, and the errand count at HQ
- [ ] Check the townsfolk in Unity (bubbles readable, items easy to spot)

## Milestone 15: Return visits
- [x] A second mystery for Pemberton Cottage, the farm, Willow Lane and Blackwood Manor
- [x] Same neighbours and outfits, new alibis, clues, gossip, rumours and motives
- [x] A house calls again once its first case is solved; houses with an unsolved case call first
- [x] Call board shows RETURN VISIT; the case book counts all nine cases
- [ ] Playtest a return visit in Unity

## Milestone 16: The character pass
- [x] Faces: two-tone irises, lashes, lower lids, a nose bridge and nostrils, both lips, a chin, inner ears
- [x] Hair that frames the face (short, parted, bald, bob, long, updo, curly) instead of one sphere
- [x] Separate fingers, sloping shoulders, elbows, trouser creases, skirt pleats, wire spectacles
- [x] Every character has their own height and build
- [x] FaceLife moves the lashes with the blink and lifts the brows while talking
- [x] README renders use smooth shading, like Unity's own spheres and capsules
- [ ] Check in Unity that ~100 shapes per person stays fast with a full town

## Milestone 17: A town that remembers (inspiration pack)
- [x] Slice plan with one gameplay, one visual and one systems reference (Docs/SLICE_PLAN.md)
- [x] Lantern Watch costume: a piece from each errand, worn from the HQ trunk, softens scares
- [x] The street remembers: solved yards keep a party, tonight's call glows violet
- [x] Saved errands, favours and costume pieces; host Start over (two presses)
- [x] Favours are spent when a case starts, not lost on the drive back to HQ
- [x] Case checker: all 9 cases solvable, every alibi room exists
- [x] Silhouette check of all 33 characters
- [ ] Playtest the slice in Unity and fill in Docs/TEST_REPORT.md

## Milestone 18: The Club Handbook and a README you can watch
- [x] First-time hint cards for ten moments of a night (HQ, the drive, clues, the board, accusing, panic, the trap, playing the Haunter, errands, case closed)
- [x] F1 opens the handbook page; hints are saved per machine and can be shown again
- [x] Animated README: progress tracker read from this file, every round on a timeline, one night start to finish, the cast turning
- [ ] See the hints on screen in Unity and adjust the wording after a first playtest

## Milestone 19: The design pass
- [x] One interface theme (`UI/UITheme.cs`): colour roles, four type sizes, spacing steps, flat surfaces
- [x] HUD, Suspect Board, town map and handbook restyled; panels and toasts no longer overlap at 720p
- [x] Text size and reduced-motion settings on the handbook page (F1)
- [x] README reorganised around overview, features, setup and design; the full tour moved to Docs/GUIDE.md
- [ ] Check the new look in Unity at 720p, 1080p and 4K

## Milestone 20: The Case Book
- [x] Direction picked from three concepts: the club's paperwork, a corkboard and evidence-tag red
- [x] Fraunces and Atkinson Hyperlegible shipped with the game (Resources/Fonts, SIL Open Font License)
- [x] Suspect Board as a corkboard: clue tags, pinned cards, red string, a real strikethrough, cards that swing
- [x] Town map pins and string to tonight's call; hint cards pinned up; keys in bold ink
- [x] Website in site/ with light and dark modes and a playable Suspect Board built from Cases.cs
- [x] Website published by GitHub Actions (`unmasked pages`), previewed with `unmasked site`
- [x] Suspect Board works by keyboard in the game (arrows pick, H, X, C, A twice to accuse)
- [x] Website remembers solved cases, shows each legend's portrait, and has a link preview picture
- [ ] Check the board's swing and string in Unity, and turn the site on once the repo is public

## Milestone 21: Ready for the first Unity session
- [x] Smoke test that plays a whole night by itself: host, call, drive, clues, accusation, trap, unmasking, next night
- [x] Any error or exception during the run fails it; saved progress is put back afterwards
- [x] Unmasked > Check Project Data: every level, costume, case and font file loads
- [x] `unmasked smoke` runs it headless from a terminal with an exit code
- [x] Docs/FIRST_RUN.md: the first session step by step, and what to send back
- [ ] Run the smoke test in Unity and fix whatever it finds

## Milestone 22: The website's moving pictures
- [x] "How a night goes" plays as a scroll-driven scene, dusk to dawn, with the timeline kept for phones and screen readers
- [x] Solving a case knocks the Haunter's mask off the culprit's card
- [x] Section headings set themselves word by word; the front-page board leans toward the mouse
- [x] All of it switches off with reduced motion, and the site still passes axe in both modes
- [ ] Watch it on a real phone and a slow laptop once the site is live

## Milestone 23: Moments in the game
- [x] An hour card under the phase bar for the van, the house, each hour of the investigation and the trap, worded for your side
- [x] The unmasking plays out: the mask dips, flies off, and the culprit's name types in
- [x] Both fall back to plain fades with Reduce motion on, and hide while the board or map is open
- [ ] See both in Unity at 720p and 4K, and tune the timings by feel

## Milestone 24: Playing together in one house
- [x] Hosts announce themselves on the Wi-Fi, and the Join screen lists them with a one-click Join
- [x] Each game shows the host's computer, how many are playing and what they're doing
- [x] A different version shows up greyed out instead of failing to connect
- [x] The last address you joined is remembered
- [ ] Try it on two computers on one Wi-Fi, and check the Windows firewall prompt

## Milestone 25: A town worth walking
- [x] Seven new side streets, each laid only where it fits, with lamps, sidewalks and trick-or-treaters
- [x] 35 more houses in five styles, each with a porch, path, mailbox, fence or hedge and a yard dressed by Wave Function Collapse
- [x] Eight landmarks: corn maze, cemetery and crypt, mill pond, orchard, pumpkin farm, scout camp, hayride field, park
- [x] Every part of town has a name, so "where am I?" always has an answer
- [x] 24 lost lanterns to find, shown on the map once found
- [ ] Walk the whole town in Unity and check the frame rate with the new houses

## Milestone 26: The Club Book
- [x] 34 challenges in six chapters, finished automatically, none of them timed or expiring
- [x] Candy earned only by playing; a Wardrobe of 17 looks that everyone in the game sees
- [x] A Play button on every house: the call list, the map card, the house challenges and the website
- [x] A gentle "good place to stop" after three nights in a row, which can be turned off
- [ ] Play ten nights and tune the candy prices so the Wardrobe takes a fair while, not forever

## Milestone 27: Trick or treat
- [x] A family, a house number and a porch light at all 35 doors on the new streets
- [x] Knock where the light is on: a treat once per door per night, and who's home changes nightly
- [x] Twelve Stories of Hollow Creek told at the doors, kept in the Club Book's Stories tab
- [x] Neighbours who point you at the nearest lost lantern
- [x] A Trick or treat chapter (six challenges), a pumpkin pail and a scarecrow hat, a knock sound
- [ ] Knock on a few doors in Unity and check the prompt, the bowl and the bubble read well

## Milestone 28: The storybook lighting pass
- [x] A teal night: ambient, fog, moon, sky and mist; a teal-and-amber colour grade
- [x] Toon shader: teal shadows, creek mist that lit windows shine through, a painted edge on lamplight
- [x] Violet only for hauntings: fear, the haunted lot and the Haunter's own view (StoryLight)
- [x] Amber near HQ and a gold swell at the unmasking
- [x] Warm window light in several shades, curtains, a few television glows; the same windows lit on every build
- [ ] See it in Unity and tune the mist, the edge and the haunting by eye

## Milestone 29: Storybook cast and the Hook Board
- [x] Storybook proportions for everyone: heads 1.3x, eyes 1.18x, hands 1.14x (make_costumes.py)
- [x] A silhouette for each role: Sleuth capelet and coat, Techie headphones and aerials, Brawn gloves and boots, Snacker round with a bobble hat
- [x] The Hook Board outside the Historical Society: 24 named hooks, hang found lanterns (+5 candy each)
- [x] Every filled hook lowers the creek mist across town; all 24 makes the Club the new Lantern Watch
- [x] Two new challenges (42 in all)
- [ ] In Unity: check the board sits clear of the path and the bigger heads clear doorways and the van roof

## Milestone 30: Wisps and moods
- [x] Will-o'-the-wisps off the creek that lead to a lantern you've missed (or the Hook Board), between cases only
- [x] A rumour about the creek lights and a Follow the light challenge (43 in all)
- [x] Face moods: happy, worried, surprised and cross, the same for every suspect
- [ ] In Unity: follow a wisp end to end and check it never gets stuck, and that the moods read at a few metres

## Milestone 31: The carving bench and the trick-or-treaters
- [x] A carving bench outside HQ: pick eyes, nose and mouth, see it on the bench, carve one a night
- [x] A lit porch row along the HQ wall that keeps your last six jack-o'-lanterns
- [x] Two new challenges (45 in all)
- [x] Trick-or-treaters with storybook heads, real eyes, cheeks and a smile; mummy and bat costumes
- [ ] In Unity: check the bench and porch sit clear of the door and the van, and the panel reads at every text size

## Milestone 32: The club camera
- [x] P takes a snapshot: flash, shutter, an instant photo that develops in the corner
- [x] A twelve-frame album in the Club Book (landmarks, a neighbour, a wisp, the Hook Board, your porch)
- [x] Neighbours turn and smile for the camera; suspects look startled, all alike
- [x] Two new challenges (47 in all)
- [ ] In Unity: check the photo crop, the album at every text size, and that walls block a sight

## Milestone 33: The lamplighter
- [x] Tobias Wick, the old lamplighter: stooped, greatcoat and muffler, flat cap, spectacles, mutton chops; blinks, talks and smiles (FaceLife)
- [x] Twelve gas lamps on the creek bank by the Creekside Path, dark until you light them with his pole; they stay lit
- [x] Lit lamps glow amber with a warm pool of light and two moths each; the dark ones show a blue pilot
- [x] Bring the pole back with every lamp lit: the Lamplighter's cap, a Wardrobe look that's a gift, never sold
- [x] A new challenge (48 in all), a thirteenth album frame, a map pin and lamps on the map, a Handbook hint
- [x] With the whole path lit, the creek's wisps rise a little more often
- [ ] In Unity: walk the path, check the lamp lights and Tobias's face, the pole on each role, and the cap on each head

## Milestone 34: Past the edge of town
- [x] Six haunted places joined to town by lit roads: Ravenhold Castle, the Moonlight Circus, Gloamwood Tower, Gull Harbor with Saltmarsh Lighthouse, Wreckers' Beach with Smugglers' Cave, Hag's Hollow
- [x] Five wayside spots between them: the Nine Widows, a scarecrow field, a wishing well, Whisker Hill, an old mine
- [x] 32 curiosities with little stories (E to examine), a Curiosities page in the Club Book, and the Explorer's hat for finding them all
- [x] Moving pieces: flags, carousel, Ferris wheel, lighthouse beam, tower beacon, crane hook; first-visit stories and two climbs
- [x] The map covers the whole world, with the places named and found curiosities starred; six new album frames; seven new challenges (55 in all)
- [x] A character detail pass: two-tone irises, second glints, lower lashes, blush, fingernails, laces and cuffs, cuter trick-or-treaters
- [ ] In Unity: drive every road, climb the lighthouse stair and the fire escape, check the moving pieces and the frame rate with the whole world loaded

## Milestone 35: A painted menu and free assets
- [x] A storybook night behind the first menu (sky, moon, drifting hills, manor window, fog, fireflies, grain), still with Reduce motion
- [x] A short dip through dark between the menu and the town
- [x] `unmasked import`: free CC0 (and known CC BY) sounds and models dropped into Incoming replace the built-in ones, with credits
- [x] The website shows the menu and the world map on CSS-drawn devices
- [x] First Unity compile (6000.6.5f1 on Alek's PC): the 2 errors fixed (missing screen-capture module), and the case check now catches a missing module
- [x] Club camera photos look printed (ordered-dither ink and cream paper)
- [ ] Download Kenney's Halloween Kit and a CC0 sound pack on a machine that can reach them, import, and listen and look in Unity

## Milestone 36: A town of haunts
- [x] Twelve one-of-a-kind buildings on the town's streets (cinema, bakery, school, town hall, hotel, toy shop, music hall, creamery, gazette, apothecary, depot, laundromat)
- [x] A haunt in each: three violet signs to read, then a ghost to catch three times; violet names on the map, green once busted
- [x] A "Haunts in town" chapter (three challenges, 58 in all) and the Haunt Buster's cap
- [x] Softer people: boots, belts, bibs, collars and cuffs with rounded edges on the whole cast
- [ ] In Unity: bust a haunt start to finish, check the soft shapes in the editor and on a build

## Milestone 37: Step inside the haunts
- [x] Each haunt's ground floor is a walk-in room with an open doorway, furnished for its haunt
- [x] The ghost's last hiding spot is indoors, so every bust ends inside
- [ ] In Unity: walk into each haunt, check the camera under the ceiling and the doorway height

## Milestone 38: Nicer people, livelier streets
- [x] Chunky storybook hands on every person (round palm, plump fingers held together, thumb, nails)
- [x] Skirts and long coats flare toward the hem in soft tiers instead of one straight tube
- [x] Street life on every sidewalk: autumn trees and leaves, hydrants, post boxes, bins, newspaper boxes, street signs
- [ ] In Unity: check the hands at arm's length and the street props for frame rate across the whole town

## Milestone 39: Real bodies, full rooms
- [x] One smooth skin per person: body parts melted together, no toy-piece seams at joints (SmoothBody.cs)
- [x] Clothes keep their colours across the smooth skin; faces, hair, hands and shoes stay on top
- [x] Every room furnished for what it is: 276 pieces, 92 paintings, 18 rugs (roomdetail.py)
- [ ] In Unity: check how long the skins take to build on the first night, and look at faces up close

## Milestone 40: Faces and lived-in rooms
- [x] Noses grow out of the face; softer jaws and cheeks; one-piece palms; hair as one soft mass
- [x] Head, hair and hands built on a grid twice as fine as the body
- [x] Curtains on brass rods at every indoor window (109)
- [x] Things left out on tables, desks and counters (89 table tops)
- [ ] In Unity: check the finer heads still build quickly on the first night

## Milestone 41: One smooth body and front gardens
- [x] Barrel chests melt into the body; beards, mutton chops and bald rings melt into soft hair
- [x] Skin relaxed with Taubin smoothing (ripples gone, volume unchanged)
- [x] Window boxes under all 62 front windows of the 23 homes
- [x] Foundation shrubs, path borders with lantern stakes, clipped hedge crowns
- [x] Rocking chairs on 17 porches; a leaf pile or a wheelbarrow of pumpkins in every yard
- [ ] In Unity: check the relaxed skins still build quickly on the first night

## Release pipeline
- [x] One-click test room generator
- [x] Player builds for Windows, macOS, Linux (menu, terminal, GitHub Actions)
- [x] Downloads published on GitHub Releases from a version tag
- [x] Offline compile check: every script builds against Unity's DLLs with no errors
- [x] First open in Unity: turns on the Input System, offers to build the town, opens it; Unmasked > Play Hollow Creek
- [ ] First compile in Unity and fix errors
- [ ] First real in-game screenshots (F12) in the README

## Later
- [ ] Real characters, house art, audio
- [ ] Styled UI (UI Toolkit) to replace the debug HUD
- [ ] Several cases per house, campaign
- [ ] Lobby and online matchmaking (Unity Relay)
<!-- progress:end -->
