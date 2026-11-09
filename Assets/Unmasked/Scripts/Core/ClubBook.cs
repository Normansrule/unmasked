using System;
using System.Collections.Generic;
using System.Linq;
using Unity.Netcode;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// The Club Book: what you have done in Hollow Creek, kept on this computer. Candy is earned by
    /// playing (a night, a solved case, the clues you found, errands, lost lanterns, challenges) and
    /// spent in the Wardrobe on looks for your Solver. There is nothing to buy with money, no
    /// premium currency and no prize draws; every look has a price in candy and a name.
    ///
    /// The challenges are a finite book in chapters, not a daily list: they never expire, nothing
    /// is lost for taking a week off, and after three nights in one sitting the book suggests a
    /// good place to stop (it can be told not to).
    ///
    /// Local only. It watches the match from this machine's point of view (phase changes, the
    /// result, your pawn's position in town) and never asks the server for anything except to show
    /// your look to everyone (<see cref="PlayerAgent.SetLookRpc"/>). The page is drawn by
    /// ClubBookPage.cs (K).
    /// </summary>
    public partial class ClubBook : MonoBehaviour
    {
        public const string SaveKey = "Unmasked.ClubBook";
        public static ClubBook Instance { get; private set; }

        // ---- What's saved ---------------------------------------------------------------------

        [Serializable] class Stat { public string k; public int v; }

        [Serializable]
        class Data
        {
            public int candy, earned;
            public List<Stat> stats = new();
            /// <summary>Things that happened once: "lantern:L03", "place:Mill Pond", "case:PembertonCottage", "done:first-clue".</summary>
            public List<string> marks = new();
            public List<string> owned = new();
            public string hat = "", back = "", beam = "";
            public bool breakReminder = true;
            /// <summary>Trick-or-treat: the night (DoorNight) the list below is for, and the doors that gave a treat that night.</summary>
            public int treatNight = -1;
            public List<string> treated = new();
            /// <summary>Jack-o'-lanterns carved at HQ ("eyes,nose,mouth"), oldest first, at most CarvingBench.PorchSize; and the night of the last one.</summary>
            public List<string> carvings = new();
            public int carveNight = -1;
        }

        static Data data;
        static Data D
        {
            get
            {
                if (data != null) return data;
                try { data = JsonUtility.FromJson<Data>(PlayerPrefs.GetString(SaveKey, "")); } catch (ArgumentException) { data = null; }
                data ??= new Data();
                return data;
            }
        }

        static void Save()
        {
            PlayerPrefs.SetString(SaveKey, JsonUtility.ToJson(D));
            PlayerPrefs.Save();
        }

        /// <summary>Start over: forget everything in the Club Book on this computer.</summary>
        public static void Wipe()
        {
            data = new Data();
            PlayerPrefs.DeleteKey(SaveKey);
        }

        public static int Candy => D.candy;
        public static int CandyEarned => D.earned;
        public static bool BreakReminder { get => D.breakReminder; set { D.breakReminder = value; Save(); } }

        public static int Get(string stat) => D.stats.FirstOrDefault(s => s.k == stat)?.v ?? 0;

        static void Add(string stat, int n = 1)
        {
            if (n == 0) return;
            var s = D.stats.FirstOrDefault(x => x.k == stat);
            if (s == null) D.stats.Add(s = new Stat { k = stat });
            s.v += n;
        }

        public static bool Has(string mark) => D.marks.Contains(mark);
        public static int CountMarks(string prefix) => D.marks.Count(m => m.StartsWith(prefix, StringComparison.Ordinal));

        /// <summary>True the first time.</summary>
        static bool Mark(string mark)
        {
            if (D.marks.Contains(mark)) return false;
            D.marks.Add(mark);
            return true;
        }

        /// <summary>Candy earned tonight, line by line, for the card at the end of the night.</summary>
        public static readonly List<(string what, int candy)> Tonight = new();

        static void Earn(int amount, string why)
        {
            if (amount <= 0) return;
            D.candy += amount;
            D.earned += amount;
            Tonight.Add((why, amount));
        }

        // ---- Challenges ---------------------------------------------------------------------------

        public class Challenge
        {
            public string Id, Title, Text;
            public int Goal = 1, Reward;
            public Func<int> Count;
            /// <summary>Set when the challenge is about one house: the page shows a Play button for its call.</summary>
            public string House;
            public bool Done => Has("done:" + Id);
            public int Progress => Mathf.Min(Goal, Count());
        }

        public class Chapter
        {
            public string Name, Blurb;
            public Challenge[] Items;
        }

        static Challenge C(string id, string title, string text, int goal, int reward, Func<int> count, string house = null) =>
            new() { Id = id, Title = title, Text = text, Goal = goal, Reward = reward, Count = count, House = house };

        static int Solved(string house) => Has("house:" + house) ? 1 : 0;

        public static readonly Chapter[] Chapters =
        {
            new() { Name = "New member", Blurb = "Your first nights with the Mystery Club.", Items = new[]
            {
                C("first-night", "Clock in", "Play a night, on either side.", 1, 20, () => Get("nights")),
                C("first-clue", "Something glints", "Find a clue with your flashlight.", 1, 20, () => Get("clues")),
                C("first-alibi", "Where were you?", "Check a suspect's alibi during a case.", 1, 25, () => Get("alibis")),
                C("first-solve", "Case closed", "Solve a case as a Solver.", 1, 40, () => Get("solves")),
                C("first-lantern", "A light in the grass", "Find one of the lost lanterns around town.", 1, 25, () => Get("lanterns")),
                C("first-errand", "Good neighbour", "Finish an errand for one of the townsfolk.", 1, 25, () => Get("errands")),
            }},
            new() { Name = "House calls", Blurb = "One case at every house in town. Press Play to make it tonight's call.", Items = new[]
            {
                C("solve-cottage", "Pemberton Cottage", "Solve the case at 14 Elm Street.", 1, 40, () => Solved("PembertonCottage"), "PembertonCottage"),
                C("solve-farm", "Hollow Creek Farm", "Solve the case out on Old Mill Road.", 1, 50, () => Solved("HollowCreekFarm"), "HollowCreekFarm"),
                C("solve-victorian", "Willow Lane Victorian", "Solve the case at 3 Willow Lane.", 1, 60, () => Solved("WillowLaneVictorian"), "WillowLaneVictorian"),
                C("solve-manor", "Blackwood Manor", "Solve the case past the creek: the longest night.", 1, 80, () => Solved("BlackwoodManor"), "BlackwoodManor"),
                C("solve-society", "The Historical Society", "Solve the last case, once the other four are done.", 1, 120, () => Solved("HistoricalSociety"), "HistoricalSociety"),
            }},
            new() { Name = "Around town", Blurb = "Hollow Creek is bigger than it looks. Walk it.", Items = new[]
            {
                C("streets", "Know the streets", "Walk down eight different streets.", 8, 30, () => CountMarks("street:")),
                C("districts", "Every corner", "Set foot in every part of town, North Bank too.", 9, 40, () => CountMarks("district:")),
                C("places", "Sights of Hollow Creek", "Visit all eight landmarks: the maze, the cemetery, the pond and the rest.", 8, 60, () => CountMarks("place:")),
                C("snap-1", "Say cheese", "Take a snapshot of one of the album's sights with the club camera (P).", 1, 15, () => CountMarks("snap:")),
                C("snap-all", "The whole album", "Fill every frame in the Snapshots album.", Snapshots.SightCount, 80, () => CountMarks("snap:")),
                C("maze", "The heart of the maze", "Reach the scarecrow in the middle of Hatcher's Corn Maze.", 1, 40, () => Has("mazeheart") ? 1 : 0),
                C("lanterns-6", "Lamplighter", "Find six lost lanterns.", 6, 50, () => Get("lanterns")),
                C("creek-lamps", "Lamplighter's apprentice", "Light all twelve gas lamps on the Creekside Path with Tobias Wick's pole.", Lamplighter.Lamps, 40, () => CreekLampsLit),
                C("wisp-1", "Follow the light", "Follow a will-o'-the-wisp from the creek to where it goes out.", 1, 30, () => Get("wisps")),
                C("hook-1", "Back on its hook", "Hang a lost lantern on its family's hook at the Historical Society.", 1, 25, () => HooksFilled),
                C("errands-5", "Pillar of the community", "Finish every errand the townsfolk give you.", 5, 60, () => Get("errands")),
            }},
            new() { Name = "Past the edge of town", Blurb = "Six haunted places round Hollow Creek, and curiosities hidden all over. Drive out and look closely.", Items = new[]
            {
                C("region-1", "Off the map", "Drive out of town to one of the haunted places: the castle, the circus, the tower, the harbor, the beach or the swamp.", 1, 20, () => RegionsVisited),
                C("regions-all", "The grand tour", "Visit all six haunted places past the edge of town.", WorldLife.Places, 80, () => RegionsVisited),
                C("curio-1", "Now what's this?", "Find one of the curiosities hidden round the world and read its story.", 1, 15, () => CuriosFound),
                C("curio-10", "Cabinet of curiosities", "Find ten curiosities.", 10, 50, () => CuriosFound),
                C("curio-all", "Explorer of Hollow Creek", "Find every curiosity, from the castle's helmet to the gnome in town.", Curio.Total, 150, () => CuriosFound),
                C("lighthouse", "Keeper of the light", "Climb Saltmarsh Lighthouse and step out on the gallery.", 1, 30, () => Has("climb:lighthouse") ? 1 : 0),
                C("tower-roof", "Top floor", "Climb the fire escape all the way to the roof of Gloamwood Tower.", 1, 30, () => Has("climb:tower") ? 1 : 0),
            }},
            new() { Name = "Casework", Blurb = "Solving it is one thing. Solving it well is another.", Items = new[]
            {
                C("clues-25", "Magnifying glass", "Find 25 clues across your nights.", 25, 50, () => Get("clues")),
                C("clean", "First try", "Solve a case without a wrong accusation.", 1, 40, () => Get("cleanSolves")),
                C("fast", "Home before midnight", "Solve a case with three minutes or more left on the clock.", 1, 50, () => Get("fastSolves")),
                C("roles", "Every hat in the club", "Win a case as each role: Sleuth, Techie, Brawn and Snacker.", 4, 80, () => CountMarks("role:")),
                C("event", "Whatever the weather", "Solve a case on a night with a special event.", 1, 40, () => CountMarks("eventsolve:")),
                C("brave", "Steady nerves", "Finish five nights as a Solver without getting scared out.", 5, 50, () => Get("braveNights")),
            }},
            new() { Name = "The other side", Blurb = "Somebody has to wear the mask.", Items = new[]
            {
                C("haunt-1", "Boo", "Play a night as the Haunter.", 1, 25, () => Get("haunterNights")),
                C("haunt-win", "Nobody saw a thing", "Win a night as the Haunter.", 1, 50, () => Get("haunterWins")),
                C("haunt-scare", "Full house", "As the Haunter, scare out two Solvers in one night and win.", 1, 60, () => Get("bigScares")),
                C("haunt-legends", "Every legend", "Wear all four legends: Horseman, Banshee, Stingy Jack and Baba Yaga.", 4, 80, () => CountMarks("villain:")),
                C("haunt-escape", "Not today", "Escape the Solvers' trap and get away.", 1, 60, () => Get("escapes")),
            }},
            new() { Name = "Trick or treat", Blurb = "Knock where the porch light is on. Each door gives one treat a night, and some families have a story.", Items = new[]
            {
                C("knock-1", "Knock knock", "Trick-or-treat at a door with its porch light on.", 1, 15, () => Get("treats")),
                C("bag-10", "A full bag", "Get treats from ten different doors in one night.", 10, 40, () => Get("bestTreats")),
                C("street-all", "The whole street", "Get a treat at every door on one of the longer streets, like Chapel Lane or Pine Street (any number of nights).", 1, 40, StreetsDone),
                C("doors-all", "Every door in town", "Get a treat at all 35 doors on the new streets.", 35, 100, () => CountMarks("door:")),
                C("carve-1", "Jack of all trades", "Carve a jack-o'-lantern at the bench outside HQ.", 1, 20, () => Get("carvings")),
                C("carve-6", "A porch full of faces", "Carve six jack-o'-lanterns, one a night, and fill the HQ porch.", CarvingBench.PorchSize, 50, () => Get("carvings")),
                C("tales-3", "Story time", "Hear three of the Stories of Hollow Creek.", 3, 30, () => CountMarks("tale:")),
                C("tales-all", "The whole story", "Hear all twelve Stories of Hollow Creek.", Tales.All.Length, 120, () => CountMarks("tale:")),
            }},
            new() { Name = "Legend of Hollow Creek", Blurb = "The long haul. Take your time: none of this expires.", Items = new[]
            {
                C("all-cases", "The whole case book", "Solve every case, return visits included.", Cases.All.Length, 150, () => CountMarks("case:")),
                C("all-lanterns", "Every light in town", "Find all of the lost lanterns.", 24, 150, () => Get("lanterns")),
                C("hooks-all", "The new Lantern Watch", "Hang all twenty-four lanterns on the Hook Board, and the mist stays down on the creek.", HookBoard.Hooks, 150, () => HooksFilled),
                C("unmask-all", "Unmasked", "Catch each of the four legends as a Solver.", 4, 100, () => CountMarks("legend:")),
                C("watch", "On the Watch", "Solve a case wearing the Lantern Watch costume.", 1, 60, () => Has("watch:solve") ? 1 : 0),
                C("nights-25", "Regular", "Play 25 nights.", 25, 100, () => Get("nights")),
                C("events-all", "Seen it all", "Play a night under each of the five special events.", 5, 80, () => CountMarks("event:")),
            }},
        };

        public static IEnumerable<Challenge> AllChallenges => Chapters.SelectMany(c => c.Items);
        public static int ChallengesDone => AllChallenges.Count(c => c.Done);
        public static int ChallengeCount => AllChallenges.Count();

        /// <summary>Challenges finished just now: shown in the end-of-night card.</summary>
        public static readonly List<Challenge> JustDone = new();

        static void CheckChallenges()
        {
            bool changed = false;
            foreach (var c in AllChallenges)
            {
                if (c.Done || c.Count() < c.Goal) continue;
                Mark("done:" + c.Id);
                Earn(c.Reward, "Challenge: " + c.Title);
                JustDone.Add(c);
                GameHUD.Toast($"Challenge done: {c.Title}. +{c.Reward} candy (K opens the Club Book).");
                Sfx.Play2D("clue_chime", 0.6f, 1.25f);
                changed = true;
            }
            if (changed) Save();
        }

        // ---- The Wardrobe ---------------------------------------------------------------------------

        public class Item
        {
            public string Id, Name, Slot, Blurb;
            public int Price;
            /// <summary>Given in play, never sold (the lamplighter's cap): the Wardrobe says how to earn it.</summary>
            public string GiftFrom;
            public Color A, B;
        }

        static Item W(string id, string name, string slot, int price, string a, string b, string blurb) => new()
        {
            Id = id, Name = name, Slot = slot, Price = price, Blurb = blurb,
            A = ColorUtility.TryParseHtmlString("#" + a, out var ca) ? ca : Color.white,
            B = ColorUtility.TryParseHtmlString("#" + b, out var cb) ? cb : Color.white,
        };

        /// <summary>Every look in the Wardrobe. Only ever add to the end: the order is what goes over the network.</summary>
        public static readonly Item[] Wardrobe =
        {
            W("cat-ears", "Cat ears", "hat", 60, "222026", "f0a0b0", "Two felt ears on a band. Midnight approves."),
            W("leaf-crown", "Crown of leaves", "hat", 80, "c04a2a", "d8a03a", "Maple and oak from Applegate Orchard."),
            W("top-hat", "Top hat", "hat", 100, "1a1820", "e8731c", "Tall, black, an orange band. Very Mortimer Vane."),
            W("tricorn", "Tricorn", "hat", 110, "3a2a22", "e8d8a8", "A pirate's hat from the Harvest Festival's lost and found."),
            W("witch-hat", "Witch hat", "hat", 120, "2a1d3a", "9fe870", "Pointed, with a green band and a crumpled tip."),
            W("antlers", "Antlers", "hat", 120, "8a6a4a", "e8dcc8", "From the costume trunk at the back of the Fire Station."),
            W("halo", "Ghostly halo", "hat", 140, "fff0c8", "fff0c8", "A ring of soft light. Nobody knows who left it."),
            W("wizard-hat", "Wizard hat", "hat", 160, "2a3a8a", "ffe08a", "Deep blue with stars that catch the lamplight."),
            W("pumpkin-head", "Pumpkin head", "hat", 220, "e8731c", "ffcf5a", "A whole carved pumpkin, candle and all."),
            W("cape", "Vampire cape", "back", 150, "1a1218", "a01c24", "Black outside, red inside, and a collar that stands up."),
            W("bat-wings", "Bat wings", "back", 180, "1c1a22", "6a2a8a", "They don't flap. They do look great."),
            W("lantern-pack", "Lantern pack", "back", 90, "6a4a2a", "ffcf7a", "A satchel with a lantern clipped on, for the long walks."),
            W("pocket-ghost", "Pocket ghost", "back", 240, "f2efe8", "1a1420", "A little ghost that follows you everywhere. It's shy."),
            W("beam-candle", "Candlelight beam", "beam", 50, "ffbf73", "ffbf73", "Your flashlight burns warm orange."),
            W("beam-moon", "Moonlight beam", "beam", 70, "b3d9ff", "b3d9ff", "A cold blue beam, like the moon on the creek."),
            W("beam-wisp", "Wisp beam", "beam", 70, "9fff9f", "9fff9f", "Green as the lights in the churchyard."),
            W("beam-rose", "Rose beam", "beam", 90, "ffb3c8", "ffb3c8", "Pink. Clues look the same; you look better."),
            W("candy-pail", "Pumpkin pail", "back", 100, "e8731c", "1a1218", "The plastic jack-o'-lantern pail every trick-or-treater carries."),
            W("scarecrow-hat", "Scarecrow hat", "hat", 130, "c8a050", "8a3a2a", "Straw, a patch, and a crow feather. Like the one in the middle of the maze."),
            Gift(W("lamplighter-cap", "Lamplighter's cap", "hat", 0, "3a3a46", "e8c96a", "Tobias Wick's spare flat cap, with the little brass lamp badge."),
                 "Light every gas lamp on the Creekside Path for Tobias Wick, then take him back his pole."),
            Gift(W("explorer-hat", "Explorer's hat", "hat", 0, "8a6a44", "3a2a1e", "A wide-brimmed field hat with a leather band and a little brass compass pinned to it."),
                 "Find every curiosity hidden round the world past the edge of town."),
        };

        static Item Gift(Item item, string how) { item.GiftFrom = how; return item; }

        public static Item FindItem(string id) => Wardrobe.FirstOrDefault(i => i.Id == id);
        public static bool Owns(string id) => D.owned.Contains(id);
        public static bool Wearing(string id) => id == D.hat || id == D.back || id == D.beam;

        /// <summary>Buy with candy you earned. False if you can't afford it yet.</summary>
        public static bool Buy(string id)
        {
            var item = FindItem(id);
            if (item == null || item.GiftFrom != null || Owns(id) || D.candy < item.Price) return false;
            D.candy -= item.Price;
            D.owned.Add(id);
            Mark("bought:" + id);
            Wear(id, true);
            Save();
            return true;
        }

        public static void Wear(string id, bool on)
        {
            var item = FindItem(id);
            if (item == null || !Owns(id)) return;
            string value = on ? id : "";
            if (item.Slot == "hat") D.hat = value;
            else if (item.Slot == "back") D.back = value;
            else D.beam = value;
            Save();
            lookSent = -1; // send it again
        }

        /// <summary>The look as one number: hat, back and beam slots (index + 1 into <see cref="Wardrobe"/>, 0 = none).</summary>
        public static int PackedLook => ClubLook.Pack(Array.FindIndex(Wardrobe, i => i.Id == D.hat), Array.FindIndex(Wardrobe, i => i.Id == D.back),
                                                       Array.FindIndex(Wardrobe, i => i.Id == D.beam));

        // ---- Watching the match ---------------------------------------------------------------------

        class Night
        {
            public PlayerSide Side;
            public SolverRole Role;
            public string Case, House;
            public NightEvent Event;
            public VillainKind Villain;
            public int Accusations;
            public float ClockLeft;
        }

        Night night;
        MatchPhase? lastPhase;
        int errandBaseline = -1;
        float nextCheck;
        static int lookSent = -1;
        static float lookSentAt;
        static PlayerAgent lookAgent;

        /// <summary>Nights finished since the game was started (for the "good place to stop" card).</summary>
        public static int SessionNights { get; private set; }

        void Awake()
        {
            Instance = this;
            if (GetComponent<ClubLook>() == null) gameObject.AddComponent<ClubLook>();
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void Update()
        {
            var keyboard = Keyboard.current;
            if (keyboard != null && keyboard.kKey.wasPressedThisFrame && GUIUtility.keyboardControl == 0) pageOpen = !pageOpen;
            if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame) pageOpen = false;

            var game = MysteryGameManager.Instance;
            var agent = PlayerAgent.Local;
            var net = NetworkManager.Singleton;
            if (game == null || !game.IsSpawned || agent == null || net == null || !net.IsClient)
            {
                lastPhase = null;
                night = null;
                errandBaseline = -1;
                return;
            }

            // Show everyone your look (once per connection, and again when it changes).
            if (lookAgent != agent) { lookAgent = agent; lookSent = -1; }
            if (agent.Look.Value != PackedLook && (lookSent != PackedLook || Time.unscaledTime - lookSentAt > 2f))
            {
                agent.SetLookRpc(PackedLook);
                lookSent = PackedLook;
                lookSentAt = Time.unscaledTime;
            }

            var phase = game.Phase.Value;
            if (lastPhase != phase)
            {
                OnPhase(lastPhase, phase, game, agent);
                lastPhase = phase;
            }
            if (night != null && (phase == MatchPhase.Investigation || phase == MatchPhase.Trap))
            {
                night.ClockLeft = game.PhaseTimeRemaining;
                night.Accusations = Mathf.Max(night.Accusations, game.AccusationsLeft.Value);
            }

            if (game.InTown) Wander(game);
            Errands(game);

            if (Time.unscaledTime > nextCheck)
            {
                nextCheck = Time.unscaledTime + 1f;
                CheckChallenges();
            }
        }

        void OnPhase(MatchPhase? from, MatchPhase to, MysteryGameManager game, PlayerAgent agent)
        {
            if (to == MatchPhase.Investigation && from != MatchPhase.Trap)
            {
                night = new Night
                {
                    Side = agent.Side.Value,
                    Role = agent.Role.Value,
                    Case = game.ActiveCase.Value.ToString(),
                    House = game.ActiveHouse.Value.ToString(),
                    Event = game.Event.Value,
                    Villain = game.Villain.Value,
                    Accusations = game.AccusationsLeft.Value,
                };
                Tonight.Clear();
                JustDone.Clear();
            }
            else if (to == MatchPhase.Ended && night != null)
            {
                FinishNight(game, agent, night);
                night = null;
            }
        }

        static void FinishNight(MysteryGameManager game, PlayerAgent agent, Night n)
        {
            var winner = game.Winner.Value;
            Add("nights");
            SessionNights++;
            Earn(10, "A night's work");
            if (n.Event != NightEvent.None) Mark("event:" + n.Event);
            if (string.IsNullOrEmpty(n.House)) n.House = game.ActiveHouse.Value.ToString();
            if (string.IsNullOrEmpty(n.Case)) n.Case = game.ActiveCase.Value.ToString();

            if (n.Side == PlayerSide.Solver)
            {
                int clues = agent.CluesFound.Value;
                Add("clues", clues);
                Earn(3 * clues, clues == 1 ? "1 clue found" : $"{clues} clues found");
                Add("alibis", game.AlibisHold.Count + game.AlibisBroken.Count);
                if (!agent.ScaredOut.Value) Add("braveNights");
                if (winner == MatchWinner.Solvers)
                {
                    Add("solves");
                    if (!string.IsNullOrEmpty(n.Case)) Mark("case:" + n.Case);
                    if (!string.IsNullOrEmpty(n.House)) Mark("house:" + n.House);
                    Mark("role:" + n.Role);
                    Mark("legend:" + game.Villain.Value);
                    if (n.Event != NightEvent.None) Mark("eventsolve:" + n.Event);
                    if (n.ClockLeft >= 180f) Add("fastSolves");
                    if (game.AccusationsLeft.Value >= n.Accusations) Add("cleanSolves");
                    if (game.WearingWatch.Value && game.WatchPieceCount >= MysteryGameManager.WatchPiecesNeeded) Mark("watch:solve");
                    Earn(30, "Case solved");
                }
            }
            else
            {
                Add("haunterNights");
                Mark("villain:" + game.Villain.Value);
                if (winner == MatchWinner.Haunter)
                {
                    Add("haunterWins");
                    int scared = PlayerAgent.All.Count(a => a.Side.Value == PlayerSide.Solver && a.ScaredOut.Value);
                    if (scared >= 2) Add("bigScares");
                    if (game.EndReason.Value == MatchEndReason.Escaped) Add("escapes");
                    Earn(30, "The Haunter got away with it");
                }
            }
            CheckChallenges();
            Save();
            breakShownFor = -1;
        }

        /// <summary>Streets, districts and landmarks you've been to, from where your Solver is standing.</summary>
        static void Wander(MysteryGameManager game)
        {
            var me = SolverController.Local;
            var town = TownLayout.Current;
            if (me == null || town == null) return;
            var p = me.transform.position;
            var place = town.LandmarkAt(p);
            bool changed = false;
            if (place != null && Mark("place:" + place.n))
            {
                GameHUD.Toast($"New place: {place.n}. ({CountMarks("place:")} of {town.landmarks.Length} landmarks)");
                changed = true;
            }
            if (place != null && place.kind == "maze" && Vector3.Distance(new Vector3(p.x, 0, p.z), place.Center) < 3f && Mark("mazeheart"))
            {
                GameHUD.Toast("You found the middle of the corn maze. The scarecrow doesn't say anything.");
                changed = true;
            }
            string district = town.DistrictAt(p);
            if (district.Length > 0 && Mark("district:" + district)) changed = true;
            var room = town.TownRoomAt(p);
            if (room != null && town.roads != null && Array.IndexOf(town.roads, room.n) >= 0 && Mark("street:" + room.n)) changed = true;
            if (changed) Save();
        }

        void Errands(MysteryGameManager game)
        {
            if (!game.InTown) return;
            int done = Townsperson.ErrandsDone;
            if (errandBaseline < 0) { errandBaseline = done; return; }
            if (done > errandBaseline)
            {
                int n = done - errandBaseline;
                Add("errands", n);
                Earn(10 * n, "Errand run");
                GameHUD.Toast($"+{10 * n} candy for helping out (Club Book: K).");
                Save();
            }
            errandBaseline = done;
        }

        // ---- Trick-or-treat (Doorstep.cs) ---------------------------------------------------------------

        /// <summary>Which night it is for the doors: nights played so far. Who's home changes when it does.</summary>
        public static int DoorNight => Get("nights");

        static void RollTreatNight()
        {
            if (D.treatNight == DoorNight) return;
            D.treatNight = DoorNight;
            D.treated.Clear();
        }

        public static bool TreatedTonight(string homeId)
        {
            RollTreatNight();
            return D.treated.Contains(homeId);
        }

        /// <summary>A door opened for this player. True (and candy) the first time tonight.</summary>
        public static bool Treat(string homeId, string street)
        {
            RollTreatNight();
            if (D.treated.Contains(homeId)) return false;
            D.treated.Add(homeId);
            Add("treats");
            if (D.treated.Count > Get("bestTreats")) Add("bestTreats", D.treated.Count - Get("bestTreats"));
            bool first = Mark("door:" + homeId);
            Earn(first ? 5 : 3, "Trick or treat");
            GameHUD.Toast($"Trick or treat: +{(first ? 5 : 3)} candy ({D.treated.Count} doors tonight).");
            Sfx.Play2D("clue_chime", 0.45f, 1.7f);
            Save();
            return true;
        }

        public static bool HeardTale(int tale) => Has("tale:" + tale);

        /// <summary>A story was told for the first time: true, and it goes in the Club Book.</summary>
        public static bool HearTale(int tale)
        {
            if (!Mark("tale:" + tale)) return false;
            Earn(10, "A story of Hollow Creek");
            Save();
            return true;
        }

        /// <summary>1 once every door on a street of five houses or more has given you a treat.</summary>
        static int StreetsDone()
        {
            var homes = TownLayout.Current?.homes;
            if (homes == null) return Has("streetdone") ? 1 : 0;
            foreach (var g in homes.GroupBy(h => h.street).Where(g => g.Count() >= 5))
                if (g.All(h => Has("door:" + h.id))) { Mark("streetdone"); return 1; }
            return Has("streetdone") ? 1 : 0;
        }

        /// <summary>A photo of an album sight was taken (Snapshots.cs): +5 candy the first time for each.</summary>
        public static void Snapped(string id, string name)
        {
            bool first = Mark("snap:" + id);
            if (first) Earn(5, "A snapshot for the album");
            GameHUD.Toast(first ? $"Snapshot: {name}. A new photo for the album, +5 candy." : $"Snapshot: {name}. The album has the new one.");
            Save();
        }

        /// <summary>The jack-o'-lanterns on the HQ porch, oldest first.</summary>
        public static IReadOnlyList<string> Carvings => D.carvings ??= new List<string>();
        public static string LastCarving => Carvings.Count > 0 ? Carvings[Carvings.Count - 1] : null;
        public static bool CanCarveTonight => D.carveNight != DoorNight;

        /// <summary>Carve one (once a night): it goes on the porch, the oldest comes off past six.</summary>
        public static void Carve(string code)
        {
            if (!CanCarveTonight) return;
            D.carveNight = DoorNight;
            D.carvings ??= new List<string>();
            D.carvings.Add(code);
            while (D.carvings.Count > CarvingBench.PorchSize) D.carvings.RemoveAt(0);
            Add("carvings");
            Earn(10, "Carved a jack-o'-lantern");
            GameHUD.Toast("Carved! It's on the porch now. +10 candy.");
            Save();
        }

        /// <summary>A will-o'-the-wisp led you somewhere and went out (Wisp.cs).</summary>
        public static void FollowedWisp()
        {
            Add("wisps");
            if (Get("wisps") == 1) Earn(10, "Followed a will-o'-the-wisp");
            Save();
        }

        // ---- The lamplighter (Lamplighter.cs) -------------------------------------------------------

        public static bool CreekLampLit(int lamp) => Has("creeklamp:" + lamp);
        public static int CreekLampsLit => CountMarks("creeklamp:");

        public static void MetLamplighter()
        {
            if (Mark("lamplighter:met")) Save();
        }

        /// <summary>A creekside gas lamp lit with Tobias's pole: +5 candy, and it stays lit.</summary>
        public static void LitCreekLamp(int lamp)
        {
            if (!Mark("creeklamp:" + lamp)) return;
            Earn(5, "Lit a creekside lamp");
            GameHUD.Toast($"Creekside lamp lit ({CreekLampsLit} of {Lamplighter.Lamps}). +5 candy.");
            Save();
        }

        /// <summary>The pole goes back with every lamp lit: his spare cap, the first time. True the first time.</summary>
        public static bool ThankLamplighter()
        {
            if (CreekLampsLit < Lamplighter.Lamps || !Mark("lamplighter:thanks")) return false;
            Earn(30, "Lit the whole Creekside Path");
            var cap = FindItem("lamplighter-cap");
            if (cap != null && !Owns(cap.Id))
            {
                D.owned.Add(cap.Id);
                Wear(cap.Id, true);
                GameHUD.Toast("A gift from Tobias: the Lamplighter's cap. You're wearing it now (K, Wardrobe). +30 candy.");
            }
            Save();
            return true;
        }

        /// <summary>How many hooks on the Hook Board have their lantern back (HookBoard.cs).</summary>
        public static int HooksFilled => CountMarks("hook:");

        /// <summary>Lanterns you've found but not yet hung on the Hook Board.</summary>
        public static int LanternsToHang() => D.marks.Count(m => m.StartsWith("lantern:", StringComparison.Ordinal) && !Has("hook:" + m.Substring(8)));

        /// <summary>Hangs every found lantern that isn't on its hook yet: +5 candy each. Returns their ids.</summary>
        public static List<string> HangLanterns()
        {
            var ids = D.marks.Where(m => m.StartsWith("lantern:", StringComparison.Ordinal)).Select(m => m.Substring(8)).OrderBy(id => id, StringComparer.Ordinal).ToList();
            var hung = new List<string>();
            foreach (var id in ids)
                if (Mark("hook:" + id)) hung.Add(id);
            if (hung.Count == 0) return hung;
            Earn(5 * hung.Count, "Lanterns hung on the Hook Board");
            if (HooksFilled >= HookBoard.Hooks && Mark("watch:sworn")) Earn(50, "The new Lantern Watch");
            Save();
            return hung;
        }

        /// <summary>A lost lantern was picked up on this machine (LostLantern.cs).</summary>
        public static void FoundLantern(string id, string where)
        {
            if (!Mark("lantern:" + id)) return;
            Add("lanterns");
            Earn(15, "Lost lantern");
            int total = TownLayout.Current?.collectibles?.Length ?? 0;
            GameHUD.Toast($"Lost lantern found ({Get("lanterns")} of {total}). +15 candy.");
            Sfx.Play2D("clue_chime", 0.7f, 1.5f);
            Save();
        }
    }
}
