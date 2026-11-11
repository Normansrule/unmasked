# Test report (round 46, 2026-11-10)

**First real Unity compile (round 41).** On 2026-11-09 Unity 6000.6.5f1 opened the project on
Alek's PC in batch mode (`Logs/build.log`). It upgraded the packages to their 6000.6 versions and
compiled every script with **2 errors**, both `The name 'ScreenCapture' does not exist`
(`UI/Snapshots.cs`, `UI/GameHUD.cs`): the screen-capture module wasn't in `Packages/manifest.json`.
Round 41 adds it (and image conversion), and `tools/casecheck/casecheck.py` now fails when a script
uses a built-in module the manifest doesn't list. The other messages were warnings: 6000.6 marks
`FindObjectsSortMode` as obsolete (fine on the pinned 6000.0.32f1). Nothing has been played yet;
the next Unity run should compile clean.

**Not played in Unity yet.** These are the checks that could be run offline in the build container
(Linux, Python 3, .NET 8), and what still needs a person with Unity.

## Run and passed

| Check | Command | Result |
|---|---|---|
| Every C# script compiles against Unity's DLLs (runtime and editor) | `bash tools/compilecheck/check.sh` | 0 errors, 0 warnings |
| Netcode RPC naming | same script | 0 problems |
| Every case can be solved | `python3 tools/casecheck/casecheck.py` | 9 cases, 0 problems |
| Every built-in Unity module a game script uses is in `Packages/manifest.json` | same script (prints "Unity modules: 12 listed, none missing") | pass; it reported the 2 missing modules before the fix |
| The smooth skin (round 45) builds for all 30 outfits as a closed surface with its triangles facing out (every edge shared by exactly two triangles, positive volume) | a one-off Python check over `smoothbody.build()` for every outfit | 30 built, all facing out; 29 perfectly closed, the Snacker has 4 edges where two bits of skin just touch (draws fine) |
| Room furniture (round 45) overlaps no wall, stair, door, possessable or other piece, and no two pieces share a name | a one-off Python check of the 6 layout files after `make_manor.py`, `make_houses.py`, `make_town.py` | 0 overlaps, 0 duplicates; every other piece is unchanged |
| The round 46 skin (each limb, the head, the hair and each hand meshed on its own) builds for all 30 outfits with every piece facing out | a one-off Python check over `smoothbody.build()` for every outfit, piece by piece | 30 built, 308 pieces, 0 facing in; 15 outfits have 1 to 15 edges where two bits of skin just touch (the same harmless kind as the Snacker in round 45) |
| Curtains and table-top still lifes (round 46) overlap no wall, stair, door, possessable or other piece, and no two pieces share a name | a one-off Python check of the 6 layout files after `make_manor.py`, `make_houses.py`, `make_town.py` | 0 overlaps, 0 duplicates; only additions (109 curtained windows, 89 still lifes) |
| No street prop (tree, hydrant, post box, bin, newspaper box, sign) stands on a road or sidewalk, and no town piece shares a name | a one-off Python check of `HollowCreek.json` | 0 on roads, 0 duplicates |
| Each of the 12 town haunts has three signs, three hiding spots and a matching `HauntBust.Total` | `python3 tools/casecheck/casecheck.py` (prints "12 haunts in town") | pass |
| No two town pieces share a name, and the haunt buildings overlap no road or each other | a one-off Python check of `HollowCreek.json` | 0 duplicates, 0 overlaps |
| Website accessibility (axe-core 4.10) at 1440 and 390 pixels wide, light and dark | Playwright in headless Chromium | 0 violations |
| Website has no sideways scroll at 390, 768, 1024 and 1440 pixels, or at 200% text | same | none |
| Website touch targets on a phone are at least 44 pixels | same | all, except the inline "Releases page" link in a sentence (allowed) |
| Every website text colour pair reaches 4.5:1 contrast, light and dark | computed from the tokens | all pass (lowest 4.72) |
| Website plays every case to a win and a loss; loading and error states show (including opened from a file) | Playwright | pass |
| Website remembers a solved case after a reload, and "Clear it" empties the case book and keeps keyboard focus | Playwright | pass |
| No hero card covers the board's caption at 390 to 1920 pixels wide | Playwright | pass |
| The scroll-driven night plays every chapter at 1440 pixels, falls back to the timeline below 861 pixels and with reduced motion, and logs no errors | Playwright | pass |
| The mask fly-off plays on a win (a fade with reduced motion) and removes itself afterwards | Playwright | pass |
| The importer takes a known CC BY pack and a CC0 pack, skips a pack with no licence, matches "Woosh" to whoosh, and writes the credits | `python3 tools/import_incoming.py --apply` on a test Incoming folder | pass |
| The menu backdrop's picture matches its code (same numbers ported to Python) | `python3 Docs/tools/make_images_menu.py` | menu-backdrop.png, looked at |
| Website "Past the edge of town" devices: no sideways scroll at 375 and 1366 pixels, light and dark; images load; axe 0 violations | Playwright + axe-core 4.10.2 | pass |
| The world past the town: no new solid piece overlaps anything in town, no two pieces share a name, the town file has 6 places and 32 curiosities and the C# counts agree | `python3 Docs/tools/make_town.py`, a one-off overlap script, and `python3 tools/casecheck/casecheck.py` (prints "World: 6 haunted places, 32 curiosities") | pass |
| The album's view point for each haunted place isn't buried inside a solid piece | a one-off script over HollowCreek.json | pass |
| The grown town: every lost lantern is clear of walls, stones and tents, and the town is 7,799 boxes | `python3 Docs/tools/make_town.py` (prints "24 lost lanterns (24 clear of walls)") | pass |
| No new solid box sits on a street | a one-off script over HollowCreek.json this round | pass |
| Only the trick-or-treat costumes changed in the town file this round (mummy and bat added) | `python3 Docs/tools/make_town.py`, compared with round 35's HollowCreek.json | pass |
| Round 35: only the townsfolk rumours changed in the town file (one new line about the creek lights) | `python3 Docs/tools/make_town.py`, compared with round 34's HollowCreek.json | pass |
| The town file comes out byte-for-byte the same on every build (lit windows used Python's per-run hash() before this round, so they changed every time) | `python3 Docs/tools/make_town.py` run twice, compared with md5sum | pass |
| Every one of the 35 homes has a unique family and address (no clash with 1 Founders Way, 3 Willow Lane or 14 Elm Street), and each of the 12 stories is told at exactly one door | `python3 Docs/tools/make_town.py` plus a check over HollowCreek.json | pass |
| `unmasked` picks Unity right: the exact 6000.0.32f1 first, then the newest 6000.0.x, and with only a newer Unity 6 it stops and explains unless told to upgrade; a missing log says Unity never started | `bash tools/unmasked.sh check` and `doctor` with stand-in installs in a temporary home folder | pass |
| The WSL check prints the interop fix and stops when Windows programs can't run | `ensure_interop` with WSL forced on in the build container (no interop there) | pass |
| Costumes.json has Tobias Wick ("Folk.Lamplighter", 133 shapes) with FaceLife's face parts named as before | `python3 Docs/tools/make_costumes.py`, checked in lamplighter.png | pass |
| Costumes.json rebuilds with storybook proportions: every person's head, hair and hat grow about the top of the neck and nothing else moves (the Techie's backpack aerials are left alone) | `python3 Docs/tools/make_costumes.py`, checked in storybook-cast.png | pass |
| The website's "Things to do" shows 7 chapters, 48 challenges, 20 looks (the cap marked "A gift") and the first story, with no sideways scroll at 390 and 1440 pixels and 0 axe violations in light and dark | Playwright, axe-core 4.10 | pass |
| The website's "Things to do" section lists 8 places, 24 lanterns, 6 chapters with 34 challenges and 17 looks, and every Play button opens its case | Playwright | pass |
| "Things to do" has no sideways scroll at 390 and 1440 pixels, and axe finds 0 violations in light and dark | Playwright, axe-core 4.10 | pass |

