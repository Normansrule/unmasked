using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// A hidden trapdoor. The Haunter's Trapdoor power springs it while a Solver stands on it: they
    /// drop to DropDestination (the cellar), or get bounced into the air if there's none.
    /// </summary>
    public class Trapdoor : NetworkBehaviour, INewNight
    {
        [Tooltip("Hinged lid. Rotates open when sprung.")]
        public Transform Panel;
        public Transform DropDestination;
        [Tooltip("Half-size of the area that counts as standing on the trapdoor.")]
        public Vector3 TriggerExtents = new(0.9f, 1f, 0.9f);
        public float BounceSpeed = 9f;

        readonly NetworkVariable<bool> open = new();
        float closeAt;
        float angle;

        public bool IsOpen => open.Value;

        /// <summary>Server: open under whoever is standing on it. False if nobody is.</summary>
        public bool Spring(float fear, float seconds)
        {
            if (!IsServer || open.Value) return false;

            var bounds = new Bounds(transform.position + Vector3.up * TriggerExtents.y, TriggerExtents * 2f);
            bool caughtSomeone = false;
            foreach (var solver in SolverController.All)
            {
                if (!bounds.Contains(solver.transform.position + Vector3.up * 0.1f)) continue;
                caughtSomeone = true;
                if (DropDestination != null) solver.ServerTeleport(DropDestination.position);
                else solver.ServerLaunch(BounceSpeed);
                solver.Fear.AddFear(fear, transform.position);
            }
            if (!caughtSomeone) return false;

            open.Value = true;
            closeAt = Time.time + Mathf.Max(1f, seconds);
            return true;
        }

        public void ServerNewNight() => open.Value = false;

        void Update()
        {
            if (IsServer && open.Value && Time.time >= closeAt) open.Value = false;
            if (Panel == null) return;
            angle = Mathf.Lerp(angle, open.Value ? -90f : 0f, 1f - Mathf.Exp(-12f * Time.deltaTime));
            Panel.localRotation = Quaternion.Euler(angle, 0f, 0f);
        }

        void OnDrawGizmos()
        {
            Gizmos.color = new Color(0.8f, 0.3f, 0.1f);
            Gizmos.DrawWireCube(transform.position + Vector3.up * TriggerExtents.y, TriggerExtents * 2f);
            if (DropDestination != null) Gizmos.DrawLine(transform.position, DropDestination.position);
        }
    }
}
