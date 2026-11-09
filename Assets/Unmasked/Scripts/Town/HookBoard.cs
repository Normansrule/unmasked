using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The Hook Board (round 34): twenty-four brass hooks on a board outside the Historical Society,
    /// one for each of the 1823 lantern families ("Twenty-four hooks" in Tales.cs). Bring the lost
    /// lanterns you've found here and press E to hang each one on its family's hook. A hung lantern
    /// stays lit on the board from then on, every hook you fill pushes the creek mist a little further
    /// down all over town (StoryLight reads ClubBook.HooksFilled), and with all twenty-four back the
    /// mist settles on the creek for good: the Club becomes the new Lantern Watch.
    ///
    /// Like the doorsteps it happens on your own computer (ILocalInteractable): your Club Book keeps
    /// which hooks are filled. Pressing E with nothing to hang tells you which family's lantern is
    /// still missing and roughly where it is.
    /// </summary>
    public class HookBoard : MonoBehaviour, ILocalInteractable
    {
        public const int Hooks = 24;

        /// <summary>The 1823 ledger: the family over each hook, in lantern order (L01 is hook 1).</summary>
        public static readonly string[] Families =
        {
            "Hatcher", "Quill", "Pemberton", "Blackwood", "Wren", "Finch", "Crane", "Ashby",
            "Thorne", "Pell", "Mabry", "Dunmore", "Hale", "Kettering", "Larkin", "Morrow",
            "Oakes", "Prewitt", "Rook", "Sable", "Tolliver", "Vance", "Whitlock", "Yarrow",
        };

        public static HookBoard Instance { get; private set; }

        readonly GameObject[] lanterns = new GameObject[Hooks];
        Light glow;
        TextMesh title, bubble;
        float bubbleUntil;
        bool busy;
        int shown = -1;

        /// <summary>Called by TownDirector: one board, just in front of the Historical Society's lot.</summary>
        public static void Ensure(GameObject host)
        {
            var town = TownLayout.Current;
            if (town?.lots == null || host.transform.Find("HookBoard") != null) return;
            TownLayout.Lot society = null;
            foreach (var l in town.lots) if (l.id == Cases.FinaleCase) society = l;
            if (society?.lot == null) return;
            var go = new GameObject("HookBoard");
            go.transform.SetParent(host.transform, false);
            // On the grass verge left of the front path, facing Founders Way.
            go.transform.SetPositionAndRotation(new Vector3(society.Min.x + 8f, 0f, society.Min.y - 3.5f), Quaternion.Euler(0f, 180f, 0f));
            go.AddComponent<HookBoard>().Build();
        }

        void Awake() => Instance = this;
        void OnDestroy() { if (Instance == this) Instance = null; }

        void Build()
        {
            var wood = Horizon.Lit("HookBoardWood", new Color(0.36f, 0.22f, 0.13f));
            var trim = Horizon.Lit("HookBoardTrim", new Color(0.22f, 0.13f, 0.08f));
            var brass = Horizon.Lit("HookBrass", new Color(0.78f, 0.62f, 0.3f));
            var tin = Horizon.Lit("LanternTin", new Color(0.2f, 0.19f, 0.22f));
            var lit = Horizon.Lit("LanternGlass", new Color(1f, 0.78f, 0.42f), true);
            var roof = Horizon.Lit("HookBoardRoof", new Color(0.18f, 0.24f, 0.26f));

            // Solid enough to walk into, and a trigger the camera finds when you look at it.
            var solid = gameObject.AddComponent<BoxCollider>();
            solid.center = new Vector3(0f, 1.4f, 0f);
            solid.size = new Vector3(4.6f, 2.8f, 0.3f);
            var hit = gameObject.AddComponent<BoxCollider>();
            hit.isTrigger = true;
            hit.center = new Vector3(0f, 1.4f, 0.5f);
            hit.size = new Vector3(4.8f, 2.8f, 1f);

            // Two posts, a board, a little pitched roof against the rain.
            Part(transform, PrimitiveType.Cube, new Vector3(-2.35f, 1.5f, 0f), new Vector3(0.18f, 3f, 0.18f), trim);
            Part(transform, PrimitiveType.Cube, new Vector3(2.35f, 1.5f, 0f), new Vector3(0.18f, 3f, 0.18f), trim);
            Part(transform, PrimitiveType.Cube, new Vector3(0f, 1.55f, 0f), new Vector3(4.5f, 2.1f, 0.12f), wood);
            Part(transform, PrimitiveType.Cube, new Vector3(0f, 2.66f, 0f), new Vector3(4.7f, 0.12f, 0.2f), trim);
            Part(transform, PrimitiveType.Cube, new Vector3(0f, 0.46f, 0f), new Vector3(4.7f, 0.12f, 0.2f), trim);
            Part(transform, PrimitiveType.Cube, new Vector3(0f, 3.12f, 0.24f), new Vector3(5f, 0.08f, 0.75f), roof, new Vector3(-28f, 0f, 0f));
            Part(transform, PrimitiveType.Cube, new Vector3(0f, 3.12f, -0.24f), new Vector3(5f, 0.08f, 0.75f), roof, new Vector3(28f, 0f, 0f));

            title = Horizon.MakeText(transform, "THE TWENTY-FOUR HOOKS", new Vector3(0f, 2.48f, 0.08f), 0.028f, new Color(0.95f, 0.85f, 0.6f));

            // Four rows of six: a brass hook, the family's name under it, and its lantern (hidden until hung).
            for (int i = 0; i < Hooks; i++)
            {
                int row = i / 6, col = i % 6;
                var at = new Vector3(-1.85f + col * 0.74f, 2.2f - row * 0.48f, 0.07f);
                Part(transform, PrimitiveType.Cylinder, at, new Vector3(0.03f, 0.05f, 0.03f), brass, new Vector3(90f, 0f, 0f));
                Part(transform, PrimitiveType.Cylinder, at + new Vector3(0f, -0.03f, 0.05f), new Vector3(0.025f, 0.03f, 0.025f), brass);
                Horizon.MakeText(transform, Families[i].ToUpperInvariant(), at + new Vector3(0f, -0.36f, 0.01f), 0.012f, new Color(0.85f, 0.75f, 0.55f));

                var l = new GameObject("Hook_" + (i + 1)).transform;
                l.SetParent(transform, false);
                l.localPosition = at + new Vector3(0f, -0.17f, 0.1f);
                Part(l, PrimitiveType.Cylinder, Vector3.zero, new Vector3(0.13f, 0.1f, 0.13f), lit);
                Part(l, PrimitiveType.Cylinder, new Vector3(0f, 0.11f, 0f), new Vector3(0.16f, 0.015f, 0.16f), tin);
                Part(l, PrimitiveType.Cylinder, new Vector3(0f, -0.11f, 0f), new Vector3(0.16f, 0.015f, 0.16f), tin);
                Part(l, PrimitiveType.Sphere, new Vector3(0f, 0.15f, 0f), new Vector3(0.09f, 0.06f, 0.09f), tin);
                lanterns[i] = l.gameObject;
                l.gameObject.SetActive(false);
            }

            // One warm light for the whole board, brighter the more hooks are filled.
            glow = new GameObject("BoardGlow").AddComponent<Light>();
            glow.transform.SetParent(transform, false);
            glow.transform.localPosition = new Vector3(0f, 1.8f, 2.0f);
            glow.type = LightType.Point;
            glow.color = new Color(1f, 0.76f, 0.44f);
            glow.range = 7f;
            glow.shadows = LightShadows.None;

            bubble = Horizon.MakeText(transform, "", new Vector3(0f, 3.5f, 0.3f), 0.03f, new Color(1f, 0.93f, 0.75f));
            bubble.gameObject.SetActive(false);
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

        static string LanternId(int hook) => "L" + (hook + 1).ToString("00");

        void Update()
        {
            int filled = ClubBook.HooksFilled;
            if (filled != shown)
            {
                shown = filled;
                for (int i = 0; i < Hooks; i++) lanterns[i].SetActive(ClubBook.Has("hook:" + LanternId(i)));
                glow.intensity = filled == 0 ? 0.15f : 0.4f + 1.0f * filled / (float)Hooks;
                title.text = filled >= Hooks ? "THE LANTERN WATCH" : "THE TWENTY-FOUR HOOKS";
            }
            if (bubble.gameObject.activeSelf && Time.time > bubbleUntil) bubble.gameObject.SetActive(false);
        }

        // ---- IInteractable -------------------------------------------------------------------------

        public bool CanInteract(SolverController solver) => !busy && solver != null && !solver.IsRiding;

        public string GetPrompt(SolverController solver)
        {
            int waiting = ClubBook.LanternsToHang();
            if (waiting > 0) return waiting == 1 ? "Hang your lantern on its hook" : $"Hang your {waiting} lanterns on their hooks";
            return ClubBook.HooksFilled >= Hooks ? "Look at the Hook Board" : $"Read the Hook Board ({ClubBook.HooksFilled} of {Hooks} hooks filled)";
        }

        /// <summary>A board has no NetworkObject, so this never runs.</summary>
        public void Interact(SolverController solver) { }

        public void LocalInteract(SolverController solver)
        {
            if (!busy) StartCoroutine(Hang());
        }

        IEnumerator Hang()
        {
            busy = true;
            var hung = ClubBook.HangLanterns();
            // One at a time, with a little chime each, so you watch the board fill.
            foreach (var id in hung)
            {
                int i = int.Parse(id.Substring(1)) - 1;
                if (i >= 0 && i < Hooks) lanterns[i].SetActive(true);
                Sfx.Play("clue_chime", transform.position, 0.6f, 14f, 1.3f + 0.04f * i);
                yield return new WaitForSeconds(0.35f);
            }
            shown = -1;
            Say(hung.Count > 0 ? Hung(hung) : Missing());
            busy = false;
        }

        static string Hung(List<string> hung)
        {
            int filled = ClubBook.HooksFilled;
            if (filled >= Hooks)
                return "All twenty-four lanterns are home. Down by the creek the mist lies still. Hollow Creek has a Lantern Watch again: you.";
            string who = hung.Count == 1 ? $"The {Families[int.Parse(hung[0].Substring(1)) - 1]} lantern is back on its hook." : $"{hung.Count} lanterns back on their hooks.";
            return $"{who} {filled} of {Hooks}. The mist sits a little lower tonight.";
        }

        static string Missing()
        {
            var town = TownLayout.Current;
            if (town?.collectibles != null)
                foreach (var c in town.collectibles)
                {
                    if (ClubBook.Has("lantern:" + c.id) || !int.TryParse(c.id.Substring(1), out int n) || n < 1 || n > Hooks) continue;
                    return $"Hook {n}, the {Families[n - 1]} family: still out there, somewhere around {c.where}.";
                }
            return "Every hook is filled. The board glows all night.";
        }

        void Say(string line)
        {
            bubble.text = Wrap(line, 34);
            bubble.gameObject.SetActive(true);
            bubbleUntil = Time.time + 6f;
            GameHUD.Toast(line);
        }

        static string Wrap(string s, int width)
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
    }
}
