# Offline compile check

Compiles every script in Assets/ against Unity's real engine DLLs (2021.3, with the Unity 6 members
the game uses added) and signature-only stubs of Netcode for GameObjects 2.1.1, Input System 1.11.2,
Post Processing 3.4.0 and Unity.Collections 2.2.1. Nothing in Assets/ is touched.

    bash tools/compilecheck/check.sh    # needs dotnet-sdk-8.0; the first run downloads from api.nuget.org

## Latest result (2026-10-20, round 25)
Runtime: 0 errors, 0 warnings. Editor: 0 errors. RPC naming check: 0 problems.

New this round: the Case Book look. UITheme.cs gets the paper-and-ink palette, the fonts in
Resources/Fonts, and helpers for pins, red string, struck names, the cork texture and the Swing
pendulum. GameHUD.DrawBoard is a corkboard laid out by hand in a scroll view; Handbook and TownMap
use the pins and string.

## Round 24 (2026-10-20)
Runtime: 0 errors, 0 warnings. Editor: 0 errors. RPC naming check: 0 problems.

New this round: UI/UITheme.cs (skin, colour and type tokens, GUI scale, motion helpers, text-size
and reduced-motion preferences). GameHUD, Handbook and TownMap now call UITheme.Begin() and lay out
in GUI points (UITheme.W / H) instead of raw screen pixels.

## Round 23 (2026-10-18)
Runtime: 0 errors, 0 warnings. Editor: 0 errors. RPC naming check: 0 problems.

New this round: UI/Handbook.cs (first-time hint cards, F1 page, saved in PlayerPrefs
Unmasked.Handbook); TestRoomBuilder adds it to the HUD object; the GameHUD help line mentions F1.
Also see tools/casecheck/casecheck.py: 9 cases, 0 problems.

Round 22: Town/HouseMood.cs, Town/CostumeTrunk.cs, Spooky/WatchCostume.cs; MysteryGameManager
WatchPieces / WearingWatch / GrantWatchPiece / ToggleWatch / SaveProgress / HandleStartOver (favours
now spent in BeginInvestigation); PlayerAgent.StartOverRpc; saved errands in Townsperson;
TownLayout Afterglow, Hq.trunk, Folk.piece; Costumes.watch; Horizon.MakeText is public (the editor
builder uses it). Also see tools/casecheck/casecheck.py: 9 cases, 0 problems.

Round 21: FaceLife.cs moves LashL/LashR with the blink, IrisL/IrisR with the eyes, and lifts
BrowL/BrowR while talking. The rest of the round is outfit data (Costumes.json).

Round 20: return visits in Cases.cs (Spec.Visit, CaseId, HouseOf, NextCase and four new
cases), MysteryGameManager.ActiveCase / NextCaseFor / CaseKey, MysteryServer.CaseId, and the call
board's RETURN VISIT tag.

Round 19: Town/Townsperson.cs and Town/ErrandItem.cs (townsfolk, errands), TownLayout.Folk,
MysteryGameManager.Favours / GrantFavour, townsfolk pins in TownMap, the errand count in GameHUD and
TownBuilder.BuildFolk.

Round 18: the Historical Society case in Cases.cs (FinaleCase, ArcCases, ArcFinale,
ArcEpilogue), MysteryGameManager.IsUnlocked / ArcComplete and the locked call, the call board's
locked label in GameHUD, and the museum keepsake in TownBuilder.

Round 17: Town/TownLife.cs (trick-or-treaters, cars, the train), Animation/FaceLife.cs, rumours
in Cases.cs, Horizon.MakeText (world text with Unity's built-in font).

## Not covered
- Netcode's own build-time checks (what RPCs and NetworkVariables may carry) only run inside Unity.
- APIs Unity 6 made obsolete or removed still compile against the 2021.3 DLLs.
- Editor APIs newer than 2021.1 would show up as false errors.
- If a real Unity 6 API reports as missing, add it to unity6-members.txt.
