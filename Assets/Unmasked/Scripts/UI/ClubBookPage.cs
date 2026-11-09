using System.Linq;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The Club Book page (K): Challenges, the Wardrobe, Lost lanterns and Places. Also the small
    /// card at the end of a night (what you earned) and, after three nights in one sitting, a
    /// friendly "good place to stop". Drawn with <see cref="UITheme"/> like the rest of the HUD.
    /// </summary>
    public partial class ClubBook
    {
        static readonly string[] Tabs = { "Challenges", "Wardrobe", "Stories", "Lost lanterns", "Places", "Snapshots", "Curiosities" };

        bool pageOpen;
        int tab;
        Vector2 scroll;
        static int breakShownFor = -1;
        bool breakDismissed;

        public static bool IsOpen => Instance != null && Instance.pageOpen;
        public static void Open(int whichTab = 0)
        {
            if (Instance == null) return;
            Instance.pageOpen = true;
            Instance.tab = whichTab;
        }

        void OnGUI()
        {
            GUI.depth = pageOpen ? -10 : 0; // the open book sits on top of the HUD and takes the clicks
            UITheme.Begin();
            var game = MysteryGameManager.Instance;
            bool inMatch = game != null && game.IsSpawned && PlayerAgent.Local != null;
            if (inMatch && game.Phase.Value == MatchPhase.Ended && !pageOpen) NightCard(game);
            if (pageOpen) Page(game, inMatch);
        }

        // ---- The end of a night --------------------------------------------------------------------

        void NightCard(MysteryGameManager game)
        {
            if (Tonight.Count == 0 && JustDone.Count == 0) return;
            const float w = 300f;
            float h = 92f + Tonight.Count * 22f + JustDone.Count * 22f;
            bool stop = BreakReminder && SessionNights >= 3 && SessionNights % 3 == 0 && !breakDismissed;
            if (breakShownFor != SessionNights) { breakShownFor = SessionNights; breakDismissed = false; }
            if (stop) h += 128f;
            var r = new Rect(UITheme.Edge, UITheme.H / 2f - h / 2f, w, h);
            UITheme.Rect(new Rect(r.x + 1, r.y + 3, r.width, r.height), UITheme.Shadow);
            UITheme.Rect(r, UITheme.Raised);
            UITheme.Pin(new Vector2(r.center.x, r.y + 2f));
            float y = r.y + 12;
            GUI.Label(new Rect(r.x + 16, y, w - 32, 26), "Club Book", UITheme.Title);
            y += 32;
            foreach (var (what, candy) in Tonight)
            {
                GUI.Label(new Rect(r.x + 16, y, w - 90, 22), what, UITheme.Small);
                GUI.Label(new Rect(r.xMax - 80, y, 64, 22), UITheme.Tint($"+{candy}", UITheme.Good), UITheme.Key);
                y += 22;
            }
            foreach (var c in JustDone)
            {
                GUI.Label(new Rect(r.x + 16, y, w - 32, 22), UITheme.Tint("Done: ", UITheme.Good) + c.Title, UITheme.Small);
                y += 22;
            }
            GUI.Label(new Rect(r.x + 16, y + 4, w - 32, 22), $"{Candy} candy to spend. K opens the book.", UITheme.Small);
            y += 30;
            if (!stop) return;

            // A good place to stop. No penalty for leaving, no timer, nothing lost.
            UITheme.Rect(new Rect(r.x + 16, y, w - 32, 1), UITheme.InkFaint);
            y += 8;
            GUI.Label(new Rect(r.x + 16, y, w - 32, 24), "A good place to stop", UITheme.Strong);
            GUI.Label(new Rect(r.x + 16, y + 24, w - 32, 44),
                      $"That's {SessionNights} nights. Everything is saved, and the next call will wait for you.", UITheme.Small);
            if (GUI.Button(new Rect(r.x + 16, y + 74, 130, 30), "One more night", UITheme.CardButton)) breakDismissed = true;
            if (GUI.Button(new Rect(r.x + 154, y + 74, 130, 30), "Don't remind me", UITheme.CardButton)) BreakReminder = false;
        }

        // ---- The page --------------------------------------------------------------------------------

        void Page(MysteryGameManager game, bool inMatch)
        {
            UITheme.Rect(new Rect(0, 0, UITheme.W, UITheme.H), UITheme.Scrim);
            float pw = Mathf.Min(760f, UITheme.W - 2 * UITheme.S6);
            var page = new Rect(UITheme.W / 2f - pw / 2f, UITheme.S6, pw, UITheme.H - 2 * UITheme.S6);
            GUILayout.BeginArea(page, UITheme.Panel);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Club Book", UITheme.Display);
            GUILayout.FlexibleSpace();
            GUILayout.Label($"{UITheme.Tint(Candy.ToString(), UITheme.Accent)} candy", UITheme.Title);
            GUILayout.EndHorizontal();
            GUILayout.Label($"{ChallengesDone} of {ChallengeCount} challenges · {D.owned.Count} of {Wardrobe.Length} looks · " +
                            $"{Get("lanterns")} of {TownLayout.Current?.collectibles?.Length ?? 0} lanterns · {CountMarks("tale:")} of {Tales.All.Length} stories. Candy is earned by playing; nothing here costs money.",
                            UITheme.MutedWrap);
            GUILayout.Space(UITheme.S2);
            GUILayout.BeginHorizontal();
            for (int i = 0; i < Tabs.Length; i++)
                if (GUILayout.Toggle(tab == i, Tabs[i], GUI.skin.button) && tab != i) { tab = i; scroll = Vector2.zero; }
            GUILayout.EndHorizontal();
            GUILayout.Space(UITheme.S3);

            scroll = GUILayout.BeginScrollView(scroll);
            switch (tab)
            {
                case 0: ChallengesTab(game, inMatch); break;
                case 1: WardrobeTab(); break;
                case 2: StoriesTab(); break;
                case 3: LanternsTab(); break;
                case 4: PlacesTab(); break;
                case 5: SnapshotsTab(); break;
                default: CuriosTab(); break;
            }
            GUILayout.EndScrollView();

            GUILayout.Space(UITheme.S2);
            GUILayout.BeginHorizontal();
            bool remind = GUILayout.Toggle(BreakReminder, " Suggest a break after three nights in a row");
            if (remind != BreakReminder) BreakReminder = remind;
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("Close", UITheme.Primary, GUILayout.Width(120))) pageOpen = false;
            GUILayout.EndHorizontal();
            GUILayout.EndArea();
        }

        void ChallengesTab(MysteryGameManager game, bool inMatch)
        {
            var agent = PlayerAgent.Local;
            bool canPick = inMatch && game.InTown && game.Phase.Value <= MatchPhase.Setup && agent != null && agent.Side.Value == PlayerSide.Solver;
            foreach (var chapter in Chapters)
            {
                int done = chapter.Items.Count(c => c.Done);
                GUILayout.Label($"{chapter.Name}  {UITheme.Tint($"{done}/{chapter.Items.Length}", UITheme.InkFaint)}", UITheme.Title);
                GUILayout.Label(chapter.Blurb, UITheme.Small);
                GUILayout.Space(UITheme.S1);
                foreach (var c in chapter.Items)
                {
                    GUILayout.BeginHorizontal(UITheme.Card);
                    GUILayout.BeginVertical();
                    GUILayout.Label(c.Done ? c.Title + UITheme.Tint("  · done", UITheme.Good) : c.Title, UITheme.Strong);
                    GUILayout.Label(c.Text, UITheme.Small);
                    if (!c.Done && c.Goal > 1)
                    {
                        var bar = GUILayoutUtility.GetRect(200, 8, GUILayout.ExpandWidth(true));
                        UITheme.Meter(new Rect(bar.x, bar.y + 2, bar.width, 6), c.Progress / (float)c.Goal, UITheme.Accent);
                        GUILayout.Label($"{c.Progress} of {c.Goal}", UITheme.Small);
                    }
                    GUILayout.EndVertical();
                    GUILayout.BeginVertical(GUILayout.Width(150));
                    GUILayout.Label(c.Done ? UITheme.Tint("Earned", UITheme.Good) : $"+{c.Reward} candy", UITheme.Key);
                    if (c.House != null && !c.Done)
                    {
                        bool open = canPick && game.IsUnlocked(c.House);
                        bool tonight = inMatch && game.ActiveHouse.Value.ToString() == c.House;
                        GUI.enabled = open && !tonight;
                        if (GUILayout.Button(tonight ? "Tonight's call" : "Play", open && !tonight ? UITheme.Primary : GUI.skin.button, GUILayout.Height(30)))
                        {
                            agent.ChooseCallRpc(c.House);
                            GameHUD.Toast("Tonight's call is picked. Get in the van when you're ready.");
                            pageOpen = false;
                        }
                        GUI.enabled = true;
                        if (!canPick) GUILayout.Label("Pick it at HQ, before a night.", UITheme.Small);
                        else if (!open) GUILayout.Label("Solve the other four first.", UITheme.Small);
                    }
                    GUILayout.EndVertical();
                    GUILayout.EndHorizontal();
                    GUILayout.Space(UITheme.S1);
                }
                GUILayout.Space(UITheme.S3);
            }
        }

        void WardrobeTab()
        {
            GUILayout.Label("Looks for your Solver. Everyone in the game sees what you wear. One hat, one thing on your back and one beam colour at a time.", UITheme.MutedWrap);
            GUILayout.Space(UITheme.S2);
            foreach (var slot in new[] { ("hat", "Hats"), ("back", "On your back"), ("beam", "Flashlight beam") })
            {
                GUILayout.Label(slot.Item2, UITheme.Title);
                foreach (var item in Wardrobe.Where(i => i.Slot == slot.Item1))
                {
                    GUILayout.BeginHorizontal(UITheme.Card);
                    var sw = GUILayoutUtility.GetRect(44, 44, GUILayout.Width(44), GUILayout.Height(44));
                    UITheme.Rect(sw, item.A);
                    UITheme.Rect(new Rect(sw.x, sw.yMax - 12, sw.width, 12), item.B);
                    GUILayout.Space(UITheme.S2);
                    GUILayout.BeginVertical();
                    GUILayout.Label(item.Name, UITheme.Strong);
                    GUILayout.Label(item.Blurb, UITheme.Small);
                    GUILayout.EndVertical();
                    GUILayout.BeginVertical(GUILayout.Width(150));
                    if (Owns(item.Id))
                    {
                        bool wearing = Wearing(item.Id);
                        if (GUILayout.Button(wearing ? "Take off" : "Wear", wearing ? GUI.skin.button : UITheme.Primary, GUILayout.Height(30)))
                            Wear(item.Id, !wearing);
                    }
                    else if (item.GiftFrom != null)
                    {
                        GUILayout.Label(UITheme.Tint("A gift", UITheme.Good), UITheme.Key);
                        GUILayout.Label(item.GiftFrom, UITheme.Small);
                    }
                    else
                    {
                        bool afford = Candy >= item.Price;
                        GUI.enabled = afford;
                        if (GUILayout.Button($"Buy: {item.Price} candy", afford ? UITheme.Primary : GUI.skin.button, GUILayout.Height(30)) && Buy(item.Id))
                            GameHUD.Toast($"{item.Name}: yours. You're wearing it now.");
                        GUI.enabled = true;
                        if (!afford) GUILayout.Label($"{item.Price - Candy} more to go", UITheme.Small);
                    }
                    GUILayout.EndVertical();
                    GUILayout.EndHorizontal();
                    GUILayout.Space(UITheme.S1);
                }
                GUILayout.Space(UITheme.S3);
            }
        }

        void StoriesTab()
        {
            var homes = TownLayout.Current?.homes;
            GUILayout.Label("The Stories of Hollow Creek. Knock where the porch light is on: some families have a story to tell, " +
                            "and they'll be home until you've heard it.", UITheme.MutedWrap);
            GUILayout.Space(UITheme.S2);
            for (int i = 0; i < Tales.All.Length; i++)
            {
                var tale = Tales.All[i];
                var teller = homes?.FirstOrDefault(h => h.tale == i);
                if (HeardTale(i))
                {
                    GUILayout.Label($"{i + 1}. {tale.Title}", UITheme.Strong);
                    GUILayout.Label(tale.Text, UITheme.BodyWrap);
                    if (teller != null) GUILayout.Label($"Told by {teller.family}, {teller.address}", UITheme.Small);
                }
                else
                {
                    GUILayout.Label($"{i + 1}. Not heard yet", UITheme.Muted);
                    if (teller != null) GUILayout.Label($"Someone on {teller.street} knows this one.", UITheme.Small);
                }
                GUILayout.Space(UITheme.S2);
            }
        }

        void LanternsTab()
        {
            var town = TownLayout.Current;
            if (town?.collectibles == null) { GUILayout.Label("The lanterns are lost in Hollow Creek. Play the town to look for them.", UITheme.MutedWrap); return; }
            GUILayout.Label("Little tin lanterns, lost all over town. Walk into one to pick it up. Found ones say where they were; the rest give the part of town.", UITheme.MutedWrap);
            GUILayout.Space(UITheme.S2);
            foreach (var c in town.collectibles)
            {
                bool found = Has("lantern:" + c.id);
                var p = new Vector3(c.p[0], 0, c.p[2]);
                string hint = found ? "Found: " + c.where : "Somewhere in " + (town.DistrictAt(p) is { Length: > 0 } d ? d : "Hollow Creek");
                GUILayout.Label($"{c.id.Substring(1)}  " + (found ? UITheme.Tint(hint, new Color(1f, 0.78f, 0.42f)) : hint), found ? UITheme.Body : UITheme.Muted);
            }
        }

        void SnapshotsTab()
        {
            GUILayout.Label("Press P to take a snapshot with the club camera. Get one of the sights below in the middle of the picture and it goes in the album.", UITheme.MutedWrap);
            GUILayout.Space(UITheme.S2);
            var sights = Snapshots.Sights;
            const int perRow = 3;
            float cellW = 220f, cellH = cellW * Snapshots.ThumbH / Snapshots.ThumbW;
            for (int i = 0; i < sights.Count; i += perRow)
            {
                GUILayout.BeginHorizontal();
                for (int j = i; j < i + perRow && j < sights.Count; j++)
                {
                    var (id, name, hint) = sights[j];
                    GUILayout.BeginVertical(GUILayout.Width(cellW));
                    var r = GUILayoutUtility.GetRect(cellW, cellH);
                    UITheme.Rect(r, new Color(0.96f, 0.93f, 0.86f));
                    var inner = new Rect(r.x + 6, r.y + 6, r.width - 12, r.height - 12);
                    var photo = Has("snap:" + id) ? Snapshots.Instance?.PhotoOf(id) : null;
                    if (photo != null) GUI.DrawTexture(inner, photo, ScaleMode.ScaleAndCrop);
                    else
                    {
                        UITheme.Rect(inner, UITheme.Raised);
                        GUI.Label(inner, "?", UITheme.TitleCenter);
                    }
                    GUILayout.Label(Has("snap:" + id) ? name : UITheme.Tint(name, UITheme.InkFaint), UITheme.Strong);
                    if (!Has("snap:" + id)) GUILayout.Label(hint, UITheme.Small);
                    GUILayout.EndVertical();
                    GUILayout.Space(UITheme.S3);
                }
                GUILayout.EndHorizontal();
                GUILayout.Space(UITheme.S3);
            }
        }

        void CuriosTab()
        {
            var town = TownLayout.Current;
            if (town?.curios == null) { GUILayout.Label("Curiosities are hidden all over the world past the edge of town. Play the town to look for them.", UITheme.MutedWrap); return; }
            GUILayout.Label($"Strange little things hidden round Hollow Creek and the haunted places past it. Look for a twinkle, then press E. " +
                            $"Found {ClubBook.CuriosFound} of {Curio.Total}. Find them all and there's a hat in it.", UITheme.MutedWrap);
            GUILayout.Space(UITheme.S2);
            foreach (var c in town.curios)
            {
                if (ClubBook.HasCurio(c.id))
                {
                    GUILayout.Label(c.n + UITheme.Tint("  · " + c.where, UITheme.InkMuted), UITheme.Strong);
                    GUILayout.Label(c.lore, UITheme.BodyWrap);
                }
                else
                {
                    var region = town.regions?.FirstOrDefault(r => r.Contains(new Vector3(c.p[0], 0, c.p[2])));
                    GUILayout.Label("Not found yet, somewhere " + (region != null ? "round " + region.n : "in or near town"), UITheme.Muted);
                }
                GUILayout.Space(UITheme.S1);
            }
        }

        void PlacesTab()
        {
            var town = TownLayout.Current;
            if (town == null) return;
            if (town.regions != null)
            {
                GUILayout.Label("Past the edge of town", UITheme.Title);
                foreach (var r in town.regions)
                {
                    bool been = Has("region:" + r.id);
                    GUILayout.Label(been ? r.n + UITheme.Tint("  · visited", UITheme.Good) : r.n, been ? UITheme.Strong : UITheme.Muted);
                    if (been) GUILayout.Label(r.blurb, UITheme.BodyWrap);
                }
                GUILayout.Space(UITheme.S3);
            }
            GUILayout.Label("Landmarks", UITheme.Title);
            if (town.landmarks != null)
                foreach (var l in town.landmarks)
                    GUILayout.Label((Has("place:" + l.n) ? l.n + UITheme.Tint("  · visited", UITheme.Good) : "Not found yet, somewhere in " + l.district),
                                    Has("place:" + l.n) ? UITheme.Body : UITheme.Muted);
            GUILayout.Space(UITheme.S3);
            GUILayout.Label("Parts of town", UITheme.Title);
            if (town.districts != null)
                GUILayout.Label(string.Join(" · ", town.districts.Select(d => Has("district:" + d.n) ? d.n : UITheme.Tint(d.n, UITheme.InkFaint))), UITheme.BodyWrap);
            GUILayout.Space(UITheme.S3);
            GUILayout.Label("Streets", UITheme.Title);
            if (town.roads != null)
                GUILayout.Label(string.Join(" · ", town.roads.Select(r => Has("street:" + r) ? r : UITheme.Tint(r, UITheme.InkFaint))), UITheme.BodyWrap);
        }
    }
}
