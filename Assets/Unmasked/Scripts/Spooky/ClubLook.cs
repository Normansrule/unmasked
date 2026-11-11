using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Puts each Solver's Club Book look on them: a hat, something on their back and the colour of
    /// their flashlight beam, all earned with candy in the Wardrobe (<see cref="ClubBook.Wardrobe"/>).
    /// Built from plain shapes at runtime, fitted to whichever role outfit is showing, on every
    /// machine (the look travels as one number, <see cref="PlayerAgent.Look"/>). Cosmetic only:
    /// nothing here changes how anyone plays.
    /// </summary>
    public class ClubLook : MonoBehaviour
    {
        static readonly Color DefaultBeam = new(1f, 0.95f, 0.8f);

        /// <summary>Hat, back and beam as indexes into the Wardrobe (-1 = nothing), packed into one number.</summary>
        public static int Pack(int hat, int back, int beam) => (hat + 1) | ((back + 1) << 8) | ((beam + 1) << 16);

        public static (int hat, int back, int beam) Unpack(int look) => ((look & 0xff) - 1, ((look >> 8) & 0xff) - 1, ((look >> 16) & 0xff) - 1);

        /// <summary>Server check on what a client sends: every part is nothing, or a Wardrobe item of the right slot.</summary>
        public static bool Valid(int look)
        {
            if (look < 0 || look >= 1 << 24) return false;
            var (hat, back, beam) = Unpack(look);
            return Fits(hat, "hat") && Fits(back, "back") && Fits(beam, "beam");
        }

        static bool Fits(int index, string slot) => index == -1 || (index >= 0 && index < ClubBook.Wardrobe.Length && ClubBook.Wardrobe[index].Slot == slot);

        readonly Dictionary<SolverController, int> shown = new();
        readonly Dictionary<Color, Material> mats = new();
        float nextCheck;

        void Update()
        {
            if (Time.unscaledTime < nextCheck) return;
            nextCheck = Time.unscaledTime + 0.25f;
            foreach (var solver in SolverController.All)
            {
                if (solver == null || !solver.IsSpawned) continue;
                var agent = PlayerAgent.ForClient(solver.OwnerClientId);
                int look = agent != null ? agent.Look.Value : 0;
                int key = look * 8 + (agent != null ? (int)agent.Role.Value : 0);
                if (shown.TryGetValue(solver, out int was) && was == key) continue;
                shown[solver] = key;
                Dress(solver, look, agent != null ? agent.Role.Value : SolverRole.Sleuth);
            }
            // forget pawns that are gone
            var gone = new List<SolverController>();
            foreach (var kv in shown) if (kv.Key == null) gone.Add(kv.Key);
            foreach (var g in gone) shown.Remove(g);
        }

        void Dress(SolverController solver, int look, SolverRole role)
        {
            var model = solver.transform.Find("Model");
            if (model == null) return;
            var old = model.Find("ClubLook");
            if (old != null) Destroy(old.gameObject);
            var (hat, back, beam) = Unpack(look);

            var beamLight = solver.transform.Find("Flashlight")?.GetComponent<Light>();
            if (beamLight != null) beamLight.color = beam >= 0 ? ClubBook.Wardrobe[beam].A : DefaultBeam;
            if (hat < 0 && back < 0) return;

            var root = new GameObject("ClubLook").transform;
            root.SetParent(model, false);

            // Fit to the role showing: the top of its head, and its back.
            Vector3 top = new(0f, 1.97f, 0f);
            float r = 0.17f;
            var outfit = model.Find("Outfits/" + role);
            var head = outfit != null ? FindDeep(outfit, "Head") : null;
            var headRenderer = head != null ? head.GetComponent<Renderer>() : null;
            if (headRenderer != null)
            {
                var b = headRenderer.bounds;
                top = model.InverseTransformPoint(new Vector3(b.center.x, b.max.y, b.center.z));
                r = b.extents.x / Mathf.Max(0.01f, model.lossyScale.x);
            }
            float s = r / 0.17f; // the shapes below are sized for a 0.17 m head
            float chest = top.y - 0.62f * s;

            if (hat >= 0) Hat(root, ClubBook.Wardrobe[hat], top, s);
            if (back >= 0) Back(root, ClubBook.Wardrobe[back], new Vector3(0f, chest, -0.2f * s), s);
        }

        void Hat(Transform root, ClubBook.Item item, Vector3 top, float s)
        {
            Color a = item.A, b = item.B;
            switch (item.Id)
            {
                case "cat-ears":
                    for (int side = -1; side <= 1; side += 2)
                    {
                        P(root, PrimitiveType.Cube, top + new Vector3(side * 0.09f, 0.02f, -0.01f) * s, new Vector3(0.09f, 0.09f, 0.025f) * s, a, false, new Vector3(0, 0, 45));
                        P(root, PrimitiveType.Cube, top + new Vector3(side * 0.09f, 0.015f, 0.005f) * s, new Vector3(0.05f, 0.05f, 0.01f) * s, b, false, new Vector3(0, 0, 45));
                    }
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, -0.02f, 0) * s, new Vector3(0.33f, 0.008f, 0.33f) * s, a);
                    break;
                case "leaf-crown":
                    for (int i = 0; i < 9; i++)
                    {
                        float ang = i / 9f * Mathf.PI * 2f;
                        P(root, PrimitiveType.Sphere, top + new Vector3(Mathf.Sin(ang) * 0.16f, -0.035f, Mathf.Cos(ang) * 0.16f) * s,
                          new Vector3(0.09f, 0.04f, 0.07f) * s, i % 2 == 0 ? a : b, false, new Vector3(0, ang * Mathf.Rad2Deg, 20));
                    }
                    break;
                case "top-hat":
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, 0.0f, 0) * s, new Vector3(0.42f, 0.01f, 0.42f) * s, a);
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, 0.12f, 0) * s, new Vector3(0.27f, 0.12f, 0.27f) * s, a);
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, 0.04f, 0) * s, new Vector3(0.275f, 0.025f, 0.275f) * s, b);
                    break;
                case "tricorn":
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, 0.03f, 0) * s, new Vector3(0.28f, 0.05f, 0.28f) * s, a);
                    for (int i = 0; i < 3; i++)
                    {
                        float ang = i * 120f;
                        var dir = Quaternion.Euler(0, ang, 0) * Vector3.forward;
                        P(root, PrimitiveType.Cube, top + (dir * 0.15f + new Vector3(0, 0.05f, 0)) * s, new Vector3(0.3f, 0.09f, 0.025f) * s, a, false, new Vector3(-12, ang, 0));
                        P(root, PrimitiveType.Cube, top + (dir * 0.163f + new Vector3(0, 0.095f, 0)) * s, new Vector3(0.3f, 0.012f, 0.012f) * s, b, false, new Vector3(-12, ang, 0));
                    }
                    break;
                case "witch-hat":
                case "wizard-hat":
                {
                    bool wizard = item.Id == "wizard-hat";
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, -0.005f, 0) * s, new Vector3(wizard ? 0.42f : 0.52f, 0.008f, wizard ? 0.42f : 0.52f) * s, a);
                    int steps = 5;
                    float h = wizard ? 0.46f : 0.36f;
                    for (int i = 0; i < steps; i++)
                    {
                        float w = Mathf.Lerp(0.28f, 0.05f, i / (float)(steps - 1));
                        var lean = new Vector3(0, 0, wizard ? 0 : -i * 0.012f);
                        P(root, PrimitiveType.Cylinder, top + (new Vector3(0, 0.02f + (i + 0.5f) * h / steps, 0) + lean) * s, new Vector3(w, h / steps / 2f, w) * s, a);
                    }
                    if (!wizard) P(root, PrimitiveType.Cube, top + new Vector3(0, 0.02f + h + 0.02f, -0.1f) * s, new Vector3(0.03f, 0.03f, 0.12f) * s, a, false, new Vector3(-30, 0, 0));
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, 0.04f, 0) * s, new Vector3(0.285f, 0.02f, 0.285f) * s, b);
                    if (wizard)
                        for (int i = 0; i < 4; i++)
                            P(root, PrimitiveType.Sphere, top + new Vector3(Mathf.Sin(i * 1.7f) * 0.09f, 0.12f + i * 0.08f, Mathf.Cos(i * 1.7f) * 0.09f) * s,
                              Vector3.one * 0.03f * s, b, true);
                    break;
                }
                case "antlers":
                    for (int side = -1; side <= 1; side += 2)
                    {
                        var basePos = top + new Vector3(side * 0.08f, -0.01f, 0) * s;
                        P(root, PrimitiveType.Capsule, basePos + new Vector3(side * 0.06f, 0.1f, 0) * s, new Vector3(0.03f, 0.1f, 0.03f) * s, a, false, new Vector3(0, 0, -side * 30));
                        P(root, PrimitiveType.Capsule, basePos + new Vector3(side * 0.15f, 0.2f, 0) * s, new Vector3(0.025f, 0.07f, 0.025f) * s, a, false, new Vector3(0, 0, -side * 60));
                        P(root, PrimitiveType.Capsule, basePos + new Vector3(side * 0.08f, 0.25f, 0.02f) * s, new Vector3(0.022f, 0.06f, 0.022f) * s, a, false, new Vector3(10, 0, side * 10));
                    }
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, -0.03f, 0) * s, new Vector3(0.33f, 0.008f, 0.33f) * s, b);
                    break;
                case "halo":
                    for (int i = 0; i < 14; i++)
                    {
                        float ang = i / 14f * Mathf.PI * 2f;
                        P(root, PrimitiveType.Sphere, top + new Vector3(Mathf.Sin(ang) * 0.14f, 0.12f, Mathf.Cos(ang) * 0.14f) * s, Vector3.one * 0.035f * s, a, true);
                    }
                    break;
                case "pumpkin-head":
                {
                    var centre = top - new Vector3(0, 0.17f, 0) * s;
                    P(root, PrimitiveType.Sphere, centre, new Vector3(0.48f, 0.42f, 0.46f) * s, a);
                    for (int i = 0; i < 4; i++) // ribs
                        P(root, PrimitiveType.Sphere, centre, new Vector3(0.18f, 0.43f, 0.47f) * s, a * 0.9f, false, new Vector3(0, i * 45, 0));
                    P(root, PrimitiveType.Cylinder, centre + new Vector3(0, 0.23f, 0) * s, new Vector3(0.05f, 0.04f, 0.05f) * s, new Color(0.24f, 0.42f, 0.16f));
                    for (int side = -1; side <= 1; side += 2)
                        P(root, PrimitiveType.Cube, centre + new Vector3(side * 0.08f, 0.05f, 0.225f) * s, new Vector3(0.06f, 0.05f, 0.02f) * s, b, true, new Vector3(0, 0, 45));
                    P(root, PrimitiveType.Cube, centre + new Vector3(0, -0.07f, 0.215f) * s, new Vector3(0.16f, 0.035f, 0.02f) * s, b, true);
                    break;
                }
                case "lamplighter-cap":
                    P(root, PrimitiveType.Sphere, top + new Vector3(0, -0.005f, -0.01f) * s, new Vector3(0.36f, 0.13f, 0.37f) * s, a);
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, -0.035f, 0) * s, new Vector3(0.345f, 0.025f, 0.355f) * s, a * 0.8f);
                    P(root, PrimitiveType.Cube, top + new Vector3(0, -0.04f, 0.17f) * s, new Vector3(0.25f, 0.02f, 0.12f) * s, a * 0.7f, false, new Vector3(10, 0, 0));
                    P(root, PrimitiveType.Cube, top + new Vector3(0, -0.005f, 0.178f) * s, new Vector3(0.05f, 0.06f, 0.01f) * s, b, true);
                    break;
                case "buster-cap":
                    // a peaked cap: a soft crown, a stiff peak, a button on top and a little sheet-ghost badge
                    P(root, PrimitiveType.Sphere, top + new Vector3(0, 0.05f, 0) * s, new Vector3(0.36f, 0.2f, 0.37f) * s, a);
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, -0.005f, 0.2f) * s, new Vector3(0.3f, 0.01f, 0.2f) * s, a * 0.8f, false, new Vector3(-8, 0, 0));
                    P(root, PrimitiveType.Sphere, top + new Vector3(0, 0.15f, 0) * s, Vector3.one * 0.04f * s, a * 0.8f);
                    P(root, PrimitiveType.Sphere, top + new Vector3(0, 0.07f, 0.175f) * s, new Vector3(0.07f, 0.08f, 0.02f) * s, b, true);
                    P(root, PrimitiveType.Sphere, top + new Vector3(-0.012f, 0.08f, 0.186f) * s, Vector3.one * 0.012f * s, new Color(0.1f, 0.08f, 0.12f));
                    P(root, PrimitiveType.Sphere, top + new Vector3(0.012f, 0.08f, 0.186f) * s, Vector3.one * 0.012f * s, new Color(0.1f, 0.08f, 0.12f));
                    break;
                case "explorer-hat":
                    // a wide-brimmed field hat: brim, crown with a dent, leather band and a brass compass pin
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, -0.01f, 0) * s, new Vector3(0.62f, 0.012f, 0.62f) * s, a, false, new Vector3(-4, 0, 0));
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, 0.07f, 0) * s, new Vector3(0.3f, 0.075f, 0.3f) * s, a * 0.95f);
                    P(root, PrimitiveType.Sphere, top + new Vector3(0, 0.14f, 0) * s, new Vector3(0.3f, 0.07f, 0.3f) * s, a * 0.95f);
                    P(root, PrimitiveType.Cube, top + new Vector3(0, 0.17f, 0) * s, new Vector3(0.03f, 0.03f, 0.22f) * s, a * 0.7f);
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, 0.025f, 0) * s, new Vector3(0.305f, 0.022f, 0.305f) * s, b);
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0.1f, 0.03f, 0.13f) * s, new Vector3(0.05f, 0.006f, 0.05f) * s, new Color(0.85f, 0.68f, 0.32f), true, new Vector3(90, 0, -35));
                    break;
                case "scarecrow-hat":
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, -0.005f, 0) * s, new Vector3(0.58f, 0.012f, 0.58f) * s, a, false, new Vector3(4, 0, -3));
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, 0.07f, 0) * s, new Vector3(0.27f, 0.07f, 0.27f) * s, a * 0.92f);
                    P(root, PrimitiveType.Cylinder, top + new Vector3(0, 0.025f, 0) * s, new Vector3(0.275f, 0.018f, 0.275f) * s, b);
                    P(root, PrimitiveType.Cube, top + new Vector3(0.07f, 0.08f, 0.13f) * s, new Vector3(0.07f, 0.06f, 0.01f) * s, b * 1.3f, false, new Vector3(0, 0, 12));
                    P(root, PrimitiveType.Capsule, top + new Vector3(-0.14f, 0.12f, 0.02f) * s, new Vector3(0.015f, 0.09f, 0.03f) * s, new Color(0.08f, 0.08f, 0.1f), false, new Vector3(0, 0, 30));
                    for (int i = 0; i < 6; i++) // straw poking out under the brim
                    {
                        float ang = i / 6f * Mathf.PI * 2f + 0.4f;
                        P(root, PrimitiveType.Cube, top + new Vector3(Mathf.Sin(ang) * 0.27f, -0.03f, Mathf.Cos(ang) * 0.27f) * s,
                          new Vector3(0.012f, 0.012f, 0.08f) * s, a * 1.1f, false, new Vector3(25, ang * Mathf.Rad2Deg, 0));
                    }
                    break;
                default:
                    P(root, PrimitiveType.Cylinder, top, new Vector3(0.3f, 0.06f, 0.3f) * s, a);
                    break;
            }
        }

        void Back(Transform root, ClubBook.Item item, Vector3 at, float s)
        {
            Color a = item.A, b = item.B;
            switch (item.Id)
            {
                case "cape":
                    P(root, PrimitiveType.Cube, at + new Vector3(0, -0.28f, -0.03f) * s, new Vector3(0.58f, 0.95f, 0.03f) * s, a, false, new Vector3(8, 0, 0));
                    P(root, PrimitiveType.Cube, at + new Vector3(0, -0.28f, -0.01f) * s, new Vector3(0.54f, 0.9f, 0.01f) * s, b, false, new Vector3(8, 0, 0));
                    for (int side = -1; side <= 1; side += 2)
                        P(root, PrimitiveType.Cube, at + new Vector3(side * 0.16f, 0.27f, 0.1f) * s, new Vector3(0.2f, 0.2f, 0.02f) * s, a, false, new Vector3(-10, side * 35, 0));
                    break;
                case "bat-wings":
                    for (int side = -1; side <= 1; side += 2)
                    {
                        var euler = new Vector3(0, side * 25, side * 20);
                        P(root, PrimitiveType.Cube, at + new Vector3(side * 0.32f, 0.08f, -0.06f) * s, new Vector3(0.5f, 0.28f, 0.02f) * s, a, false, euler);
                        for (int k = 0; k < 3; k++)
                            P(root, PrimitiveType.Capsule, at + new Vector3(side * (0.16f + k * 0.15f), -0.03f - k * 0.04f, -0.06f) * s, new Vector3(0.025f, 0.08f, 0.025f) * s, b, false, euler);
                    }
                    break;
                case "lantern-pack":
                    P(root, PrimitiveType.Cube, at + new Vector3(0, -0.05f, -0.04f) * s, new Vector3(0.32f, 0.38f, 0.15f) * s, a);
                    P(root, PrimitiveType.Cube, at + new Vector3(0, 0.08f, -0.08f) * s, new Vector3(0.33f, 0.12f, 0.12f) * s, a * 0.8f);
                    P(root, PrimitiveType.Cylinder, at + new Vector3(0.2f, 0.2f, -0.06f) * s, new Vector3(0.09f, 0.07f, 0.09f) * s, b, true);
                    P(root, PrimitiveType.Cylinder, at + new Vector3(0.2f, 0.29f, -0.06f) * s, new Vector3(0.11f, 0.015f, 0.11f) * s, new Color(0.15f, 0.15f, 0.17f));
                    break;
                case "candy-pail":
                {
                    // carried at the hip: a jack-o'-lantern pail with a black handle and a carved face
                    var c = at + new Vector3(0.34f, -0.5f, 0.16f) * s;
                    P(root, PrimitiveType.Cylinder, c, new Vector3(0.2f, 0.09f, 0.2f) * s, a);
                    P(root, PrimitiveType.Sphere, c + new Vector3(0, -0.06f, 0) * s, new Vector3(0.2f, 0.1f, 0.2f) * s, a);
                    P(root, PrimitiveType.Cube, c + new Vector3(0, 0.2f, 0) * s, new Vector3(0.18f, 0.015f, 0.015f) * s, b);
                    for (int side = -1; side <= 1; side += 2)
                    {
                        P(root, PrimitiveType.Cube, c + new Vector3(side * 0.09f, 0.14f, 0) * s, new Vector3(0.015f, 0.12f, 0.015f) * s, b);
                        P(root, PrimitiveType.Cube, c + new Vector3(side * 0.04f, 0.025f, 0.098f) * s, new Vector3(0.035f, 0.03f, 0.01f) * s, b, false, new Vector3(0, 0, 45));
                    }
                    P(root, PrimitiveType.Cube, c + new Vector3(0, -0.035f, 0.098f) * s, new Vector3(0.09f, 0.02f, 0.01f) * s, b);
                    break;
                }
                case "pocket-ghost":
                {
                    var c = at + new Vector3(0.38f, 0.58f, -0.12f) * s;
                    P(root, PrimitiveType.Sphere, c, new Vector3(0.2f, 0.24f, 0.2f) * s, a, true);
                    P(root, PrimitiveType.Sphere, c + new Vector3(0, -0.1f, 0) * s, new Vector3(0.22f, 0.12f, 0.22f) * s, a, true);
                    for (int side = -1; side <= 1; side += 2)
                        P(root, PrimitiveType.Sphere, c + new Vector3(side * 0.04f, 0.03f, 0.09f) * s, new Vector3(0.03f, 0.045f, 0.02f) * s, b);
                    break;
                }
            }
        }

        static Transform FindDeep(Transform t, string name)
        {
            if (t.name == name) return t;
            foreach (Transform child in t)
            {
                var hit = FindDeep(child, name);
                if (hit != null) return hit;
            }
            return null;
        }

        void P(Transform parent, PrimitiveType type, Vector3 pos, Vector3 scale, Color c, bool glow = false, Vector3 euler = default)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.SetLocalPositionAndRotation(pos, Quaternion.Euler(euler));
            go.transform.localScale = scale;
            var key = new Color(c.r, c.g, c.b, glow ? 0.5f : 1f);
            if (!mats.TryGetValue(key, out var mat)) mats[key] = mat = Horizon.Lit("ClubLook", new Color(c.r, c.g, c.b), glow);
            go.GetComponent<Renderer>().sharedMaterial = mat;
        }
    }
}
