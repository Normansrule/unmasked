using System.Collections.Generic;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// A lamp the Haunter can possess to flicker it or kill it. Solvers switch it back on with E.
    /// Before it acts it pauses, then slowly tips its shade toward the nearest Solver, as if it
    /// has noticed them; afterwards it eases back upright.
    /// </summary>
    public class PossessableLight : PossessableObject, IInteractable
    {
        public Light Lamp;
        public float FlickerDuration = 2.5f;

        readonly NetworkVariable<bool> lightOn = new(true);
        float flickerUntil;
        float baseIntensity = 1f;

        protected override List<ObjectActionSpec> DefaultActions() => new()
        {
            new ObjectActionSpec(PossessedAction.Flicker, 5f, 4f, 10f, 8f, 0.03f),
            new ObjectActionSpec(PossessedAction.CutPower, 15f, 12f, 15f, 10f, 0.08f),
        };

        protected override void Awake()
        {
            base.Awake();
            if (Lamp == null) Lamp = GetComponentInChildren<Light>();
            if (Lamp != null) baseIntensity = Lamp.intensity;
        }

        protected override bool CanPerform(ObjectActionSpec spec) =>
            spec.Action is PossessedAction.Flicker or PossessedAction.CutPower ? lightOn.Value : base.CanPerform(spec);

        protected override float LeanDegrees(float sinceWindUp)
        {
            if (sinceWindUp < 0f) return 0f;
            float hold = Anticipation + FlickerDuration;
            if (sinceWindUp < Anticipation)
            {
                // A held beat (the pause), then it turns to look.
                float k = Mathf.Clamp01((sinceWindUp / Anticipation - 0.4f) / 0.6f);
                return 16f * Mathf.SmoothStep(0f, 1f, k);
            }
            if (sinceWindUp < hold) return 16f;
            return 16f * (1f - Mathf.SmoothStep(0f, 1f, (sinceWindUp - hold) / 0.9f));
        }

        protected override bool PerformAction(ObjectActionSpec spec)
        {
            switch (spec.Action)
            {
                case PossessedAction.Flicker:
                    return lightOn.Value;
                case PossessedAction.CutPower:
                    if (!lightOn.Value) return false;
                    lightOn.Value = false;
                    return true;
            }
            return base.PerformAction(spec);
        }

        protected override void PlayFx(PossessedAction action)
        {
            if (action == PossessedAction.Flicker) flickerUntil = Time.time + FlickerDuration;
            base.PlayFx(action);
        }

        protected override void Update()
        {
            base.Update();
            if (Lamp == null) return;
            bool flickering = Time.time < flickerUntil;
            Lamp.enabled = lightOn.Value && (!flickering || Random.value > 0.45f);
            Lamp.intensity = flickering ? baseIntensity * Random.Range(0.2f, 1f) : baseIntensity;
        }

        /// <summary>Server: knock the lamp out (the Banshee's wail). Solvers switch it back on with E.</summary>
        public void ServerCutPower()
        {
            if (IsServer) lightOn.Value = false;
        }

        public override void ServerNewNight()
        {
            base.ServerNewNight();
            lightOn.Value = true;
        }

        public bool CanInteract(SolverController solver) => !lightOn.Value;
        public string GetPrompt(SolverController solver) => "Switch on";
        public void Interact(SolverController solver)
        {
            if (IsServer) lightOn.Value = true;
        }
    }
}
