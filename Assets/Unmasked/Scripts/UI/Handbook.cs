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
        float currentUntil;
        bool pageOpen;
        Vector2 scroll;
        GUIStyle wrap, head;

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

            if (current >= 0 && Time.time > currentUntil) current = -1;
            if (current < 0 && queue.Count > 0) Show(queue.Dequeue());
        }

        void Show(int index)
        {
            current = index;
            currentUntil = Time.time + CardSeconds;
            seen |= 1 << index;
            PlayerPrefs.SetInt(SeenKey, seen);
            PlayerPrefs.Save();
        }

        void OnGUI()
        {
            if (wrap == null)
            {
                wrap = new GUIStyle(GUI.skin.label) { wordWrap = true };
                head = new GUIStyle(GUI.skin.label) { fontSize = 15, fontStyle = FontStyle.Bold };
            }

            if (current >= 0)
            {
                var hint = Hints[current];
                var r = new Rect(Screen.width / 2f - 260, Screen.height - 150, 520, 96);
                GUI.Box(r, "");
                GUI.Label(new Rect(r.x + 12, r.y + 6, 380, 24), "Handbook: " + hint.Title, head);
                GUI.Label(new Rect(r.x + 12, r.y + 30, r.width - 24, 44), hint.Text, wrap);
                GUI.Label(new Rect(r.x + 12, r.y + 72, 300, 20), "F1: the whole handbook");
                if (GUI.Button(new Rect(r.xMax - 92, r.y + 8, 80, 24), "Got it")) current = -1;
            }

            if (!pageOpen) return;
            var page = new Rect(Screen.width / 2f - 300, 70, 600, Screen.height - 160);
            GUI.Box(page, "Mystery Club Handbook");
            scroll = GUI.BeginScrollView(new Rect(page.x + 10, page.y + 28, page.width - 20, page.height - 70), scroll,
                new Rect(0, 0, page.width - 40, Hints.Length * 74));
            for (int i = 0; i < Hints.Length; i++)
            {
                bool known = (seen & (1 << i)) != 0;
                GUI.Label(new Rect(0, i * 74, 540, 22), known ? Hints[i].Title : "???", head);
                GUI.Label(new Rect(0, i * 74 + 22, 540, 48), known ? Hints[i].Text : "You'll find this one out on a night.", wrap);
            }
            GUI.EndScrollView();
            if (GUI.Button(new Rect(page.x + 10, page.yMax - 36, 160, 26), "Show hints again"))
            {
                seen = 0;
                PlayerPrefs.DeleteKey(SeenKey);
            }
            if (GUI.Button(new Rect(page.xMax - 110, page.yMax - 36, 100, 26), "Close")) pageOpen = false;
        }
    }
}
