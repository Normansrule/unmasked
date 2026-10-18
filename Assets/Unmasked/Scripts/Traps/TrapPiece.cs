using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Rope, a net, a crate... Hidden until the Trap phase starts, then Solvers pick them up (E,
    /// two at a time) and carry them to the TrapSite.
    /// </summary>
    public class TrapPiece : NetworkBehaviour, IInteractable, INewNight
    {
        public const int MaxCarried = 2;

        readonly NetworkVariable<bool> available = new();

        public override void OnNetworkSpawn()
        {
            available.OnValueChanged += (_, now) => Apply(now);
            Apply(available.Value);
        }

        /// <summary>Server: the trap phase began, show up.</summary>
        public void Activate()
        {
            if (IsServer) available.Value = true;
        }

        public void ServerNewNight() => available.Value = false;

        void Apply(bool visible)
        {
            foreach (var r in GetComponentsInChildren<Renderer>()) r.enabled = visible;
            foreach (var c in GetComponentsInChildren<Collider>()) c.enabled = visible;
        }

        public bool CanInteract(SolverController solver)
        {
            var agent = solver != null ? PlayerAgent.ForClient(solver.OwnerClientId) : null;
            return available.Value && (agent == null || agent.CarriedTrapPieces.Value < MaxCarried);
        }

        public string GetPrompt(SolverController solver) => "Pick up trap piece";

        public void Interact(SolverController solver)
        {
            if (!IsServer || !available.Value) return;
            var agent = PlayerAgent.ForClient(solver.OwnerClientId);
            if (agent == null || agent.CarriedTrapPieces.Value >= MaxCarried) return;
            agent.CarriedTrapPieces.Value++;
            available.Value = false;
        }
    }
}
