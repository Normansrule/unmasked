using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace Unmasked
{
    /// <summary>
    /// Everything past the edge of the map, so Hollow Creek feels like one valley in a bigger world
    /// (built on every machine from the "horizon" block of HollowCreek.json; purely cosmetic):
    ///
    ///  - Far: three rings of hills that follow the camera like the sky does, so they never get any
    ///    closer. Far-off windows and farm lights twinkle on them, and landmarks stand on the ridges:
    ///    Ravensford's steeple, the Gull Point lighthouse (its beam sweeps round), a windmill turning,
    ///    a water tower, the Thornbury ruins. Drawn without fog so they show through the night haze,
    ///    with a band of mist at their feet so they sit in the valley.
    ///  - Near: the roads carry on out of town, lit by street lamps, with signposts to the next towns,
    ///    until the fog swallows them; a band of autumn forest closes in round the fields; the ground
    ///    keeps going under it all.
    /// </summary>
    public class Horizon : MonoBehaviour
    {
        Transform sky, beam, blades;
        Mesh lightsMesh;
        Color[] lightColors, lightBase;
        float nextTwinkle, maxRadius;
        System.Random twinkle = new(11);

        public static void Ensure(GameObject host)
        {
            var town = TownLayout.Current;
            if (town?.horizon?.rings == null || host.GetComponent<Horizon>() != null) return;
            host.AddComponent<Horizon>().Build(town);
        }

        // ---- The same height curve and random numbers as Docs/tools/render3d.py's horizon ----

        public static float RingHeight(TownLayout.HorizonInfo.Ring ring, float angleDeg)
        {
            float h = ring.@base;
            for (int i = 0; i + 2 < ring.waves.Length; i += 3)
                h += ring.waves[i] * Mathf.Sin(ring.waves[i + 1] * angleDeg * Mathf.Deg2Rad + ring.waves[i + 2]);
            return h;
        }

        /// <summary>A tiny LCG so Python and C# scatter lights and trees in the same places.</summary>
        internal class Lcg
        {
            uint state;
            public Lcg(int seed) { state = (uint)seed * 2654435761u + 1u; }
            public float Next()
            {
                state = state * 1664525u + 1013904223u;
                return (state >> 8) / 16777216f;
            }
            public float Range(float a, float b) => a + (b - a) * Next();
        }

        internal static Vector3 OnRing(float radius, float angleDeg, float y)
        {
            float a = angleDeg * Mathf.Deg2Rad;
            return new Vector3(Mathf.Sin(a) * radius, y, Mathf.Cos(a) * radius);
        }

        static Color C(float[] c, int i = 0) => new(c[i], c[i + 1], c[i + 2]);

        void Build(TownLayout town)
        {
            var h = town.horizon;
            sky = new GameObject("FarHorizon").transform;
            sky.SetParent(transform, false);

            var unlit = new Material(Shader.Find("Sprites/Default")) { name = "HorizonUnlit" };
            var mist = new Color(0.17f, 0.12f, 0.24f);
            if (RenderSettings.fog) mist = Color.Lerp(RenderSettings.fogColor, mist, 0.5f);

            // Hills, farthest first so nearer ridges draw over them.
            for (int r = 0; r < h.rings.Length; r++)
            {
                var ring = h.rings[r];
                maxRadius = Mathf.Max(maxRadius, ring.radius);
                var b = new MeshBuilder();
                Color top = C(ring.color), foot = Color.Lerp(top, mist, 0.65f);
                for (int a = 0; a < 360; a++)
                {
                    float y0 = RingHeight(ring, a), y1 = RingHeight(ring, a + 1);
                    b.Quad(OnRing(ring.radius, a, -8f), OnRing(ring.radius, a + 1, -8f), OnRing(ring.radius, a + 1, y1), OnRing(ring.radius, a, y0),
                        foot, foot, top, top);
                }
                AddLayer(b, "Hills" + r, unlit, r * 10);
            }

            // Mist lying in the valley, in front of every ridge.
            {
                var b = new MeshBuilder();
                float radius = h.rings[h.rings.Length - 1].radius - 15f;
                Color low = new(mist.r, mist.g, mist.b, 0.85f), high = new(mist.r, mist.g, mist.b, 0f);
                for (int a = 0; a < 360; a += 2)
                    b.Quad(OnRing(radius, a, -8f), OnRing(radius, a + 2, -8f), OnRing(radius, a + 2, 26f), OnRing(radius, a, 26f), low, low, high, high);
                AddLayer(b, "ValleyMist", unlit, 100);
            }

            // Far-off windows and farm lights.
            if (h.lights != null && h.lights.count > 0)
            {
                var rng = new Lcg(h.lights.seed);
                var b = new MeshBuilder();
                int colors = Mathf.Max(1, h.lights.colors.Length / 3);
                for (int i = 0; i < h.lights.count; i++)
                {
                    float angle = rng.Range(0f, 360f);
                    int r = Mathf.Min(h.rings.Length - 1, (int)(rng.Next() * h.rings.Length));
                    var ring = h.rings[r];
                    float y = RingHeight(ring, angle) * rng.Range(0.15f, 0.8f);
                    float size = rng.Range(1.0f, 2.4f) * ring.radius / 540f;
                    var c = C(h.lights.colors, 3 * (int)(rng.Next() * colors) % (3 * colors));
                    var centre = OnRing(ring.radius - 2f, angle, y);
                    Vector3 right = Vector3.Cross(Vector3.up, -centre.normalized) * size * 0.5f, up = Vector3.up * size * 0.5f;
                    b.Quad(centre - right - up, centre + right - up, centre + right + up, centre - right + up, c, c, c, c);
                }
                var mf = AddLayer(b, "FarLights", unlit, 50);
                lightsMesh = mf.mesh;
                lightColors = lightsMesh.colors;
                lightBase = (Color[])lightColors.Clone();
            }

            // Landmarks on the ridges.
            if (h.landmarks != null)
                foreach (var lm in h.landmarks)
                    BuildLandmark(h, lm, unlit);

            BuildRoads(h);
            BuildForest(h);
            BuildGround(h);
        }

        MeshFilter AddLayer(MeshBuilder b, string name, Material mat, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(sky, false);
            var mf = go.AddComponent<MeshFilter>();
            mf.mesh = b.ToMesh(name);
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = mat;
            mr.sortingOrder = order;
            mr.shadowCastingMode = ShadowCastingMode.Off;
            mr.receiveShadows = false;
            return mf;
        }

        void BuildLandmark(TownLayout.HorizonInfo h, TownLayout.HorizonInfo.Landmark lm, Material unlit)
        {
            var ring = h.rings[Mathf.Clamp(lm.ring, 0, h.rings.Length - 1)];
            float s = lm.size * ring.radius / 540f;
            float ground = RingHeight(ring, lm.angle) - 3f * s;
            var root = new GameObject("Landmark_" + lm.kind).transform;
            root.SetParent(sky, false);
            root.localPosition = OnRing(ring.radius - 4f, lm.angle, ground);
            var inward = -root.localPosition;
            inward.y = 0f;
            root.localRotation = Quaternion.LookRotation(inward.normalized);
            Color dark = C(ring.color) * 0.8f, lit = new(1f, 0.8f, 0.45f);
            dark.a = 1f;
            var b = new MeshBuilder();
            switch (lm.kind)
            {
                case "steeple":
                    b.Box(new Vector3(0, 9, 0) * s, new Vector3(14, 18, 10) * s, dark);
                    b.Box(new Vector3(0, 26, 0) * s, new Vector3(6, 16, 6) * s, dark);
                    b.Pyramid(new Vector3(0, 34, 0) * s, 4f * s, 18f * s, dark);
                    b.Box(new Vector3(0, 27, -3.1f) * s, new Vector3(2, 3, 0.2f) * s, lit);
                    b.Box(new Vector3(-3.5f, 8, -5.1f) * s, new Vector3(2, 4, 0.2f) * s, lit);
                    b.Box(new Vector3(3.5f, 8, -5.1f) * s, new Vector3(2, 4, 0.2f) * s, lit);
                    break;
                case "lighthouse":
                    b.Box(new Vector3(0, 18, 0) * s, new Vector3(7, 36, 7) * s, dark);
                    b.Box(new Vector3(0, 38, 0) * s, new Vector3(5, 4, 5) * s, lit);
                    b.Pyramid(new Vector3(0, 40, 0) * s, 3.4f * s, 5f * s, dark);
                    beam = BeamAt(root, new Vector3(0, 38, 0) * s, 90f * s, unlit);
                    break;
                case "windmill":
                    b.Box(new Vector3(0, 9, 0) * s, new Vector3(9, 18, 9) * s, dark);
                    b.Pyramid(new Vector3(0, 18, 0) * s, 5f * s, 6f * s, dark);
                    b.Box(new Vector3(0, 6, -4.6f) * s, new Vector3(1.6f, 2.2f, 0.2f) * s, lit);
                    blades = new GameObject("Blades").transform;
                    blades.SetParent(root, false);
                    blades.localPosition = new Vector3(0, 17, -5.2f) * s;
                    var bb = new MeshBuilder();
                    for (int i = 0; i < 4; i++)
                    {
                        var q = Quaternion.Euler(0, 0, i * 90f);
                        bb.Quad(q * new Vector3(-0.8f, 0, 0) * s, q * new Vector3(0.8f, 0, 0) * s, q * new Vector3(1.6f, 13, 0) * s, q * new Vector3(-0.4f, 13, 0) * s, dark, dark, dark, dark);
                    }
                    var bgo = blades.gameObject;
                    bgo.AddComponent<MeshFilter>().mesh = bb.ToMesh("Blades");
                    var bmr = bgo.AddComponent<MeshRenderer>();
                    bmr.sharedMaterial = unlit;
                    bmr.sortingOrder = 61;
                    break;
                case "watertower":
                    for (int i = 0; i < 4; i++)
                    {
                        float x = (i % 2 == 0 ? -1 : 1) * 3.5f, z = (i < 2 ? -1 : 1) * 3.5f;
                        b.Box(new Vector3(x, 8, z) * s, new Vector3(0.8f, 16, 0.8f) * s, dark);
                    }
                    b.Box(new Vector3(0, 20, 0) * s, new Vector3(11, 8, 11) * s, dark);
                    b.Pyramid(new Vector3(0, 24, 0) * s, 6f * s, 3f * s, dark);
                    b.Box(new Vector3(0, 24.6f, 0) * s, new Vector3(0.6f, 0.6f, 0.6f) * s, new Color(1f, 0.25f, 0.2f)); // aircraft light
                    break;
                default: // ruined castle
                    b.Box(new Vector3(-10, 8, 0) * s, new Vector3(8, 16, 8) * s, dark);
                    b.Box(new Vector3(10, 11, 0) * s, new Vector3(9, 22, 9) * s, dark);
                    b.Box(new Vector3(0, 5, 0) * s, new Vector3(14, 10, 4) * s, dark);
                    for (int i = 0; i < 4; i++) b.Box(new Vector3(6.6f + i * 2.2f, 23, 0) * s, new Vector3(1.2f, 2.4f, 9) * s, dark);
                    b.Box(new Vector3(10, 14, -4.6f) * s, new Vector3(1.4f, 2.4f, 0.2f) * s, lit);
                    break;
            }
            root.gameObject.AddComponent<MeshFilter>().mesh = b.ToMesh(lm.kind);
            var mr = root.gameObject.AddComponent<MeshRenderer>();
            mr.sharedMaterial = unlit;
            mr.sortingOrder = 60;
            mr.shadowCastingMode = ShadowCastingMode.Off;
        }

        static Transform BeamAt(Transform parent, Vector3 at, float length, Material unlit)
        {
            var t = new GameObject("LighthouseBeam").transform;
            t.SetParent(parent, false);
            t.localPosition = at;
            var b = new MeshBuilder();
            Color near = new(1f, 0.92f, 0.7f, 0.45f), far = new(1f, 0.92f, 0.7f, 0f);
            b.Quad(new Vector3(0, -0.6f, 0), new Vector3(0, 0.6f, 0), new Vector3(length, 5f, 0), new Vector3(length, -5f, 0), near, near, far, far);
            t.gameObject.AddComponent<MeshFilter>().mesh = b.ToMesh("Beam");
            var mr = t.gameObject.AddComponent<MeshRenderer>();
            mr.sharedMaterial = unlit;
            mr.sortingOrder = 70;
            return t;
        }

        // ---- Near the edge: roads, lamps, signs, forest, more ground. These stay put. ----

        internal static Material Lit(string name, Color c, bool emissive = false)
        {
            var m = new Material(Shader.Find("Standard")) { name = name, color = c };
            if (emissive)
            {
                m.EnableKeyword("_EMISSION");
                m.SetColor("_EmissionColor", c * 2.2f);
            }
            return m;
        }

        void BuildRoads(TownLayout.HorizonInfo h)
        {
            if (h.roads == null) return;
            var root = new GameObject("RoadsOutOfTown").transform;
            root.SetParent(transform, false);
            var asphalt = new MeshBuilder();
            var lines = new MeshBuilder();
            var poles = new MeshBuilder();
            var bulbs = new MeshBuilder();
            Color road = new(0.16f, 0.15f, 0.17f), dash = new(0.85f, 0.8f, 0.6f), pole = new(0.12f, 0.12f, 0.14f), bulb = new(1f, 0.8f, 0.5f);
            float w = h.roadWidth > 0 ? h.roadWidth : 8f;
            foreach (var r in h.roads)
            {
                var a = new Vector3(r.from[0], 0f, r.from[1]);
                var z = new Vector3(r.to[0], 0f, r.to[1]);
                var dir = (z - a).normalized;
                var side = Vector3.Cross(Vector3.up, dir);
                float len = Vector3.Distance(a, z);
                asphalt.Quad(a - side * w / 2 + Vector3.up * 0.005f, a + side * w / 2 + Vector3.up * 0.005f, z + side * w / 2 + Vector3.up * 0.005f, z - side * w / 2 + Vector3.up * 0.005f, road, road, road, road);
                for (float d = 3f; d < len - 3f; d += 6f)
                {
                    var p0 = a + dir * d + Vector3.up * 0.02f;
                    var p1 = p0 + dir * 2.4f;
                    lines.Quad(p0 - side * 0.09f, p0 + side * 0.09f, p1 + side * 0.09f, p1 - side * 0.09f, dash, dash, dash, dash);
                }
                int lamp = 0;
                for (float d = 10f; d < len; d += h.lampEvery > 0 ? h.lampEvery : 28f, lamp++)
                {
                    float sx = lamp % 2 == 0 ? 1f : -1f;
                    var basePos = a + dir * d + side * sx * (w / 2 + 1.2f);
                    poles.Box(basePos + Vector3.up * 2.6f, new Vector3(0.18f, 5.2f, 0.18f), pole);
                    poles.Box(basePos + Vector3.up * 5.1f - side * sx * 0.6f, new Vector3(0.12f, 0.12f, 1.3f) , pole);
                    bulbs.Box(basePos + Vector3.up * 4.95f - side * sx * 1.1f, new Vector3(0.4f, 0.25f, 0.4f), bulb);
                    if (lamp < 3)
                    {
                        var l = new GameObject("RoadLamp").AddComponent<Light>();
                        l.transform.SetParent(root, false);
                        l.transform.position = basePos + Vector3.up * 4.6f - side * sx * 1.1f;
                        l.type = LightType.Point;
                        l.color = bulb;
                        l.range = 14f;
                        l.intensity = 1.1f;
                        l.shadows = LightShadows.None;
                    }
                }
                if (!string.IsNullOrEmpty(r.sign)) BuildSign(root, a + dir * 22f + side * (w / 2 + 2.5f), dir, r.sign);
            }
            Part(root, "Asphalt", asphalt, Lit("RoadOut", road));
            Part(root, "Dashes", lines, Lit("RoadDash", dash));
            Part(root, "LampPoles", poles, Lit("LampPole", pole));
            Part(root, "LampBulbs", bulbs, Lit("LampBulb", bulb, true));
        }

        static void BuildSign(Transform parent, Vector3 at, Vector3 dir, string text)
        {
            var go = new GameObject("Signpost");
            go.transform.SetParent(parent, false);
            go.transform.position = at;
            go.transform.rotation = Quaternion.LookRotation(-dir);
            var wood = Lit("SignWood", new Color(0.36f, 0.24f, 0.14f));
            var post = GameObject.CreatePrimitive(PrimitiveType.Cube);
            post.transform.SetParent(go.transform, false);
            post.transform.localPosition = new Vector3(0, 1.1f, 0);
            post.transform.localScale = new Vector3(0.15f, 2.2f, 0.15f);
            post.GetComponent<Renderer>().sharedMaterial = wood;
            var board = GameObject.CreatePrimitive(PrimitiveType.Cube);
            board.transform.SetParent(go.transform, false);
            board.transform.localPosition = new Vector3(0, 2.0f, 0);
            board.transform.localScale = new Vector3(2.6f, 0.55f, 0.08f);
            board.GetComponent<Renderer>().sharedMaterial = Lit("SignBoard", new Color(0.82f, 0.74f, 0.55f));
            var label = MakeText(go.transform, text, new Vector3(0, 2.0f, -0.05f), 0.07f, new Color(0.2f, 0.12f, 0.08f));
            label.transform.localRotation = Quaternion.identity;
        }

        /// <summary>
        /// World-space text. A TextMesh made in code has no font, so give it Unity's built-in one
        /// (LegacyRuntime.ttf in Unity 6, Arial.ttf in older versions) and that font's material.
        /// </summary>
        public static TextMesh MakeText(Transform parent, string text, Vector3 localPosition, float characterSize, Color color)
        {
            var label = new GameObject("Text").AddComponent<TextMesh>();
            label.transform.SetParent(parent, false);
            label.transform.localPosition = localPosition;
            if (builtinFont == null) builtinFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            if (builtinFont == null) builtinFont = Resources.GetBuiltinResource<Font>("Arial.ttf");
            if (builtinFont != null)
            {
                label.font = builtinFont;
                label.GetComponent<MeshRenderer>().sharedMaterial = builtinFont.material;
            }
            label.text = text;
            label.anchor = TextAnchor.MiddleCenter;
            label.alignment = TextAlignment.Center;
            label.characterSize = characterSize;
            label.fontSize = 48;
            label.color = color;
            return label;
        }

        static Font builtinFont;

        void BuildForest(TownLayout.HorizonInfo h)
        {
            var f = h.forest;
            if (f == null || f.count <= 0 || f.town == null || f.town.Length < 4) return;
            var root = new GameObject("Forest").transform;
            root.SetParent(transform, false);
            var rng = new Lcg(f.seed);
            var trunks = new MeshBuilder();
            var crowns = new[] { new MeshBuilder(), new MeshBuilder(), new MeshBuilder() };
            Color bark = new(0.22f, 0.15f, 0.1f);
            float x0 = f.town[0], z0 = f.town[1], x1 = f.town[2], z1 = f.town[3];
            for (int i = 0, placed = 0; i < f.count * 3 && placed < f.count; i++)
            {
                // A random point in the band round the town rectangle.
                float x = rng.Range(x0 - f.outer, x1 + f.outer), z = rng.Range(z0 - f.outer, z1 + f.outer);
                float dx = Mathf.Max(x0 - f.inner - x, 0f, x - (x1 + f.inner));
                float dz = Mathf.Max(z0 - f.inner - z, 0f, z - (z1 + f.inner));
                float kind = rng.Next(), height = rng.Range(9f, 18f);
                if (dx <= 0f && dz <= 0f) continue; // inside the town (and its fields)
                if (NearRoad(h, x, z, 9f)) continue;
                var at = new Vector3(x, 0f, z);
                trunks.Box(at + Vector3.up * height * 0.2f, new Vector3(0.5f, height * 0.4f, 0.5f), bark);
                int v = kind < 0.55f ? 0 : kind < 0.82f ? 1 : 2;
                crowns[v].Pyramid(at + Vector3.up * height * 0.25f, height * 0.32f, height * 0.55f, Color.white);
                crowns[v].Pyramid(at + Vector3.up * height * 0.55f, height * 0.24f, height * 0.45f, Color.white);
                placed++;
            }
            Part(root, "Trunks", trunks, Lit("Bark", bark));
            Part(root, "Pines", crowns[0], Lit("Pine", new Color(0.12f, 0.2f, 0.14f)));
            Part(root, "AutumnOrange", crowns[1], Lit("AutumnOrange", new Color(0.55f, 0.27f, 0.1f)));
            Part(root, "AutumnRed", crowns[2], Lit("AutumnRed", new Color(0.4f, 0.12f, 0.1f)));
        }

        static bool NearRoad(TownLayout.HorizonInfo h, float x, float z, float margin)
        {
            if (h.roads == null) return false;
            var p = new Vector2(x, z);
            foreach (var r in h.roads)
            {
                var a = new Vector2(r.from[0], r.from[1]);
                var b = new Vector2(r.to[0], r.to[1]);
                var ab = b - a;
                float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / ab.sqrMagnitude);
                if (Vector2.Distance(p, a + ab * t) < h.roadWidth / 2 + margin) return true;
            }
            return false;
        }

        void BuildGround(TownLayout.HorizonInfo h)
        {
            var b = new MeshBuilder();
            Color grass = new(0.15f, 0.2f, 0.12f);
            float r = maxRadius > 0 ? maxRadius : 900f;
            var c = new Vector3(0, -0.06f, 100f);
            b.Quad(c + new Vector3(-r, 0, -r), c + new Vector3(-r, 0, r), c + new Vector3(r, 0, r), c + new Vector3(r, 0, -r), grass, grass, grass, grass);
            var root = new GameObject("FarFields").transform;
            root.SetParent(transform, false);
            Part(root, "Fields", b, Lit("FarFields", grass));
        }

        static void Part(Transform parent, string name, MeshBuilder b, Material m)
        {
            if (b.Empty) return;
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().mesh = b.ToMesh(name);
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = m;
            mr.shadowCastingMode = ShadowCastingMode.Off;
        }

        void LateUpdate()
        {
            var cam = Camera.main;
            if (cam != null && sky != null)
            {
                var p = cam.transform.position;
                sky.position = new Vector3(p.x, 0f, p.z);
                if (cam.farClipPlane < maxRadius + 60f) cam.farClipPlane = maxRadius + 60f;
            }
            if (beam != null) beam.localRotation = Quaternion.Euler(0f, Time.time * 40f, 0f);
            if (blades != null) blades.localRotation = Quaternion.Euler(0f, 0f, Time.time * 12f);
            if (lightsMesh != null && Time.time > nextTwinkle)
            {
                nextTwinkle = Time.time + 0.25f;
                for (int k = 0; k < 6; k++)
                {
                    int quad = twinkle.Next(lightBase.Length / 8) * 2; // each light is a front and a back quad
                    float dim = twinkle.NextDouble() < 0.3 ? 0.2f : 1f;
                    for (int v = 0; v < 8; v++)
                    {
                        var c = lightBase[quad * 4 + v];
                        lightColors[quad * 4 + v] = new Color(c.r, c.g, c.b, c.a * dim);
                    }
                }
                lightsMesh.colors = lightColors;
            }
        }

        /// <summary>Collects quads, boxes and pyramids into one mesh with vertex colours.</summary>
        internal class MeshBuilder
        {
            readonly List<Vector3> v = new();
            readonly List<Color> c = new();
            readonly List<int> t = new();
            public bool Empty => v.Count == 0;

            public void Quad(Vector3 a, Vector3 b, Vector3 d, Vector3 e, Color ca, Color cb, Color cd, Color ce)
            {
                // Both sides, each with its own vertices so lit materials get proper normals.
                for (int side = 0; side < 2; side++)
                {
                    int i = v.Count;
                    v.Add(a); v.Add(b); v.Add(d); v.Add(e);
                    c.Add(ca); c.Add(cb); c.Add(cd); c.Add(ce);
                    if (side == 0) { t.Add(i); t.Add(i + 2); t.Add(i + 1); t.Add(i); t.Add(i + 3); t.Add(i + 2); }
                    else { t.Add(i); t.Add(i + 1); t.Add(i + 2); t.Add(i); t.Add(i + 2); t.Add(i + 3); }
                }
            }

            public void Box(Vector3 centre, Vector3 size, Color col)
            {
                var h = size / 2f;
                Vector3 P(float x, float y, float z) => centre + new Vector3(x * h.x, y * h.y, z * h.z);
                Quad(P(-1, -1, -1), P(1, -1, -1), P(1, 1, -1), P(-1, 1, -1), col, col, col, col);
                Quad(P(1, -1, 1), P(-1, -1, 1), P(-1, 1, 1), P(1, 1, 1), col, col, col, col);
                Quad(P(-1, -1, 1), P(-1, -1, -1), P(-1, 1, -1), P(-1, 1, 1), col, col, col, col);
                Quad(P(1, -1, -1), P(1, -1, 1), P(1, 1, 1), P(1, 1, -1), col, col, col, col);
                Quad(P(-1, 1, -1), P(1, 1, -1), P(1, 1, 1), P(-1, 1, 1), col, col, col, col);
            }

            /// <summary>A four-sided pyramid (spires, roofs, and stacked into fir trees).</summary>
            public void Pyramid(Vector3 baseCentre, float halfWidth, float height, Color col)
            {
                var top = baseCentre + Vector3.up * height;
                Vector3[] corners =
                {
                    baseCentre + new Vector3(-halfWidth, 0, -halfWidth), baseCentre + new Vector3(halfWidth, 0, -halfWidth),
                    baseCentre + new Vector3(halfWidth, 0, halfWidth), baseCentre + new Vector3(-halfWidth, 0, halfWidth),
                };
                for (int k = 0; k < 4; k++)
                {
                    for (int side = 0; side < 2; side++)
                    {
                        int i = v.Count;
                        v.Add(corners[k]); v.Add(corners[(k + 1) % 4]); v.Add(top);
                        c.Add(col); c.Add(col); c.Add(col);
                        if (side == 0) { t.Add(i); t.Add(i + 2); t.Add(i + 1); }
                        else { t.Add(i); t.Add(i + 1); t.Add(i + 2); }
                    }
                }
            }

            public Mesh ToMesh(string name)
            {
                var m = new Mesh { name = name, indexFormat = IndexFormat.UInt32 };
                m.SetVertices(v);
                m.SetColors(c);
                m.SetTriangles(t, 0);
                m.RecalculateNormals();
                m.RecalculateBounds();
                return m;
            }
        }
    }
}
