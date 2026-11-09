using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// The carving bench (round 36): a trestle table on the porch outside Mystery Club HQ, with a
    /// pumpkin on it and a knife. Press E to carve: pick the eyes, the nose and the mouth (the
    /// pumpkin on the bench changes as you choose), then "Carve it" and it joins the row of
    /// jack-o'-lanterns along the HQ wall, lit. One carving a night; the porch keeps your last six.
    ///
    /// On your own computer only (ILocalInteractable), saved in the Club Book. The panel docks to the
    /// left so you can see the pumpkin; arrow keys move, Enter carves, Esc closes.
    /// </summary>
    public class CarvingBench : MonoBehaviour, ILocalInteractable
    {
        public const int PorchSize = 6;
        public static readonly string[] Eyes = { "Triangles", "Round", "Angry", "Sleepy" };
        public static readonly string[] Noses = { "Triangle", "Button", "None" };
        public static readonly string[] Mouths = { "Grin", "Toothy", "Oh!", "Wobbly" };

        public static CarvingBench Instance { get; private set; }
        public static bool IsOpen => Instance != null && Instance.open;

        bool open;
        int row, eyes, nose, mouth;
        Transform preview, porch;
        Material skin, glow, stem;
        string shownPorch = null;

        /// <summary>Called by TownDirector: the bench and the porch row, just outside HQ's east door.</summary>
        public static void Ensure(GameObject host)
        {
            var town = TownLayout.Current;
            if (town?.hq?.trunk == null || host.transform.Find("CarvingBench") != null) return;
            var go = new GameObject("CarvingBench");
            go.transform.SetParent(host.transform, false);
            // On the porch outside the east door (the wall is at x -16), facing the parking lot.
            go.transform.SetPositionAndRotation(new Vector3(-13.6f, 0f, -68.2f), Quaternion.Euler(0f, 90f, 0f));
            go.AddComponent<CarvingBench>().Build(host.transform);
        }

        /// <summary>The middle of the porch row (for the club camera); null-safe before Build.</summary>
        public Vector3 PorchPoint => porch != null ? porch.position + new Vector3(0.6f, 0.3f, 1.4f) : transform.position;
        public bool PorchHasPumpkins => ClubBook.Carvings.Count > 0;

        void Awake() => Instance = this;
        void OnDestroy() { if (Instance == this) Instance = null; }

        void Build(Transform host)
        {
            skin = Horizon.Lit("CarvePumpkin", new Color(0.91f, 0.45f, 0.11f));
            glow = Horizon.Lit("CarveGlow", new Color(1f, 0.74f, 0.32f), true);
            stem = Horizon.Lit("CarveStem", new Color(0.32f, 0.42f, 0.18f));
            var wood = Horizon.Lit("CarveBench", new Color(0.42f, 0.28f, 0.16f));
            var steel = Horizon.Lit("CarveKnife", new Color(0.7f, 0.72f, 0.76f));

            var solid = gameObject.AddComponent<BoxCollider>();
            solid.center = new Vector3(0f, 0.45f, 0f);
            solid.size = new Vector3(1.6f, 0.9f, 0.8f);
            var hit = gameObject.AddComponent<BoxCollider>();
            hit.isTrigger = true;
            hit.center = new Vector3(0f, 0.9f, 0.3f);
            hit.size = new Vector3(1.8f, 1.8f, 1.4f);

            // A trestle table: top, two A-frame legs, a knife and a scoop.
            Part(transform, PrimitiveType.Cube, new Vector3(0f, 0.86f, 0f), new Vector3(1.6f, 0.06f, 0.8f), wood);
            foreach (float x in new[] { -0.62f, 0.62f })
            {
                Part(transform, PrimitiveType.Cube, new Vector3(x, 0.42f, -0.18f), new Vector3(0.07f, 0.86f, 0.07f), wood, new Vector3(-12f, 0f, 0f));
                Part(transform, PrimitiveType.Cube, new Vector3(x, 0.42f, 0.18f), new Vector3(0.07f, 0.86f, 0.07f), wood, new Vector3(12f, 0f, 0f));
            }
            Part(transform, PrimitiveType.Cube, new Vector3(0.5f, 0.9f, 0.2f), new Vector3(0.22f, 0.012f, 0.03f), steel, new Vector3(0f, 25f, 0f));
            Part(transform, PrimitiveType.Cube, new Vector3(0.36f, 0.9f, 0.25f), new Vector3(0.1f, 0.025f, 0.035f), wood, new Vector3(0f, 25f, 0f));
            Part(transform, PrimitiveType.Sphere, new Vector3(-0.5f, 0.9f, 0.15f), new Vector3(0.12f, 0.04f, 0.12f), steel);

            preview = new GameObject("Preview").transform;
            preview.SetParent(transform, false);
            preview.localPosition = new Vector3(0f, 1.1f, 0f);

            // The porch row along the HQ wall, beside the door.
            porch = new GameObject("PorchPumpkins").transform;
            porch.SetParent(host, false);
            porch.position = new Vector3(-15.55f, 0f, -69.9f);
            var light = new GameObject("PorchGlow").AddComponent<Light>();
            light.transform.SetParent(porch, false);
            light.transform.localPosition = new Vector3(0.9f, 0.6f, 1.6f);
            light.type = LightType.Point;
            light.color = new Color(1f, 0.7f, 0.38f);
            light.range = 5f;
            light.intensity = 0f;
            light.shadows = LightShadows.None;

            var last = ClubBook.LastCarving;
            if (last != null && Decode(last, out int e, out int n, out int m)) { eyes = e; nose = n; mouth = m; }
            Rebuild();
        }

        static void Part(Transform parent, PrimitiveType type, Vector3 pos, Vector3 scale, Material mat, Vector3 euler = default)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localEulerAngles = euler;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
        }

        public static string Encode(int e, int n, int m) => $"{e},{n},{m}";

        public static bool Decode(string code, out int e, out int n, out int m)
        {
            e = n = m = 0;
            var p = code.Split(',');
            return p.Length == 3 && int.TryParse(p[0], out e) && int.TryParse(p[1], out n) && int.TryParse(p[2], out m)
                   && e >= 0 && e < Eyes.Length && n >= 0 && n < Noses.Length && m >= 0 && m < Mouths.Length;
        }

        /// <summary>
        /// A jack-o'-lantern under parent, 0.5 m across, face towards local +z. The cut-outs are the
        /// glowing candlelight showing through, set just proud of the skin.
        /// </summary>
        public static void BuildPumpkin(Transform parent, int e, int n, int m, Material skin, Material glow, Material stem, float size = 1f)
        {
            var root = new GameObject("Jack").transform;
            root.SetParent(parent, false);
            root.localScale = Vector3.one * size;
            // Ribbed body: a squashed centre and four lobes around it.
            Part(root, PrimitiveType.Sphere, new Vector3(0f, 0.22f, 0f), new Vector3(0.5f, 0.42f, 0.48f), skin);
            for (int i = 0; i < 4; i++)
            {
                float a = i * Mathf.PI / 2f + Mathf.PI / 4f;
                Part(root, PrimitiveType.Sphere, new Vector3(Mathf.Sin(a) * 0.07f, 0.22f, Mathf.Cos(a) * 0.07f), new Vector3(0.38f, 0.4f, 0.38f), skin);
            }
            Part(root, PrimitiveType.Cylinder, new Vector3(0.01f, 0.46f, 0f), new Vector3(0.05f, 0.05f, 0.05f), stem, new Vector3(0f, 0f, -14f));

            const float z = 0.245f; // the front of the skin
            for (int s = -1; s <= 1; s += 2)
            {
                var at = new Vector3(s * 0.09f, 0.29f, z);
                switch (e)
                {
                    case 0: Part(root, PrimitiveType.Cube, at, new Vector3(0.07f, 0.07f, 0.02f), glow, new Vector3(0f, 0f, 45f)); break;
                    case 1: Part(root, PrimitiveType.Sphere, at, new Vector3(0.08f, 0.08f, 0.02f), glow); break;
                    case 2: Part(root, PrimitiveType.Cube, at + new Vector3(0f, -0.01f, 0f), new Vector3(0.1f, 0.035f, 0.02f), glow, new Vector3(0f, 0f, s * 22f)); break;
                    default: Part(root, PrimitiveType.Capsule, at + new Vector3(0f, -0.015f, 0f), new Vector3(0.025f, 0.05f, 0.02f), glow, new Vector3(0f, 0f, 90f)); break;
                }
            }
            switch (n)
            {
                case 0: Part(root, PrimitiveType.Cube, new Vector3(0f, 0.21f, z + 0.005f), new Vector3(0.04f, 0.04f, 0.02f), glow, new Vector3(0f, 0f, 45f)); break;
                case 1: Part(root, PrimitiveType.Sphere, new Vector3(0f, 0.21f, z + 0.005f), new Vector3(0.04f, 0.04f, 0.02f), glow); break;
            }
            float my = 0.13f;
            switch (m)
            {
                case 0: // a grin: a row of slits curving up at the ends
                    for (int i = -3; i <= 3; i++)
                        Part(root, PrimitiveType.Cube, new Vector3(i * 0.032f, my + i * i * 0.004f, z - Mathf.Abs(i) * 0.008f), new Vector3(0.03f, 0.035f, 0.02f), glow, new Vector3(0f, -i * 8f, i * 6f));
                    break;
                case 1: // toothy: a wide mouth with two teeth left in
                    Part(root, PrimitiveType.Cube, new Vector3(0f, my, z - 0.005f), new Vector3(0.22f, 0.06f, 0.02f), glow);
                    Part(root, PrimitiveType.Cube, new Vector3(-0.04f, my + 0.018f, z + 0.002f), new Vector3(0.03f, 0.03f, 0.025f), skin);
                    Part(root, PrimitiveType.Cube, new Vector3(0.05f, my - 0.018f, z + 0.002f), new Vector3(0.03f, 0.03f, 0.025f), skin);
                    break;
                case 2: // a round "oh!"
                    Part(root, PrimitiveType.Sphere, new Vector3(0f, my, z), new Vector3(0.07f, 0.09f, 0.02f), glow);
                    break;
                default: // wobbly: a zigzag
                    for (int i = -2; i <= 2; i++)
                        Part(root, PrimitiveType.Cube, new Vector3(i * 0.04f, my + (i % 2 == 0 ? 0.008f : -0.008f), z - Mathf.Abs(i) * 0.01f), new Vector3(0.045f, 0.02f, 0.02f), glow, new Vector3(0f, -i * 10f, i % 2 == 0 ? 30f : -30f));
                    break;
            }
        }

        void Rebuild()
        {
            for (int i = preview.childCount - 1; i >= 0; i--) Destroy(preview.GetChild(i).gameObject);
            BuildPumpkin(preview, eyes, nose, mouth, skin, glow, stem);
            preview.localRotation = Quaternion.identity;
        }

        void RebuildPorch()
        {
            var list = ClubBook.Carvings;
            string key = string.Join("|", list);
            if (key == shownPorch) return;
            shownPorch = key;
            for (int i = porch.childCount - 1; i >= 0; i--)
                if (porch.GetChild(i).name.StartsWith("Slot")) Destroy(porch.GetChild(i).gameObject);
            int k = 0;
            foreach (var code in list)
            {
                if (!Decode(code, out int e, out int n, out int m)) continue;
                var slot = new GameObject("Slot" + k).transform;
                slot.SetParent(porch, false);
                // Two staggered rows along the wall, faces out to the parking lot (+x).
                slot.localPosition = new Vector3(0.35f + (k % 2) * 0.45f, 0f, k * 0.55f);
                slot.localRotation = Quaternion.Euler(0f, 90f + (k % 3 - 1) * 12f, 0f);
                BuildPumpkin(slot, e, n, m, skin, glow, stem, 0.9f + (k % 3) * 0.08f);
                k++;
            }
            var light = porch.Find("PorchGlow")?.GetComponent<Light>();
            if (light != null) light.intensity = k == 0 ? 0f : 0.5f + 0.15f * k;
        }

        void Update()
        {
            RebuildPorch();
            if (!open) return;
            var me = SolverController.Local;
            if (me == null || Vector3.Distance(me.transform.position, transform.position) > 4f) { open = false; return; }
            preview.localRotation = Quaternion.Euler(0f, Mathf.Sin(Time.time * 0.8f) * (UITheme.ReduceMotion ? 0f : 18f), 0f);
            var kb = Keyboard.current;
            if (kb == null) return;
            if (kb.escapeKey.wasPressedThisFrame) open = false;
            if (kb.upArrowKey.wasPressedThisFrame) row = (row + 2) % 3;
            if (kb.downArrowKey.wasPressedThisFrame) row = (row + 1) % 3;
            if (kb.leftArrowKey.wasPressedThisFrame) Step(-1);
            if (kb.rightArrowKey.wasPressedThisFrame) Step(1);
            if (kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame) CarveIt();
        }

        void Step(int d)
        {
            if (row == 0) eyes = (eyes + d + Eyes.Length) % Eyes.Length;
            else if (row == 1) nose = (nose + d + Noses.Length) % Noses.Length;
            else mouth = (mouth + d + Mouths.Length) % Mouths.Length;
            Rebuild();
        }

        void CarveIt()
        {
            if (!ClubBook.CanCarveTonight) return;
            ClubBook.Carve(Encode(eyes, nose, mouth));
            Sfx.Play("creak", transform.position, 0.5f, 10f, 1.6f);
            open = false;
        }

        // ---- IInteractable -------------------------------------------------------------------------

        public bool CanInteract(SolverController solver) => solver != null && !solver.IsRiding;

        public string GetPrompt(SolverController solver) =>
            ClubBook.CanCarveTonight ? "Carve a jack-o'-lantern" : "Look at the carving bench (you've carved one tonight)";

        public void Interact(SolverController solver) { }

        public void LocalInteract(SolverController solver) => open = !open;

        void OnGUI()
        {
            if (!open) return;
            UITheme.Begin();
            float w = 340f;
            var r = new Rect(UITheme.S6, UITheme.H / 2f - 170f, w, 340f);
            UITheme.Rect(new Rect(r.x + 1, r.y + 3, r.width, r.height), UITheme.Shadow);
            GUILayout.BeginArea(r, UITheme.Panel);
            GUILayout.Label("Carve a jack-o'-lantern", UITheme.Title);
            GUILayout.Label("Pick a face. The pumpkin on the bench shows it.", UITheme.MutedWrap);
            GUILayout.Space(UITheme.S2);
            Choice(0, "Eyes", Eyes, eyes);
            Choice(1, "Nose", Noses, nose);
            Choice(2, "Mouth", Mouths, mouth);
            GUILayout.Space(UITheme.S3);
            if (ClubBook.CanCarveTonight)
            {
                if (GUILayout.Button("Carve it  (Enter)", UITheme.Primary, GUILayout.Height(40))) CarveIt();
            }
            else GUILayout.Label("You've carved one tonight. Come back after the next night.", UITheme.MutedWrap);
            GUILayout.Label($"Arrow keys pick, Esc closes. Your porch holds your last {PorchSize}.", UITheme.Small);
            GUILayout.EndArea();
        }

        void Choice(int which, string label, string[] options, int current)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(row == which ? UITheme.Tint("▸ " + label, UITheme.Accent) : "  " + label, UITheme.Strong, GUILayout.Width(80));
            if (GUILayout.Button("‹", GUILayout.Width(36), GUILayout.Height(32))) { row = which; Step(-1); }
            GUILayout.Label(options[current], UITheme.Center, GUILayout.Height(32));
            if (GUILayout.Button("›", GUILayout.Width(36), GUILayout.Height(32))) { row = which; Step(1); }
            GUILayout.EndHorizontal();
        }
    }
}
