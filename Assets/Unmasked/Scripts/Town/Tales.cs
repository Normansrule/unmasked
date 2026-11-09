namespace Unmasked
{
    /// <summary>
    /// The Stories of Hollow Creek: twelve tales the families on the new streets tell when you knock
    /// (Doorstep.cs). Each is told at one house (HollowCreek.json "homes", "tale"), and together they
    /// say where the lost lanterns came from, why everyone leaves the porch light on, and why the town
    /// needs a Mystery Club. They can be heard in any order; the Club Book keeps them in order.
    /// </summary>
    public static class Tales
    {
        public class Tale
        {
            public string Title, Text;
        }

        static Tale T(string title, string text) => new() { Title = title, Text = text };

        public static readonly Tale[] All =
        {
            T("The first Halloween",
              "In 1823 the first families built their houses by the creek. On the last night of October a mist rolled up off the water, " +
              "thick as wool. Abel Hatcher hung a lantern on his mill door, and the mist stopped right at the edge of the light."),
            T("Twenty-four lanterns",
              "Hester Quill, the tinsmith, made a lantern for every family that first winter: twenty-four of them, with stars punched in the tin. " +
              "Every Halloween after that, each family carried its lantern down to the creek and kept it lit until morning."),
            T("The Lantern Watch",
              "The ones who carried the lanterns were the Lantern Watch. They wore masks, so the mist wouldn't learn their faces. " +
              "That's where all the old folklore masks come from, you know. The Watch made them."),
            T("Stingy Jack's coal",
              "They say Hester lit the very first candle from a coal Stingy Jack carried, and paid him for it with a bowl of her apple pie. " +
              "He thinks he was cheated. Every so often he comes back to town, asking for it back."),
            T("The Hollow Creek Mask",
              "The oldest mask was carved from an oak beam out of Hatcher's mill, and only the captain of the Watch wore it. " +
              "The Historical Society keeps it now, behind glass. Mostly behind glass."),
            T("The flood of 1891",
              "One Halloween the creek came up over the banks in an hour. The Watch held on as long as they could, but the water took the lanterns " +
              "and scattered them all over the valley. People were finding them in hedges and orchards for years."),
            T("Why the porch lights",
              "With the lanterns gone, every family left a light burning by the door instead, all Halloween night. " +
              "The children went door to door to make sure every light was lit, and got a treat for checking. That's trick-or-treat, that is."),
            T("The ledger",
              "The 1823 ledger lists all twenty-four lantern families. Some people will tell you that whoever finds every lantern owns a share of the town. " +
              "Nonsense, of course. But you'd be surprised who goes looking."),
            T("Why there's a Haunter",
              "Every few years somebody gets hold of one of the old masks and decides the night belongs to them. " +
              "They frighten everyone off the streets so they can do as they please. That's what the Mystery Club is for."),
            T("The scarecrow's coat",
              "Hatcher's Corn Maze is planted on Abel Hatcher's old field. The scarecrow in the middle is wearing the last Watch captain's coat. " +
              "Nobody remembers putting it there."),
            T("Twenty-four hooks",
              "In the back room of the Historical Society there's a board with twenty-four brass hooks, one for each lantern, and a name over every hook. " +
              "Most of the hooks are empty. A few of them aren't any more."),
            T("The last lantern",
              "The old folks say that when all twenty-four lanterns are found and lit again, the mist will stay down on the creek for good. " +
              "And whoever found them would be the new Lantern Watch. I think that might be you lot."),
        };
    }
}
