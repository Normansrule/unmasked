using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The lamplighter (round 38). Twelve old gas lamps stand along the creek bank beside the
    /// Creekside Path, six each side of the bridge, and nobody has lit them in years. Tobias Wick
    /// still waits on his bench by the bridge every Halloween with his lighting pole, but his knees
    /// won't do the bank any more. Talk to him and he lends you the pole; walk the path and press E
    /// at each dark lamp to light it. A lit lamp stays lit from then on (your Club Book keeps them),
    /// and when all twelve burn, bring the pole back: he gives you his spare cap, a Wardrobe look
    /// you can't buy. With the whole path lit the creek's wisps come round a little more often.
    ///
    /// Like the Hook Board it all happens on your own computer (ILocalInteractable), so nobody can
    /// light your lamps for you, and there's no clock on it: any night, as many nights as you like.
    /// Tobias is built from Costumes.json "Folk.Lamplighter" (Docs/tools/make_costumes.py).
    /// </summary>
    public class Lamplighter : MonoBehaviour, ILocalInteractable
    {
        /// <summary>Where the lamps stand along the bank (x), six west and six east of the bridge.</summary>
        public static readonly float[] LampX = { -138f, -114f, -90f, -66f, -42f, -18f, 18f, 36f, 54f, 72f, 90f, 108f };
        public const int Lamps = 12;
        /// <summary>The lamps stand on the bank this far north of the creek's middle, just off the path.</summary>
        public const float BankZ = 9f;
        /// <summary>Tobias and his bench, at the west end of the bridge, just north of the path.</summary>
        public static readonly Vector3 HomeOffset = new(-10.5f, 0f, 13.3f);

        public static Lamplighter Instance { get; private set; }
        /// <summary>Is the local player carrying the lighting pole?</summary>
        public static bool Carrying { get; private set; }
        public static int Lit => ClubBook.CreekLampsLit;
        public static bool AllLit => Lit >= Lamps;
        public Vector3 HeadPoint => transform.position + Vector3.up * 2.0f;

        static readonly string[] Stories =
        {
            "The Lantern Watch walked this bank every night in 1823. Twenty-four lanterns. I only ever had the twelve lamps, mind.",
            "Wisps don't care for a lit path. They come and look at it all the same. Curious things.",
            "My grandmother said the mist can't climb past a lamp that's been lit with care. I've never seen it try.",
            "Nell Thistle says I'll outlive these lamps. I tell her the lamps will outlive the both of us.",
            "Mind the third lamp past the bridge. It's been sulking since 1974.",
            "Gas lamps want a steady hand and a bit of patience. Same as people, really.",
        };

        readonly CreekLamp[] lamps = new CreekLamp[Lamps];
        Transform turn, poleHome, carried;
        FaceLife face;
        TextMesh bubble;
        float bubbleUntil, nextTalk, poseUntil;
        Vector3 poseAt;
        int story;

        /// <summary>Called by TownDirector: the twelve lamps and Tobias, once.</summary>
        public static void Ensure(GameObject host)
        {
            var town = TownLayout.Current;
            if (town == null || host.transform.Find("CreeksideLamps") != null) return;
            var root = new GameObject("CreeksideLamps").transform;
            root.SetParent(host.transform, false);
            float z = town.creekZ + BankZ;
            var m = CreekLamp.Materials.Make();
            for (int i = 0; i < Lamps; i++)
            {
                var go = new GameObject("CreekLamp_" + (i + 1));
                go.transform.SetParent(root, false);
                // On the creek side of the path, facing it, so the lamp head hangs over the walkers.
                go.transform.SetPositionAndRotation(new Vector3(LampX[i], 0f, z), Quaternion.identity);
                var lamp = go.AddComponent<CreekLamp>();
                lamp.Index = i;
                lamp.Build(m);
            }
            var tobias = new GameObject("Lamplighter");
            tobias.transform.SetParent(root, false);
            tobias.transform.SetPositionAndRotation(new Vector3(HomeOffset.x, 0f, town.creekZ + HomeOffset.z), Quaternion.Euler(0f, 160f, 0f));
            var lamplighter = tobias.AddComponent<Lamplighter>();
            foreach (var l in root.GetComponentsInChildren<CreekLamp>()) lamplighter.lamps[l.Index] = l;
            lamplighter.Build();
        }

        void Awake() => Instance = this;
        void OnDestroy()
        {
            if (Instance == this) Instance = null;
            Carrying = false;
        }

        void Build()
        {
            var solid = gameObject.AddComponent<CapsuleCollider>();
            solid.center = new Vector3(0f, 1f, 0f);
            solid.height = 2f;
            solid.radius = 0.4f;

            turn = new GameObject("Turn").transform;
            turn.SetParent(transform, false);
            var model = new GameObject("Model").transform;
            model.SetParent(turn, false);
            var parts = Costumes.FindOutfit(Costumes.Current?.suspects, "Folk.Lamplighter");
            if (parts != null) BuildParts(model, parts);
            else Shape(model, PrimitiveType.Capsule, new Vector3(0f, 1f, 0f), new Vector3(0.7f, 1f, 0.7f), Vector3.zero, Mat(new Color(0.35f, 0.2f, 0.28f), false));
            face = gameObject.AddComponent<FaceLife>();

            // His bench, behind him, and the pole leaning in his right hand.
            var wood = Mat(new Color(0.36f, 0.24f, 0.15f), false);
            var iron = Mat(new Color(0.12f, 0.12f, 0.14f), false);
            var bench = new GameObject("Bench").transform;
            bench.SetParent(transform, false);
            bench.localPosition = new Vector3(0f, 0f, -1.1f);
            Shape(bench, PrimitiveType.Cube, new Vector3(0f, 0.45f, 0f), new Vector3(1.6f, 0.06f, 0.45f), Vector3.zero, wood);
            Shape(bench, PrimitiveType.Cube, new Vector3(0f, 0.78f, -0.2f), new Vector3(1.6f, 0.3f, 0.05f), new Vector3(-10f, 0f, 0f), wood);
            for (int s = -1; s <= 1; s += 2)
                Shape(bench, PrimitiveType.Cube, new Vector3(s * 0.7f, 0.22f, 0f), new Vector3(0.06f, 0.44f, 0.4f), Vector3.zero, iron);
            var benchSolid = bench.gameObject.AddComponent<BoxCollider>();
            benchSolid.center = new Vector3(0f, 0.45f, 0f);
            benchSolid.size = new Vector3(1.6f, 0.9f, 0.5f);

            poleHome = new GameObject("PoleHome").transform;
            poleHome.SetParent(turn, false);
            poleHome.localPosition = new Vector3(0.47f, 0.04f, 0.06f);
            poleHome.localRotation = Quaternion.Euler(4f, 0f, -3f);
            BuildPole(poleHome);

            bubble = Horizon.MakeText(transform, "", new Vector3(0f, 2.75f, 0f), 0.03f, new Color(1f, 0.93f, 0.75f));
            bubble.gameObject.SetActive(false);
        }

        /// <summary>The lighting pole: a long ash pole, a brass hook to open the lamp's little door and a wick that burns at the top.</summary>
        static Transform BuildPole(Transform parent)
        {
            var pole = new GameObject("LightingPole").transform;
            pole.SetParent(parent, false);
            var ash = Mat(new Color(0.55f, 0.42f, 0.28f), false);
            var brass = Mat(new Color(0.85f, 0.68f, 0.32f), false);
            Shape(pole, PrimitiveType.Cylinder, new Vector3(0f, 1.42f, 0f), new Vector3(0.045f, 1.42f, 0.045f), Vector3.zero, ash);
            Shape(pole, PrimitiveType.Cylinder, new Vector3(0f, 2.86f, 0f), new Vector3(0.06f, 0.05f, 0.06f), Vector3.zero, brass);
            Shape(pole, PrimitiveType.Cube, new Vector3(0.05f, 2.98f, 0f), new Vector3(0.1f, 0.025f, 0.025f), Vector3.zero, brass);
            Shape(pole, PrimitiveType.Cube, new Vector3(0.1f, 2.94f, 0f), new Vector3(0.025f, 0.08f, 0.025f), Vector3.zero, brass);
            Shape(pole, PrimitiveType.Cylinder, new Vector3(-0.03f, 2.96f, 0f), new Vector3(0.02f, 0.06f, 0.02f), Vector3.zero, brass);
            var flame = Shape(pole, PrimitiveType.Sphere, new Vector3(-0.03f, 3.05f, 0f), new Vector3(0.05f, 0.08f, 0.05f), Vector3.zero, Mat(new Color(1f, 0.72f, 0.3f), true));
            var light = flame.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = new Color(1f, 0.75f, 0.42f);
            light.range = 3f;
            light.intensity = 0.8f;
            light.shadows = LightShadows.None;
            var flicker = flame.AddComponent<CandleFlicker>();
            flicker.Amount = 0.3f;
            flicker.Speed = 9f;
            flicker.CullDistance = 50f;
            return pole;
        }

        void Update()
        {
            // Turn towards whoever comes close; otherwise look out over the creek.
            var me = SolverController.Local;
            Vector3 look = transform.forward;
            if (Time.time < poseUntil) look = poseAt - transform.position;
            else if (me != null && (me.transform.position - transform.position).sqrMagnitude < 36f) look = me.transform.position - transform.position;
            look.y = 0f;
            if (look.sqrMagnitude > 0.01f)
                turn.rotation = Quaternion.Slerp(turn.rotation, Quaternion.LookRotation(look), 1f - Mathf.Exp(-3f * Time.deltaTime));
            // An old man's breathing.
            turn.localScale = new Vector3(1f, 1f + Mathf.Sin(Time.time * 1.6f) * 0.006f, 1f);

            if (bubble.gameObject.activeSelf && Time.time > bubbleUntil) bubble.gameObject.SetActive(false);

            // The pole goes with you, and back to him.
            if (Carrying && me != null)
            {
                if (carried == null)
                {
                    var hold = new GameObject("CarriedPole").transform;
                    hold.SetParent(me.transform, false);
                    hold.localPosition = new Vector3(0.42f, 0.25f, 0.3f);
                    hold.localRotation = Quaternion.Euler(14f, 0f, -6f);
                    BuildPole(hold);
                    carried = hold;
                }
                carried.gameObject.SetActive(!me.IsRiding);
            }
            poleHome.gameObject.SetActive(!Carrying);
            if (!Carrying && carried != null) { Destroy(carried.gameObject); carried = null; }
        }

        /// <summary>The club camera points at him: he turns and smiles.</summary>
        public void Pose(Vector3 from)
        {
            poseAt = from;
            poseUntil = Time.time + 3f;
            face?.Feel(FaceLife.Mood.Happy, 3f);
        }

        // ---- IInteractable -------------------------------------------------------------------------

        public bool CanInteract(SolverController solver) => solver != null && !solver.IsRiding && Time.time >= nextTalk;

        public string GetPrompt(SolverController solver)
        {
            if (Carrying) return AllLit ? "Give Tobias his pole back" : "Talk to Tobias Wick";
            return AllLit ? "Talk to Tobias Wick" : "Talk to Tobias Wick, the lamplighter";
        }

        /// <summary>No NetworkObject, so this never runs.</summary>
        public void Interact(SolverController solver) { }

        public void LocalInteract(SolverController solver)
        {
            if (Time.time < nextTalk) return;
            nextTalk = Time.time + 1f;
            int lit = Lit;
            if (Carrying && AllLit)
            {
                Carrying = false;
                bool first = ClubBook.ThankLamplighter();
                face.Feel(FaceLife.Mood.Happy, 5f);
                Say(first
                    ? "Look at that: the whole creek lit end to end, like when the Watch walked it. Keep the cap, it's my spare. And I'll have my pole back, thank you kindly."
                    : "Thank you. I'll keep her by the bench. The lamps will keep themselves now.");
                Sfx.Play("clue_chime", transform.position, 0.6f, 14f, 1.1f);
            }
            else if (Carrying)
            {
                face.Feel(FaceLife.Mood.Calm, 1f);
                int left = Lamps - lit;
                Say(lit == 0
                    ? "Hook the little door open and touch the wick. Six lamps this side of the bridge, six the other."
                    : $"{lit} of {Lamps} lit. {left} to go{(left <= 3 ? ". The far ones out past the fields always get forgotten." : ".")}");
            }
            else if (!AllLit)
            {
                Carrying = true;
                face.Feel(lit == 0 ? FaceLife.Mood.Worried : FaceLife.Mood.Happy, 3f);
                Say(lit == 0 && !ClubBook.Has("lamplighter:met")
                    ? "Evening. Tobias Wick. I've lit the creek lamps every Halloween since I was your age, but my knees won't do the bank tonight. Take my pole? Twelve lamps, six each side of the bridge."
                    : $"Back for the pole? {Lamps - lit} still dark. Off you go, and mind the bank.");
                ClubBook.MetLamplighter();
                Sfx.Play("knock", transform.position, 0.4f, 10f, 1.6f);
            }
            else
            {
                face.Feel(FaceLife.Mood.Happy, 3f);
                Say(Stories[story++ % Stories.Length]);
            }
        }

        void Say(string line)
        {
            bubble.text = Wrap(line, 36);
            bubble.gameObject.SetActive(true);
            bubbleUntil = Time.time + 7f;
            face?.Talk(Mathf.Clamp(line.Length * 0.045f, 1.2f, 5f));
            GameHUD.Toast("Tobias Wick: " + line);
        }

        /// <summary>A lamp was just lit: he gives a little cheer from the bench if you're near.</summary>
        internal void Cheer(int lit)
        {
            if (AllLit)
                GameHUD.Toast("All twelve creekside lamps are lit. Take the pole back to Tobias by the bridge.");
            else if (SolverController.Local != null && (SolverController.Local.transform.position - transform.position).sqrMagnitude < 400f)
                face.Feel(FaceLife.Mood.Happy, 2f);
        }

        internal static string Wrap(string s, int width)
        {
            var sb = new System.Text.StringBuilder();
            int col = 0;
            foreach (var word in s.Split(' '))
            {
                if (col > 0 && col + word.Length > width) { sb.Append('\n'); col = 0; }
                else if (col > 0) { sb.Append(' '); col++; }
                sb.Append(word);
                col += word.Length;
            }
            return sb.ToString();
        }

        // ---- Building shapes at runtime ------------------------------------------------------------

        static readonly Dictionary<string, Material> mats = new();

        internal static Material Mat(Color c, bool glow)
        {
            string key = ColorUtility.ToHtmlStringRGB(c) + (glow ? "g" : "");
            if (!mats.TryGetValue(key, out var m) || m == null) mats[key] = m = Horizon.Lit("Lamplighter_" + key, c, glow);
            return m;
        }

        internal static GameObject Shape(Transform parent, PrimitiveType type, Vector3 pos, Vector3 scale, Vector3 euler, Material mat, string name = null)
        {
            var go = GameObject.CreatePrimitive(type);
            if (name != null) go.name = name;
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localEulerAngles = euler;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
            return go;
        }

        /// <summary>A Costumes.json outfit, built the way the editor builds the townsfolk (TestRoomBuilder.BuildParts).</summary>
        static void BuildParts(Transform parent, Costumes.Part[] parts)
        {
            int first = parent.childCount;
            foreach (var q in parts)
            {
                var type = q.t switch { "cyl" or "rcyl" => PrimitiveType.Cylinder, "capsule" => PrimitiveType.Capsule, "sphere" => PrimitiveType.Sphere, _ => PrimitiveType.Cube };
                bool glow = q.m == "emissive" || q.m == "ghost";
                var go = Shape(parent, type, ManorLayout.V(q.p), ManorLayout.V(q.s), ManorLayout.V(q.r), Mat(ManorLayout.C(q.c), glow), q.n);
                if (glow) go.GetComponent<Renderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                if (q.t == "rbox") go.AddComponent<SoftBox>();
                if (q.t == "rcyl") go.AddComponent<SoftBox>().Cylinder = true;
            }
            SmoothBody.Attach(parent, parts, first); // round 45: one smooth skin, as the townsfolk have
        }
    }

    /// <summary>
    /// One of the twelve gas lamps on the Creekside Path (Lamplighter.cs): a fluted iron post with a
    /// ladder bar, a four-paned lantern head with a little pitched cap and a finial. Dark, it shows
    /// only a blue pilot flame; lit, the glass glows amber, a warm pool of light falls on the path,
    /// and a couple of moths come to circle it.
    /// </summary>
    public class CreekLamp : MonoBehaviour, ILocalInteractable
    {
        public int Index;

        internal class Materials
        {
            public Material Iron, IronDark, GlassDark, GlassLit, Pilot, Flame, Moth;
            public static Materials Make() => new()
            {
                Iron = Lamplighter.Mat(new Color(0.16f, 0.17f, 0.18f), false),
                IronDark = Lamplighter.Mat(new Color(0.09f, 0.1f, 0.11f), false),
                GlassDark = Lamplighter.Mat(new Color(0.18f, 0.24f, 0.27f), false),
                GlassLit = Lamplighter.Mat(new Color(1f, 0.76f, 0.4f), true),
                Pilot = Lamplighter.Mat(new Color(0.35f, 0.6f, 1f), true),
                Flame = Lamplighter.Mat(new Color(1f, 0.85f, 0.5f), true),
                Moth = Lamplighter.Mat(new Color(0.75f, 0.7f, 0.6f), false),
            };
        }

        public const float HeadY = 3.25f;

        Materials m;
        readonly List<Renderer> glass = new();
        Transform flame;
        Light glow;
        Transform[] moths;
        bool lit, busy;

        public bool IsLit => lit;
        public Vector3 HeadPoint => transform.position + transform.forward * 0.35f + Vector3.up * HeadY;

        internal void Build(Materials mats)
        {
            m = mats;
            var t = transform;
            // Solid post you bump into, and a trigger the camera finds when you look at the lamp.
            var post = gameObject.AddComponent<BoxCollider>();
            post.center = new Vector3(0f, 1.6f, 0f);
            post.size = new Vector3(0.3f, 3.2f, 0.3f);
            var hit = gameObject.AddComponent<BoxCollider>();
            hit.isTrigger = true;
            hit.center = new Vector3(0f, 1.8f, 0.2f);
            hit.size = new Vector3(1.2f, 3.6f, 1.2f);

            // Base, fluted post, ladder bar.
            Lamplighter.Shape(t, PrimitiveType.Cylinder, new Vector3(0f, 0.12f, 0f), new Vector3(0.42f, 0.12f, 0.42f), Vector3.zero, m.IronDark);
            Lamplighter.Shape(t, PrimitiveType.Cylinder, new Vector3(0f, 0.32f, 0f), new Vector3(0.3f, 0.1f, 0.3f), Vector3.zero, m.Iron);
            Lamplighter.Shape(t, PrimitiveType.Cylinder, new Vector3(0f, 1.6f, 0f), new Vector3(0.12f, 1.3f, 0.12f), Vector3.zero, m.Iron);
            for (int i = 0; i < 4; i++)
            {
                float a = i * Mathf.PI / 2f + Mathf.PI / 4f;
                Lamplighter.Shape(t, PrimitiveType.Cube, new Vector3(Mathf.Cos(a) * 0.075f, 0.95f, Mathf.Sin(a) * 0.075f), new Vector3(0.035f, 1.1f, 0.035f), new Vector3(0f, -a * Mathf.Rad2Deg, 0f), m.IronDark);
            }
            Lamplighter.Shape(t, PrimitiveType.Cylinder, new Vector3(0f, 1.55f, 0f), new Vector3(0.17f, 0.04f, 0.17f), Vector3.zero, m.IronDark);
            Lamplighter.Shape(t, PrimitiveType.Cube, new Vector3(0f, 2.75f, 0f), new Vector3(0.7f, 0.05f, 0.05f), Vector3.zero, m.Iron);
            for (int s = -1; s <= 1; s += 2)
                Lamplighter.Shape(t, PrimitiveType.Sphere, new Vector3(s * 0.36f, 2.75f, 0f), Vector3.one * 0.08f, Vector3.zero, m.IronDark);

            // A curled arm out over the path, and the lantern head on it.
            Lamplighter.Shape(t, PrimitiveType.Cylinder, new Vector3(0f, 2.95f, 0f), new Vector3(0.09f, 0.1f, 0.09f), Vector3.zero, m.IronDark);
            Lamplighter.Shape(t, PrimitiveType.Cube, new Vector3(0f, 3.06f, 0.18f), new Vector3(0.05f, 0.05f, 0.4f), Vector3.zero, m.Iron);
            Lamplighter.Shape(t, PrimitiveType.Cylinder, new Vector3(0f, 3.0f, 0.36f), new Vector3(0.05f, 0.05f, 0.05f), new Vector3(90f, 0f, 0f), m.Iron);
            var head = new GameObject("Head").transform;
            head.SetParent(t, false);
            head.localPosition = new Vector3(0f, HeadY - 0.15f, 0.35f);
            Lamplighter.Shape(head, PrimitiveType.Cylinder, new Vector3(0f, -0.04f, 0f), new Vector3(0.3f, 0.03f, 0.3f), Vector3.zero, m.Iron);
            glass.Add(Lamplighter.Shape(head, PrimitiveType.Cube, new Vector3(0f, 0.2f, 0f), new Vector3(0.3f, 0.42f, 0.3f), new Vector3(0f, 45f, 0f), m.GlassDark).GetComponent<Renderer>());
            for (int i = 0; i < 4; i++)
            {
                float a = i * Mathf.PI / 2f;
                Lamplighter.Shape(head, PrimitiveType.Cube, new Vector3(Mathf.Cos(a) * 0.215f, 0.2f, Mathf.Sin(a) * 0.215f), new Vector3(0.025f, 0.46f, 0.025f), Vector3.zero, m.IronDark);
            }
            Lamplighter.Shape(head, PrimitiveType.Cylinder, new Vector3(0f, 0.44f, 0f), new Vector3(0.38f, 0.035f, 0.38f), Vector3.zero, m.Iron);
            Lamplighter.Shape(head, PrimitiveType.Cylinder, new Vector3(0f, 0.5f, 0f), new Vector3(0.26f, 0.04f, 0.26f), Vector3.zero, m.Iron);
            Lamplighter.Shape(head, PrimitiveType.Cylinder, new Vector3(0f, 0.56f, 0f), new Vector3(0.14f, 0.04f, 0.14f), Vector3.zero, m.Iron);
            Lamplighter.Shape(head, PrimitiveType.Sphere, new Vector3(0f, 0.64f, 0f), new Vector3(0.07f, 0.1f, 0.07f), Vector3.zero, m.IronDark);
            flame = Lamplighter.Shape(head, PrimitiveType.Sphere, new Vector3(0f, 0.14f, 0f), new Vector3(0.05f, 0.07f, 0.05f), Vector3.zero, m.Pilot).transform;

            glow = new GameObject("Glow").AddComponent<Light>();
            glow.transform.SetParent(head, false);
            glow.transform.localPosition = new Vector3(0f, 0.15f, 0.2f);
            glow.type = LightType.Point;
            glow.color = new Color(1f, 0.78f, 0.46f);
            glow.range = 10f;
            glow.intensity = 1.25f;
            glow.shadows = LightShadows.None;
            var flicker = glow.gameObject.AddComponent<CandleFlicker>();
            flicker.Amount = 0.1f;
            flicker.Speed = 4f;
            flicker.CullDistance = 80f;
            glow.gameObject.SetActive(false);

            moths = new Transform[2];
            for (int i = 0; i < moths.Length; i++)
            {
                moths[i] = Lamplighter.Shape(head, PrimitiveType.Sphere, Vector3.zero, new Vector3(0.05f, 0.012f, 0.03f), Vector3.zero, m.Moth).transform;
                moths[i].gameObject.SetActive(false);
            }

            Show(ClubBook.CreekLampLit(Index), 1f);
        }

        void Show(bool on, float k)
        {
            lit = on;
            foreach (var r in glass) r.sharedMaterial = on ? m.GlassLit : m.GlassDark;
            flame.GetComponent<Renderer>().sharedMaterial = on ? m.Flame : m.Pilot;
            flame.localScale = on ? new Vector3(0.08f, 0.14f, 0.08f) * Mathf.Max(0.3f, k) : new Vector3(0.05f, 0.07f, 0.05f);
            glow.gameObject.SetActive(on);
            foreach (var moth in moths) moth.gameObject.SetActive(on);
        }

        void Update()
        {
            if (!lit || moths == null) return;
            var cam = Camera.main;
            if (cam != null && (cam.transform.position - transform.position).sqrMagnitude > 1600f) return;
            float t = Time.time;
            for (int i = 0; i < moths.Length; i++)
            {
                float a = t * (2.2f + i * 0.7f) + Index * 1.7f + i * 3f;
                moths[i].localPosition = new Vector3(Mathf.Cos(a) * (0.32f + 0.05f * i), 0.25f + Mathf.Sin(a * 1.7f) * 0.12f, Mathf.Sin(a) * (0.32f + 0.05f * i));
                moths[i].localRotation = Quaternion.Euler(0f, -a * Mathf.Rad2Deg, Mathf.Sin(t * 30f + i) * 40f); // wings a-flutter
            }
        }

        // ---- IInteractable -------------------------------------------------------------------------

        public bool CanInteract(SolverController solver) => !lit && !busy && solver != null && !solver.IsRiding;

        public string GetPrompt(SolverController solver) => Lamplighter.Carrying ? "Light the gas lamp" : "A cold gas lamp";

        /// <summary>No NetworkObject, so this never runs.</summary>
        public void Interact(SolverController solver) { }

        public void LocalInteract(SolverController solver)
        {
            if (lit || busy) return;
            if (!Lamplighter.Carrying)
            {
                GameHUD.Toast("Too high to reach, and the little door is stiff. Old Tobias Wick on his bench by the bridge has a lighting pole.");
                return;
            }
            StartCoroutine(LightUp());
        }

        IEnumerator LightUp()
        {
            busy = true;
            int lit = ClubBook.CreekLampsLit;
            Sfx.Play("knock", HeadPoint, 0.3f, 10f, 2.2f); // the little door clicks open
            yield return new WaitForSeconds(0.25f);
            Show(true, 0.3f);
            float target = glow.intensity;
            var flicker = glow.GetComponent<CandleFlicker>();
            if (flicker != null) flicker.enabled = false;
            Sfx.Play("clue_chime", HeadPoint, 0.55f, 16f, 1.2f + 0.05f * lit);
            for (float u = 0f; u < 1f; u += Time.deltaTime / 0.8f)
            {
                float k = Mathf.SmoothStep(0f, 1f, u);
                glow.intensity = target * (k + Mathf.Sin(u * 18f) * 0.15f * (1f - k)); // it catches, sputters, settles
                flame.localScale = new Vector3(0.08f, 0.14f, 0.08f) * Mathf.Lerp(0.3f, 1f, k);
                yield return null;
            }
            glow.intensity = target;
            if (flicker != null) flicker.enabled = true;
            ClubBook.LitCreekLamp(Index);
            Lamplighter.Instance?.Cheer(ClubBook.CreekLampsLit);
            busy = false;
        }
    }
}
