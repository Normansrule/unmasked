using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The Headless Horseman's flaming jack-o'-lantern. Flies in an arc (simulated on the server, synced by
    /// NetworkTransform) and bursts on the first thing it hits: every Solver in sight of the burst gets a scare.
    /// </summary>
    public class PumpkinProjectile : NetworkBehaviour
    {
        public float Gravity = -14f;
        public float SpinSpeed = 540f;

        Vector3 velocity;
        float fear = 30f, burstRadius = 3.5f, flightTime = 1f, age;
        bool burst;

        /// <summary>Server, before spawning: aim so the arc lands on target.</summary>
        public void Initialize(Vector3 target, float fearAmount, float radius)
        {
            fear = fearAmount;
            burstRadius = radius;
            Vector3 to = target - transform.position;
            flightTime = Mathf.Clamp(new Vector3(to.x, 0f, to.z).magnitude / 12f, 0.45f, 1.4f);
            velocity = to / flightTime - 0.5f * Gravity * flightTime * Vector3.up;
        }

        void Update()
        {
            if (!IsServer || !IsSpawned || burst) return;
            age += Time.deltaTime;
            Vector3 step = velocity * Time.deltaTime;
            velocity += Vector3.up * Gravity * Time.deltaTime;
            transform.Rotate(SpinSpeed * Time.deltaTime, SpinSpeed * 0.3f * Time.deltaTime, 0f, Space.Self);

            if (age > 0.08f && Physics.Raycast(transform.position, step.normalized, out var hit, step.magnitude + 0.25f, ~0, QueryTriggerInteraction.Ignore))
            {
                Burst(hit.point - step.normalized * 0.2f);
                return;
            }
            transform.position += step;
            if (age > flightTime + 1.5f) Burst(transform.position);
        }

        void Burst(Vector3 at)
        {
            burst = true;
            transform.position = at;
            FearMeter.ScareSolversInRadius(at + Vector3.up * 0.3f, burstRadius, fear, transform);
            MysteryGameManager.Instance.PlayFx(SpookyFxKind.PumpkinBurst, at);
            HideRpc();
            Invoke(nameof(DespawnSelf), 0.4f);
        }

        [Rpc(SendTo.ClientsAndHost)]
        void HideRpc()
        {
            foreach (var r in GetComponentsInChildren<Renderer>()) r.enabled = false;
            foreach (var l in GetComponentsInChildren<Light>()) l.enabled = false;
        }

        void DespawnSelf()
        {
            if (IsSpawned) NetworkObject.Despawn();
        }
    }
}
