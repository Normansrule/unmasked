using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// A clue in the world. Every clue looks the same until examined: only "discovered or not" is
    /// replicated. What it is, and whether it's a fake, stays in the server's MysteryServer.
    /// </summary>
    public class ClueItem : NetworkBehaviour, IInteractable
    {
        readonly NetworkVariable<bool> discovered = new();

        /// <summary>Server only. Never replicated.</summary>
        public int InstanceId { get; set; } = -1;

        public bool IsDiscovered => discovered.Value;

        public override void OnNetworkSpawn()
        {
            discovered.OnValueChanged += (_, now) => ApplyDiscovered(now);
            ApplyDiscovered(discovered.Value);
        }

        /// <summary>Server: called once the clue has been recorded.</summary>
        public void MarkDiscovered()
        {
            discovered.Value = true;
            Invoke(nameof(DespawnSelf), 2f);
        }

        void DespawnSelf()
        {
            if (IsSpawned) NetworkObject.Despawn();
        }

        Vector3 baseScale;
        void Awake() => baseScale = transform.localScale;

        void Update()
        {
            // Sleuth role: clues close to you pulse so they're easier to spot (your screen only).
            if (discovered.Value) return;
            var me = SolverController.Local;
            var agent = PlayerAgent.Local;
            bool sense = me != null && agent != null && agent.Role.Value == SolverRole.Sleuth
                         && Vector3.Distance(me.transform.position, transform.position) <= SleuthSenseRadius;
            float pulse = sense ? 1f + 0.35f * Mathf.Abs(Mathf.Sin(Time.time * 4f)) : 1f;
            transform.localScale = baseScale * pulse;
            transform.Rotate(0f, 45f * Time.deltaTime, 0f, Space.World);
        }

        public const float SleuthSenseRadius = 9f;

        void ApplyDiscovered(bool isDiscovered)
        {
            foreach (var r in GetComponentsInChildren<Renderer>()) r.enabled = !isDiscovered;
            foreach (var c in GetComponentsInChildren<Collider>()) c.enabled = !isDiscovered;
        }

        public bool CanInteract(SolverController solver) => !discovered.Value;

        public string GetPrompt(SolverController solver) => "Examine";

        public void Interact(SolverController solver)
        {
            if (IsServer && !discovered.Value)
                MysteryGameManager.Instance.Mystery.DiscoverClue(this, solver);
        }
    }
}
