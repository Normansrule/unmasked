using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Haunter power: a phantom that drifts toward the nearest Solver and pops in their face. Holding a
    /// flashlight beam on it dispels it ("it was just a sheet on a coat rack!").
    /// </summary>
    public class PhantomIllusion : NetworkBehaviour
    {
        public float FloatSpeed = 2.6f;
        public float PopDistance = 1.2f;
        [Tooltip("Seconds of flashlight needed to dispel it.")]
        public float DispelTime = 0.6f;

        float fear = 25f;
        float seekRadius = 15f;
        float despawnAt;
        float litTime;
        bool vanishing;

        /// <summary>Server, before spawning.</summary>
        public void Initialize(float fearAmount, float duration, float radius)
        {
            fear = fearAmount;
            seekRadius = radius;
            despawnAt = Time.time + duration;
        }

        void Update()
        {
            if (!IsServer || !IsSpawned || vanishing) return;

            if (Time.time >= despawnAt) { Vanish(false); return; }

            if (Lit()) { litTime += Time.deltaTime; if (litTime >= DispelTime) { Vanish(false); return; } }
            else litTime = Mathf.Max(0f, litTime - Time.deltaTime);

            SolverController target = null;
            float best = seekRadius;
            foreach (var s in SolverController.All)
            {
                float d = Vector3.Distance(s.transform.position, transform.position);
                if (d < best && !s.IsPanicked) { best = d; target = s; }
            }
            if (target == null) return;

            Vector3 to = target.EyePosition - transform.position;
            if (to.magnitude <= PopDistance)
            {
                target.Fear.AddFear(fear, transform.position);
                Vanish(true);
                return;
            }

            Vector3 bob = Vector3.up * Mathf.Sin(Time.time * 4f) * 0.4f * Time.deltaTime;
            transform.position += to.normalized * FloatSpeed * Time.deltaTime + bob;
            transform.rotation = Quaternion.LookRotation(new Vector3(to.x, 0f, to.z));
        }

        bool Lit()
        {
            foreach (var s in SolverController.All)
            {
                if (s.Flashlight == null || !s.Flashlight.IsPointInBeam(transform.position)) continue;
                Vector3 from = s.Flashlight.transform.position;
                if (!Physics.Linecast(from, transform.position, out var hit, ~0, QueryTriggerInteraction.Ignore)
                    || hit.transform.root == transform.root)
                    return true;
            }
            return false;
        }

        void Vanish(bool scaredSomeone)
        {
            vanishing = true;
            VanishRpc(scaredSomeone);
            Invoke(nameof(DespawnSelf), 0.5f);
        }

        void DespawnSelf()
        {
            if (IsSpawned) NetworkObject.Despawn();
        }

        [Rpc(SendTo.ClientsAndHost)]
        void VanishRpc(bool scaredSomeone)
        {
            // TODO(Polish): "BOO!" pop vs. "just a sheet" fizzle effects.
            foreach (var r in GetComponentsInChildren<Renderer>()) r.enabled = false;
            foreach (var l in GetComponentsInChildren<Light>()) l.enabled = false;
            SpookyFX.Play(scaredSomeone ? SpookyFxKind.Hex : SpookyFxKind.Wisps, transform.position);
            if (scaredSomeone) Sfx.Play("ghost_moan", transform.position, 0.9f, 25f);
        }
    }
}
