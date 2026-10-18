using System.IO;
using Unity.Netcode;
using Unity.Netcode.Components;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Unmasked.EditorTools
{
    /// <summary>
    /// Unmasked > Build Hollow Creek (town). Builds the whole semi-open town from
    /// Assets/Unmasked/Resources/HollowCreek.json (Docs/tools/make_town.py): Main Street, the shops,
    /// the square, the creek and bridge, Mystery Club HQ with the van, and every haunted house fully
    /// built on its lot (Resources/Houses/*.json from make_houses.py, plus Blackwood Manor).
    ///
    /// A night here starts at HQ: pick a call, drive the van to the house, solve it. Each house is a
    /// HouseSite, so only the house tonight's call is about gets clues, trap pieces and the Haunter.
    /// </summary>
    public static class TownBuilder
    {
        public const string ScenePath = "Assets/Unmasked/Scenes/HollowCreek.unity";
        const string JsonPath = "Assets/Unmasked/Resources/HollowCreek.json";

        static readonly (string id, Vector3 pos, float ry)[] WaitingSuspects =
        {
            ("Groundskeeper", new Vector3(-35.5f, 0f, -18.5f), 90f),
            ("Heiress", new Vector3(-10.5f, 0f, -24.5f), -90f),
            ("Rival", new Vector3(-21.5f, 0f, -31.5f), 0f),
            ("Cook", new Vector3(-24.5f, 0f, -31.5f), 0f),
        };

        [MenuItem("Unmasked/Build Hollow Creek (town)", priority = -10)]
        public static void Build()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            if (!File.Exists(JsonPath))
            {
                Debug.LogError($"[Unmasked] {JsonPath} is missing. Run: python3 Docs/tools/make_houses.py && python3 Docs/tools/make_town.py");
                return;
            }

            string json = File.ReadAllText(JsonPath);
            var streets = ManorLayout.Parse(json);
            var town = TownLayout.Parse(json);
            var prefabs = TestRoomBuilder.BuildPrefabs();
            var scene = TestRoomBuilder.NewNetworkedScene(prefabs, new Vector3(-6, 12, -100));

            // ---- Streets, shops, the square, the creek and Mystery Club HQ ----
            var streetsRoot = ManorBuilder.BuildLevel(streets, "HollowCreek", Vector3.zero, true);
            ManorBuilder.BuildHalloween(streets, streetsRoot);
            BuildHQ(town);

            // ---- Every haunted house on its lot ----
            int houses = 0;
            foreach (var lot in town.lots)
            {
                string path = $"Assets/Unmasked/Resources/{lot.resource}.json";
                if (!File.Exists(path))
                {
                    Debug.LogWarning($"[Unmasked] {path} is missing, so {lot.name} was skipped. Run Docs/tools/make_houses.py and make_manor.py.");
                    continue;
                }
                var layout = ManorLayout.Parse(File.ReadAllText(path));
                var root = ManorBuilder.BuildLevel(layout, lot.id, lot.Offset, true);
                ManorBuilder.BuildHalloween(layout, root);
                if (lot.id == "BlackwoodManor") ManorBuilder.ManorAtmosphere(root);

                var site = root.gameObject.AddComponent<HouseSite>();
                site.HouseId = lot.id;
                site.DisplayName = lot.name;
                site.LotMin = lot.Min;
                site.LotMax = lot.Max;
                var arrival = new GameObject("VanArrival").transform;
                arrival.SetParent(root, false);
                arrival.SetPositionAndRotation(lot.Arrival, Quaternion.identity);
                site.Arrival = arrival;
                var spots = root.Find("SuspectSpots");
                if (spots != null)
                {
                    site.SuspectSpots = new Transform[spots.childCount];
                    for (int i = 0; i < spots.childCount; i++) site.SuspectSpots[i] = spots.GetChild(i);
                }
                BuildAfterglow(lot);
                houses++;
            }

            // ---- The suspects wait in the town square until a call comes in ----
            var suspects = new GameObject("Suspects").transform;
            foreach (var (id, pos, ry) in WaitingSuspects)
            {
                TestRoomBuilder.Suspect(suspects, id, pos, Color.gray, ry, everyHouse: true);
            }

            BuildVan(town.hq.van);
            BuildFolk(town);

            // ---- Town systems ----
            new GameObject("TownDirector").AddComponent<TownDirector>();
            new GameObject("TownMap").AddComponent<TownMap>();
            new GameObject("NightEvents").AddComponent<NightEventFX>();

            // ---- Atmosphere: mist along Main Street, fireflies in the churchyard and over the creek, bats round the steeple ----
            var air = new GameObject("TownAtmosphere").transform;
            SpookyLook.Mist(air, new Vector3(0, 0.4f, 60), new Vector3(60, 0.6f, 300));
            SpookyLook.Fireflies(air, new Vector3(-35, 1.2f, 90), new Vector3(16, 2f, 14), new Color(0.65f, 1f, 0.45f));
            SpookyLook.Fireflies(air, new Vector3(0, 1.0f, town.creekZ), new Vector3(120, 1.5f, 10), new Color(0.7f, 1f, 0.6f));
            SpookyLook.Bats(air, new Vector3(-15, 20f, 68), 9f, 8);

            TestRoomBuilder.SetupNight(0.008f);
            TestRoomBuilder.SaveScene(scene, ScenePath, true);
            Debug.Log($"[Unmasked] Hollow Creek built: {streets.boxes.Length} town pieces and {houses} haunted houses. Press Play, then Host.");
        }

        static void BuildHQ(TownLayout town)
        {
            var hq = new GameObject("MysteryClubHQ");
            var site = hq.AddComponent<HouseSite>();
            site.HouseId = HouseSite.HqId;
            site.DisplayName = "Mystery Club HQ";
            Vector2 min = new(float.MaxValue, float.MaxValue), max = new(float.MinValue, float.MinValue);
            foreach (var room in town.rooms)
            {
                if (room.n != "Mystery Club HQ" && room.n != "HQ Parking") continue;
                min = Vector2.Min(min, new Vector2(room.min[0], room.min[2]));
                max = Vector2.Max(max, new Vector2(room.max[0], room.max[2]));
            }
            site.LotMin = min;
            site.LotMax = max;
            for (int i = 0; i < town.hq.spawns.Length; i++)
                TestRoomBuilder.Spawn(hq.transform, $"SolverSpawn_{i}", ManorLayout.V(town.hq.spawns[i].p), false);
            TestRoomBuilder.Spawn(hq.transform, "HaunterSpawn", ManorLayout.V(town.hq.haunter.p), true);
            if (town.hq.keepsakes != null)
                foreach (var k in town.hq.keepsakes) BuildKeepsake(hq.transform, k);
            if (town.hq.trunk != null && town.hq.trunk.p != null) BuildTrunk(hq.transform, town.hq.trunk);
        }

        /// <summary>The dressing-up trunk at HQ, where the club puts the Lantern Watch costume on.</summary>
        static void BuildTrunk(Transform parent, TownLayout.Placed spot)
        {
            var go = new GameObject("CostumeTrunk");
            go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(ManorLayout.V(spot.p), Quaternion.Euler(0, spot.ry, 0));
            var box = go.AddComponent<BoxCollider>();
            box.center = new Vector3(0, 0.4f, 0);
            box.size = new Vector3(1.2f, 0.8f, 0.7f);
            var prop = TestRoomBuilder.LoadCostumes()?.FindProp("trunk");
            if (prop != null) TestRoomBuilder.BuildParts(go.transform, "Model", prop.parts, Vector3.zero);
            Horizon.MakeText(go.transform, "LANTERN WATCH", new Vector3(0, 0.36f, 0.32f), 0.012f, new Color(0.3f, 0.18f, 0.1f));
            go.AddComponent<NetworkObject>();
            go.AddComponent<CostumeTrunk>();
        }

        /// <summary>
        /// The street remembers: the front-yard party that appears once a house's case is solved, and the
        /// violet light over the yard while its call is open (HouseMood).
        /// </summary>
        static void BuildAfterglow(TownLayout.Lot lot)
        {
            var a = lot.afterglow;
            if (a == null) return;
            var props = TestRoomBuilder.LoadCostumes();
            var moodGo = new GameObject("StreetRemembers_" + lot.id); // at the origin: the afterglow data is in town coordinates
            var party = new GameObject("Afterglow").transform;
            party.SetParent(moodGo.transform, false);
            int n = 0;
            if (a.items != null)
                foreach (var item in a.items)
                {
                    var prop = props?.FindProp(item.k);
                    if (prop == null) continue;
                    var t = TestRoomBuilder.BuildParts(party, $"{item.k}_{++n}", prop.parts, Vector3.zero);
                    t.SetPositionAndRotation(ManorLayout.V(item.p), Quaternion.Euler(0, item.ry, 0));
                    t.localScale = Vector3.one * (item.sc > 0f ? item.sc : 1f);
                    if (prop.glow != null && prop.glow.Length >= 3) WarmLight(party, ManorLayout.V(item.p) + Vector3.up * prop.glowY * t.localScale.y, ManorLayout.C(prop.glow), 3.5f, 0.9f);
                }
            if (a.banner != null && a.banner.Length >= 3)
            {
                var prop = props?.FindProp("banner");
                var at = ManorLayout.V(a.banner);
                if (prop != null)
                {
                    var t = TestRoomBuilder.BuildParts(party, "Banner", prop.parts, Vector3.zero);
                    t.position = at;
                    t.localScale = new Vector3(a.bannerWidth > 0f ? a.bannerWidth / 5.2f : 1f, 1f, 1f);
                }
                // The words face the street (-z), so they read from the van and the sidewalk.
                var words = Horizon.MakeText(party, a.bannerText ?? "THANK YOU!", at + new Vector3(0, 2.3f, -0.03f), 0.06f, new Color(0.55f, 0.22f, 0.08f));
                words.transform.rotation = Quaternion.identity;
                WarmLight(party, at + new Vector3(0, 2.6f, -1.5f), new Color(1f, 0.78f, 0.45f), 9f, 1.4f);
            }
            party.gameObject.SetActive(false);

            Light haunt = null;
            if (a.haunt != null && a.haunt.Length >= 3)
            {
                haunt = new GameObject("HauntLight").AddComponent<Light>();
                haunt.transform.SetParent(moodGo.transform, false);
                haunt.transform.position = ManorLayout.V(a.haunt);
                haunt.type = LightType.Point;
                haunt.range = 14f;
                haunt.intensity = 2.2f;
                haunt.color = new Color(0.62f, 0.32f, 1f);
                haunt.shadows = LightShadows.None;
                haunt.enabled = false;
            }
            var mood = moodGo.AddComponent<HouseMood>();
            mood.HouseId = lot.id;
            mood.Afterglow = party.gameObject;
            mood.Haunt = haunt;
        }

        static void WarmLight(Transform parent, Vector3 at, Color color, float range, float intensity)
        {
            var lamp = new GameObject("Glow").AddComponent<Light>();
            lamp.transform.SetParent(parent, false);
            lamp.transform.position = at;
            lamp.type = LightType.Point;
            lamp.range = range;
            lamp.intensity = intensity;
            lamp.color = color;
            lamp.shadows = LightShadows.None;
            lamp.gameObject.AddComponent<CandleFlicker>().Amount = 0.25f;
        }

        /// <summary>One spot on the HQ keepsake shelf: the case's souvenir, hidden until it's solved.</summary>
        static void BuildKeepsake(Transform parent, TownLayout.Keepsake k)
        {
            var go = new GameObject("Keepsake_" + k.house);
            go.transform.SetParent(parent, false);
            go.transform.position = ManorLayout.V(k.p);
            var display = go.AddComponent<KeepsakeDisplay>();
            display.HouseId = k.house;

            var model = new GameObject("Model").transform;
            model.SetParent(go.transform, false);
            var brass = TestRoomBuilder.Mat("KeepsakeBrass", new Color(0.78f, 0.6f, 0.25f));
            switch (k.house)
            {
                case "PembertonCottage": // the Harvest Lantern's spare wick, in a little lantern
                    TestRoomBuilder.Shape(PrimitiveType.Cylinder, "Base", model, new Vector3(0, 0.02f, 0), new Vector3(0.22f, 0.02f, 0.22f), brass, false);
                    TestRoomBuilder.Shape(PrimitiveType.Cylinder, "Glass", model, new Vector3(0, 0.16f, 0), new Vector3(0.17f, 0.12f, 0.17f),
                        TestRoomBuilder.Mat("KeepsakeEmber", new Color(1f, 0.68f, 0.3f), true), false);
                    TestRoomBuilder.Shape(PrimitiveType.Sphere, "Cap", model, new Vector3(0, 0.3f, 0), new Vector3(0.2f, 0.06f, 0.2f), brass, false);
                    var glow = new GameObject("Glow").AddComponent<Light>();
                    glow.transform.SetParent(model, false);
                    glow.transform.localPosition = new Vector3(0, 0.18f, 0.2f);
                    glow.type = LightType.Point;
                    glow.color = new Color(1f, 0.7f, 0.35f);
                    glow.range = 2.5f;
                    glow.intensity = 1.2f;
                    break;
                case "HollowCreekFarm": // a blue prize rosette
                    TestRoomBuilder.Shape(PrimitiveType.Cylinder, "Rosette", model, new Vector3(0, 0.2f, 0.05f), new Vector3(0.26f, 0.01f, 0.26f),
                        TestRoomBuilder.Mat("KeepsakeBlue", new Color(0.2f, 0.35f, 0.8f)), false).transform.localRotation = Quaternion.Euler(90, 0, 0);
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "RibbonL", model, new Vector3(-0.05f, 0.05f, 0.06f), new Vector3(0.05f, 0.16f, 0.01f),
                        TestRoomBuilder.Mat("KeepsakeBlue", new Color(0.2f, 0.35f, 0.8f)), false);
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "RibbonR", model, new Vector3(0.05f, 0.05f, 0.06f), new Vector3(0.05f, 0.16f, 0.01f),
                        TestRoomBuilder.Mat("KeepsakeBlue", new Color(0.2f, 0.35f, 0.8f)), false);
                    break;
                case "WillowLaneVictorian": // a recital programme, propped up
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "Programme", model, new Vector3(0, 0.13f, 0.05f), new Vector3(0.18f, 0.26f, 0.01f),
                        TestRoomBuilder.Mat("KeepsakeLilac", new Color(0.78f, 0.68f, 0.86f)), false).transform.localRotation = Quaternion.Euler(-12, 0, 0);
                    break;
                case "HistoricalSociety": // the Hollow Creek Mask's old museum label, a little brass plaque on a stand
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "Stand", model, new Vector3(0, 0.05f, 0.05f), new Vector3(0.05f, 0.1f, 0.05f), brass, false);
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "Plaque", model, new Vector3(0, 0.13f, 0.04f), new Vector3(0.24f, 0.12f, 0.015f), brass, false)
                        .transform.localRotation = Quaternion.Euler(-15, 0, 0);
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "Lettering", model, new Vector3(0, 0.13f, 0.03f), new Vector3(0.18f, 0.03f, 0.016f),
                        TestRoomBuilder.Mat("KeepsakeInk", new Color(0.15f, 0.1f, 0.08f)), false).transform.localRotation = Quaternion.Euler(-15, 0, 0);
                    break;
                default: // the ledger's first page, in a little frame
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "Frame", model, new Vector3(0, 0.12f, 0.05f), new Vector3(0.22f, 0.24f, 0.02f),
                        TestRoomBuilder.Mat("KeepsakeFrame", new Color(0.35f, 0.2f, 0.1f)), false).transform.localRotation = Quaternion.Euler(-12, 0, 0);
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "Page", model, new Vector3(0, 0.12f, 0.04f), new Vector3(0.17f, 0.19f, 0.022f),
                        TestRoomBuilder.Mat("KeepsakePaper", new Color(0.92f, 0.86f, 0.7f)), false).transform.localRotation = Quaternion.Euler(-12, 0, 0);
                    break;
            }
            display.Model = model.gameObject;

            var card = TestRoomBuilder.Shape(PrimitiveType.Cube, "OpenCaseCard", go.transform, new Vector3(0, 0.06f, 0.05f), new Vector3(0.16f, 0.11f, 0.01f),
                TestRoomBuilder.Mat("KeepsakeCard", new Color(0.9f, 0.84f, 0.7f)), false);
            card.transform.localRotation = Quaternion.Euler(-20, 0, 0);
            display.EmptyCard = card;
        }

        /// <summary>The townsfolk out tonight, and the lost things they'll ask the club to find.</summary>
        static void BuildFolk(TownLayout town)
        {
            if (town.folk == null) return;
            var costumes = TestRoomBuilder.LoadCostumes();
            var root = new GameObject("Townsfolk").transform;
            foreach (var f in town.folk)
            {
                var go = new GameObject("Folk_" + f.id);
                go.transform.SetParent(root, false);
                go.transform.SetPositionAndRotation(ManorLayout.V(f.p), Quaternion.Euler(0, f.ry, 0));
                var collider = go.AddComponent<CapsuleCollider>();
                collider.center = new Vector3(0, 1f, 0); collider.height = 2f; collider.radius = 0.4f;
                // Turn (Townsperson faces you) holds Model (PawnAnimator sways it), so the two don't fight
                var turn = new GameObject("Turn").transform;
                turn.SetParent(go.transform, false);
                var model = new GameObject("Model").transform;
                model.SetParent(turn, false);
                var parts = Costumes.FindOutfit(costumes?.suspects, "Folk." + f.id);
                if (parts != null) TestRoomBuilder.BuildParts(model, "Outfit", parts, Vector3.zero);
                else TestRoomBuilder.Shape(PrimitiveType.Capsule, "Body", model, new Vector3(0, 1f, 0), new Vector3(0.8f, 1f, 0.8f),
                    TestRoomBuilder.Mat("Folk", new Color(0.6f, 0.5f, 0.5f)), false);
                var anim = go.AddComponent<PawnAnimator>();
                anim.Kind = PawnAnimator.Style.Suspect;
                anim.Body = model;
                go.AddComponent<NetworkObject>();
                var person = go.AddComponent<Townsperson>();
                person.FolkId = f.id;
                person.Model = turn;

                if (string.IsNullOrEmpty(f.item) || f.itemP == null) continue;
                var item = new GameObject("Lost_" + f.id);
                item.transform.SetParent(root, false);
                item.transform.SetPositionAndRotation(ManorLayout.V(f.itemP), Quaternion.Euler(0, f.itemRy, 0));
                var sphere = item.AddComponent<SphereCollider>();
                sphere.center = new Vector3(0, 0.45f, 0);
                sphere.radius = 0.6f;
                var look = new GameObject("Model").transform;
                look.SetParent(item.transform, false);
                var prop = costumes?.FindProp(f.item);
                if (prop != null) TestRoomBuilder.BuildParts(look, "Prop", prop.parts, Vector3.zero);
                else TestRoomBuilder.Shape(PrimitiveType.Sphere, "Prop", look, new Vector3(0, 0.3f, 0), Vector3.one * 0.5f,
                    TestRoomBuilder.Mat("Lost", new Color(1f, 0.6f, 0.2f)), false);
                item.AddComponent<NetworkObject>();
                var errand = item.AddComponent<ErrandItem>();
                errand.Owner = person;
                errand.Model = look;
            }
        }

        static void BuildVan(TownLayout.Placed spot)
        {
            var van = new GameObject("MysteryVan");
            van.transform.SetPositionAndRotation(ManorLayout.V(spot.p), Quaternion.Euler(0, spot.ry, 0));
            var model = TestRoomBuilder.LoadCostumes()?.FindProp("van");
            if (model != null) TestRoomBuilder.BuildParts(van.transform, "Model", model.parts, Vector3.zero);
            else TestRoomBuilder.Shape(PrimitiveType.Cube, "Model", van.transform, new Vector3(0, 1.2f, 0), new Vector3(2f, 2f, 4.6f),
                TestRoomBuilder.Mat("Van", new Color(0.25f, 0.65f, 0.63f)), false);

            var box = van.AddComponent<BoxCollider>();
            box.center = new Vector3(0, 1.3f, 0);
            box.size = new Vector3(2.0f, 2.3f, 4.7f);

            // Seats: feet low so heads stay under the roof (nobody animates sitting yet).
            var seats = new Transform[4];
            Vector3[] seatPos = { new(-0.45f, 0.3f, 0.8f), new(0.45f, 0.3f, 0.8f), new(-0.45f, 0.3f, -0.8f), new(0.45f, 0.3f, -0.8f) };
            for (int i = 0; i < seats.Length; i++)
            {
                seats[i] = new GameObject(i == 0 ? "DriverSeat" : $"Seat{i}").transform;
                seats[i].SetParent(van.transform, false);
                seats[i].localPosition = seatPos[i];
            }
            var exit = new GameObject("Exit").transform;
            exit.SetParent(van.transform, false);
            exit.localPosition = new Vector3(-2.0f, 0f, 0.6f);

            var lights = new Light[2];
            for (int i = 0; i < 2; i++)
            {
                var lamp = new GameObject(i == 0 ? "HeadlightL" : "HeadlightR").AddComponent<Light>();
                lamp.transform.SetParent(van.transform, false);
                lamp.transform.localPosition = new Vector3(i == 0 ? -0.7f : 0.7f, 0.95f, 2.4f);
                lamp.transform.localRotation = Quaternion.Euler(8f, 0f, 0f);
                lamp.type = LightType.Spot;
                lamp.range = 30f;
                lamp.spotAngle = 60f;
                lamp.intensity = 2.2f;
                lamp.color = new Color(1f, 0.93f, 0.75f);
                lamp.shadows = LightShadows.None;
                lights[i] = lamp;
            }

            van.AddComponent<NetworkObject>();
            van.AddComponent<OwnerNetworkTransform>();
            var mv = van.AddComponent<MysteryVan>();
            mv.Seats = seats;
            mv.ExitPoint = exit;
            mv.Headlights = lights;
        }
    }
}
