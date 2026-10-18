using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The Fear Meter. Scares raise it (server only), it drains when things calm down (faster with
    /// friends nearby), and at max the Solver panics: they run away screaming and can't do anything
    /// until it wears off or a teammate calms them down.
    /// </summary>
    public class FearMeter : NetworkBehaviour
    {
        public float MaxFear = 100f;
        public float DecayPerSecond = 4f;
        [Tooltip("Seconds after the last scare before fear starts draining.")]
        public float DecayDelay = 3f;
        public float TeammateComfortRadius = 6f;
        [Tooltip("Each calm teammate nearby adds this much to the drain rate multiplier.")]
        public float DecayBonusPerTeammate = 0.75f;
        [Tooltip("Scares hurt less with your flashlight on.")]
        public float FlashlightOnFearMultiplier = 0.75f;
        public float PanicDuration = 8f;
        [Tooltip("Fear after recovering, so the next scare hits harder.")]
        public float FearAfterRecovery = 35f;
        [Tooltip("Kid-friendly no-fear custom mode.")]
        public bool FearEnabled = true;

        readonly NetworkVariable<float> fear = new();
        readonly NetworkVariable<bool> panicked = new();
        readonly NetworkVariable<Vector3> fleeDirection = new(Vector3.forward);

        public float Fear => fear.Value;
        public float Percent => MaxFear > 0 ? fear.Value / MaxFear : 0f;
        public bool IsPanicked => panicked.Value;
        public Vector3 FleeDirection => fleeDirection.Value;

        float lastScareTime = -1000f;
        float panicEndsAt;
        SolverController solver;

        void Awake() => solver = GetComponent<SolverController>();

        void Update()
        {
            if (!IsServer || !IsSpawned) return;

            if (panicked.Value)
            {
                if (Time.time >= panicEndsAt) Recover();
                return;
            }

            if (fear.Value <= 0f || Time.time - lastScareTime < DecayDelay) return;

            int teammates = 0;
            foreach (var other in SolverController.All)
                if (other != solver && !other.IsPanicked && Vector3.Distance(other.transform.position, transform.position) < TeammateComfortRadius)
                    teammates++;

            fear.Value = Mathf.Max(0f, fear.Value - DecayPerSecond * (1f + DecayBonusPerTeammate * teammates) * Time.deltaTime);
        }

        /// <summary>Server: scare this Solver.</summary>
        public void AddFear(float amount, Vector3 source)
        {
            if (!IsServer || !FearEnabled || panicked.Value || amount <= 0f) return;

            if (solver.Flashlight != null && solver.Flashlight.IsOn) amount *= FlashlightOnFearMultiplier;
            if (MysteryGameManager.Instance != null)
                amount *= MysteryGameManager.Instance.FearMultiplier * MysteryGameManager.Instance.WatchFearMultiplier; // night events, the Lantern Watch costume

            lastScareTime = Time.time;
            fear.Value = Mathf.Min(MaxFear, fear.Value + amount);
            if (fear.Value >= MaxFear) EnterPanic(source);
        }

        void EnterPanic(Vector3 source)
        {
            Vector3 away = transform.position - source;
            away.y = 0f;
            fleeDirection.Value = away.sqrMagnitude < 0.01f ? transform.forward : away.normalized;
            panicked.Value = true;
            panicEndsAt = Time.time + PanicDuration;

            if (solver.Flashlight != null) solver.Flashlight.ForceOff(); // dropped it while screaming
            MysteryGameManager.Instance.NotifySolverPanicked(solver);
        }

        /// <summary>Server: a teammate talks them down.</summary>
        public void CalmDown()
        {
            if (IsServer && panicked.Value) Recover();
        }

        void Recover()
        {
            panicked.Value = false;
            fear.Value = Mathf.Min(fear.Value, FearAfterRecovery);
            lastScareTime = Time.time;
        }

        /// <summary>
        /// Server: scare every Solver within radius of origin, half strength at the edge.
        /// Returns how many were scared.
        /// </summary>
        public static int ScareSolversInRadius(Vector3 origin, float radius, float amount, Transform ignore = null, bool requireLineOfSight = true)
        {
            SuspectNPC.StartleInRadius(origin, radius, ignore, requireLineOfSight); // the suspects get a fright too
            int scared = 0;
            foreach (var s in SolverController.All.ToArray())
            {
                float distance = Vector3.Distance(s.transform.position, origin);
                if (distance > radius) continue;

                if (requireLineOfSight && !HasLineOfSight(origin, s, ignore)) continue;

                s.Fear.AddFear(amount * Mathf.Lerp(1f, 0.5f, distance / radius), origin);
                scared++;
            }
            return scared;
        }

        static bool HasLineOfSight(Vector3 origin, SolverController s, Transform ignore)
        {
            Vector3 to = s.EyePosition - origin;
            foreach (var hit in Physics.RaycastAll(origin, to.normalized, to.magnitude, ~0, QueryTriggerInteraction.Ignore))
            {
                var root = hit.transform.root;
                if (root == s.transform.root || (ignore != null && root == ignore.root)) continue;
                return false;
            }
            return true;
        }
    }
}
