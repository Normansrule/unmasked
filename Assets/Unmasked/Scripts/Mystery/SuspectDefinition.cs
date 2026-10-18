using UnityEngine;

namespace Unmasked
{
    /// <summary>One suspect in a case (the groundskeeper, the heiress...). The Haunter secretly IS one of these.</summary>
    [CreateAssetMenu(menuName = "Unmasked/Suspect", fileName = "Suspect")]
    public class SuspectDefinition : ScriptableObject
    {
        public string Id;
        public string DisplayName;
        public string Occupation;
        [TextArea] public string Bio;
        [Tooltip("What they claim they were doing.")]
        [TextArea] public string Alibi;
        [Tooltip("The room the alibi puts them in (a room in the house, or a place in town like \"Diner\"). Solvers can search it once to check the alibi. Empty: can't be checked.")]
        public string AlibiRoom;
        [Tooltip("Give each suspect one unique trait plus a couple of shared ones.")]
        public Trait Traits;
        public Texture2D Portrait;

        public SuspectInfo ToPublicInfo() => new SuspectInfo
        {
            Id = Id,
            Name = DisplayName,
            Occupation = Occupation,
            Bio = Bio,
            Alibi = Alibi,
            AlibiRoom = AlibiRoom ?? string.Empty,
            Traits = (int)Traits
        };
    }
}
