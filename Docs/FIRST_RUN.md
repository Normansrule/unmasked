# The first session in Unity

Nobody has opened Unmasked in the Unity editor yet. This is the shortest path from "never opened"
to "a night played", and what to send back if something breaks. It takes about twenty minutes,
most of it Unity importing.

## 1. Open the project

1. In **Unity Hub**, click **Add** > **Add project from disk** and pick the `Unmasked Game` folder.
2. Open it with Unity **6000.0.32f1**. Hub offers to install that version if you don't have it.
3. If Unity asks to restart for the Input System, click **Restart Unity**.
4. When **Welcome to UNMASKED** appears, click **Build Hollow Creek**.

**Only a newer Unity 6 installed (say 6000.6.5f1)?** It works, but the first open upgrades the
project's files. To keep the project's own version, install 6000.0.32f1 beside it: press Win+R,
paste `unityhub://6000.0.32f1/b2e806cf271c` and press Enter. From the terminal, `unmasked doctor`
lists what you have and what's missing.

**If the Console shows red compile errors**, stop here. Copy the first few lines of the Console
(or the file `Logs/check.log` from `unmasked check`) and send them over. The first error is the
one that matters; the rest often follow from it.

## 2. Check the data

Choose **Unmasked > Check Project Data**. It reads every file the game loads: the costumes, the
town, the five house layouts, the manor, the four fonts and all nine cases. A dialog says
"Every level, costume, case and font file loads", or lists what's missing.

## 3. Run the smoke test

Choose **Unmasked > Run Smoke Test (plays one night by itself)**. Unity presses Play and a panel on
the left ticks off each step as the game plays itself:

| Step | What it proves |
|---|---|
| Host a game | the network starts, the player and their Solver spawn |
| Take the first call | the HQ call board and setup work |
| Drive to the house | arriving at the lot starts the investigation |
| Find clues | clues spawn in the house and can be examined |
| Accuse the one who fits | the Suspect Board logic and the accusation |
| Build the trap | trap pieces appear, can be carried and built |
| Catch and unmask the Haunter | the test steps back from the armed trap, the culprit (in costume) walks in within 75 s, and is unmasked |
| Back to HQ for another night | the town resets for the next call |

It takes about a minute. Any error or exception logged on the way fails the run, even if every step
ticked, because those are the bugs you'd trip over by hand. The report is printed to the Console
and saved as `Logs/smoke-test.txt`, which is the file to send back. Your saved progress (solved
cases, favours, costume pieces, errands, hints) is put back exactly as it was.

From a terminal, the same thing runs headless:

```bash
export PATH="$HOME/.local/bin:$PATH"
unmasked smoke    # exits 0 on a pass; the report is in Logs/smoke-test.txt, Unity's log in Logs/smoke.log
```

## 4. Play it yourself

Choose **Unmasked > Play Hollow Creek**, then **Host a game**. Things to look at, because they've
only been checked in pictures so far:

- The Suspect Board (**Tab**): do the cards swing and settle, does the red string land on the
  pins, does it fit at your screen size? Try it with the keyboard: arrows, **H**, **X**, **C**, **A** twice.
- The town map (**M**): is tonight's call the violet pin with string from HQ?
- The Club Book (**K**): does a challenge claim itself with a toast, does **Play** set tonight's call,
  and does a bought hat sit on your head? Walk into a lost lantern near the bandstand to try a pickup.
- Walk the new side streets: can you get stuck anywhere?
- Knock on a door with its porch light on (**E**): does the bowl come out, is the bubble readable, and
  does the Club Book's Stories tab fill in?
- The storybook light: is the night teal with warm windows, does the mist sit low (not a wall of
  fog), and does violet creep in when you're scared, then go gold at the unmasking?
- The storybook cast: do the bigger heads look right in the van and through doorways, and does an
  earned hat still sit on top? Pick each role and look at their outline from across the street.
- The Hook Board: drive the van to the Historical Society with a lantern or two found, walk to the
  board on the grass left of the path and press **E**. Do the lanterns go up one by one, and is the
  mist a little lower afterwards?
- A will-o'-the-wisp: with three lanterns found, stand near the creek between cases and wait. Does
  one rise, lead you to a lantern, and go out? Does it ever get stuck on a wall?
- Moods: interview a suspect up close. Do the brows read as worried? Do neighbours smile?
- The carving bench outside HQ's east door: press **E**, try the arrows and Enter. Does the pumpkin
  on the bench change, and does your jack-o'-lantern appear lit on the porch?
- The trick-or-treaters: do the bigger heads, eyes and hats line up? Spot a mummy and a bat.
- The club camera: press **P** looking at a landmark or a neighbour. Does the photo develop in the
  corner, does the neighbour smile, and does the photo show up in the Club Book's Snapshots tab?
- Past the edge of town: drive each road out (open the map with **M** to pick one). Can you drive
  up the castle's hill, climb the lighthouse's outside stair and Gloamwood Tower's fire escape? Do
  the flags, carousel, Ferris wheel and lighthouse beam move? Find a twinkling curiosity and press **E**.
- Faces up close: do the new eye sparkles, lower lashes and blush sit right on every head?
- The hint cards: do they appear once each, and stay out of the way?
- Frame rate in town with all the townsfolk out (each person is now about 150 parts), and out at
  the haunted places (the world is about 13,500 boxes).
- Press **F12** for screenshots. They land in `Docs/screenshots`, ready to replace the mockups.

Two windows on one computer: `unmasked build`, then `unmasked play 2`. Click **Host** in one; the
other should list it under **Games on your Wi-Fi** within a second or two. Click **Join** there (or
type `127.0.0.1` if the list stays empty, and say so in what you send back).

## What to send back

- `Logs/smoke-test.txt`
- The first red Console error, if there was one
- A couple of F12 screenshots and anything that felt off
