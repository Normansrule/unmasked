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
            LostLantern.Ensure(gameObject); // lanterns to find around town (the Club Book keeps count)
            Doorstep.Ensure(gameObject);    // front doors to knock on for trick-or-treat
            HookBoard.Ensure(gameObject);   // the Historical Society's 24 hooks, where found lanterns go home
            CarvingBench.Ensure(gameObject); // carve a jack-o'-lantern for the HQ porch, one a night
            Wisp.Ensure(gameObject);        // will-o'-the-wisps off the creek that lead to lost lanterns
            Lamplighter.Ensure(gameObject); // Tobias Wick and the twelve gas lamps on the Creekside Path
            WorldLife.Ensure(gameObject);   // the haunted places past the edge of town: moving pieces, first visits, climbs
            Curio.Ensure(gameObject);       // curiosities hidden all over the world, each with a little story
            HauntBust.Ensure(gameObject);   // a haunt to bust in each of the twelve one-of-a-kind buildings in town
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
