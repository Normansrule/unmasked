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
    /// Placeholder HUD in IMGUI so the prototype runs with no UI assets: connect menu, phase timer,
    /// setup picks, Solver and Haunter panels, the Suspect Board (Tab) and the end screens.
    /// TODO(UI milestone): replace with a styled UI Toolkit HUD.
    /// </summary>
    public class GameHUD : MonoBehaviour
    {
        struct ToastLine { public string Text; public float Until; }
        static readonly List<ToastLine> toasts = new();

        /// <summary>Any machine: show a message for a few seconds.</summary>
        public static void Toast(string message)
        {
            toasts.Add(new ToastLine { Text = message, Until = Time.time + 6f });
            if (toasts.Count > 5) toasts.RemoveAt(0);
            Debug.Log("[Unmasked] " + message);
        }

        string address = "127.0.0.1";
        string port = "7777";
        bool boardOpen;
        Vector2 boardScroll;
        GUIStyle wrap, big, title, centered;

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

            toasts.RemoveAll(t => Time.time > t.Until);

            if (keyboard != null && keyboard.f12Key.wasPressedThisFrame) TakeScreenshot();
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
            Vector2 m = Mouse.current.position.ReadValue();
            return m.x < 340f; // the setup panel lives on the left edge
        }

        void OnGUI()
        {
            if (wrap == null)
            {
                wrap = new GUIStyle(GUI.skin.label) { wordWrap = true };
                big = new GUIStyle(GUI.skin.label) { fontSize = 26, alignment = TextAnchor.MiddleCenter, wordWrap = true };
                title = new GUIStyle(GUI.skin.label) { fontSize = 16, fontStyle = FontStyle.Bold };
                centered = new GUIStyle(GUI.skin.label) { fontSize = 15, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
            }

            var net = NetworkManager.Singleton;
            if (net == null) { GUI.Label(new Rect(10, 10, 600, 30), "No NetworkManager in the scene. Run Unmasked > Build Blackwood Manor (3D)."); return; }

            if (!net.IsClient && !net.IsServer) { DrawConnectMenu(net); DrawToasts(); return; }

            var game = MysteryGameManager.Instance;
            var agent = PlayerAgent.Local;

            if (net.IsServer && !net.IsClient)
            {
                GUI.Label(new Rect(10, 10, 400, 25), $"Dedicated server running. Players: {net.ConnectedClientsIds.Count}");
                if (GUI.Button(new Rect(10, 40, 120, 30), "Stop")) net.Shutdown();
                DrawToasts();
                return;
            }

            if (game == null || !game.IsSpawned || agent == null) { GUI.Label(new Rect(10, 10, 300, 25), "Connecting..."); return; }

            DrawTopBar(game);

            if (game.Phase.Value == MatchPhase.Setup) DrawSetup(game, agent);

            if (agent.Side.Value == PlayerSide.Solver) DrawSolverPanel(game, agent);
            else DrawHaunterPanel(game, agent);

            if (boardOpen) DrawBoard(game, agent);
            DrawEnd(game, agent);
            DrawToasts();

            if (!boardOpen && Cursor.lockState != CursorLockMode.Locked)
                GUI.Label(new Rect(Screen.width / 2f - 230, Screen.height - 30, 460, 25), TownMap.Instance != null ? "Click to look around. Esc frees the mouse. Tab: Suspect Board. M: map. F1: handbook" : "Click to look around. Esc frees the mouse. Tab: Suspect Board. F1: handbook");
            else if (Cursor.lockState == CursorLockMode.Locked)
                GUI.Label(new Rect(Screen.width / 2f - 5, Screen.height / 2f - 10, 20, 20), "+");
        }

        // ---------------------------------------------------------------

        void DrawConnectMenu(NetworkManager net)
        {
            GUILayout.BeginArea(new Rect(20, 20, 320, 260), GUI.skin.box);
            GUILayout.Label("UNMASKED: prototype", title);
            GUILayout.Label("Address");
            address = GUILayout.TextField(address);
            GUILayout.Label("Port");
            port = GUILayout.TextField(port);

            var transport = net.GetComponent<UnityTransport>();
            ushort portNumber = ushort.TryParse(port, out var parsed) ? parsed : (ushort)7777;

            if (GUILayout.Button("Host (play + serve)"))
            {
                transport?.SetConnectionData("0.0.0.0", portNumber);
                net.StartHost();
            }
            if (GUILayout.Button("Join"))
            {
                transport?.SetConnectionData(address, portNumber);
                net.StartClient();
            }
            if (GUILayout.Button("Dedicated server"))
            {
                transport?.SetConnectionData("0.0.0.0", portNumber);
                net.StartServer();
            }
            GUILayout.EndArea();
        }

        void DrawTopBar(MysteryGameManager game)
        {
            float t = game.PhaseTimeRemaining;
            string time = game.PhaseEndTime.Value > 0 ? $"{(int)t / 60}:{(int)t % 60:00}" : "";
            string phase = game.Phase.Value switch
            {
                MatchPhase.Setup => game.InTown ? "At HQ: pick tonight's call. The Haunter picks a disguise" : "Setup: the Haunter picks a disguise",
                MatchPhase.Dispatch => $"Call from {game.HouseName}! Drive there ({time})",
                MatchPhase.Investigation => $"Investigation, {game.NightClock(game.Now)}. Dawn in {time}",
                MatchPhase.Trap => $"TRAP! Catch the Haunter: {time}",
                MatchPhase.Unmasking => "Unmasking!",
                MatchPhase.Ended => "Match over",
                _ => "Waiting"
            };
            string info = game.Phase.Value == MatchPhase.Investigation
                ? $"   Clues {game.Clues.Count} (need {game.CluesRequiredToAccuse.Value} to accuse)   Accusations left {game.AccusationsLeft.Value}   Alibi checks {game.AlibiChecksLeft.Value}"
                : "";
            GUI.Box(new Rect(Screen.width / 2f - 330, 6, 660, 28), phase + (game.Phase.Value == MatchPhase.Setup ? $" ({time})" : "") + info);
            if (game.Event.Value != NightEvent.None && game.Phase.Value >= MatchPhase.Dispatch && game.Phase.Value < MatchPhase.Ended)
            {
                GUI.color = new Color(1f, 0.45f, 0.45f);
                GUI.Label(new Rect(Screen.width / 2f - 330, 56, 660, 22), $"Tonight: {TownLayout.EventName(game.Event.Value)}", centered);
                GUI.color = Color.white;
            }
            if (game.Phase.Value >= MatchPhase.Investigation && game.Phase.Value < MatchPhase.Ended)
            {
                GUI.color = new Color(1f, 0.65f, 0.25f);
                GUI.Label(new Rect(Screen.width / 2f - 330, 36, 660, 22), $"Mask in play: {MysteryGameManager.MaskName(game.Villain.Value)}. Who is wearing it? That's the case.", centered);
                GUI.color = Color.white;
            }
        }

        float startOverArmedUntil;

        void DrawSetup(MysteryGameManager game, PlayerAgent agent)
        {
            GUILayout.BeginArea(new Rect(10, 40, 340, 560), GUI.skin.box);
            GUILayout.Label("Pick a side", title);
            GUILayout.BeginHorizontal();
            if (GUILayout.Toggle(agent.Side.Value == PlayerSide.Solver, "Solver", GUI.skin.button) && agent.Side.Value != PlayerSide.Solver)
                agent.RequestSideRpc(PlayerSide.Solver);
            if (GUILayout.Toggle(agent.Side.Value == PlayerSide.Haunter, "Haunter", GUI.skin.button) && agent.Side.Value != PlayerSide.Haunter)
                agent.RequestSideRpc(PlayerSide.Haunter);
            GUILayout.EndHorizontal();

            if (agent.Side.Value == PlayerSide.Solver)
            {
                GUILayout.Label("Role", title);
                foreach (SolverRole role in System.Enum.GetValues(typeof(SolverRole)))
                    if (GUILayout.Toggle(agent.Role.Value == role, $"{role}: {RoleBlurb(role)}", GUI.skin.button) && agent.Role.Value != role)
                        agent.RequestRoleRpc(role);

                var town = game.InTown ? TownLayout.Current : null;
                if (town?.lots != null)
                {
                    GUILayout.Space(8);
                    GUILayout.Label("Call board: tonight's call", title);
                    string active = game.ActiveHouse.Value.ToString();
                    foreach (var lot in town.lots)
                    {
                        if (!game.IsUnlocked(lot.id))
                        {
                            GUILayout.Label($"???: solve the other four cases and this one will call ({lot.street})", wrap);
                            continue;
                        }
                        string next = game.NextCaseFor(lot.id);
                        var nextSpec = Cases.For(next);
                        string tag = game.IsSolved(next) ? "  SOLVED" : nextSpec.IsReturnVisit ? "  RETURN VISIT" : "";
                        if (GUILayout.Toggle(active == lot.id, $"{lot.name} ({lot.size}): {nextSpec.CaseName}{tag}", GUI.skin.button) && active != lot.id)
                            agent.ChooseCallRpc(lot.id);
                    }
                    GUILayout.Label(game.SolvedCases.Count == 0
                        ? "No pick = The Missing Harvest Lantern, the club's first case. Open the map (M) to see every house."
                        : "No pick = a random call. Open the map (M) to see every house.", wrap);
                    GUILayout.Label($"Case book: {game.SolvedCases.Count} of {Cases.All.Length} solved. Keepsakes are on the shelf at HQ.", wrap);
                    if (Townsperson.All.Count > 0)
                        GUILayout.Label($"Errands for the townsfolk: {Townsperson.ErrandsDone} of {Townsperson.All.Count} done" +
                                        (game.Favours.Value > 0 ? $". Favours owed: {game.Favours.Value} extra alibi check{(game.Favours.Value > 1 ? "s" : "")} on the next case." : ". Talk to people around town (E)."), wrap);
                    if (Townsperson.All.Count > 0)
                    {
                        int pieces = game.WatchPieceCount;
                        GUILayout.Label(game.WearingWatch.Value
                            ? $"Lantern Watch costume: ON ({pieces} pieces). Scares hit {Mathf.RoundToInt((1f - game.WatchFearMultiplier) * 100f)}% softer. Take it off at the trunk."
                            : pieces >= MysteryGameManager.WatchPiecesNeeded
                                ? $"Lantern Watch costume: {pieces} pieces in the trunk at HQ. Put it on (E at the trunk)."
                                : $"Lantern Watch costume: {pieces} of {MysteryGameManager.WatchPiecesNeeded} pieces. The townsfolk give one for each errand.", wrap);
                    }
                    GUILayout.Label("The Mask Keeper", title);
                    GUILayout.Label(game.IsSolved(Cases.FinaleCase) ? Cases.ArcEpilogue : game.ArcComplete ? Cases.ArcFinale : Cases.ArcQuestion, wrap);
                    foreach (var solved in game.SolvedCases)
                        if (solved.ToString() != Cases.FinaleCase && !string.IsNullOrEmpty(Cases.For(solved.ToString()).ArcClue))
                            GUILayout.Label("- " + Cases.For(solved.ToString()).ArcClue, wrap);
                    if (NetworkManager.Singleton.IsHost && GUILayout.Button("Everyone's ready: leave now"))
                        agent.LeaveNowRpc();
                    if (NetworkManager.Singleton.IsHost)
                    {
                        // Irreversible, so it takes two presses, and the second has to come within a few seconds.
                        bool armed = Time.time < startOverArmedUntil;
                        if (GUILayout.Button(armed ? "Really start over? Press again to wipe the save" : "Start over (wipe the case book and errands)"))
                        {
                            if (armed) { agent.StartOverRpc(); startOverArmedUntil = 0f; }
                            else startOverArmedUntil = Time.time + 4f;
                        }
                    }
                }
            }
            else
            {
                GUILayout.Label("Who are you really? (secret)", title);
                foreach (var s in game.Suspects)
                {
                    string id = s.Id.ToString();
                    bool chosen = agent.LocalSecretIdentity == id;
                    if (GUILayout.Toggle(chosen, $"{s.Name} ({s.Occupation})", GUI.skin.button) && !chosen)
                        agent.ChooseIdentityRpc(id);
                }
                GUILayout.Label("No pick by the end of setup = a random suspect.", wrap);

                GUILayout.Space(8);
                GUILayout.Label("Your costume (everyone sees it)", title);
                foreach (VillainKind v in System.Enum.GetValues(typeof(VillainKind)))
                {
                    bool chosen = game.Villain.Value == v;
                    if (GUILayout.Toggle(chosen, $"{Costumes.NameOf(v)}: {Costumes.PowerOf(v)}", GUI.skin.button) && !chosen)
                        agent.ChooseVillainRpc(v);
                }
                var legend = Costumes.For(game.Villain.Value);
                if (legend != null) GUILayout.Label($"{legend.legend}\n[6/Q] {legend.power}: {legend.powerBlurb}", wrap);
            }
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
            GUILayout.BeginArea(new Rect(10, Screen.height - 170, 320, 160), GUI.skin.box);
            if (agent.ScaredOut.Value)
            {
                GUILayout.Label("You ran screaming out of the house. Watch your friends finish the case!", wrap);
            }
            else if (solver != null)
            {
                GUILayout.Label($"{agent.Role.Value}   Panics {agent.PanicCount.Value}/{game.MaxPanicsBeforeScaredOut}");
                string here = ManorLayout.Describe(solver.transform.position);
                if (here.Length > 0) GUILayout.Label("You're in the " + here);
                Bar("Fear", solver.Fear.Percent, solver.IsPanicked ? "PANIC!" : null);
                if (solver.Flashlight != null) Bar("Battery", solver.Flashlight.BatteryPercent, solver.Flashlight.IsOn ? "on" : "off (F)");
                if (game.Phase.Value == MatchPhase.Trap)
                {
                    GUILayout.Label($"Carrying {agent.CarriedTrapPieces.Value}/{TrapPiece.MaxCarried} trap pieces");
                    var site = FindAnyObjectByType<TrapSite>();
                    if (site != null) GUILayout.Label(site.StatusText);
                }
                if (agent.Role.Value == SolverRole.Sleuth) GUILayout.Label(SleuthSense(solver));
                if (agent.Role.Value == SolverRole.Techie) GUILayout.Label(EctoDetector(solver));
                if (MysteryVan.TryGetSeat(solver.OwnerClientId, out _, out bool driving))
                    GUILayout.Label(driving ? $"Driving  {Mathf.Abs(MysteryVan.Instance.Speed) * 3.6f:0} km/h\n[W/S] gas/reverse [A/D] steer [Space] brake [E] get out" : "Riding in the van. [E] get out", title);
                else if (solver.Focused != null) GUILayout.Label($"[E] {solver.Focused.GetPrompt(solver)}", title);
            }
            GUILayout.EndArea();
        }

        static string SleuthSense(SolverController me)
        {
            float best = float.MaxValue;
            foreach (var clue in FindObjectsByType<ClueItem>(FindObjectsSortMode.None))
                if (!clue.IsDiscovered) best = Mathf.Min(best, Vector3.Distance(clue.transform.position, me.transform.position));
            return best <= ClueItem.SleuthSenseRadius ? $"Clue sense: something is {best:0}m away!" : "Clue sense: nothing close";
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
            return "Ecto-detector: " + new string('|', bars * 2) + (bars >= 4 ? "  BEEP BEEP" : "");
        }

        void DrawHaunterPanel(MysteryGameManager game, PlayerAgent agent)
        {
            var haunter = HaunterController.Local;
            GUILayout.BeginArea(new Rect(10, Screen.height - 320, 360, 310), GUI.skin.box);
            string identity = string.IsNullOrEmpty(agent.LocalSecretIdentity) ? "(not chosen)" : game.SuspectName(agent.LocalSecretIdentity);
            GUILayout.Label($"HAUNTER. Secretly: {identity}", title);
            GUILayout.Label("Careful: suspects who see a scare up close remember a detail about you.", wrap);
            if (haunter != null)
            {
                string here = ManorLayout.Describe(haunter.transform.position);
                if (here.Length > 0) GUILayout.Label("Haunting the " + here);
            }
            if (haunter != null)
            {
                Bar("Ecto", haunter.Ectoplasm.Value / haunter.Ectoplasm.Max, null);
                string form = haunter.IsStunned ? "STUNNED" : haunter.IsPhysical ? "In costume (visible!)" : "Spectral (invisible)";
                GUILayout.Label(form);

                var obj = haunter.Possessed;
                if (obj != null)
                {
                    GUILayout.Label($"Inside {obj.name}. [E] leave");
                    for (int i = 0; i < obj.Actions.Count && i < 2; i++)
                    {
                        var spec = obj.Actions[i];
                        float cd = obj.CooldownRemaining(i);
                        GUILayout.Label($"[{(i == 0 ? "LMB" : "RMB")}] {spec.Action} ({spec.Cost:0} ecto){(cd > 0 ? $" {cd:0}s" : "")}");
                    }
                }
                else if (haunter.FocusedObject != null)
                {
                    GUILayout.Label($"[E] Possess {haunter.FocusedObject.name} ({haunter.PossessCost:0} ecto)", title);
                }

                for (int i = 0; i < haunter.Powers.Powers.Count; i++)
                {
                    var spec = haunter.Powers.Powers[i];
                    float cd = haunter.Powers.CooldownRemaining(i);
                    bool ok = haunter.Powers.IsAllowedNow(spec) && cd <= 0f && haunter.Ectoplasm.CanAfford(spec.Cost);
                    GUI.color = ok ? Color.white : new Color(1f, 1f, 1f, 0.45f);
                    string key = spec.Power == HaunterPower.Signature ? $"{i + 1}/Q" : $"{i + 1}";
                    GUILayout.Label($"[{key}] {haunter.Powers.DisplayName(spec)} ({spec.Cost:0}){(cd > 0 ? $" {cd:0}s" : "")}");
                }
                GUI.color = Color.white;
                float plantCd = haunter.PlantFakeClueCooldownRemaining;
                GUILayout.Label($"[G] Plant fake clue ({haunter.PlantFakeClueCost:0}){(plantCd > 0 ? $" {plantCd:0}s" : "")}");
                string myId = agent.LocalSecretIdentity;
                string alibiRoom = string.IsNullOrEmpty(myId) ? "" : game.AlibiRoomOf(myId);
                if (alibiRoom.Length > 0)
                {
                    bool faked = game.Mystery != null && game.Mystery.AlibiFaked; // host only; clients just see the prompt
                    int status = game.AlibiStatus(myId);
                    GUILayout.Label(status == 1 ? "Your alibi was checked and held up."
                        : status == -1 ? "Your alibi was checked and fell apart!"
                        : faked ? "Alibi faked."
                        : $"[H] Fake your alibi in the {alibiRoom} ({haunter.FakeAlibiCost:0})");
                }
            }
            if (Time.time - agent.LastClueLeakTime < 4f)
            {
                GUI.color = new Color(1f, 0.5f, 0.3f);
                GUILayout.Label("Careful! You left a clue behind.", title);
                GUI.color = Color.white;
            }
            GUILayout.EndArea();
        }

        void Bar(string label, float fraction, string note)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(label, GUILayout.Width(55));
            Rect r = GUILayoutUtility.GetRect(180, 16);
            GUI.Box(r, "");
            GUI.Box(new Rect(r.x, r.y, r.width * Mathf.Clamp01(fraction), r.height), "");
            GUILayout.Label(note ?? $"{fraction * 100f:0}%", GUILayout.Width(80));
            GUILayout.EndHorizontal();
        }

        void DrawBoard(MysteryGameManager game, PlayerAgent agent)
        {
            var area = new Rect(Screen.width * 0.08f, Screen.height * 0.08f, Screen.width * 0.84f, Screen.height * 0.84f);
            GUILayout.BeginArea(area, GUI.skin.box);
            GUILayout.Label("SUSPECT BOARD  (Tab to close)", title);
            boardScroll = GUILayout.BeginScrollView(boardScroll);

            int[] matches = game.ClueMatchCounts();
            bool isSolver = agent.Side.Value == PlayerSide.Solver && !agent.ScaredOut.Value;
            for (int i = 0; i < game.Suspects.Count; i++)
            {
                var s = game.Suspects[i];
                string id = s.Id.ToString();
                bool cleared = game.IsCleared(id);

                GUILayout.BeginVertical(GUI.skin.box);
                GUILayout.BeginHorizontal();
                GUILayout.Label($"{(cleared ? "<s>" : "")}{s.Name}{(cleared ? "</s>  CLEARED" : "")}  ({s.Occupation}){(hunches.Contains(id) ? "   YOUR HUNCH" : "")}", new GUIStyle(title) { richText = true });
                GUILayout.FlexibleSpace();
                GUILayout.Label($"Clues pointing here: {matches[i]}");
                if (isSolver)
                {
                    bool hunch = hunches.Contains(id);
                    if (GUILayout.Button(hunch ? "Drop hunch" : "Hunch", GUILayout.Width(90)))
                    {
                        if (hunch) hunches.Remove(id); else hunches.Add(id);
                    }
                    if (GUILayout.Button(cleared ? "Restore" : "Cross off", GUILayout.Width(90))) agent.SetSuspectClearedRpc(id, !cleared);
                    GUI.enabled = game.CanAccuseNow && !cleared;
                    if (GUILayout.Button("ACCUSE", GUILayout.Width(90))) agent.AccuseRpc(id);
                    GUI.enabled = true;
                }
                GUILayout.EndHorizontal();
                GUILayout.Label(s.Bio.ToString(), wrap);
                string alibiRoom = s.AlibiRoom.ToString();
                int alibi = game.AlibiStatus(id);
                GUILayout.BeginHorizontal();
                GUILayout.Label("Statement on arrival (8:00 PM): " + s.Alibi + (alibi == 1 ? "  (checked: holds up)" : alibi == -1 ? "  (checked: FALLS APART!)" : ""), wrap);
                if (isSolver && alibi == 0 && alibiRoom.Length > 0 && game.Phase.Value == MatchPhase.Investigation)
                {
                    bool here = LocalSolverRoom() == alibiRoom;
                    GUI.enabled = here && game.AlibiChecksLeft.Value > 0;
                    if (GUILayout.Button(here ? "Check alibi" : $"Search the {alibiRoom}", GUILayout.Width(170))) agent.CheckAlibiRpc(id);
                    GUI.enabled = true;
                }
                GUILayout.EndHorizontal();
                GUILayout.Label("Traits: " + TraitText(game, s.Traits));
                GUILayout.EndVertical();
            }

            // The board keeps what was seen, what was said and what follows apart: a jumpy suspect is
            // character, not proof. Every entry carries its source and the time of night.
            GUILayout.Space(8);
            GUILayout.Label($"Evidence: what the club found ({game.Clues.Count})", title);
            if (game.Clues.Count == 0) GUILayout.Label("None yet. Search the house!");
            foreach (var c in game.Clues)
            {
                string where = ManorLayout.Describe(c.Location);
                string when = game.NightClock(c.DiscoveredAt);
                string stamp = string.Join(", ", new[] { when, where }.Where(x => !string.IsNullOrEmpty(x)));
                GUILayout.Label($"- {(stamp.Length > 0 ? "[" + stamp + "] " : "")}{c.Name}: {c.Description}  ({TraitText(game, c.Traits)})", wrap);
            }

            GUILayout.Space(8);
            GUILayout.Label("Testimony: what people said", title);
            if (game.Interviews.Count == 0) GUILayout.Label("Nobody interviewed yet. Talk to the suspects (E).");
            foreach (var n in game.Interviews)
            {
                string when = game.NightClock(n.At);
                string kind = n.SuspiciousOfId.Length == 0 ? "saw the Haunter up close" : "gossip";
                GUILayout.Label($"- {(when.Length > 0 ? "[" + when + "] " : "")}{game.SuspectName(n.SpeakerId.ToString())} ({kind}): \"{n.Statement}\"", wrap);
            }

            GUILayout.Space(8);
            GUILayout.Label("Deductions: what follows", title);
            foreach (var line in Deductions(game))
                GUILayout.Label("- " + line, wrap);

            GUILayout.Space(8);
            GUILayout.Label("Tip: clues can be planted by the Haunter. Suspects can lie, and everyone is nervous when questioned. A suspect who saw a scare up close noticed something about the Haunter: interview them. Check an alibi by standing in the room it names (the Haunter can fake one, so a held-up alibi isn't proof). Hunches are yours alone. A wrong accusation clears that suspect but powers up the Haunter.", wrap);
            GUILayout.EndScrollView();
            GUILayout.EndArea();
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
                GUI.Label(new Rect(0, Screen.height * 0.2f, Screen.width, 80), $"UNMASKED! It was {game.SuspectName(game.RevealedCulprit.Value.ToString())}!", big);
                GUI.Label(new Rect(Screen.width / 2f - 320, Screen.height * 0.2f + 80, 640, 60), game.UnmaskLine(), new GUIStyle(wrap) { alignment = TextAnchor.UpperCenter, fontSize = 18 });
                return;
            }
            if (game.Phase.Value != MatchPhase.Ended) return;

            bool solversWon = game.Winner.Value == MatchWinner.Solvers;
            string reason = game.EndReason.Value switch
            {
                MatchEndReason.Unmasked => "The Haunter was caught and unmasked!",
                MatchEndReason.Dawn => "Dawn broke and the mystery went unsolved.",
                MatchEndReason.WrongAccusations => "Too many wrong accusations.",
                MatchEndReason.SolversScaredOut => "Every Solver was scared out of the house.",
                MatchEndReason.Escaped => "The Haunter escaped the trap.",
                _ => ""
            };
            bool youWon = (agent.Side.Value == PlayerSide.Solver) == solversWon;
            GUI.Box(new Rect(Screen.width / 2f - 300, Screen.height * 0.25f, 600, 230), "");
            GUI.Label(new Rect(Screen.width / 2f - 300, Screen.height * 0.25f + 10, 600, 50), youWon ? "YOU WIN" : "YOU LOSE", big);
            GUI.Label(new Rect(Screen.width / 2f - 290, Screen.height * 0.25f + 70, 580, 155),
                $"{(solversWon ? "Solvers" : "Haunter")} win. {reason}\n{game.UnmaskLine()}{(solversWon && game.EndReason.Value == MatchEndReason.Unmasked ? "\n" + Cases.For(game.CaseKey).Recovered + (string.IsNullOrEmpty(Cases.For(game.CaseKey).ArcClue) ? "" : "\nMask Keeper clue: " + Cases.For(game.CaseKey).ArcClue) : "")}", new GUIStyle(wrap) { alignment = TextAnchor.UpperCenter, fontSize = 16 });
            if (game.InTown && NetworkManager.Singleton.IsHost && GUI.Button(new Rect(Screen.width / 2f - 130, Screen.height * 0.25f + 236, 260, 34), "Next night: back to HQ"))
                agent.NextNightRpc();
            else if (game.InTown && !NetworkManager.Singleton.IsHost)
                GUI.Label(new Rect(Screen.width / 2f - 200, Screen.height * 0.25f + 236, 400, 30), "Waiting for the host to drive back to HQ...", new GUIStyle(wrap) { alignment = TextAnchor.UpperCenter });
        }

        void DrawToasts()
        {
            float y = 40;
            foreach (var t in toasts)
            {
                GUI.Box(new Rect(Screen.width - 430, y, 420, 40), "");
                GUI.Label(new Rect(Screen.width - 425, y + 3, 410, 36), t.Text, wrap);
                y += 44;
            }
        }
    }
}
