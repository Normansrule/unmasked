using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Unmasked.EditorTools
{
    /// <summary>
    /// The first time Unity opens this folder: turn on the Input System if it's off (one restart),
    /// offer to build Hollow Creek and Blackwood Manor (the scenes are generated, not stored), and open
    /// the town. After that, Unmasked > Play Hollow Creek builds whatever is missing and presses Play.
    /// </summary>
    [InitializeOnLoad]
    static class FirstOpen
    {
        const string CheckedKey = "Unmasked.FirstOpenChecked";

        static FirstOpen()
        {
            EditorApplication.delayCall += Check;
        }

        static string ProjectRoot => Directory.GetParent(Application.dataPath).FullName;
        static bool Exists(string scenePath) => File.Exists(Path.Combine(ProjectRoot, scenePath));

        static void Check()
        {
            if (Application.isBatchMode || EditorApplication.isPlayingOrWillChangePlaymode) return;
            if (SessionState.GetBool(CheckedKey, false)) return;
            SessionState.SetBool(CheckedKey, true);

            if (EnsureInputSystem()) return; // Unity restarts; we'll be back

            if (!Exists(TownBuilder.ScenePath))
            {
                bool build = EditorUtility.DisplayDialog("Welcome to UNMASKED",
                    "The town of Hollow Creek and Blackwood Manor are generated from data files, so they need building once on this computer.\n\n" +
                    "Build them now? It takes a minute or two. (You can always do it later from the Unmasked menu.)",
                    "Build Hollow Creek", "Later");
                if (build) BuildEverything();
                return;
            }

            // Opened on an empty untitled scene? Show the town instead.
            var active = EditorSceneManager.GetActiveScene();
            if (string.IsNullOrEmpty(active.path) && !active.isDirty)
                EditorSceneManager.OpenScene(TownBuilder.ScenePath);
        }

        /// <summary>The game reads the keyboard through the Input System package. Returns true if Unity is restarting.</summary>
        static bool EnsureInputSystem()
        {
            var assets = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset");
            if (assets == null || assets.Length == 0) return false;
            var settings = new SerializedObject(assets[0]);
            var handler = settings.FindProperty("activeInputHandler");
            if (handler == null || handler.intValue != 0) return false; // already the Input System, or both

            handler.intValue = 2; // both: the Input System for the game, the old one for anything else
            settings.ApplyModifiedProperties();
            AssetDatabase.SaveAssets();
            if (EditorUtility.DisplayDialog("UNMASKED needs one restart",
                    "The game uses Unity's Input System, which was switched off in this project. It's now on, but Unity has to restart to use it.",
                    "Restart Unity", "Later"))
            {
                EditorApplication.OpenProject(ProjectRoot);
                return true;
            }
            return false;
        }

        [MenuItem("Unmasked/Play Hollow Creek", priority = -20)]
        static void PlayTown()
        {
            if (!Exists(ManorBuilder.ScenePath)) ManorBuilder.Build();
            if (!Exists(TownBuilder.ScenePath)) TownBuilder.Build();
            else if (EditorSceneManager.GetActiveScene().path != TownBuilder.ScenePath)
            {
                if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
                EditorSceneManager.OpenScene(TownBuilder.ScenePath);
            }
            EditorApplication.EnterPlaymode();
        }

        [MenuItem("Unmasked/Rebuild Everything (town and manor)", priority = -15)]
        static void BuildEverything()
        {
            ManorBuilder.Build();
            TownBuilder.Build(); // last, so the town is the scene left open
            Debug.Log("[Unmasked] Hollow Creek and Blackwood Manor are built. Press Play, then Host.");
        }
    }
}
