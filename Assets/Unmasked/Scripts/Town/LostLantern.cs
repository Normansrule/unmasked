using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The lost lanterns of Hollow Creek: little tin lanterns hidden around town (HollowCreek.json
    /// "collectibles", placed by Docs/tools/worldgen.py: one at every landmark, a few in places
    /// everyone knows, the rest in back yards). Walk into one to pick it up. Each player collects
    /// their own on their own computer (the Club Book keeps them), so nobody can take one before
    /// you get there; the ones you have found stay gone.
    /// </summary>
    public class LostLantern : MonoBehaviour
    {
        public const float PickupRadius = 1.6f;
        const float LightDistance = 45f;

        public string Id, Where;

        public static readonly List<LostLantern> All = new();

        Light glow;
        Transform body;
        float phase;

        /// <summary>Called by TownDirector: build every lantern this player hasn't found yet.</summary>
        public static void Ensure(GameObject host)
        {
            var town = TownLayout.Current;
            if (town?.collectibles == null || host.transform.Find("LostLanterns") != null) return;
            var root = new GameObject("LostLanterns").transform;
            root.SetParent(host.transform, false);
            var tin = Horizon.Lit("LanternTin", new Color(0.2f, 0.19f, 0.22f));
            var glass = Horizon.Lit("LanternGlass", new Color(1f, 0.78f, 0.42f), true);
            foreach (var c in town.collectibles)
            {
                if (c.p == null || c.p.Length < 3) continue;
                var go = new GameObject("LostLantern_" + c.id);
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(c.p[0], c.p[1], c.p[2]);
                var lantern = go.AddComponent<LostLantern>();
                lantern.Id = c.id;
                lantern.Where = c.where;
                lantern.Build(tin, glass);
            }
        }

        void Build(Material tin, Material glass)
        {
            body = new GameObject("Body").transform;
            body.SetParent(transform, false);
            Part(PrimitiveType.Cylinder, new Vector3(0, 0.03f, 0), new Vector3(0.26f, 0.03f, 0.26f), tin);
            Part(PrimitiveType.Cylinder, new Vector3(0, 0.2f, 0), new Vector3(0.2f, 0.14f, 0.2f), glass);
            for (int i = 0; i < 4; i++) // the frame's corner wires
            {
                float a = i * Mathf.PI / 2f + Mathf.PI / 4f;
                Part(PrimitiveType.Cube, new Vector3(Mathf.Cos(a) * 0.1f, 0.2f, Mathf.Sin(a) * 0.1f), new Vector3(0.02f, 0.3f, 0.02f), tin);
            }
            Part(PrimitiveType.Cylinder, new Vector3(0, 0.37f, 0), new Vector3(0.24f, 0.03f, 0.24f), tin);
            Part(PrimitiveType.Cylinder, new Vector3(0, 0.43f, 0), new Vector3(0.12f, 0.04f, 0.12f), tin);
            Part(PrimitiveType.Cube, new Vector3(0, 0.53f, 0), new Vector3(0.16f, 0.02f, 0.02f), tin);
            for (int side = -1; side <= 1; side += 2)
                Part(PrimitiveType.Cube, new Vector3(side * 0.08f, 0.49f, 0), new Vector3(0.02f, 0.09f, 0.02f), tin);
            body.localScale = Vector3.one * 1.4f;

            glow = new GameObject("Glow").AddComponent<Light>();
            glow.transform.SetParent(transform, false);
            glow.transform.localPosition = new Vector3(0, 0.45f, 0);
            glow.type = LightType.Point;
            glow.color = new Color(1f, 0.75f, 0.4f);
            glow.range = 4f;
            glow.intensity = 1.3f;
            glow.shadows = LightShadows.None;
            phase = (Id?.GetHashCode() ?? 0) % 100 * 0.1f;
        }

        void Part(PrimitiveType type, Vector3 pos, Vector3 scale, Material mat)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(body, false);
            go.transform.localPosition = pos;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
        }

        void OnEnable() => All.Add(this);
        void OnDisable() => All.Remove(this);

        void Update()
        {
            if (ClubBook.Has("lantern:" + Id)) { gameObject.SetActive(false); return; }

            // A slow sway, and the candle breathing.
            float t = Time.time + phase;
            if (body != null)
            {
                body.localPosition = new Vector3(0, 0.12f + Mathf.Sin(t * 1.3f) * 0.05f, 0);
                body.localRotation = Quaternion.Euler(Mathf.Sin(t * 0.9f) * 4f, t * 20f, 0);
            }
            var cam = Camera.main;
            if (glow != null)
            {
                glow.enabled = cam == null || (cam.transform.position - transform.position).sqrMagnitude < LightDistance * LightDistance;
                glow.intensity = 1.2f + Mathf.PerlinNoise(t * 2f, phase) * 0.4f;
            }

            var me = SolverController.Local;
            if (me == null) return;
            var d = me.transform.position - transform.position;
            d.y = 0f;
            if (d.sqrMagnitude < PickupRadius * PickupRadius && Mathf.Abs(me.transform.position.y - transform.position.y) < 2.5f)
            {
                ClubBook.FoundLantern(Id, Where);
                gameObject.SetActive(false);
            }
        }
    }
}
