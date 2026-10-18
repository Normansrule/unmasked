using System.Collections.Generic;
using Unity.Netcode;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// A member of the Midnight Mystery Club. Third-person movement, a flashlight, an Interact button
    /// and a Fear Meter. Keys: WASD move, mouse look, Space jump, E interact, F flashlight,
    /// Tab Suspect Board.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public class SolverController : NetworkBehaviour, IInteractable
    {
        public static readonly List<SolverController> All = new();
        public static SolverController Local { get; private set; }

        public float WalkSpeed = 4.5f;
        public float PanicSpeedMultiplier = 1.5f;
        public float JumpHeight = 1.1f;
        public float Gravity = -20f;
        public float TurnSpeed = 12f;
        [Tooltip("How far from the Solver's body something can be used.")]
        public float InteractDistance = 2.5f;
        [Tooltip("Latency slack when the server re-checks range.")]
        public float ServerInteractTolerance = 1f;

        public FearMeter Fear { get; private set; }
        public Flashlight Flashlight { get; private set; }

        /// <summary>Local player only: what the crosshair is on, for the prompt.</summary>
        public IInteractable Focused { get; private set; }

        public Vector3 EyePosition => transform.position + Vector3.up * 1.6f;
        public bool IsPanicked => Fear != null && Fear.IsPanicked;
        /// <summary>In the Mystery Club van (any machine).</summary>
        public bool IsRiding => MysteryVan.IsRiding(OwnerClientId);

        CharacterController controller;
        float verticalVelocity;
        float nextFocusUpdate;
        float lastServerInteract = -1000f;
        bool riding;

        void Awake()
        {
            controller = GetComponent<CharacterController>();
            Fear = GetComponent<FearMeter>();
            Flashlight = GetComponentInChildren<Flashlight>();
        }

        public override void OnNetworkSpawn()
        {
            All.Add(this);
            if (IsOwner)
            {
                Local = this;
                if (CameraRig.Instance != null) CameraRig.Instance.SetTarget(transform, 4f);
            }
        }

        public override void OnNetworkDespawn()
        {
            All.Remove(this);
            if (Local == this) Local = null;
        }

        void Update()
        {
            if (!IsOwner || !IsSpawned) return;

            var keyboard = Keyboard.current;
            bool menuOpen = CameraRig.Instance != null && CameraRig.Instance.InputLocked;

            // ---- Riding in the Mystery Club van (Hollow Creek) ----
            if (MysteryVan.TryGetSeat(OwnerClientId, out var seat, out bool driving))
            {
                if (!riding)
                {
                    riding = true;
                    if (CameraRig.Instance != null) CameraRig.Instance.Follow(MysteryVan.Instance.transform, 9f, 2.4f, true);
                }
                controller.enabled = false;
                transform.SetPositionAndRotation(seat.position, seat.rotation);
                Focused = null;
                if (keyboard != null && !menuOpen && keyboard.eKey.wasPressedThisFrame) MysteryVan.Instance.LeaveRpc();
                return;
            }
            if (riding)
            {
                riding = false;
                var van = MysteryVan.Instance;
                if (van != null && van.ExitPoint != null && Vector3.Distance(transform.position, van.transform.position) < 4f)
                    transform.position = van.ExitPoint.position + Vector3.up * 0.2f;
                controller.enabled = true;
                if (CameraRig.Instance != null) CameraRig.Instance.SetTarget(transform, 4f);
            }

            // ---- Movement ----
            Vector3 move = Vector3.zero;
            if (IsPanicked)
            {
                move = Fear.FleeDirection; // you've lost control: run away screaming
            }
            else if (keyboard != null && !menuOpen)
            {
                Vector2 input = new(
                    (keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0),
                    (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0));
                float yaw = CameraRig.Instance != null ? CameraRig.Instance.Yaw : transform.eulerAngles.y;
                move = Quaternion.Euler(0f, yaw, 0f) * new Vector3(input.x, 0f, input.y);
                if (move.sqrMagnitude > 1f) move.Normalize();
            }

            if (controller.isGrounded)
            {
                verticalVelocity = -2f;
                if (!IsPanicked && !menuOpen && keyboard != null && keyboard.spaceKey.wasPressedThisFrame)
                    verticalVelocity = Mathf.Sqrt(JumpHeight * -2f * Gravity);
            }
            verticalVelocity += Gravity * Time.deltaTime;

            float speed = WalkSpeed * (IsPanicked ? PanicSpeedMultiplier : 1f);
            controller.Move((move * speed + Vector3.up * verticalVelocity) * Time.deltaTime);

            if (move.sqrMagnitude > 0.01f)
            {
                var face = Quaternion.LookRotation(new Vector3(move.x, 0f, move.z));
                transform.rotation = Quaternion.Slerp(transform.rotation, face, TurnSpeed * Time.deltaTime);
            }

            // ---- Interaction and flashlight ----
            if (Time.time >= nextFocusUpdate)
            {
                nextFocusUpdate = Time.time + 0.1f;
                UpdateFocus();
            }

            if (keyboard == null || menuOpen || IsPanicked) return;

            if (keyboard.eKey.wasPressedThisFrame && Focused is Component target)
            {
                var targetObject = target.GetComponentInParent<NetworkObject>();
                if (targetObject != null) InteractRpc(targetObject);
            }

            if (keyboard.fKey.wasPressedThisFrame && Flashlight != null)
                Flashlight.Toggle();
        }

        void UpdateFocus()
        {
            Focused = null;
            var cam = Camera.main;
            if (cam == null) return;

            float reach = Vector3.Distance(cam.transform.position, transform.position) + InteractDistance;
            var hits = Physics.SphereCastAll(cam.transform.position, 0.2f, cam.transform.forward, reach, ~0, QueryTriggerInteraction.Collide);
            System.Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            foreach (var hit in hits)
            {
                if (hit.transform.root == transform.root) continue;
                var interactable = hit.collider.GetComponentInParent<IInteractable>();
                if (interactable == null)
                {
                    if (!hit.collider.isTrigger) break; // something solid is in the way
                    continue;
                }
                if (DistanceTo(hit.collider) <= InteractDistance && interactable.CanInteract(this))
                    Focused = interactable;
                break;
            }
        }

        float DistanceTo(Collider c) => Vector3.Distance(c.ClosestPoint(transform.position + Vector3.up), transform.position + Vector3.up);

        [Rpc(SendTo.Server)]
        void InteractRpc(NetworkObjectReference targetRef, RpcParams p = default)
        {
            if (p.Receive.SenderClientId != OwnerClientId || IsPanicked) return;
            if (Time.time - lastServerInteract < 0.25f) return;
            lastServerInteract = Time.time;

            if (!targetRef.TryGet(out var targetObject)) return;
            var interactable = targetObject.GetComponentInChildren<IInteractable>();
            var target = interactable as Component;
            if (target == null) return;

            // Range, with latency slack.
            var col = target.GetComponentInChildren<Collider>();
            float distance = col != null ? DistanceTo(col) : Vector3.Distance(target.transform.position, transform.position);
            if (distance > InteractDistance + ServerInteractTolerance) return;

            // No using things through walls.
            Vector3 aimPoint = col != null ? col.bounds.center : target.transform.position;
            Vector3 toTarget = aimPoint - EyePosition;
            foreach (var hit in Physics.RaycastAll(EyePosition, toTarget.normalized, toTarget.magnitude, ~0, QueryTriggerInteraction.Ignore))
            {
                var root = hit.transform.root;
                if (root != transform.root && root != target.transform.root) return;
            }

            if (interactable.CanInteract(this)) interactable.Interact(this);
        }

        // ---- Calming a panicked teammate ----

        public bool CanInteract(SolverController solver) => solver != this && IsPanicked;
        public string GetPrompt(SolverController solver) => "Calm down";
        public void Interact(SolverController solver)
        {
            if (IsServer && solver != this) Fear.CalmDown();
        }

        // ---- Server pushes (the owner moves this transform) ----

        /// <summary>Server: move this Solver somewhere (trapdoors).</summary>
        public void ServerTeleport(Vector3 position) => TeleportRpc(position);

        /// <summary>Server: throw this Solver into the air.</summary>
        public void ServerLaunch(float upwardSpeed) => LaunchRpc(upwardSpeed);

        [Rpc(SendTo.Owner)]
        void TeleportRpc(Vector3 position)
        {
            controller.enabled = false;
            transform.position = position;
            controller.enabled = true;
        }

        [Rpc(SendTo.Owner)]
        void LaunchRpc(float upwardSpeed) => verticalVelocity = upwardSpeed;
    }
}