What the case checker proves for all nine cases:
- Any two of the culprit's three traits name exactly one suspect, for every possible culprit.
- Each case has 4 suspects, 4 motives, 8 traits and 8 clues with different ids.
- Every alibi room exists in the house or the town, so every alibi can be checked.
- Case ids are unique, and each return visit comes after its first case.

## The smoke test (round 26)

The game can now test itself in Unity: **Unmasked > Run Smoke Test** (or `unmasked smoke`) plays
one night start to finish and fails on the first broken step or on any logged error. It has not
been run yet, because it needs Unity; it compiles against Unity's libraries like everything else.
Running it is step 3 of [FIRST_RUN.md](FIRST_RUN.md), and its report replaces most of the
"Needs a Unity playtest" table below.

Since round 29 the "Catch and unmask" step walks the test Solver away from the armed trap and
waits up to 75 seconds, because the costumed stand-in won't go near a guarded trap.

## Found and fixed in round 25
- **A card covered the front page caption.** At most widths Leonard Crisp's card overlapped "Any two true clues…". The caption now hangs under the board.
- **Legend names overflowed at 200% text.** The portrait and text now stack when the text column would get too narrow.
- **The terminal block hid the end of the clone command.** It wraps now.
- **The website jumped on load.** Selecting the first case tab scrolled the whole page down to it. The tab strip now scrolls on its own.
- **Phones scrolled sideways.** The terminal block in "Get the game" pushed its column wider than the screen.
- **Accuse was too loud.** Four filled red buttons on the board drowned the red string. Accuse is now outlined and only fills red when pressed, in the game and on the site.
- **Reduced motion turned everything off.** It now swaps movement for fades, so a wrong guess still shows (a red outline instead of a shake).
- **Hard-coded colours.** The minimap pins, card shadows and the map's dark overlay used raw colours; they now come from the theme.

