using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Something one of the townsfolk lost (Townsperson): a pumpkin, a cat, a lantern. It only shows
    /// up once they've asked the club to look for it, glows a little so it can be found in the dark,
    /// and goes back to them when a Solver picks it up. Same on every machine, from the owner's
    /// networked errand state.
    /// </summary>
    public class ErrandItem : NetworkBehaviour, IInteractable
    {
        public Townsperson Owner;
        public Transform Model;

        Collider col;
        Light glow;
        bool shown = true;

        void Awake()
        {
            col = GetComponent<Collider>();
            glow = new GameObject("Glow").AddComponent<Light>();
            glow.transform.SetParent(transform, false);
            glow.transform.localPosition = new Vector3(0f, 0.8f, 0f);
            glow.type = LightType.Point;
            glow.range = 3.5f;
            glow.intensity = 1.2f;
            glow.color = new Color(1f, 0.8f, 0.45f);
            glow.shadows = LightShadows.None;
        }

        bool Waiting => Owner != null && Owner.Errand.Value == Townsperson.ErrandState.Asked;

        public bool CanInteract(SolverController solver) => Waiting && !solver.IsRiding;

        public string GetPrompt(SolverController solver) => $"Pick up {Owner.ItemName}";

        public void Interact(SolverController solver)
        {
            if (IsServer && Waiting) Owner.ServerFound(solver);
        }

        void Update()
        {
            bool show = Waiting;
            if (show != shown)
            {
                shown = show;
                if (Model != null) Model.gameObject.SetActive(show);
                if (col != null) col.enabled = show;
                glow.enabled = show;
            }
            if (show)
            {
                glow.intensity = 1.0f + 0.4f * Mathf.Sin(Time.time * 2.4f);
                if (Model != null) Model.localPosition = new Vector3(0f, 0.04f * Mathf.Sin(Time.time * 1.7f), 0f);
            }
        }
    }
}
