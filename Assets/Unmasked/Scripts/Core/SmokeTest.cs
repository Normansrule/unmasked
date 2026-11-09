using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Unity.Netcode;
using Unity.Netcode.Transports.UTP;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Plays one whole night by itself and says where it breaks: host a game, take the first call,
    /// drive to the house, find clues, work out who fits them, accuse, build the trap, unmask, and
    /// drive back to HQ. Every step has a time limit, and any error or exception logged along the way
    /// fails the run.
    ///
    /// Start it from the editor with Unmasked > Run Smoke Test, from a terminal with
    /// `unmasked smoke`, or in a built player with the `-unmasked-smoke` argument. The report goes
    /// to the Console, a panel on screen, and Logs/smoke-test.txt (in a player, next to its log).
    /// The club's saved progress (case book, favours, costume pieces, errands, hints) is put back
    /// exactly as it was afterwards.
    /// </summary>
    public class SmokeTest : MonoBehaviour
    {
        /// <summary>Set by the editor menu just before it presses Play; read once and cleared.</summary>
        public const string RequestKey = "Unmasked.SmokeRequested";
        /// <summary>1 when the run should quit Unity with an exit code (terminal and player runs).</summary>
        public const string QuitKey = "Unmasked.SmokeQuit";

        static readonly string[] SavedKeys =
        {
            "Unmasked.SolvedCases", "Unmasked.Favours", "Unmasked.WatchPieces", "Unmasked.WearingWatch",
            MysteryGameManager.ErrandsKey, Handbook.SeenKey, ClubBook.SaveKey,
        };

        public static bool Running { get; private set; }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void MaybeStart()
        {
            bool fromArgs = System.Environment.GetCommandLineArgs().Contains("-unmasked-smoke");
            bool requested = PlayerPrefs.GetInt(RequestKey, 0) == 1;
            if (!fromArgs && !requested) return;
            bool quit = fromArgs || PlayerPrefs.GetInt(QuitKey, 0) == 1;
            PlayerPrefs.DeleteKey(RequestKey);
            PlayerPrefs.DeleteKey(QuitKey);
            PlayerPrefs.Save();
            var go = new GameObject("Smoke Test");
            DontDestroyOnLoad(go);
            go.AddComponent<SmokeTest>().quitWhenDone = quit;
        }

        class Step { public string Name; public bool? Passed; public string Note = ""; public float Seconds; }

        readonly List<Step> steps = new();
        readonly List<string> problems = new();
        readonly Dictionary<string, string> savedPrefs = new();
        bool quitWhenDone, finished;
        float started;

        const float OverallLimit = 300f;

        void OnEnable() => Application.logMessageReceived += OnLog;
        void OnDisable() => Application.logMessageReceived -= OnLog;

        void OnLog(string message, string stack, LogType type)
        {
            if (finished || type == LogType.Log || type == LogType.Warning) return;
            if (problems.Count < 12)
                problems.Add($"{type}: {message}" + (type == LogType.Exception && stack.Length > 0 ? "\n    " + stack.Split('\n')[0] : ""));
        }

        IEnumerator Start()
        {
            Running = true;
            started = Time.realtimeSinceStartup;
            foreach (var key in SavedKeys)
                if (PlayerPrefs.HasKey(key)) savedPrefs[key] = PlayerPrefs.GetString(key, PlayerPrefs.GetInt(key, 0).ToString());
            Debug.Log("[Unmasked] Smoke test: playing one night by itself.");
            yield return Run();
            Finish();
        }

        void Update()
        {
            if (!finished && Time.realtimeSinceStartup - started > OverallLimit)
            {
                Fail(Current, $"the whole run took more than {OverallLimit:0} seconds");
                StopAllCoroutines();
                Finish();
            }
        }

        Step Current => steps.Count > 0 ? steps[^1] : null;

        Step Begin(string name)
        {
            var step = new Step { Name = name, Seconds = Time.realtimeSinceStartup };
            steps.Add(step);
            Debug.Log($"[Unmasked] Smoke test: {name}...");
            return step;
        }

        void Pass(Step step, string note = "")
        {
            step.Passed = true;
            step.Note = note;
            step.Seconds = Time.realtimeSinceStartup - step.Seconds;
        }

        void Fail(Step step, string why)
        {
            if (step == null) step = Begin("Start");
            step.Passed = false;
            step.Note = why;
            step.Seconds = Time.realtimeSinceStartup - step.Seconds;
        }

        bool failed;

        /// <summary>Waits until the condition holds, or fails the step after `limit` seconds.</summary>
        IEnumerator Until(Step step, System.Func<bool> done, float limit, string why)
        {
            float t0 = Time.realtimeSinceStartup;
            while (!done())
            {
                if (Time.realtimeSinceStartup - t0 > limit) { Fail(step, $"{why} (waited {limit:0} s)"); failed = true; yield break; }
                yield return null;
            }
        }

        IEnumerator Run()
        {
            // ---- 1. Host ----
            var step = Begin("Host a game");
            var net = NetworkManager.Singleton;
            if (net == null) { Fail(step, "no NetworkManager in the scene: build Hollow Creek first (Unmasked menu)"); yield break; }
            if (!net.IsListening)
            {
                net.GetComponent<UnityTransport>()?.SetConnectionData("127.0.0.1", 7777, "0.0.0.0");
                if (!net.StartHost()) { Fail(step, "NetworkManager.StartHost returned false (is port 7777 in use?)"); yield break; }
            }
            yield return Until(step, () => MysteryGameManager.Instance != null && MysteryGameManager.Instance.IsSpawned
                && PlayerAgent.Local != null && PlayerAgent.Local.Pawn != null && SolverController.Local != null, 20f,
                "the game manager, the player or their Solver never spawned");
            if (failed) yield break;
            var game = MysteryGameManager.Instance;
            var agent = PlayerAgent.Local;
            Pass(step, game.InTown ? "Hollow Creek" : "a single house");

            // ---- 2. Setup and the call ----
            step = Begin("Take the first call");
            yield return Until(step, () => game.Phase.Value == MatchPhase.Setup, 10f, "setup never started");
            if (failed) yield break;
            if (game.InTown)
            {
                game.HandleCallChoice(agent, Cases.FirstCase);
                if (game.ActiveHouse.Value.ToString() != Cases.FirstCase) { Fail(step, $"picking {Cases.FirstCase} on the call board didn't stick"); yield break; }
                game.HandleLeaveNow(agent);
            }
            else game.PhaseEndTime.Value = game.Now + 1.0;
            var next = game.InTown ? MatchPhase.Dispatch : MatchPhase.Investigation;
            yield return Until(step, () => game.Phase.Value == next, 15f, $"the night never moved on to {next}");
            if (failed) yield break;
            Pass(step, game.InTown ? game.Mystery.Case.CaseName : "");

            // ---- 3. The drive ----
            if (game.InTown)
            {
                step = Begin("Drive to the house");
                var site = game.ActiveSite;
                if (site == null || site.Arrival == null) { Fail(step, "tonight's house has no arrival point"); yield break; }
                SolverController.Local.ServerTeleport(site.Arrival.position + Vector3.up * 0.2f);
                yield return Until(step, () => game.Phase.Value == MatchPhase.Investigation, 15f, "arriving at the lot didn't start the investigation");
                if (failed) yield break;
                Pass(step, site.DisplayName);
            }

            // ---- 4. Clues ----
            step = Begin("Find clues");
            string accused = "";
            float clueLimit = Time.realtimeSinceStartup + 60f;
            while (game.Phase.Value == MatchPhase.Investigation)
            {
                if (Time.realtimeSinceStartup > clueLimit) { Fail(step, $"found {game.Clues.Count} clue(s) but couldn't name anyone in 60 s"); yield break; }
                string fits = OnlySuspectFittingEveryClue(game);
                if (game.Clues.Count >= game.CluesRequiredToAccuse.Value && fits != null && fits != accused)
                {
                    // ---- 5. The accusation ----
                    if (step.Name != "Accuse the one who fits")
                    {
                        Pass(step, $"{game.Clues.Count} clues: {string.Join(", ", ClueNames(game))}");
                        step = Begin("Accuse the one who fits");
                    }
                    accused = fits;
                    agent.LastAccusationTime = -1000f; // the cooldown is for people, not for this
                    game.HandleAccusation(agent, fits);
                    yield return new WaitForSeconds(0.5f);
                    if (game.Phase.Value == MatchPhase.Trap) { Pass(step, game.SuspectName(fits)); break; }
                    if (game.Phase.Value == MatchPhase.Ended) { Fail(step, $"{game.SuspectName(fits)} was wrong and the club ran out of accusations"); yield break; }
                    step.Note = $"{game.SuspectName(fits)} was innocent (a planted clue?), looking again";
                    continue;
                }
                var clue = Object.FindObjectsByType<ClueItem>(FindObjectsSortMode.None)
                    .FirstOrDefault(c => c.IsSpawned && !c.IsDiscovered && HouseSite.InPlay(c));
                if (clue != null)
                {
                    SolverController.Local.ServerTeleport(clue.transform.position + Vector3.up * 0.2f);
                    yield return new WaitForSeconds(0.3f);
                    game.Mystery.DiscoverClue(clue, SolverController.Local);
                }
                yield return new WaitForSeconds(0.3f);
            }
            if (game.Phase.Value != MatchPhase.Trap) { Fail(step, $"the night ended during the investigation ({game.EndReason.Value})"); yield break; }

            // ---- 6. The trap ----
            step = Begin("Build the trap");
            var trap = Object.FindObjectsByType<TrapSite>(FindObjectsSortMode.None).FirstOrDefault(HouseSite.InPlay);
            if (trap == null) { Fail(step, "no trap site at this house"); yield break; }
            float trapLimit = Time.realtimeSinceStartup + 40f;
            while (!trap.IsArmed && game.Phase.Value == MatchPhase.Trap)
            {
                if (Time.realtimeSinceStartup > trapLimit) { Fail(step, $"the trap has {trap.Pieces} of {trap.RequiredPieces} pieces and {trap.Work} work after 40 s"); yield break; }
                var solver = SolverController.Local;
                if (trap.Pieces < trap.RequiredPieces && agent.CarriedTrapPieces.Value < TrapPiece.MaxCarried)
                {
                    var piece = Object.FindObjectsByType<TrapPiece>(FindObjectsSortMode.None).FirstOrDefault(p => HouseSite.InPlay(p) && p.CanInteract(solver));
                    if (piece != null) { solver.ServerTeleport(piece.transform.position + Vector3.up * 0.2f); yield return new WaitForSeconds(0.2f); piece.Interact(solver); }
                    else if (agent.CarriedTrapPieces.Value == 0) { Fail(step, $"only {trap.Pieces} trap pieces could be found, {trap.RequiredPieces} are needed"); yield break; }
                }
                else
                {
                    solver.ServerTeleport(trap.transform.position + Vector3.up * 0.2f);
                    yield return new WaitForSeconds(0.2f);
                    trap.Interact(solver);
                }
                yield return new WaitForSeconds(0.2f);
            }
            Pass(step, $"{trap.Pieces} pieces");

            // ---- 7. Unmasking ----
            step = Begin("Catch and unmask the Haunter");
            if (StandInHaunter.Active != null)
            {
                // The costumed stand-in only takes the bait while nobody guards the trap: step back and wait.
                var site = game.ActiveSite;
                Vector3 away = site != null && site.Arrival != null ? site.Arrival.position : trap.transform.position;
                if (Vector3.Distance(away, trap.transform.position) < StandInHaunter.Active.GuardDistance + 2f)
                    away = trap.transform.position + (trap.transform.position - StandInHaunter.Active.Position).normalized * (StandInHaunter.Active.GuardDistance + 4f);
                SolverController.Local.ServerTeleport(away + Vector3.up * 0.2f);
            }
            yield return Until(step, () => game.Phase.Value == MatchPhase.Ended, 75f,
                StandInHaunter.Active != null ? "the costumed suspect never walked into the armed trap" : "the Haunter was never caught and unmasked");
            if (failed) yield break;
            if (game.Winner.Value != MatchWinner.Solvers) { Fail(step, $"the night ended with {game.Winner.Value} winning ({game.EndReason.Value})"); yield break; }
            Pass(step, game.UnmaskLine());

            // ---- 8. Another night ----
            if (game.InTown)
            {
                step = Begin("Back to HQ for another night");
                game.HandleNextNight(agent);
                yield return Until(step, () => game.Phase.Value == MatchPhase.Setup && game.ActiveHouse.Value.Length == 0 && game.Clues.Count == 0, 15f,
                    "the town didn't reset for the next night");
                if (failed) yield break;
                Pass(step, $"{game.SolvedCases.Count} case(s) in the book");
            }
        }

        /// <summary>The one suspect, not crossed off, who shares a trait with every clue found; null if none or several.</summary>
        static string OnlySuspectFittingEveryClue(MysteryGameManager game)
        {
            if (game.Clues.Count == 0) return null;
            string only = null;
            foreach (var s in game.Suspects)
            {
                string id = s.Id.ToString();
                if (game.IsCleared(id)) continue;
                bool all = true;
                foreach (var c in game.Clues)
                    if ((s.Traits & c.Traits) == 0) { all = false; break; }
                if (!all) continue;
                if (only != null) return null;
                only = id;
            }
            return only;
        }

        static IEnumerable<string> ClueNames(MysteryGameManager game)
        {
            foreach (var c in game.Clues) yield return c.Name.ToString();
        }

        void Finish()
        {
            if (finished) return;
            finished = true;
            Running = false;

            foreach (var key in SavedKeys) PlayerPrefs.DeleteKey(key);
            foreach (var kv in savedPrefs)
            {
                if (int.TryParse(kv.Value, out int n) && kv.Key != MysteryGameManager.ErrandsKey && kv.Key != "Unmasked.SolvedCases") PlayerPrefs.SetInt(kv.Key, n);
                else PlayerPrefs.SetString(kv.Key, kv.Value);
            }
            PlayerPrefs.Save();

            bool ok = steps.Count > 0 && steps.All(s => s.Passed == true) && problems.Count == 0;
            string report = Report(ok);
            if (ok) Debug.Log(report); else Debug.LogError(report);
            try
            {
                string dir = Application.isEditor ? Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Logs") : Application.persistentDataPath;
                Directory.CreateDirectory(dir);
                File.WriteAllText(Path.Combine(dir, "smoke-test.txt"), report);
            }
            catch (System.Exception e) { Debug.LogWarning("[Unmasked] Couldn't save the smoke test report: " + e.Message); }

            Finished?.Invoke(ok); // the editor's SelfTest quits Unity here for terminal runs
            if (quitWhenDone && !Application.isEditor) Application.Quit(ok ? 0 : 1);
        }

        /// <summary>Raised once with the result (true = passed).</summary>
        public static event System.Action<bool> Finished;

        string Report(bool ok)
        {
            var sb = new StringBuilder();
            sb.AppendLine(ok ? "[Unmasked] SMOKE TEST PASSED: one whole night played by itself." : "[Unmasked] SMOKE TEST FAILED");
            foreach (var s in steps)
                sb.AppendLine($"  {(s.Passed == true ? "ok  " : s.Passed == false ? "FAIL" : "... ")} {s.Name,-30} {s.Seconds,5:0.0} s  {s.Note}");
            if (problems.Count > 0)
            {
                sb.AppendLine("  Errors logged during the run (fix the first one first):");
                foreach (var p in problems) sb.AppendLine("    " + p);
            }
            sb.AppendLine($"  Total {Time.realtimeSinceStartup - started:0.0} s. Saved progress was put back as it was.");
            return sb.ToString();
        }

        Vector2 scroll;

        void OnGUI()
        {
            UITheme.Begin();
            var r = new Rect(UITheme.Edge, UITheme.H / 2f - 150f, 460f, 300f);
            UITheme.Rect(r, UITheme.Ground);
            GUILayout.BeginArea(new Rect(r.x + UITheme.S4, r.y + UITheme.S3, r.width - 2 * UITheme.S4, r.height - 2 * UITheme.S3));
            GUILayout.Label(finished ? (steps.All(s => s.Passed == true) && problems.Count == 0 ? "Smoke test passed" : "Smoke test failed") : "Smoke test running", UITheme.Title);
            scroll = GUILayout.BeginScrollView(scroll);
            foreach (var s in steps)
            {
                string mark = s.Passed == true ? UITheme.Tint("✓", UITheme.Good) : s.Passed == false ? UITheme.Tint("✗", UITheme.Danger) : UITheme.Tint("…", UITheme.Accent);
                GUILayout.Label($"{mark}  {s.Name}" + (s.Note.Length > 0 ? UITheme.Tint("  " + s.Note, UITheme.InkMuted) : ""), UITheme.BodyWrap);
            }
            foreach (var p in problems.Take(3)) GUILayout.Label(UITheme.Tint(p, UITheme.Danger), UITheme.Small);
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }
    }
}