## Found and fixed in round 24
- **Favours could be lost.** Favours earned after a case ended were spent when the club drove back to HQ, then thrown away when the next call loaded a different case. Favours are now spent only when an investigation starts (`MysteryGameManager.BeginInvestigation`), and they are saved.
- **Errands weren't saved.** Errands, favours and costume pieces only lived in memory, so quitting lost them. They are now saved on the host. A Done errand stays Done, so its rewards can't be collected twice.
- **Two suspects looked alike.** Pemberton Cottage's Heiress and Cook had the same silhouette. Beatrice Hollis now has a shawl and a cane.

## Needs a Unity playtest (not verified)

| What to check | Why it isn't verified |
|---|---|
| The ToonSpooky shader still compiles with the storybook additions (teal shadows, creek mist, painted edge, violet haunting) | Shaders can't be compiled outside Unity; written against Unity's surface shader rules (finalcolor, no mist in the additive light passes) |
| You can walk into every haunt through its doorway, the camera stays under the ceiling, and the ghost's last hiding spot inside is reachable | New in round 43; checked offline that no outside piece pokes into a room and the last spot is clear of furniture, not walked in Unity |
| Soft street props (hydrants, post boxes, bins) show rounded in the built town, and ~110 extra props keep the frame rate | New in round 44; `ManorBuilder` now adds `SoftBox` to `rbox`/`rcyl` layout pieces, not built in Unity yet |
| A haunt plays start to finish: the three signs light up and say their lore, the ghost appears only after all three, hops between its hiding spots, and the third catch busts it (toast, sound, map turns green, signs fade) | New in round 42 (`Town/HauntBust.cs`); only seen as haunts.png |
| Soft boots, belts and collars show rounded in the editor and in a build, with no missing mesh after a domain reload | New in round 42 (`Spooky/SoftBox.cs` makes its mesh in code with `[ExecuteAlways]`) |
| The menu backdrop draws behind the first menu at any window size, drifts smoothly, holds still with Reduce motion; the dip through dark plays once when you host or join and when you leave | New in round 40 (`UI/MenuBackdrop.cs`); only seen as menu-backdrop.png |
| Dropped-in sounds play instead of the synthesized ones; a dropped-in .fbx/.obj replaces its prop at the right height and sits on the ground | New in round 40 (`Spooky/Sfx.cs`, `Editor/ManorBuilder.cs`); needs real packs in Incoming |
| The haunted places: the roads are drivable, the castle ramp, the lighthouse's spiral stair (0.25 m steps) and the tower's fire escape can be climbed, nothing blocks the way in | New in round 39 (`Docs/tools/regions.py`); only seen in the Python renderer (world-map.png, regions.png) |
| Moving pieces (flags, carousel, Ferris wheel, beam, beacon, bobbing) move and aren't static-batched; frame rate with the whole world (about 13,500 boxes) | New in round 39 (`Town/WorldLife.cs`, `Editor/ManorBuilder.cs`) |
| Curiosities: each twinkles, E shows its story, it stops twinkling once found, the map stars it, the hat is given for the last one | New in round 39 (`Town/Curio.cs`) |
| The new faces: two-tone irises, glints and blush line up on every head, and FaceLife still finds its parts | New in round 39 (`make_costumes.py`); drawn in characters-detail.png only |
| The lamplighter: Tobias talks and lends the pole, the pole shows on your side and hides in the van, E lights each lamp once and it stays lit after a restart, the cap is given with all twelve lit, the map shows him and the lit lamps | New in round 38 (`Town/Lamplighter.cs`); shapes drawn in lamplighter.png and creekside.png only |
| `unmasked build` on WSL: the Exec format error is caught before Unity runs and the fix is offered; with only a newer Unity installed the tool asks before upgrading | New in round 38 (`tools/unmasked.sh`); tested here with stand-in Unity installs, not on Windows |
| The club camera: P captures, the card develops, the right sight is picked, walls block it, PNGs save and load back into the album, neighbours turn and smile | New in round 37 (`UI/Snapshots.cs`); drawn as a mockup in snapshots.png only |
| The carving bench: E opens the panel, the bench pumpkin follows each choice, Enter carves once a night, the porch shows the last six, movement and the camera are locked while it's open | New in round 36 (`Town/CarvingBench.cs`); shapes drawn in carving.png only |
| The new trick-or-treaters: heads, eyes and hats line up, mummy and bat costumes look right walking | New in round 36 (`Town/TownLife.cs`); drawn in kids.png only |
| A wisp: rises only near the creek between cases, leads to the nearest unfound lantern, waits when you lag, floats over walls, goes out on arrival or after 90 seconds alone | New in round 35 (`Town/Wisp.cs`); only seen in the Python renderer |
| Face moods: brows, lids, mouth and cheeks move the right way and settle back to calm | New in round 35 (`Animation/FaceLife.cs`); the same numbers drawn in moods.png |
| The Hook Board: it sits clear of the Historical Society's path and the afterglow party, E hangs every found lantern, the mist lowers as hooks fill | New in round 34 (`Town/HookBoard.cs`); only seen in the Python renderer |
| The storybook heads: no clipping through doorways, the van roof or the HQ shelves; earned hats sit right on the bigger heads | New in round 34; ClubLook fits hats to the head's bounds, not checked by eye |
| The StoryLight moods: violet with fear and on the haunted lot, amber at HQ, gold at the unmasking; post-processing volumes blend without popping | New in round 33 (`Spooky/StoryLight.cs`); only seen in the Python renderer with the same numbers |
| Knocking (E) at a lit door: the knock, the bowl, the bubble and the toast; a dark door says nobody's home; each door gives one treat a night | New in round 32 (`Town/Doorstep.cs`, a local-only interactable added to `SolverController`); only checked by reading the code and in the mockup |
| The pumpkin pail and scarecrow hat sit right on every role | `Spooky/ClubLook.cs`; untested in play |
| Frame rate in the grown town (about 7,800 boxes, 35 houses, 24 lantern lights) | Not measured; the lantern lights switch off past 45 m to help |
| The Club Book (K): challenges claim themselves with a toast, Play makes that house tonight's call, buying and wearing a look works, the break card shows after every third night | New in round 31 (`Core/ClubBook.cs`, `UI/ClubBookPage.cs`); only checked by reading the code and in the mockup |
| Hats and backpieces sit right on every role's outfit, and other players see your look | `Spooky/ClubLook.cs` fits them to the head's bounds; `PlayerAgent.Look` syncs it; untested in play |
| Walking into a lost lantern picks it up once and it stays gone after a reload | `Town/LostLantern.cs`, PlayerPrefs; untested in play |
| The new streets and yards can be walked without getting stuck | Placement was checked on a 1 m grid, not with Unity's colliders |
| The smoke test itself: every step passes in the editor and headless (`unmasked smoke`) | New in round 26; batch mode play needs Unity to try |
| Games on your Wi-Fi: a host shows up on another computer's Join screen, and Join connects | New in round 30 (`Net/LanDiscovery.cs`). The same socket calls were tried in .NET 8 on Linux: a broadcast reached two listeners sharing the port (two windows on one computer), and the loopback copy reached one. Not tried on Windows, across two computers, or through the Windows firewall |
| With nobody playing the Haunter, the named suspect puts on the costume, keeps away from the club, finds its way through doors and walks into an armed trap nobody guards (the smoke test now steps back and waits for this) | New in round 29 (`AI/StandInHaunter.cs`); the rules were tried in a Python copy on a two-room plan (`standin.gif`), not in Unity |
| The hour card drops in on each phase and each new hour, and the unmasking mask flies off before the name types in | New in round 28 (`UI/Moments.cs`); the timings were checked in a mockup drawn with the same numbers, not in Unity |
| The corkboard Suspect Board: cards swing and settle, string lands on the pins, two columns below 900 points wide | IMGUI drawing only checked by reading the code and in the mockup |
| The Fraunces and Atkinson fonts load from Resources/Fonts and fall back to Unity's font if missing | `Resources.Load` is untested in a build |
| Suspect Board keys: arrows and 1 to 4 pick a card and scroll to it, H, X and C act on it, A needs a second press within 3 seconds | New this round; key handling only checked by reading the code |
| The keys don't also move the player while the board is open | Movement checks `CameraRig.InputLocked`, which the board sets; untested in play |
| The new interface theme looks right at 720p, 1080p and 4K, and nothing overlaps | Laid out with Unity's GUI scale matrix; only checked in the README mockups |
| The text-size and reduced-motion settings (F1 page) apply at once and are remembered | New in round 24 |
| Clicking the setup panel still frees the mouse correctly with the GUI scaled | The mouse position is now converted to GUI points (`UITheme.ToGui`) |
| Each Handbook card appears once at its moment, F1 opens the page, "Show hints again" works | New in round 23; IMGUI layout and timing only checked by reading the code |
| The hint card doesn't cover the trap or unmasking prompts | Its spot at the bottom of the screen was picked without seeing the HUD in Unity |
| The trunk prompt appears at HQ and toggles the costume for every client | Untested networking. `WearingWatch` is a NetworkVariable read by `WatchCostume` |
| Watch pieces sit right on all four Solvers at their new heights | Only checked in the README renderer |
| A solved house's party appears for a client who joins later | `HouseMood` reads `SolvedCases`, which should sync on join |
| The banner text fits the cloth | The TextMesh size comes from the renderer estimate, not Unity |
| Quit and reload keeps errands, favours and pieces; Start over clears everything | PlayerPrefs logic is untested |
| Performance with about 100 shapes per character and the yard parties | Not measured on any device |
| A new player finds the trunk and understands the costume without being told | No player test yet |

## Known issues
- The project has not been opened in Unity. The first open may surface errors the offline compile check can't see, such as Netcode's own build-time checks and Unity 6 deprecations.
- All pictures in `Docs/images` and `Reference renders` come from the project's own software renderer, not from Unity.
