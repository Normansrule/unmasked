using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Haunts to bust (round 42). Twelve one-of-a-kind buildings in Hollow Creek (HollowCreek.json
    /// "haunts", built by Docs/tools/haunts.py) each have a ghost of their own: the Projectionist at
    /// the Bijou, the Flour Phantom at Crumb &amp; Co., the Clockwinder up on Town Hall.
    ///
    /// A bust, start to finish:
    ///   1. Three faint violet signs of the haunt wait round the building. Press E on each to read it.
    ///   2. With all three found, the ghost shows itself in front of the building.
    ///   3. Get close and press E to catch it. It slips away to another spot twice; the third catch
    ///      busts it. The sheet comes off, the haunt turns out to be something silly and sweet, and
    ///      the building's sign glows warm from then on. +20 candy, and the Club Book counts it.
    ///
    /// Like the curiosities it all happens on your own computer (ILocalInteractable), and a busted
    /// haunt stays busted ("haunt:id" in the Club Book). Signs found along the way are remembered too.
    /// </summary>
    public class HauntBust : MonoBehaviour
    {
        /// <summary>How many haunts there are (casecheck makes sure HollowCreek.json agrees).</summary>
        public const int Total = 12;
        public static readonly List<HauntBust> All = new();

        public TownLayout.HauntInfo Info;
        readonly List<HauntSignSpot> signs = new();
        HauntGhost ghost;

        public bool Busted => ClubBook.HasHaunt(Info.id);
        public int SignsFound { get { int n = 0; foreach (var s in signs) if (s.Found) n++; return n; } }

        /// <summary>Called by TownDirector: one bust for every haunt in the layout.</summary>
        public static void Ensure(GameObject host)
        {
            var town = TownLayout.Current;
            if (town?.haunts == null || host.transform.Find("Haunts") != null) return;
            var root = new GameObject("Haunts").transform;
            root.SetParent(host.transform, false);
            foreach (var h in town.haunts)
            {
                if (h?.signs == null || h.hide == null || h.hide.Length < 9) continue;
                var go = new GameObject("Haunt_" + h.id);
                go.transform.SetParent(root, false);
                var bust = go.AddComponent<HauntBust>();
                bust.Info = h;
                bust.Build();
            }
        }

        void OnEnable() => All.Add(this);
        void OnDisable() => All.Remove(this);

        static readonly Dictionary<string, Material> mats = new();

        internal static Material M(Color c, bool glow, string key)
        {
            if (mats.TryGetValue(key, out var m) && m != null) return m;
            return mats[key] = Horizon.Lit("Haunt" + key, c, glow);
        }

        internal static void Part(Transform parent, PrimitiveType type, Vector3 pos, Vector3 scale, Material mat, Vector3 euler = default)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localRotation = Quaternion.Euler(euler);
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
        }

        internal Vector3 Hide(int i)
        {
            i = Mathf.Clamp(i, 0, Info.hide.Length / 3 - 1);
            return new Vector3(Info.hide[i * 3], Info.hide[i * 3 + 1], Info.hide[i * 3 + 2]);
        }

        void Build()
        {
            for (int i = 0; i < Info.signs.Length; i++)
            {
                var s = Info.signs[i];
                if (s?.p == null || s.p.Length < 3) continue;
                var go = new GameObject($"Sign{i}");
                go.transform.SetParent(transform, false);
                go.transform.position = new Vector3(s.p[0], s.p[1], s.p[2]);
                var spot = go.AddComponent<HauntSignSpot>();
                spot.Init(this, i, s);
                signs.Add(spot);
            }
            var g = new GameObject("Ghost");
            g.transform.SetParent(transform, false);
            g.transform.position = Hide(0);
            ghost = g.AddComponent<HauntGhost>();
            ghost.Init(this);
            Refresh();
        }

        /// <summary>A sign was read: once all three are found the ghost appears.</summary>
        internal void SignRead(HauntSignSpot spot, bool first)
        {
            int found = SignsFound;
            if (first && found < signs.Count)
                GameHUD.Toast($"{spot.Title}. {spot.Lore} (Sign {found} of {signs.Count} at {Info.n}.)");
            else if (first)
            {
                GameHUD.Toast($"{spot.Title}. {spot.Lore} That's all three. {Info.ghost} is here! Get close and press E to catch it.");
                Sfx.Play2D("ghost_moan", 0.55f, 1.15f);
            }
            else GameHUD.Toast($"{spot.Title}. {spot.Lore}");
            Refresh();
        }

        /// <summary>The third catch: off comes the sheet.</summary>
        internal void Bust()
        {
            ClubBook.BustedHaunt(Info.id, Info.n);
            GameHUD.Toast($"Busted! {Info.ghost}: {Info.twist} (Haunt {ClubBook.HauntsBusted} of {Total}, +20 candy.)");
            Sfx.Play2D("unmask", 0.7f, 1.1f);
            Sfx.Play2D("clue_chime", 0.7f, 1.1f);
            Refresh();
        }

        void Refresh()
        {
            bool busted = Busted;
            foreach (var s in signs) s.gameObject.SetActive(!busted);
            ghost.gameObject.SetActive(!busted && SignsFound >= signs.Count);
        }
    }

    /// <summary>One sign of a haunt: a small violet wisp with a glyph, E to read it.</summary>
    public class HauntSignSpot : MonoBehaviour, ILocalInteractable
    {
        public string Title, Lore;
        HauntBust bust;
        int index;
        Transform wisp;
        float phase;

        public bool Found => ClubBook.HasHauntSign(bust.Info.id, index);

        internal void Init(HauntBust owner, int i, TownLayout.HauntSign s)
        {
            bust = owner;
            index = i;
            Title = s.n;
            Lore = s.lore;
            phase = i * 1.7f;
            wisp = new GameObject("Wisp").transform;
            wisp.SetParent(transform, false);
            var violet = HauntBust.M(new Color(0.72f, 0.6f, 1f), true, "violet");
            HauntBust.Part(wisp, PrimitiveType.Sphere, new Vector3(0, 0.9f, 0), Vector3.one * 0.22f, violet);
            HauntBust.Part(wisp, PrimitiveType.Sphere, new Vector3(0, 0.75f, 0), new Vector3(0.12f, 0.2f, 0.12f), violet);
            HauntBust.Part(transform, PrimitiveType.Cylinder, new Vector3(0, 0.01f, 0), new Vector3(0.9f, 0.005f, 0.9f), HauntBust.M(new Color(0.45f, 0.35f, 0.75f), true, "ring"));
            var hit = gameObject.AddComponent<BoxCollider>();
            hit.isTrigger = true;
            hit.center = new Vector3(0f, 0.7f, 0f);
            hit.size = new Vector3(1.2f, 1.4f, 1.2f);
        }

        void Update()
        {
            if (wisp == null) return;
            float t = UITheme.ReduceMotion ? 0f : Time.time;
            wisp.localPosition = new Vector3(0f, Mathf.Sin(t * 1.6f + phase) * 0.12f, 0f);
            float s = Found ? 0.55f : 1f + Mathf.Sin(t * 3f + phase) * 0.12f;
            wisp.localScale = Vector3.one * s;
        }

        public bool CanInteract(SolverController solver) => solver != null && !solver.IsRiding;
        public string GetPrompt(SolverController solver) => Found ? $"Look at the {Title.ToLowerInvariant()} again" : $"Examine the {Title.ToLowerInvariant()}";
        public void Interact(SolverController solver) => LocalInteract(solver);

        public void LocalInteract(SolverController solver)
        {
            bool first = ClubBook.FoundHauntSign(bust.Info.id, index);
            Sfx.Play2D("clue_chime", first ? 0.6f : 0.3f, 1.25f);
            bust.SignRead(this, first);
        }
    }

    /// <summary>The ghost: a sheet with a face and its own colour. E to catch; it hops away twice.</summary>
    public class HauntGhost : MonoBehaviour, ILocalInteractable
    {
        HauntBust bust;
        Transform body;
        int caught, spot;
        float hopAt = -10f;
        Vector3 from, to;
        Light glow;

        internal void Init(HauntBust owner)
        {
            bust = owner;
            var c = owner.Info.c != null && owner.Info.c.Length >= 3 ? new Color(owner.Info.c[0], owner.Info.c[1], owner.Info.c[2]) : Color.white;
            body = new GameObject("Sheet").transform;
            body.SetParent(transform, false);
            var sheet = HauntBust.M(c, true, "ghost" + owner.Info.id);
            var ink = HauntBust.M(new Color(0.08f, 0.06f, 0.1f), false, "ink");
            // A soft, round sheet ghost: head, body and a wavy hem, all spheres and capsules.
            HauntBust.Part(body, PrimitiveType.Sphere, new Vector3(0, 0.55f, 0), new Vector3(0.7f, 0.7f, 0.7f), sheet);
            HauntBust.Part(body, PrimitiveType.Capsule, new Vector3(0, 0.05f, 0), new Vector3(0.78f, 0.55f, 0.78f), sheet);
            for (int i = 0; i < 6; i++)
            {
                float a = i * Mathf.PI / 3f;
                HauntBust.Part(body, PrimitiveType.Sphere, new Vector3(Mathf.Cos(a) * 0.3f, -0.42f, Mathf.Sin(a) * 0.3f), Vector3.one * 0.24f, sheet);
            }
            for (int s = -1; s <= 1; s += 2)
            {
                HauntBust.Part(body, PrimitiveType.Sphere, new Vector3(s * 0.12f, 0.62f, 0.31f), new Vector3(0.1f, 0.14f, 0.06f), ink);
                HauntBust.Part(body, PrimitiveType.Capsule, new Vector3(s * 0.38f, 0.15f, 0.05f), new Vector3(0.16f, 0.22f, 0.16f), sheet, new Vector3(0, 0, s * -40));
            }
            HauntBust.Part(body, PrimitiveType.Sphere, new Vector3(0, 0.45f, 0.33f), new Vector3(0.12f, 0.09f, 0.05f), ink);
            glow = new GameObject("Glow").AddComponent<Light>();
            glow.transform.SetParent(transform, false);
            glow.transform.localPosition = new Vector3(0, 0.6f, 0.4f);
            glow.type = LightType.Point;
            glow.color = c;
            glow.range = 5f;
            glow.intensity = 1.2f;
            glow.shadows = LightShadows.None;
            var hit = gameObject.AddComponent<BoxCollider>();
            hit.isTrigger = true;
            hit.center = new Vector3(0f, 0.2f, 0f);
            hit.size = new Vector3(1.4f, 1.8f, 1.4f);
            from = to = transform.position;
        }

        void Update()
        {
            float t = UITheme.ReduceMotion ? 0f : Time.time;
            // Hop: a quick ease-out slide to the next spot, with a little arc.
            float k = Mathf.Clamp01((Time.time - hopAt) / 0.6f);
            float e = 1f - (1f - k) * (1f - k);
            var p = Vector3.Lerp(from, to, e) + Vector3.up * Mathf.Sin(k * Mathf.PI) * 1.2f;
            transform.position = p + Vector3.up * Mathf.Sin(t * 1.4f) * 0.18f;
            // Always face whoever is looking, and sway.
            var cam = Camera.main;
            if (cam != null)
            {
                var d = cam.transform.position - transform.position;
                d.y = 0f;
                if (d.sqrMagnitude > 0.01f) transform.rotation = Quaternion.LookRotation(d) * Quaternion.Euler(0f, 0f, Mathf.Sin(t * 2f) * 6f);
            }
        }

        public bool CanInteract(SolverController solver) => solver != null && !solver.IsRiding && Time.time - hopAt > 0.6f;
        public string GetPrompt(SolverController solver) => caught < 2 ? $"Catch {bust.Info.ghost}!" : $"Bust {bust.Info.ghost}!";
        public void Interact(SolverController solver) => LocalInteract(solver);

        public void LocalInteract(SolverController solver)
        {
            caught++;
            if (caught >= 3) { bust.Bust(); return; }
            spot = (spot + 1) % 3;
            from = transform.position;
            to = bust.Hide(spot);
            hopAt = Time.time;
            Sfx.Play2D("whoosh", 0.5f, 1.3f);
            GameHUD.Toast(caught == 1 ? $"Got a corner of the sheet! {bust.Info.ghost} slipped away. After it!" : $"Nearly! {bust.Info.ghost} fled inside {bust.Info.n}. Go in after it!");
        }
    }
}
