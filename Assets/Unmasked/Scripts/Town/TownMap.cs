using Unity.Netcode;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// The Hollow Creek map (M), a bit like the phone map in Schedule I: a top-down picture of the
    /// whole town with every house fully built on its lot, pins for each haunted house and HQ, the
    /// van and your friends, and a card for the selected house with a live 3D preview orbiting it.
    /// Pick a waypoint from the card (or tonight's call while you're still at HQ). A minimap sits in
    /// the corner the rest of the time, and an arrow points at the waypoint.
    ///
    /// Two extra cameras render to textures: one straight down over the town (rendered when the
    /// map opens, with the night brightened so you can read it) and one circling the selected house.
    /// </summary>
    public class TownMap : MonoBehaviour
    {
        public static TownMap Instance { get; private set; }
        public static bool IsOpen => Instance != null && Instance.open;

        [Tooltip("Width of the minimap view in metres.")]
        public float MinimapSpan = 110f;
        public int MapResolution = 1400;

        bool open;
        Camera mapCam, previewCam;
        RenderTexture mapTexture, previewTexture;
        Rect world; // x/z bounds of the town
        TownLayout town;
        TownLayout.Lot selected;
        Vector3? waypoint;
        string waypointName;
        float lastMapRender = -100f;
        GUIStyle pinLabel, cardTitle, cardText, small, arrowStyle;

        // Saved night lighting while the map cameras render brighter.
        bool savedFog;
        Color savedSky, savedEquator, savedGround;

        void Awake()
        {
            Instance = this;
            town = TownLayout.Current;
            world = TownBounds(town);

            mapCam = MakeCamera("MapCamera", true);
            mapCam.orthographicSize = world.height / 2f;
            mapCam.aspect = world.width / world.height;
            mapCam.transform.SetPositionAndRotation(new Vector3(world.center.x, 400f, world.center.y), Quaternion.Euler(90f, 0f, 0f));
            mapTexture = new RenderTexture(MapResolution, Mathf.RoundToInt(MapResolution * world.height / world.width), 24) { name = "TownMap" };
            mapCam.targetTexture = mapTexture;

            previewCam = MakeCamera("HousePreviewCamera", false);
            previewTexture = new RenderTexture(560, 340, 24) { name = "HousePreview" };
            previewCam.targetTexture = previewTexture;

            Camera.onPreRender += BrightenFor;
            Camera.onPostRender += Restore;
        }

        void OnDestroy()
        {
            Camera.onPreRender -= BrightenFor;
            Camera.onPostRender -= Restore;
            if (mapTexture != null) mapTexture.Release();
            if (previewTexture != null) previewTexture.Release();
        }

        Camera MakeCamera(string name, bool ortho)
        {
            var cam = new GameObject(name).AddComponent<Camera>();
            cam.transform.SetParent(transform, false);
            cam.orthographic = ortho;
            cam.fieldOfView = 40f;
            cam.nearClipPlane = 0.5f;
            cam.farClipPlane = 1000f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.05f, 0.04f, 0.09f);
            cam.cullingMask = ~(1 << 1); // skip TransparentFX: the mist and fireflies
            cam.enabled = false;
            return cam;
        }

        static Rect TownBounds(TownLayout t)
        {
            if (t?.rooms != null)
                foreach (var room in t.rooms)
                    if (room.n == t.name) return Rect.MinMaxRect(room.min[0], room.min[2], room.max[0], room.max[2]);
            return Rect.MinMaxRect(-170, -110, 130, 300);
        }

        // ---- The map is easier to read with the lights up ----

        void BrightenFor(Camera cam)
        {
            if (cam != mapCam && cam != previewCam) return;
            savedFog = RenderSettings.fog;
            savedSky = RenderSettings.ambientSkyColor;
            savedEquator = RenderSettings.ambientEquatorColor;
            savedGround = RenderSettings.ambientGroundColor;
            RenderSettings.fog = false;
            RenderSettings.ambientSkyColor = savedSky * 2.2f + new Color(0.08f, 0.08f, 0.12f);
            RenderSettings.ambientEquatorColor = savedEquator * 2.2f + new Color(0.08f, 0.07f, 0.1f);
            RenderSettings.ambientGroundColor = savedGround * 2f + new Color(0.06f, 0.06f, 0.08f);
        }

        void Restore(Camera cam)
        {
            if (cam != mapCam && cam != previewCam) return;
            RenderSettings.fog = savedFog;
            RenderSettings.ambientSkyColor = savedSky;
            RenderSettings.ambientEquatorColor = savedEquator;
            RenderSettings.ambientGroundColor = savedGround;
        }

        // ---- Input and cameras ----

        void Update()
        {
            var keyboard = Keyboard.current;
            bool inGame = NetworkManager.Singleton != null && NetworkManager.Singleton.IsClient && PlayerAgent.Local != null;
            if (!inGame) { open = false; return; }

            if (keyboard != null && keyboard.mKey.wasPressedThisFrame) open = !open;
            if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame) open = false;

            if ((open && Time.time - lastMapRender > 2f) || lastMapRender < 0f)
            {
                mapCam.Render(); // houses are static, so a fresh picture now and then is plenty
                lastMapRender = Time.time;
            }

            var game = MysteryGameManager.Instance;
            if (selected == null && game != null && game.IsSpawned) selected = town?.FindLot(game.ActiveHouse.Value.ToString());
            if (open && selected != null)
            {
                float t = Time.time * 0.25f;
                Vector3 c = selected.Center;
                float r = Mathf.Max(selected.Max.x - selected.Min.x, selected.Max.y - selected.Min.y) * 0.75f + 8f;
                previewCam.transform.position = c + new Vector3(Mathf.Sin(t) * r, r * 0.55f, -Mathf.Cos(t) * r);
                previewCam.transform.LookAt(c + Vector3.up * 3f);
                previewCam.Render();
            }
        }

        /// <summary>Where the arrow points: your own waypoint, or tonight's call while driving there.</summary>
        public bool TryGetWaypoint(out Vector3 position, out string label)
        {
            position = default;
            label = null;
            if (waypoint.HasValue) { position = waypoint.Value; label = waypointName; return true; }
            var game = MysteryGameManager.Instance;
            var lot = game != null && game.IsSpawned && game.Phase.Value == MatchPhase.Dispatch ? town?.FindLot(game.ActiveHouse.Value.ToString()) : null;
            if (lot == null) return false;
            position = lot.Arrival;
            label = lot.name;
            return true;
        }

        // ---- Drawing ----

        void OnGUI()
        {
            if (town == null || NetworkManager.Singleton == null || PlayerAgent.Local == null) return;
            GUI.depth = -10;
            if (pinLabel == null)
            {
                pinLabel = new GUIStyle(GUI.skin.label) { fontSize = 13, fontStyle = FontStyle.Bold, alignment = TextAnchor.UpperCenter };
                cardTitle = new GUIStyle(GUI.skin.label) { fontSize = 22, fontStyle = FontStyle.Bold, wordWrap = true };
                cardText = new GUIStyle(GUI.skin.label) { fontSize = 14, wordWrap = true };
                small = new GUIStyle(GUI.skin.label) { fontSize = 11, alignment = TextAnchor.MiddleCenter };
                arrowStyle = new GUIStyle(GUI.skin.label) { fontSize = 30, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
            }

            if (open) DrawMap();
            else
            {
                DrawMinimap();
                DrawWaypointArrow();
            }
        }

        Vector2 ToMap(Vector3 p, Rect r) => new(
            r.x + (p.x - world.xMin) / world.width * r.width,
            r.yMax - (p.z - world.yMin) / world.height * r.height);

        void DrawMap()
        {
            var game = MysteryGameManager.Instance;
            GUI.color = new Color(0f, 0f, 0f, 0.82f);
            GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), Texture2D.whiteTexture);
            GUI.color = Color.white;

            float mapH = Screen.height - 90f;
            float mapW = mapH * world.width / world.height;
            if (mapW > Screen.width * 0.62f) { mapW = Screen.width * 0.62f; mapH = mapW * world.height / world.width; }
            var r = new Rect(30, 60, mapW, mapH);
            GUI.Label(new Rect(30, 14, 600, 40), $"<size=28><b>{town.name.ToUpperInvariant()}</b></size>   <size=14>M or Esc to close · click a house</size>",
                new GUIStyle(GUI.skin.label) { richText = true });
            GUI.DrawTexture(r, mapTexture, ScaleMode.StretchToFill);

            // HQ
            if (town.hq?.van != null)
            {
                var hq = ToMap(ManorLayout.V(town.hq.spawns[0].p), r);
                Pin(hq, new Color(0.25f, 0.95f, 0.9f), "Mystery Club HQ", 11f);
            }

            // Houses
            string active = game != null && game.IsSpawned ? game.ActiveHouse.Value.ToString() : "";
            foreach (var lot in town.lots)
            {
                var p = ToMap(lot.Center, r);
                bool isCall = lot.id == active;
                float pulse = isCall ? 1f + 0.25f * Mathf.Sin(Time.time * 6f) : 1f;
                var color = isCall ? new Color(1f, 0.35f, 0.25f) : selected == lot ? new Color(1f, 0.8f, 0.3f) : new Color(1f, 0.6f, 0.2f);
                Pin(p, color, $"{lot.name}\n<size=11>{lot.size}{(isCall ? " · TONIGHT'S CALL" : "")}</size>", 13f * pulse);
                if (GUI.Button(new Rect(p.x - 16, p.y - 16, 32, 32), GUIContent.none, GUIStyle.none)) selected = lot;
            }

            // The van and the club
            var van = MysteryVan.Instance;
            // Townsfolk: a "!" while they're waiting on an errand, a tick once it's done
            foreach (var folk in Townsperson.All)
            {
                var state = folk.Errand.Value;
                string mark = state == Townsperson.ErrandState.Done ? " (done)" : state == Townsperson.ErrandState.NotAsked ? "" : " !";
                Pin(ToMap(folk.transform.position, r), new Color(1f, 0.75f, 0.85f), $"<size=10>{folk.DisplayName}{mark}</size>", 6f);
            }

            if (van != null) Pin(ToMap(van.transform.position, r), new Color(0.3f, 0.9f, 0.85f), "Van", 8f);
            foreach (var solver in SolverController.All)
            {
                if (solver == null || solver.IsRiding) continue;
                bool me = solver == SolverController.Local;
                Pin(ToMap(solver.transform.position, r), me ? Color.white : new Color(0.6f, 0.8f, 1f), me ? "You" : "", me ? 8f : 6f);
            }
            if (TryGetWaypoint(out var wp, out _))
                Pin(ToMap(wp, r), new Color(1f, 1f, 0.4f), "", 5f);

            // Event banner
            if (game != null && game.IsSpawned && game.Event.Value != NightEvent.None && game.Phase.Value >= MatchPhase.Dispatch)
                GUI.Label(new Rect(r.x, r.yMax + 4, r.width, 24), $"Tonight: {TownLayout.EventName(game.Event.Value)}. {TownLayout.EventBlurb(game.Event.Value)}", cardText);

            DrawCard(new Rect(r.xMax + 24, 60, Screen.width - r.xMax - 54, Screen.height - 90), game);
        }

        void DrawCard(Rect r, MysteryGameManager game)
        {
            if (selected == null)
            {
                GUI.Label(r, "Click a house on the map to see it.", cardText);
                return;
            }
            GUILayout.BeginArea(r, GUI.skin.box);
            GUILayout.Label(selected.name, cardTitle);
            GUILayout.Label($"{selected.street}   ·   {selected.style}", cardText);
            float w = r.width - 16f;
            var preview = GUILayoutUtility.GetRect(w, w * previewTexture.height / previewTexture.width);
            GUI.DrawTexture(preview, previewTexture, ScaleMode.ScaleToFit);
            string skulls = new string('●', Mathf.Clamp(selected.difficulty, 1, 4)) + new string('○', 4 - Mathf.Clamp(selected.difficulty, 1, 4));
            GUILayout.Label($"Size: {selected.size}   Floors: {selected.floors}   Rooms: {selected.rooms}", cardText);
            GUILayout.Label($"Lot: {selected.Max.x - selected.Min.x:0} x {selected.Max.y - selected.Min.y:0} m   Spookiness: {skulls}", cardText);
            GUILayout.Space(6);
            GUILayout.Label(selected.blurb, cardText);
            GUILayout.FlexibleSpace();

            var me = SolverController.Local;
            if (me != null)
                GUILayout.Label($"{Vector3.Distance(me.transform.position, selected.Arrival):0} m away", cardText);
            if (GUILayout.Button(waypoint.HasValue && waypointName == selected.name ? "Clear waypoint" : "Set waypoint", GUILayout.Height(30)))
            {
                if (waypoint.HasValue && waypointName == selected.name) waypoint = null;
                else { waypoint = selected.Arrival; waypointName = selected.name; }
            }
            var agent = PlayerAgent.Local;
            if (game != null && game.IsSpawned && game.Phase.Value <= MatchPhase.Setup && agent != null && agent.Side.Value == PlayerSide.Solver)
            {
                bool isCall = game.ActiveHouse.Value.ToString() == selected.id;
                GUI.enabled = !isCall;
                if (GUILayout.Button(isCall ? "This is tonight's call" : "Take this call", GUILayout.Height(30)))
                    agent.ChooseCallRpc(selected.id);
                GUI.enabled = true;
            }
            GUILayout.EndArea();
        }

        void Pin(Vector2 at, Color color, string label, float size)
        {
            GUI.color = new Color(0f, 0f, 0f, 0.6f);
            GUI.DrawTexture(new Rect(at.x - size / 2 - 2, at.y - size / 2 - 2, size + 4, size + 4), Texture2D.whiteTexture);
            GUI.color = color;
            GUI.DrawTexture(new Rect(at.x - size / 2, at.y - size / 2, size, size), Texture2D.whiteTexture);
            GUI.color = Color.white;
            if (!string.IsNullOrEmpty(label))
            {
                var style = new GUIStyle(pinLabel) { richText = true };
                GUI.color = new Color(0, 0, 0, 0.8f);
                GUI.Label(new Rect(at.x - 99, at.y + size / 2 + 3, 200, 40), label, style);
                GUI.color = color;
                GUI.Label(new Rect(at.x - 100, at.y + size / 2 + 2, 200, 40), label, style);
                GUI.color = Color.white;
            }
        }

        void DrawMinimap()
        {
            var me = SolverController.Local;
            Transform focus = me != null ? me.transform : HaunterController.Local != null ? HaunterController.Local.transform : null;
            if (focus == null || mapTexture == null) return;

            const float size = 190f;
            var r = new Rect(Screen.width - size - 14, 44, size, size);
            float spanU = MinimapSpan / world.width, spanV = MinimapSpan / world.height;
            float u = (focus.position.x - world.xMin) / world.width - spanU / 2;
            float v = (focus.position.z - world.yMin) / world.height - spanV / 2;
            GUI.color = new Color(0, 0, 0, 0.7f);
            GUI.DrawTexture(new Rect(r.x - 3, r.y - 3, r.width + 6, r.height + 6), Texture2D.whiteTexture);
            GUI.color = Color.white;
            GUI.DrawTextureWithTexCoords(r, mapTexture, new Rect(u, v, spanU, spanV));

            Vector2 ToMini(Vector3 p) => new(
                r.center.x + (p.x - focus.position.x) / MinimapSpan * r.width,
                r.center.y - (p.z - focus.position.z) / MinimapSpan * r.height);

            if (TryGetWaypoint(out var wp, out _))
            {
                var p = ToMini(wp);
                p.x = Mathf.Clamp(p.x, r.xMin + 4, r.xMax - 4);
                p.y = Mathf.Clamp(p.y, r.yMin + 4, r.yMax - 4);
                GUI.color = new Color(1f, 1f, 0.4f);
                GUI.DrawTexture(new Rect(p.x - 5, p.y - 5, 10, 10), Texture2D.whiteTexture);
            }
            var van = MysteryVan.Instance;
            if (van != null && r.Contains(ToMini(van.transform.position)))
            {
                var p = ToMini(van.transform.position);
                GUI.color = new Color(0.3f, 0.9f, 0.85f);
                GUI.DrawTexture(new Rect(p.x - 4, p.y - 4, 8, 8), Texture2D.whiteTexture);
            }
            GUI.color = Color.white;
            GUI.DrawTexture(new Rect(r.center.x - 4, r.center.y - 4, 8, 8), Texture2D.whiteTexture);
            string here = ManorLayout.Describe(focus.position);
            GUI.Label(new Rect(r.x, r.yMax + 2, r.width, 18), here, small);
            GUI.Label(new Rect(r.x, r.yMax + 18, r.width, 18), "[M] map", small);
        }

        void DrawWaypointArrow()
        {
            var me = SolverController.Local;
            var cam = Camera.main;
            if (me == null || cam == null || !TryGetWaypoint(out var wp, out var label)) return;
            Vector3 to = wp - me.transform.position;
            to.y = 0f;
            float dist = to.magnitude;
            if (dist < 6f) return;
            float angle = Vector3.SignedAngle(Vector3.ProjectOnPlane(cam.transform.forward, Vector3.up), to, Vector3.up);
            var center = new Vector2(Screen.width / 2f, 84f);
            var matrix = GUI.matrix;
            GUIUtility.RotateAroundPivot(angle, center);
            GUI.color = new Color(1f, 0.9f, 0.4f);
            GUI.Label(new Rect(center.x - 20, center.y - 20, 40, 40), "^", arrowStyle);
            GUI.matrix = matrix;
            GUI.Label(new Rect(center.x - 150, center.y + 16, 300, 20), $"{label}  {dist:0} m", pinLabel);
            GUI.color = Color.white;
        }
    }
}
