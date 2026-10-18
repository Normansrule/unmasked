using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>Haunter power: a creeping fog bank. Solvers standing in it slowly get more scared.</summary>
    public class FogCloud : NetworkBehaviour
    {
        readonly NetworkVariable<float> radius = new(6f);
        float fearPerSecond = 3f;
        float despawnAt;
        float nextTick;

        /// <summary>Server, before spawning.</summary>
        public void Initialize(float fogRadius, float fear, float duration)
        {
            radius.Value = fogRadius;
            fearPerSecond = fear;
            despawnAt = Time.time + duration;
        }

        void Update()
        {
            transform.localScale = Vector3.one * radius.Value * 2f;
            if (!IsServer || !IsSpawned) return;

            if (Time.time >= despawnAt)
            {
                NetworkObject.Despawn();
                return;
            }

            if (Time.time < nextTick) return;
            nextTick = Time.time + 0.5f;
            foreach (var s in SolverController.All)
                if (Vector3.Distance(s.transform.position, transform.position) <= radius.Value)
                    s.Fear.AddFear(fearPerSecond * 0.5f, transform.position);
        }
    }
}
