# UNMASKED: story and art direction

This is the direction Alek set on 2026-10-12. It steers every round of work. The reference games
and films below are **study material only**: none of their artwork, characters or designs go into
the game or its marketing.

## The promise

**Solve the haunting. Unmask the person.**

UNMASKED is a storybook Halloween detective adventure, not a horror game with cute characters.
Hollow Creek should be a place players enjoy visiting; the hauntings give them a reason to explore
its houses, meet its residents and uncover their secrets. Rough mood target: 70% comfort, 20%
curiosity, 10% startle. No gore, no long helpless chases, no face-filling screams.

## The story

Hollow Creek's old folklore masks were brought out for the Halloween festival. Whoever wears one
can really haunt a house: possess furniture, wail, throw pumpkins. Tonight a resident is using one
to cover up something ordinary: a theft, a sabotage, a forged claim. Pulling off the mask ends the
haunting.

- **Which mask** is in play is announced at the start (the Haunter's legend).
- **Who is wearing it** is the case. Each suspect has a motive, revealed only for the one unmasked.
- A suspect being jumpy is personality, not proof. Everyone hesitates before answering, guilty or not.
- The Haunter can distract, block a route for a while or plant a decoy that can be disproved, but it
  must never make the case unsolvable.

## The Mask Keeper

The thread through every case: none of the culprits took a mask on their own. Each solved case adds
one clue to the case book about who lent it (a loan tag, a note on a porch, lavender and old paper, a
key signed out to E. Wren). With all four solved, the finale: Edie Wren, the Historical Society's
curator, lent the masks out hoping real hauntings would bring visitors back to the closing museum.
Gentle, human, and put right at the end, like every case.

## The houses and their cases

| House | Look | Case | What it teaches |
|---|---|---|---|
| Pemberton Cottage | Hearth, patchwork rugs, crowded pantry, tiny garden | The Missing Harvest Lantern | Physical traces and one alibi that doesn't add up |
| Hollow Creek Farm | Greenhouse/workshop feel, muddy potting room (Alek's "Rookwood" idea) | The Sabotaged Prize Display | Opportunity, access, misleading traces |
| Willow Lane Victorian | Faded lilac walls, music room, family photos (Alek's "Briarbell" idea) | The Interrupted Recital | Testimony against a timed event |
| Blackwood Manor | Grand staircase, library, old theatre, service passages | The Missing Blackwood Ledger | Motive, access and timeline together |

Houses get more intricate as the game goes on, not just bigger.

## Visual vocabulary

- **Warm amber:** welcome, HQ, the festival, the way home.
- **Muted teal:** night depth.
- **Soft violet:** an active haunting.
- **Parchment:** documents and the Suspect Board.
- **Sage:** everyday objects and clothes.

Pair every gameplay colour with a shape, symbol or label. Light the way with a few strong
practical lights (porch lamps, lanterns, windows) rather than flat orange everywhere.

## Animation: anticipation, action, recovery

Every scare has a readable wind-up, the surprise, and a moment to recover. In the game now:

- A possessed chair leans back before it hops, then wobbles back to rest (`PossessableObject`).
- A lamp pauses, then tips its shade toward the nearest Solver before it flickers (`PossessableLight`).
- A suspect glances away and swallows before answering, the same for everyone (`SuspectNPC`, `PawnAnimator.Hesitate`).
- The trap wobbles before it snaps shut (`TrapSite.Wobble`).

Still to do: a pumpkin lid lifting, the team reacting together at the unmasking.

## The world past the town line

Hollow Creek must never feel like a set with nothing behind it. Three ridges of hills ring the
horizon, darker the nearer they are, with valley mist at their feet and the warm lights of farms and
far towns scattered on them. Landmarks give each direction a name (Ravensford church, Gull Point
lighthouse, Hatcher's windmill, the water tower, the Thornbury ruins), and the lighthouse beam and
windmill keep the far distance alive. Roads keep going past the last house, lit and signposted, and
a forest band hides where the playable town ends. The hills follow the camera, so the horizon is
always the horizon. Keep it quiet and low-contrast: it frames the houses, it never competes with them.

## A town that's out tonight

Hollow Creek is never empty: kids in homemade costumes trick-or-treat up and down the streets with
glowing buckets, cars come and go on the roads out of town, and a late train crosses the valley.
The kids stop and talk when you come close (gossip, the museum, tonight's house), which makes the
town feel lived in and quietly feeds the Mask Keeper story. They're scenery: never clues, never in
the way.

## The people of Hollow Creek

The grown-ups in town are character pieces you can read from across the square: the mayor's top hat,
sash and chain of office, Old Nell's headscarf of coins and glowing crystal ball, the minister's
collar and candle, Dot's beehive, bandana and coffee pot, the sheriff's campaign hat and badge. They
are warm, a little funny, and never menacing, so the town feels like home between hauntings. What
they've lost glows softly where it landed, a small lantern-light in the dark to lead you there.

## The fifth call

The Historical Society is the town's memory: red brick, white columns, a clock in the pediment and
warm lamps in every window, a place that should feel safe. Inside it's hushed and amber, with masks
under glass in pools of light and one empty case behind a velvet rope. The suspects are the
museum's own people, dressed for their jobs (a watchman's brass buttons and lantern, a curator's
cardigan and inky fingers, a treasurer's waistcoat and ledger, a tea-room apron and a cake), so the
finale feels like the town unmasking itself.

## Characters

Storybook people, not mannequins: big readable heads with eyes that catch the light, brows that
carry the expression, a nose, ears and rosy cheeks; hands with fingers; arms and legs that bend;
boots, shoes and dresses that say who someone is from across the room. Faces are never frozen:
they blink, glance at whoever comes close, and talk with their lips moving.

Close up they should still hold up: irises with a lighter centre, lashes, a nose with nostrils,
two lips, hair that frames the face and falls behind it, fingers rather than mittens. And nobody is
the same size: a tall thin minister, a broad mayor, a short fortune teller. Height changes the
whole person, build only the body, so faces never stretch.

Silhouette first: everyone should be recognisable as one flat dark shape at the size you see them
in play (hat, hair, coat length, the thing in their hand). The four suspects at a house must never
share a silhouette. Check with `make_images_hub.py silhouettes` after changing an outfit.

## The van and the town

An original rounded utility van (not the Mystery Machine's colours or graphics) with maps, drawers,
mugs and keepsakes from solved cases. One compact town loop; the drive is for gossip and
atmosphere, not traffic or upgrades.

## The first playable target

The Missing Harvest Lantern at Pemberton Cottage, end to end: call at HQ, short drive, statements,
clues, one mask, the Suspect Board, one trap, an earned unmasking, back to HQ. Prove it solo, then
co-op, then against a human Haunter. Afterwards players should be able to say who did it, how and why.

## The README is part of the look (round 23)

The top of the README moves: the tracker bars fill, round cards cross-fade along a timeline, and
one night plays from HQ to the unmasking. Same rules as the game: warm amber for what's done and
welcoming, violet for the haunted, one beat of anticipation before a change. Every animation says
it is an illustration, never an engine capture, until real F12 screenshots replace them.

## Reference list (study only)

Night of the Jack (lighting), Luigi's Mansion 3 (expressive 3D, readable ghosts), Tangle Tower
(suspects and rooms), Beacon Pines (small-town warmth, cosy interiors), Costume Quest, Over the
Garden Wall, ParaNorman, Midnight Ghost Hunt (possession ideas, not its combat), Ghostbusters:
Spirits Unleashed, Night in the Woods, and the historical Headless Horseman (John Quidor, 1858)
and Baba Yaga (Ivan Bilibin, 1900) paintings. Alek's full guide with links is in the project
uploads (`Unmasked_Visual_Reference_Guide.html`).
