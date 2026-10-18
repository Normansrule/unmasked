using System.Collections.Generic;
using System.IO;
using Unity.Netcode;
using Unity.Netcode.Components;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Unmasked.EditorTools
{
    /// <summary>
    /// Unmasked > Build Blackwood Manor (3D). Builds the full 3D level (cellar, two floors, roof and
    /// grounds) from Assets/Unmasked/Resources/BlackwoodManor.json, which Docs/tools/make_manor.py
    /// writes, dressed for Halloween night with the props in Costumes.json (Docs/tools/make_costumes.py):
    /// a jack-o'-lantern trail, a pumpkin patch, candles, cobwebs, mist, fireflies and bats.
    /// Edit the level in those scripts, re-run them, then run this menu again.
    /// </summary>
    public static class ManorBuilder
    {
        public const string ScenePath = "Assets/Unmasked/Scenes/BlackwoodManor.unity";
        const string JsonPath = "Assets/Unmasked/Resources/BlackwoodManor.json";

        [MenuItem("Unmasked/Build Blackwood Manor (3D)", priority = 0)]
        public static void Build()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            if (!File.Exists(JsonPath))
            {
                Debug.LogError($"[Unmasked] {JsonPath} is missing. Run: python3 Docs/tools/make_manor.py");
                return;
            }

            var layout = ManorLayout.Parse(File.ReadAllText(JsonPath));
            var prefabs = TestRoomBuilder.BuildPrefabs();
            var scene = TestRoomBuilder.NewNetworkedScene(prefabs, new Vector3(18, 14, -48));
            var root = BuildLevel(layout, "BlackwoodManor", Vector3.zero, false);
            BuildHalloween(layout, root);
            ManorAtmosphere(root);
            TestRoomBuilder.SetupNight(0.012f);
            TestRoomBuilder.SaveScene(scene, ScenePath, true);
            Debug.Log($"[Unmasked] Blackwood Manor built: {layout.boxes.Length} pieces, {layout.rooms.Length} rooms. Press Play, then Host.");
        }

        /// <summary>
        /// Builds one house (or the town's streets) from its layout under a new root placed at offset.
        /// Everything is placed in the root's local space, so the same layout works anywhere in town.
        /// suspectSpots: make empty "SuspectSpots/{id}" markers instead of the suspects themselves
        /// (in Hollow Creek the four suspects walk to whichever house the call is about).
        /// </summary>
        internal static Transform BuildLevel(ManorLayout L, string name, Vector3 offset, bool suspectSpots)
        {
            var root = new GameObject(name).transform;
            root.position = offset;
            var levels = new Dictionary<int, Transform>();
            Transform Level(int l)
            {
                if (levels.TryGetValue(l, out var t)) return t;
                t = new GameObject(l switch { -1 => "Cellar", 0 => "GroundFloor", 1 => "Upstairs", 2 => "Roof", _ => "Grounds" }).transform;
                t.SetParent(root, false);
                return levels[l] = t;
            }

            // ---- Static geometry ----
            foreach (var b in L.boxes ?? new ManorLayout.Box[0])
            {
                var go = TestRoomBuilder.Shape(Primitive(b.t), b.n, Level(b.l), ManorLayout.V(b.p), ManorLayout.V(b.s), GetMaterial(b.c, b.m, b.sf), b.m != "nocollide");
                go.transform.localRotation = Quaternion.Euler(ManorLayout.V(b.r));
                GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccluderStatic | StaticEditorFlags.OccludeeStatic);
                if (b.m == "glass") go.GetComponent<Renderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            }

            // ---- Doors ----
            var doorMat = TestRoomBuilder.Mat("Door", new Color(0.42f, 0.25f, 0.13f));
            foreach (var d in L.doors ?? new ManorLayout.Door[0])
            {
                var door = new GameObject(d.n);
                door.transform.SetParent(Level(d.l), false);
                door.transform.SetLocalPositionAndRotation(ManorLayout.V(d.p), Quaternion.Euler(0, d.ry, 0));
                door.AddComponent<NetworkObject>();
                var hinge = new GameObject("Hinge").transform;
                hinge.SetParent(door.transform, false);
                TestRoomBuilder.Shape(PrimitiveType.Cube, "Panel", hinge, new Vector3(0, d.h / 2, d.w / 2), new Vector3(0.1f, d.h, d.w), doorMat, true);
                TestRoomBuilder.Shape(PrimitiveType.Sphere, "Knob", hinge, new Vector3(0.08f, 1.05f, d.w - 0.15f), Vector3.one * 0.08f, GetMaterial(new[] { 0.7f, 0.55f, 0.24f }, "solid"), false);
                door.AddComponent<HouseDoor>().Hinge = hinge;
                if (d.n == "Door_Front")
                {
                    // A harvest wreath that swings open with the door (the hinge's +x is the outside).
                    var wreath = TestRoomBuilder.LoadCostumes()?.FindProp("wreath");
                    if (wreath != null)
                    {
                        var w = TestRoomBuilder.BuildParts(hinge, "Wreath", wreath.parts, Vector3.zero);
                        w.SetLocalPositionAndRotation(new Vector3(0.09f, 1.6f, d.w / 2), Quaternion.Euler(0, 90, 0));
                        w.localScale = Vector3.one * 0.8f;
                    }
                }
            }

            // ---- Trapdoors ----
            foreach (var t in L.trapdoors ?? new ManorLayout.Trapdoor[0])
            {
                var go = new GameObject(t.n);
                go.transform.SetParent(root, false);
                go.transform.localPosition = ManorLayout.V(t.p);
                go.AddComponent<NetworkObject>();
                var lid = new GameObject("Lid").transform;
                lid.SetParent(go.transform, false);
                lid.localPosition = new Vector3(0, 0.02f, -0.9f);
                TestRoomBuilder.Shape(PrimitiveType.Cube, "Planks", lid, new Vector3(0, 0, 0.9f), new Vector3(1.8f, 0.04f, 1.8f), TestRoomBuilder.Mat("Trapdoor", new Color(0.3f, 0.17f, 0.08f)), false);
                var drop = new GameObject(t.n + " Drop").transform;
                drop.SetParent(root, false);
                drop.localPosition = ManorLayout.V(t.drop);
                var trapdoor = go.AddComponent<Trapdoor>();
                trapdoor.Panel = lid;
                trapdoor.DropDestination = drop;
            }

            // ---- Possessables and lamps ----
            foreach (var p in L.possessables ?? new ManorLayout.Possessable[0])
                TestRoomBuilder.Possessable(Level(p.l), p.n, Primitive(p.t), ManorLayout.V(p.p), ManorLayout.V(p.s), ManorLayout.C(p.c), p.phys);

            foreach (var l in L.lights ?? new ManorLayout.LightSpec[0])
            {
                var go = new GameObject(l.n);
                go.transform.SetParent(Level(l.l), false);
                go.transform.localPosition = ManorLayout.V(l.p);
                TestRoomBuilder.Shape(Primitive(l.ft), "Fixture", go.transform, ManorLayout.V(l.fo), ManorLayout.V(l.fs), GetMaterial(l.fc, "solid"), true);
                TestRoomBuilder.Shape(PrimitiveType.Sphere, "Glow", go.transform, Vector3.zero, Vector3.one * 0.18f, GetMaterial(l.c, "emissive"), false);
                var bulb = new GameObject("Bulb").AddComponent<Light>();
                bulb.transform.SetParent(go.transform, false);
                bulb.type = LightType.Point;
                bulb.range = l.range;
                bulb.intensity = l.intensity;
                bulb.color = ManorLayout.C(l.c);
                bulb.shadows = LightShadows.None;
                go.AddComponent<NetworkObject>();
                go.AddComponent<NetworkTransform>();
                go.AddComponent<PossessableLight>().Lamp = bulb;
            }

            // ---- Suspects (or where they stand when the call is here) ----
            if (suspectSpots)
            {
                var spots = new GameObject("SuspectSpots").transform;
                spots.SetParent(root, false);
                foreach (var s in L.suspects ?? new ManorLayout.Suspect[0])
                {
                    var spot = new GameObject(s.id).transform;
                    spot.SetParent(spots, false);
                    spot.SetLocalPositionAndRotation(ManorLayout.V(s.p), Quaternion.Euler(0, s.ry, 0));
                }
            }
            else
            {
                foreach (var s in L.suspects ?? new ManorLayout.Suspect[0])
                    TestRoomBuilder.Suspect(root, s.id, ManorLayout.V(s.p), ManorLayout.C(s.c), s.ry);
            }

            // ---- Spawns and clue spots ----
            if (L.solverSpawns != null)
                for (int i = 0; i < L.solverSpawns.Length; i++)
                    TestRoomBuilder.Spawn(root, $"SolverSpawn_{i}", ManorLayout.V(L.solverSpawns[i].p), false);
            if (L.haunterSpawn?.p != null && L.haunterSpawn.p.Length >= 3)
                TestRoomBuilder.Spawn(root, "HaunterSpawn", ManorLayout.V(L.haunterSpawn.p), true);

            var clueRoot = new GameObject("ClueSpots").transform;
            clueRoot.SetParent(root, false);
            for (int i = 0; i < (L.clueSpots?.Length ?? 0); i++)
            {
                var spot = new GameObject($"ClueSpot_{i}");
                spot.transform.SetParent(clueRoot, false);
                spot.transform.localPosition = ManorLayout.V(L.clueSpots[i].p);
                spot.AddComponent<ClueSpawnPoint>();
            }

            // ---- Trap pieces and the trap site ----
            var pieceMat = TestRoomBuilder.Mat("TrapPiece", new Color(1f, 0.5f, 0.1f), emissive: true);
            for (int i = 0; i < (L.trapPieces?.Length ?? 0); i++)
            {
                var piece = TestRoomBuilder.Shape(PrimitiveType.Cube, $"TrapPiece_{i}", root, ManorLayout.V(L.trapPieces[i].p), new Vector3(0.6f, 0.5f, 0.6f), pieceMat, true);
                piece.AddComponent<NetworkObject>();
                piece.AddComponent<TrapPiece>();
            }

            if (L.trapSite?.p == null || L.trapSite.p.Length < 3) return root;
            var site = new GameObject("TrapSite");
            site.transform.SetParent(root, false);
            site.transform.localPosition = ManorLayout.V(L.trapSite.p);
            site.AddComponent<NetworkObject>();
            var trigger = site.AddComponent<BoxCollider>();
            trigger.isTrigger = true; trigger.center = new Vector3(0, 0.75f, 0); trigger.size = new Vector3(2f, 1.5f, 2f);
            TestRoomBuilder.Shape(PrimitiveType.Cylinder, "Marker", site.transform, new Vector3(0, 0.03f, 0), new Vector3(2.5f, 0.02f, 2.5f), TestRoomBuilder.Mat("TrapMarker", new Color(0.2f, 0.8f, 0.3f), emissive: true), false);
            var cage = TestRoomBuilder.Shape(PrimitiveType.Cube, "Cage", site.transform, new Vector3(0, 1.5f, 0), new Vector3(2.4f, 3f, 2.4f), TestRoomBuilder.Transparent("Cage", new Color(0.3f, 1f, 0.4f, 0.2f)), false);
            cage.SetActive(false);
            site.AddComponent<TrapSite>().ArmedVisual = cage;
            return root;
        }

        /// <summary>Jack-o'-lanterns, pumpkins, candles, cobwebs and their flickering glows, under parent.</summary>
        internal static void BuildHalloween(ManorLayout L, Transform parent)
        {
            var root = new GameObject("Halloween").transform;
            root.SetParent(parent, false);
            var props = TestRoomBuilder.LoadCostumes();
            var made = new Dictionary<string, int>();

            if (props != null && L.decor != null)
            {
                foreach (var d in L.decor)
                {
                    var prop = props.FindProp(d.k);
                    if (prop == null) continue;
                    made[d.k] = made.TryGetValue(d.k, out int n) ? n + 1 : 1;
                    var item = TestRoomBuilder.BuildParts(root, $"{d.k}_{made[d.k]}", prop.parts, Vector3.zero);
                    item.SetLocalPositionAndRotation(ManorLayout.V(d.p), Quaternion.Euler(0, d.ry, 0));
                    item.localScale = Vector3.one * (d.sc > 0f ? d.sc : 1f);
                    foreach (var r in item.GetComponentsInChildren<Renderer>())
                        GameObjectUtility.SetStaticEditorFlags(r.gameObject, StaticEditorFlags.BatchingStatic);
                }
            }

            if (L.glows != null)
                for (int i = 0; i < L.glows.Length; i++)
                {
                    var g = L.glows[i];
                    var lamp = new GameObject($"Glow_{i}").AddComponent<Light>();
                    lamp.transform.SetParent(root, false);
                    lamp.transform.localPosition = ManorLayout.V(g.p);
                    lamp.type = LightType.Point;
                    lamp.range = g.range;
                    lamp.intensity = g.intensity;
                    lamp.color = ManorLayout.C(g.c);
                    lamp.shadows = LightShadows.None;
                    var flicker = lamp.gameObject.AddComponent<CandleFlicker>();
                    flicker.Amount = 0.3f;
                    if (g.c != null && g.c.Length >= 3 && g.c[1] > g.c[0]) flicker.Bob = 0.3f; // green ones are wisps
                }

            Debug.Log($"[Unmasked] Halloween dressing for {parent.name}: {L.decor?.Length ?? 0} props, {L.glows?.Length ?? 0} glows.");
        }

        /// <summary>
        /// Blackwood Manor's atmosphere: low mist over the grounds, embers on the pumpkin trail,
        /// fireflies in the cemetery and pumpkin patch, and bats circling the roof. Positions are
        /// relative to the manor, so it works wherever the manor stands.
        /// </summary>
        internal static void ManorAtmosphere(Transform manor)
        {
            var root = new GameObject("Atmosphere").transform;
            root.SetParent(manor, false);
            SpookyLook.Mist(root, new Vector3(0, 0.4f, -2), new Vector3(86, 0.6f, 78));
            SpookyLook.Embers(root, new Vector3(0, 0.6f, -26), new Vector3(6, 0.6f, 26));
            SpookyLook.Fireflies(root, new Vector3(-33, 1.2f, -13), new Vector3(14, 2f, 22), new Color(0.65f, 1f, 0.45f));
            SpookyLook.Fireflies(root, new Vector3(30, 1.2f, -24), new Vector3(16, 2f, 16), new Color(1f, 0.8f, 0.35f));
            SpookyLook.Bats(root, new Vector3(0, 13.5f, 0), 15f, 14);
        }

        static PrimitiveType Primitive(string shape) => TestRoomBuilder.PartPrimitive(shape);

        /// <summary>One material per colour and kind, shared across the level.</summary>
        static Material GetMaterial(float[] rgb, string mode, string surface = null) => TestRoomBuilder.ColorMaterial(ManorLayout.C(rgb), mode, 1f, surface);
    }
}
