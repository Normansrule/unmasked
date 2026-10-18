using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The street remembers. Each house on its lot looks the way its story stands, on every machine,
    /// from the same networked state the case book uses:
    ///   Quiet    no call yet: just the house.
    ///   Haunted  tonight's call is here (ActiveHouse): a violet light pulses over the yard.
    ///   Solved   its first case is in the case book: lanterns line the walk, jack-o'-lanterns at the
    ///            gate, a thank-you banner and a party table in the yard, warm light over it all.
    /// Built by TownBuilder from the "afterglow" block of each lot in HollowCreek.json.
    /// </summary>
    public class HouseMood : MonoBehaviour
    {
        public enum Mood { Quiet, Haunted, Solved }

        public string HouseId;
        [Tooltip("Everything that goes up once the case is solved.")]
        public GameObject Afterglow;
        [Tooltip("The violet light over the yard while the call is open.")]
        public Light Haunt;

        public Mood Current { get; private set; } = Mood.Quiet;
        bool known;
        float hauntBase;

        void Awake()
        {
            if (Haunt != null) hauntBase = Haunt.intensity;
        }

        public static Mood MoodOf(MysteryGameManager game, string houseId)
        {
            if (game == null || !game.IsSpawned) return Mood.Quiet;
            // A solved house stays warm even when it calls again for its return visit, but tonight's
            // call still shows: the violet light comes on over the party.
            if (game.ActiveHouse.Value.ToString() == houseId && game.Phase.Value != MatchPhase.Ended)
                return Mood.Haunted;
            return game.IsSolved(houseId) ? Mood.Solved : Mood.Quiet;
        }

        void Update()
        {
            var game = MysteryGameManager.Instance;
            var mood = MoodOf(game, HouseId);
            bool solved = game != null && game.IsSpawned && game.IsSolved(HouseId);
            if (Afterglow != null && Afterglow.activeSelf != solved)
            {
                Afterglow.SetActive(solved);
                if (solved && known) Sfx.Play("clue_chime", transform.position, 0.7f, 30f, 0.9f);
            }
            if (Haunt != null)
            {
                bool haunted = mood == Mood.Haunted;
                if (Haunt.enabled != haunted) Haunt.enabled = haunted;
                if (haunted) Haunt.intensity = hauntBase * (0.75f + 0.25f * Mathf.Sin(Time.time * 2.3f) + 0.1f * Mathf.Sin(Time.time * 7.1f));
            }
            Current = mood;
            known = true;
        }
    }
}
