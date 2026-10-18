using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Unmasked.EditorTools
{
    /// <summary>
    /// Makes playable builds. From the menu: Unmasked > Build Players. From a terminal (see
    /// tools/unmasked.sh): -executeMethod Unmasked.EditorTools.BuildScript.BuildAll
    /// GitHub Actions (GameCI) calls BuildFromCommandLine with -customBuildPath and -buildTarget.
    /// </summary>
    public static class BuildScript
    {
        /// <summary>The town comes first: a build starts in Hollow Creek. Blackwood Manor on its own is the second scene.</summary>
        static readonly string[] Scenes = { TownBuilder.ScenePath, ManorBuilder.ScenePath };

        static readonly (BuildTarget target, string folder, string exe)[] Targets =
        {
            (BuildTarget.StandaloneWindows64, "Windows", "Unmasked.exe"),
            (BuildTarget.StandaloneOSX, "macOS", "Unmasked.app"),
            (BuildTarget.StandaloneLinux64, "Linux", "Unmasked.x86_64"),
        };

        [MenuItem("Unmasked/Build Players (every installed platform)")]
        public static void BuildAll()
        {
            EnsureScene();
            string root = Path.Combine(ProjectRoot, "Builds");
            int built = 0;
            foreach (var (target, folder, exe) in Targets)
            {
                if (!BuildPipeline.IsBuildTargetSupported(BuildPipeline.GetBuildTargetGroup(target), target))
                {
                    Debug.Log($"[Unmasked] Skipping {folder}: that build support module isn't installed (Unity Hub > Installs > Add modules).");
                    continue;
                }
                if (Build(target, Path.Combine(root, folder, exe))) built++;
            }
            Debug.Log($"[Unmasked] Built {built} player(s) into {root}");
            if (Application.isBatchMode && built == 0) EditorApplication.Exit(1);
        }

        [MenuItem("Unmasked/Build Player (this computer)")]
        public static void BuildCurrent()
        {
            EnsureScene();
            var target = EditorUserBuildSettings.activeBuildTarget;
            var match = Targets.FirstOrDefault(t => t.target == target);
            string exe = match.exe ?? "Unmasked";
            string folder = match.folder ?? target.ToString();
            bool ok = Build(target, Path.Combine(ProjectRoot, "Builds", folder, exe));
            if (Application.isBatchMode && !ok) EditorApplication.Exit(1);
        }

        /// <summary>Entry point for GameCI: honours -customBuildPath and -buildTarget.</summary>
        public static void BuildFromCommandLine()
        {
            EnsureScene();
            string[] args = Environment.GetCommandLineArgs();
            string Arg(string name)
            {
                int i = Array.IndexOf(args, name);
                return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
            }

            var target = Enum.TryParse(Arg("-buildTarget"), out BuildTarget parsed) ? parsed : EditorUserBuildSettings.activeBuildTarget;
            string path = Arg("-customBuildPath") ?? Path.Combine(ProjectRoot, "Builds", target.ToString(), "Unmasked");
            bool ok = Build(target, path);
            EditorApplication.Exit(ok ? 0 : 1);
        }

        static bool Build(BuildTarget target, string path)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var options = new BuildPlayerOptions
            {
                scenes = Scenes,
                locationPathName = path,
                target = target,
                targetGroup = BuildPipeline.GetBuildTargetGroup(target),
                options = BuildOptions.None
            };
            var report = BuildPipeline.BuildPlayer(options);
            bool ok = report.summary.result == BuildResult.Succeeded;
            Debug.Log($"[Unmasked] {target}: {report.summary.result} -> {path} ({report.summary.totalSize / (1024 * 1024)} MB)");
            return ok;
        }

        /// <summary>The scenes are generated, so make them if this checkout doesn't have them yet.</summary>
        static void EnsureScene()
        {
            PlayerSettings.productName = "Unmasked";
            PlayerSettings.companyName = "Midnight Mystery Club";
            PlayerSettings.runInBackground = true; // so a host keeps ticking while you alt-tab
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            if (!File.Exists(Path.Combine(ProjectRoot, ManorBuilder.ScenePath))) ManorBuilder.Build();
            if (!File.Exists(Path.Combine(ProjectRoot, TownBuilder.ScenePath))) TownBuilder.Build();
        }

        static string ProjectRoot => Directory.GetParent(Application.dataPath).FullName;
    }
}
