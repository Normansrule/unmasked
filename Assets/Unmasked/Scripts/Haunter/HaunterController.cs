using System.Collections.Generic;
using Unity.Collections;
using Unity.Netcode;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// The Haunter. Two forms:
    /// - Spectral (default): a flying ghost that possesses objects and uses spectral powers. Only the
    ///   Haunter's own machine is sent this object at all, so Solvers can't see or datamine it.
    /// - Physical (costume chase, and the whole Trap phase): walks around in costume, visible to all.
    ///   Getting close tags a Solver for a big scare, every few seconds risks leaving footprints (a clue),
    ///   and a flashlight held on the costume stuns the Haunter.
    ///
    /// Keys: WASD move, mouse look, Space/Ctrl up/down, E possess/leave, LMB/RMB object powers,
    /// 1-5 spectral powers, 6 or Q the villain's signature power, G plant a fake clue, Tab Suspect Board.
    ///
    /// The costume is tonight's villain (MysteryGameManager.Villain): CostumeVisual has one child per
    /// VillainKind, built from Resources/Costumes.json, and only that one is shown.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    public class HaunterController : NetworkBehaviour
    {
        public static HaunterController Local { get; private set; }

        [Header("Movement")]
        public float FlySpeed = 6.5f;
        public float CostumeWalkSpeed = 5.2f;
        public float Gravity = -20f;

        [Tooltip("How far from the middle of the map the ghost may drift (x, z).")]
        public Vector2 SpectralBounds = new(44f, 42f);
        [Tooltip("Lowest and highest the ghost may drift (the cellar floor up to above the roof).")]
        public Vector2 SpectralHeight = new(-3.2f, 16f);

        [Header("Possession")]
        public float PossessRange = 15f;
        public float ServerRangeTolerance = 1.5f;
        public float PossessCost = 10f;

        [Header("Costume")]
        public float TagRadius = 1.3f;
        public float TagCooldownPerSolver = 4f;
        public float TagClueLeakChance = 0.3f;
        [Tooltip("Every this many seconds in costume, roll for a footprint clue.")]
        public float FootprintInterval = 6f;
        public float FootprintLeakChance = 0.15f;
        [Tooltip("Seconds of flashlight on the costume before the Haunter is stunned.")]
        public float FlashlightStunExposure = 1.5f;
        public float FlashlightStunDuration = 2.5f;
        public float StunImmunityTime = 6f;

        [Header("Fake clues")]
        public float PlantFakeClueCost = 30f;
        [Tooltip("Ectoplasm to fake your alibi (once a night, in the room your alibi names).")]
        public float FakeAlibiCost = 35f;
        public float PlantFakeClueCooldown = 45f;

        [Header("Visuals")]
        [Tooltip("Spectral wisp, only the Haunter sees it.")]
        public GameObject GhostVisual;
        [Tooltip("The costume everyone sees during a chase: one child per VillainKind.")]
        public GameObject CostumeVisual;
        [Tooltip("A light the costume carries (pumpkin, lantern, wisp glow), tinted per villain.")]
        public Light CostumeGlow;

        readonly NetworkVariable<bool> physical = new();
        readonly NetworkVariable<bool> stunned = new();
        readonly NetworkVariable<NetworkObjectReference> possessed = new();

        public Ectoplasm Ectoplasm { get; private set; }
        public HaunterPowers Powers { get; private set; }
        public bool IsPhysical => physical.Value;
        public bool IsStunned => stunned.Value;
        public bool IsPossessing => Possessed != null;
        public PossessableObject Possessed => possessed.Value.TryGet(out var obj) ? obj.GetComponent<PossessableObject>() : null;

        /// <summary>Local Haunter only: the object under the crosshair.</summary>
        public PossessableObject FocusedObject { get; private set; }

        CharacterController controller;
        float verticalVelocity;
        float nextFocusUpdate;
        float nextIgnoreRefresh;

        // Server bookkeeping
        bool forcedPhysical;
        float physicalEndsAt;
        float stunEndsAt;
        float stunImmuneUntil;
        float beamExposure;
        float nextFootprintRoll;
        float tagFear = 35f;
        float lastPlantTime = -1000f;
        float lastRequestTime = -1000f;
        readonly Dictionary<SolverController, float> lastTagTime = new();

        void Awake()
        {
            controller = GetComponent<CharacterController>();
            Ectoplasm = GetComponent<Ectoplasm>();
            Powers = GetComponent<HaunterPowers>();
        }

        public override void OnNetworkSpawn()
        {
            // Only the owner moves this pawn; elsewhere the collider would just get in the way.
            controller.enabled = IsOwner;
            if (IsOwner)
            {
                Local = this;
                if (CameraRig.Instance != null) CameraRig.Instance.SetTarget(transform, 4f);
            }
        }

        public override void OnNetworkDespawn()
        {
            if (Local == this) Local = null;
            if (IsServer) ForceRelease();
        }

        void Update()
        {
            if (!IsSpawned) return;

            var obj = Possessed;
            if (GhostVisual != null) GhostVisual.SetActive(IsOwner && !physical.Value && obj == null);
            if (CostumeVisual != null) CostumeVisual.SetActive(physical.Value);
            ApplyVillain();

            if (IsOwner) OwnerUpdate(obj);
            if (IsServer && physical.Value) ServerPhysicalUpdate();
            if (IsServer) ServerTimers();
        }

        // -------------------------------------------------------------------
        // Owner: movement and input
        // -------------------------------------------------------------------

        void OwnerUpdate(PossessableObject obj)
        {
            var keyboard = Keyboard.current;
            var mouse = Mouse.current;
            bool menuOpen = CameraRig.Instance != null && CameraRig.Instance.InputLocked;
            bool canAct = keyboard != null && !menuOpen && !stunned.Value;

            if (CameraRig.Instance != null) CameraRig.Instance.Distance = obj != null ? 5.5f : 4f;

            if (obj != null)
            {
                // Riding inside the object.
                controller.enabled = false;
                transform.position = obj.transform.position + Vector3.up * 0.5f;
            }
            else
            {
                // A ghost drifts through walls and floors; the costume has to use doors and stairs.
                if (physical.Value && !wasPhysical) StepOutOfWalls();
                wasPhysical = physical.Value;
                controller.enabled = physical.Value;
                if (physical.Value) RefreshSolverCollisions();
                Move(keyboard, canAct);
            }

            if (Time.time >= nextFocusUpdate)
            {
                nextFocusUpdate = Time.time + 0.1f;
                UpdateFocus(obj);
            }

            if (!canAct) return;

            if (keyboard.eKey.wasPressedThisFrame)
            {
                if (obj != null) ReleaseRpc();
                else if (FocusedObject != null) PossessRpc(FocusedObject.NetworkObject);
            }

            if (obj != null && mouse != null && Cursor.lockState == CursorLockMode.Locked)
            {
                if (mouse.leftButton.wasPressedThisFrame) ObjectPowerRpc(0);
                if (mouse.rightButton.wasPressedThisFrame) ObjectPowerRpc(1);
            }

            Key[] powerKeys = { Key.Digit1, Key.Digit2, Key.Digit3, Key.Digit4, Key.Digit5, Key.Digit6 };
            for (int i = 0; i < powerKeys.Length; i++)
                if (keyboard[powerKeys[i]].wasPressedThisFrame) Powers.Activate(i);
            if (keyboard.qKey.wasPressedThisFrame) Powers.Activate(powerKeys.Length - 1);

            if (keyboard.gKey.wasPressedThisFrame) RequestPlantFakeClue(null);
            if (keyboard.hKey.wasPressedThisFrame && !IsPossessing) FakeAlibiRpc();
        }

        void Move(Keyboard keyboard, bool canAct)
        {
            Vector3 move = Vector3.zero;
            if (canAct)
            {
                Vector2 input = new(
                    (keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0),
                    (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0));
                float yaw = CameraRig.Instance != null ? CameraRig.Instance.Yaw : transform.eulerAngles.y;
                move = Quaternion.Euler(0f, yaw, 0f) * new Vector3(input.x, 0f, input.y);
                if (move.sqrMagnitude > 1f) move.Normalize();
                transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            }

            if (physical.Value)
            {
                verticalVelocity = controller.isGrounded ? -2f : verticalVelocity + Gravity * Time.deltaTime;
                controller.Move((move * CostumeWalkSpeed * villainSpeed + Vector3.up * verticalVelocity) * Time.deltaTime);
            }
            else
            {
                float vertical = canAct ? (keyboard.spaceKey.isPressed ? 1 : 0) - (keyboard.leftCtrlKey.isPressed ? 1 : 0) : 0;
                Vector3 next = transform.position + (move + Vector3.up * vertical) * FlySpeed * Time.deltaTime;
                // Around tonight's house in Hollow Creek, or the middle of the map in a single-house scene.
                Vector3 center = Vector3.zero;
                Vector2 bounds = SpectralBounds;
                var game = MysteryGameManager.Instance;
                if (game != null && game.IsSpawned && game.TryGetPlayArea(out var areaCenter, out var areaHalf))
                {
                    center = areaCenter;
                    bounds = areaHalf;
                }
                next.x = Mathf.Clamp(next.x, center.x - bounds.x, center.x + bounds.x);
                next.y = Mathf.Clamp(next.y, SpectralHeight.x, SpectralHeight.y);
                next.z = Mathf.Clamp(next.z, center.z - bounds.y, center.z + bounds.y);
                transform.position = next;
            }
        }

        bool wasPhysical;

        // -------------------------------------------------------------------
        // Villain costume (every machine; cosmetic, plus the costume's walk speed)
        // -------------------------------------------------------------------

        VillainKind? shownVillain;
        float villainSpeed = 1f;

        void ApplyVillain()
        {
            var game = MysteryGameManager.Instance;
            if (game == null || !game.IsSpawned || CostumeVisual == null) return;
            var villain = game.Villain.Value;
            if (shownVillain == villain) return;
            shownVillain = villain;

            Transform chosen = null;
            foreach (Transform child in CostumeVisual.transform)
            {
                bool match = child.name == villain.ToString();
                child.gameObject.SetActive(match);
                if (match) chosen = child;
            }

            var info = Costumes.For(villain);
            villainSpeed = info != null && info.speed > 0f ? info.speed : 1f;
            if (CostumeGlow != null && info?.glow != null && info.glow.Length >= 3)
                CostumeGlow.color = new Color(info.glow[0], info.glow[1], info.glow[2]);

            var anim = GetComponent<PawnAnimator>();
            if (anim != null && chosen != null)
            {
                anim.SetMask(chosen.Find("Mask"));
                anim.Hover = info != null ? info.hover : 0f;
            }
        }

        /// <summary>
        /// The ghost may have been inside a wall when the costume went on. Find the nearest spot
        /// where a body fits (searching outwards, then upwards) and stand there.
        /// </summary>
        void StepOutOfWalls()
        {
            int mask = ~0;
            bool Fits(Vector3 p) => !Physics.CheckCapsule(p + Vector3.up * 0.4f, p + Vector3.up * 1.4f, 0.35f, mask, QueryTriggerInteraction.Ignore)
                                    && Physics.Raycast(p + Vector3.up * 0.5f, Vector3.down, 1.5f, mask, QueryTriggerInteraction.Ignore);
            Vector3 start = transform.position;
            if (Physics.Raycast(start + Vector3.up * 0.5f, Vector3.down, out var floor, 4f, mask, QueryTriggerInteraction.Ignore))
                start = floor.point + Vector3.up * 0.05f;
            if (Fits(start)) { transform.position = start; return; }
            for (float radius = 0.5f; radius <= 4f; radius += 0.5f)
                for (int k = 0; k < 12; k++)
                {
                    float a = k * Mathf.PI / 6f;
                    Vector3 p = start + new Vector3(Mathf.Cos(a), 0f, Mathf.Sin(a)) * radius;
                    if (Fits(p)) { transform.position = p; return; }
                }
        }

        void RefreshSolverCollisions()
        {
            // Ghosts drift through Solvers; the costume bumps into them.
            if (Time.time < nextIgnoreRefresh) return;
            nextIgnoreRefresh = Time.time + 0.5f;
            foreach (var s in SolverController.All)
            {
                var other = s.GetComponent<CharacterController>();
                if (other != null) Physics.IgnoreCollision(controller, other, !physical.Value);
            }
        }

        void UpdateFocus(PossessableObject current)
        {
            FocusedObject = null;
            var cam = Camera.main;
            if (cam == null || current != null || physical.Value) return;

            float reach = Vector3.Distance(cam.transform.position, transform.position) + PossessRange;
            if (Physics.SphereCast(cam.transform.position, 0.3f, cam.transform.forward, out var hit, reach, ~0, QueryTriggerInteraction.Ignore))
            {
                var candidate = hit.collider.GetComponentInParent<PossessableObject>();
                if (candidate != null && candidate.CanBePossessed && Vector3.Distance(candidate.transform.position, transform.position) <= PossessRange)
                    FocusedObject = candidate;
            }
        }

        // -------------------------------------------------------------------
        // Server: requests
        // -------------------------------------------------------------------

        bool Accept(RpcParams p)
        {
            if (p.Receive.SenderClientId != OwnerClientId || Time.time - lastRequestTime < 0.15f) return false;
            lastRequestTime = Time.time;
            return true;
        }

        static bool InvestigationRunning => MysteryGameManager.Instance != null && MysteryGameManager.Instance.Phase.Value == MatchPhase.Investigation;

        /// <summary>Server: move the Haunter (to tonight's house when a call comes in).</summary>
        public void ServerTeleport(Vector3 position) => TeleportRpc(position);

        [Rpc(SendTo.Owner)]
        void TeleportRpc(Vector3 position)
        {
            controller.enabled = false;
            transform.position = position;
            controller.enabled = true;
        }

        [Rpc(SendTo.Server)]
        void PossessRpc(NetworkObjectReference target, RpcParams p = default)
        {
            if (!Accept(p) || !InvestigationRunning || physical.Value || stunned.Value || IsPossessing) return;
            if (!target.TryGet(out var targetObj)) return;
            var obj = targetObj.GetComponent<PossessableObject>();
            if (obj == null || !obj.CanBePossessed) return;
            if (Vector3.Distance(obj.transform.position, transform.position) > PossessRange + ServerRangeTolerance) return;
            if (!Ectoplasm.TrySpend(PossessCost)) return;

            possessed.Value = obj.NetworkObject;
            obj.SetPossessed(true);
        }

        [Rpc(SendTo.Server)]
        void ReleaseRpc(RpcParams p = default)
        {
            if (Accept(p)) ForceRelease();
        }

        /// <summary>Server: kick the Haunter out of whatever they're in.</summary>
        public void ForceRelease()
        {
            var obj = Possessed;
            if (obj == null) return;
            obj.SetPossessed(false);
            possessed.Value = default;
            ReleasedRpc(obj.transform.position + Vector3.up * 1.2f);
        }

        [Rpc(SendTo.Owner)]
        void ReleasedRpc(Vector3 popOutAt)
        {
            controller.enabled = false;
            transform.position = popOutAt;
            controller.enabled = true;
            Sfx.Play("whoosh", popOutAt, 0.7f, 15f, 0.8f); // a faint tell for sharp-eared Solvers
        }

        [Rpc(SendTo.Server)]
        void ObjectPowerRpc(int slot, RpcParams p = default)
        {
            var obj = Possessed;
            if (!Accept(p) || obj == null || !InvestigationRunning || stunned.Value) return;

            var spec = obj.GetSpec(slot);
            if (spec == null || obj.CooldownRemaining(slot) > 0f || !Ectoplasm.TrySpend(spec.Cost)) return;
            ulong owner = OwnerClientId;
            bool started = obj.Execute(slot, () =>
            {
                FearMeter.ScareSolversInRadius(obj.transform.position, spec.FearRadius, spec.Fear, obj.transform);
                // The mind game: every power risks leaving evidence of who the Haunter really is.
                MysteryGameManager.Instance.Mystery.TryLeakClue(obj.transform.position, spec.LeakChance, PlayerAgent.ForClient(owner));
            });
            if (!started) Ectoplasm.Add(spec.Cost);
        }

        /// <summary>Owner: plant a fake clue here framing a suspect (null = random innocent).</summary>
        public void RequestPlantFakeClue(string framedId)
        {
            if (!IsPossessing && Ectoplasm.CanAfford(PlantFakeClueCost)) PlantFakeClueRpc(framedId ?? string.Empty);
        }

        [Rpc(SendTo.Server)]
        void PlantFakeClueRpc(FixedString32Bytes framedId, RpcParams p = default)
        {
            if (!Accept(p) || !InvestigationRunning || IsPossessing || stunned.Value) return;
            if (Time.time - lastPlantTime < PlantFakeClueCooldown || !Ectoplasm.TrySpend(PlantFakeClueCost)) return;

            if (MysteryGameManager.Instance.Mystery.PlantFakeClue(transform.position, framedId.ToString()))
                lastPlantTime = Time.time;
            else
                Ectoplasm.Add(PlantFakeClueCost);
        }

        /// <summary>
        /// Cover your tracks: standing in the room your alibi names, plant signs you were there all
        /// along, so if the Solvers check it, it holds up.
        /// </summary>
        [Rpc(SendTo.Server)]
        void FakeAlibiRpc(RpcParams p = default)
        {
            if (!Accept(p) || !InvestigationRunning || IsPossessing || stunned.Value) return;
            var game = MysteryGameManager.Instance;
            var mystery = game.Mystery;
            var agent = PlayerAgent.ForClient(OwnerClientId);
            string id = mystery.CulpritId;
            string room = game.AlibiRoomOf(id);
            if (string.IsNullOrEmpty(room) || mystery.AlibiFaked || game.AlibiStatus(id) != 0) return;
            if (ManorLayout.RoomNameAt(transform.position) != room)
            {
                agent?.Tell($"Your alibi says the {room}. Go there to fake it.");
                return;
            }
            if (!Ectoplasm.TrySpend(FakeAlibiCost)) return;
            mystery.FakeAlibi();
            agent?.Tell("Alibi faked. If they check it, it will hold up.");
        }

        public float PlantFakeClueCooldownRemaining => Mathf.Max(0f, PlantFakeClueCooldown - (Time.time - lastPlantTime));

        // -------------------------------------------------------------------
        // Server: physical form, stun
        // -------------------------------------------------------------------

        /// <summary>Server: put on the costume. duration &lt;= 0 means until told otherwise.</summary>
        public void EnterPhysicalForm(float duration, float fearOnTag)
        {
            ForceRelease();
            tagFear = fearOnTag;
            beamExposure = 0f;
            nextFootprintRoll = Time.time + FootprintInterval;
            physicalEndsAt = duration > 0f ? Time.time + duration : float.MaxValue;
            physical.Value = true;
            UpdateVisibility();
        }

        /// <summary>Server</summary>
        public void ExitPhysicalForm()
        {
            if (forcedPhysical || !physical.Value) return;
            physical.Value = false;
            UpdateVisibility();
        }

        /// <summary>Server: Trap phase, stuck in costume until the match ends.</summary>
        public void SetForcedPhysical(bool forced)
        {
            forcedPhysical = forced;
            if (forced) EnterPhysicalForm(0f, tagFear);
        }

        /// <summary>Server: freeze the Haunter. seconds &lt;= 0 means for good (caught in the trap).</summary>
        public void Stun(float seconds)
        {
            stunned.Value = true;
            stunEndsAt = seconds > 0f ? Time.time + seconds : float.MaxValue;
        }

        void ServerTimers()
        {
            if (physical.Value && Time.time >= physicalEndsAt) ExitPhysicalForm();
            if (stunned.Value && Time.time >= stunEndsAt)
            {
                stunned.Value = false;
                stunImmuneUntil = Time.time + StunImmunityTime;
            }
        }

        void UpdateVisibility()
        {
            // In costume everyone may see the Haunter; as a ghost, only its owner gets the object.
            foreach (ulong clientId in NetworkManager.ConnectedClientsIds)
            {
                if (clientId == OwnerClientId || clientId == NetworkManager.ServerClientId) continue;
                bool visible = NetworkObject.IsNetworkVisibleTo(clientId);
                if (physical.Value && !visible) NetworkObject.NetworkShow(clientId);
                else if (!physical.Value && visible) NetworkObject.NetworkHide(clientId);
            }
        }

        void ServerPhysicalUpdate()
        {
            var mystery = MysteryGameManager.Instance.Mystery;
            var owner = PlayerAgent.ForClient(OwnerClientId);

            // Flashlights hurt: hold a beam on the costume and the Haunter staggers.
            if (!stunned.Value && Time.time >= stunImmuneUntil)
            {
                beamExposure = InAnyFlashlightBeam() ? beamExposure + Time.deltaTime : Mathf.Max(0f, beamExposure - Time.deltaTime);
                if (beamExposure >= FlashlightStunExposure)
                {
                    beamExposure = 0f;
                    Stun(FlashlightStunDuration);
                }
            }
            if (stunned.Value) return;

            // Tag any Solver we catch.
            foreach (var s in SolverController.All.ToArray())
            {
                if (s.IsPanicked || Vector3.Distance(s.transform.position, transform.position) > TagRadius) continue;
                if (lastTagTime.TryGetValue(s, out float last) && Time.time - last < TagCooldownPerSolver) continue;
                lastTagTime[s] = Time.time;
                s.Fear.AddFear(tagFear, transform.position);
                mystery.TryLeakClue(transform.position, TagClueLeakChance, owner);
            }

            // Running around in a costume leaves footprints.
            if (Time.time >= nextFootprintRoll)
            {
                nextFootprintRoll = Time.time + FootprintInterval;
                mystery.TryLeakClue(transform.position, FootprintLeakChance, owner);
            }
        }

        bool InAnyFlashlightBeam()
        {
            Vector3 chest = transform.position + Vector3.up;
            foreach (var s in SolverController.All)
            {
                if (s.Flashlight == null || !s.Flashlight.IsPointInBeam(chest)) continue;
                Vector3 from = s.Flashlight.transform.position;
                bool blocked = false;
                foreach (var hit in Physics.RaycastAll(from, (chest - from).normalized, Vector3.Distance(from, chest), ~0, QueryTriggerInteraction.Ignore))
                {
                    var root = hit.transform.root;
                    if (root != transform.root && root != s.transform.root) { blocked = true; break; }
                }
                if (!blocked) return true;
            }
            return false;
        }
    }
}
