using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The root of one place in Hollow Creek: a haunted house on its lot, or Mystery Club HQ.
    /// Everything built under it (clue spots, trap pieces, the trap site, spawns, suspect spots)
    /// belongs to it, and only the house tonight's call is about is in play.
    /// Built by Unmasked > Build Hollow Creek (Editor/TownBuilder.cs).
    /// </summary>
    public class HouseSite : MonoBehaviour
    {
        public const string HqId = "HQ";

        public string HouseId;
        public string DisplayName;
        [Tooltip("The lot, in world space (x, z).")]
        public Vector2 LotMin, LotMax;
        [Tooltip("Where the van parks for this call.")]
        public Transform Arrival;
        [Tooltip("Where each suspect waits when the call is here. Named after the suspect id.")]
        public Transform[] SuspectSpots;

        public bool IsHQ => HouseId == HqId;
        public Vector3 Center => new((LotMin.x + LotMax.x) / 2f, 0f, (LotMin.y + LotMax.y) / 2f);
        public Vector2 HalfSize => (LotMax - LotMin) / 2f;

        public bool Contains(Vector3 p, float margin = 0f) =>
            p.x >= LotMin.x - margin && p.x <= LotMax.x + margin && p.z >= LotMin.y - margin && p.z <= LotMax.y + margin;

        public Transform SuspectSpot(string suspectId)
        {
            if (SuspectSpots == null) return null;
            foreach (var spot in SuspectSpots) if (spot != null && spot.name == suspectId) return spot;
            return null;
        }

        public static HouseSite Of(Component c) => c != null ? c.GetComponentInParent<HouseSite>() : null;

        /// <summary>
        /// True if this object takes part in tonight's case: anything outside a town (Blackwood Manor
        /// on its own), or anything in the house the call is about.
        /// </summary>
        public static bool InPlay(Component c)
        {
            var site = Of(c);
            if (site == null) return true;
            var game = MysteryGameManager.Instance;
            return game != null && game.IsSpawned && site.HouseId == game.ActiveHouse.Value.ToString();
        }

        void OnDrawGizmosSelected()
        {
            Gizmos.color = IsHQ ? new Color(0.2f, 0.9f, 0.9f) : new Color(1f, 0.6f, 0.2f);
            Gizmos.DrawWireCube(Center + Vector3.up * 3f, new Vector3(LotMax.x - LotMin.x, 6f, LotMax.y - LotMin.y));
        }
    }
}
