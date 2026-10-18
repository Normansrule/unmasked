using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The Haunter's power resource. Server-owned; regenerates over time.
    /// TODO(GAS-style abilities): fold into a proper ability/attribute system once powers settle.
    /// </summary>
    public class Ectoplasm : NetworkBehaviour
    {
        public float Max = 100f;
        public float StartAmount = 40f;
        [Tooltip("Difficulty knob for the AI Director, too.")]
        public float RegenPerSecond = 2f;

        readonly NetworkVariable<float> value = new();

        public float Value => value.Value;
        public bool CanAfford(float amount) => value.Value >= amount;

        public override void OnNetworkSpawn()
        {
            if (IsServer) value.Value = StartAmount;
        }

        void Update()
        {
            if (IsServer && IsSpawned && value.Value < Max)
            {
                float boost = MysteryGameManager.Instance != null ? MysteryGameManager.Instance.EctoplasmRegenMultiplier : 1f; // Blood Moon
                value.Value = Mathf.Min(Max, value.Value + RegenPerSecond * boost * Time.deltaTime);
            }
        }

        /// <summary>Server: spend if affordable.</summary>
        public bool TrySpend(float amount)
        {
            if (!IsServer || amount < 0f || value.Value < amount) return false;
            value.Value -= amount;
            return true;
        }

        /// <summary>Server</summary>
        public void Add(float amount)
        {
            if (IsServer) value.Value = Mathf.Clamp(value.Value + amount, 0f, Max);
        }
    }
}
