using System;
using System.Collections.Generic;
using Unity.Netcode;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// The Mystery Club Handbook: first-time hints so a new player can get through a night without
    /// being told what to do. Each hint fires once, the first time its moment comes up, as a small
    /// card at the bottom of the screen. F1 opens the handbook page with every hint seen so far.
    /// Local only: nothing here goes over the network, and the seen hints are saved per machine.
    /// </summary>
    public class Handbook : MonoBehaviour
    {
        public const string SeenKey = "Unmasked.Handbook";
        const float CardSeconds = 10f;

        struct Hint
        {
            public string Title, Text;
            public Func<MysteryGameManager, PlayerAgent, bool> When;
        }

        static readonly Hint[] Hints =
        {
            new() { Title = "Mystery Club HQ", Text = "Every night starts here. The host picks a call on the call board, then the club drives out in the van.",
                When = (g, a) => g.InTown && g.Phase.Value == MatchPhase.Setup },
            new() { Title = "On the way", Text = "Whoever sits in the driver's seat steers with WASD. M opens the town map; follow the arrow to tonight's house.",
                When = (g, a) => g.Phase.Value == MatchPhase.Dispatch },
            new() { Title = "Look for clues", Text = "Things that glow in your flashlight are clues. Each one fits some suspects and rules others out.",
                When = (g, a) => g.Phase.Value == MatchPhase.Investigation && a.Side.Value == PlayerSide.Solver },
            new() { Title = "The Suspect Board", Text = "You found a clue. Press Tab to see who it fits, and cross off anyone it rules out.",
                When = (g, a) => g.Phase.Value == MatchPhase.Investigation && a.Side.Value == PlayerSide.Solver && g.Clues.Count >= 1 },
            new() { Title = "Ready to accuse", Text = "You have enough clues to name someone. You only get two tries, so check an alibi first if two suspects still fit.",
                When = (g, a) => a.Side.Value == PlayerSide.Solver && g.CanAccuseNow },
            new() { Title = "Scared!", Text = "Stay near a teammate to calm down. Three panics and you are out for the night.",
                When = (g, a) => a.Side.Value == PlayerSide.Solver && a.PanicCount.Value >= 1 && !a.ScaredOut.Value },
            new() { Title = "Build the trap", Text = "Right suspect! Carry trap pieces to the trap site, build it, then lure the costumed Haunter into it.",
                When = (g, a) => g.Phase.Value == MatchPhase.Trap && a.Side.Value == PlayerSide.Solver },
            new() { Title = "You are the Haunter", Text = "Possess furniture, slam doors and use your legend's power (6 or Q). Scare the club out before dawn, and keep your suspect's secret.",
                When = (g, a) => a.Side.Value == PlayerSide.Haunter && g.Phase.Value == MatchPhase.Investigation },
            new() { Title = "Help the town", Text = "Townsfolk with an errand will ask for a hand. Each errand you finish gives a favour and a Lantern Watch piece for the trunk at HQ.",
                When = (g, a) => g.InTown && g.Phase.Value == MatchPhase.Setup && g.SolvedCases.Count >= 1 },
            new() { Title = "Case closed", Text = "That house throws a party now, and the town remembers. Back at HQ, the next call is waiting.",
                When = (g, a) => g.Phase.Value == MatchPhase.Ended && g.Winner.Value == MatchWinner.Solvers },
        };

        readonly Queue<int> queue = new();
        int seen, current = -1;
        float currentShown, currentUntil, closingAt = -1f;
        bool pageOpen;
        Vector2 scroll;

        void Awake() => seen = PlayerPrefs.GetInt(SeenKey, 0);

        void Update()
        {
            var keyboard = Keyboard.current;
            if (keyboard != null && keyboard.f1Key.wasPressedThisFrame) pageOpen = !pageOpen;

            var game = MysteryGameManager.Instance;
            var agent = PlayerAgent.Local;
            var net = NetworkManager.Singleton;
            if (game == null || !game.IsSpawned || agent == null || net == null || !net.IsClient) return;

            for (int i = 0; i < Hints.Length; i++)
            {
                if ((seen & (1 << i)) != 0 || queue.Contains(i) || current == i) continue;
                if (Hints[i].When(game, agent)) queue.Enqueue(i);
            }

            if (current >= 0 && Time.unscaledTime > currentUntil) current = -1;
            if (current < 0 && queue.Count > 0) Show(queue.Dequeue());
        }

        void Show(int index)
        {
            current = index;
            currentShown = Time.unscaledTime;
            currentUntil = currentShown + CardSeconds;
            seen |= 1 << index;
            PlayerPrefs.SetInt(SeenKey, seen);
            PlayerPrefs.Save();
        }

        /// <summary>Dismiss the card: it fades out instead of vanishing.</summary>
        void Dismiss() => currentUntil = Mathf.Min(currentUntil, Time.unscaledTime + UITheme.ExitSeconds);

        void OnGUI()
        {
            UITheme.Begin();

            if (current >= 0)
            {
                // Bottom centre, above the help line: a note pinned up for you. It arrives by itself,
                // so it eases in; the handbook page (F1) is opened from the keyboard and appears at once.
                var hint = Hints[current];
                const float w = 560f;
                float textH = UITheme.BodyWrap.CalcHeight(new GUIContent(hint.Text), w - 32f);
                float h = 44f + textH + 28f;
                var (alpha, rise) = UITheme.Arrive(currentShown, currentUntil, 12f);
                var r = new Rect(UITheme.W / 2f - w / 2f, UITheme.H - 44f - h + rise, w, h);
                var old = GUI.color;
                GUI.color = new Color(1f, 1f, 1f, alpha);
                UITheme.Rect(new Rect(r.x + 1f, r.y + 3f, r.width, r.height), UITheme.Shadow);
                UITheme.Rect(r, UITheme.Raised);
                UITheme.Pin(new Vector2(r.center.x, r.y + 2f));
                GUI.Label(new Rect(r.x + 16, r.y + 12, w - 140, 26), hint.Title, UITheme.Title);
                GUI.Label(new Rect(r.x + 16, r.y + 40, w - 32, textH), hint.Text, UITheme.BodyWrap);
                GUI.Label(new Rect(r.x + 16, r.yMax - 26, 300, 20), "F1 opens the whole handbook", UITheme.Small);
                if (GUI.Button(new Rect(r.xMax - 104, r.y + 10, 88, 30), "Got it", UITheme.CardButton)) Dismiss();
                GUI.color = old;
            }

            if (!pageOpen) return;
            UITheme.Rect(new Rect(0, 0, UITheme.W, UITheme.H), UITheme.Scrim);
            float pw = Mathf.Min(640f, UITheme.W - 2 * UITheme.S6);
            var page = new Rect(UITheme.W / 2f - pw / 2f, UITheme.S6, pw, UITheme.H - 2 * UITheme.S6);
            GUILayout.BeginArea(page, UITheme.Panel);
            GUILayout.Label("Mystery Club Handbook", UITheme.Display);
            GUILayout.Label("Hints you've seen so far. The rest turn up on a night.", UITheme.MutedWrap);
            GUILayout.Space(UITheme.S3);
            scroll = GUILayout.BeginScrollView(scroll);
            for (int i = 0; i < Hints.Length; i++)
            {
                bool known = (seen & (1 << i)) != 0;
                GUILayout.Label(known ? Hints[i].Title : UITheme.Tint("Not found yet", UITheme.InkFaint), UITheme.Title);
                if (known) GUILayout.Label(Hints[i].Text, UITheme.BodyWrap);
                GUILayout.Space(UITheme.S3);
            }

            // Settings that belong to whoever is at this computer.
            GUILayout.Space(UITheme.S3);
            GUILayout.Label("Reading and motion", UITheme.Title);
            GUILayout.BeginHorizontal();
            GUILayout.Label("Text size", UITheme.Muted, GUILayout.Width(110));
            for (int i = 0; i < UITheme.TextSizes.Length; i++)
                if (GUILayout.Toggle(UITheme.TextSize == i, UITheme.TextSizeNames[i], GUI.skin.button) && UITheme.TextSize != i)
                    UITheme.SetTextSize(i);
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            GUILayout.Label("Motion", UITheme.Muted, GUILayout.Width(110));
            if (GUILayout.Toggle(!UITheme.ReduceMotion, "Full", GUI.skin.button) && UITheme.ReduceMotion) UITheme.SetReduceMotion(false);
            if (GUILayout.Toggle(UITheme.ReduceMotion, "Reduced (fades only)", GUI.skin.button) && !UITheme.ReduceMotion) UITheme.SetReduceMotion(true);
            GUILayout.EndHorizontal();
            GUILayout.EndScrollView();

            GUILayout.Space(UITheme.S3);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Show hints again", GUILayout.Width(180)))
            {
                seen = 0;
                PlayerPrefs.DeleteKey(SeenKey);
            }
            GUILayout.FlexibleSpace();
            if (GUILayout.Button("Close", UITheme.Primary, GUILayout.Width(120))) pageOpen = false;
            GUILayout.EndHorizontal();
            GUILayout.EndArea();
        }
    }
}
