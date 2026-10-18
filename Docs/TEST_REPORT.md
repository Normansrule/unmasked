# Test report (round 23, 2026-10-18)

**Not tested in Unity yet.** The project has never been opened in the Unity editor, so nothing below
was played. These are the checks that could be run offline in the build container (Linux, Python
3, .NET 8), and what still needs a person with Unity.

## Run and passed

| Check | Command | Result |
|---|---|---|
| Every C# script compiles against Unity's DLLs (runtime and editor) | `bash tools/compilecheck/check.sh` | 0 errors, 0 warnings |
| Netcode RPC naming | same script | 0 problems |
| Every case can be solved | `python3 tools/casecheck/casecheck.py` | 9 cases, 0 problems |

What the case checker proves for all nine cases:
- Any two of the culprit's three traits name exactly one suspect, for every possible culprit.
- Each case has 4 suspects, 4 motives, 8 traits and 8 clues with different ids.
- Every alibi room exists in the house or the town, so every alibi can be checked.
- Case ids are unique, and each return visit comes after its first case.

## Found and fixed this round
- **Favours could be lost.** Favours earned after a case ended were spent when the club drove back to HQ, then thrown away when the next call loaded a different case. Favours are now spent only when an investigation starts (`MysteryGameManager.BeginInvestigation`), and they are saved.
- **Errands weren't saved.** Errands, favours and costume pieces only lived in memory, so quitting lost them. They are now saved on the host. A Done errand stays Done, so its rewards can't be collected twice.
- **Two suspects looked alike.** Pemberton Cottage's Heiress and Cook had the same silhouette. Beatrice Hollis now has a shawl and a cane.

## Needs a Unity playtest (not verified)

| What to check | Why it isn't verified |
|---|---|
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
