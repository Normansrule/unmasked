using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// A replicated spotlight with a battery. The owner aims it with the camera; the server owns the
    /// on/off state and battery drain. Put it on a child object with a spot Light.
    /// </summary>
    public class Flashlight : NetworkBehaviour
    {
        public float MaxBattery = 100f;
        [Tooltip("Battery per second while on. 100 / 0.5 = 200 seconds of light.")]
        public float DrainPerSecond = 0.5f;
        [Tooltip("Below this battery fraction the beam sputters.")]
        public float LowBatteryThreshold = 0.15f;

        readonly NetworkVariable<bool> isOn = new();
        readonly NetworkVariable<float> battery = new(100f);
        // Cosmetic aim, written by the owner so everyone sees the beam sweep around.
        readonly NetworkVariable<Vector2> aim = new(default, NetworkVariableReadPermission.Everyone, NetworkVariableWritePermission.Owner);

        public bool IsOn => isOn.Value;
        public float BatteryPercent => MaxBattery > 0 ? battery.Value / MaxBattery : 0f;

        Light beam;
        float baseIntensity;

        void Awake()
        {
            beam = GetComponentInChildren<Light>();
            if (beam != null) baseIntensity = beam.intensity;
        }

        public override void OnNetworkSpawn()
        {
            if (IsServer) battery.Value = MaxBattery;
        }

        void Update()
        {
            if (!IsSpawned) return;

            if (IsOwner && CameraRig.Instance != null)
            {
                var wanted = new Vector2(CameraRig.Instance.Pitch, CameraRig.Instance.Yaw);
                if ((wanted - aim.Value).sqrMagnitude > 0.25f) aim.Value = wanted;
            }
            transform.rotation = Quaternion.Euler(aim.Value.x, aim.Value.y, 0f);

            if (IsServer && isOn.Value)
            {
                // Techie role: tuned-up flashlight, drains 40% slower.
                var owner = PlayerAgent.ForClient(OwnerClientId);
                float drain = DrainPerSecond * (owner != null && owner.Role.Value == SolverRole.Techie ? 0.6f : 1f);
                if (MysteryGameManager.Instance != null) drain *= MysteryGameManager.Instance.BatteryDrainMultiplier; // night events
                battery.Value = Mathf.Max(0f, battery.Value - drain * Time.deltaTime);
                if (battery.Value <= 0f) isOn.Value = false;
            }

            if (beam != null)
            {
                beam.enabled = isOn.Value;
                bool sputter = isOn.Value && BatteryPercent < LowBatteryThreshold && Random.value < 0.15f;
                beam.intensity = sputter ? baseIntensity * 0.2f : baseIntensity;
            }
        }

        /// <summary>Owner: flip it on or off.</summary>
        public void Toggle() => ToggleRpc();

        [Rpc(SendTo.Server)]
        void ToggleRpc(RpcParams p = default)
        {
            if (p.Receive.SenderClientId != OwnerClientId) return;
            isOn.Value = !isOn.Value && battery.Value > 0f;
        }

        /// <summary>Server</summary>
        public void ForceOff()
        {
            if (IsServer) isOn.Value = false;
        }

        /// <summary>Server</summary>
        public void AddBattery(float amount)
        {
            if (IsServer) battery.Value = Mathf.Clamp(battery.Value + amount, 0f, MaxBattery);
        }

        /// <summary>Is the point lit by the beam right now? (Cone and range only; check walls separately.)</summary>
        public bool IsPointInBeam(Vector3 point)
        {
            if (!isOn.Value || beam == null) return false;
            Vector3 to = point - transform.position;
            float distance = to.magnitude;
            if (distance < 0.01f) return true;
            if (distance > beam.range) return false;
            return Vector3.Angle(transform.forward, to) <= beam.spotAngle * 0.5f;
        }
    }
}
