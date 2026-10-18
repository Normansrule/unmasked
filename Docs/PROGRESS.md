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
- [ ] AI Haunter wears the costume and dodges the trap

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
- [ ] Storybook lighting pass (amber, teal, violet) on the cottage first
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
