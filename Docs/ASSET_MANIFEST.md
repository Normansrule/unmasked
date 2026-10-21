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
| In-game text | `Assets/Unmasked/Resources/Fonts` (Fraunces, Atkinson Hyperlegible), falls back to Unity's LegacyRuntime font | Fraunces by Undercase Type; Atkinson Hyperlegible by the Braille Institute | SIL Open Font License 1.1, licence texts next to the fonts |
| Website fonts | `site/fonts/*.woff2` | Subset from the same fonts | SIL Open Font License 1.1, licence texts in `site/fonts` |
| Website house pictures | `site/img/*.jpg` | Cropped from `Reference renders` | The project's own renders, not Unity |
| Website case data | `site/data/game.json` | `Docs/tools/make_site_data.py`, read from `Cases.cs` and `PROGRESS.md` | Original |
| Website screenshots and GIFs (`site-*.png`, `site-*.gif`) | `Docs/images` | `Docs/tools/make_site_pictures.py` (Playwright) | Real browser screenshots of `site/` |
| Interface mockups (`hud-refresh.png`, `hud-board.png`) | `Docs/images` | `Docs/tools/make_readme_anim.py` | Drawn from the UITheme colour and type tokens over a Reference render; mockups, not Unity |
| Animated README pieces (progress tracker SVG, rounds, one night, cast, handbook GIFs) | `Docs/images` | `Docs/tools/make_readme_anim.py` | Drawn from PROGRESS.md and the other README pictures; illustrations, not Unity |
| README pictures and Reference renders | `Docs/images`, `Reference renders` | `Docs/tools/make_images*.py`, `render3d.py` | Rendered by the project's own renderer, not Unity |
| Fonts in the README pictures | `Resources/Fonts` (Fraunces, Atkinson Hyperlegible); embedded subset in the tracker SVGs | Same as in-game | SIL Open Font License 1.1 |

## Reference material (study only, never shipped)
Alek's reference uploads are kept outside the project: the story and art direction pack, the
visual reference guide, screenshots of Beacon Pines, Luigi's Mansion 3 and Pumpkin Jack, the Game
Builder's atlas and brief, and the Tinykin / I Am Future contact sheet. They are copyrighted and
used only to study principles. None of their images, names or designs are in `Assets/` or `Docs/images`.
