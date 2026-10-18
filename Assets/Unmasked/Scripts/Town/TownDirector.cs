using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Marks a scene as the Hollow Creek town and finds its places. With a TownDirector in the scene,
    /// a night starts at Mystery Club HQ and goes through the Dispatch phase (drive to the call);
    /// without one (Blackwood Manor on its own) it starts in the house as before.
    /// </summary>
    public class TownDirector : MonoBehaviour
    {
        public static TownDirector Instance { get; private set; }

        public HouseSite[] Sites { get; private set; } = new HouseSite[0];
        public HouseSite HQ { get; private set; }

        void Awake()
        {
            Instance = this;
            Sites = FindObjectsByType<HouseSite>(FindObjectsSortMode.None);
            foreach (var site in Sites) if (site.IsHQ) HQ = site;
            Horizon.Ensure(gameObject); // the world past the edge of the map
            TownLife.Ensure(gameObject); // trick-or-treaters, cars, a far-off train
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        public HouseSite Find(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            foreach (var site in Sites) if (site.HouseId == id) return site;
            return null;
        }

        /// <summary>The houses a call can be about (everything but HQ).</summary>
        public HouseSite[] Houses => System.Array.FindAll(Sites, s => !s.IsHQ);
    }
}
