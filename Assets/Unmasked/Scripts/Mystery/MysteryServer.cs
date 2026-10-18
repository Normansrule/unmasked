using System.Collections.Generic;
using System.Linq;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The secret half of the mystery: who the Haunter really is, which clue is where, and which
    /// clues are fakes. A plain C# object that only ever exists on the server; nothing in it is a
    /// NetworkVariable, so a client can't read it. Clients only see discovered clues, through
    /// MysteryGameManager's public lists.
    /// </summary>
    public class MysteryServer
    {
        class ClueRecord
        {
            public ClueDefinition Definition;
            public ClueItem Item;
            public bool Fake;
            public bool Discovered;
        }

        readonly MysteryGameManager manager;
        readonly Dictionary<int, ClueRecord> clues = new();
        readonly HashSet<string> usedTrueClueIds = new();
        readonly HashSet<string> interviewed = new();
        readonly HashSet<string> witnesses = new();
        int leaksThisMatch;

        public CaseDefinition Case { get; private set; }
        /// <summary>The house the case is set at (picks the interview gossip); empty means Blackwood Manor.</summary>
        public string HouseId { get; private set; }
        /// <summary>Which of the house's cases this is ("PembertonCottage", or "PembertonCottage#2" on a return visit).</summary>
        public string CaseId { get; private set; }
        public string CulpritId { get; private set; }
        public bool CulpritLocked { get; private set; }

        /// <summary>Chance an innocent suspect's tip points at the real culprit.</summary>
        public float InterviewHintAccuracy = 0.55f;
        /// <summary>Snack bribes loosen tongues.</summary>
        public float SnackerAccuracyBonus = 0.25f;
        public float LeakScatterRadius = 2f;

        SuspectDefinition Culprit => Case.FindSuspect(CulpritId);

        public MysteryServer(MysteryGameManager manager, CaseDefinition caseDefinition)
        {
            this.manager = manager;
            Case = caseDefinition != null ? caseDefinition : DemoCase.BuildBlackwoodManor();
        }

        /// <summary>
        /// Swaps in another house's case before the culprit is locked in. Suspect ids are the same
        /// four slots in every case, so the Haunter's pick carries over.
        /// </summary>
        public bool UseCase(CaseDefinition caseDefinition, string houseId, string caseId = null)
        {
            if (CulpritLocked || caseDefinition == null) return false;
            Case = caseDefinition;
            HouseId = houseId;
            CaseId = string.IsNullOrEmpty(caseId) ? houseId : caseId;
            return true;
        }

        public bool IsValidSuspect(string id) => Case.FindSuspect(id) != null;
        public bool IsCulprit(string id) => CulpritLocked && id == CulpritId;
        public bool HasBeenInterviewed(string id) => interviewed.Contains(id);

        /// <summary>Haunter's pick during Setup. null clears it.</summary>
        public bool SetCulpritChoice(string id)
        {
            if (CulpritLocked || (!string.IsNullOrEmpty(id) && !IsValidSuspect(id))) return false;
            CulpritId = id;
            return true;
        }

        /// <summary>Start of Investigation: the Haunter's pick, or random if nobody picked (AI / no Haunter).</summary>
        public string LockInCulprit()
        {
            if (!CulpritLocked)
            {
                if (!IsValidSuspect(CulpritId) && Case.Suspects.Count > 0)
                    CulpritId = Case.Suspects[Random.Range(0, Case.Suspects.Count)].Id;
                CulpritLocked = true;
            }
            return CulpritId;
        }

        public void SeedClues()
        {
            var culprit = Culprit;
            if (culprit == null) return;

            var candidates = Case.Clues.Where(c => c != null && c.CanBeSeeded && c.Implicates(culprit)).ToList();
            // In Hollow Creek only tonight's house gets clues.
            var points = Object.FindObjectsByType<ClueSpawnPoint>(FindObjectsSortMode.None).Where(HouseSite.InPlay).ToList();
            if (points.Count == 0)
            {
                Debug.LogWarning("[Unmasked] No ClueSpawnPoints in the scene, so no clues were hidden.");
                return;
            }

            Shuffle(candidates);
            Shuffle(points);
            int count = Mathf.Min(Case.MaxSeededClues, Mathf.Min(candidates.Count, points.Count));
            for (int i = 0; i < count; i++)
            {
                SpawnClue(candidates[i], points[i].transform.position, false);
                usedTrueClueIds.Add(candidates[i].Id);
            }
        }

        /// <summary>A Haunter power went off near this point: roll whether it left a true clue behind.</summary>
        public bool TryLeakClue(Vector3 near, float baseChance, PlayerAgent haunter)
        {
            var culprit = Culprit;
            if (culprit == null || leaksThisMatch >= Case.MaxLeaksPerMatch) return false;
            if (Random.value >= baseChance * Case.LeakChanceMultiplier) return false;

            var any = Case.Clues.Where(c => c != null && c.CanBeLeaked && c.Implicates(culprit)).ToList();
            var fresh = any.Where(c => !usedTrueClueIds.Contains(c.Id)).ToList();
            var pool = fresh.Count > 0 ? fresh : any;
            if (pool.Count == 0) return false;

            var chosen = pool[Random.Range(0, pool.Count)];
            Vector2 offset = Random.insideUnitCircle * LeakScatterRadius;
            SpawnClue(chosen, FloorBelow(near + new Vector3(offset.x, 0f, offset.y)), false);
            usedTrueClueIds.Add(chosen.Id);
            leaksThisMatch++;

            if (haunter != null) haunter.NotifyClueLeaked(near);
            return true;
        }

        /// <summary>Haunter power: drop a fake clue framing an innocent (null = random innocent).</summary>
        public bool PlantFakeClue(Vector3 at, string framedId)
        {
            var culprit = Culprit;
            if (culprit == null) return false;

            var framed = string.IsNullOrEmpty(framedId)
                ? RandomFrom(Case.Suspects.Where(s => s != null && s != culprit).ToList())
                : Case.FindSuspect(framedId);
            if (framed == null || framed == culprit) return false;

            // A good fake points at the framed suspect and NOT at the Haunter.
            var candidates = Case.Clues.Where(c => c != null && c.CanBeFaked && c.Implicates(framed) && !c.Implicates(culprit)).ToList();
            if (candidates.Count == 0) return false;

            SpawnClue(RandomFrom(candidates), FloorBelow(at), true);
            return true;
        }

        public bool DiscoverClue(ClueItem item, SolverController solver)
        {
            if (item == null || !clues.TryGetValue(item.InstanceId, out var record) || record.Discovered || record.Item != item)
                return false;

            record.Discovered = true;
            // record.Fake is intentionally not published. Solvers have to work that out themselves.
            manager.PublishClue(new DiscoveredClue
            {
                InstanceId = item.InstanceId,
                ClueId = record.Definition.Id,
                Name = record.Definition.DisplayName,
                Description = record.Definition.Description,
                Traits = (int)record.Definition.Traits,
                Location = item.transform.position,
                DiscoveredAt = (float)manager.NetworkManager.ServerTime.Time,
                DiscoveredBy = solver != null ? solver.OwnerClientId : 0
            });
            item.MarkDiscovered();

            var agent = solver != null ? PlayerAgent.ForClient(solver.OwnerClientId) : null;
            if (agent != null) agent.CluesFound.Value++;
            return true;
        }

        /// <summary>
        /// A suspect saw a scare up close. When interviewed they describe a detail of the Haunter
        /// instead of gossiping: one of the culprit's shared traits (narrowing it to two suspects).
        /// The culprit, of course, describes someone else's.
        /// </summary>
        public void NoteWitness(string suspectId)
        {
            if (CulpritLocked && IsValidSuspect(suspectId) && !interviewed.Contains(suspectId)) witnesses.Add(suspectId);
        }

        public bool IsWitness(string id) => witnesses.Contains(id);

        /// <summary>The Haunter covered its tracks: the culprit's alibi will hold up if checked.</summary>
        public bool AlibiFaked { get; private set; }

        public bool FakeAlibi()
        {
            if (!CulpritLocked || AlibiFaked) return false;
            AlibiFaked = true;
            return true;
        }

        /// <summary>Innocents' alibis always hold; the culprit's falls apart unless the Haunter faked it.</summary>
        public bool AlibiHolds(string id) => !IsCulprit(id) || AlibiFaked;

        static readonly string[] WitnessLines =
        {
            "It rushed right past me in the dark! I'm sure I noticed {0}.",
            "I saw it up close, I swear! There was {0}, plain as day.",
            "It brushed my sleeve. Afterwards I found {0} on my coat!",
        };

        /// <summary>What a witness says they noticed: true for an innocent, a lie for the culprit.</summary>
        string WitnessStatement(SuspectDefinition speaker, SuspectDefinition culprit)
        {
            var shared = Cases.Bits.Skip(4).ToList();
            bool lying = speaker == culprit;
            var pool = shared.Where(b => ((culprit.Traits & b) != 0) != lying).ToList();
            if (pool.Count == 0) return null;
            string detail = Cases.TraitName(CaseId, pool[Random.Range(0, pool.Count)]).ToLowerInvariant();
            return string.Format(WitnessLines[Random.Range(0, WitnessLines.Length)], detail);
        }

        /// <summary>
        /// A Solver interviewed a suspect. Innocents point at the culprit some of the time; the culprit
        /// always points at an innocent.
        /// </summary>
        public bool InterviewSuspect(string speakerId, SolverController interviewer)
        {
            var speaker = Case.FindSuspect(speakerId);
            var culprit = Culprit;
            if (speaker == null || culprit == null || interviewed.Contains(speakerId)) return false;

            var others = Case.Suspects.Where(s => s != null && s != speaker).ToList();
            var otherInnocents = others.Where(s => s != culprit).ToList();
            if (others.Count == 0) return false;

            SuspectDefinition target;
            if (speaker == culprit)
            {
                target = otherInnocents.Count > 0 ? RandomFrom(otherInnocents) : others[0];
            }
            else
            {
                var agent = interviewer != null ? PlayerAgent.ForClient(interviewer.OwnerClientId) : null;
                float accuracy = InterviewHintAccuracy + (agent != null && agent.Role.Value == SolverRole.Snacker ? SnackerAccuracyBonus : 0f);
                target = Random.value < accuracy ? culprit : RandomFrom(others);
            }

            var lines = Cases.For(CaseId).Gossip;

            string witnessed = witnesses.Contains(speakerId) ? WitnessStatement(speaker, culprit) : null;

            interviewed.Add(speakerId);
            manager.PublishInterview(new InterviewNote
            {
                SpeakerId = speaker.Id,
                SuspiciousOfId = witnessed != null ? "" : target.Id,
                Statement = witnessed ?? string.Format(lines[Random.Range(0, lines.Length)], target.DisplayName),
                Interviewer = interviewer != null ? interviewer.OwnerClientId : 0,
                At = (float)manager.Now
            });
            return true;
        }

        void SpawnClue(ClueDefinition definition, Vector3 position, bool fake)
        {
            var go = Object.Instantiate(manager.CluePrefab, position, Quaternion.identity);
            var item = go.GetComponent<ClueItem>();
            int id;
            do { id = Random.Range(1, int.MaxValue); } while (clues.ContainsKey(id)); // random: ids say nothing about spawn order
            item.InstanceId = id;
            clues[id] = new ClueRecord { Definition = definition, Item = item, Fake = fake };
            go.GetComponent<NetworkObject>().Spawn(true);
        }

        static Vector3 FloorBelow(Vector3 point)
        {
            return Physics.Raycast(point + Vector3.up * 0.5f, Vector3.down, out var hit, 10f, ~0, QueryTriggerInteraction.Ignore)
                ? hit.point + Vector3.up * 0.1f
                : point;
        }

        static T RandomFrom<T>(IList<T> list) => list.Count == 0 ? default : list[Random.Range(0, list.Count)];

        static void Shuffle<T>(IList<T> list)
        {
            for (int i = list.Count - 1; i > 0; i--)
            {
                int j = Random.Range(0, i + 1);
                (list[i], list[j]) = (list[j], list[i]);
            }
        }
    }
}
