using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Curiosities: small strange things hidden all over the world past the edge of town (round 39,
    /// HollowCreek.json "curios", placed by Docs/tools/regions.py). A rusted helm in the castle's great
    /// hall, a squeaky red nose in the circus ring, a gnome with fangs under the Main Street bridge.
    /// Each one twinkles until you've looked at it. Press E to examine it and read its little story:
    /// +10 candy the first time, and the Club Book keeps it ("curio:id"). Like the lost lanterns it all
    /// happens on your own computer (ILocalInteractable), so nobody can find one before you do, and
    /// found ones stay in the world (they just stop twinkling) so you can show your friends.
    /// </summary>
    public class Curio : MonoBehaviour, ILocalInteractable
    {
        /// <summary>How many there are (casecheck makes sure HollowCreek.json agrees).</summary>
        public const int Total = 32;
        const float LightDistance = 40f;

        public string Id, Title, Where, Lore, Kind;
        public static readonly List<Curio> All = new();

        Transform body, twinkle;
        Light glint;
        float phase;

        /// <summary>Called by TownDirector: build every curiosity in the layout.</summary>
        public static void Ensure(GameObject host)
        {
            var town = TownLayout.Current;
            if (town?.curios == null || host.transform.Find("Curios") != null) return;
            var root = new GameObject("Curios").transform;
            root.SetParent(host.transform, false);
            foreach (var c in town.curios)
            {
                if (c.p == null || c.p.Length < 3) continue;
                var go = new GameObject("Curio_" + c.id);
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(c.p[0], c.p[1], c.p[2]);
                var curio = go.AddComponent<Curio>();
                curio.Id = c.id;
                curio.Title = c.n;
                curio.Where = c.where;
                curio.Lore = c.lore;
                curio.Kind = c.kind;
                curio.Build();
            }
        }

        static readonly Dictionary<string, Material> mats = new();

        static Material M(string hex, bool glow = false)
        {
            string key = hex + (glow ? "*" : "");
            if (mats.TryGetValue(key, out var m) && m != null) return m;
            ColorUtility.TryParseHtmlString("#" + hex, out var c);
            return mats[key] = Horizon.Lit("Curio" + key, c, glow);
        }

        void Build()
        {
            body = new GameObject("Body").transform;
            body.SetParent(transform, false);
            BuildShape(Kind);

            var hit = gameObject.AddComponent<BoxCollider>();
            hit.isTrigger = true;
            hit.center = new Vector3(0f, 0.5f, 0f);
            hit.size = new Vector3(1.4f, 1.4f, 1.4f);

            // The twinkle: a little star that turns and pulses above it until you've found it.
            twinkle = new GameObject("Twinkle").transform;
            twinkle.SetParent(transform, false);
            twinkle.localPosition = new Vector3(0f, 0.95f, 0f);
            var gold = M("ffe7a0", true);
            Part(twinkle, PrimitiveType.Cube, Vector3.zero, new Vector3(0.05f, 0.22f, 0.05f), gold, new Vector3(0, 0, 45));
            Part(twinkle, PrimitiveType.Cube, Vector3.zero, new Vector3(0.05f, 0.22f, 0.05f), gold, new Vector3(0, 0, -45));
            Part(twinkle, PrimitiveType.Sphere, Vector3.zero, Vector3.one * 0.07f, gold);

            glint = new GameObject("Glint").AddComponent<Light>();
            glint.transform.SetParent(transform, false);
            glint.transform.localPosition = new Vector3(0f, 0.7f, 0f);
            glint.type = LightType.Point;
            glint.color = new Color(1f, 0.88f, 0.6f);
            glint.range = 3f;
            glint.intensity = 0.9f;
            glint.shadows = LightShadows.None;
            phase = Mathf.Abs(Id?.GetHashCode() ?? 0) % 100 * 0.1f;
        }

        /// <summary>A few primitives per kind: small, chunky and readable from a couple of metres away.</summary>
        void BuildShape(string kind)
        {
            Transform b = body;
            switch (kind)
            {
                case "helm": // a rusted great helm with a visor slit and a crest
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.22f, 0), new Vector3(0.3f, 0.2f, 0.3f), M("6a5040"));
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.42f, 0), new Vector3(0.3f, 0.18f, 0.3f), M("6a5040"));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.3f, 0.15f), new Vector3(0.2f, 0.025f, 0.02f), M("140f0c"));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.56f, 0), new Vector3(0.03f, 0.08f, 0.24f), M("8a2a24"));
                    break;
                case "key": // a big iron key
                    Part(b, PrimitiveType.Cylinder, new Vector3(-0.16f, 0.03f, 0), new Vector3(0.14f, 0.02f, 0.14f), M("3a3a40"));
                    Part(b, PrimitiveType.Cube, new Vector3(0.06f, 0.03f, 0), new Vector3(0.34f, 0.04f, 0.04f), M("3a3a40"));
                    Part(b, PrimitiveType.Cube, new Vector3(0.2f, 0.03f, 0.05f), new Vector3(0.04f, 0.04f, 0.08f), M("3a3a40"));
                    Part(b, PrimitiveType.Cube, new Vector3(0.14f, 0.03f, 0.04f), new Vector3(0.03f, 0.04f, 0.06f), M("3a3a40"));
                    break;
                case "frame": // a picture in a gilt frame, propped up
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.36f, 0), new Vector3(0.5f, 0.66f, 0.04f), M("b08a3a"), new Vector3(-12, 0, 0));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.36f, 0.02f), new Vector3(0.4f, 0.56f, 0.02f), M("3a2a3a"), new Vector3(-12, 0, 0));
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.42f, 0.04f), new Vector3(0.14f, 0.18f, 0.02f), M("d8b89a"), new Vector3(-12, 0, 0));
                    break;
                case "raven": // a stuffed raven on a little stand, one glass eye
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.03f, 0), new Vector3(0.2f, 0.03f, 0.2f), M("4a3424"));
                    Part(b, PrimitiveType.Capsule, new Vector3(0, 0.2f, 0), new Vector3(0.14f, 0.13f, 0.2f), M("16141c"), new Vector3(70, 0, 0));
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.3f, 0.1f), Vector3.one * 0.1f, M("16141c"));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.3f, 0.17f), new Vector3(0.025f, 0.025f, 0.08f), M("3a3a3a"));
                    Part(b, PrimitiveType.Sphere, new Vector3(0.04f, 0.32f, 0.13f), Vector3.one * 0.022f, M("ffcf5a", true));
                    break;
                case "nose": // a squeaky red nose
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.08f, 0), Vector3.one * 0.16f, M("e0282e"));
                    Part(b, PrimitiveType.Sphere, new Vector3(0.03f, 0.13f, 0.03f), Vector3.one * 0.04f, M("ffb0b0"));
                    break;
                case "ticket": // a torn ticket on a spike
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.45f, 0), new Vector3(0.03f, 0.45f, 0.03f), M("3a3a40"));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.75f, 0.02f), new Vector3(0.26f, 0.12f, 0.01f), M("e8c860"), new Vector3(0, 0, 8));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.75f, 0.03f), new Vector3(0.18f, 0.02f, 0.005f), M("a01c24"), new Vector3(0, 0, 8));
                    break;
                case "doll": // a ventriloquist's dummy, slumped, with a hinged jaw
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.2f, 0), new Vector3(0.24f, 0.28f, 0.14f), M("2a2a48"));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.3f, 0.075f), new Vector3(0.06f, 0.1f, 0.01f), M("a01c24"));
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.45f, 0), Vector3.one * 0.2f, M("e8c8a8"), new Vector3(0, 0, 14));
                    Part(b, PrimitiveType.Cube, new Vector3(0.01f, 0.38f, 0.08f), new Vector3(0.1f, 0.015f, 0.01f), M("3a1a1a"), new Vector3(0, 0, 14));
                    for (int side = -1; side <= 1; side += 2)
                    {
                        Part(b, PrimitiveType.Sphere, new Vector3(side * 0.045f, 0.47f, 0.09f), Vector3.one * 0.04f, M("ffffff"));
                        Part(b, PrimitiveType.Sphere, new Vector3(side * 0.045f, 0.47f, 0.105f), Vector3.one * 0.018f, M("1a1420"));
                        Part(b, PrimitiveType.Sphere, new Vector3(side * 0.07f, 0.42f, 0.08f), Vector3.one * 0.04f, M("e88080"));
                        Part(b, PrimitiveType.Cube, new Vector3(side * 0.08f, 0.05f, 0.14f), new Vector3(0.06f, 0.06f, 0.24f), M("2a2a48"));
                    }
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.54f, -0.01f), new Vector3(0.21f, 0.1f, 0.2f), M("3a2416"));
                    break;
                case "button": // a lift button panel with a lit 13
                    Part(b, PrimitiveType.Cube, new Vector3(0, 1.2f, 0), new Vector3(0.24f, 0.4f, 0.03f), M("b0a890"));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 1.28f, 0.02f), new Vector3(0.07f, 0.01f, 0.07f), M("ffb347", true), new Vector3(90, 0, 0));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 1.12f, 0.02f), new Vector3(0.07f, 0.01f, 0.07f), M("6a6458"), new Vector3(90, 0, 0));
                    break;
                case "letter": // a sealed envelope (or half a recipe) on a crate
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.2f, 0), new Vector3(0.4f, 0.4f, 0.4f), M("6a4a2a"));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.41f, 0), new Vector3(0.26f, 0.01f, 0.17f), M("efe4cc"), new Vector3(0, 18, 0));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.42f, 0), new Vector3(0.05f, 0.006f, 0.05f), M("a01c24"));
                    break;
                case "chair": // a striped deckchair
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.3f, 0), new Vector3(0.6f, 0.03f, 0.9f), M("e0d8c8"), new Vector3(-30, 0, 0));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.31f, 0), new Vector3(0.2f, 0.035f, 0.9f), M("2a6a9a"), new Vector3(-30, 0, 0));
                    for (int side = -1; side <= 1; side += 2)
                    {
                        Part(b, PrimitiveType.Cube, new Vector3(side * 0.31f, 0.3f, 0), new Vector3(0.04f, 0.04f, 1.0f), M("8a6a44"), new Vector3(-30, 0, 0));
                        Part(b, PrimitiveType.Cube, new Vector3(side * 0.31f, 0.2f, 0.18f), new Vector3(0.04f, 0.04f, 0.6f), M("8a6a44"), new Vector3(40, 0, 0));
                    }
                    break;
                case "bottle": // a green bottle with a rolled note inside
                    Part(b, PrimitiveType.Capsule, new Vector3(0, 0.08f, 0), new Vector3(0.14f, 0.16f, 0.14f), M("2a6a48"), new Vector3(0, 0, 90));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0.2f, 0.08f, 0), new Vector3(0.05f, 0.05f, 0.05f), M("2a6a48"), new Vector3(0, 0, 90));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0.25f, 0.08f, 0), new Vector3(0.04f, 0.02f, 0.04f), M("8a6a44"), new Vector3(0, 0, 90));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.08f, 0), new Vector3(0.05f, 0.1f, 0.05f), M("efe4cc"), new Vector3(0, 0, 90));
                    break;
                case "book": // the keeper's logbook, open
                    for (int side = -1; side <= 1; side += 2)
                    {
                        Part(b, PrimitiveType.Cube, new Vector3(side * 0.12f, 0.03f, 0), new Vector3(0.24f, 0.04f, 0.32f), M("3a2a5a"), new Vector3(0, 0, side * -6));
                        Part(b, PrimitiveType.Cube, new Vector3(side * 0.11f, 0.055f, 0), new Vector3(0.21f, 0.02f, 0.29f), M("efe4cc"), new Vector3(0, 0, side * -6));
                    }
                    break;
                case "tooth": // a gold tooth on a fish hook, hanging from a nail
                    Part(b, PrimitiveType.Cube, new Vector3(0, 1.4f, 0), new Vector3(0.04f, 0.04f, 0.1f), M("3a3a40"));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 1.25f, 0.04f), new Vector3(0.012f, 0.14f, 0.012f), M("c8c8d0"));
                    Part(b, PrimitiveType.Capsule, new Vector3(0, 1.08f, 0.04f), new Vector3(0.06f, 0.05f, 0.05f), M("ffcf5a", true));
                    break;
                case "anchor": // a tiny anchor charm on a coil of rope
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.04f, 0), new Vector3(0.36f, 0.04f, 0.36f), M("b0905a"));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.16f, 0), new Vector3(0.025f, 0.2f, 0.025f), M("c8a848"));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.07f, 0), new Vector3(0.14f, 0.025f, 0.025f), M("c8a848"));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.27f, 0), new Vector3(0.05f, 0.008f, 0.05f), M("c8a848"), new Vector3(90, 0, 0));
                    break;
                case "shell": // a big spiral shell
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.08f, 0), new Vector3(0.26f, 0.16f, 0.18f), M("f0d8c8"));
                    Part(b, PrimitiveType.Sphere, new Vector3(0.1f, 0.12f, 0), new Vector3(0.12f, 0.12f, 0.12f), M("e8b8a0"));
                    Part(b, PrimitiveType.Sphere, new Vector3(-0.08f, 0.07f, 0.06f), new Vector3(0.1f, 0.08f, 0.06f), M("f8a0a0"));
                    break;
                case "gem": // the figurehead's eye: a big green glass gem
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.1f, 0), new Vector3(0.18f, 0.14f, 0.18f), M("3aff9a", true));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.03f, 0), new Vector3(0.22f, 0.03f, 0.22f), M("8a6a44"));
                    break;
                case "map": // a rolled map tied with string, half open
                    Part(b, PrimitiveType.Cube, new Vector3(0.1f, 0.01f, 0), new Vector3(0.4f, 0.01f, 0.3f), M("d8c49a"));
                    Part(b, PrimitiveType.Cylinder, new Vector3(-0.12f, 0.04f, 0), new Vector3(0.07f, 0.16f, 0.07f), M("d8c49a"), new Vector3(90, 0, 0));
                    Part(b, PrimitiveType.Cube, new Vector3(0.15f, 0.02f, 0.05f), new Vector3(0.06f, 0.005f, 0.01f), M("a01c24"), new Vector3(0, 45, 0));
                    Part(b, PrimitiveType.Cube, new Vector3(0.15f, 0.02f, 0.05f), new Vector3(0.06f, 0.005f, 0.01f), M("a01c24"), new Vector3(0, -45, 0));
                    break;
                case "coin": // a gold doubloon, standing on its edge in the sand
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.09f, 0), new Vector3(0.18f, 0.01f, 0.18f), M("ffcf5a", true), new Vector3(80, 30, 0));
                    break;
                case "broom": // a broom handle with no bristles
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.75f, 0), new Vector3(0.035f, 0.75f, 0.035f), M("6a4a2a"), new Vector3(0, 0, 14));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0.03f, 0.1f, 0), new Vector3(0.09f, 0.05f, 0.09f), M("a08040"), new Vector3(0, 0, 14));
                    break;
                case "jar": // a jar of fireflies
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.12f, 0), new Vector3(0.16f, 0.12f, 0.16f), M("a8ffb0", true));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.25f, 0), new Vector3(0.17f, 0.02f, 0.17f), M("6a6a70"));
                    for (int i = 0; i < 4; i++)
                        Part(b, PrimitiveType.Sphere, new Vector3(Mathf.Cos(i * 1.6f) * 0.04f, 0.08f + i * 0.04f, Mathf.Sin(i * 1.6f) * 0.04f), Vector3.one * 0.025f, M("ffff80", true));
                    break;
                case "gnome": // a garden gnome, with fangs
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.14f, 0), new Vector3(0.22f, 0.14f, 0.22f), M("2a5a9a"));
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.34f, 0), Vector3.one * 0.18f, M("f0c8a8"));
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.27f, 0.05f), new Vector3(0.17f, 0.14f, 0.12f), M("f2efe8"));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.5f, 0), new Vector3(0.18f, 0.12f, 0.18f), M("c0282e"));
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.36f, 0.09f), Vector3.one * 0.05f, M("e89080"));
                    for (int side = -1; side <= 1; side += 2)
                    {
                        Part(b, PrimitiveType.Sphere, new Vector3(side * 0.04f, 0.39f, 0.08f), Vector3.one * 0.022f, M("1a1420"));
                        Part(b, PrimitiveType.Cube, new Vector3(side * 0.02f, 0.31f, 0.1f), new Vector3(0.012f, 0.03f, 0.01f), M("ffffff"));
                    }
                    break;
                case "watch": // a stopped pocket watch on its chain
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.02f, 0), new Vector3(0.14f, 0.015f, 0.14f), M("c8a848"));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.03f, 0), new Vector3(0.11f, 0.01f, 0.11f), M("f2efe8"));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.04f, 0.02f), new Vector3(0.008f, 0.004f, 0.05f), M("1a1420"));
                    Part(b, PrimitiveType.Cube, new Vector3(0.015f, 0.04f, 0), new Vector3(0.035f, 0.004f, 0.008f), M("1a1420"));
                    Part(b, PrimitiveType.Cube, new Vector3(-0.12f, 0.01f, 0.06f), new Vector3(0.14f, 0.01f, 0.01f), M("c8a848"), new Vector3(0, 30, 0));
                    break;
                case "sign": // a signpost pointing the wrong way
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.9f, 0), new Vector3(0.1f, 1.8f, 0.1f), M("5a4028"));
                    Part(b, PrimitiveType.Cube, new Vector3(0.3f, 1.55f, 0), new Vector3(0.7f, 0.2f, 0.04f), M("d8c49a"), new Vector3(0, 0, -8));
                    Part(b, PrimitiveType.Cube, new Vector3(-0.28f, 1.25f, 0), new Vector3(0.6f, 0.18f, 0.04f), M("c8b48a"), new Vector3(0, 0, 11));
                    break;
                case "shoe": // a single red dancing shoe
                    Part(b, PrimitiveType.Capsule, new Vector3(0, 0.05f, 0), new Vector3(0.1f, 0.13f, 0.06f), M("c0282e"), new Vector3(90, 0, 0));
                    Part(b, PrimitiveType.Cube, new Vector3(0, 0.05f, -0.1f), new Vector3(0.03f, 0.1f, 0.03f), M("c0282e"));
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.08f, 0.07f), Vector3.one * 0.035f, M("ffcf5a", true));
                    break;
                case "umbrella": // a black umbrella, open, upside down, bone dry
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.3f, 0), new Vector3(0.9f, 0.3f, 0.9f), M("16141c"), new Vector3(180, 0, 0));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0, 0.5f, 0), new Vector3(0.025f, 0.4f, 0.025f), M("3a3a40"));
                    Part(b, PrimitiveType.Cylinder, new Vector3(0.04f, 0.92f, 0), new Vector3(0.06f, 0.015f, 0.06f), M("6a4a2a"), new Vector3(0, 0, 90));
                    break;
                default:
                    Part(b, PrimitiveType.Sphere, new Vector3(0, 0.12f, 0), Vector3.one * 0.2f, M("b48cff", true));
                    break;
            }
        }

        static void Part(Transform parent, PrimitiveType type, Vector3 pos, Vector3 scale, Material mat, Vector3 euler = default)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localRotation = Quaternion.Euler(euler);
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
        }

        void OnEnable() => All.Add(this);
        void OnDisable() => All.Remove(this);

        public bool Found => ClubBook.HasCurio(Id);

        void Update()
        {
            bool found = Found;
            if (twinkle != null)
            {
                twinkle.gameObject.SetActive(!found);
                if (!found)
                {
                    float t = Time.time + phase;
                    twinkle.localRotation = Quaternion.Euler(0f, t * 90f, 0f);
                    twinkle.localScale = Vector3.one * (0.75f + 0.35f * Mathf.Max(0f, Mathf.Sin(t * 2.4f)));
                }
            }
            if (glint != null)
            {
                var cam = Camera.main;
                glint.enabled = !found && (cam == null || (cam.transform.position - transform.position).sqrMagnitude < LightDistance * LightDistance);
            }
        }

        public bool CanInteract(SolverController solver) => solver != null && !solver.IsRiding;

        public string GetPrompt(SolverController solver) => Found ? $"Look at {Lower(Title)} again" : $"Examine {Lower(Title)}";

        static string Lower(string s)
        {
            if (string.IsNullOrEmpty(s)) return "it";
            // "A stuffed raven" reads "Examine a stuffed raven"; a name like "Admit One, 31 Oct 1958" stays as it is.
            foreach (var w in new[] { "A ", "An ", "The ", "Half " })
                if (s.StartsWith(w, System.StringComparison.Ordinal)) return char.ToLowerInvariant(s[0]) + s.Substring(1);
            return s;
        }

        public void Interact(SolverController solver) { }

        public void LocalInteract(SolverController solver)
        {
            bool first = !Found;
            ClubBook.FoundCurio(Id, Title);
            GameHUD.Toast(first
                ? $"{Title}. {Lore} (Curiosity {ClubBook.CuriosFound} of {Total}, +10 candy.)"
                : $"{Title}. {Lore}");
            Sfx.Play2D("clue_chime", first ? 0.7f : 0.35f, first ? 1.7f : 1.4f);
        }
    }
}
