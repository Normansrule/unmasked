using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Where the Solvers build their trap. Bring RequiredPieces pieces, then press E to build
    /// (Brawn builds twice as fast). Once armed, it springs on its own when the costumed Haunter
    /// steps close, or a Solver can spring it by hand (E). A miss knocks it back one build step.
    /// When sprung it wobbles for a beat before it snaps shut: everyone sees it coming, and a
    /// quick Haunter can still dart clear.
    /// </summary>
    public class TrapSite : NetworkBehaviour, IInteractable, INewNight
    {
        public int RequiredPieces = 3;
        public int RequiredBuildWork = 4;
        [Tooltip("How close the Haunter must be when the trap is sprung.")]
        public float CatchRadius = 3.5f;
        [Tooltip("The armed trap springs itself when the Haunter gets this close.")]
        public float AutoTriggerRadius = 1.5f;
        [Tooltip("Shown once the trap is armed (a cage, a net).")]
        public GameObject ArmedVisual;
        [Tooltip("Seconds the trap wobbles between being sprung and snapping shut.")]
        public float Wobble = 0.35f;

        readonly NetworkVariable<int> pieces = new();
        readonly NetworkVariable<int> work = new();
        readonly NetworkVariable<bool> armed = new();

        public int Pieces => pieces.Value;
        public int Work => work.Value;
        public bool IsArmed => armed.Value;

        bool springing;
        float wobbleStart = -10f;
        Vector3 armedRestScale = Vector3.one;
        Quaternion armedRestRotation = Quaternion.identity;
        bool restCaptured;

        static bool TrapPhase => MysteryGameManager.Instance != null && MysteryGameManager.Instance.Phase.Value == MatchPhase.Trap;

        public string StatusText =>
            armed.Value ? "Trap ARMED: lure the Haunter in!"
            : pieces.Value < RequiredPieces ? $"Trap pieces {pieces.Value}/{RequiredPieces}"
            : $"Building {work.Value}/{RequiredBuildWork}";

        void Update()
        {
            if (ArmedVisual != null)
            {
                ArmedVisual.SetActive(armed.Value);
                AnimateWobble();
            }
            if (!IsServer || !armed.Value || !TrapPhase) return;

            var haunter = MysteryGameManager.Instance.HaunterPawn;
            if (!springing && haunter != null && haunter.IsPhysical && Vector3.Distance(haunter.transform.position, transform.position) <= AutoTriggerRadius)
                Spring();
        }

        public bool CanInteract(SolverController solver) => TrapPhase;

        public string GetPrompt(SolverController solver)
        {
            if (armed.Value) return "Spring the trap!";
            if (pieces.Value < RequiredPieces)
            {
                var agent = PlayerAgent.Local;
                return agent != null && agent.CarriedTrapPieces.Value > 0 ? "Add trap pieces" : $"Needs trap pieces ({pieces.Value}/{RequiredPieces})";
            }
            return "Build the trap";
        }

        public void Interact(SolverController solver)
        {
            if (!IsServer || !TrapPhase) return;
            var agent = PlayerAgent.ForClient(solver.OwnerClientId);
            if (agent == null) return;

            if (armed.Value) { if (!springing) StartCoroutine(SpringAfterWobble()); return; }

            if (pieces.Value < RequiredPieces)
            {
                int add = Mathf.Min(agent.CarriedTrapPieces.Value, RequiredPieces - pieces.Value);
                if (add <= 0) { agent.Tell("Find trap pieces around the house first."); return; }
                agent.CarriedTrapPieces.Value -= add;
                pieces.Value += add;
                return;
            }

            work.Value = Mathf.Min(RequiredBuildWork, work.Value + (agent.Role.Value == SolverRole.Brawn ? 2 : 1));
            if (work.Value >= RequiredBuildWork)
            {
                armed.Value = true;
                MysteryGameManager.Instance.Announce("The trap is armed! Lure the Haunter in!");
                MysteryGameManager.Instance.NotifyTrapArmed(this);
            }
        }

        void Spring()
        {
            if (!springing && armed.Value) StartCoroutine(SpringAfterWobble());
        }

        System.Collections.IEnumerator SpringAfterWobble()
        {
            springing = true;
            WobbleRpc();
            yield return new WaitForSeconds(Wobble);
            springing = false;
            Resolve();
        }

        [Rpc(SendTo.ClientsAndHost)]
        void WobbleRpc()
        {
            wobbleStart = Time.time;
            Sfx.Play("rattle", transform.position + Vector3.up, 0.7f, 18f, 1.5f);
        }

        /// <summary>Every machine: rock side to side faster and faster, then snap down.</summary>
        void AnimateWobble()
        {
            var t = ArmedVisual.transform;
            if (!restCaptured) { armedRestScale = t.localScale; armedRestRotation = t.localRotation; restCaptured = true; }
            float w = Time.time - wobbleStart;
            if (w < 0f || w > Wobble + 0.25f)
            {
                t.localScale = armedRestScale;
                t.localRotation = armedRestRotation;
                return;
            }
            if (w < Wobble)
            {
                float k = w / Wobble;
                t.localRotation = armedRestRotation * Quaternion.Euler(0f, 0f, Mathf.Sin(w * (30f + 40f * k)) * 9f * k);
                t.localScale = Vector3.Scale(armedRestScale, new Vector3(1f, 1f + 0.06f * k, 1f));
            }
            else
            {
                float snap = 1f - (w - Wobble) / 0.25f;
                t.localRotation = armedRestRotation;
                t.localScale = Vector3.Scale(armedRestScale, new Vector3(1f + 0.12f * snap, 1f - 0.2f * snap, 1f + 0.12f * snap));
            }
        }

        void Resolve()
        {
            if (!armed.Value) return;
            if (MysteryGameManager.Instance.TryCatchHaunter(this)) return;

            armed.Value = false;
            work.Value = Mathf.Max(0, RequiredBuildWork - 1);
            MysteryGameManager.Instance.Announce("Missed! Quick, re-arm the trap!");
        }

        public void ServerNewNight()
        {
            StopAllCoroutines();
            springing = false;
            pieces.Value = 0;
            work.Value = 0;
            armed.Value = false;
        }

        void OnDrawGizmos()
        {
            Gizmos.color = new Color(0.2f, 0.9f, 0.4f);
            Gizmos.DrawWireSphere(transform.position, CatchRadius);
        }
    }
}
