# Slice plan: Hollow Creek, one night at a time (round 22)

Written against the "Game Builder's" brief Alek sent on 2026-10-18. It covers the part of UNMASKED
that should be playable end to end first. Reference games are studied for one principle each.
Nothing is copied from them: no characters, names, art, maps, music, text or interface.

## References (one each, plus one supporting)

| Role | Reference | What was looked at | What Unmasked does instead |
|---|---|---|---|
| Gameplay | Costume Quest (Double Fine) | The atlas card and the official description: a small neighbourhood where exploring, helping people and costumes feed one premise, and a costume is useful, not just shown in a menu | Errands for five townsfolk each give a piece of a homemade **Lantern Watch** costume. Three pieces can be worn, every piece shows on all four Solvers, and it softens scares by 7% per piece. No combat or transformation. |
| Visual | Hollow Knight (Team Cherry) | The atlas card: cute-but-eerie characters that read by silhouette, places told apart by landmarks | A **silhouette check** of all 33 characters at gameplay size (`Docs/images/silhouettes.png`). It found one pair too alike, and Beatrice Hollis got a shawl and a cane. |
| Supporting (systems) | A persistent hub (the atlas's "place that improves" assignment) | Players should see what they changed without a popup | **The street remembers:** solved houses keep a front-yard party, the open call glows violet, and progress is saved on the host. |

Not used this round, on purpose: karts, combat arenas, companions, survival pressure. The atlas
route for Unmasked says the case (evidence, alibis, deduction) stays the centre.

The reference media was not watched or played for this round. Observations come from the atlas
text and the reference contact sheet only.

## Player promise
A night in Hollow Creek: pick a call at HQ, drive there, work out who is wearing the folklore mask
from clues, interviews and alibis, trap them and unmask them. Then go home to a town that remembers.

## The loop
1. **HQ (Setup).** Pick a call on the board, put the Lantern Watch on or take it off at the trunk, and see the case book and errands.
2. **Dispatch.** Drive the van to the house. Talk to townsfolk on the way, and pick up lost things.
3. **Investigation.** Find clues (two true ones name exactly one suspect), interview suspects, check alibis by standing in the alibi room, and accuse.
4. **Trap and unmask.** Catch the Haunter, pull off the mask, and learn why they did it.
5. **Back to HQ.** The case book, the keepsake shelf and the house's yard all change. Another night starts.

## Success, failure, recovery
- **Success:** unmask the right suspect. The case goes in the book, a keepsake goes on the shelf, the yard throws a party and the next case for that house unlocks.
- **Recoverable failure:** a wrong accusation clears that suspect and helps the Haunter, and you still have one more accusation. If the night ends (dawn, escape, out of accusations), the house is still unsolved and can be called again next night.
- **Restart:** "Next night: back to HQ" resets the houses but keeps the book. The host's **Start over** button (two presses) wipes the save.

## Authoritative state (server)
| State | Where | Read by |
|---|---|---|
| Solved cases | `MysteryGameManager.SolvedCases` | case book, keepsakes (`KeepsakeDisplay`), yards (`HouseMood`), call board |
| Tonight's call | `MysteryGameManager.ActiveHouse` / `ActiveCase` | call board, violet yard light (`HouseMood`), map |
| Errands | `Townsperson.Errand` (NotAsked, Asked, Found, Done) | lost items (`ErrandItem`), map pins, HQ panel |
| Favours | `MysteryGameManager.Favours` | spent as extra alibi checks when a case starts |
| Costume | `MysteryGameManager.WatchPieces` (bit per townsperson), `WearingWatch` | trunk prompt, Solver models (`WatchCostume`), `FearMeter` |

All of it is saved on the host in PlayerPrefs (`Unmasked.*` keys) whenever it changes.

## Scope cuts
Co-op is the existing Netcode host/join. The relay lobby, controller support and a styled UI are
not part of this slice.
