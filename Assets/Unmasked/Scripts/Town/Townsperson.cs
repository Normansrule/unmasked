using System.Collections.Generic;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// One of the grown-ups out in Hollow Creek tonight (the "folk" block of HollowCreek.json, from
    /// Docs/tools/make_town.py): the mayor, the fortune teller, the minister, the diner owner and the
    /// sheriff. Press E to talk: they tell the town's side of the Mask Keeper story, and each has lost
    /// something somewhere in town (an ErrandItem). Bring it back and they put in a word for the club,
    /// which is one more alibi check (MysteryGameManager.GrantFavour), and they give the club a piece
    /// of the homemade Lantern Watch costume (GrantWatchPiece). Errands carry on from night to night
    /// and are saved on the host; what people say is never a clue.
    /// </summary>
    public class Townsperson : NetworkBehaviour, IInteractable
    {
        public enum ErrandState : byte { NotAsked, Asked, Found, Done }

        public string FolkId;
        /// <summary>The outfit, turned towards whoever comes close (the root never moves).</summary>
        public Transform Model;

        public readonly NetworkVariable<ErrandState> Errand = new();

        public static readonly List<Townsperson> All = new();

        TextMesh bubble;
        float bubbleUntil, nextTalk;
        int nextLine;
        Quaternion modelRest;

        const float BubbleTime = 6f;

        public TownLayout.Folk Info => TownLayout.Current?.FolkById(FolkId);
        public string DisplayName => Info?.name ?? FolkId;
        public string ItemName => Info?.itemName ?? "it";
        /// <summary>Which bit of MysteryGameManager.WatchPieces this person's thank-you gift is.</summary>
        public int FolkIndex
        {
            get
            {
                var folk = TownLayout.Current?.folk;
                if (folk != null) for (int i = 0; i < folk.Length; i++) if (folk[i].id == FolkId) return i;
                return -1;
            }
        }

        public static int ErrandsDone
        {
            get
            {
                int n = 0;
                foreach (var t in All) if (t.Errand.Value == ErrandState.Done) n++;
                return n;
            }
        }

        void Awake()
        {
            if (Model != null) modelRest = Model.localRotation;
            bubble = Horizon.MakeText(transform, "", new Vector3(0f, 2.55f, 0f), 0.032f, new Color(1f, 0.93f, 0.75f));
            bubble.gameObject.SetActive(false);
        }

        public override void OnNetworkSpawn()
        {
            All.Add(this);
            if (IsServer) Errand.Value = Saved(FolkId);
        }

        /// <summary>"Mayor:3,Fortune:1": every errand's state, for MysteryGameManager.SaveProgress.</summary>
        public static string SaveString()
        {
            var parts = new List<string>();
            foreach (var t in All) parts.Add($"{t.FolkId}:{(int)t.Errand.Value}");
            return string.Join(",", parts);
        }

        static ErrandState Saved(string folkId)
        {
            foreach (var entry in PlayerPrefs.GetString(MysteryGameManager.ErrandsKey, "").Split(','))
            {
                int colon = entry.IndexOf(':');
                if (colon > 0 && entry.Substring(0, colon) == folkId && int.TryParse(entry.Substring(colon + 1), out int v)
                    && v >= 0 && v <= (int)ErrandState.Done)
                    return (ErrandState)v;
            }
            return ErrandState.NotAsked;
        }

        /// <summary>Server: Start Over at HQ.</summary>
        public void ServerReset()
        {
            if (!IsServer) return;
            Errand.Value = ErrandState.NotAsked;
            nextLine = 0;
        }
        public override void OnNetworkDespawn() => All.Remove(this);

        public bool CanInteract(SolverController solver) => Info != null && Time.time >= nextTalk && !solver.IsRiding;

        public string GetPrompt(SolverController solver) =>
            Errand.Value == ErrandState.Found ? $"Give {ItemName} back to {DisplayName}" : $"Talk to {DisplayName}";

        /// <summary>Server: the errand moves on, then they say something to everyone nearby.</summary>
        public void Interact(SolverController solver)
        {
            var info = Info;
            if (!IsServer || info == null || Time.time < nextTalk) return;
            nextTalk = Time.time + 1.2f;
            switch (Errand.Value)
            {
                case ErrandState.NotAsked:
                    Errand.Value = ErrandState.Asked;
                    SayRpc(-1);
                    MysteryGameManager.Instance?.SaveProgress();
                    break;
                case ErrandState.Found:
                    Errand.Value = ErrandState.Done;
                    SayRpc(-2);
                    var game = MysteryGameManager.Instance;
                    if (game != null)
                    {
                        game.GrantFavour(info.name); // saves too
                        if (!string.IsNullOrEmpty(info.piece)) game.GrantWatchPiece(FolkIndex, info.name, info.pieceName);
                    }
                    break;
                default:
                    int count = info.lines?.Length ?? 0;
                    if (count == 0) { SayRpc(-1); break; }
                    SayRpc(nextLine % count);
                    nextLine++;
                    break;
            }
        }

        /// <summary>Server: the club picked up the lost thing; it now goes back to its owner.</summary>
        public void ServerFound(SolverController solver)
        {
            if (!IsServer || Errand.Value != ErrandState.Asked) return;
            Errand.Value = ErrandState.Found;
            var game = MysteryGameManager.Instance;
            if (game != null)
            {
                game.Announce($"Found {ItemName}! Take it back to {DisplayName}.");
                game.SaveProgress();
            }
        }

        /// <summary>-1 is the errand, -2 the thank-you, otherwise one of their lines.</summary>
        [Rpc(SendTo.ClientsAndHost)]
        void SayRpc(int line)
        {
            var info = Info;
            if (info == null) return;
            string text = line == -1 ? info.ask : line == -2 ? info.thanks
                : info.lines != null && line >= 0 && line < info.lines.Length ? info.lines[line] : "";
            if (string.IsNullOrEmpty(text)) return;
            bubble.text = TownLife.Wrap(text, 38);
            bubbleUntil = Time.time + BubbleTime;
            var face = GetComponent<FaceLife>();
            if (face != null) face.Talk(Mathf.Clamp(text.Length * 0.05f, 1.5f, 4f));
            // Bubbles are hard to read from far off, so whoever is close also gets it on screen.
            var local = SolverController.Local;
            if (local != null && Vector3.Distance(local.transform.position, transform.position) < 8f)
                GameHUD.Toast($"{info.name}: {text}");
        }

        void LateUpdate()
        {
            var cam = Camera.main;
            bool show = Time.time < bubbleUntil;
            if (bubble.gameObject.activeSelf != show) bubble.gameObject.SetActive(show);
            if (show && cam != null) bubble.transform.rotation = Quaternion.LookRotation(bubble.transform.position - cam.transform.position);

            // Turn to face the nearest Solver who comes up to them, and back again when they leave.
            if (Model == null) return;
            Transform nearest = null;
            float best = 5f;
            foreach (var s in SolverController.All)
            {
                if (s == null) continue;
                float d = Vector3.Distance(s.transform.position, transform.position);
                if (d < best) { best = d; nearest = s.transform; }
            }
            var target = modelRest;
            if (nearest != null)
            {
                var to = nearest.position - transform.position;
                to.y = 0f;
                if (to.sqrMagnitude > 0.01f) target = Quaternion.Inverse(transform.rotation) * Quaternion.LookRotation(to);
            }
            Model.localRotation = Quaternion.Slerp(Model.localRotation, target, 1f - Mathf.Exp(-5f * Time.deltaTime));
        }
    }
}
