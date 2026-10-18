using System;
using System.Collections.Generic;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    public enum PossessedAction { Rattle, Launch, Slam, Flicker, CutPower }

    /// <summary>One thing the Haunter can do while inside an object (LMB = slot 0, RMB = slot 1).</summary>
    [Serializable]
    public class ObjectActionSpec
    {
        public PossessedAction Action;
        public float Cost = 5f;
        public float Cooldown = 4f;
        public float Fear = 8f;
        public float FearRadius = 6f;
        [Range(0f, 1f)] public float LeakChance = 0.05f;

        public ObjectActionSpec(PossessedAction action, float cost, float cooldown, float fear, float radius, float leak)
        {
            Action = action; Cost = cost; Cooldown = cooldown; Fear = fear; FearRadius = radius; LeakChance = leak;
        }
    }

    /// <summary>
    /// Furniture the Haunter can hide inside: chairs, vases, suits of armor. The server runs every
    /// action; clients only see the result (movement through NetworkTransform, plus a shake effect).
    /// A Rigidbody is optional; without one, Launch just hops the object.
    ///
    /// Every action has a beat of anticipation before it lands (the chair leans back before it
    /// hops) and a wobble of recovery after, so Solvers can read what happened: a warning, the
    /// surprise, then a moment to breathe. The fear lands with the action, not the warning.
    /// </summary>
    public class PossessableObject : NetworkBehaviour, INewNight
    {
        public List<ObjectActionSpec> Actions = new();
        [Tooltip("The mesh child that shakes. Defaults to the first child.")]
        public Transform Visual;
        public float LaunchSpeed = 7f;
        [Tooltip("Seconds of wind-up before an action lands, so it can be read (and dodged).")]
        public float Anticipation = 0.35f;

        readonly NetworkVariable<bool> possessed = new();
        NetworkList<double> readyTimes;
        Rigidbody body;

        float shakeUntil;
        Vector3 visualRestPosition, visualRestScale = Vector3.one;
        Quaternion visualRestRotation = Quaternion.identity;
        /// <summary>Every machine: when the wind-up began, and the point it is aimed at.</summary>
        protected float anticipateStart = -10f;
        protected Vector3 anticipateTarget;

        public bool IsPossessed => possessed.Value;
        public virtual bool CanBePossessed => IsSpawned && !possessed.Value;

        protected virtual List<ObjectActionSpec> DefaultActions() => new()
        {
            new ObjectActionSpec(PossessedAction.Rattle, 5f, 3f, 8f, 6f, 0.03f),
            new ObjectActionSpec(PossessedAction.Launch, 15f, 8f, 18f, 7f, 0.08f),
        };

        void Reset() => Actions = DefaultActions();

        protected virtual void Awake()
        {
            readyTimes = new NetworkList<double>();
            body = GetComponent<Rigidbody>();
            if (Actions == null || Actions.Count == 0) Actions = DefaultActions();
            if (Visual == null && transform.childCount > 0) Visual = transform.GetChild(0);
            if (Visual != null)
            {
                visualRestPosition = Visual.localPosition;
                visualRestRotation = Visual.localRotation;
                visualRestScale = Visual.localScale;
            }
        }

        public override void OnNetworkSpawn()
        {
            if (IsServer)
                for (int i = 0; i < Actions.Count; i++) readyTimes.Add(0);
        }

        /// <summary>Server</summary>
        public void SetPossessed(bool value)
        {
            if (IsServer) possessed.Value = value;
        }

        /// <summary>Server: nobody is in the furniture and every action is ready again.</summary>
        public virtual void ServerNewNight()
        {
            StopAllCoroutines();
            possessed.Value = false;
            for (int i = 0; i < readyTimes.Count; i++) readyTimes[i] = 0;
        }

        public ObjectActionSpec GetSpec(int slot) => slot >= 0 && slot < Actions.Count ? Actions[slot] : null;

        public float CooldownRemaining(int slot)
        {
            if (slot < 0 || slot >= readyTimes.Count || MysteryGameManager.Instance == null) return 0f;
            return Mathf.Max(0f, (float)(readyTimes[slot] - MysteryGameManager.Instance.Now));
        }

        /// <summary>
        /// Server: start an action. False means nothing will happen (the Haunter is refunded).
        /// The object winds up for Anticipation seconds, then the action lands and onLanded runs
        /// (that's where the scare and its fear go).
        /// </summary>
        public bool Execute(int slot, Action onLanded = null)
        {
            var spec = GetSpec(slot);
            if (!IsServer || spec == null || CooldownRemaining(slot) > 0f || !CanPerform(spec)) return false;
            readyTimes[slot] = MysteryGameManager.Instance.Now + spec.Cooldown;
            var nearest = NearestSolver(spec.FearRadius * 1.5f);
            AnticipateRpc(spec.Action, nearest != null ? nearest.EyePosition : transform.position + transform.forward);
            StartCoroutine(Land(spec, onLanded));
            return true;
        }

        System.Collections.IEnumerator Land(ObjectActionSpec spec, Action onLanded)
        {
            yield return new WaitForSeconds(Anticipation);
            if (!IsSpawned || !PerformAction(spec)) yield break;
            FxRpc(spec.Action);
            onLanded?.Invoke();
        }

        /// <summary>Server: is this action possible right now? (Checked before the wind-up.)</summary>
        protected virtual bool CanPerform(ObjectActionSpec spec) => true;

        protected SolverController NearestSolver(float within)
        {
            SolverController nearest = null;
            float best = within;
            foreach (var s in SolverController.All)
            {
                float d = Vector3.Distance(s.transform.position, transform.position);
                if (d < best) { best = d; nearest = s; }
            }
            return nearest;
        }

        /// <summary>Server</summary>
        protected virtual bool PerformAction(ObjectActionSpec spec)
        {
            switch (spec.Action)
            {
                case PossessedAction.Rattle:
                    return true;

                case PossessedAction.Launch:
                {
                    Vector3 direction = Vector3.up;
                    var nearest = NearestSolver(spec.FearRadius * 1.5f);
                    if (nearest != null) direction = ((nearest.EyePosition - transform.position).normalized + Vector3.up * 0.6f).normalized;

                    if (body != null && !body.isKinematic)
                        body.linearVelocity = direction * LaunchSpeed;
                    else
                        transform.position += Vector3.up * 0.3f;
                    return true;
                }
            }
            return false;
        }

        [Rpc(SendTo.ClientsAndHost)]
        void AnticipateRpc(PossessedAction action, Vector3 target)
        {
            anticipateStart = Time.time;
            anticipateTarget = target;
            OnAnticipate(action);
        }

        /// <summary>Every machine: the wind-up has started (the action lands Anticipation seconds later).</summary>
        protected virtual void OnAnticipate(PossessedAction action) { }

        [Rpc(SendTo.ClientsAndHost)]
        void FxRpc(PossessedAction action)
        {
            Sfx.PlayAction(action, transform.position);
            PlayFx(action);
        }

        /// <summary>Every machine: cosmetic feedback for an action.</summary>
        protected virtual void PlayFx(PossessedAction action)
        {
            if (action == PossessedAction.Rattle || action == PossessedAction.Launch || action == PossessedAction.Slam)
                shakeUntil = Time.time + 0.8f;
        }

        protected virtual void Update()
        {
            if (Visual == null) return;
            bool shaking = Time.time < shakeUntil;
            float wind = Time.time - anticipateStart;
            bool anticipating = wind >= 0f && wind < Anticipation;
            // A possessed object trembles faintly all the time: an observant Solver can spot it.
            float strength = shaking ? 0.06f : anticipating ? 0.012f : (possessed.Value ? 0.006f : 0f);
            Visual.localPosition = strength > 0f ? visualRestPosition + UnityEngine.Random.insideUnitSphere * strength : visualRestPosition;

            // Lean: tip about the axis across the line to the target (positive = toward it).
            Vector3 to = anticipateTarget - transform.position;
            to.y = 0f;
            Vector3 axis = to.sqrMagnitude > 0.001f ? Vector3.Cross(Vector3.up, to.normalized) : transform.right;
            float lean = LeanDegrees(wind);
            Quaternion world = Quaternion.AngleAxis(lean, axis);
            Quaternion parent = Visual.parent != null ? Visual.parent.rotation : Quaternion.identity;
            Visual.localRotation = Quaternion.Inverse(parent) * world * parent * visualRestRotation;

            // Squash while winding up, a little stretch as it lets go.
            float squash = anticipating ? Mathf.SmoothStep(0f, 1f, wind / Anticipation) * 0.08f
                : wind >= Anticipation && wind < Anticipation + 0.15f ? -0.06f : 0f;
            Visual.localScale = Vector3.Scale(visualRestScale, new Vector3(1f + squash * 0.5f, 1f - squash, 1f + squash * 0.5f));
        }

        /// <summary>
        /// Every machine: how far the object leans, by seconds since the wind-up began. Furniture
        /// leans back (away from the Solver) to wind up, lets go, then wobbles back to rest.
        /// </summary>
        protected virtual float LeanDegrees(float sinceWindUp)
        {
            if (sinceWindUp < 0f) return 0f;
            if (sinceWindUp < Anticipation) return -12f * Mathf.SmoothStep(0f, 1f, sinceWindUp / Anticipation);
            float u = sinceWindUp - Anticipation - 0.8f; // after the action's shake
            if (u < 0f || u > 1.2f) return 0f;
            return 7f * Mathf.Exp(-4f * u) * Mathf.Sin(u * 16f); // recovery wobble
        }
    }
}
