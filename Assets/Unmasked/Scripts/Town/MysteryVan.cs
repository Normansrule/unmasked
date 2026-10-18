using Unity.Netcode;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// The Mystery Club van. Walk up and press E to get in: the first one in drives, the rest ride.
    /// The driver's machine owns the van while driving (arcade handling, OwnerNetworkTransform),
    /// so it feels instant. Keys while driving: W/S gas and reverse, A/D steer, Space brake,
    /// E get out. Passengers just press E to hop out.
    /// </summary>
    public class MysteryVan : NetworkBehaviour, IInteractable, INewNight
    {
        public static MysteryVan Instance { get; private set; }

        const ulong Empty = ulong.MaxValue;

        [Tooltip("Seat 0 is the driver.")]
        public Transform[] Seats;
        [Tooltip("Where people step out (left side of the van).")]
        public Transform ExitPoint;
        public Light[] Headlights;

        [Header("Handling")]
        public float MaxSpeed = 20f;
        public float ReverseSpeed = 7f;
        public float Acceleration = 9f;
        public float BrakeForce = 22f;
        public float Drag = 3f;
        [Tooltip("Degrees per second at full speed.")]
        public float TurnRate = 75f;
        public Vector3 HalfExtents = new(1.0f, 0.9f, 2.35f);

        NetworkList<ulong> riders;
        float speed;
        float steerVisual;

        public float Speed => speed;
        public bool HasDriver => riders != null && riders.Count > 0 && riders[0] != Empty;

        void Awake()
        {
            Instance = this;
            riders = new NetworkList<ulong>();
        }

        Vector3 homePosition;
        Quaternion homeRotation;

        public override void OnNetworkSpawn()
        {
            homePosition = transform.position;
            homeRotation = transform.rotation;
            if (IsServer && riders.Count == 0)
                for (int i = 0; i < Seats.Length; i++) riders.Add(Empty);
        }

        /// <summary>Server: everyone out, and the van is back in the HQ driveway.</summary>
        public void ServerNewNight()
        {
            for (int i = 0; i < riders.Count; i++) riders[i] = Empty;
            ServerPark(homePosition, homeRotation);
        }

        public override void OnDestroy()
        {
            if (Instance == this) Instance = null;
            base.OnDestroy();
        }

        // -------------------------------------------------------------------
        // Seats (any machine reads, the server writes)
        // -------------------------------------------------------------------

        public int SeatIndexOf(ulong clientId)
        {
            if (riders == null) return -1;
            for (int i = 0; i < riders.Count; i++) if (riders[i] == clientId) return i;
            return -1;
        }

        public static bool IsRiding(ulong clientId) => Instance != null && Instance.SeatIndexOf(clientId) >= 0;

        public static bool TryGetSeat(ulong clientId, out Transform seat, out bool driving)
        {
            seat = null;
            driving = false;
            if (Instance == null || !Instance.IsSpawned) return false;
            int i = Instance.SeatIndexOf(clientId);
            if (i < 0 || i >= Instance.Seats.Length) return false;
            seat = Instance.Seats[i];
            driving = i == 0;
            return true;
        }

        int FreeSeat()
        {
            for (int i = 0; i < riders.Count; i++) if (riders[i] == Empty) return i;
            return -1;
        }

        public bool CanInteract(SolverController solver) => IsSpawned && !IsRiding(solver.OwnerClientId) && FreeSeat() >= 0;

        public string GetPrompt(SolverController solver) => FreeSeat() == 0 ? "Drive the van" : "Ride in the van";

        /// <summary>Server: get in.</summary>
        public void Interact(SolverController solver)
        {
            if (!IsServer || !CanInteract(solver)) return;
            int seat = FreeSeat();
            riders[seat] = solver.OwnerClientId;
            if (seat == 0) NetworkObject.ChangeOwnership(solver.OwnerClientId);
        }

        /// <summary>Riding: press E to get out.</summary>
        [Rpc(SendTo.Server)]
        public void LeaveRpc(RpcParams p = default)
        {
            ulong who = p.Receive.SenderClientId;
            int seat = SeatIndexOf(who);
            if (seat < 0) return;
            riders[seat] = Empty;
            if (seat == 0)
            {
                // Hand the wheel to the next passenger, or park it.
                int next = -1;
                for (int i = 1; i < riders.Count; i++) if (riders[i] != Empty) { next = i; break; }
                if (next > 0)
                {
                    riders[0] = riders[next];
                    riders[next] = Empty;
                    NetworkObject.ChangeOwnership(riders[0]);
                }
                else
                {
                    NetworkObject.RemoveOwnership();
                }
            }

            var agent = PlayerAgent.ForClient(who);
            var solver = agent != null && agent.Pawn != null ? agent.Pawn.GetComponent<SolverController>() : null;
            if (solver != null)
            {
                Vector3 exit = ExitPoint != null ? ExitPoint.position : transform.position - transform.right * 2f;
                solver.ServerTeleport(exit - transform.forward * (seat * 0.9f) + Vector3.up * 0.2f);
            }
        }

        /// <summary>Server: move the van (to tonight's house, if nobody drove it there).</summary>
        public void ServerPark(Vector3 position, Quaternion rotation)
        {
            if (!IsServer) return;
            if (!IsOwnedByServer) NetworkObject.RemoveOwnership();
            ParkRpc(position, rotation);
        }

        [Rpc(SendTo.Everyone)]
        void ParkRpc(Vector3 position, Quaternion rotation)
        {
            speed = 0f;
            if (IsOwner) transform.SetPositionAndRotation(position, rotation);
        }

        /// <summary>Server: a Solver left the game or was scared out.</summary>
        public void ServerRemove(ulong clientId)
        {
            if (!IsServer) return;
            int seat = SeatIndexOf(clientId);
            if (seat < 0) return;
            riders[seat] = Empty;
            if (seat == 0) NetworkObject.RemoveOwnership();
        }

        // -------------------------------------------------------------------
        // Driving (the owner, which is the driver's machine)
        // -------------------------------------------------------------------

        void Update()
        {
            if (!IsSpawned || !IsOwner) return;

            bool driving = HasDriver && riders[0] == NetworkManager.LocalClientId;
            var keyboard = Keyboard.current;
            bool menuOpen = CameraRig.Instance != null && CameraRig.Instance.InputLocked;

            float throttle = 0f, steer = 0f;
            bool brake = !driving;
            if (driving && keyboard != null && !menuOpen)
            {
                throttle = (keyboard.wKey.isPressed ? 1f : 0f) - (keyboard.sKey.isPressed ? 1f : 0f);
                steer = (keyboard.dKey.isPressed ? 1f : 0f) - (keyboard.aKey.isPressed ? 1f : 0f);
                brake = keyboard.spaceKey.isPressed;
            }

            float dt = Time.deltaTime;
            if (brake) speed = Mathf.MoveTowards(speed, 0f, BrakeForce * dt);
            else if (throttle > 0f) speed = Mathf.MoveTowards(speed, MaxSpeed, Acceleration * (speed < 0 ? 2.5f : 1f) * dt);
            else if (throttle < 0f) speed = Mathf.MoveTowards(speed, -ReverseSpeed, Acceleration * (speed > 0 ? 2.5f : 1f) * dt);
            else speed = Mathf.MoveTowards(speed, 0f, Drag * dt);

            // Steering grows with speed, and flips in reverse like a real car.
            float grip = Mathf.Clamp01(Mathf.Abs(speed) / 6f) * Mathf.Sign(speed);
            steerVisual = Mathf.Lerp(steerVisual, steer, dt * 6f);
            transform.Rotate(0f, steerVisual * TurnRate * grip * dt, 0f, Space.World);

            Vector3 step = transform.forward * (speed * dt);
            if (step.sqrMagnitude > 1e-6f && Blocked(step))
            {
                speed = -speed * 0.25f; // bonk
                step = Vector3.zero;
            }
            Vector3 next = transform.position + step;

            // Stick to the ground (roads, lawns, the bridge).
            var downs = Physics.RaycastAll(next + Vector3.up * 3f, Vector3.down, 8f, ~0, QueryTriggerInteraction.Ignore);
            System.Array.Sort(downs, (x, y) => x.distance.CompareTo(y.distance));
            foreach (var h in downs)
            {
                if (IsMine(h.collider) || h.collider.GetComponentInParent<SolverController>() != null) continue;
                next.y = Mathf.Lerp(next.y, h.point.y, dt * 10f);
                break;
            }

            transform.position = next;
        }

        bool Blocked(Vector3 step)
        {
            Vector3 dir = step.normalized;
            Vector3 center = transform.position + Vector3.up * (HalfExtents.y + 0.35f);
            var hits = Physics.BoxCastAll(center, HalfExtents * 0.95f, dir, transform.rotation, step.magnitude + 0.15f, ~0, QueryTriggerInteraction.Ignore);
            foreach (var hit in hits)
            {
                if (IsMine(hit.collider)) continue;
                var solver = hit.collider.GetComponentInParent<SolverController>();
                if (solver != null && IsRiding(solver.OwnerClientId)) continue;
                if (hit.normal.y > 0.6f) continue; // ground and kerbs
                return true;
            }
            return false;
        }

        bool IsMine(Collider c) => c != null && c.transform.IsChildOf(transform);
    }
}
