using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Shows the Lantern Watch pieces on a Solver while the club wears the costume: only the pieces
    /// the club actually has. Every role's outfit carries its own Watch_&lt;Piece&gt; children (built
    /// by TestRoomBuilder from Costumes.json "watch"). Cosmetic, read on every machine.
    /// </summary>
    public class WatchCostume : MonoBehaviour
    {
        int shownMask = -1;

        void Update()
        {
            var game = MysteryGameManager.Instance;
            var folk = TownLayout.Current?.folk;
            int mask = game != null && game.IsSpawned && game.WearingWatch.Value ? game.WatchPieces.Value : 0;
            if (mask == shownMask) return;
            shownMask = mask;
            foreach (var t in GetComponentsInChildren<Transform>(true))
            {
                if (!t.name.StartsWith("Watch_")) continue;
                string piece = t.name.Substring(6);
                bool on = false;
                if (folk != null)
                    for (int i = 0; i < folk.Length; i++)
                        if (folk[i].piece == piece && (mask & (1 << i)) != 0) on = true;
                t.gameObject.SetActive(on);
            }
        }
    }
}
