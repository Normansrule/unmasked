# Asset manifest

Everything that ships in the game is made by code in this repository. No third-party art, models,
music or fonts are in `Assets/`.

| Asset | Where it lives | Made by | Source |
|---|---|---|---|
| Characters, villains, props, the van, costume pieces | `Assets/Unmasked/Resources/Costumes.json` | `Docs/tools/make_costumes.py` | Original, built from primitive shapes |
| Town, houses, Blackwood Manor | `Resources/HollowCreek.json`, `Resources/Houses/*.json`, `Resources/BlackwoodManor.json` | `make_town.py`, `make_houses.py`, `make_manor.py`, `dressing.py` | Original layouts |
| Surface patterns (siding, shingles, brick...) | `Assets/Unmasked/Textures/Surfaces` | `make_textures.py` | Procedural |
| Sounds (29 .wav) | `Assets/Unmasked/Resources/Sounds` | `make_sounds.py` | Synthesized |
| Toon shader | `Assets/Unmasked/Shaders/ToonSpooky.shader` | Hand-written | Original |
| In-game text | Unity's built-in LegacyRuntime font | Unity | Ships with Unity |
| Animated README pieces (progress tracker SVG, rounds, one night, cast, handbook GIFs) | `Docs/images` | `Docs/tools/make_readme_anim.py` | Drawn from PROGRESS.md and the other README pictures; illustrations, not Unity |
| README pictures and Reference renders | `Docs/images`, `Reference renders` | `Docs/tools/make_images*.py`, `render3d.py` | Rendered by the project's own renderer, not Unity |
| Fonts in the README pictures | Not in the repo | Inter or DejaVu, from the build machine | Open-source fonts (SIL OFL / Bitstream Vera licence), used only to draw the pictures |

## Reference material (study only, never shipped)
Alek's reference uploads are kept outside the project: the story and art direction pack, the
visual reference guide, screenshots of Beacon Pines, Luigi's Mansion 3 and Pumpkin Jack, the Game
Builder's atlas and brief, and the Tinykin / I Am Future contact sheet. They are copyrighted and
used only to study principles. None of their images, names or designs are in `Assets/` or `Docs/images`.
