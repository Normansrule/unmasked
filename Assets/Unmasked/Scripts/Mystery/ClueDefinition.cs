using UnityEngine;

namespace Unmasked
{
    /// <summary>A kind of clue. It points at every suspect sharing one of its traits.</summary>
    [CreateAssetMenu(menuName = "Unmasked/Clue", fileName = "Clue")]
    public class ClueDefinition : ScriptableObject
    {
        public string Id;
        public string DisplayName;
        [TextArea] public string Description;
        public Trait Traits;

        [Tooltip("Can be hidden around the house at the start of the night.")]
        public bool CanBeSeeded = true;
        [Tooltip("Can be left behind by the Haunter's own actions.")]
        public bool CanBeLeaked = true;
        [Tooltip("The Haunter can plant it to frame someone else.")]
        public bool CanBeFaked = true;

        public bool Implicates(SuspectDefinition suspect) => suspect != null && (suspect.Traits & Traits) != 0;
    }
}
