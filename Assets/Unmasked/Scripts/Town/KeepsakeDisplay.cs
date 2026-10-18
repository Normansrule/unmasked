using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// A keepsake on the shelf at Mystery Club HQ: it appears once the club has solved that house's
    /// case (MysteryGameManager.SolvedCases, saved on the host). Purely cosmetic, read on every machine.
    /// </summary>
    public class KeepsakeDisplay : MonoBehaviour
    {
        public string HouseId;
        [Tooltip("Shown once the case is solved.")]
        public GameObject Model;
        [Tooltip("Shown until then: a little card saying which case is still open.")]
        public GameObject EmptyCard;

        bool shown, known;

        void Update()
        {
            var game = MysteryGameManager.Instance;
            bool solved = game != null && game.IsSpawned && game.IsSolved(HouseId);
            if (known && solved == shown) return;
            known = true;
            shown = solved;
            if (Model != null) Model.SetActive(solved);
            if (EmptyCard != null) EmptyCard.SetActive(!solved);
            if (solved && Model != null) Sfx.Play("clue_chime", transform.position, 0.6f, 12f, 1.2f);
        }
    }
}
