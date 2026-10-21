# Test report (round 25, 2026-10-20)

**Not tested in Unity yet.** The project has never been opened in the Unity editor, so nothing below
was played. These are the checks that could be run offline in the build container (Linux, Python
3, .NET 8), and what still needs a person with Unity.

## Run and passed

| Check | Command | Result |
|---|---|---|
| Every C# script compiles against Unity's DLLs (runtime and editor) | `bash tools/compilecheck/check.sh` | 0 errors, 0 warnings |
| Netcode RPC naming | same script | 0 problems |
| Every case can be solved | `python3 tools/casecheck/casecheck.py` | 9 cases, 0 problems |
| Website accessibility (axe-core 4.10) at 1440 and 390 pixels wide, light and dark | Playwright in headless Chromium | 0 violations |
| Website has no sideways scroll at 390, 768, 1024 and 1440 pixels, or at 200% text | same | none |
| Website touch targets on a phone are at least 44 pixels | same | all, except the inline "Releases page" link in a sentence (allowed) |
| Every website text colour pair reaches 4.5:1 contrast, light and dark | computed from the tokens | all pass (lowest 4.72) |
| Website plays every case to a win and a loss; loading and error states show (including opened from a file) | Playwright | pass |
| Website remembers a solved case after a reload, and "Clear it" empties the case book and keeps keyboard focus | Playwright | pass |
| No hero card covers the board's caption at 390 to 1920 pixels wide | Playwright | pass |

What the case checker proves for all nine cases:
- Any two of the culprit's three traits name exactly one suspect, for every possible culprit.
- Each case has 4 suspects, 4 motives, 8 traits and 8 clues with different ids.
- Every alibi room exists in the house or the town, so every alibi can be checked.
- Case ids are unique, and each return visit comes after its first case.

## Found and fixed this round
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
