using System.Collections.Generic;
using System.Linq;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Plays the Haunter when no human picked it. Runs only on the server. It has its own Ectoplasm
    /// budget and uses the same house tools a player would: possessed furniture, slammed doors,
    /// trapdoors, fog and phantoms. Every scare can leak a true clue, exactly like a player Haunter.
    /// Difficulty scales how often it acts and how much it can spend.
    /// TODO: let the AI wear the costume and dodge the trap in the Trap phase.
    /// </summary>
    public class AIDirector : MonoBehaviour
    {
        [Range(0.25f, 2f)] public float Difficulty = 1f;
        public float StartEctoplasm = 40f;
        public float MaxEctoplasm = 100f;
        public float RegenPerSecond = 2f;
        [Tooltip("Seconds between decisions at difficulty 1.")]
        public Vector2 ThinkInterval = new(6f, 11f);
        [Tooltip("How close to its target Solver the AI looks for things to haunt.")]
        public float ReachAroundSolver = 10f;
        [Tooltip("Base chance that each AI scare leaves a true clue (scaled by the case).")]
        public float LeakChance = 0.15f;
        [Tooltip("Chance (at difficulty 1) the AI fakes the culprit's alibi at the start of the night.")]
        public float FakeAlibiChance = 0.35f;

        float ectoplasm;
        float nextThink;
        bool started;

        public bool IsActive
        {
            get
            {
                var game = MysteryGameManager.Instance;
                return game != null && game.IsServer && game.IsSpawned && game.HaunterAgent == null
                       && game.Phase.Value == MatchPhase.Investigation;
            }
        }

        /// <summary>For the HUD on the host (debug): how much the AI has to spend.</summary>
        public float Ectoplasm => ectoplasm;

        void Update()
        {
            if (!IsActive) { started = false; return; }

            if (!started)
            {
                started = true;
                ectoplasm = StartEctoplasm;
                nextThink = Time.time + Random.Range(ThinkInterval.x, ThinkInterval.y);
                MysteryGameManager.Instance.Announce("Nobody is playing the Haunter, so the house haunts itself...");
                // Sometimes the house covers its tracks too (more often on harder settings).
                if (Random.value < FakeAlibiChance * Difficulty) MysteryGameManager.Instance.Mystery.FakeAlibi();
            }

            ectoplasm = Mathf.Min(MaxEctoplasm, ectoplasm + RegenPerSecond * Difficulty * Time.deltaTime);
            if (Time.time < nextThink) return;
            nextThink = Time.time + Random.Range(ThinkInterval.x, ThinkInterval.y) / Mathf.Max(0.1f, Difficulty);
            Think();
        }

        void Think()
        {
            var targets = SolverController.All.Where(s => s != null && s.IsSpawned && !s.IsPanicked).ToList();
            if (targets.Count == 0) return;

            // Prefer whoever is alone: that's scarier and it's what a good Haunter does.
            var target = targets.OrderBy(s => targets.Count(o => o != s && Vector3.Distance(o.transform.position, s.transform.position) < 6f))
                                .ThenBy(_ => Random.value).First();
            Vector3 at = target.transform.position;

            // Try options in a shuffled order and use the first one that works and is affordable.
            var options = new List<System.Func<SolverController, bool>> { TryTrapdoor, TryFurniture, TryDoors, TryFog, TryPhantom, TrySignature };
            foreach (var option in options.OrderBy(_ => Random.value))
            {
                if (option(target))
                {
                    MysteryGameManager.Instance.Mystery.TryLeakClue(at, LeakChance, null);
                    return;
                }
            }
        }

        bool Spend(float amount)
        {
            if (ectoplasm < amount) return false;
            ectoplasm -= amount;
            return true;
        }

        bool TryTrapdoor(SolverController target)
        {
            foreach (var trapdoor in FindObjectsByType<Trapdoor>(FindObjectsSortMode.None))
            {
                if (Vector3.Distance(trapdoor.transform.position, target.transform.position) > 2f || ectoplasm < 25f) continue;
                if (trapdoor.Spring(30f, 3f)) { Spend(25f); return true; }
            }
            return false;
        }

        bool TryFurniture(SolverController target)
        {
            var objects = FindObjectsByType<PossessableObject>(FindObjectsSortMode.None)
                .Where(o => o.IsSpawned && !o.IsPossessed && Vector3.Distance(o.transform.position, target.transform.position) <= ReachAroundSolver)
                .OrderBy(_ => Random.value);
            foreach (var obj in objects)
            {
                for (int slot = obj.Actions.Count - 1; slot >= 0; slot--)
                {
                    var spec = obj.GetSpec(slot);
                    if (spec == null || obj.CooldownRemaining(slot) > 0f || ectoplasm < spec.Cost) continue;
                    var o = obj;
                    if (!o.Execute(slot, () => FearMeter.ScareSolversInRadius(o.transform.position, spec.FearRadius, spec.Fear, o.transform))) continue;
                    Spend(spec.Cost);
                    return true;
                }
            }
            return false;
        }

        bool TryDoors(SolverController target)
        {
            if (ectoplasm < 15f) return false;
            var doors = FindObjectsByType<HouseDoor>(FindObjectsSortMode.None)
                .Where(d => Vector3.Distance(d.transform.position, target.transform.position) <= ReachAroundSolver).ToList();
            if (doors.Count == 0) return false;
            Spend(15f);
            foreach (var door in doors)
            {
                door.SlamShut(8f);
                FearMeter.ScareSolversInRadius(door.transform.position, 7f, 15f, door.transform, false);
            }
            return true;
        }

        bool TryFog(SolverController target)
        {
            var game = MysteryGameManager.Instance;
            if (game.FogPrefab == null || ectoplasm < 20f || FindObjectsByType<FogCloud>(FindObjectsSortMode.None).Length > 0) return false;
            Spend(20f);
            var go = Instantiate(game.FogPrefab, target.transform.position, Quaternion.identity);
            go.GetComponent<FogCloud>().Initialize(6f, 3f, 20f);
            go.GetComponent<NetworkObject>().Spawn(true);
            return true;
        }

        bool TrySignature(SolverController target)
        {
            // Tonight's legend strikes from somewhere out of sight, a few metres off.
            if (ectoplasm < 30f) return false;
            Vector3 from = target.transform.position - target.transform.forward * 7f;
            if (Physics.Linecast(target.EyePosition, from + Vector3.up * 1.5f, ~0, QueryTriggerInteraction.Ignore))
                from = target.transform.position + Random.onUnitSphere.WithY(0).normalized * 5f;
            if (!VillainPowers.Use(MysteryGameManager.Instance.Villain.Value, from, 30f, 18f, 10f, null)) return false;
            Spend(30f);
            return true;
        }

        bool TryPhantom(SolverController target)
        {
            var game = MysteryGameManager.Instance;
            if (game.PhantomPrefab == null || ectoplasm < 25f) return false;

            // Appear somewhere behind the Solver, out of their flashlight.
            Vector3 behind = target.transform.position - target.transform.forward * 6f + Vector3.up * 1.2f;
            if (Physics.Linecast(target.EyePosition, behind, ~0, QueryTriggerInteraction.Ignore))
                behind = target.transform.position + Random.onUnitSphere.WithY(0).normalized * 4f + Vector3.up * 1.2f;

            Spend(25f);
            var go = Instantiate(game.PhantomPrefab, behind, Quaternion.identity);
            go.GetComponent<PhantomIllusion>().Initialize(25f, 12f, 15f);
            go.GetComponent<NetworkObject>().Spawn(true);
            return true;
        }
    }

    static class VectorExtensions
    {
        public static Vector3 WithY(this Vector3 v, float y) => new(v.x, y, v.z);
    }
}
