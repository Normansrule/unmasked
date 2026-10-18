using System.Collections.Generic;
using System.Linq;
using Unity.Collections;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Runs one mystery: Setup (Haunter secretly picks a suspect) -> [Dispatch: in Hollow Creek, drive
    /// the van from HQ to the house the call is about] -> Investigation (until dawn)
    /// -> Trap (right suspect named: build the trap, catch the costumed Haunter) -> Unmasking -> Ended.
    ///
    /// Everything here that is a NetworkVariable/NetworkList is public. The secret half of the case
    /// (culprit, clue truth, fakes) lives in <see cref="Mystery"/>, which only exists on the server.
    /// </summary>
    public class MysteryGameManager : NetworkBehaviour
    {
        public static MysteryGameManager Instance { get; private set; }

        [Header("Prefabs (filled in by the Unmasked menu level builders)")]
        public GameObject SolverPrefab;
        public GameObject HaunterPrefab;
        public GameObject CluePrefab;
        public GameObject FogPrefab;
        public GameObject PhantomPrefab;
        [Tooltip("The Headless Horseman's flaming jack-o'-lantern.")]
        public GameObject PumpkinPrefab;
        [Tooltip("Stingy Jack's will-o'-the-wisps.")]
        public GameObject WispPrefab;

        [Header("Mystery")]
        [Tooltip("Leave empty to play the built-in Blackwood Manor demo case.")]
        public CaseDefinition Case;

        [Header("Timing (seconds)")]
        public float SetupDuration = 30f;
        [Tooltip("Length of the night. The Haunter wins if the mystery is unsolved at dawn.")]
        public float MatchDuration = 900f;
        public float MaxTrapDuration = 180f;
        public float MinTrapDuration = 60f;
        public float UnmaskDuration = 8f;

        [Header("Hollow Creek (town scene only)")]
        [Tooltip("How long the Solvers have to drive to the call before everyone is brought there.")]
        public float DispatchDuration = 150f;
        [Tooltip("Chance that a night gets a special event (Blood Moon, Thunderstorm...).")]
        [Range(0f, 1f)] public float EventChance = 0.6f;

        [Header("Rules")]
        public float AccusationCooldown = 10f;
        [Tooltip("A Solver who panics this many times is scared out of the match. 0 disables.")]
        public int MaxPanicsBeforeScaredOut = 3;
        public float ScaredOutDelay = 4f;

        // ---- Public, replicated match state ----
        public readonly NetworkVariable<MatchPhase> Phase = new();
        public readonly NetworkVariable<double> PhaseEndTime = new();
        /// <summary>When tonight's investigation began and how long the night lasts (for the night clock).</summary>
        /// <summary>Houses whose case this club has solved (saved on the host between sessions).</summary>
        public NetworkList<FixedString32Bytes> SolvedCases;
        public readonly NetworkVariable<double> NightStart = new();
        public readonly NetworkVariable<float> NightLength = new();
        public readonly NetworkVariable<int> CluesRequiredToAccuse = new(2);
        public readonly NetworkVariable<int> AccusationsLeft = new(2);
        public readonly NetworkVariable<int> AlibiChecksLeft = new(2);
        /// <summary>Tonight's case: the house id, or "HouseId#2" on a return visit (Cases.For takes either).</summary>
        public readonly NetworkVariable<FixedString32Bytes> ActiveCase = new();
        /// <summary>Favours the townsfolk owe the club (errands run between cases): extra alibi checks on the next case.</summary>
        public readonly NetworkVariable<int> Favours = new(0);
        /// <summary>
        /// Pieces of the Lantern Watch costume the townsfolk have given the club (bit i = the i-th
        /// townsperson in HollowCreek.json "folk"), and whether the club has it on (CostumeTrunk at HQ).
        /// </summary>
        public readonly NetworkVariable<int> WatchPieces = new(0);
        public readonly NetworkVariable<bool> WearingWatch = new(false);
        public readonly NetworkVariable<MatchWinner> Winner = new();
        public readonly NetworkVariable<MatchEndReason> EndReason = new();
        /// <summary>Which legend the Haunter's costume is tonight (public: everyone sees the costume).</summary>
        public readonly NetworkVariable<VillainKind> Villain = new();
        /// <summary>Hollow Creek: the house tonight's call is about (a HouseSite id). Empty until a call is picked.</summary>
        public readonly NetworkVariable<FixedString32Bytes> ActiveHouse = new();
        /// <summary>Tonight's special event, if any (public: the HUD announces it).</summary>
        public readonly NetworkVariable<NightEvent> Event = new();
        /// <summary>Empty until the Haunter is unmasked or the match ends.</summary>
        public readonly NetworkVariable<FixedString32Bytes> RevealedCulprit = new();
        public NetworkList<SuspectInfo> Suspects;
        public NetworkList<DiscoveredClue> Clues;
        public NetworkList<InterviewNote> Interviews;
        public NetworkList<FixedString32Bytes> ClearedSuspects;
        /// <summary>Alibis the Solvers checked: those that held up and those that fell apart.</summary>
        public NetworkList<FixedString32Bytes> AlibisHold, AlibisBroken;

        /// <summary>Server only. Null on clients.</summary>
        public MysteryServer Mystery { get; private set; }

        public double Now => NetworkManager != null ? NetworkManager.ServerTime.Time : 0;
        public float PhaseTimeRemaining => PhaseEndTime.Value > 0 ? Mathf.Max(0f, (float)(PhaseEndTime.Value - Now)) : 0f;

        void Awake()
        {
            Instance = this;
            Suspects = new NetworkList<SuspectInfo>();
            Clues = new NetworkList<DiscoveredClue>();
            Interviews = new NetworkList<InterviewNote>();
            ClearedSuspects = new NetworkList<FixedString32Bytes>();
            AlibisHold = new NetworkList<FixedString32Bytes>();
            AlibisBroken = new NetworkList<FixedString32Bytes>();
            SolvedCases = new NetworkList<FixedString32Bytes>();
        }

        public override void OnNetworkSpawn()
        {
            if (!IsServer) return;

            Mystery = new MysteryServer(this, Case);
            PublishCase();
            LoadCaseBook();
            LoadProgress();

            foreach (var agent in PlayerAgent.All.ToList())
                OnPlayerJoined(agent);

            BeginSetup();
        }

        void Update()
        {
            if (!IsServer) return;
            if (Phase.Value == MatchPhase.Dispatch) CheckArrival();
            if (Phase.Value == MatchPhase.Investigation || Phase.Value == MatchPhase.Trap) UpdateNightEvent();
            if (PhaseEndTime.Value <= 0 || Now < PhaseEndTime.Value) return;

            switch (Phase.Value)
            {
                case MatchPhase.Setup:
                    if (InTown) BeginDispatch(); else BeginInvestigation();
                    break;
                case MatchPhase.Dispatch:
                    BringEveryoneToTheHouse();
                    BeginInvestigation();
                    break;
                case MatchPhase.Investigation: EndMatch(MatchWinner.Haunter, MatchEndReason.Dawn); break;
                case MatchPhase.Trap: EndMatch(MatchWinner.Haunter, MatchEndReason.Escaped); break;
                case MatchPhase.Unmasking: EndMatch(MatchWinner.Solvers, MatchEndReason.Unmasked); break;
            }
        }

        // -------------------------------------------------------------------
        // Queries (any machine)
        // -------------------------------------------------------------------

        public bool FindSuspect(string id, out SuspectInfo info)
        {
            foreach (var s in Suspects)
            {
                if (s.Id.ToString() == id) { info = s; return true; }
            }
            info = default;
            return false;
        }

        public string SuspectName(string id) => FindSuspect(id, out var info) ? info.Name.ToString() : id;

        /// <summary>The room a suspect's alibi puts them in ("" if it can't be checked).</summary>
        public string AlibiRoomOf(string id) => FindSuspect(id, out var info) ? info.AlibiRoom.ToString() : "";

        /// <summary>1: checked and it held up. -1: checked and it fell apart. 0: not checked.</summary>
        public int AlibiStatus(string id)
        {
            foreach (var a in AlibisHold) if (a.ToString() == id) return 1;
            foreach (var a in AlibisBroken) if (a.ToString() == id) return -1;
            return 0;
        }

        public bool IsCleared(string id)
        {
            foreach (var c in ClearedSuspects) if (c.ToString() == id) return true;
            return false;
        }

        public bool HasBeenInterviewed(string id)
        {
            foreach (var n in Interviews) if (n.SpeakerId.ToString() == id) return true;
            return false;
        }

        /// <summary>How many discovered clues point at each suspect, in Suspects order.</summary>
        public int[] ClueMatchCounts()
        {
            var counts = new int[Suspects.Count];
            for (int i = 0; i < Suspects.Count; i++)
                foreach (var clue in Clues)
                    if ((Suspects[i].Traits & clue.Traits) != 0) counts[i]++;
            return counts;
        }

        /// <summary>
        /// The time of night at a server time: the investigation runs from 8:00 PM to dawn at 6:00 AM,
        /// so every clue and statement on the board gets a time ("10:40 PM").
        /// </summary>
        public string NightClock(double serverTime)
        {
            if (NightLength.Value <= 0f) return "";
            double k = System.Math.Clamp((serverTime - NightStart.Value) / NightLength.Value, 0.0, 1.0);
            int minutes = 20 * 60 + (int)(k * 10 * 60);
            minutes = (minutes / 5 * 5) % (24 * 60);
            int h = minutes / 60, m = minutes % 60;
            return $"{(h % 12 == 0 ? 12 : h % 12)}:{m:00} {(h >= 12 ? "PM" : "AM")}";
        }

        public bool CanAccuseNow => Phase.Value == MatchPhase.Investigation && AccusationsLeft.Value > 0 && Clues.Count >= CluesRequiredToAccuse.Value;

        // ---- Hollow Creek ----

        /// <summary>True in the town scene: nights start at HQ and go through Dispatch.</summary>
        public bool InTown => TownDirector.Instance != null;

        /// <summary>The house tonight's call is about (null outside the town or before a call is picked).</summary>
        public HouseSite ActiveSite => InTown ? TownDirector.Instance.Find(ActiveHouse.Value.ToString()) : null;

        public string HouseName => ActiveSite != null ? ActiveSite.DisplayName : InTown ? "Hollow Creek" : "Blackwood Manor";

        /// <summary>Where the Haunter may drift: around tonight's house, or HQ before the call.</summary>
        public bool TryGetPlayArea(out Vector3 center, out Vector2 halfSize)
        {
            var site = ActiveSite != null ? ActiveSite : InTown ? TownDirector.Instance.HQ : null;
            center = site != null ? site.Center : Vector3.zero;
            halfSize = site != null ? site.HalfSize + new Vector2(4f, 4f) : Vector2.zero;
            return site != null;
        }

        /// <summary>Night events: scares hit harder under the Blood Moon, softer at the Harvest Festival.</summary>
        public float FearMultiplier => Event.Value switch
        {
            NightEvent.BloodMoon => 1.25f,
            NightEvent.HarvestFestival => 0.8f,
            _ => 1f
        };

        public float EctoplasmRegenMultiplier => Event.Value == NightEvent.BloodMoon ? 1.5f : 1f;

        public float BatteryDrainMultiplier => Event.Value switch
        {
            NightEvent.PowerOutage => 1.6f,
            NightEvent.Thunderstorm => 1.2f,
            _ => 1f
        };

        public PlayerAgent HaunterAgent => PlayerAgent.All.FirstOrDefault(a => a.Side.Value == PlayerSide.Haunter);

        /// <summary>Server only.</summary>
        public HaunterController HaunterPawn => HaunterAgent != null && HaunterAgent.Pawn != null ? HaunterAgent.Pawn.GetComponent<HaunterController>() : null;

        // -------------------------------------------------------------------
        // Phases (server)
        // -------------------------------------------------------------------

        void SetPhase(MatchPhase phase, float duration)
        {
            Phase.Value = phase;
            PhaseEndTime.Value = duration > 0 ? Now + duration : 0;
        }

        void BeginSetup()
        {
            // A random legend haunts tonight; a player Haunter can pick another during setup.
            Villain.Value = (VillainKind)Random.Range(0, System.Enum.GetValues(typeof(VillainKind)).Length);
            SetPhase(MatchPhase.Setup, SetupDuration);
            Announce(InTown
                ? "A spooky night in Hollow Creek. Waiting at HQ for a call... (pick one on the call board, or wait for a random one)"
                : "A spooky night begins... the Haunter is choosing a disguise.");
        }

        /// <summary>Server: tells everyone who the suspects are and how many accusations the case allows.</summary>
        void PublishCase()
        {
            Suspects.Clear();
            foreach (var suspect in Mystery.Case.Suspects.Where(s => s != null))
                Suspects.Add(suspect.ToPublicInfo());
            CluesRequiredToAccuse.Value = Mystery.Case.CluesRequiredToAccuse;
            AccusationsLeft.Value = Mathf.Max(1, Mystery.Case.MaxAccusations);
            // Favours are only spent when the club actually starts a case (BeginInvestigation): the case
            // published at HQ is often replaced by the call the club picks.
            AlibiChecksLeft.Value = Mathf.Max(0, Mystery.Case.AlibiChecks);
            AlibisHold.Clear();
            AlibisBroken.Clear();
        }

        /// <summary>
        /// Server: each house in Hollow Creek has its own case (suspects, alibis, clues). A case set on
        /// this component in the Inspector wins over the built-in ones.
        /// </summary>
        bool LoadCaseFor(string houseId)
        {
            string caseId = NextCaseFor(houseId);
            if (Case != null || Mystery == null || caseId == Mystery.CaseId) return false;
            if (!Mystery.UseCase(Cases.Build(caseId), houseId, caseId)) return false;
            ActiveCase.Value = caseId;
            PublishCase();
            return true;
        }

        /// <summary>Every machine: which case a call to this house would be (its first case, then its return visit).</summary>
        public string NextCaseFor(string houseId) => Cases.NextCase(houseId, IsSolved);

        /// <summary>Every machine: tonight's case id, or the house's if no case has been loaded.</summary>
        public string CaseKey => ActiveCase.Value.Length > 0 ? ActiveCase.Value.ToString() : ActiveHouse.Value.ToString();

        /// <summary>Hollow Creek: a call came in. Suspects gather at the house, the Haunter is already there.</summary>
        void BeginDispatch()
        {
            var director = TownDirector.Instance;
            var houses = director.Houses;
            if (houses.Length == 0) { BeginInvestigation(); return; }
            if (ActiveSite == null || ActiveSite.IsHQ)
            {
                // A brand-new club always starts with the gentle intro case.
                var first = SolvedCases.Count == 0 ? houses.FirstOrDefault(h => h.HouseId == Cases.FirstCase) : null;
                // ...and once the four clues are in, the museum calls next.
                if (first == null && ArcComplete && !IsSolved(Cases.FinaleCase))
                    first = houses.FirstOrDefault(h => h.HouseId == Cases.FinaleCase);
                var open = houses.Where(h => IsUnlocked(h.HouseId)).ToArray();
                if (open.Length == 0) open = houses;
                // Houses with a case still to solve (a first case or a return visit) call first.
                var fresh = open.Where(h => !IsSolved(NextCaseFor(h.HouseId))).ToArray();
                if (fresh.Length > 0) open = fresh;
                ActiveHouse.Value = (first ?? open[Random.Range(0, open.Length)]).HouseId;
            }
            var site = ActiveSite;
            LoadCaseFor(site.HouseId);

            Event.Value = Random.value < EventChance
                ? (NightEvent)Random.Range(1, System.Enum.GetValues(typeof(NightEvent)).Length)
                : NightEvent.None;

            SetPhase(MatchPhase.Dispatch, DispatchDuration);

            // The suspects are waiting at the house when the club arrives.
            foreach (var npc in FindObjectsByType<SuspectNPC>(FindObjectsSortMode.None))
            {
                var spot = site.SuspectSpot(npc.SuspectId);
                if (spot != null) npc.ServerPlace(spot.position, spot.rotation);
            }

            // So is the Haunter.
            var haunter = HaunterPawn;
            if (haunter != null)
            {
                var spawn = PickSpawn(true);
                haunter.ServerTeleport(spawn.position);
            }

            string evt = Event.Value != NightEvent.None ? $" Tonight: {TownLayout.EventName(Event.Value)}!" : "";
            Announce($"Call from {site.DisplayName}: {Mystery.Case.CaseName}! Everybody in the van and follow the map (M).{evt}");
        }

        float nextArrivalCheck;

        void CheckArrival()
        {
            if (Time.time < nextArrivalCheck) return;
            nextArrivalCheck = Time.time + 0.5f;
            var site = ActiveSite;
            if (site == null) return;
            foreach (var solver in SolverController.All)
            {
                if (solver == null || !site.Contains(solver.transform.position, 2f)) continue;
                Announce($"The Mystery Club has arrived at {site.DisplayName}.");
                BringEveryoneToTheHouse();
                BeginInvestigation();
                return;
            }
        }

        /// <summary>Anyone not at the house (and not riding in the van) is brought to the gate.</summary>
        void BringEveryoneToTheHouse()
        {
            var site = ActiveSite;
            if (site == null) return;
            var spawns = FindObjectsByType<SpawnPoint>(FindObjectsSortMode.None)
                .Where(p => !p.HaunterSpawn && HouseSite.Of(p) == site).ToArray();
            int i = 0;
            foreach (var solver in SolverController.All)
            {
                if (solver == null || site.Contains(solver.transform.position, 6f) || MysteryVan.IsRiding(solver.OwnerClientId)) continue;
                Vector3 to = spawns.Length > 0 ? spawns[i++ % spawns.Length].transform.position : site.Arrival.position;
                solver.ServerTeleport(to);
            }
            var van = MysteryVan.Instance;
            if (van != null && !site.Contains(van.transform.position, 20f) && site.Arrival != null)
                van.ServerPark(site.Arrival.position, site.Arrival.rotation);
        }

        float nextStormStrike;

        /// <summary>Server: what tonight's event does during the investigation.</summary>
        void UpdateNightEvent()
        {
            if (Event.Value != NightEvent.Thunderstorm || Time.time < nextStormStrike) return;
            nextStormStrike = Time.time + Random.Range(20f, 40f);
            var lamps = FindObjectsByType<PossessableLight>(FindObjectsSortMode.None).Where(HouseSite.InPlay).ToArray();
            if (lamps.Length > 0 && Random.value < 0.5f) lamps[Random.Range(0, lamps.Length)].ServerCutPower();
            LightningRpc(Random.Range(0.6f, 1.2f));
        }

        [Rpc(SendTo.ClientsAndHost)]
        void LightningRpc(float strength) => NightEventFX.Lightning(strength);

        void BeginInvestigation()
        {
            Mystery.LockInCulprit();
            Mystery.SeedClues();
            HaunterAgent?.SendSecretIdentity(Mystery.CulpritId);
            float night = MatchDuration * (Event.Value == NightEvent.HarvestFestival ? 0.8f : 1f);
            SetPhase(MatchPhase.Investigation, night);
            NightStart.Value = Now;
            NightLength.Value = night;
            if (Favours.Value > 0)
            {
                AlibiChecksLeft.Value += Favours.Value;
                Announce($"Favours from the townsfolk: {Favours.Value} extra alibi check{(Favours.Value > 1 ? "s" : "")} on this case.");
                Favours.Value = 0;
                SaveProgress();
            }
            if (WearingWatch.Value)
                Announce($"The club is wearing the Lantern Watch costume: scares hit {Mathf.RoundToInt((1f - WatchFearMultiplier) * 100f)}% softer tonight.");
            if (Event.Value == NightEvent.PowerOutage)
                foreach (var lamp in FindObjectsByType<PossessableLight>(FindObjectsSortMode.None).Where(HouseSite.InPlay))
                    lamp.ServerCutPower();
            // The story: someone took a folklore mask from the festival. The mask is no secret; the wearer is.
            var spec = Cases.For(Mystery.CaseId);
            if (spec.IsReturnVisit) Announce($"{HouseName} is calling again. Same neighbours, new mystery: {spec.CaseName}.");
            Announce($"{spec.Premise} Someone took the {MaskName(Villain.Value)} from the festival and is haunting {HouseName}. Find out who is wearing it before dawn!");
        }

        /// <summary>"the Banshee mask", "Stingy Jack's mask": the folklore mask that grants tonight's powers.</summary>
        public static string MaskName(VillainKind villain)
        {
            string name = Costumes.NameOf(villain);
            if (name.StartsWith("The ")) return "the " + name.Substring(4) + " mask";
            return name + "'s mask";
        }

        /// <summary>Every machine: "Daisy Pemberton wore the Banshee mask to scare Grandma into moving out."</summary>
        public string UnmaskLine()
        {
            string id = RevealedCulprit.Value.ToString();
            string motive = Cases.MotiveOf(CaseKey, id);
            string line = $"{SuspectName(id)} wore {MaskName(Villain.Value)}";
            return string.IsNullOrEmpty(motive) ? line + "." : $"{line} {motive}.";
        }

        void BeginTrap()
        {
            PlayFx(SpookyFxKind.TrapSting, Vector3.zero);
            var sites = FindObjectsByType<TrapSite>(FindObjectsSortMode.None).Where(HouseSite.InPlay).ToArray();
            var haunter = HaunterPawn;

            if (sites.Length == 0)
            {
                Debug.LogWarning("[Unmasked] No TrapSite in the scene, so skipping straight to the unmasking.");
                BeginUnmasking(haunter != null ? haunter.transform.position : Vector3.zero);
                return;
            }

            foreach (var piece in FindObjectsByType<TrapPiece>(FindObjectsSortMode.None).Where(HouseSite.InPlay))
                piece.Activate();

            // Named! The Haunter is stuck in costume and has to dodge the trap.
            if (haunter != null) haunter.SetForcedPhysical(true);

            float duration = Mathf.Max(MinTrapDuration, Mathf.Min(MaxTrapDuration, PhaseTimeRemaining));
            SetPhase(MatchPhase.Trap, duration);
            Announce("That's the culprit! Gather trap pieces, build the trap and catch them!");
        }

        void BeginUnmasking(Vector3 focus)
        {
            if (Phase.Value == MatchPhase.Unmasking || Phase.Value == MatchPhase.Ended) return;

            var haunter = HaunterPawn;
            if (haunter != null) haunter.Stun(0f); // caught for good

            RevealedCulprit.Value = Mystery.CulpritId;
            SetPhase(MatchPhase.Unmasking, UnmaskDuration);
            PlayUnmaskRpc(focus, UnmaskDuration);
            PlayFx(SpookyFxKind.Unmask, focus + Vector3.up * 2f);
            Announce($"UNMASKED! It was {SuspectName(Mystery.CulpritId)}! \"And I would've gotten away with it too, if it weren't for you meddling kids!\"");
        }

        void EndMatch(MatchWinner winner, MatchEndReason reason)
        {
            if (Phase.Value == MatchPhase.Ended) return;
            Winner.Value = winner;
            EndReason.Value = reason;
            RevealedCulprit.Value = Mystery.CulpritId; // the match is decided, so everyone may know now
            SetPhase(MatchPhase.Ended, 0f);
            if (winner == MatchWinner.Solvers && reason == MatchEndReason.Unmasked) MarkSolved(Mystery.CaseId);
        }

        // ---- The case book: solved cases stay solved (a keepsake on the HQ shelf) ----

        const string CaseBookKey = "Unmasked.SolvedCases";

        void LoadCaseBook()
        {
            SolvedCases.Clear();
            foreach (var id in PlayerPrefs.GetString(CaseBookKey, "").Split(','))
                if (!string.IsNullOrEmpty(id) && !IsSolved(id)) SolvedCases.Add(id);
        }

        void MarkSolved(string houseId)
        {
            if (string.IsNullOrEmpty(houseId) || IsSolved(houseId)) return;
            SolvedCases.Add(houseId);
            var ids = new List<string>();
            foreach (var s in SolvedCases) ids.Add(s.ToString());
            PlayerPrefs.SetString(CaseBookKey, string.Join(",", ids));
            PlayerPrefs.Save();
            var spec = Cases.For(houseId);
            if (spec.IsReturnVisit) { Announce($"Case closed! {spec.Recovered}"); return; }
            Announce($"Case closed! {spec.Recovered} A keepsake goes on the HQ shelf: {Cases.KeepsakeOf(houseId)}.");
            if (houseId == Cases.FinaleCase) { Announce(Cases.ArcEpilogue); return; }
            Announce($"A clue to the Mask Keeper: {Cases.For(houseId).ArcClue}");
            if (ArcComplete) Announce(Cases.ArcFinale);
        }

        /// <summary>All four clues to the Mask Keeper are in the case book.</summary>
        public bool ArcComplete => Cases.ArcCases.All(IsSolved);

        /// <summary>The fifth call (the Historical Society) only comes in once the other four are solved.</summary>
        public bool IsUnlocked(string houseId) => houseId != Cases.FinaleCase || ArcComplete;

        public bool IsSolved(string houseId)
        {
            foreach (var s in SolvedCases) if (s.ToString() == houseId) return true;
            return false;
        }

        [Rpc(SendTo.ClientsAndHost)]
        void PlayUnmaskRpc(Vector3 focus, float duration)
        {
            if (CameraRig.Instance != null) CameraRig.Instance.PlayUnmask(focus, duration);
        }

        public void Announce(string message) => AnnounceRpc(message);

        /// <summary>
        /// Server: one of the townsfolk got their lost thing back (Townsperson) and puts in a word for
        /// the club: one more alibi check now if a case is under way, otherwise on the next one.
        /// </summary>
        public void GrantFavour(string who)
        {
            if (Phase.Value == MatchPhase.Investigation || Phase.Value == MatchPhase.Trap)
            {
                AlibiChecksLeft.Value++;
                Announce($"{who} will vouch for the club: one more alibi check tonight.");
            }
            else
            {
                Favours.Value++;
                Announce($"{who} owes the club a favour: one more alibi check on the next case.");
            }
            SaveProgress();
        }

        // ---- The Lantern Watch: a homemade costume from the townsfolk's thank-you gifts ----

        /// <summary>Pieces needed before the club can put the costume on.</summary>
        public const int WatchPiecesNeeded = 3;

        public static int CountBits(int mask)
        {
            int n = 0;
            for (; mask != 0; mask &= mask - 1) n++;
            return n;
        }

        public int WatchPieceCount => CountBits(WatchPieces.Value);
        public bool HasWatchPiece(int index) => index >= 0 && (WatchPieces.Value & (1 << index)) != 0;

        /// <summary>Scares are this much softer while the club wears it: 7% per piece, so 79% with three and 65% with all five.</summary>
        public float WatchFearMultiplier => WearingWatch.Value ? Mathf.Max(0.6f, 1f - 0.07f * WatchPieceCount) : 1f;

        /// <summary>Server: a townsperson's thank-you gift. Never given twice (the errand stays Done).</summary>
        public void GrantWatchPiece(int index, string who, string pieceName)
        {
            if (index < 0 || index > 30 || HasWatchPiece(index)) return;
            WatchPieces.Value |= 1 << index;
            int have = WatchPieceCount;
            Announce(have >= WatchPiecesNeeded
                ? $"{who} gives the club {pieceName}. That's {have} pieces of the Lantern Watch costume: try it on at the trunk at HQ."
                : $"{who} gives the club {pieceName}: a piece of a homemade costume. {WatchPiecesNeeded - have} more and the club can wear it.");
            SaveProgress();
        }

        /// <summary>Server: the trunk at HQ. Only between cases, and only with enough pieces.</summary>
        public void ToggleWatch(SolverController solver)
        {
            if (Phase.Value != MatchPhase.Setup && Phase.Value != MatchPhase.Ended) return;
            if (!WearingWatch.Value && WatchPieceCount < WatchPiecesNeeded)
            {
                PlayerAgent.ForClient(solver.OwnerClientId)?.Tell(
                    $"The Lantern Watch costume needs {WatchPiecesNeeded} pieces. The club has {WatchPieceCount}: run errands for the townsfolk.");
                return;
            }
            WearingWatch.Value = !WearingWatch.Value;
            Announce(WearingWatch.Value
                ? $"The club puts on the Lantern Watch costume. Scares hit {Mathf.RoundToInt((1f - WatchFearMultiplier) * 100f)}% softer while you wear it."
                : "The club takes the Lantern Watch costume off and packs it back in the trunk.");
            SaveProgress();
        }

        // ---- Saved progress (on the host): errands, favours, costume pieces. The case book is above. ----

        const string FavoursKey = "Unmasked.Favours", WatchKey = "Unmasked.WatchPieces", WearingKey = "Unmasked.WearingWatch";
        public const string ErrandsKey = "Unmasked.Errands";

        void LoadProgress()
        {
            Favours.Value = Mathf.Max(0, PlayerPrefs.GetInt(FavoursKey, 0));
            WatchPieces.Value = PlayerPrefs.GetInt(WatchKey, 0);
            WearingWatch.Value = PlayerPrefs.GetInt(WearingKey, 0) == 1 && WatchPieceCount >= WatchPiecesNeeded;
        }

        /// <summary>Server: writes everything that carries over between sessions.</summary>
        public void SaveProgress()
        {
            if (!IsServer) return;
            PlayerPrefs.SetInt(FavoursKey, Favours.Value);
            PlayerPrefs.SetInt(WatchKey, WatchPieces.Value);
            PlayerPrefs.SetInt(WearingKey, WearingWatch.Value ? 1 : 0);
            PlayerPrefs.SetString(ErrandsKey, Townsperson.SaveString());
            PlayerPrefs.Save();
        }

        /// <summary>
        /// Server, host only, at HQ: wipe the case book, errands, favours and costume pieces and start
        /// Hollow Creek over. The HUD asks twice first.
        /// </summary>
        public void HandleStartOver(PlayerAgent agent)
        {
            if (!InTown || Phase.Value != MatchPhase.Setup || agent.OwnerClientId != NetworkManager.ServerClientId) return;
            SolvedCases.Clear();
            Favours.Value = 0;
            WatchPieces.Value = 0;
            WearingWatch.Value = false;
            foreach (var t in Townsperson.All) t.ServerReset();
            PlayerPrefs.DeleteKey(CaseBookKey);
            PlayerPrefs.DeleteKey(FavoursKey);
            PlayerPrefs.DeleteKey(WatchKey);
            PlayerPrefs.DeleteKey(WearingKey);
            PlayerPrefs.DeleteKey(ErrandsKey);
            PlayerPrefs.Save();
            Announce("A fresh start: the case book is empty, the errands are undone and the trunk at HQ is bare. Hollow Creek is waiting.");
        }

        /// <summary>Server: play a particle effect on every machine.</summary>
        public void PlayFx(SpookyFxKind kind, Vector3 at) => PlayFxRpc(kind, at);

        [Rpc(SendTo.ClientsAndHost)]
        void PlayFxRpc(SpookyFxKind kind, Vector3 at) => SpookyFX.Play(kind, at);

        [Rpc(SendTo.ClientsAndHost)]
        void AnnounceRpc(FixedString512Bytes message) => GameHUD.Toast(message.ToString());

        // -------------------------------------------------------------------
        // Players and pawns (server)
        // -------------------------------------------------------------------

        public void OnPlayerJoined(PlayerAgent agent)
        {
            if (agent.Pawn != null) return;

            if (agent.Side.Value == PlayerSide.Haunter && HaunterAgent != agent)
                agent.Side.Value = PlayerSide.Solver;

            SpawnPawn(agent);
            if (agent.Side.Value == PlayerSide.Haunter && Mystery.CulpritLocked)
                agent.SendSecretIdentity(Mystery.CulpritId);
        }

        public void OnPlayerLeft(PlayerAgent agent)
        {
            if (MysteryVan.Instance != null) MysteryVan.Instance.ServerRemove(agent.OwnerClientId);
            if (agent.Pawn != null && agent.Pawn.IsSpawned) agent.Pawn.Despawn(true);
            // TODO(AI milestone): hand the Haunter to the AI Director if the Haunter player leaves.
            CheckAllSolversScaredOut();
        }

        void SpawnPawn(PlayerAgent agent)
        {
            bool haunter = agent.Side.Value == PlayerSide.Haunter;
            var prefab = haunter ? HaunterPrefab : SolverPrefab;
            var spawn = PickSpawn(haunter);
            var go = Instantiate(prefab, spawn.position, spawn.rotation);
            var netObj = go.GetComponent<NetworkObject>();

            if (haunter)
            {
                // Spectral form is invisible on the wire: only the Haunter's own machine gets this object.
                var controller = go.GetComponent<HaunterController>();
                ulong owner = agent.OwnerClientId;
                netObj.CheckObjectVisibility = clientId => clientId == owner || controller.IsPhysical;
            }

            netObj.SpawnWithOwnership(agent.OwnerClientId, true);
            agent.Pawn = netObj;
        }

        Transform PickSpawn(bool haunter)
        {
            var points = FindObjectsByType<SpawnPoint>(FindObjectsSortMode.None);
            if (InTown)
            {
                // Before the call everyone is at HQ; after it, at tonight's house.
                var site = ActiveSite != null && Phase.Value >= MatchPhase.Dispatch ? ActiveSite : TownDirector.Instance.HQ;
                var here = points.Where(p => HouseSite.Of(p) == site).ToArray();
                var preferredHere = here.Where(p => p.HaunterSpawn == haunter).ToArray();
                if (preferredHere.Length > 0) here = preferredHere;
                if (here.Length > 0) points = here;
            }
            var preferred = points.Where(p => p.HaunterSpawn == haunter).ToArray();
            var pool = preferred.Length > 0 ? preferred : points;
            return pool.Length > 0 ? pool[Random.Range(0, pool.Length)].transform : transform;
        }

        void Respawn(PlayerAgent agent)
        {
            if (agent.Pawn != null && agent.Pawn.IsSpawned) agent.Pawn.Despawn(true);
            agent.Pawn = null;
            SpawnPawn(agent);
        }

        // -------------------------------------------------------------------
        // Requests (server, already rate-limited and owner-checked by PlayerAgent)
        // -------------------------------------------------------------------

        public void HandleSideRequest(PlayerAgent agent, PlayerSide side)
        {
            if (agent.Side.Value == side) return;
            if (Phase.Value > MatchPhase.Setup) { agent.Tell("Sides can only change before the investigation starts."); return; }
            if (side == PlayerSide.Haunter && HaunterAgent != null) { agent.Tell("Someone is already the Haunter."); return; }

            if (agent.Side.Value == PlayerSide.Haunter)
                Mystery.SetCulpritChoice(null); // leaving the role forgets the pick

            agent.Side.Value = side;
            Respawn(agent);
        }

        public void HandleIdentityChoice(PlayerAgent agent, string suspectId)
        {
            if (agent.Side.Value != PlayerSide.Haunter) return;
            if (Phase.Value != MatchPhase.Setup || Mystery.CulpritLocked) { agent.Tell("Your identity is already locked in."); return; }
            if (Mystery.SetCulpritChoice(suspectId))
                agent.SendSecretIdentity(suspectId); // only the Haunter's machine hears about it
        }

        public void HandleVillainChoice(PlayerAgent agent, VillainKind villain)
        {
            if (agent.Side.Value != PlayerSide.Haunter) return;
            if (Phase.Value > MatchPhase.Setup) { agent.Tell("The legend is set for tonight."); return; }
            Villain.Value = villain;
        }

        /// <summary>Hollow Creek: a Solver picked tonight's call on the HQ call board.</summary>
        public void HandleCallChoice(PlayerAgent agent, string houseId)
        {
            if (!InTown || agent.Side.Value != PlayerSide.Solver) return;
            if (Phase.Value > MatchPhase.Setup) { agent.Tell("The van has already left for tonight's call."); return; }
            var site = TownDirector.Instance.Find(houseId);
            if (site == null || site.IsHQ) return;
            if (!IsUnlocked(site.HouseId)) { agent.Tell("Nobody's called from there yet. Solve the other four cases first."); return; }
            ActiveHouse.Value = site.HouseId;
            LoadCaseFor(site.HouseId);
            Announce($"Tonight's call: {site.DisplayName}, {Mystery.Case.CaseName}. The van leaves when setup ends.");
        }

        /// <summary>Hollow Creek, host only: the case is over, so everyone heads back to HQ for another night.</summary>
        public void HandleNextNight(PlayerAgent agent)
        {
            if (!InTown || Phase.Value != MatchPhase.Ended || agent.OwnerClientId != NetworkManager.ServerClientId) return;
            StartNextNight();
        }

        /// <summary>
        /// Server: a soft reset without reloading the scene. Every house goes back to how it was,
        /// tonight's clues and notes are cleared, the van is back in the HQ driveway and every pawn is
        /// spawned fresh at HQ (so fear, batteries and ectoplasm start full). The case book stays.
        /// </summary>
        void StartNextNight()
        {
            foreach (var clue in FindObjectsByType<ClueItem>(FindObjectsSortMode.None))
                if (clue.IsSpawned) clue.NetworkObject.Despawn(true);
            foreach (var b in FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None))
                if (b is INewNight n && !(b is PlayerAgent)) n.ServerNewNight();

            Mystery = new MysteryServer(this, Case);
            PublishCase();
            Clues.Clear();
            Interviews.Clear();
            ClearedSuspects.Clear();
            RevealedCulprit.Value = default;
            ActiveHouse.Value = default;
            ActiveCase.Value = default;
            Event.Value = NightEvent.None;
            NightStart.Value = 0;
            NightLength.Value = 0;
            Winner.Value = default;
            EndReason.Value = default;

            foreach (var agent in PlayerAgent.All.ToList())
            {
                agent.ServerNewNight();
                Respawn(agent);
            }

            BeginSetup();
            Announce(SolvedCases.Count >= Cases.All.Length
                ? "Back at HQ. Every case is in the book, but the phone is ringing again..."
                : $"Back at HQ. {SolvedCases.Count} of {Cases.All.Length} cases in the book. Who calls tonight?");
        }

        /// <summary>Hollow Creek: the host can skip the wait at HQ.</summary>
        public void HandleLeaveNow(PlayerAgent agent)
        {
            if (!InTown || Phase.Value != MatchPhase.Setup || agent.OwnerClientId != NetworkManager.ServerClientId) return;
            PhaseEndTime.Value = Now + 3.0;
        }

        public void HandleAccusation(PlayerAgent agent, string suspectId)
        {
            if (agent.Side.Value != PlayerSide.Solver || agent.ScaredOut.Value || Phase.Value != MatchPhase.Investigation) return;

            if (Clues.Count < CluesRequiredToAccuse.Value)
            {
                agent.Tell($"You need at least {CluesRequiredToAccuse.Value} clues before you can accuse anyone.");
                return;
            }
            if (!Mystery.IsValidSuspect(suspectId) || IsCleared(suspectId)) return;
            if (Time.time - agent.LastAccusationTime < AccusationCooldown) return;
            agent.LastAccusationTime = Time.time;

            if (Mystery.IsCulprit(suspectId))
            {
                BeginTrap();
                return;
            }

            // Wrong! The accused is proven innocent and the Haunter gets a big Ectoplasm boost.
            ClearedSuspects.Add(suspectId);
            Announce($"{SuspectName(suspectId)} is innocent! The Haunter cackles and grows stronger...");
            var haunter = HaunterPawn;
            if (haunter != null) haunter.Ectoplasm.Add(Mystery.Case.WrongAccusationEctoplasmBonus);

            AccusationsLeft.Value = Mathf.Max(0, AccusationsLeft.Value - 1);
            if (AccusationsLeft.Value <= 0) EndMatch(MatchWinner.Haunter, MatchEndReason.WrongAccusations);
        }

        /// <summary>
        /// A Solver searched the room a suspect's alibi names. Innocents' alibis hold up; the
        /// culprit's falls apart, unless the Haunter got there first and faked it.
        /// </summary>
        public void HandleAlibiCheck(PlayerAgent agent, string suspectId)
        {
            if (agent.Side.Value != PlayerSide.Solver || agent.ScaredOut.Value || Phase.Value != MatchPhase.Investigation) return;
            if (!Mystery.IsValidSuspect(suspectId) || AlibiStatus(suspectId) != 0) return;
            if (AlibiChecksLeft.Value <= 0) { agent.Tell("No alibi checks left tonight."); return; }
            string room = AlibiRoomOf(suspectId);
            if (string.IsNullOrEmpty(room)) { agent.Tell("There's nowhere to check that alibi."); return; }
            var pawn = SolverController.All.FirstOrDefault(s => s != null && s.OwnerClientId == agent.OwnerClientId);
            if (pawn == null || ManorLayout.RoomNameAt(pawn.transform.position) != room)
            {
                agent.Tell($"To check {SuspectName(suspectId)}'s alibi, search the {room}.");
                return;
            }

            AlibiChecksLeft.Value--;
            if (Mystery.AlibiHolds(suspectId))
            {
                AlibisHold.Add(suspectId);
                PlayFx(SpookyFxKind.AlibiHolds, pawn.transform.position);
                Announce($"{SuspectName(suspectId)}'s alibi holds up: someone really was in the {room}.");
            }
            else
            {
                AlibisBroken.Add(suspectId);
                PlayFx(SpookyFxKind.AlibiBroken, pawn.transform.position);
                Announce($"{SuspectName(suspectId)}'s alibi falls apart: nobody's been in the {room} all night!");
            }
        }

        public void HandleBoardMark(PlayerAgent agent, string suspectId, bool cleared)
        {
            if (agent.Side.Value != PlayerSide.Solver || !Mystery.IsValidSuspect(suspectId)) return;
            if (cleared && !IsCleared(suspectId)) ClearedSuspects.Add(suspectId);
            if (!cleared) ClearedSuspects.Remove(suspectId);
        }

        public void PublishClue(DiscoveredClue clue)
        {
            Clues.Add(clue);
            PlayFx(SpookyFxKind.ClueFound, clue.Location);
            string where = ManorLayout.Describe(clue.Location);
            Announce(string.IsNullOrEmpty(where) ? $"Clue found: {clue.Name}" : $"Clue found in the {where}: {clue.Name}");
        }

        public void PublishInterview(InterviewNote note) => Interviews.Add(note);

        // -------------------------------------------------------------------
        // Fear and traps (server)
        // -------------------------------------------------------------------

        public void NotifySolverPanicked(SolverController solver)
        {
            var agent = PlayerAgent.ForClient(solver.OwnerClientId);
            if (agent == null || agent.ScaredOut.Value || (Phase.Value != MatchPhase.Investigation && Phase.Value != MatchPhase.Trap)) return;

            agent.PanicCount.Value++;
            if (MaxPanicsBeforeScaredOut > 0 && agent.PanicCount.Value >= MaxPanicsBeforeScaredOut)
            {
                agent.ScaredOut.Value = true;
                StartCoroutine(ScareOut(agent));
            }
        }

        System.Collections.IEnumerator ScareOut(PlayerAgent agent)
        {
            yield return new WaitForSeconds(ScaredOutDelay); // let the comedic flee play first
            if (agent != null && agent.Pawn != null && agent.Pawn.IsSpawned)
            {
                if (MysteryVan.Instance != null) MysteryVan.Instance.ServerRemove(agent.OwnerClientId);
                agent.Pawn.Despawn(true);
                agent.Pawn = null;
            }
            Announce(InTown ? "A Solver ran screaming all the way back to HQ!" : "A Solver ran screaming out of the house!");
            CheckAllSolversScaredOut();
        }

        void CheckAllSolversScaredOut()
        {
            if (Phase.Value != MatchPhase.Investigation && Phase.Value != MatchPhase.Trap) return;
            var solvers = PlayerAgent.All.Where(a => a.Side.Value == PlayerSide.Solver).ToList();
            if (solvers.Count > 0 && solvers.All(a => a.ScaredOut.Value))
                EndMatch(MatchWinner.Haunter, MatchEndReason.SolversScaredOut);
        }

        /// <summary>A trap was sprung. True (and the unmasking starts) if the Haunter was caught.</summary>
        public bool TryCatchHaunter(TrapSite trap)
        {
            if (trap == null || Phase.Value != MatchPhase.Trap) return false;

            if (HaunterAgent == null)
            {
                // Nobody is playing the Haunter: an armed trap catches the AI stand-in.
                BeginUnmasking(trap.transform.position);
                return true;
            }

            var haunter = HaunterPawn;
            if (haunter == null || !haunter.IsPhysical || Vector3.Distance(haunter.transform.position, trap.transform.position) > trap.CatchRadius)
                return false;

            BeginUnmasking(haunter.transform.position);
            return true;
        }

        /// <summary>A trap finished building. With no Haunter player, the AI stand-in walks right into it.</summary>
        public void NotifyTrapArmed(TrapSite trap)
        {
            // TODO(AI milestone): the AI Director should try to dodge the trap like a player would.
            if (HaunterAgent == null) StartCoroutine(AutoCatch(trap));
        }

        System.Collections.IEnumerator AutoCatch(TrapSite trap)
        {
            yield return new WaitForSeconds(2.5f);
            TryCatchHaunter(trap);
        }
    }
}
