using System.Collections.Generic;
using System.Linq;
using System.Text;
using Unity.Netcode;
using Unity.Netcode.Transports.UTP;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// The heads-up display (HUD), drawn with Unity's immediate-mode GUI (IMGUI) so the prototype
    /// needs no UI assets: connect menu, phase bar, setup picks, Solver and Haunter panels, the
    /// Suspect Board (Tab) and the end screens. Colours, type, spacing and motion come from
    /// <see cref="UITheme"/>. Screen zones: phase bar top centre, setup top left, your panel bottom
    /// left, toasts bottom right, hint cards bottom centre, minimap top right (town).
    /// TODO(UI milestone): move to UI Toolkit once the layout has been played.
    /// </summary>
    public class GameHUD : MonoBehaviour
    {
        struct ToastLine { public string Text; public float Shown, Until; }
        static readonly List<ToastLine> toasts = new();

        /// <summary>Any machine: show a message for a few seconds.</summary>
        public static void Toast(string message)
        {
            toasts.Add(new ToastLine { Text = message, Shown = Time.unscaledTime, Until = Time.unscaledTime + 6f });
            if (toasts.Count > 5) toasts.RemoveAt(0);
            Debug.Log("[Unmasked] " + message);
        }

        string address = "127.0.0.1";
        string port = "7777";
        bool boardOpen;
        Vector2 boardScroll, setupScroll;

        // Keyboard on the Suspect Board: the card you've picked (-1 = none yet), whether the scroll
        // view should bring it into view, and a first press of A that is waiting for the second.
        int boardPick = -1;
        bool scrollToPick;
        string accuseArmed = "";
        float accuseArmedUntil;

        void Update()
        {
            var keyboard = Keyboard.current;
            var mouse = Mouse.current;
            bool inGame = NetworkManager.Singleton != null && NetworkManager.Singleton.IsClient && PlayerAgent.Local != null;

            if (keyboard != null && keyboard.tabKey.wasPressedThisFrame && inGame) boardOpen = !boardOpen;
            if (!inGame) boardOpen = false;

            if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame)
            {
                if (boardOpen) boardOpen = false;
                else Cursor.lockState = CursorLockMode.None;
            }

            bool menu = boardOpen || TownMap.IsOpen;
            if (CameraRig.Instance != null) CameraRig.Instance.InputLocked = menu;

            if (menu || !inGame)
            {
                Cursor.lockState = CursorLockMode.None;
            }
            else if (mouse != null && mouse.leftButton.wasPressedThisFrame && Cursor.lockState != CursorLockMode.Locked && !MouseOverSetupPanel())
            {
                Cursor.lockState = CursorLockMode.Locked;
            }
            Cursor.visible = Cursor.lockState != CursorLockMode.Locked;

            toasts.RemoveAll(t => Time.unscaledTime > t.Until);

            if (keyboard != null && keyboard.f12Key.wasPressedThisFrame) TakeScreenshot();
            if (boardOpen && keyboard != null) BoardKeys(keyboard);
            else { boardPick = -1; accuseArmed = ""; }
        }

        /// <summary>
        /// The Suspect Board without a mouse: arrow keys or 1 to 4 pick a card, H hunch, X cross off
        /// or put back, C check alibi, A accuse. Accusing is the one thing that can't be undone, so it
        /// takes a second press of A within three seconds.
        /// </summary>
        void BoardKeys(Keyboard keyboard)
        {
            var game = MysteryGameManager.Instance;
            var agent = PlayerAgent.Local;
            if (game == null || agent == null || game.Suspects.Count == 0) return;
            int n = game.Suspects.Count;

            int step = keyboard.rightArrowKey.wasPressedThisFrame || keyboard.downArrowKey.wasPressedThisFrame ? 1
                     : keyboard.leftArrowKey.wasPressedThisFrame || keyboard.upArrowKey.wasPressedThisFrame ? -1 : 0;
            if (step != 0) Pick(boardPick < 0 ? (step > 0 ? 0 : n - 1) : (boardPick + step + n) % n);
            Key[] digits = { Key.Digit1, Key.Digit2, Key.Digit3, Key.Digit4 };
            for (int i = 0; i < digits.Length && i < n; i++)
                if (keyboard[digits[i]].wasPressedThisFrame) Pick(i);

            if (Time.unscaledTime > accuseArmedUntil) accuseArmed = "";
            if (boardPick < 0 || boardPick >= n) return;
            if (agent.Side.Value != PlayerSide.Solver || agent.ScaredOut.Value) return;

            var s = game.Suspects[boardPick];
            string id = s.Id.ToString();
            if (keyboard.hKey.wasPressedThisFrame) ToggleHunch(id);
            if (keyboard.xKey.wasPressedThisFrame) ToggleCleared(game, agent, id);
            if (keyboard.cKey.wasPressedThisFrame)
            {
                if (CanCheckAlibi(game, s) && LocalSolverRoom() == s.AlibiRoom.ToString() && game.AlibiChecksLeft.Value > 0) agent.CheckAlibiRpc(id);
                else Toast(CanCheckAlibi(game, s) ? $"Go to the {s.AlibiRoom} to check {s.Name}'s alibi." : $"{s.Name}'s alibi can't be checked right now.");
            }
            if (keyboard.aKey.wasPressedThisFrame)
            {
                if (!game.CanAccuseNow || game.IsCleared(id)) Toast(game.IsCleared(id) ? $"{s.Name} is crossed off. Press X to put them back first." : $"You need {game.CluesRequiredToAccuse.Value} clues to accuse.");
                else if (accuseArmed == id) { Accuse(agent, id); accuseArmed = ""; }
                else { accuseArmed = id; accuseArmedUntil = Time.unscaledTime + 3f; }
            }
        }

        void Pick(int i)
        {
            if (i == boardPick) return;
            boardPick = i;
            accuseArmed = "";
            scrollToPick = true;
        }

        // What the card buttons and the keys both do.
        void ToggleHunch(string id)
        {
            if (!hunches.Remove(id)) hunches.Add(id);
            SwingOf(id).Push(24f);
        }

        void ToggleCleared(MysteryGameManager game, PlayerAgent agent, string id)
        {
            bool cleared = game.IsCleared(id);
            agent.SetSuspectClearedRpc(id, !cleared);
            SwingOf(id).Push(cleared ? -30f : 30f);
        }

        void Accuse(PlayerAgent agent, string id)
        {
            agent.AccuseRpc(id);
            SwingOf(id).Push(45f);
        }

        /// <summary>F12: save a screenshot. In the editor they land in Docs/screenshots for the README.</summary>
        static void TakeScreenshot()
        {
            string folder = Application.isEditor
                ? System.IO.Path.Combine(System.IO.Directory.GetParent(Application.dataPath).FullName, "Docs", "screenshots")
                : System.IO.Path.Combine(Application.persistentDataPath, "screenshots");
            System.IO.Directory.CreateDirectory(folder);
            string path = System.IO.Path.Combine(folder, $"unmasked_{System.DateTime.Now:yyyyMMdd_HHmmss}.png");
            ScreenCapture.CaptureScreenshot(path);
            Toast("Screenshot saved: " + path);
        }

        bool MouseOverSetupPanel()
        {
            var game = MysteryGameManager.Instance;
            if (game == null || game.Phase.Value != MatchPhase.Setup || Mouse.current == null) return false;
            Vector2 m = UITheme.ToGui(Mouse.current.position.ReadValue());
            return m.x < UITheme.Edge + SetupWidth; // the setup panel lives on the left edge
        }

        void OnGUI()
        {
            UITheme.Begin();

            var net = NetworkManager.Singleton;
            if (net == null) { GUI.Label(new Rect(UITheme.Edge, UITheme.Edge, 700, 30), "No NetworkManager in the scene. Run Unmasked > Build Hollow Creek (town)."); return; }

            if (!net.IsClient && !net.IsServer) { DrawConnectMenu(net); DrawToasts(); return; }

            var game = MysteryGameManager.Instance;
            var agent = PlayerAgent.Local;

            if (net.IsServer && !net.IsClient)
            {
                GUI.Label(new Rect(UITheme.Edge, UITheme.Edge, 400, 25), $"Dedicated server running. Players: {net.ConnectedClientsIds.Count}");
                if (GUI.Button(new Rect(UITheme.Edge, UITheme.Edge + 32, 120, 32), "Stop")) net.Shutdown();
                DrawToasts();
                return;
            }

            if (game == null || !game.IsSpawned || agent == null) { GUI.Label(new Rect(UITheme.Edge, UITheme.Edge, 300, 25), "Connecting…", UITheme.Muted); return; }

            DrawTopBar(game);

            if (game.Phase.Value == MatchPhase.Setup) DrawSetup(game, agent);

            if (agent.Side.Value == PlayerSide.Solver) DrawSolverPanel(game, agent);
            else DrawHaunterPanel(game, agent);

            if (boardOpen) DrawBoard(game, agent);
            DrawEnd(game, agent);
            DrawToasts();

            if (!boardOpen && Cursor.lockState != CursorLockMode.Locked)
                GUI.Label(new Rect(UITheme.W / 2f - 320, UITheme.H - 28, 640, 22), TownMap.Instance != null
                    ? "Click to look around · Esc frees the mouse · Tab Suspect Board · M map · F1 handbook"
                    : "Click to look around · Esc frees the mouse · Tab Suspect Board · F1 handbook", UITheme.SmallCenter);
            else if (Cursor.lockState == CursorLockMode.Locked)
            {
                // A small dot reads as an aim point without covering what you look at.
                UITheme.Rect(new Rect(UITheme.W / 2f - 2, UITheme.H / 2f - 2, 4, 4), new Color(1f, 1f, 1f, 0.85f));
            }
        }

        // ---------------------------------------------------------------

        void DrawConnectMenu(NetworkManager net)
        {
            GUILayout.BeginArea(new Rect(UITheme.Edge * 2, UITheme.Edge * 2, 340, 330), UITheme.Panel);
            GUILayout.Label("Unmasked", UITheme.Display);
            GUILayout.Label("A Halloween mystery. Host a game, or join a friend's.", UITheme.MutedWrap);
            GUILayout.Space(UITheme.S3);
            GUILayout.Label("Host address", UITheme.Small);
            address = GUILayout.TextField(address);
            GUILayout.Label("Port", UITheme.Small);
            port = GUILayout.TextField(port);
            GUILayout.Space(UITheme.S2);

            var transport = net.GetComponent<UnityTransport>();
            ushort portNumber = ushort.TryParse(port, out var parsed) ? parsed : (ushort)7777;

            if (GUILayout.Button("Host a game", UITheme.Primary))
            {
                transport?.SetConnectionData("0.0.0.0", portNumber);
                net.StartHost();
            }
            if (GUILayout.Button("Join"))
            {
                transport?.SetConnectionData(address, portNumber);
                net.StartClient();
            }
            if (GUILayout.Button("Run a dedicated server"))
            {
                transport?.SetConnectionData("0.0.0.0", portNumber);
                net.StartServer();
            }
            GUILayout.EndArea();
        }

        const float TopBarWidth = 680f, SetupWidth = 340f, PanelWidth = 340f;

        /// <summary>
        /// Top centre: what's happening now and how long is left, then the context in a quieter line.
        /// The timer is set in the serif and turns red in the last minute, because it's what everyone keeps checking.
        /// </summary>
        void DrawTopBar(MysteryGameManager game)
        {
            float t = game.PhaseTimeRemaining;
            string time = game.PhaseEndTime.Value > 0 ? $"{(int)t / 60}:{(int)t % 60:00}" : "";
            var phaseNow = game.Phase.Value;
            string phase = phaseNow switch
            {
                MatchPhase.Setup => game.InTown ? "At HQ: pick tonight's call" : "Setup",
                MatchPhase.Dispatch => $"Drive to {game.HouseName}",
                MatchPhase.Investigation => $"Investigation · {game.NightClock(game.Now)}",
                MatchPhase.Trap => "Trap: catch the Haunter",
                MatchPhase.Unmasking => "Unmasking",
                MatchPhase.Ended => "The night is over",
                _ => "Waiting for players"
            };
            string context = phaseNow switch
            {
                MatchPhase.Setup => "The Haunter is choosing a disguise.",
                MatchPhase.Investigation => $"Clues {game.Clues.Count} (accuse at {game.CluesRequiredToAccuse.Value}) · Accusations {game.AccusationsLeft.Value} · Alibi checks {game.AlibiChecksLeft.Value}",
                _ => ""
            };
            if (phaseNow >= MatchPhase.Investigation && phaseNow < MatchPhase.Ended)
                context = $"Mask in play: {MysteryGameManager.MaskName(game.Villain.Value)}. Who is wearing it?" + (context.Length > 0 ? "\n" + context : "");
            if (game.Event.Value != NightEvent.None && phaseNow >= MatchPhase.Dispatch && phaseNow < MatchPhase.Ended)
                context += (context.Length > 0 ? " · " : "") + UITheme.Tint("Tonight: " + TownLayout.EventName(game.Event.Value), UITheme.Danger);

            float w = Mathf.Min(TopBarWidth, UITheme.W - 2 * (UITheme.Edge + 220f));
            float h = 40f + UITheme.Small.CalcHeight(new GUIContent(context), w - 32f);
            var r = new Rect(UITheme.W / 2f - w / 2f, UITheme.Edge, w, context.Length > 0 ? h : 40f);
            GUI.Box(r, GUIContent.none);
            GUI.Label(new Rect(r.x + 16, r.y + 8, w - 120, 26), phase, UITheme.Title);
            if (time.Length > 0) GUI.Label(new Rect(r.xMax - 116, r.y + 8, 100, 26), time, t < 60f ? UITheme.TimerLow : UITheme.Timer);
            if (context.Length > 0) GUI.Label(new Rect(r.x + 16, r.y + 34, w - 32, h - 36), context, UITheme.Small);
        }

        float startOverArmedUntil;

        void DrawSetup(MysteryGameManager game, PlayerAgent agent)
        {
            // Leaves room for your own panel in the bottom-left corner; long lists scroll.
            GUILayout.BeginArea(new Rect(UITheme.Edge, UITheme.Edge, SetupWidth, UITheme.H - UITheme.Edge * 3 - 200f), UITheme.Panel);
            setupScroll = GUILayout.BeginScrollView(setupScroll);
            GUILayout.Label("Pick a side", UITheme.Title);
            GUILayout.BeginHorizontal();
            if (GUILayout.Toggle(agent.Side.Value == PlayerSide.Solver, "Solver", GUI.skin.button) && agent.Side.Value != PlayerSide.Solver)
                agent.RequestSideRpc(PlayerSide.Solver);
            if (GUILayout.Toggle(agent.Side.Value == PlayerSide.Haunter, "Haunter", GUI.skin.button) && agent.Side.Value != PlayerSide.Haunter)
                agent.RequestSideRpc(PlayerSide.Haunter);
            GUILayout.EndHorizontal();

            if (agent.Side.Value == PlayerSide.Solver)
            {
                GUILayout.Space(UITheme.S3);
                GUILayout.Label("Role", UITheme.Title);
                foreach (SolverRole role in System.Enum.GetValues(typeof(SolverRole)))
                    if (GUILayout.Toggle(agent.Role.Value == role, $"{role}: {RoleBlurb(role)}", GUI.skin.button) && agent.Role.Value != role)
                        agent.RequestRoleRpc(role);

                var town = game.InTown ? TownLayout.Current : null;
                if (town?.lots != null)
                {
                    GUILayout.Space(UITheme.S4);
                    GUILayout.Label("Tonight's call", UITheme.Title);
                    string active = game.ActiveHouse.Value.ToString();
                    foreach (var lot in town.lots)
                    {
                        if (!game.IsUnlocked(lot.id))
                        {
                            GUILayout.Label($"Locked: solve the other four cases and {lot.street} will call.", UITheme.Small);
                            continue;
                        }
                        string next = game.NextCaseFor(lot.id);
                        var nextSpec = Cases.For(next);
                        string tag = game.IsSolved(next) ? " · solved" : nextSpec.IsReturnVisit ? " · return visit" : "";
                        if (GUILayout.Toggle(active == lot.id, $"{lot.name} ({lot.size}): {nextSpec.CaseName}{tag}", GUI.skin.button) && active != lot.id)
                            agent.ChooseCallRpc(lot.id);
                    }
                    GUILayout.Space(UITheme.S2);
                    GUILayout.Label(game.SolvedCases.Count == 0
                        ? "No pick = The Missing Harvest Lantern, the club's first case. Open the map (M) to see every house."
                        : "No pick = a random call. Open the map (M) to see every house.", UITheme.Small);
                    GUILayout.Space(UITheme.S4);
                    GUILayout.Label("The club", UITheme.Title);
                    GUILayout.Label($"Case book: {game.SolvedCases.Count} of {Cases.All.Length} solved. Keepsakes are on the shelf at HQ.", UITheme.MutedWrap);
                    if (Townsperson.All.Count > 0)
                        GUILayout.Label($"Errands for the townsfolk: {Townsperson.ErrandsDone} of {Townsperson.All.Count} done" +
                                        (game.Favours.Value > 0 ? $". Favours owed: {game.Favours.Value} extra alibi check{(game.Favours.Value > 1 ? "s" : "")} on the next case." : ". Talk to people around town (E)."), UITheme.MutedWrap);
                    if (Townsperson.All.Count > 0)
                    {
                        int pieces = game.WatchPieceCount;
                        GUILayout.Label(game.WearingWatch.Value
                            ? $"Lantern Watch costume: on ({pieces} pieces). Scares hit {Mathf.RoundToInt((1f - game.WatchFearMultiplier) * 100f)}% softer. Take it off at the trunk."
                            : pieces >= MysteryGameManager.WatchPiecesNeeded
                                ? $"Lantern Watch costume: {pieces} pieces in the trunk at HQ. Put it on (E at the trunk)."
                                : $"Lantern Watch costume: {pieces} of {MysteryGameManager.WatchPiecesNeeded} pieces. The townsfolk give one for each errand.", UITheme.MutedWrap);
                    }
                    GUILayout.Space(UITheme.S4);
                    GUILayout.Label("The Mask Keeper", UITheme.Title);
                    GUILayout.Label(game.IsSolved(Cases.FinaleCase) ? Cases.ArcEpilogue : game.ArcComplete ? Cases.ArcFinale : Cases.ArcQuestion, UITheme.BodyWrap);
                    foreach (var solved in game.SolvedCases)
                        if (solved.ToString() != Cases.FinaleCase && !string.IsNullOrEmpty(Cases.For(solved.ToString()).ArcClue))
                            GUILayout.Label("· " + Cases.For(solved.ToString()).ArcClue, UITheme.MutedWrap);
                    GUILayout.Space(UITheme.S4);
                    if (NetworkManager.Singleton.IsHost && GUILayout.Button("Everyone's ready: leave now", UITheme.Primary))
                        agent.LeaveNowRpc();
                    if (NetworkManager.Singleton.IsHost)
                    {
                        // Irreversible, so it takes two presses, and the second has to come within a few seconds.
                        bool armed = Time.time < startOverArmedUntil;
                        GUILayout.Space(UITheme.S5);
                        if (GUILayout.Button(armed ? "Press again to wipe the save" : "Start over (wipes the case book and errands)", armed ? UITheme.DangerButton : GUI.skin.button))
                        {
                            if (armed) { agent.StartOverRpc(); startOverArmedUntil = 0f; }
                            else startOverArmedUntil = Time.time + 4f;
                        }
                    }
                }
            }
            else
            {
                GUILayout.Space(UITheme.S3);
                GUILayout.Label("Who are you really? (secret)", UITheme.Title);
                foreach (var s in game.Suspects)
                {
                    string id = s.Id.ToString();
                    bool chosen = agent.LocalSecretIdentity == id;
                    if (GUILayout.Toggle(chosen, $"{s.Name} ({s.Occupation})", GUI.skin.button) && !chosen)
                        agent.ChooseIdentityRpc(id);
                }
                GUILayout.Label("No pick by the end of setup = a random suspect.", UITheme.Small);

                GUILayout.Space(UITheme.S4);
                GUILayout.Label("Your costume (everyone sees it)", UITheme.Title);
                foreach (VillainKind v in System.Enum.GetValues(typeof(VillainKind)))
                {
                    bool chosen = game.Villain.Value == v;
                    if (GUILayout.Toggle(chosen, $"{Costumes.NameOf(v)}: {Costumes.PowerOf(v)}", GUI.skin.button) && !chosen)
                        agent.ChooseVillainRpc(v);
                }
                var legend = Costumes.For(game.Villain.Value);
                if (legend != null) GUILayout.Label($"{legend.legend}\n{UITheme.Tint("6 or Q", UITheme.Haunt)}  {legend.power}: {legend.powerBlurb}", UITheme.MutedWrap);
            }
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        static string RoleBlurb(SolverRole role) => role switch
        {
            SolverRole.Sleuth => "senses nearby clues",
            SolverRole.Techie => "ecto-detector, long battery",
            SolverRole.Brawn => "builds traps fast",
            SolverRole.Snacker => "better interviews",
            _ => ""
        };

        void DrawSolverPanel(MysteryGameManager game, PlayerAgent agent)
        {
            var solver = SolverController.Local;
            GUILayout.BeginArea(new Rect(UITheme.Edge, UITheme.H - UITheme.Edge - 200f, PanelWidth, 200f), UITheme.Panel);
            if (agent.ScaredOut.Value)
            {
                GUILayout.Label("Scared out", UITheme.Title);
                GUILayout.Label("You ran screaming out of the house. Watch your friends finish the case.", UITheme.MutedWrap);
            }
            else if (solver != null)
            {
                string here = ManorLayout.Describe(solver.transform.position);
                GUILayout.Label($"{agent.Role.Value}{(here.Length > 0 ? UITheme.Tint("  ·  " + here, UITheme.InkMuted) : "")}", UITheme.Title);
                // Fear warms from pale ink to evidence red as it climbs, so a glance is enough.
                float fear = solver.Fear.Percent;
                Bar("Fear", fear, Color.Lerp(UITheme.InkMuted, UITheme.Accent, fear), solver.IsPanicked ? UITheme.Tint("Panic", UITheme.Danger) : null);
                if (solver.Flashlight != null) Bar("Battery", solver.Flashlight.BatteryPercent, UITheme.Ink, solver.Flashlight.IsOn ? null : "off (F)");
                GUILayout.Label($"Panics {agent.PanicCount.Value} of {game.MaxPanicsBeforeScaredOut}", UITheme.Small);
                if (game.Phase.Value == MatchPhase.Trap)
                {
                    GUILayout.Label($"Carrying {agent.CarriedTrapPieces.Value}/{TrapPiece.MaxCarried} trap pieces");
                    var site = FindAnyObjectByType<TrapSite>();
                    if (site != null) GUILayout.Label(site.StatusText);
                }
                if (agent.Role.Value == SolverRole.Sleuth) GUILayout.Label(SleuthSense(solver));
                if (agent.Role.Value == SolverRole.Techie) GUILayout.Label(EctoDetector(solver));
                if (MysteryVan.TryGetSeat(solver.OwnerClientId, out _, out bool driving))
                    GUILayout.Label(driving ? $"Driving · {Mathf.Abs(MysteryVan.Instance.Speed) * 3.6f:0} km/h\n{UITheme.KeyCap("W S")} gas and reverse  {UITheme.KeyCap("A D")} steer  {UITheme.KeyCap("Space")} brake  {UITheme.KeyCap("E")} get out"
                        : $"Riding in the van · {UITheme.KeyCap("E")} get out", UITheme.BodyWrap);
                else if (solver.Focused != null) GUILayout.Label($"{UITheme.KeyCap("E")}  {solver.Focused.GetPrompt(solver)}", UITheme.Title);
            }
            GUILayout.EndArea();
        }

        static string SleuthSense(SolverController me)
        {
            float best = float.MaxValue;
            foreach (var clue in FindObjectsByType<ClueItem>(FindObjectsSortMode.None))
                if (!clue.IsDiscovered) best = Mathf.Min(best, Vector3.Distance(clue.transform.position, me.transform.position));
            return best <= ClueItem.SleuthSenseRadius ? $"Clue sense: something is {best:0} m away" : "Clue sense: nothing close";
        }

        static string EctoDetector(SolverController me)
        {
            // Possession is public (the object trembles); the detector just makes it easy to read.
            float best = float.MaxValue;
            foreach (var obj in FindObjectsByType<PossessableObject>(FindObjectsSortMode.None))
                if (obj.IsPossessed) best = Mathf.Min(best, Vector3.Distance(obj.transform.position, me.transform.position));
            foreach (var fog in FindObjectsByType<FogCloud>(FindObjectsSortMode.None))
                best = Mathf.Min(best, Vector3.Distance(fog.transform.position, me.transform.position));
            foreach (var phantom in FindObjectsByType<PhantomIllusion>(FindObjectsSortMode.None))
                best = Mathf.Min(best, Vector3.Distance(phantom.transform.position, me.transform.position));
            if (best > 12f) return "Ecto-detector: quiet";
            int bars = Mathf.Clamp(5 - (int)(best / 2.5f), 1, 5);
            return "Ecto-detector: " + new string('|', bars * 2) + (bars >= 4 ? "  beep beep" : "");
        }

        void DrawHaunterPanel(MysteryGameManager game, PlayerAgent agent)
        {
            var haunter = HaunterController.Local;
            float height = game.Phase.Value == MatchPhase.Setup ? 200f : 330f;
            GUILayout.BeginArea(new Rect(UITheme.Edge, UITheme.H - UITheme.Edge - height, PanelWidth + 20f, height), UITheme.Panel);
            string identity = string.IsNullOrEmpty(agent.LocalSecretIdentity) ? "not chosen yet" : game.SuspectName(agent.LocalSecretIdentity);
            GUILayout.Label($"{UITheme.Tint("Haunter", UITheme.Haunt)} · secretly {identity}", UITheme.Title);
            GUILayout.Label("Suspects who see a scare up close remember a detail about you.", UITheme.Small);
            if (haunter != null)
            {
                string here = ManorLayout.Describe(haunter.transform.position);
                if (here.Length > 0) GUILayout.Label("Haunting the " + here, UITheme.Muted);
            }
            if (haunter != null)
            {
                Bar("Ecto", haunter.Ectoplasm.Value / haunter.Ectoplasm.Max, UITheme.Haunt, null);
                string form = haunter.IsStunned ? UITheme.Tint("Stunned", UITheme.Danger) : haunter.IsPhysical ? UITheme.Tint("In costume: they can see you", UITheme.Accent) : "Spectral: invisible";
                GUILayout.Label(form);

                var obj = haunter.Possessed;
                if (obj != null)
                {
                    GUILayout.Label($"Inside {obj.name} · {UITheme.KeyCap("E")} leave");
                    for (int i = 0; i < obj.Actions.Count && i < 2; i++)
                    {
                        var spec = obj.Actions[i];
                        float cd = obj.CooldownRemaining(i);
                        GUILayout.Label($"{UITheme.KeyCap(i == 0 ? "Left click" : "Right click")}  {spec.Action} ({spec.Cost:0} ecto){(cd > 0 ? $" · {cd:0}s" : "")}");
                    }
                }
                else if (haunter.FocusedObject != null)
                {
                    GUILayout.Label($"{UITheme.KeyCap("E")}  Possess {haunter.FocusedObject.name} ({haunter.PossessCost:0} ecto)", UITheme.Title);
                }

                for (int i = 0; i < haunter.Powers.Powers.Count; i++)
                {
                    var spec = haunter.Powers.Powers[i];
                    float cd = haunter.Powers.CooldownRemaining(i);
                    bool ok = haunter.Powers.IsAllowedNow(spec) && cd <= 0f && haunter.Ectoplasm.CanAfford(spec.Cost);
                    // Unavailable powers drop to the faint ink (still readable), instead of fading out.
                    string key = spec.Power == HaunterPower.Signature ? $"{i + 1} or Q" : $"{i + 1}";
                    string line = $"{UITheme.Tint(key, ok ? UITheme.Haunt : UITheme.InkFaint)}  {haunter.Powers.DisplayName(spec)} ({spec.Cost:0}){(cd > 0 ? $" · {cd:0}s" : "")}";
                    GUILayout.Label(ok ? line : UITheme.Tint(line, UITheme.InkFaint), UITheme.Body);
                }
                float plantCd = haunter.PlantFakeClueCooldownRemaining;
                GUILayout.Label($"{UITheme.Tint("G", UITheme.Haunt)}  Plant a fake clue ({haunter.PlantFakeClueCost:0}){(plantCd > 0 ? $" · {plantCd:0}s" : "")}");
                string myId = agent.LocalSecretIdentity;
                string alibiRoom = string.IsNullOrEmpty(myId) ? "" : game.AlibiRoomOf(myId);
                if (alibiRoom.Length > 0)
                {
                    bool faked = game.Mystery != null && game.Mystery.AlibiFaked; // host only; clients just see the prompt
                    int status = game.AlibiStatus(myId);
                    GUILayout.Label(status == 1 ? "Your alibi was checked and held up."
                        : status == -1 ? UITheme.Tint("Your alibi was checked and fell apart.", UITheme.Danger)
                        : faked ? "Alibi faked."
                        : $"{UITheme.Tint("H", UITheme.Haunt)}  Fake your alibi in the {alibiRoom} ({haunter.FakeAlibiCost:0})");
                }
            }
            if (Time.time - agent.LastClueLeakTime < 4f)
            {
                GUILayout.Label(UITheme.Tint("You left a clue behind.", UITheme.Danger), UITheme.Title);
            }
            GUILayout.EndArea();
        }

        static void Bar(string label, float fraction, Color fill, string note)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(label, UITheme.Muted, GUILayout.Width(64));
            Rect r = GUILayoutUtility.GetRect(170, 22);
            UITheme.Meter(new Rect(r.x, r.y + 7, r.width, 8), fraction, fill);
            GUILayout.Label(note ?? $"{fraction * 100f:0}%", UITheme.Body, GUILayout.Width(64));
            GUILayout.EndHorizontal();
        }

        // The Suspect Board is a corkboard: the club's evidence pinned along the top as tags, the
        // four suspects pinned below, and red string from each clue to everyone it fits. What was
        // said and what follows are underneath. Opened from the keyboard, so it appears at once.
        readonly Dictionary<string, UITheme.Swing> swings = new();

        UITheme.Swing SwingOf(string id)
        {
            if (!swings.TryGetValue(id, out var s)) swings[id] = s = new UITheme.Swing();
            return s;
        }

        const float TagW = 236f, TagH = 62f, CardPad = 16f, ButtonH = 30f;

        void DrawBoard(MysteryGameManager game, PlayerAgent agent)
        {
            UITheme.Rect(new Rect(0, 0, UITheme.W, UITheme.H), UITheme.Scrim);
            float w = Mathf.Min(1120f, UITheme.W - 2 * UITheme.S6);
            var area = new Rect(UITheme.W / 2f - w / 2f, UITheme.S6, w, UITheme.H - 2 * UITheme.S6);
            UITheme.CorkRect(area);

            const float pad = UITheme.S5;
            bool isSolver = agent.Side.Value == PlayerSide.Solver && !agent.ScaredOut.Value;
            bool armed = accuseArmed.Length > 0 && boardPick >= 0 && boardPick < game.Suspects.Count;
            var closeHint = new GUIContent(armed ? UITheme.Tint($"Press A again to accuse {game.Suspects[boardPick].Name}", UITheme.Accent)
                : isSolver ? "Arrows pick a card · H hunch · X cross off · C alibi · A accuse · Tab closes"
                : "Arrows pick a card · Tab or Esc closes");
            float hintW = UITheme.Small.CalcSize(closeHint).x;
            GUI.Label(new Rect(area.x + pad, area.y + UITheme.S4, w - 2 * pad - hintW - pad, 42), "Suspect Board", UITheme.Display);
            GUI.Label(new Rect(area.xMax - pad - hintW, area.y + UITheme.S5, hintW, 20), closeHint, UITheme.Small);
            var deductions = Deductions(game);
            GUI.Label(new Rect(area.x + pad, area.y + 62, w - 2 * pad, 24), deductions[0], UITheme.MutedWrap);

            var view = new Rect(area.x, area.y + 96, w, area.height - 96 - UITheme.S3);
            float innerW = w - 2 * pad - 14f; // room for the scrollbar
            int[] matches = game.ClueMatchCounts();
            int n = game.Suspects.Count;

            // ---- Layout first (so the scroll view knows its height), then draw. ----
            var tags = new List<Rect>();
            float x = 0f, y = UITheme.S2;
            for (int i = 0; i < game.Clues.Count; i++)
            {
                if (x > 0 && x + TagW > innerW) { x = 0; y += TagH + UITheme.S4; }
                tags.Add(new Rect(pad + x, y, TagW, TagH));
                x += TagW + UITheme.S5;
            }
            float tagsBottom = game.Clues.Count > 0 ? y + TagH : y + 54f;

            int cols = innerW >= 900f ? 4 : 2;
            float cardW = (innerW - (cols - 1) * UITheme.S5) / cols;
            var cards = new Rect[n];
            float rowTop = tagsBottom + UITheme.S7, rowH = 0f;
            for (int row = 0; row * cols < n; row++)
            {
                // Cards in a row share the tallest one's height, so the buttons line up.
                rowH = 0f;
                for (int i = row * cols; i < n && i < (row + 1) * cols; i++) rowH = Mathf.Max(rowH, CardHeight(game, game.Suspects[i], cardW, isSolver));
                for (int i = row * cols; i < n && i < (row + 1) * cols; i++)
                    cards[i] = new Rect(pad + (i % cols) * (cardW + UITheme.S5), rowTop, cardW, rowH);
                rowTop += rowH + UITheme.S6;
            }
            float notesTop = rowTop;
            string notes = NotesText(game, deductions);
            float notesH = UITheme.BodyWrap.CalcHeight(new GUIContent(notes), innerW - 2 * CardPad) + 2 * CardPad;
            float contentH = notesTop + notesH + UITheme.S5;

            // A card picked with the keyboard is scrolled into view once, then the mouse wheel is free.
            if (scrollToPick && boardPick >= 0 && boardPick < n)
            {
                var c = cards[boardPick];
                if (c.y - UITheme.S4 < boardScroll.y) boardScroll.y = c.y - UITheme.S4;
                else if (c.yMax + UITheme.S4 > boardScroll.y + view.height) boardScroll.y = c.yMax + UITheme.S4 - view.height;
                scrollToPick = false;
            }

            boardScroll = GUI.BeginScrollView(view, boardScroll, new Rect(0, 0, w - 16f, contentH));

            // Red string from each clue to every suspect it fits, faint for anyone crossed off. Drawn
            // first, so it runs under the paper and comes out at the pins.
            if (Event.current.type == EventType.Repaint)
                for (int i = 0; i < game.Clues.Count; i++)
                for (int k = 0; k < n; k++)
                {
                    if ((game.Suspects[k].Traits & game.Clues[i].Traits) == 0) continue;
                    bool cleared = game.IsCleared(game.Suspects[k].Id.ToString());
                    UITheme.RedString(new Vector2(tags[i].x + 14f, tags[i].center.y), new Vector2(cards[k].center.x, cards[k].y + 2f), cleared ? 0.3f : 0.9f);
                }


            // Evidence tags (or a slip saying there's nothing yet).
            if (game.Clues.Count == 0)
            {
                var slip = new Rect(pad, UITheme.S2, Mathf.Min(440f, innerW), 46f);
                UITheme.Rect(slip, UITheme.Raised);
                GUI.Label(new Rect(slip.x + CardPad, slip.y + 12, slip.width - 2 * CardPad, 24), "No evidence yet. Things that glow in your flashlight are clues.", UITheme.MutedWrap);
            }
            for (int i = 0; i < game.Clues.Count; i++)
            {
                var c = game.Clues[i];
                var r = tags[i];
                UITheme.Rect(r, UITheme.TagWash);
                UITheme.Pin(new Vector2(r.x + 14f, r.center.y), 12f, UITheme.Accent);
                UITheme.Pin(new Vector2(r.x + 14f, r.center.y), 7f, UITheme.Cork);
                GUI.Label(new Rect(r.x + 30f, r.y + 8f, r.width - 40f, 24f), c.Name.ToString(), UITheme.Title);
                string where = ManorLayout.Describe(c.Location);
                string when = game.NightClock(c.DiscoveredAt);
                string stamp = string.Join(", ", new[] { when, where }.Where(s => !string.IsNullOrEmpty(s)));
                GUI.Label(new Rect(r.x + 30f, r.y + 34f, r.width - 40f, 20f), stamp.Length > 0 ? stamp : TraitText(game, c.Traits), UITheme.Small);
            }

            for (int i = 0; i < n; i++) DrawSuspectCard(game, agent, game.Suspects[i], cards[i], matches[i], isSolver, i == boardPick);

            var notesRect = new Rect(pad, notesTop, innerW, notesH);
            UITheme.Rect(notesRect, UITheme.Raised);
            GUI.Label(new Rect(notesRect.x + CardPad, notesRect.y + CardPad, notesRect.width - 2 * CardPad, notesH - 2 * CardPad), notes, UITheme.BodyWrap);
            GUI.EndScrollView();
        }

        float CardHeight(MysteryGameManager game, SuspectInfo s, float cardW, bool isSolver)
        {
            float tw = cardW - 2 * CardPad;
            float h = CardPad + 28f + 20f + UITheme.S2;
            h += UITheme.MutedWrap.CalcHeight(new GUIContent(s.Bio.ToString()), tw) + UITheme.S2;
            h += UITheme.BodyWrap.CalcHeight(new GUIContent(AlibiLine(game, s)), tw) + UITheme.S2;
            h += 20f; // fits / hunch line
            h += UITheme.Small.CalcHeight(new GUIContent("Traits: " + TraitText(game, s.Traits)), tw);
            if (isSolver) h += UITheme.S3 + 2 * ButtonH + UITheme.S2 + (CanCheckAlibi(game, s) ? ButtonH + UITheme.S2 : 0f);
            return h + CardPad;
        }

        static string AlibiLine(MysteryGameManager game, SuspectInfo s)
        {
            int alibi = game.AlibiStatus(s.Id.ToString());
            string check = alibi == 1 ? UITheme.Tint(" It holds up.", UITheme.Good) : alibi == -1 ? UITheme.Tint(" It falls apart.", UITheme.Danger) : "";
            return $"{UITheme.Tint("8:00 PM, on arrival:", UITheme.InkMuted)} {s.Alibi}{check}";
        }

        static bool CanCheckAlibi(MysteryGameManager game, SuspectInfo s) =>
            game.AlibiStatus(s.Id.ToString()) == 0 && s.AlibiRoom.Length > 0 && game.Phase.Value == MatchPhase.Investigation;

        void DrawSuspectCard(MysteryGameManager game, PlayerAgent agent, SuspectInfo s, Rect r, int fits, bool isSolver, bool picked)
        {
            string id = s.Id.ToString();
            bool cleared = game.IsCleared(id);
            var swing = SwingOf(id);
            float angle = Event.current.type == EventType.Repaint ? swing.Step() : swing.Angle;
            var pin = new Vector2(r.center.x, r.y + 2f);
            var keep = GUI.matrix;
            // Rotate only while it swings: at rest every card is square, so text stays crisp.
            if (Mathf.Abs(angle) > 0.01f) GUIUtility.RotateAroundPivot(angle, pin);

            UITheme.Rect(new Rect(r.x + 1f, r.y + 3f, r.width, r.height), UITheme.Shadow);
            if (picked) UITheme.Outline(r, 3f, 2f, accuseArmed == id ? UITheme.Accent : UITheme.Ink);
            UITheme.Rect(r, UITheme.Raised);
            float tw = r.width - 2 * CardPad, y = r.y + CardPad;
            UITheme.Struck(new Rect(r.x + CardPad, y, tw, 28f), s.Name.ToString(), UITheme.CardName, cleared);
            y += 28f;
            GUI.Label(new Rect(r.x + CardPad, y, tw, 20f), s.Occupation.ToString(), UITheme.Small);
            y += 20f + UITheme.S2;
            var bio = new GUIContent(s.Bio.ToString());
            float bh = UITheme.MutedWrap.CalcHeight(bio, tw);
            GUI.Label(new Rect(r.x + CardPad, y, tw, bh), bio, cleared ? UITheme.Small : UITheme.MutedWrap);
            y += bh + UITheme.S2;
            var alibi = new GUIContent(AlibiLine(game, s));
            float ah = UITheme.BodyWrap.CalcHeight(alibi, tw);
            GUI.Label(new Rect(r.x + CardPad, y, tw, ah), alibi, UITheme.BodyWrap);
            y += ah + UITheme.S2;
            string fitsText = game.Clues.Count == 0 ? "" : fits == game.Clues.Count && fits > 1 ? "Fits every clue" : fits == 0 ? "Fits none of the clues" : $"Fits {fits} of {game.Clues.Count} clues";
            if (hunches.Contains(id)) fitsText += (fitsText.Length > 0 ? " · " : "") + "your hunch";
            GUI.Label(new Rect(r.x + CardPad, y, tw, 20f), UITheme.Tint(fitsText, UITheme.Accent), UITheme.Strong);
            y += 20f;
            var traits = new GUIContent("Traits: " + TraitText(game, s.Traits));
            float th = UITheme.Small.CalcHeight(traits, tw);
            GUI.Label(new Rect(r.x + CardPad, y, tw, th), traits, UITheme.Small);
            y += th + UITheme.S3;

            if (isSolver)
            {
                float half = (tw - UITheme.S2) / 2f;
                bool hunch = hunches.Contains(id);
                if (GUI.Button(new Rect(r.x + CardPad, y, half, ButtonH), hunch ? "Drop hunch" : "Hunch", UITheme.CardButton)) ToggleHunch(id);
                if (GUI.Button(new Rect(r.x + CardPad + half + UITheme.S2, y, half, ButtonH), cleared ? "Put back" : "Cross off", UITheme.CardButton)) ToggleCleared(game, agent, id);
                y += ButtonH + UITheme.S2;
                bool canAccuse = game.CanAccuseNow && !cleared;
                GUI.enabled = canAccuse;
                if (GUI.Button(new Rect(r.x + CardPad, y, tw, ButtonH), canAccuse || cleared ? "Accuse" : $"Accuse (needs {game.CluesRequiredToAccuse.Value} clues)", canAccuse ? UITheme.AccuseButton : UITheme.CardButton))
                    Accuse(agent, id);
                GUI.enabled = true;
                y += ButtonH + UITheme.S2;
                if (CanCheckAlibi(game, s))
                {
                    string room = s.AlibiRoom.ToString();
                    bool here = LocalSolverRoom() == room;
                    GUI.enabled = here && game.AlibiChecksLeft.Value > 0;
                    if (GUI.Button(new Rect(r.x + CardPad, y, tw, ButtonH), here ? "Check alibi" : $"Go to the {room}", UITheme.CardButton)) agent.CheckAlibiRpc(id);
                    GUI.enabled = true;
                }
            }
            UITheme.Pin(pin, 14f, UITheme.Accent);
            GUI.matrix = keep;
        }

        /// <summary>Testimony and deductions under the cards: what people said, what follows, and the rules of evidence.</summary>
        string NotesText(MysteryGameManager game, List<string> deductions)
        {
            var sb = new StringBuilder();
            sb.Append(UITheme.Tint("<b>What people said</b>", UITheme.Ink)).Append('\n');
            if (game.Interviews.Count == 0) sb.Append(UITheme.Tint("Nobody interviewed yet. Talk to the suspects (E).", UITheme.InkMuted)).Append('\n');
            foreach (var note in game.Interviews)
            {
                string when = game.NightClock(note.At);
                string kind = note.SuspiciousOfId.Length == 0 ? "saw the Haunter up close" : "gossip";
                sb.Append(when.Length > 0 ? UITheme.Tint(when + "  ", UITheme.InkMuted) : "")
                  .Append(game.SuspectName(note.SpeakerId.ToString())).Append(UITheme.Tint($" ({kind})", UITheme.InkMuted))
                  .Append(": \"").Append(note.Statement).Append("\"\n");
            }
            sb.Append('\n').Append(UITheme.Tint("<b>What follows</b>", UITheme.Ink)).Append('\n');
            foreach (var line in deductions) sb.Append(line).Append('\n');
            sb.Append('\n').Append(UITheme.Tint("The Haunter can plant clues and fake an alibi, so a held-up alibi isn't proof. Suspects can lie, and everyone is nervous when questioned. Hunches are yours alone. A wrong accusation clears that suspect but powers up the Haunter.", UITheme.InkMuted));
            return sb.ToString();
        }

        /// <summary>This player's own suspicions. Local only: a hunch never changes anyone else's board.</summary>
        readonly HashSet<string> hunches = new();

        /// <summary>What the evidence so far proves, worded carefully (a clue may have been planted).</summary>
        static List<string> Deductions(MysteryGameManager game)
        {
            var lines = new List<string>();
            var fits = new List<string>();
            for (int i = 0; i < game.Suspects.Count; i++)
            {
                var s = game.Suspects[i];
                bool all = game.Clues.Count > 0;
                foreach (var c in game.Clues)
                    if ((s.Traits & c.Traits) == 0) { all = false; break; }
                if (all) fits.Add(s.Name.ToString());
                if (game.AlibiStatus(s.Id.ToString()) == -1) lines.Add($"{s.Name}'s alibi fell apart: they weren't where they said.");
            }
            if (game.Clues.Count == 0) lines.Insert(0, "Nothing yet. Find some evidence first.");
            else if (fits.Count == 0) lines.Insert(0, "No suspect fits every clue, so at least one clue was planted.");
            else if (fits.Count == 1) lines.Insert(0, $"Every clue so far fits {fits[0]} and nobody else (unless one was planted).");
            else lines.Insert(0, $"Every clue so far fits {string.Join(", ", fits)}.");
            return lines;
        }

        /// <summary>The room the local Solver is standing in ("" if none).</summary>
        static string LocalSolverRoom()
        {
            foreach (var s in SolverController.All)
                if (s != null && s.IsOwner) return ManorLayout.RoomNameAt(s.transform.position);
            return "";
        }

        static string TraitText(MysteryGameManager game, int traits)
        {
            string house = game.CaseKey;
            var sb = new StringBuilder();
            foreach (Trait t in System.Enum.GetValues(typeof(Trait)))
            {
                if (t == Trait.None || (traits & (int)t) == 0) continue;
                if (sb.Length > 0) sb.Append(", ");
                sb.Append(Cases.TraitName(house, t));
            }
            return sb.Length > 0 ? sb.ToString() : "none";
        }

        void DrawEnd(MysteryGameManager game, PlayerAgent agent)
        {
            if (game.Phase.Value == MatchPhase.Unmasking)
            {
                // The big reveal: one dark band across the screen, the name large, the reason under it.
                float y = UITheme.H * 0.22f;
                UITheme.Rect(new Rect(0, y - UITheme.S5, UITheme.W, 150), UITheme.Scrim);
                GUI.Label(new Rect(0, y, UITheme.W, 44), $"Unmasked. It was {game.SuspectName(game.RevealedCulprit.Value.ToString())}.", UITheme.DisplayCenter);
                GUI.Label(new Rect(UITheme.W / 2f - 320, y + 52, 640, 70), game.UnmaskLine(), UITheme.Center);
                return;
            }
            if (game.Phase.Value != MatchPhase.Ended) return;

            bool solversWon = game.Winner.Value == MatchWinner.Solvers;
            string reason = game.EndReason.Value switch
            {
                MatchEndReason.Unmasked => "The Haunter was caught and unmasked.",
                MatchEndReason.Dawn => "Dawn broke and the mystery went unsolved.",
                MatchEndReason.WrongAccusations => "Too many wrong accusations.",
                MatchEndReason.SolversScaredOut => "Every Solver was scared out of the house.",
                MatchEndReason.Escaped => "The Haunter escaped the trap.",
                _ => ""
            };
            bool youWon = (agent.Side.Value == PlayerSide.Solver) == solversWon;
            var spec = Cases.For(game.CaseKey);
            string body = $"{(solversWon ? "The Solvers" : "The Haunter")} win. {reason}\n{game.UnmaskLine()}";
            if (solversWon && game.EndReason.Value == MatchEndReason.Unmasked)
                body += "\n\n" + spec.Recovered + (string.IsNullOrEmpty(spec.ArcClue) ? "" : "\n" + UITheme.Tint("Mask Keeper clue: ", UITheme.Accent) + spec.ArcClue);

            const float w = 600f;
            float bodyH = UITheme.Center.CalcHeight(new GUIContent(body), w - 48f);
            var r = new Rect(UITheme.W / 2f - w / 2f, UITheme.H * 0.24f, w, 96f + bodyH + 64f);
            GUI.Box(r, GUIContent.none);
            GUI.Label(new Rect(r.x, r.y + UITheme.S5, w, 44), youWon ? "You win" : "You lose", UITheme.DisplayCenter);
            GUI.Label(new Rect(r.x + 24, r.y + 80, w - 48, bodyH), body, UITheme.Center);
            var action = new Rect(r.center.x - 140, r.yMax - 52, 280, 36);
            if (game.InTown && NetworkManager.Singleton.IsHost && GUI.Button(action, "Next night: back to HQ", UITheme.Primary))
                agent.NextNightRpc();
            else if (game.InTown && !NetworkManager.Singleton.IsHost)
                GUI.Label(action, "Waiting for the host to drive back to HQ…", UITheme.SmallCenter);
        }

        /// <summary>
        /// Bottom right, newest at the bottom. Toasts arrive on their own (not from a key press), so
        /// they ease in over 180 ms and fade out over 140 ms; reduced motion keeps only the fade.
        /// </summary>
        void DrawToasts()
        {
            const float w = 380f;
            float bottom = UITheme.H - UITheme.Edge - 36f;
            for (int i = toasts.Count - 1; i >= 0; i--)
            {
                var t = toasts[i];
                float h = Mathf.Max(40f, UITheme.BodyWrap.CalcHeight(new GUIContent(t.Text), w - 28f) + 18f);
                var (alpha, rise) = UITheme.Arrive(t.Shown, t.Until);
                var r = new Rect(UITheme.W - UITheme.Edge - w, bottom - h + rise, w, h);
                var old = GUI.color;
                GUI.color = new Color(1f, 1f, 1f, alpha);
                GUI.Box(r, GUIContent.none);
                GUI.Label(new Rect(r.x + 14, r.y + 9, w - 28, h - 12), t.Text, UITheme.BodyWrap);
                GUI.color = old;
                bottom -= h + UITheme.S2;
            }
        }
    }
}
