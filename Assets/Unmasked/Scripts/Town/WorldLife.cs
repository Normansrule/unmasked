using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The world past the edge of town, alive (round 39). The six haunted places (HollowCreek.json
    /// "regions", built by Docs/tools/regions.py) are boxes like the rest of town; a few named pieces
    /// move, and this makes them:
    ///
    ///   Spin_Flag*, Spin_BigTopFlag   flutter in the wind
    ///   Spin_Ferris*                  the Ferris wheel turns round its hub; the cars stay upright
    ///   Spin_*Beam                    the lighthouse beam sweeps round the lamp
    ///   Spin_* (anything else)        turns slowly on the spot (the carousel, the circus spotlight)
    ///   Blink_*                       blinks (the beacon on top of Gloamwood Tower)
    ///   Bob_*                         bobs (the crane hook, the lantern on the wreck, the witch's chimney smoke)
    ///
    /// It also notices when you arrive somewhere new: the first time you set foot in one of the
    /// haunted places the Club Book marks it (+15 candy) and tells you about it, and climbing to the
    /// top of Saltmarsh Lighthouse or Gloamwood Tower counts too. All on this computer only.
    /// </summary>
    public class WorldLife : MonoBehaviour
    {
        public const int Places = 6;

        /// <summary>True for a layout box that moves at runtime, so the builder leaves it out of static batching.</summary>
        public static bool Moves(string name) =>
            name != null && (name.StartsWith("Spin_") || name.StartsWith("Blink_") || name.StartsWith("Bob_"));

        class Mover
        {
            public Transform t;
            public Vector3 pos, pivot;
            public Quaternion rot;
            public float offset, phase;
            public Renderer renderer;
        }

        readonly List<Mover> flutters = new(), spins = new(), beams = new(), bobs = new(), blinks = new(), ferrisArms = new(), ferrisCars = new();
        Vector3 ferrisHub;
        TownLayout town;
        ManorLayout.Room lighthouseTop, towerRoof;
        string inRegion;
        float nextCheck;

        public static void Ensure(GameObject host)
        {
            if (host.GetComponent<WorldLife>() == null) host.AddComponent<WorldLife>();
        }

        void Start()
        {
            town = TownLayout.Current;
            if (town?.rooms != null)
                foreach (var room in town.rooms)
                {
                    if (room.n == "Saltmarsh Lighthouse") lighthouseTop = room;
                    if (room.n == "The roof of Gloamwood Tower") towerRoof = room;
                }

            // Find the moving pieces once (the town is built in the editor, so they're already in the scene).
            var all = FindObjectsByType<Transform>(FindObjectsSortMode.None);
            foreach (var t in all)
            {
                string n = t.name;
                if (!Moves(n)) continue;
                var m = new Mover { t = t, pos = t.position, rot = t.rotation, phase = (n.GetHashCode() & 255) / 40f, renderer = t.GetComponent<Renderer>() };
                if (n.StartsWith("Spin_Ferris")) (n.Contains("Car") ? ferrisCars : ferrisArms).Add(m);
                else if (n.StartsWith("Spin_") && n.Contains("Flag")) flutters.Add(m);
                else if (n.StartsWith("Spin_") && n.EndsWith("Beam"))
                {
                    // Turns round its near end: the lamp it shines out of.
                    m.pivot = t.position - t.right * t.lossyScale.x / 2f;
                    beams.Add(m);
                }
                else if (n.StartsWith("Spin_")) spins.Add(m);
                else if (n.StartsWith("Bob_")) bobs.Add(m);
                else blinks.Add(m);
            }
            foreach (var m in ferrisArms)
                if (m.t.name == "Spin_FerrisSpoke0") ferrisHub = m.pos;
            foreach (var m in ferrisCars) m.offset = 1f; // cars hang a metre below the rim
        }

        void Update()
        {
            float t = Time.time;
            foreach (var m in flutters)
                m.t.rotation = m.rot * Quaternion.Euler(0f, Mathf.Sin(t * 2.3f + m.phase) * 18f + Mathf.Sin(t * 5.1f + m.phase) * 6f, 0f);
            foreach (var m in spins)
                m.t.rotation = Quaternion.Euler(0f, t * (m.t.name.Contains("Carousel") ? 14f : 40f), 0f) * m.rot;
            foreach (var m in beams)
            {
                var q = Quaternion.Euler(0f, t * 30f, 0f);
                m.t.SetPositionAndRotation(m.pivot + q * (m.pos - m.pivot), q * m.rot);
            }
            // The Ferris wheel: one slow turn every 80 seconds round the hub; the cars swing level.
            var wheel = Quaternion.Euler(0f, 0f, t * 4.5f);
            foreach (var m in ferrisArms)
                m.t.SetPositionAndRotation(ferrisHub + wheel * (m.pos - ferrisHub), wheel * m.rot);
            foreach (var m in ferrisCars)
            {
                var rim = m.pos + Vector3.up * m.offset;
                m.t.position = ferrisHub + wheel * (rim - ferrisHub) - Vector3.up * m.offset;
            }
            foreach (var m in bobs)
                m.t.position = m.pos + Vector3.up * Mathf.Sin(t * 1.1f + m.phase) * (m.t.name.Contains("Smoke") ? 0.6f : 0.25f);
            foreach (var m in blinks)
                if (m.renderer != null) m.renderer.enabled = Mathf.Repeat(t, 1.6f) < 0.8f;

            if (t >= nextCheck)
            {
                nextCheck = t + 0.5f;
                CheckWhereYouAre();
            }
        }

        void CheckWhereYouAre()
        {
            var me = SolverController.Local != null ? SolverController.Local.transform : HaunterController.Local != null ? HaunterController.Local.transform : null;
            if (me == null || town?.regions == null) return;
            var p = me.position;

            string now = null;
            foreach (var region in town.regions)
            {
                if (!region.Contains(p)) continue;
                now = region.id;
                if (now != inRegion)
                {
                    if (ClubBook.VisitedRegion(region.id, region.n))
                    {
                        GameHUD.Toast($"{region.n}. {region.blurb} (Place {ClubBook.RegionsVisited} of {Places}, +15 candy.)");
                        Sfx.Play2D("clue_chime", 0.6f, 0.9f);
                    }
                    else GameHUD.Toast(region.n);
                }
                break;
            }
            inRegion = now;

            if (Inside(lighthouseTop, p) && p.y > 19f) ClubBook.Climbed("lighthouse");
            if (Inside(towerRoof, p)) ClubBook.Climbed("tower");
        }

        static bool Inside(ManorLayout.Room r, Vector3 p) =>
            r?.min != null && r.max != null && p.x >= r.min[0] && p.x <= r.max[0] && p.y >= r.min[1] && p.y <= r.max[1] && p.z >= r.min[2] && p.z <= r.max[2];
    }
}
