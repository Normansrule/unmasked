using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// A will-o'-the-wisp (round 35): once you've found three lost lanterns, little teal-green lights
    /// start rising off the creek. Walk up to one and it drifts away ahead of you, waiting when you
    /// fall behind, and leads you to a lost lantern you haven't found yet (the nearest one to the
    /// creek where it rose). When it gets there it circles the lantern and goes out. If every lantern
    /// is found but some aren't on the Hook Board, it leads you there instead.
    ///
    /// Only between cases (never during an investigation, a trap or the unmasking), only on your own
    /// computer, one at a time, with a rest between wisps. It floats over roofs rather than through
    /// them; you find your own way round.
    /// </summary>
    public class Wisp : MonoBehaviour
    {
        const int LanternsFirst = 3;      // how many lanterns you find on your own before wisps appear
        const float WakeDistance = 5f;    // walk this close and it sets off
        const float LeadDistance = 7f;    // it stays about this far ahead
        const float WaitDistance = 13f;   // further than this and it waits for you
        const float Speed = 4.2f;
        const float Rest = 75f;           // seconds between one wisp going out and the next rising (50 once the creek lamps are lit)

        enum State { Gone, Rising, Waiting, Leading, Arrived }

        public static Wisp Instance { get; private set; }
        /// <summary>Is a wisp out right now, and where (for the club camera).</summary>
        public bool Out => state != State.Gone;
        public Vector3 Position => orb != null ? orb.position : transform.position;
        void Awake() => Instance = this;
        void OnDestroy() { if (Instance == this) Instance = null; }

        State state = State.Gone;
        float stateAt, nextRise = 20f, phase;
        Vector3 target;
        string targetName;
        Light glow;
        Transform orb;
        TrailRenderer trail;

        /// <summary>Called by TownDirector: one wisp object for the whole town, reused.</summary>
        public static void Ensure(GameObject host)
        {
            if (TownLayout.Current == null || host.transform.Find("Wisp") != null) return;
            var go = new GameObject("Wisp");
            go.transform.SetParent(host.transform, false);
            go.AddComponent<Wisp>().Build();
        }

        void Build()
        {
            var core = Horizon.Lit("WispCore", new Color(0.72f, 1f, 0.88f), true);
            var halo = Horizon.Lit("WispHalo", new Color(0.36f, 0.85f, 0.78f), true);
            orb = new GameObject("Orb").transform;
            orb.SetParent(transform, false);
            Part(PrimitiveType.Sphere, Vector3.zero, Vector3.one * 0.16f, core);
            Part(PrimitiveType.Sphere, Vector3.zero, Vector3.one * 0.3f, halo);

            glow = orb.gameObject.AddComponent<Light>();
            glow.type = LightType.Point;
            glow.color = new Color(0.5f, 1f, 0.85f);
            glow.range = 6f;
            glow.shadows = LightShadows.None;

            trail = orb.gameObject.AddComponent<TrailRenderer>();
            trail.sharedMaterial = halo;
            trail.time = 0.9f;
            trail.widthCurve = AnimationCurve.EaseInOut(0f, 0.12f, 1f, 0f);
            trail.minVertexDistance = 0.08f;
            trail.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            Show(false);
        }

        void Part(PrimitiveType type, Vector3 pos, Vector3 scale, Material mat)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(orb, false);
            go.transform.localPosition = pos;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
        }

        void Show(bool on)
        {
            orb.gameObject.SetActive(on);
            if (on) trail.Clear();
        }

        void Set(State s)
        {
            state = s;
            stateAt = Time.time;
        }

        static bool BetweenCases()
        {
            var game = MysteryGameManager.Instance;
            if (game == null || !game.IsSpawned) return false;
            var p = game.Phase.Value;
            return p != MatchPhase.Investigation && p != MatchPhase.Trap && p != MatchPhase.Unmasking;
        }

        /// <summary>Where a wisp rising at `from` should lead, if anywhere.</summary>
        static bool PickTarget(Vector3 from, out Vector3 to, out string name)
        {
            to = default;
            name = null;
            var town = TownLayout.Current;
            if (town?.collectibles == null || ClubBook.Get("lanterns") < LanternsFirst) return false;
            float best = float.MaxValue;
            foreach (var c in town.collectibles)
            {
                if (ClubBook.Has("lantern:" + c.id) || c.p == null || c.p.Length < 3) continue;
                var p = new Vector3(c.p[0], c.p[1], c.p[2]);
                float d = (p - from).sqrMagnitude;
                if (d < best) { best = d; to = p; name = c.where; }
            }
            if (name != null) return true;
            if (ClubBook.LanternsToHang() > 0 && HookBoard.Instance != null)
            {
                to = HookBoard.Instance.transform.position + HookBoard.Instance.transform.forward * 2f;
                name = "the Hook Board";
                return true;
            }
            return false;
        }

        void Update()
        {
            float t = Time.time;
            var me = SolverController.Local;
            bool can = me != null && !me.IsRiding && BetweenCases();

            if (state == State.Gone)
            {
                if (!can || t < nextRise) return;
                var town = TownLayout.Current;
                var at = me.transform.position;
                if (Mathf.Abs(at.z - town.creekZ) > 45f) return; // they only rise near the creek
                var rise = new Vector3(at.x + Random.Range(-10f, 10f), 0.4f, town.creekZ + Random.Range(-2f, 2f));
                if (!PickTarget(rise, out target, out targetName)) { nextRise = t + 20f; return; }
                transform.position = rise;
                phase = Random.value * 10f;
                Show(true);
                Set(State.Rising);
                GameHUD.Toast("A little green light is rising off the creek...");
                return;
            }

            if (!can && state != State.Arrived) { GoOut(); return; }

            float bob = Mathf.Sin(t * 2.3f + phase) * 0.18f;
            glow.intensity = 1.2f + Mathf.PerlinNoise(t * 3f, phase) * 0.8f;
            var pos = transform.position;
            var toMe = me != null ? me.transform.position - pos : Vector3.zero;
            toMe.y = 0f;

            switch (state)
            {
                case State.Rising:
                    pos.y = Mathf.MoveTowards(pos.y, 1.5f, Time.deltaTime * 0.8f);
                    if (pos.y >= 1.49f) Set(State.Waiting);
                    break;

                case State.Waiting:
                    pos.y = 1.5f + bob;
                    if (toMe.magnitude < WakeDistance) Set(State.Leading);
                    if (t - stateAt > 90f) GoOut(); // nobody came
                    break;

                case State.Leading:
                {
                    var flat = target - pos;
                    flat.y = 0f;
                    if (flat.magnitude < 1.5f) { Arrive(); break; }
                    float behind = toMe.magnitude;
                    float speed = behind > WaitDistance ? 0f : behind > LeadDistance ? Speed * 0.5f : Speed;
                    var step = flat.normalized * speed * Time.deltaTime;
                    // Anything in the way at head height: float up over it.
                    bool blocked = Physics.Raycast(pos, flat.normalized, 2.5f, ~0, QueryTriggerInteraction.Ignore);
                    float cruise = blocked ? Mathf.Min(pos.y + 3f * Time.deltaTime * 4f, 9f) : Mathf.MoveTowards(pos.y, 1.5f + bob, Time.deltaTime * 2f);
                    pos += step;
                    pos.y = cruise;
                    break;
                }

                case State.Arrived:
                {
                    float a = (t - stateAt) * 3f;
                    pos = target + new Vector3(Mathf.Cos(a) * 0.9f, 1.2f + Mathf.Sin(a * 0.5f) * 0.2f, Mathf.Sin(a) * 0.9f);
                    float fade = 1f - Mathf.Clamp01((t - stateAt - 2f) / 1.5f);
                    glow.intensity *= fade;
                    orb.localScale = Vector3.one * Mathf.Max(0.01f, fade);
                    if (fade <= 0f) GoOut();
                    break;
                }
            }
            transform.position = pos;
        }

        void Arrive()
        {
            Set(State.Arrived);
            ClubBook.FollowedWisp();
            GameHUD.Toast(targetName == "the Hook Board"
                ? "The wisp circles the Hook Board and goes out. You've lanterns to hang."
                : $"The wisp circles something in the dark near {targetName}, and goes out.");
        }

        void GoOut()
        {
            Show(false);
            orb.localScale = Vector3.one;
            Set(State.Gone);
            nextRise = Time.time + (Lamplighter.AllLit ? Rest * 0.66f : Rest); // a lit path draws them
        }
    }
}
