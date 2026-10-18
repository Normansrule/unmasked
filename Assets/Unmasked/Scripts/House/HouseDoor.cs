using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// A swinging door. Solvers open and close it with E. The Haunter's Slam Doors power slams it
    /// shut and jams it for a while. Put the door mesh (with its collider) on the Hinge child.
    /// </summary>
    public class HouseDoor : NetworkBehaviour, IInteractable, INewNight
    {
        public Transform Hinge;
        public float OpenAngle = 100f;
        public float SwingSpeed = 6f;
        public float SlamSpeed = 25f;

        readonly NetworkVariable<bool> open = new();
        readonly NetworkVariable<bool> jammed = new();
        float jammedUntil;
        float currentAngle;

        public bool IsOpen => open.Value;
        bool wasOpen;
        public bool IsJammed => jammed.Value;

        void Awake()
        {
            if (Hinge == null && transform.childCount > 0) Hinge = transform.GetChild(0);
        }

        public void ServerNewNight()
        {
            open.Value = false;
            jammed.Value = false;
        }

        /// <summary>Server: bang! Shut and jammed for a few seconds.</summary>
        public void SlamShut(float jamSeconds)
        {
            if (!IsServer) return;
            open.Value = false;
            jammed.Value = jamSeconds > 0f;
            jammedUntil = Time.time + jamSeconds;
        }

        void Update()
        {
            if (IsServer && jammed.Value && Time.time >= jammedUntil) jammed.Value = false;
            if (Hinge == null) return;

            if (open.Value != wasOpen)
            {
                wasOpen = open.Value;
                if (wasOpen) Sfx.Play("creak", Hinge.position + Vector3.up, 0.6f, 18f, Random.Range(0.85f, 1.15f));
                else Sfx.Play("door_slam", Hinge.position + Vector3.up, jammed.Value ? 1f : 0.35f, 25f, jammed.Value ? 1f : 1.3f);
            }

            float target = open.Value ? OpenAngle : 0f;
            float speed = !open.Value && jammed.Value ? SlamSpeed : SwingSpeed;
            currentAngle = Mathf.Lerp(currentAngle, target, 1f - Mathf.Exp(-speed * Time.deltaTime));
            Hinge.localRotation = Quaternion.Euler(0f, currentAngle, 0f);
        }

        public bool CanInteract(SolverController solver) => !jammed.Value;
        public string GetPrompt(SolverController solver) => open.Value ? "Close" : "Open";
        public void Interact(SolverController solver)
        {
            if (IsServer && !jammed.Value) open.Value = !open.Value;
        }
    }
}
