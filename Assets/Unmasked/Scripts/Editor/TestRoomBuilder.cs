using System.Collections.Generic;
using System.IO;
using System.Reflection;
using Unity.Netcode;
using Unity.Netcode.Components;
using Unity.Netcode.Transports.UTP;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace Unmasked.EditorTools
{
    /// <summary>
    /// Unmasked > Build Test Room. Generates every material, prefab and the playable test scene from
    /// code, so the prototype needs no hand-made assets. Safe to run again: it overwrites what it made.
    /// </summary>
    public static class TestRoomBuilder
    {
        internal const string Root = "Assets/Unmasked/Generated";
        const string MaterialDir = Root + "/Materials";
        const string PrefabDir = Root + "/Prefabs";
        const string ScenePath = "Assets/Unmasked/Scenes/BlackwoodManor_Test.unity";

        const string CostumesPath = "Assets/Unmasked/Resources/Costumes.json";

        static readonly Dictionary<string, Material> materials = new();
        static Costumes costumes;

        /// <summary>Everything a playable scene needs that isn't the level itself.</summary>
        internal struct Prefabs
        {
            public GameObject Agent, Solver, Haunter, Clue, Fog, Phantom, Pumpkin, Wisp;
            public NetworkPrefabsList List;
        }

        /// <summary>The characters and props (Docs/tools/make_costumes.py writes the file).</summary>
        internal static Costumes LoadCostumes()
        {
            if (costumes != null) return costumes;
            if (!File.Exists(CostumesPath))
            {
                Debug.LogWarning($"[Unmasked] {CostumesPath} is missing, so characters will be plain capsules. Run: python3 Docs/tools/make_costumes.py");
                return null;
            }
            return costumes = Costumes.Parse(File.ReadAllText(CostumesPath));
        }

        [MenuItem("Unmasked/Build Test Room (small, flat)")]
        public static void Build()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            var prefabs = BuildPrefabs();
            var scene = NewNetworkedScene(prefabs, new Vector3(0, 8, -14));
            BuildHouse();
            SetupNight(0.02f);
            SaveScene(scene, ScenePath, false);
            Debug.Log("[Unmasked] Test room built. Press Play, then Host.");
        }

        /// <summary>Generates materials and network prefabs (shared by every generated level).</summary>
        internal static Prefabs BuildPrefabs()
        {
            Directory.CreateDirectory(MaterialDir);
            Directory.CreateDirectory(PrefabDir);
            Directory.CreateDirectory("Assets/Unmasked/Scenes");
            AssetDatabase.Refresh();
            materials.Clear();
            costumes = null;
            SpookyLook.Reset();
            LoadCostumes();

            var prefabs = new Prefabs
            {
                Agent = SavePrefab(BuildPlayerAgent(), "PlayerAgent"),
                Solver = SavePrefab(BuildSolver(), "Solver"),
                Haunter = SavePrefab(BuildHaunter(), "Haunter"),
                Clue = SavePrefab(BuildClue(), "Clue"),
                Fog = SavePrefab(BuildFog(), "Fog"),
                Phantom = SavePrefab(BuildPhantom(), "Phantom"),
                Pumpkin = SavePrefab(BuildPumpkin(), "FlamingPumpkin"),
                Wisp = SavePrefab(BuildWisp(), "Wisp"),
            };

            var prefabList = ScriptableObject.CreateInstance<NetworkPrefabsList>();
            foreach (var p in new[] { prefabs.Agent, prefabs.Solver, prefabs.Haunter, prefabs.Clue, prefabs.Fog, prefabs.Phantom, prefabs.Pumpkin, prefabs.Wisp })
                prefabList.Add(new NetworkPrefab { Prefab = p });
            const string listPath = Root + "/UnmaskedNetworkPrefabs.asset";
            AssetDatabase.DeleteAsset(listPath);
            AssetDatabase.CreateAsset(prefabList, listPath);
            prefabs.List = prefabList;
            return prefabs;
        }

        /// <summary>A new scene with the NetworkManager, camera, HUD and match manager in it.</summary>
        internal static UnityEngine.SceneManagement.Scene NewNetworkedScene(Prefabs prefabs, Vector3 cameraStart)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var netGo = new GameObject("NetworkManager");
            var transport = netGo.AddComponent<UnityTransport>();
            var net = netGo.AddComponent<NetworkManager>();
            net.NetworkConfig ??= new NetworkConfig();
            net.NetworkConfig.NetworkTransport = transport;
            net.NetworkConfig.PlayerPrefab = prefabs.Agent;
            net.NetworkConfig.Prefabs.NetworkPrefabsLists.Clear();
            net.NetworkConfig.Prefabs.NetworkPrefabsLists.Add(prefabs.List);
            transport.SetConnectionData("127.0.0.1", 7777, "0.0.0.0");

            var cam = new GameObject("Main Camera") { tag = "MainCamera" };
            var camera = cam.AddComponent<Camera>();
            camera.nearClipPlane = 0.1f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.03f, 0.03f, 0.08f);
            cam.AddComponent<AudioListener>();
            cam.AddComponent<CameraRig>();
            cam.transform.position = cameraStart;
            cam.transform.LookAt(Vector3.zero);

            var hud = new GameObject("HUD");
            hud.AddComponent<GameHUD>();
            hud.AddComponent<Handbook>();

            var managerGo = new GameObject("MysteryGameManager");
            managerGo.AddComponent<NetworkObject>();
            var manager = managerGo.AddComponent<MysteryGameManager>();
            manager.SolverPrefab = prefabs.Solver;
            manager.HaunterPrefab = prefabs.Haunter;
            manager.CluePrefab = prefabs.Clue;
            manager.FogPrefab = prefabs.Fog;
            manager.PhantomPrefab = prefabs.Phantom;
            manager.PumpkinPrefab = prefabs.Pumpkin;
            manager.WispPrefab = prefabs.Wisp;
            managerGo.AddComponent<AIDirector>();
            return scene;
        }

        /// <summary>A spooky Halloween night: sky, moon, violet fog, bloom and friends (see SpookyLook).</summary>
        internal static void SetupNight(float fogDensity) => SpookyLook.Apply(fogDensity);

        /// <summary>Saves the scene, fixes network ids, and adds it to the build (first = the scene a build starts in).</summary>
        internal static void SaveScene(UnityEngine.SceneManagement.Scene scene, string path, bool first)
        {
            EditorSceneManager.SaveScene(scene, path);
            RefreshNetworkObjectIds(Object.FindObjectsByType<NetworkObject>(FindObjectsInactive.Include, FindObjectsSortMode.None));
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene, path);

            var scenes = new List<EditorBuildSettingsScene>(EditorBuildSettings.scenes);
            scenes.RemoveAll(s => s.path == path || !File.Exists(s.path));
            var entry = new EditorBuildSettingsScene(path, true);
            if (first) scenes.Insert(0, entry); else scenes.Add(entry);
            EditorBuildSettings.scenes = scenes.ToArray();
            AssetDatabase.SaveAssets();
        }

        // -------------------------------------------------------------------
        // Prefabs
        // -------------------------------------------------------------------

        static GameObject BuildPlayerAgent()
        {
            var go = new GameObject("PlayerAgent");
            go.AddComponent<NetworkObject>();
            go.AddComponent<PlayerAgent>();
            return go;
        }

        static GameObject BuildSolver()
        {
            var go = new GameObject("Solver");
            var cc = go.AddComponent<CharacterController>();
            cc.height = 1.8f; cc.radius = 0.35f; cc.center = new Vector3(0, 0.9f, 0);
            go.AddComponent<NetworkObject>();
            go.AddComponent<OwnerNetworkTransform>();
            go.AddComponent<FearMeter>();
            go.AddComponent<SolverController>();

            var model = new GameObject("Model").transform;
            model.SetParent(go.transform, false);
            var outfits = new GameObject("Outfits").transform;
            outfits.SetParent(model, false);
            foreach (SolverRole role in System.Enum.GetValues(typeof(SolverRole)))
            {
                var parts = Costumes.FindOutfit(LoadCostumes()?.solvers, role.ToString());
                var outfit = parts != null
                    ? BuildParts(outfits, role.ToString(), parts, Vector3.zero)
                    : Shape(PrimitiveType.Capsule, role.ToString(), outfits, new Vector3(0, 0.9f, 0), new Vector3(0.7f, 0.9f, 0.7f), Mat("Solver", new Color(0.2f, 0.6f, 0.3f)), false).transform;
                // The Lantern Watch pieces, fitted to this role's height and build; WatchCostume shows them.
                foreach (var piece in new[] { "Sash", "Charm", "Bell", "Lantern", "Badge" })
                {
                    var watch = Costumes.FindOutfit(LoadCostumes()?.watch, $"{role}.{piece}");
                    if (watch != null) BuildParts(outfit, "Watch_" + piece, watch, Vector3.zero).gameObject.SetActive(false);
                }
                outfit.gameObject.SetActive(role == SolverRole.Sleuth);
            }
            go.AddComponent<RoleOutfit>().Outfits = outfits;
            go.AddComponent<WatchCostume>();
            var anim = go.AddComponent<PawnAnimator>();
            anim.Kind = PawnAnimator.Style.Solver;
            anim.Body = model;

            var lightGo = new GameObject("Flashlight");
            lightGo.transform.SetParent(go.transform, false);
            lightGo.transform.localPosition = new Vector3(0.3f, 1.35f, 0.25f);
            var spot = lightGo.AddComponent<Light>();
            spot.type = LightType.Spot;
            spot.range = 16f; spot.spotAngle = 40f; spot.intensity = 4f;
            spot.color = new Color(1f, 0.95f, 0.8f);
            spot.shadows = LightShadows.Hard;
            spot.enabled = false;
            lightGo.AddComponent<Flashlight>();
            return go;
        }

        static GameObject BuildHaunter()
        {
            var go = new GameObject("Haunter");
            var cc = go.AddComponent<CharacterController>();
            cc.height = 1.8f; cc.radius = 0.35f; cc.center = new Vector3(0, 0.9f, 0);
            go.AddComponent<NetworkObject>();
            go.AddComponent<OwnerNetworkTransform>();
            go.AddComponent<Ectoplasm>();
            go.AddComponent<HaunterPowers>();
            var haunter = go.AddComponent<HaunterController>();

            var ghost = Shape(PrimitiveType.Sphere, "GhostVisual", go.transform, new Vector3(0, 1f, 0), Vector3.one * 0.8f, Transparent("Ghost", new Color(0.6f, 0.9f, 1f, 0.35f)), false);
            var costume = new GameObject("CostumeVisual");
            costume.transform.SetParent(go.transform, false);

            // One costume per legend; HaunterController shows tonight's.
            Transform firstMask = null;
            foreach (VillainKind kind in System.Enum.GetValues(typeof(VillainKind)))
            {
                var villain = Costumes.For(kind) ?? FindVillain(kind);
                Transform variant;
                if (villain != null)
                {
                    variant = BuildParts(costume.transform, kind.ToString(), villain.parts, ManorLayout.V(villain.mask));
                    variant.localPosition = Vector3.up * villain.hover;
                }
                else
                {
                    variant = new GameObject(kind.ToString()).transform;
                    variant.SetParent(costume.transform, false);
                    Shape(PrimitiveType.Capsule, "Cloak", variant, new Vector3(0, 0.95f, 0), new Vector3(0.8f, 0.95f, 0.8f), Mat("Cloak", new Color(0.18f, 0.05f, 0.25f)), false);
                    var plain = new GameObject("Mask").transform;
                    plain.SetParent(variant, false);
                    plain.localPosition = new Vector3(0, 1.6f, 0.33f);
                    Shape(PrimitiveType.Cube, "Face", plain, Vector3.zero, new Vector3(0.4f, 0.45f, 0.08f), Mat("Mask", new Color(0.9f, 0.9f, 0.8f)), false);
                }
                variant.gameObject.SetActive(kind == VillainKind.HeadlessHorseman);
                if (firstMask == null) firstMask = variant.Find("Mask");
            }

            var glowLight = new GameObject("CostumeGlow").AddComponent<Light>();
            glowLight.transform.SetParent(costume.transform, false);
            glowLight.transform.localPosition = new Vector3(0, 1.8f, 0.4f);
            glowLight.type = LightType.Point;
            glowLight.range = 6f;
            glowLight.intensity = 1.8f;
            glowLight.color = new Color(1f, 0.45f, 0.1f);
            glowLight.gameObject.AddComponent<CandleFlicker>();
            costume.SetActive(false);
            ghost.SetActive(false);

            haunter.GhostVisual = ghost;
            haunter.CostumeVisual = costume;
            haunter.CostumeGlow = glowLight;
            var anim = go.AddComponent<PawnAnimator>();
            anim.Kind = PawnAnimator.Style.Haunter;
            anim.Body = costume.transform;
            anim.Ghost = ghost.transform;
            anim.Mask = firstMask;
            return go;
        }

        static GameObject BuildClue()
        {
            var go = Shape(PrimitiveType.Cube, "Clue", null, Vector3.zero, Vector3.one * 0.3f, Mat("Clue", new Color(1f, 0.85f, 0.2f), emissive: true), true);
            go.GetComponent<Collider>().isTrigger = true;
            go.AddComponent<NetworkObject>();
            go.AddComponent<ClueItem>();
            var glow = new GameObject("Glow").AddComponent<Light>();
            glow.transform.SetParent(go.transform, false);
            glow.type = LightType.Point; glow.range = 2.5f; glow.intensity = 1.5f; glow.color = new Color(1f, 0.85f, 0.3f);
            return go;
        }

        static GameObject BuildFog()
        {
            var go = Shape(PrimitiveType.Sphere, "Fog", null, Vector3.zero, Vector3.one, Transparent("Fog", new Color(0.7f, 0.75f, 0.8f, 0.25f)), false);
            go.AddComponent<NetworkObject>();
            go.AddComponent<FogCloud>();
            return go;
        }

        static GameObject BuildPhantom()
        {
            var go = new GameObject("Phantom");
            go.AddComponent<NetworkObject>();
            go.AddComponent<NetworkTransform>();
            go.AddComponent<PhantomIllusion>();
            Shape(PrimitiveType.Capsule, "Sheet", go.transform, Vector3.zero, new Vector3(0.9f, 0.8f, 0.9f), Transparent("Phantom", new Color(1f, 1f, 1f, 0.6f)), false);
            Shape(PrimitiveType.Sphere, "EyeL", go.transform, new Vector3(-0.15f, 0.4f, 0.4f), Vector3.one * 0.12f, Mat("Dark", Color.black), false);
            Shape(PrimitiveType.Sphere, "EyeR", go.transform, new Vector3(0.15f, 0.4f, 0.4f), Vector3.one * 0.12f, Mat("Dark", Color.black), false);
            return go;
        }

        static Costumes.Villain FindVillain(VillainKind kind)
        {
            var all = LoadCostumes()?.villains;
            if (all != null) foreach (var v in all) if (v.id == kind.ToString()) return v;
            return null;
        }

        /// <summary>The Headless Horseman's flaming jack-o'-lantern (key 6 / Q as the Horseman).</summary>
        static GameObject BuildPumpkin()
        {
            var go = new GameObject("FlamingPumpkin");
            go.AddComponent<NetworkObject>();
            go.AddComponent<NetworkTransform>();
            go.AddComponent<PumpkinProjectile>();
            var jack = LoadCostumes()?.FindProp("jack");
            if (jack != null) BuildParts(go.transform, "Jack", jack.parts, Vector3.zero).localPosition = new Vector3(0, -0.25f, 0);
            else Shape(PrimitiveType.Sphere, "Jack", go.transform, Vector3.zero, Vector3.one * 0.6f, ColorMaterial(new Color(0.9f, 0.45f, 0.1f), "emissive"), false);
            var light = new GameObject("Glow").AddComponent<Light>();
            light.transform.SetParent(go.transform, false);
            light.type = LightType.Point; light.range = 6f; light.intensity = 2.2f; light.color = new Color(1f, 0.5f, 0.15f);
            light.gameObject.AddComponent<CandleFlicker>().Amount = 0.4f;
            SpookyLook.Field("Flames", go.transform, Vector3.zero, Vector3.one * 0.4f, true, new Color(1f, 0.5f, 0.1f), new Color(1f, 0.85f, 0.3f), 60f,
                new Vector2(0.3f, 0.6f), new Vector2(0.08f, 0.2f), new Vector2(0.2f, 0.6f), 1.5f, 120, 0.3f);
            return go;
        }

        /// <summary>Stingy Jack's will-o'-the-wisp: a phantom that glows. Flashlights pop it.</summary>
        static GameObject BuildWisp()
        {
            var go = new GameObject("Wisp");
            go.AddComponent<NetworkObject>();
            go.AddComponent<NetworkTransform>();
            var phantom = go.AddComponent<PhantomIllusion>();
            phantom.FloatSpeed = 1.9f;
            phantom.DispelTime = 0.4f;
            phantom.PopDistance = 1f;
            var green = new Color(0.62f, 1f, 0.54f);
            Shape(PrimitiveType.Sphere, "Core", go.transform, Vector3.zero, Vector3.one * 0.22f, ColorMaterial(green, "emissive", 3f), false);
            Shape(PrimitiveType.Sphere, "Halo", go.transform, Vector3.zero, Vector3.one * 0.5f, ColorMaterial(green, "ghost", 1f), false);
            var light = new GameObject("Glow").AddComponent<Light>();
            light.transform.SetParent(go.transform, false);
            light.type = LightType.Point; light.range = 4.5f; light.intensity = 1.6f; light.color = green;
            light.gameObject.AddComponent<CandleFlicker>().Amount = 0.35f;
            SpookyLook.Field("Sparks", go.transform, Vector3.zero, Vector3.one * 0.3f, true, green, Color.white, 25f,
                new Vector2(0.6f, 1.2f), new Vector2(0.03f, 0.07f), new Vector2(0.1f, 0.3f), 0.3f, 60, 0.4f);
            return go;
        }

        static GameObject SavePrefab(GameObject go, string name)
        {
            string path = $"{PrefabDir}/{name}.prefab";
            var prefab = PrefabUtility.SaveAsPrefabAsset(go, path);
            Object.DestroyImmediate(go);
            RefreshNetworkObjectIds(new[] { prefab.GetComponent<NetworkObject>() });
            EditorUtility.SetDirty(prefab);
            return prefab;
        }

        // -------------------------------------------------------------------
        // The house
        // -------------------------------------------------------------------

        static void BuildHouse()
        {
            var house = new GameObject("BlackwoodManor").transform;
            var floorMat = Mat("Floor", new Color(0.25f, 0.18f, 0.12f));
            var wallMat = Mat("Wall", new Color(0.3f, 0.27f, 0.32f));

            // Floor and outer walls (30 x 30).
            Shape(PrimitiveType.Cube, "Floor", house, new Vector3(0, -0.1f, 0), new Vector3(30, 0.2f, 30), floorMat, true);
            Shape(PrimitiveType.Cube, "Wall_N", house, new Vector3(0, 2, 15), new Vector3(30, 4, 0.3f), wallMat, true);
            Shape(PrimitiveType.Cube, "Wall_S", house, new Vector3(0, 2, -15), new Vector3(30, 4, 0.3f), wallMat, true);
            Shape(PrimitiveType.Cube, "Wall_E", house, new Vector3(15, 2, 0), new Vector3(0.3f, 4, 30), wallMat, true);
            Shape(PrimitiveType.Cube, "Wall_W", house, new Vector3(-15, 2, 0), new Vector3(0.3f, 4, 30), wallMat, true);

            // Middle wall splitting the house into a west and east wing, with a door in the gap.
            Shape(PrimitiveType.Cube, "Wall_Mid_S", house, new Vector3(0, 2, -7.875f), new Vector3(0.3f, 4, 14.25f), wallMat, true);
            Shape(PrimitiveType.Cube, "Wall_Mid_N", house, new Vector3(0, 2, 7.875f), new Vector3(0.3f, 4, 14.25f), wallMat, true);
            // A second partition in the east wing with a gap, so there are corners to hide in.
            Shape(PrimitiveType.Cube, "Wall_East_Room", house, new Vector3(9, 2, -4), new Vector3(12, 4, 0.3f), wallMat, true);

            var door = new GameObject("Door");
            door.transform.SetParent(house, false);
            door.transform.localPosition = new Vector3(0, 0, -0.75f);
            door.AddComponent<NetworkObject>();
            var hinge = new GameObject("Hinge").transform;
            hinge.SetParent(door.transform, false);
            Shape(PrimitiveType.Cube, "Panel", hinge, new Vector3(0, 1.1f, 0.75f), new Vector3(0.1f, 2.2f, 1.5f), Mat("Door", new Color(0.35f, 0.2f, 0.1f)), true);
            door.AddComponent<HouseDoor>().Hinge = hinge;

            // Cellar corner (where the trapdoor drops you) and the trapdoor itself.
            Shape(PrimitiveType.Cube, "CellarFloor", house, new Vector3(-12, 0.01f, -12), new Vector3(5, 0.02f, 5), Mat("Cellar", new Color(0.08f, 0.08f, 0.08f)), false);
            var cellar = new GameObject("CellarDrop").transform;
            cellar.SetParent(house, false);
            cellar.localPosition = new Vector3(-12, 0.2f, -12);

            var trapdoorGo = new GameObject("Trapdoor");
            trapdoorGo.transform.SetParent(house, false);
            trapdoorGo.transform.localPosition = new Vector3(7, 0, 7);
            trapdoorGo.AddComponent<NetworkObject>();
            var lid = new GameObject("Lid").transform;
            lid.SetParent(trapdoorGo.transform, false);
            lid.localPosition = new Vector3(0, 0.02f, -0.9f);
            Shape(PrimitiveType.Cube, "Planks", lid, new Vector3(0, 0, 0.9f), new Vector3(1.8f, 0.04f, 1.8f), Mat("Trapdoor", new Color(0.3f, 0.17f, 0.08f)), false);
            var trapdoor = trapdoorGo.AddComponent<Trapdoor>();
            trapdoor.Panel = lid;
            trapdoor.DropDestination = cellar;

            // Things to possess.
            Possessable(house, "Armchair", PrimitiveType.Cube, new Vector3(-8, 0.5f, 4), new Vector3(1, 1, 1), new Color(0.5f, 0.1f, 0.1f), true);
            Possessable(house, "Vase", PrimitiveType.Cylinder, new Vector3(-4, 0.4f, -6), new Vector3(0.4f, 0.4f, 0.4f), new Color(0.3f, 0.4f, 0.7f), true);
            Possessable(house, "Suit of Armor", PrimitiveType.Capsule, new Vector3(4, 1f, 12), new Vector3(0.7f, 1f, 0.7f), new Color(0.6f, 0.6f, 0.65f), false);
            Possessable(house, "Grandfather Clock", PrimitiveType.Cube, new Vector3(13.5f, 1.2f, -10), new Vector3(0.8f, 2.4f, 0.6f), new Color(0.25f, 0.15f, 0.05f), false);
            Possessable(house, "Bookcase", PrimitiveType.Cube, new Vector3(-14, 1.25f, 8), new Vector3(0.6f, 2.5f, 3f), new Color(0.3f, 0.2f, 0.1f), false);
            Lamp(house, "Lamp_West", new Vector3(-9, 0, -2));
            Lamp(house, "Lamp_East", new Vector3(9, 0, 3));

            // Suspects.
            Suspect(house, "Groundskeeper", new Vector3(-11, 0, 12), new Color(0.35f, 0.45f, 0.2f));
            Suspect(house, "Heiress", new Vector3(-3, 0, 10), new Color(0.7f, 0.3f, 0.6f));
            Suspect(house, "Rival", new Vector3(11, 0, -12), new Color(0.2f, 0.25f, 0.4f));
            Suspect(house, "Cook", new Vector3(12, 0, 10), new Color(0.9f, 0.9f, 0.85f));

            // Spawns.
            for (int i = 0; i < 4; i++) Spawn(house, $"SolverSpawn_{i}", new Vector3(-6 + i * 1.5f, 0.1f, -12), false);
            Spawn(house, "HaunterSpawn", new Vector3(10, 1f, 0), true);

            // Clue hiding spots.
            Vector3[] cluePoints =
            {
                new(-13, 0.2f, -2), new(-6, 0.2f, 13), new(-1.5f, 0.2f, -13), new(-10, 0.2f, -8),
                new(3, 0.2f, 3), new(13, 0.2f, 13), new(6, 0.2f, -13), new(13, 0.2f, -2),
                new(2, 0.2f, -6), new(-7, 0.2f, 7)
            };
            for (int i = 0; i < cluePoints.Length; i++)
            {
                var p = new GameObject($"ClueSpot_{i}");
                p.transform.SetParent(house, false);
                p.transform.localPosition = cluePoints[i];
                p.AddComponent<ClueSpawnPoint>();
            }

            // Trap pieces (hidden until the Trap phase) and the trap site.
            Vector3[] piecePoints = { new(-12, 0.25f, 0), new(12, 0.25f, 6), new(-2, 0.25f, 12), new(5, 0.25f, -10) };
            for (int i = 0; i < piecePoints.Length; i++)
            {
                var piece = Shape(PrimitiveType.Cube, $"TrapPiece_{i}", house, piecePoints[i], new Vector3(0.6f, 0.5f, 0.6f), Mat("TrapPiece", new Color(1f, 0.5f, 0.1f), emissive: true), true);
                piece.AddComponent<NetworkObject>();
                piece.AddComponent<TrapPiece>();
            }

            var site = new GameObject("TrapSite");
            site.transform.SetParent(house, false);
            site.transform.localPosition = new Vector3(-6, 0, 0);
            site.AddComponent<NetworkObject>();
            var trigger = site.AddComponent<BoxCollider>();
            trigger.isTrigger = true; trigger.center = new Vector3(0, 0.75f, 0); trigger.size = new Vector3(2f, 1.5f, 2f);
            Shape(PrimitiveType.Cylinder, "Marker", site.transform, new Vector3(0, 0.02f, 0), new Vector3(2.5f, 0.02f, 2.5f), Mat("TrapMarker", new Color(0.2f, 0.8f, 0.3f), emissive: true), false);
            var armed = Shape(PrimitiveType.Cube, "Cage", site.transform, new Vector3(0, 1.5f, 0), new Vector3(2.4f, 3f, 2.4f), Transparent("Cage", new Color(0.3f, 1f, 0.4f, 0.2f)), false);
            armed.SetActive(false);
            site.AddComponent<TrapSite>().ArmedVisual = armed;
        }

        internal static void Possessable(Transform parent, string name, PrimitiveType shape, Vector3 position, Vector3 size, Color color, bool physics)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = position;
            Shape(shape, "Visual", go.transform, Vector3.zero, size, Mat(name, color), true);
            go.AddComponent<NetworkObject>();
            go.AddComponent<NetworkTransform>();
            if (physics)
            {
                var rb = go.AddComponent<Rigidbody>();
                rb.mass = 8f;
                go.AddComponent<NetworkRigidbody>();
            }
            go.AddComponent<PossessableObject>();
        }

        internal static void Lamp(Transform parent, string name, Vector3 position)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = position;
            Shape(PrimitiveType.Cylinder, "Post", go.transform, new Vector3(0, 0.8f, 0), new Vector3(0.25f, 0.8f, 0.25f), Mat("LampPost", new Color(0.15f, 0.15f, 0.15f)), true);
            var bulb = new GameObject("Bulb").AddComponent<Light>();
            bulb.transform.SetParent(go.transform, false);
            bulb.transform.localPosition = new Vector3(0, 1.8f, 0);
            bulb.type = LightType.Point; bulb.range = 9f; bulb.intensity = 1.6f; bulb.color = new Color(1f, 0.75f, 0.45f);
            go.AddComponent<NetworkObject>();
            go.AddComponent<NetworkTransform>();
            var lamp = go.AddComponent<PossessableLight>();
            lamp.Lamp = bulb;
        }

        /// <param name="everyHouse">
        /// Hollow Creek: also build the outfit this suspect slot wears at every other house (hidden);
        /// SuspectNPC shows the one for tonight's call.
        /// </param>
        internal static void Suspect(Transform parent, string id, Vector3 position, Color color, float facing = 180f, bool everyHouse = false)
        {
            var go = new GameObject("Suspect_" + id);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = position;
            go.transform.localRotation = Quaternion.Euler(0, facing, 0);
            var collider = go.AddComponent<CapsuleCollider>();
            collider.center = new Vector3(0, 1f, 0); collider.height = 2f; collider.radius = 0.4f;
            var outfits = LoadCostumes()?.suspects;
            var parts = Costumes.FindOutfit(outfits, id);
            Transform body;
            if (parts != null)
            {
                body = new GameObject("Model").transform;
                body.SetParent(go.transform, false);
                BuildParts(body, SuspectNPC.OutfitPrefix + Cases.DefaultHouse, parts, Vector3.zero);
                if (everyHouse)
                    foreach (var spec in Cases.All)
                    {
                        if (spec.IsReturnVisit) continue; // same neighbours, same outfits
                        var other = spec.HouseId == Cases.DefaultHouse ? null : Costumes.FindOutfit(outfits, spec.HouseId + "." + id);
                        if (other != null) BuildParts(body, SuspectNPC.OutfitPrefix + spec.HouseId, other, Vector3.zero).gameObject.SetActive(false);
                    }
            }
            else body = Shape(PrimitiveType.Capsule, "Body", go.transform, new Vector3(0, 1f, 0), new Vector3(0.8f, 1f, 0.8f), Mat("Suspect_" + id, color), false).transform;
            var anim = go.AddComponent<PawnAnimator>();
            anim.Kind = PawnAnimator.Style.Suspect;
            anim.Body = body;
            var label = new GameObject("Name").AddComponent<TextMesh>();
            label.transform.SetParent(go.transform, false);
            label.transform.localPosition = new Vector3(0, 2.4f, 0);
            label.text = id;
            label.anchor = TextAnchor.MiddleCenter;
            label.alignment = TextAlignment.Center;
            label.characterSize = 0.08f;
            label.fontSize = 48;
            var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            if (font != null)
            {
                label.font = font;
                label.GetComponent<MeshRenderer>().sharedMaterial = font.material;
            }
            go.AddComponent<NetworkObject>();
            go.AddComponent<NetworkTransform>(); // the server walks them around and over to tonight's house
            var npc = go.AddComponent<SuspectNPC>();
            npc.SuspectId = id;
            npc.NameLabel = label;
        }

        internal static void Spawn(Transform parent, string name, Vector3 position, bool haunter)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = position;
            go.AddComponent<SpawnPoint>().HaunterSpawn = haunter;
        }

        // -------------------------------------------------------------------
        // Helpers
        // -------------------------------------------------------------------

        internal static GameObject Shape(PrimitiveType type, string name, Transform parent, Vector3 localPosition, Vector3 scale, Material material, bool keepCollider)
        {
            var go = GameObject.CreatePrimitive(type);
            go.name = name;
            if (parent != null) go.transform.SetParent(parent, false);
            go.transform.localPosition = localPosition;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = material;
            if (!keepCollider) Object.DestroyImmediate(go.GetComponent<Collider>());
            return go;
        }

        /// <summary>
        /// Builds a character or prop from Costumes.json parts under parent. Parts marked as the mask go
        /// under a "Mask" child placed at maskPivot, so the unmasking can pull them all off together.
        /// </summary>
        internal static Transform BuildParts(Transform parent, string name, Costumes.Part[] parts, Vector3 maskPivot)
        {
            var root = new GameObject(name).transform;
            root.SetParent(parent, false);
            Transform mask = null;
            foreach (var q in parts)
            {
                var into = root;
                Vector3 p = ManorLayout.V(q.p);
                if (q.k == "mask")
                {
                    if (mask == null)
                    {
                        mask = new GameObject("Mask").transform;
                        mask.SetParent(root, false);
                        mask.localPosition = maskPivot;
                    }
                    into = mask;
                    p -= maskPivot;
                }
                var go = Shape(PartPrimitive(q.t), q.n, into, p, ManorLayout.V(q.s), ColorMaterial(ManorLayout.C(q.c), q.m, q.e), false);
                go.transform.localRotation = Quaternion.Euler(ManorLayout.V(q.r));
                if (q.m == "ghost") go.GetComponent<Renderer>().shadowCastingMode = ShadowCastingMode.Off;
            }
            return root;
        }

        internal static PrimitiveType PartPrimitive(string shape) => shape switch
        {
            "cyl" => PrimitiveType.Cylinder,
            "capsule" => PrimitiveType.Capsule,
            "sphere" => PrimitiveType.Sphere,
            _ => PrimitiveType.Cube
        };

        /// <summary>
        /// One shared material per colour and kind: solid (toon), emissive (glows: strength times the
        /// colour), ghost (see-through and glowing), glass (see-through windows).
        /// </summary>
        internal static Material ColorMaterial(Color color, string mode, float strength = 1f, string surface = null)
        {
            bool patterned = !string.IsNullOrEmpty(surface) && (mode == "solid" || mode == "nocollide");
            string key = $"C_{ColorUtility.ToHtmlStringRGB(color)}_{mode}{(mode == "emissive" || mode == "ghost" ? $"_{strength:0.0}" : "")}{(patterned ? "_" + surface : "")}";
            if (materials.TryGetValue(key, out var cached)) return cached;
            Material mat;
            switch (mode)
            {
                case "glass":
                    mat = Transparent(key, new Color(color.r, color.g, color.b, 0.55f));
                    mat.EnableKeyword("_EMISSION");
                    mat.SetColor("_EmissionColor", color * 0.7f);
                    break;
                case "ghost":
                    mat = Transparent(key, new Color(color.r, color.g, color.b, 0.45f));
                    mat.EnableKeyword("_EMISSION");
                    mat.SetColor("_EmissionColor", color * 0.5f * strength);
                    break;
                case "emissive":
                    mat = Mat(key, color, emissive: true);
                    mat.SetColor("_EmissionColor", color * strength);
                    break;
                default:
                    mat = Mat(key, color);
                    if (patterned) Surfaces.Apply(mat, surface);
                    break;
            }
            EditorUtility.SetDirty(mat);
            return materials[key] = mat;
        }

        /// <summary>Everything opaque uses the cel-shaded Unmasked/ToonSpooky shader (Standard if it's missing).</summary>
        internal static Material Mat(string name, Color color, bool emissive = false)
        {
            if (materials.TryGetValue(name, out var cached)) return cached;
            var mat = new Material(Shader.Find("Unmasked/ToonSpooky") ?? Shader.Find("Standard")) { color = color };
            if (emissive)
            {
                mat.EnableKeyword("_EMISSION");
                mat.SetColor("_EmissionColor", color * 0.8f);
            }
            return SaveMaterial(name, mat);
        }

        internal static Material Transparent(string name, Color color)
        {
            if (materials.TryGetValue(name, out var cached)) return cached;
            var mat = new Material(Shader.Find("Standard")) { color = color };
            mat.SetFloat("_Mode", 2f); // Fade
            mat.SetOverrideTag("RenderType", "Transparent");
            mat.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha);
            mat.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha);
            mat.SetInt("_ZWrite", 0);
            mat.DisableKeyword("_ALPHATEST_ON");
            mat.EnableKeyword("_ALPHABLEND_ON");
            mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            mat.renderQueue = (int)RenderQueue.Transparent;
            return SaveMaterial(name, mat);
        }

        static Material SaveMaterial(string name, Material mat)
        {
            string path = $"{MaterialDir}/{name.Replace(' ', '_')}.mat";
            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(mat, path);
            materials[name] = mat;
            return mat;
        }

        /// <summary>
        /// Netcode needs a stable GlobalObjectIdHash on every NetworkObject. It normally fills this in
        /// from the inspector; objects made from code get it by re-running that validation after save.
        /// </summary>
        internal static void RefreshNetworkObjectIds(IEnumerable<NetworkObject> objects)
        {
            var validate = typeof(NetworkObject).GetMethod("OnValidate", BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);
            foreach (var obj in objects)
            {
                if (obj == null) continue;
                try { validate?.Invoke(obj, null); }
                catch (System.Exception e) { Debug.LogWarning($"[Unmasked] Could not refresh the network id on {obj.name}: {e.Message}"); }
                EditorUtility.SetDirty(obj);
            }
        }
    }
}
