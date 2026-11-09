using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Unmasked.EditorTools
{
    /// <summary>
    /// The first things to run in Unity. "Check Project Data" reads every level, costume and case
    /// file the game needs without pressing Play. "Run Smoke Test" builds whatever scene is missing,
    /// then plays one whole night by itself (see <see cref="SmokeTest"/>) and reports where it broke.
    /// From a terminal: `unmasked smoke` runs both headless and exits 0 on a pass.
    /// </summary>
    [InitializeOnLoad]
    static class SelfTest
    {
        const string BatchKey = "Unmasked.SmokeBatch";

        // Play mode reloads the scripts, so a terminal run re-attaches here to quit with the result.
        static SelfTest()
        {
            if (SessionState.GetBool(BatchKey, false))
                SmokeTest.Finished += ok =>
                {
                    SessionState.EraseBool(BatchKey);
                    EditorApplication.Exit(ok ? 0 : 1);
                };
        }

        static string ProjectRoot => Directory.GetParent(Application.dataPath).FullName;

        [MenuItem("Unmasked/Check Project Data", priority = -19)]
        static void CheckDataMenu()
        {
            var problems = CheckData();
            if (problems.Count == 0)
                EditorUtility.DisplayDialog("Project data", "Every level, costume, case and font file loads.", "Good");
            else
                EditorUtility.DisplayDialog("Project data", $"{problems.Count} problem(s), also in the Console:\n\n" + string.Join("\n", problems.Take(8)), "OK");
        }

        [MenuItem("Unmasked/Run Smoke Test (plays one night by itself)", priority = -18)]
        static void RunMenu() => Run(false);

        /// <summary>`unmasked smoke`: Unity -batchmode -executeMethod Unmasked.EditorTools.SelfTest.RunBatch (no -quit).</summary>
        public static void RunBatch() => Run(true);

        static void Run(bool batch)
        {
            var problems = CheckData();
            if (problems.Count > 0)
            {
                Debug.LogError("[Unmasked] SMOKE TEST FAILED before Play: the project data has problems.\n  " + string.Join("\n  ", problems));
                if (batch) EditorApplication.Exit(1);
                return;
            }

            if (!File.Exists(Path.Combine(ProjectRoot, ManorBuilder.ScenePath))) ManorBuilder.Build();
            if (!File.Exists(Path.Combine(ProjectRoot, TownBuilder.ScenePath))) TownBuilder.Build();
            if (EditorSceneManager.GetActiveScene().path != TownBuilder.ScenePath)
            {
                if (!batch && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
                EditorSceneManager.OpenScene(TownBuilder.ScenePath);
            }

            // Play mode reloads every script, so the request travels in PlayerPrefs (SmokeTest reads and clears it).
            PlayerPrefs.SetInt(SmokeTest.RequestKey, 1);
            PlayerPrefs.SetInt(SmokeTest.QuitKey, batch ? 1 : 0);
            SessionState.SetBool(BatchKey, batch);
            PlayerPrefs.Save();
            Debug.Log("[Unmasked] Smoke test: pressing Play in Hollow Creek.");
            EditorApplication.isPlaying = true;
        }

        /// <summary>Everything the game loads from Resources, plus every case. Empty when all is well.</summary>
        public static List<string> CheckData()
        {
            var problems = new List<string>();

            if (Costumes.Current == null) problems.Add("Resources/Costumes.json is missing or unreadable (run Docs/tools/make_costumes.py)");
            if (ManorLayout.Current == null) problems.Add("Resources/BlackwoodManor.json is missing or unreadable (run Docs/tools/make_manor.py)");
            var town = TownLayout.Current;
            if (town == null) problems.Add("Resources/HollowCreek.json is missing or unreadable (run Docs/tools/make_town.py)");
            else if (town.lots == null || town.lots.Length == 0) problems.Add("HollowCreek.json has no house lots");
            else
                foreach (var lot in town.lots)
                    if (!string.IsNullOrEmpty(lot.resource) && TownLayout.HouseLayout(lot) == null)
                        problems.Add($"house layout Resources/{lot.resource}.json for {lot.id} is missing or unreadable");

            foreach (var font in new[] { "Fonts/Fraunces-Display", "Fonts/Fraunces-Title", "Fonts/Atkinson-Regular", "Fonts/Atkinson-Bold" })
                if (Resources.Load<Font>(font) == null) problems.Add($"Resources/{font}.ttf is missing (the interface falls back to Unity's font)");

            foreach (var spec in Cases.All)
            {
                CaseDefinition built = null;
                try { built = Cases.Build(spec.CaseId); }
                catch (System.Exception e) { problems.Add($"case {spec.CaseId} throws while building: {e.Message}"); continue; }
                if (built == null) { problems.Add($"case {spec.CaseId} builds to nothing"); continue; }
                int suspects = built.Suspects.Count(s => s != null);
                if (suspects != 4) problems.Add($"case {spec.CaseId} has {suspects} suspects, 4 expected");
                Object.DestroyImmediate(built);
            }

            foreach (var p in problems) Debug.LogError("[Unmasked] Data check: " + p);
            if (problems.Count == 0) Debug.Log($"[Unmasked] Data check: costumes, the town, {town?.lots?.Length ?? 0} house lots, the manor, 4 fonts and {Cases.All.Length} cases all load.");
            return problems;
        }
    }
}
