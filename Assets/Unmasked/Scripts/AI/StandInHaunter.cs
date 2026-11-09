using System.Linq;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The Haunter when nobody plays it, once the culprit has been named. Server only, added to the
    /// culprit's <see cref="SuspectNPC"/> when the Trap phase starts. The suspect puts on tonight's
    /// costume and plays the part the way a person would:
    /// - prowls the house, keeping away from the club;
    /// - runs from any Solver who gets close and can see it;
    /// - is drawn to an armed trap (the bait) only while no Solver is standing guard near it, so the
    ///   club has to build it, step back and wait;
    /// - may smell the trap at the last moment and back off (more often on harder settings), so a
    ///   Solver sometimes has to spring it by hand at the right time.
    /// If it's still free when the phase runs out, the Haunter wins (MatchEndReason.Escaped). At the
    /// unmasking the costume comes off. The suspect's NetworkTransform carries every move to clients.
    /// </summary>
    public class StandInHaunter : MonoBehaviour
    {
        public float WalkSpeed = 2.0f, RunSpeed = 3.8f;
        [Tooltip("A Solver this close (with a clear view) sends it running.")]
        public float SpookDistance = 5f;
        [Tooltip("It only takes the bait while no Solver is this close to the trap.")]
        public float GuardDistance = 6f;
        [Tooltip("Where it may stop and smell the trap.")]
        public float BalkDistance = 3f;
        [Tooltip("Chance to back off from the trap, per approach, at difficulty 1.")]
        public float BalkChance = 0.45f;

        public static StandInHaunter Active { get; private set; }

        SuspectNPC npc;
        float difficulty = 1f;
        int balksLeft;
        bool balkRolled;
        Vector3 goal;
        float runUntil, nextGoal, stuckFor;
        float bestToBait = float.MaxValue, lastProgress, nextRoute;
        Vector3 route, routedGoal;
        bool unmasked;

        /// <summary>Server: the named culprit at tonight's house puts on the costume. Null if there is no such suspect.</summary>
        public static StandInHaunter Begin(MysteryGameManager game, Vector3 near)
        {
            string id = game.Mystery?.CulpritId;
            if (string.IsNullOrEmpty(id)) return null;
            var culprit = SuspectNPC.All.Where(n => n != null && n.IsSpawned && n.SuspectId == id && HouseSite.InPlay(n))
                .OrderBy(n => Vector3.Distance(n.transform.position, near)).FirstOrDefault();
            if (culprit == null) return null;

            var standIn = culprit.GetComponent<StandInHaunter>() ?? culprit.gameObject.AddComponent<StandInHaunter>();
            standIn.npc = culprit;
            var director = FindAnyObjectByType<AIDirector>();
            standIn.difficulty = director != null ? director.Difficulty : 1f;
            standIn.balksLeft = Mathf.Max(0, Mathf.RoundToInt(standIn.difficulty * 1.5f));
            standIn.unmasked = false;
            standIn.goal = culprit.transform.position;
            standIn.enabled = true;
            culprit.ServerSetCostume(true);
            Active = standIn;
            return standIn;
        }

        public Vector3 Position => transform.position;

        void OnDisable() { if (Active == this) Active = null; }

        void Update()
        {
            var game = MysteryGameManager.Instance;
            if (game == null || !game.IsServer || npc == null) return;
            var phase = game.Phase.Value;

            if (phase == MatchPhase.Unmasking || phase == MatchPhase.Ended)
            {
                // Caught: the costume comes off and it stops where it is. If it got away, it keeps it on.
                if (!unmasked)
                {
                    unmasked = true;
                    if (phase == MatchPhase.Unmasking || game.Winner.Value == MatchWinner.Solvers) npc.ServerSetCostume(false);
                    FaceNearestSolver();
                }
                return;
            }
            if (phase != MatchPhase.Trap)
            {
                npc.ServerSetCostume(false);
                enabled = false;
                return;
            }

            var trap = ArmedTrap();
            var solvers = SolverController.All.Where(s => s != null && s.IsSpawned && !s.IsPanicked).ToList();
            var chaser = solvers.Where(s => Vector3.Distance(s.transform.position, transform.position) < SpookDistance && Sees(s))
                .OrderBy(s => Vector3.Distance(s.transform.position, transform.position)).FirstOrDefault();

            if (chaser != null)
            {
                // Run directly away, then keep going for a moment.
                Vector3 away = transform.position - chaser.transform.position;
                away.y = 0f;
                goal = Clamp(transform.position + away.normalized * 6f, game);
                runUntil = Time.time + 1.8f;
                nextGoal = runUntil;
            }
            else if (trap != null && Time.time >= runUntil)
            {
                bool guarded = solvers.Any(s => Vector3.Distance(s.transform.position, trap.transform.position) < GuardDistance);
                float toTrap = Flat(trap.transform.position - transform.position).magnitude;
                if (toTrap > BalkDistance + 4f) balkRolled = false; // walked off: it may smell it again next time
                if (!guarded)
                {
                    if (toTrap < BalkDistance && !balkRolled)
                    {
                        balkRolled = true;
                        if (balksLeft > 0 && Random.value < BalkChance * difficulty)
                        {
                            balksLeft--;
                            Vector3 back = Flat(transform.position - trap.transform.position).normalized;
                            goal = Clamp(transform.position + back * 7f, game);
                            runUntil = Time.time + 3f;
                            nextGoal = runUntil + 2f;
                            npc.ServerStartleOnly();
                            game.Announce("The Haunter sniffed out the trap and backed away! Stay hidden and let it come back.");
                        }
                    }
                    if (Time.time >= runUntil) goal = trap.transform.position;
                }
                else if (Time.time >= nextGoal) PickProwl(game, solvers);
            }
            else if (Time.time >= nextGoal) PickProwl(game, solvers);

            if (trap == null) balkRolled = false; // a fresh trap is a fresh chance to smell it
            Move(game, trap, Time.time < runUntil ? RunSpeed : WalkSpeed);
        }

        TrapSite ArmedTrap() =>
            FindObjectsByType<TrapSite>(FindObjectsSortMode.None).Where(t => t.IsArmed && HouseSite.InPlay(t))
                .OrderBy(t => Vector3.Distance(t.transform.position, transform.position)).FirstOrDefault();

        /// <summary>A spot somewhere in the house, as far as it can get from the nearest Solver.</summary>
        void PickProwl(MysteryGameManager game, System.Collections.Generic.List<SolverController> solvers)
        {
            nextGoal = Time.time + Random.Range(3f, 6f);
            Vector3 best = transform.position;
            float bestScore = float.MinValue;
            for (int i = 0; i < 8; i++)
            {
                Vector2 r = Random.insideUnitCircle * 8f;
                Vector3 p = Clamp(transform.position + new Vector3(r.x, 0f, r.y), game);
                float score = solvers.Count == 0 ? Random.value : solvers.Min(s => Flat(s.transform.position - p).magnitude);
                if (Blocked(p)) score -= 100f;
                if (score > bestScore) { bestScore = score; best = p; }
            }
            goal = best;
        }

        /// <summary>
        /// Where to head for to reach the goal: the goal itself if the way is clear, otherwise the
        /// first doorway on the shortest chain of doorways that can each see the next (a small
        /// search over this house's doors; houses have a dozen or so).
        /// </summary>
        Vector3 Waypoint(Vector3 target)
        {
            Vector3 from = transform.position;
            if (Clear(from, target)) return target;
            var doors = FindObjectsByType<HouseDoor>(FindObjectsSortMode.None).Where(HouseSite.InPlay).Select(d => d.Doorway).ToList();
            var cameFrom = new int[doors.Count];
            var cost = Enumerable.Repeat(float.MaxValue, doors.Count).ToArray();
            var open = new System.Collections.Generic.List<int>();
            for (int i = 0; i < doors.Count; i++)
                if (Clear(from, doors[i])) { cost[i] = Vector3.Distance(from, doors[i]); cameFrom[i] = -1; open.Add(i); }
            int best = -1;
            float bestTotal = float.MaxValue;
            while (open.Count > 0)
            {
                int cur = open.OrderBy(i => cost[i]).First();
                open.Remove(cur);
                if (Clear(doors[cur], target))
                {
                    float total = cost[cur] + Vector3.Distance(doors[cur], target);
                    if (total < bestTotal) { bestTotal = total; best = cur; }
                }
                for (int j = 0; j < doors.Count; j++)
                {
                    float c = cost[cur] + Vector3.Distance(doors[cur], doors[j]);
                    if (j == cur || c >= cost[j] || !Clear(doors[cur], doors[j])) continue;
                    cost[j] = c; cameFrom[j] = cur;
                    if (!open.Contains(j)) open.Add(j);
                }
            }
            if (best < 0) return target; // no known way: walk at it and let the side steps (or the back way) sort it out
            while (cameFrom[best] >= 0) best = cameFrom[best];
            return doors[best];
        }

        /// <summary>True if a body-wide line between two points meets nothing solid but doors, traps and people.</summary>
        bool Clear(Vector3 a, Vector3 b)
        {
            Vector3 up = Vector3.up * 1f, d = Flat(b - a);
            if (d.sqrMagnitude < 0.01f) return true;
            foreach (var hit in Physics.SphereCastAll(a + up, 0.3f, d.normalized, d.magnitude, ~0, QueryTriggerInteraction.Ignore))
                if (Solid(hit.collider)) return false;
            return true;
        }

        bool Solid(Collider c) =>
            !c.transform.IsChildOf(transform) && c.GetComponentInParent<TrapSite>() == null && c.GetComponentInParent<HouseDoor>() == null
            && c.GetComponentInParent<SolverController>() == null && c.GetComponentInParent<SuspectNPC>() == null;

        void Move(MysteryGameManager game, TrapSite trap, float speed)
        {
            // Route through doorways, re-planned twice a second, and open doors on the way.
            if (goal != routedGoal) { routedGoal = goal; nextRoute = 0f; }
            if (Time.time >= nextRoute) { nextRoute = Time.time + 0.5f; route = Waypoint(goal); }
            foreach (var door in FindObjectsByType<HouseDoor>(FindObjectsSortMode.None))
                if (!door.IsOpen && Vector3.Distance(door.Doorway, transform.position) < 1.6f) door.ServerOpen();
            Vector3 to = Flat(route - transform.position);
            if (to.sqrMagnitude < 0.04f && route != goal) { nextRoute = 0f; return; }
            if (to.sqrMagnitude < 0.04f) { stuckFor = 0f; return; }
            Vector3 dir = to.normalized;
            float step = speed * Time.deltaTime;

            // Walk around furniture and walls: straight on if clear, otherwise the first clear side step.
            if (Blocked(transform.position + dir * 0.6f))
            {
                Vector3 chosen = Vector3.zero;
                foreach (float turn in new[] { 40f, -40f, 80f, -80f, 120f, -120f })
                {
                    Vector3 d = Quaternion.Euler(0f, turn, 0f) * dir;
                    if (!Blocked(transform.position + d * 0.6f)) { chosen = d; break; }
                }
                if (chosen == Vector3.zero) { stuckFor += Time.deltaTime; dir = Vector3.zero; } else { dir = chosen; stuckFor += Time.deltaTime * 0.5f; }
            }
            else stuckFor = Mathf.Max(0f, stuckFor - Time.deltaTime);

            // On the way to the bait but getting no closer (walls in the way, going round in circles):
            // it takes the back way round and turns up near the trap, out of the club's sight.
            bool baited = trap != null && goal == trap.transform.position;
            if (!baited) { bestToBait = float.MaxValue; lastProgress = Time.time; }
            else if (Flat(goal - transform.position).magnitude < bestToBait - 0.5f) { bestToBait = Flat(goal - transform.position).magnitude; lastProgress = Time.time; }
            if (baited && (stuckFor > 5f || Time.time - lastProgress > 6f))
            {
                stuckFor = 0f;
                lastProgress = Time.time;
                bestToBait = BalkDistance + 0.5f;
                Vector3 behind = trap.transform.position + Flat(transform.position - trap.transform.position).normalized * (BalkDistance + 0.5f);
                if (!Blocked(behind) && !SolverController.All.Any(s => s != null && Vector3.Distance(s.transform.position, behind) < GuardDistance))
                    npc.ServerPlace(behind, transform.rotation);
                return;
            }
            if (stuckFor > 2.5f && (trap == null || goal != trap.transform.position)) { nextGoal = 0f; stuckFor = 0f; }

            if (dir.sqrMagnitude > 0f)
            {
                transform.position = Clamp(transform.position + dir * Mathf.Min(step, to.magnitude), game);
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(dir), 6f * Time.deltaTime);
            }
        }

        bool Sees(SolverController s)
        {
            Vector3 eye = transform.position + Vector3.up * 1.6f;
            Vector3 to = s.EyePosition - eye;
            foreach (var hit in Physics.RaycastAll(eye, to.normalized, to.magnitude, ~0, QueryTriggerInteraction.Ignore))
            {
                if (hit.transform.IsChildOf(transform) || hit.transform.IsChildOf(s.transform)) continue;
                return false;
            }
            return true;
        }

        /// <summary>Something solid at body height there (it steps into traps and through doorways it opens).</summary>
        bool Blocked(Vector3 at) =>
            Physics.OverlapSphere(at + Vector3.up * 1f, 0.35f, ~0, QueryTriggerInteraction.Ignore).Any(Solid);

        static Vector3 Flat(Vector3 v) { v.y = 0f; return v; }

        Vector3 Clamp(Vector3 p, MysteryGameManager game)
        {
            p.y = transform.position.y;
            if (game.TryGetPlayArea(out var c, out var half))
            {
                p.x = Mathf.Clamp(p.x, c.x - half.x, c.x + half.x);
                p.z = Mathf.Clamp(p.z, c.z - half.y, c.z + half.y);
            }
            return p;
        }

        void FaceNearestSolver()
        {
            var s = SolverController.All.Where(x => x != null).OrderBy(x => Vector3.Distance(x.transform.position, transform.position)).FirstOrDefault();
            if (s == null) return;
            Vector3 to = Flat(s.transform.position - transform.position);
            if (to.sqrMagnitude > 0.01f) transform.rotation = Quaternion.LookRotation(to);
        }
    }
}
