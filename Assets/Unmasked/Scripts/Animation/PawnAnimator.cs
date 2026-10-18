using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Procedural animation, so the prototype feels alive with no rigged models. Purely cosmetic and
    /// local to each machine: it reads replicated state (movement, fear, stun, phase) and wiggles
    /// child transforms. Swap for an Animator once real characters exist.
    /// </summary>
    public class PawnAnimator : MonoBehaviour
    {
        public enum Style { Solver, Haunter, Suspect }

        public Style Kind;
        [Tooltip("The mesh that bobs and leans.")]
        public Transform Body;
        [Tooltip("Haunter only: the spectral wisp.")]
        public Transform Ghost;
        [Tooltip("Haunter only: the mask that flies off when unmasked.")]
        public Transform Mask;
        [Tooltip("Haunter only: floating villains (Banshee, Baba Yaga in her mortar) bob in the air.")]
        public float Hover;

        SolverController solver;
        HaunterController haunter;
        Vector3 lastPosition;
        float speed;
        float phaseOffset;
        Vector3 bodyRest, ghostRest, maskRest, bodyRestScale = Vector3.one;
        Quaternion maskRestRotation;
        float unmaskStarted = -1f;

        void Awake()
        {
            solver = GetComponent<SolverController>();
            haunter = GetComponent<HaunterController>();
            phaseOffset = Random.value * 10f;
            if (Body != null) { bodyRest = Body.localPosition; bodyRestScale = Body.localScale; }
            if (Ghost != null) ghostRest = Ghost.localPosition;
            if (Mask != null) { maskRest = Mask.localPosition; maskRestRotation = Mask.localRotation; }
            lastPosition = transform.position;
            if (GetComponent<FaceLife>() == null) gameObject.AddComponent<FaceLife>();
        }

        /// <summary>Swap which transform flies off at the unmasking (each villain costume has its own).</summary>
        public void SetMask(Transform mask)
        {
            if (Mask == mask) return;
            if (Mask != null) { Mask.localPosition = maskRest; Mask.localRotation = maskRestRotation; }
            Mask = mask;
            if (Mask != null) { maskRest = Mask.localPosition; maskRestRotation = Mask.localRotation; }
            unmaskStarted = -1f;
        }

        void LateUpdate()
        {
            float dt = Mathf.Max(Time.deltaTime, 0.0001f);
            Vector3 delta = transform.position - lastPosition;
            delta.y = 0f;
            speed = Mathf.Lerp(speed, delta.magnitude / dt, 10f * dt);
            lastPosition = transform.position;
            float t = Time.time + phaseOffset;

            switch (Kind)
            {
                case Style.Solver: AnimateSolver(t); break;
                case Style.Haunter: AnimateHaunter(t); break;
                case Style.Suspect: AnimateSuspect(t); break;
            }
        }

        void AnimateSolver(float t)
        {
            if (Body == null) return;
            bool panicked = solver != null && solver.IsPanicked;
            float fear = solver != null && solver.Fear != null ? solver.Fear.Percent : 0f;
            float moving = Mathf.Clamp01(speed / 4.5f);

            // Walk: bob and lean into the run. Panic: a frantic cartoon scramble.
            float bobFrequency = panicked ? 22f : 11f;
            float bob = Mathf.Abs(Mathf.Sin(t * bobFrequency)) * 0.08f * moving;
            float lean = moving * (panicked ? 18f : 8f);
            Vector3 shiver = fear > 0.6f ? Random.insideUnitSphere * 0.015f * fear : Vector3.zero;
            if (panicked) bob += 0.12f + Mathf.Abs(Mathf.Sin(t * 30f)) * 0.1f; // feet barely touch the floor

            Body.localPosition = bodyRest + Vector3.up * bob + shiver;
            Body.localRotation = Quaternion.Euler(lean, 0f, Mathf.Sin(t * bobFrequency * 0.5f) * 4f * moving);
        }

        void AnimateHaunter(float t)
        {
            if (Ghost != null)
            {
                Ghost.localPosition = ghostRest + Vector3.up * Mathf.Sin(t * 2f) * 0.2f;
                Ghost.localScale = Vector3.one * (0.8f + Mathf.Sin(t * 3.3f) * 0.05f);
            }
            if (Body == null || haunter == null) return;

            if (haunter.IsStunned && !IsUnmasking)
            {
                // Dizzy spin.
                Body.localRotation = Quaternion.Euler(Mathf.Sin(t * 6f) * 10f, t * 360f, Mathf.Cos(t * 6f) * 10f);
            }
            else
            {
                float moving = Mathf.Clamp01(speed / 5f);
                // Stomping, arms-up "boogedy boogedy" sway.
                Body.localRotation = Quaternion.Euler(moving * 6f, 0f, Mathf.Sin(t * 8f) * 7f * (0.4f + moving));
                float bob = Hover > 0f ? Mathf.Sin(t * 2.2f) * 0.08f : Mathf.Abs(Mathf.Sin(t * 8f)) * 0.06f * moving;
                Body.localPosition = bodyRest + Vector3.up * bob;
            }

            if (Mask == null) return;
            if (IsUnmasking)
            {
                if (unmaskStarted < 0f) unmaskStarted = Time.time;
                float u = Time.time - unmaskStarted;
                // Hold a beat, then the mask is yanked up and away, spinning.
                float pull = Mathf.Clamp01((u - 1.2f) / 1.5f);
                Mask.localPosition = maskRest + new Vector3(0f, pull * 1.6f, pull * 0.8f) + (u < 1.2f ? Random.insideUnitSphere * 0.02f : Vector3.zero);
                Mask.localRotation = maskRestRotation * Quaternion.Euler(-pull * 540f, pull * 90f, 0f);
            }
            else
            {
                unmaskStarted = -1f;
                Mask.localPosition = maskRest;
                Mask.localRotation = maskRestRotation;
            }
        }

        float startledAt = -10f;

        /// <summary>Suspects: jump out of their skin (a hop, then a shiver).</summary>
        public void Startle() => startledAt = Time.time;

        float hesitateAt = -10f, hesitateFor;

        /// <summary>Suspects: the beat before answering (a glance down and away, then a swallow).</summary>
        public void Hesitate(float seconds)
        {
            hesitateAt = Time.time;
            hesitateFor = seconds;
        }

        void AnimateSuspect(float t)
        {
            if (Body == null) return;
            float h = Time.time - hesitateAt;
            if (h >= 0f && h < hesitateFor)
            {
                float k = h / hesitateFor;
                float settle = Mathf.SmoothStep(0f, 1f, Mathf.Min(1f, k * 4f)) * (1f - Mathf.SmoothStep(0.8f, 1f, k));
                // The swallow: a quick dip and squash about two thirds of the way in.
                float gulp = Mathf.Exp(-Mathf.Pow((k - 0.65f) / 0.06f, 2f));
                Body.localPosition = bodyRest + Vector3.down * 0.03f * gulp;
                Body.localScale = Vector3.Scale(bodyRestScale, new Vector3(1f + 0.03f * gulp, 0.97f - 0.03f * gulp, 1f + 0.03f * gulp));
                Body.localRotation = Quaternion.Euler(14f * settle, -22f * settle, 0f);
                return;
            }
            float s = Time.time - startledAt;
            if (s < 1.4f)
            {
                float hop = s < 0.35f ? Mathf.Sin(s / 0.35f * Mathf.PI) * 0.3f : 0f;
                float shake = (1.4f - s) * 0.04f;
                Body.localPosition = bodyRest + Vector3.up * hop + new Vector3(Mathf.Sin(t * 70f) * shake, 0f, Mathf.Cos(t * 63f) * shake);
                Body.localScale = Vector3.Scale(bodyRestScale, new Vector3(0.95f, 1.08f, 0.95f));
                Body.localRotation = Quaternion.Euler(-12f * Mathf.Clamp01(1.4f - s), 0f, 0f);
                return;
            }
            Body.localPosition = bodyRest;
            // Idle: breathing and nervous glances. Cleared suspects relax.
            Body.localScale = Vector3.Scale(bodyRestScale, new Vector3(1f, 1f + Mathf.Sin(t * 1.6f) * 0.02f, 1f));
            Body.localRotation = Quaternion.Euler(0f, Mathf.Sin(t * 0.4f) * 25f + Mathf.Sin(t * 2.1f) * 4f, 0f);
        }

        static bool IsUnmasking
        {
            get
            {
                var game = MysteryGameManager.Instance;
                return game != null && game.IsSpawned && (game.Phase.Value == MatchPhase.Unmasking || (game.Phase.Value == MatchPhase.Ended && game.EndReason.Value == MatchEndReason.Unmasked));
            }
        }
    }
}
