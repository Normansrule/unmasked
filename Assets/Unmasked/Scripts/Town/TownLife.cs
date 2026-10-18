using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Hollow Creek is out trick-or-treating. Groups of kids in costumes walk the sidewalks with their
    /// candy buckets, stop now and then to knock, and tell you the town's rumours when you walk past
    /// (once a call comes in, rumours about tonight's house too). Cars come and go on the roads out of
    /// town, and a train with lit windows crosses the valley in front of the hills.
    ///
    /// All of it is scenery: built from the "life" block in HollowCreek.json, seeded so every machine
    /// starts the same, and never sent over the network. Nothing here is a clue.
    /// </summary>
    public class TownLife : MonoBehaviour
    {
        /// <summary>Add the town's life to this object (TownDirector calls it).</summary>
        public static void Ensure(GameObject host)
        {
            var town = TownLayout.Current;
            if (town?.life?.walks == null || host.GetComponent<TownLife>() != null) return;
            host.AddComponent<TownLife>().Build(town);
        }

        class Group
        {
            public Transform Root;
            public TownLayout.LifeInfo.Walk Walk;
            public float U, Dir, Side, Speed, PauseUntil, NextPause;
            public readonly List<Transform> Kids = new();
            public TextMesh Bubble;
            public bool Near;
            public int Said;
        }

        class Car
        {
            public Transform T;
            public TownLayout.HorizonInfo.Road Road;
            public float U, Speed;
            public bool Incoming;
        }

        readonly List<Group> groups = new();
        readonly List<Car> cars = new();
        Transform trainSky, train;
        float trainStart;
        TownLayout.LifeInfo life;
        TownLayout.HorizonInfo horizon;
        readonly Dictionary<Color, Material> materials = new();

        static readonly Color[] Skin =
        {
            new(0.96f, 0.80f, 0.68f), new(0.85f, 0.64f, 0.48f), new(0.62f, 0.42f, 0.28f), new(0.42f, 0.27f, 0.18f),
        };

        Material Mat(Color c, bool glow = false)
        {
            var key = glow ? new Color(c.r, c.g, c.b, 0.5f) : c;
            if (!materials.TryGetValue(key, out var m))
                materials[key] = m = Horizon.Lit(glow ? "LifeGlow" : "Life", c, glow);
            return m;
        }

        Transform Part(PrimitiveType type, Transform parent, Vector3 pos, Vector3 scale, Color c, bool glow = false, Vector3 rot = default)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>()); // scenery: never in anyone's way
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localScale = scale;
            go.transform.localRotation = Quaternion.Euler(rot);
            var r = go.GetComponent<Renderer>();
            r.sharedMaterial = Mat(c, glow);
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            return go.transform;
        }

        static Color C(float[] c) => c != null && c.Length >= 3 ? new Color(c[0], c[1], c[2]) : Color.gray;

        void Build(TownLayout town)
        {
            life = town.life;
            horizon = town.horizon;
            var rng = new Horizon.Lcg(life.seed);
            for (int g = 0; g < life.groups; g++)
            {
                var group = new Group
                {
                    Walk = life.walks[(int)(rng.Next() * life.walks.Length) % life.walks.Length],
                    U = rng.Next(),
                    Dir = rng.Next() < 0.5f ? -1f : 1f,
                    Side = rng.Next() < 0.5f ? -1f : 1f,
                    Speed = rng.Range(0.8f, 1.3f),
                };
                group.Root = new GameObject("TrickOrTreaters" + g).transform;
                group.Root.SetParent(transform, false);
                int count = 2 + (int)(rng.Next() * 3f);
                for (int k = 0; k < count; k++)
                {
                    var costume = life.costumes[(int)(rng.Next() * life.costumes.Length) % life.costumes.Length];
                    float height = rng.Range(0.85f, 1.2f);
                    var skin = Skin[(int)(rng.Next() * Skin.Length) % Skin.Length];
                    var kid = BuildKid(group.Root, costume, skin, height);
                    kid.localPosition = new Vector3((k % 2 == 0 ? -0.35f : 0.35f), 0f, -k * 0.8f);
                    group.Kids.Add(kid);
                }
                group.NextPause = rng.Range(15f, 40f);
                group.Bubble = Horizon.MakeText(group.Root, "", new Vector3(0f, 2.1f, 0f), 0.035f, new Color(1f, 0.93f, 0.75f));
                group.Bubble.gameObject.SetActive(false);
                groups.Add(group);
            }

            if (horizon?.roads != null && horizon.roads.Length > 0)
            {
                var crng = new Horizon.Lcg(life.carSeed);
                float lo = life.carSpeed != null && life.carSpeed.Length > 1 ? life.carSpeed[0] : 11f;
                float hi = life.carSpeed != null && life.carSpeed.Length > 1 ? life.carSpeed[1] : 17f;
                for (int i = 0; i < life.cars; i++)
                {
                    var car = new Car
                    {
                        Road = horizon.roads[(int)(crng.Next() * horizon.roads.Length) % horizon.roads.Length],
                        U = crng.Next(),
                        Incoming = crng.Next() < 0.5f,
                        Speed = crng.Range(lo, hi),
                    };
                    car.T = BuildCar(new Color(crng.Range(0.1f, 0.5f), crng.Range(0.1f, 0.3f), crng.Range(0.12f, 0.4f)));
                    cars.Add(car);
                }
            }

            if (life.train != null && life.train.cars > 0) BuildTrain(life.train);
        }

        // ---- Kids ----

        Transform BuildKid(Transform parent, TownLayout.LifeInfo.Costume costume, Color skin, float h)
        {
            var kid = new GameObject("Kid_" + costume.kind).transform;
            kid.SetParent(parent, false);
            var body = new GameObject("Body").transform;
            body.SetParent(kid, false);
            body.localScale = Vector3.one * h;
            Color main = C(costume.body), accent = C(costume.accent), dark = new(0.12f, 0.1f, 0.12f);
            var bucket = new Color(0.95f, 0.5f, 0.12f);

            Part(PrimitiveType.Capsule, body, new Vector3(-0.1f, 0.18f, 0), new Vector3(0.13f, 0.18f, 0.13f), dark);
            Part(PrimitiveType.Capsule, body, new Vector3(0.1f, 0.18f, 0), new Vector3(0.13f, 0.18f, 0.13f), dark);
            Part(PrimitiveType.Cylinder, body, new Vector3(0.3f, 0.5f, 0.12f), new Vector3(0.18f, 0.09f, 0.18f), bucket, true); // the candy bucket
            Part(PrimitiveType.Capsule, body, new Vector3(0.24f, 0.68f, 0.08f), new Vector3(0.09f, 0.16f, 0.09f), main, false, new Vector3(0, 0, 20)); // arm holding it

            switch (costume.kind)
            {
                case "sheet":
                    Part(PrimitiveType.Capsule, body, new Vector3(0, 0.66f, 0), new Vector3(0.56f, 0.5f, 0.5f), main);
                    Part(PrimitiveType.Sphere, body, new Vector3(-0.08f, 0.95f, 0.24f), new Vector3(0.07f, 0.09f, 0.03f), accent);
                    Part(PrimitiveType.Sphere, body, new Vector3(0.08f, 0.95f, 0.24f), new Vector3(0.07f, 0.09f, 0.03f), accent);
                    return kid;
                case "pumpkin":
                    Part(PrimitiveType.Sphere, body, new Vector3(0, 0.56f, 0), new Vector3(0.62f, 0.55f, 0.6f), main);
                    break;
                default:
                    Part(PrimitiveType.Capsule, body, new Vector3(0, 0.56f, 0), new Vector3(0.42f, 0.34f, 0.36f), main);
                    break;
            }
            var headColor = costume.kind == "skeleton" ? accent : skin;
            Part(PrimitiveType.Sphere, body, new Vector3(0, 1.02f, 0), Vector3.one * 0.32f, headColor);
            var eye = costume.kind == "cat" ? accent : dark;
            Part(PrimitiveType.Sphere, body, new Vector3(-0.06f, 1.05f, 0.14f), Vector3.one * 0.05f, eye, costume.kind == "cat");
            Part(PrimitiveType.Sphere, body, new Vector3(0.06f, 1.05f, 0.14f), Vector3.one * 0.05f, eye, costume.kind == "cat");

            switch (costume.kind)
            {
                case "witch":
                    Part(PrimitiveType.Cylinder, body, new Vector3(0, 1.17f, 0), new Vector3(0.5f, 0.01f, 0.5f), main);
                    Part(PrimitiveType.Cylinder, body, new Vector3(0, 1.26f, 0), new Vector3(0.26f, 0.08f, 0.26f), accent);
                    Part(PrimitiveType.Cylinder, body, new Vector3(0, 1.4f, 0), new Vector3(0.17f, 0.06f, 0.17f), main);
                    Part(PrimitiveType.Cylinder, body, new Vector3(0.02f, 1.51f, 0), new Vector3(0.09f, 0.05f, 0.09f), main, false, new Vector3(0, 0, -12));
                    break;
                case "pumpkin":
                    Part(PrimitiveType.Cylinder, body, new Vector3(0, 1.2f, 0), new Vector3(0.06f, 0.05f, 0.06f), accent);
                    break;
                case "skeleton":
                    for (int i = 0; i < 3; i++)
                        Part(PrimitiveType.Cube, body, new Vector3(0, 0.72f - i * 0.1f, 0.17f), new Vector3(0.3f - i * 0.04f, 0.035f, 0.03f), accent);
                    break;
                case "cat":
                    Part(PrimitiveType.Cube, body, new Vector3(-0.1f, 1.17f, 0), Vector3.one * 0.09f, main, false, new Vector3(0, 0, 45));
                    Part(PrimitiveType.Cube, body, new Vector3(0.1f, 1.17f, 0), Vector3.one * 0.09f, main, false, new Vector3(0, 0, 45));
                    Part(PrimitiveType.Capsule, body, new Vector3(0, 0.4f, -0.25f), new Vector3(0.06f, 0.22f, 0.06f), main, false, new Vector3(-50, 0, 0));
                    break;
                case "vampire":
                    Part(PrimitiveType.Cube, body, new Vector3(0, 0.6f, -0.17f), new Vector3(0.52f, 0.74f, 0.04f), accent);
                    Part(PrimitiveType.Cube, body, new Vector3(0, 0.88f, -0.1f), new Vector3(0.5f, 0.16f, 0.04f), main, false, new Vector3(-20, 0, 0));
                    break;
                case "pirate":
                    Part(PrimitiveType.Sphere, body, new Vector3(0, 1.1f, 0), new Vector3(0.34f, 0.16f, 0.34f), main);
                    Part(PrimitiveType.Cube, body, new Vector3(0, 0.56f, 0.17f), new Vector3(0.34f, 0.06f, 0.04f), accent); // the sash
                    Part(PrimitiveType.Sphere, body, new Vector3(0.06f, 1.05f, 0.15f), Vector3.one * 0.065f, dark); // eye patch
                    break;
            }
            return kid;
        }

        static Vector3 WalkPoint(TownLayout.LifeInfo.Walk w, float u, float side)
        {
            var a = new Vector3(w.from[0], 0f, w.from[1]);
            var b = new Vector3(w.to[0], 0f, w.to[1]);
            var dir = (b - a).normalized;
            var right = new Vector3(dir.z, 0f, -dir.x);
            return Vector3.Lerp(a, b, u) + right * side * w.side + Vector3.up * 0.06f;
        }

        string RumourFor(Group g)
        {
            var game = MysteryGameManager.Instance;
            string house = game != null && game.IsSpawned && game.ActiveHouse.Value.Length > 0 ? game.CaseKey : "";
            g.Said++;
            if (!string.IsNullOrEmpty(house) && g.Said % 2 == 1)
            {
                var r = Cases.For(house).Rumours;
                if (r != null && r.Length > 0) return r[(g.Said / 2 + groups.IndexOf(g)) % r.Length];
            }
            if (life.rumours == null || life.rumours.Length == 0) return "Trick or treat!";
            return life.rumours[(g.Said + groups.IndexOf(g) * 3) % life.rumours.Length];
        }

        internal static string Wrap(string text, int width = 34)
        {
            var words = text.Split(' ');
            var sb = new System.Text.StringBuilder();
            int line = 0;
            foreach (var w in words)
            {
                if (line > 0 && line + w.Length + 1 > width) { sb.Append('\n'); line = 0; }
                else if (line > 0) { sb.Append(' '); line++; }
                sb.Append(w);
                line += w.Length;
            }
            return sb.ToString();
        }

        void UpdateGroups(Camera cam)
        {
            float now = Time.time, dt = Time.deltaTime;
            foreach (var g in groups)
            {
                var a = new Vector3(g.Walk.from[0], 0f, g.Walk.from[1]);
                var b = new Vector3(g.Walk.to[0], 0f, g.Walk.to[1]);
                float length = Mathf.Max(1f, Vector3.Distance(a, b));
                bool near = cam != null && Vector3.Distance(cam.transform.position, g.Root.position) < 8f;
                bool paused = now < g.PauseUntil || near; // they stop to talk to you
                if (!paused)
                {
                    g.U += g.Dir * g.Speed * dt / length;
                    if (g.U > 1f) { g.U = 1f; g.Dir = -1f; }
                    if (g.U < 0f) { g.U = 0f; g.Dir = 1f; }
                    if ((g.NextPause -= dt) <= 0f)
                    {
                        g.PauseUntil = now + 4f; // knock knock: trick or treat!
                        g.NextPause = Random.Range(20f, 45f);
                        g.Bubble.text = "Trick or treat!";
                    }
                }
                var pos = WalkPoint(g.Walk, g.U, g.Side);
                var heading = (b - a).normalized * g.Dir;
                g.Root.SetPositionAndRotation(pos, Quaternion.LookRotation(heading));
                for (int k = 0; k < g.Kids.Count; k++)
                {
                    var kid = g.Kids[k];
                    float t = now * 9f + k * 1.7f;
                    float bob = paused ? Mathf.Sin(now * 2f + k) * 0.01f : Mathf.Abs(Mathf.Sin(t)) * 0.06f;
                    var body = kid.GetChild(0);
                    body.localPosition = Vector3.up * bob;
                    body.localRotation = Quaternion.Euler(0f, 0f, paused ? 0f : Mathf.Sin(t * 0.5f) * 5f);
                    if (paused && cam != null)
                    {
                        // Turn to face whoever they're talking to.
                        var to = cam.transform.position - kid.position;
                        to.y = 0f;
                        if (to.sqrMagnitude > 0.01f && near) kid.rotation = Quaternion.Slerp(kid.rotation, Quaternion.LookRotation(to), 1f - Mathf.Exp(-6f * dt));
                    }
                    else kid.localRotation = Quaternion.Slerp(kid.localRotation, Quaternion.identity, 1f - Mathf.Exp(-6f * dt));
                }

                if (near && !g.Near) g.Bubble.text = Wrap(RumourFor(g));
                g.Near = near;
                bool show = near || now < g.PauseUntil;
                if (g.Bubble.gameObject.activeSelf != show) g.Bubble.gameObject.SetActive(show);
                if (show && cam != null) g.Bubble.transform.rotation = Quaternion.LookRotation(g.Bubble.transform.position - cam.transform.position);
            }
        }

        // ---- Cars on the roads out of town ----

        Transform BuildCar(Color paint)
        {
            var car = new GameObject("Car").transform;
            car.SetParent(transform, false);
            Part(PrimitiveType.Cube, car, new Vector3(0, 0.55f, 0), new Vector3(1.8f, 0.7f, 4.2f), paint);
            Part(PrimitiveType.Cube, car, new Vector3(0, 1.1f, -0.3f), new Vector3(1.6f, 0.55f, 2.2f), paint * 0.8f);
            Part(PrimitiveType.Cube, car, new Vector3(0, 1.1f, -0.3f), new Vector3(1.62f, 0.4f, 2.0f), new Color(0.35f, 0.4f, 0.5f));
            var head = new Color(1f, 0.92f, 0.7f);
            var tail = new Color(1f, 0.15f, 0.1f);
            for (int s = -1; s <= 1; s += 2)
            {
                Part(PrimitiveType.Sphere, car, new Vector3(s * 0.6f, 0.6f, 2.1f), new Vector3(0.3f, 0.22f, 0.1f), head, true);
                Part(PrimitiveType.Sphere, car, new Vector3(s * 0.65f, 0.65f, -2.1f), new Vector3(0.28f, 0.16f, 0.08f), tail, true);
                Part(PrimitiveType.Cylinder, car, new Vector3(s * 0.85f, 0.3f, 1.3f), new Vector3(0.55f, 0.12f, 0.55f), new Color(0.08f, 0.08f, 0.08f), false, new Vector3(0, 0, 90));
                Part(PrimitiveType.Cylinder, car, new Vector3(s * 0.85f, 0.3f, -1.3f), new Vector3(0.55f, 0.12f, 0.55f), new Color(0.08f, 0.08f, 0.08f), false, new Vector3(0, 0, 90));
            }
            return car;
        }

        void UpdateCars()
        {
            float dt = Time.deltaTime;
            foreach (var car in cars)
            {
                var a = new Vector3(car.Road.from[0], 0f, car.Road.from[1]);
                var b = new Vector3(car.Road.to[0], 0f, car.Road.to[1]);
                float length = Mathf.Max(1f, Vector3.Distance(a, b));
                car.U += car.Speed * dt / length;
                if (car.U > 1f) car.U -= 1f; // gone over the hill; another one comes along
                // Incoming cars drive from the far end towards town and turn off just before it.
                Vector3 start = car.Incoming ? b : a, end = car.Incoming ? a + (b - a).normalized * 25f : b;
                var dir = (end - start).normalized;
                var right = new Vector3(dir.z, 0f, -dir.x);
                car.T.SetPositionAndRotation(Vector3.Lerp(start, end, car.U) + right * 2f, Quaternion.LookRotation(dir));
                // Grow in and shrink out at the ends of the trip, so nobody sees a car pop into being.
                float ends = Mathf.Clamp01(Mathf.Min(car.U, 1f - car.U) / 0.02f);
                car.T.localScale = Vector3.one * ends;
            }
        }

        // ---- The train across the valley (follows the camera like the hills) ----

        /// <summary>The train is drawn a little larger than life so it reads at this distance (render3d.py matches).</summary>
        const float TrainScale = 1.7f;

        void BuildTrain(TownLayout.LifeInfo.Train t)
        {
            trainSky = new GameObject("FarTrain").transform;
            trainSky.SetParent(transform, false);
            train = new GameObject("Train").transform;
            train.SetParent(trainSky, false);
            var b = new Horizon.MeshBuilder();
            Color body = new(0.07f, 0.06f, 0.1f), window = new(1f, 0.82f, 0.5f), lamp = new(1f, 0.95f, 0.8f);
            float step = 2.0f * 540f / t.radius, carSpan = step * 0.88f;
            for (int i = 0; i < t.cars; i++)
            {
                float a0 = -i * step, a1 = a0 - carSpan;
                float y0 = t.y, y1 = t.y + (i == 0 ? 5.2f : 4.4f) * TrainScale;
                b.Quad(Horizon.OnRing(t.radius, a0, y0), Horizon.OnRing(t.radius, a1, y0), Horizon.OnRing(t.radius, a1, y1), Horizon.OnRing(t.radius, a0, y1), body, body, body, body);
                if (i == 0)
                {
                    // The engine: a bright lamp at the front and a smokestack.
                    float la = a0 - 0.08f;
                    b.Quad(Horizon.OnRing(t.radius - 0.5f, la, y0 + 2.2f * TrainScale), Horizon.OnRing(t.radius - 0.5f, la - 0.2f, y0 + 2.2f * TrainScale),
                           Horizon.OnRing(t.radius - 0.5f, la - 0.2f, y0 + 3.4f * TrainScale), Horizon.OnRing(t.radius - 0.5f, la, y0 + 3.4f * TrainScale), lamp, lamp, lamp, lamp);
                    float sa = a0 - carSpan * 0.3f;
                    b.Quad(Horizon.OnRing(t.radius, sa, y1), Horizon.OnRing(t.radius, sa - 0.25f, y1), Horizon.OnRing(t.radius, sa - 0.25f, y1 + 2f * TrainScale), Horizon.OnRing(t.radius, sa, y1 + 2f * TrainScale), body, body, body, body);
                    continue;
                }
                for (int w = 0; w < 4; w++)
                {
                    float wa = a0 - carSpan * (0.12f + w * 0.22f);
                    var c = w == (i * 7) % 5 ? window * 0.45f : window; // one window dark here and there
                    c.a = 1f;
                    b.Quad(Horizon.OnRing(t.radius - 0.5f, wa, y0 + 1.6f * TrainScale), Horizon.OnRing(t.radius - 0.5f, wa - carSpan * 0.13f, y0 + 1.6f * TrainScale),
                           Horizon.OnRing(t.radius - 0.5f, wa - carSpan * 0.13f, y0 + 3.3f * TrainScale), Horizon.OnRing(t.radius - 0.5f, wa, y0 + 3.3f * TrainScale), c, c, c, c);
                }
            }
            var go = train.gameObject;
            go.AddComponent<MeshFilter>().mesh = b.ToMesh("Train");
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = new Material(Shader.Find("Sprites/Default")) { name = "TrainUnlit" };
            mr.sortingOrder = 55; // in front of the far lights, behind the valley mist
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            trainStart = Time.time;
        }

        void UpdateTrain(Camera cam)
        {
            if (train == null) return;
            var t = life.train;
            if (cam != null)
            {
                var p = cam.transform.position;
                trainSky.position = new Vector3(p.x, 0f, p.z);
            }
            float span = Mathf.Abs(t.to - t.from) + t.cars * 2.2f;
            float cycle = span / Mathf.Max(0.1f, t.speed) + 25f; // then a pause before the next train
            float k = ((Time.time - trainStart) % cycle) * t.speed;
            bool running = k <= span;
            if (train.gameObject.activeSelf != running) train.gameObject.SetActive(running);
            train.localRotation = Quaternion.Euler(0f, t.from + k * Mathf.Sign(t.to - t.from), 0f);
        }

        void LateUpdate()
        {
            var cam = Camera.main;
            UpdateGroups(cam);
            UpdateCars();
            UpdateTrain(cam);
        }
    }
}
