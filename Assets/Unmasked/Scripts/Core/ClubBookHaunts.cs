namespace Unmasked
{
    /// <summary>
    /// The Club Book's page for the haunts in town (round 42, Town/HauntBust.cs). Marks are
    /// "hauntsign:bakery:0" for each sign you've read and "haunt:bakery" once it's busted; they
    /// never expire. Busting all twelve earns the Haunt Buster's cap.
    /// </summary>
    public partial class ClubBook
    {
        public static int HauntsBusted => CountMarks("haunt:");
        public static bool HasHaunt(string id) => Has("haunt:" + id);
        public static bool HasHauntSign(string id, int i) => Has($"hauntsign:{id}:{i}");

        /// <summary>A sign of a haunt read for the first time. True the first time.</summary>
        public static bool FoundHauntSign(string id, int i)
        {
            if (!Mark($"hauntsign:{id}:{i}")) return false;
            Save();
            return true;
        }

        /// <summary>A haunt busted: +20 candy, and the cap for the last one.</summary>
        public static void BustedHaunt(string id, string building)
        {
            if (!Mark("haunt:" + id)) return;
            Earn(20, "Busted the haunt at " + building);
            if (HauntsBusted >= HauntBust.Total)
            {
                var cap = FindItem("buster-cap");
                if (cap != null && !Owns(cap.Id))
                {
                    D.owned.Add(cap.Id);
                    Wear(cap.Id, true);
                    GameHUD.Toast("Every haunt in Hollow Creek busted. The Haunt Buster's cap is yours, and you're wearing it (K, Wardrobe).");
                }
            }
            Save();
        }
    }
}
