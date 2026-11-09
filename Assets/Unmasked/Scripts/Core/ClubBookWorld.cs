using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The Club Book's page for the world past the edge of town (round 39): the six haunted places
    /// you've set foot in (WorldLife.cs) and the curiosities you've found (Curio.cs). Marks are
    /// "region:castle", "curio:castle-helm" and "climb:lighthouse"; they never expire.
    /// </summary>
    public partial class ClubBook
    {
        public static int RegionsVisited => CountMarks("region:");
        public static int CuriosFound => CountMarks("curio:");
        public static bool HasCurio(string id) => Has("curio:" + id);

        /// <summary>First time in one of the haunted places: +15 candy. True the first time.</summary>
        public static bool VisitedRegion(string id, string name)
        {
            if (!Mark("region:" + id)) return false;
            Earn(15, "Found " + name);
            Save();
            return true;
        }

        /// <summary>A curiosity examined (Curio.cs): +10 candy, and the explorer's hat for the last one.</summary>
        public static void FoundCurio(string id, string name)
        {
            if (!Mark("curio:" + id)) return;
            Earn(10, "Curiosity: " + name);
            if (CuriosFound >= Curio.Total)
            {
                var hat = FindItem("explorer-hat");
                if (hat != null && !Owns(hat.Id))
                {
                    D.owned.Add(hat.Id);
                    Wear(hat.Id, true);
                    GameHUD.Toast("Every curiosity found. The Explorer's hat is yours, and you're wearing it (K, Wardrobe).");
                }
            }
            Save();
        }

        /// <summary>Reached the top of something tall (WorldLife.cs): "lighthouse" or "tower".</summary>
        public static void Climbed(string what)
        {
            if (!Mark("climb:" + what)) return;
            Earn(10, what == "tower" ? "Up on the tower roof" : "Up the lighthouse");
            GameHUD.Toast(what == "tower"
                ? "The roof of Gloamwood Tower. All of Hollow Creek is down there, and the sea beyond it. +10 candy."
                : "The gallery of Saltmarsh Lighthouse. The beam goes right over your head. +10 candy.");
            Save();
        }
    }
}
