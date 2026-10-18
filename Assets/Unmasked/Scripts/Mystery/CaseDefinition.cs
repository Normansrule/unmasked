using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>One mystery: its suspects, its clue pool, and the tuning that sets difficulty.</summary>
    [CreateAssetMenu(menuName = "Unmasked/Case", fileName = "Case")]
    public class CaseDefinition : ScriptableObject
    {
        public string CaseName;
        public List<SuspectDefinition> Suspects = new();
        public List<ClueDefinition> Clues = new();

        [Tooltip("True clues hidden around the house at the start of the night.")]
        public int MaxSeededClues = 2;
        public int CluesRequiredToAccuse = 2;
        public int MaxAccusations = 2;
        [Tooltip("How many alibis the Solvers may check per night (search the room the alibi names).")]
        public int AlibiChecks = 2;
        [Tooltip("Difficulty knob: scales every power's chance of leaving a clue.")]
        public float LeakChanceMultiplier = 1f;
        public int MaxLeaksPerMatch = 4;
        public float WrongAccusationEctoplasmBonus = 50f;

        public SuspectDefinition FindSuspect(string id) => Suspects.Find(s => s != null && s.Id == id);
    }
}
