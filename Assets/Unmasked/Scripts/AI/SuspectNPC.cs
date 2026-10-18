using System.Collections.Generic;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// A suspect standing around the house. Solvers interview each one once (E) during the
    /// investigation; what they say lands on everyone's Suspect Board. The culprit lies.
    /// During the investigation they mill about near where they were placed (server-driven,
    /// synced by a NetworkTransform).
    /// Scares nearby make them jump and scurry away; a suspect who saw one up close remembers a
    /// detail about the Haunter (MysteryServer.NoteWitness), which comes out when interviewed.
    /// Asked a question, everyone hesitates for a moment before answering (a glance down, a
    /// swallow). The culprit and the innocents hesitate alike: nerves are character, not proof.
    /// </summary>
    public class SuspectNPC : NetworkBehaviour, IInteractable
    {
        [Tooltip("Must match a suspect id in the case (Groundskeeper, Heiress, Rival, Cook in the demo).")]
        public string SuspectId;
        public TextMesh NameLabel;

        /// <summary>Children of "Model" named Outfit_&lt;HouseId&gt;: what this suspect wears at each house.</summary>
        public const string OutfitPrefix = "Outfit_";
        string shownHouse;

        [Tooltip("How far from their spot a suspect strolls while the club investigates.")]
        public float WanderRadius = 1.6f;
        public float WalkSpeed = 0.7f;

        public float FleeSpeed = 3.2f;

        Vector3 home, target;
        bool hasHome;
        float nextStroll, fleeUntil, eekUntil, hesitateUntil;
        bool answering;

        public static readonly List<SuspectNPC> All = new();

        public override void OnNetworkSpawn() => All.Add(this);
        public override void OnNetworkDespawn() => All.Remove(this);

        /// <summary>
        /// Server: every suspect at tonight's house within radius of a scare startles. Those who saw
        /// it (line of sight) become witnesses; with requireLineOfSight off, hearing it is enough to jump.
        /// </summary>
        public static void StartleInRadius(Vector3 origin, float radius, Transform ignore = null, bool requireLineOfSight = true)
        {
            var game = MysteryGameManager.Instance;
            if (game == null || !game.IsServer || game.Phase.Value != MatchPhase.Investigation) return;
            foreach (var npc in All.ToArray())
            {
                if (npc == null || !HouseSite.InPlay(npc)) continue;
                if (Vector3.Distance(npc.transform.position, origin) > radius) continue;
                bool saw = npc.CanSee(origin, ignore);
                if (requireLineOfSight && !saw) continue;
                npc.ServerStartle(origin, saw);
            }
        }

        bool CanSee(Vector3 origin, Transform ignore)
        {
            Vector3 eye = transform.position + Vector3.up * 1.7f;
            Vector3 to = origin - eye;
            foreach (var hit in Physics.RaycastAll(eye, to.normalized, to.magnitude, ~0, QueryTriggerInteraction.Ignore))
            {
                if (hit.transform.IsChildOf(transform)) continue;
                if (ignore != null && hit.transform.IsChildOf(ignore)) continue;
                return false;
            }
            return true;
        }

        void ServerStartle(Vector3 origin, bool saw)
        {
            if (!hasHome) { home = target = transform.position; hasHome = true; }
            Vector3 away = transform.position - origin;
            away.y = 0f;
            if (away.sqrMagnitude < 0.01f) away = Random.insideUnitSphere;
            away.y = 0f;
            Vector3 dir = away.normalized;
            Vector3 eye = transform.position + Vector3.up;
            float run = 2.5f;
            if (Physics.SphereCast(eye, 0.35f, dir, out var hit, run + 0.4f, ~0, QueryTriggerInteraction.Ignore))
                run = Mathf.Max(0f, hit.distance - 0.4f);
            target = transform.position + dir * run;
            fleeUntil = Time.time + 1.5f;
            nextStroll = Time.time + Random.Range(5f, 9f);
            if (saw) MysteryGameManager.Instance.Mystery?.NoteWitness(SuspectId);
            StartleRpc();
        }

        [Rpc(SendTo.ClientsAndHost)]
        void StartleRpc()
        {
            var anim = GetComponent<PawnAnimator>();
            if (anim != null) anim.Startle();
            Sfx.Play("eek", transform.position + Vector3.up * 1.7f, 0.8f, 20f, Random.Range(0.85f, 1.25f));
            eekUntil = Time.time + 1.2f;
        }

        void Update()
        {
            var game = MysteryGameManager.Instance;
            if (IsServer && IsSpawned) Stroll(game);
            if (game != null && game.IsSpawned)
            {
                string house = game.ActiveHouse.Value.ToString();
                if (house != shownHouse) { shownHouse = house; ShowOutfit(house); }
            }
            if (NameLabel == null) return;
            if (game != null && game.IsSpawned)
            {
                string label = game.SuspectName(SuspectId);
                if (game.IsCleared(SuspectId)) label += "\n(innocent)";
                if (Time.time < eekUntil) label = "Eek!\n" + label;
                else if (Time.time < hesitateUntil) label = "...\n" + label;
                NameLabel.text = label;
            }
            // Billboard toward the camera.
            var cam = Camera.main;
            if (cam != null) NameLabel.transform.rotation = Quaternion.LookRotation(NameLabel.transform.position - cam.transform.position);
        }

        /// <summary>Every client: dress for tonight's house (Blackwood Manor's outfit if the house has none).</summary>
        void ShowOutfit(string houseId)
        {
            var model = transform.Find("Model");
            if (model == null) return;
            var pick = string.IsNullOrEmpty(houseId) ? null : model.Find(OutfitPrefix + houseId);
            if (pick == null) pick = model.Find(OutfitPrefix + Cases.DefaultHouse);
            if (pick == null) return;
            foreach (Transform child in model)
                if (child.name.StartsWith(OutfitPrefix)) child.gameObject.SetActive(child == pick);
        }

        /// <summary>
        /// Server, Hollow Creek: walk on over to tonight's house (the town build gives suspects a
        /// NetworkTransform so the move reaches every machine).
        /// </summary>
        public void ServerPlace(Vector3 position, Quaternion rotation)
        {
            if (!IsServer) return;
            transform.SetPositionAndRotation(position, rotation);
            home = target = position;
            hasHome = true;
            nextStroll = Time.time + Random.Range(2f, 5f);
        }

        /// <summary>Server: wander a few steps from home now and then, never through a wall.</summary>
        void Stroll(MysteryGameManager game)
        {
            if (!hasHome) { home = target = transform.position; hasHome = true; }
            if (game == null || game.Phase.Value != MatchPhase.Investigation) return;

            Vector3 to = target - transform.position;
            to.y = 0f;
            if (to.sqrMagnitude > 0.01f)
            {
                float speed = Time.time < fleeUntil ? FleeSpeed : WalkSpeed;
                transform.position = Vector3.MoveTowards(transform.position, target, speed * Time.deltaTime);
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(to), 4f * Time.deltaTime);
                return;
            }
            if (Time.time < nextStroll) return;
            nextStroll = Time.time + Random.Range(3f, 8f);

            Vector2 step = Random.insideUnitCircle * WanderRadius;
            Vector3 next = home + new Vector3(step.x, 0f, step.y);
            Vector3 eye = transform.position + Vector3.up;
            Vector3 dir = next - transform.position;
            // Stay put if a wall, door or furniture is in the way (with room for the suspect's width).
            if (!Physics.SphereCast(eye, 0.35f, dir.normalized, out _, dir.magnitude + 0.4f, ~0, QueryTriggerInteraction.Ignore))
                target = next;
        }

        public bool CanInteract(SolverController solver)
        {
            var game = MysteryGameManager.Instance;
            return game != null && game.Phase.Value == MatchPhase.Investigation && !game.HasBeenInterviewed(SuspectId) && !answering;
        }

        public string GetPrompt(SolverController solver) => $"Interview {MysteryGameManager.Instance.SuspectName(SuspectId)}";

        public void Interact(SolverController solver)
        {
            if (!IsServer || !CanInteract(solver)) return;
            StartCoroutine(Answer(solver));
        }

        /// <summary>Server: a pause (same odds for everyone), then the answer lands on the board.</summary>
        System.Collections.IEnumerator Answer(SolverController solver)
        {
            answering = true;
            float pause = Random.Range(0.7f, 1.3f);
            HesitateRpc(pause);
            yield return new WaitForSeconds(pause);
            answering = false;
            var game = MysteryGameManager.Instance;
            if (game == null || game.Phase.Value != MatchPhase.Investigation) yield break;
            if (game.Mystery.InterviewSuspect(SuspectId, solver))
                game.Announce($"{game.SuspectName(SuspectId)} was interviewed. Check the Suspect Board (Tab).");
        }

        [Rpc(SendTo.ClientsAndHost)]
        void HesitateRpc(float pause)
        {
            hesitateUntil = Time.time + pause;
            var anim = GetComponent<PawnAnimator>();
            if (anim != null) anim.Hesitate(pause);
            var face = GetComponent<FaceLife>();
            if (face != null) face.Talk(2.4f, pause); // then the answer
        }
    }
}
