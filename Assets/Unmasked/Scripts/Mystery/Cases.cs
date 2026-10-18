using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// One mystery per haunted house in Hollow Creek. The same four actors play a different cast at
    /// each house (their suspect spots and models are keyed by slot: Groundskeeper, Heiress, Rival,
    /// Cook), but every house has its own names, alibis, clues and gossip.
    ///
    /// The clue maths is the same everywhere: each suspect has one unique trait and two shared ones,
    /// so any two true clues name exactly one suspect. Bits 0-3 are the unique traits (slot order),
    /// bit 4 is shared by Groundskeeper + Heiress, bit 5 by Groundskeeper + Cook, bit 6 by Heiress +
    /// Rival, bit 7 by Rival + Cook. Only the labels change from house to house.
    ///
    /// The story: Hollow Creek's old folklore masks were brought out for the Halloween festival, and
    /// whoever wears one can really haunt a house. Tonight a resident is using one to cover up
    /// something ordinary (a theft, a sabotage, a forged claim). Which mask is no secret: it's
    /// announced at the start. Who is wearing it is the case. Each suspect has a motive, revealed
    /// only for the one who is unmasked.
    ///
    /// This is plain data that every machine has, so clients can label traits without being told.
    /// </summary>
    public static class Cases
    {
        public const string DefaultHouse = "BlackwoodManor";

        public class SuspectSpec
        {
            public string Name, Job, Bio, Alibi;
            /// <summary>Where the alibi puts them: a room in the house or a place in town.</summary>
            public string AlibiRoom;
        }

        public class ClueSpec
        {
            public string Id, Name, Description;
        }

        public class Spec
        {
            public string HouseId, CaseName;
            /// <summary>1 for a house's first case; 2 for the return visit, which calls once the first is solved.</summary>
            public int Visit = 1;
            /// <summary>"PembertonCottage" for a first case, "PembertonCottage#2" for a return visit.</summary>
            public string CaseId => Visit <= 1 ? HouseId : HouseId + "#" + Visit;
            public bool IsReturnVisit => Visit > 1;
            /// <summary>The ordinary wrongdoing the haunting is covering up, told at the call.</summary>
            public string Premise;
            /// <summary>What's put right when the case is solved (shown at the end, and a keepsake goes on the HQ shelf).</summary>
            public string Recovered;
            /// <summary>The Mask Keeper arc: what this culprit lets slip about who handed them the mask.</summary>
            public string ArcClue;
            /// <summary>What the trick-or-treaters in town say about this house once the call comes in (flavour, never a clue).</summary>
            public string[] Rumours;
            /// <summary>Why each suspect would wear the mask (slot order), finishing "X wore the mask ...".</summary>
            public string[] Motives;
            /// <summary>Groundskeeper, Heiress, Rival, Cook.</summary>
            public SuspectSpec[] Suspects;
            /// <summary>One label per trait bit, as shown on the Suspect Board.</summary>
            public string[] TraitNames;
            /// <summary>One clue per trait bit.</summary>
            public ClueSpec[] Clues;
            /// <summary>What innocent suspects say; {0} is the suspect they point at.</summary>
            public string[] Gossip;
            public int MaxSeededClues = 2;
            public int MaxAccusations = 2;
            public int AlibiChecks = 2;
            public float LeakChanceMultiplier = 1f;
        }

        public static readonly string[] Slots = { "Groundskeeper", "Heiress", "Rival", "Cook" };

        /// <summary>The eight trait bits: 0-3 unique to one suspect, 4-7 shared by two.</summary>
        public static readonly Trait[] Bits =
        {
            Trait.MuddyBoots, Trait.Perfume, Trait.CigarAsh, Trait.Flour,
            Trait.MasterKeys, Trait.Gardening, Trait.Jewelry, Trait.LeatherGloves
        };

        static readonly Trait[] SlotTraits =
        {
            Trait.MuddyBoots | Trait.MasterKeys | Trait.Gardening,  // Groundskeeper
            Trait.Perfume | Trait.MasterKeys | Trait.Jewelry,       // Heiress
            Trait.CigarAsh | Trait.Jewelry | Trait.LeatherGloves,   // Rival
            Trait.Flour | Trait.LeatherGloves | Trait.Gardening,    // Cook
        };

        static SuspectSpec S(string name, string job, string bio, string alibi, string alibiRoom) =>
            new() { Name = name, Job = job, Bio = bio, Alibi = alibi, AlibiRoom = alibiRoom };
        static ClueSpec C(string id, string name, string description) => new() { Id = id, Name = name, Description = description };

        public static readonly Spec[] All =
        {
            new Spec
            {
                HouseId = "BlackwoodManor",
                CaseName = "The Missing Blackwood Ledger",
                Recovered = "The ledger is back in the Library, and Hollow Creek finally knows who owns what.",
                ArcClue = "Pinned inside the ledger thief's coat: a brass key to the Historical Society's back door, on a ring stamped \"STAFF ONLY\".",
                Rumours = new[] { "Blackwood Manor? My dad says the lights there go on and off all by themselves.", "Everyone's arguing about who owns the land up by the manor. Grown-ups are so boring." },
                Premise = "The 1823 town ledger, which says who really owns half of Hollow Creek, has vanished from the Library.",
                Motives = new[]
                {
                    "to keep the ledger from showing the greenhouse land was never his family's",
                    "to tear out the page that splits her inheritance with a long-lost cousin",
                    "to sell the ledger to a collector in the city while everyone hid from the ghost",
                    "to hide the old recipe pages tucked inside it, the ones her prize pies are copied from",
                },
                Suspects = new[]
                {
                    S("Gus Thornbury", "Groundskeeper", "Has tended the Blackwood grounds for forty years and hates visitors trampling his roses.",
                      "Says he was locking up the Greenhouse all evening.", "Greenhouse"),
                    S("Vivian Blackwood", "Heiress", "Inherits the manor next month, unless it's 'too haunted' to sell.",
                      "Claims she was in the Library reading all night.", "Library"),
                    S("Reginald Pike", "Rival antiques dealer", "Has been trying to buy the manor's antiques for a song.",
                      "Insists he left before sunset and spent the evening at the Diner in town.", "Diner"),
                    S("Martha Bunce", "Cook", "Bakes the best pies in the county and knows every servants' passage.",
                      "Says she was in the Kitchen baking for tomorrow's party until midnight.", "Kitchen"),
                },
                TraitNames = new[] { "Muddy boots", "Perfume", "Cigar ash", "Flour", "Master keys", "Gardening", "Jewelry", "Leather gloves" },
                Clues = new[]
                {
                    C("BootPrint", "Muddy boot print", "Fresh garden mud, heavy work boots."),
                    C("Perfume", "Whiff of lavender", "Expensive lavender perfume lingers on the curtain."),
                    C("CigarAsh", "Cigar ash", "Still-warm ash from an imported cigar."),
                    C("FlourPrint", "Floury handprint", "A perfect handprint in baking flour."),
                    C("KeyRing", "Dropped key ring", "A ring of old master keys to the manor."),
                    C("RosePetals", "Fresh rose petals", "Petals from the manor's prize rose garden."),
                    C("Pearl", "Loose pearl", "A real pearl from a broken necklace."),
                    C("Glove", "Torn leather glove", "A fine leather glove, torn on a nail."),
                },
                Gossip = new[]
                {
                    "I saw {0} sneaking around the east wing after dark. Very suspicious!",
                    "If you ask me, {0} has been acting strange all week.",
                    "{0} said they went to bed early... but their light was on past midnight.",
                    "Keep an eye on {0}. They know this place better than they let on.",
                },
            },
            new Spec
            {
                HouseId = "PembertonCottage",
                CaseName = "The Missing Harvest Lantern",
                Recovered = "The Harvest Lantern is back on Mrs. Pemberton's mantel, just in time for the lantern walk.",
                ArcClue = "Tied to the lantern thief's mask: a little paper tag, \"Hollow Creek Historical Society, item 7, on loan\".",
                Rumours = new[] { "Old Mrs. Pemberton's lantern walk is tomorrow. She's ever so worried about it.", "We knocked at Pemberton Cottage and something went WHOOSH behind the curtains!" },
                Premise = "The Harvest Lantern that leads the festival's lantern walk has vanished from Mrs. Pemberton's mantel, and her teapot hasn't stopped rattling since.",
                Motives = new[]
                {
                    "to sell the lantern's old brass to a scrap dealer and blame it on the ghost",
                    "to scare Grandma into moving out, lantern and all",
                    "to pocket the lantern and sell his buyer a 'charmingly haunted' cottage",
                    "to carry the lantern in the walk herself and finally win the garden prize",
                },
                MaxSeededClues = 3,
                MaxAccusations = 3,
                AlibiChecks = 3,
                LeakChanceMultiplier = 1.3f,
                Suspects = new[]
                {
                    S("Hank Moody", "Handyman", "Has been 'fixing' Mrs. Pemberton's shed since June and charges by the hour.",
                      "Says he was fixing the lock on the Garden Shed, then went home with a sore back.", "Garden Shed"),
                    S("Daisy Pemberton", "Granddaughter", "Wants the cottage for herself, and Grandma won't move out while the teapot behaves.",
                      "Claims she was at the Diner in town with friends all evening.", "Diner"),
                    S("Leonard Crisp", "Estate agent", "Already has a buyer lined up for a 'charming, slightly haunted' cottage.",
                      "Insists he was showing a house on Elm Street.", "Elm Street"),
                    S("Beatrice Hollis", "Next-door neighbour", "Runs the bake-off club and has wanted that prize-winning garden for years.",
                      "Says she was icing cupcakes in Mrs. Pemberton's Kitchen, as a favour.", "Kitchen"),
                },
                TraitNames = new[] { "Sawdust", "Glitter", "Hair pomade", "Icing sugar", "Spare key", "Potting soil", "Gold locket", "Chamomile tea" },
                Clues = new[]
                {
                    C("Sawdust", "Pile of sawdust", "Fresh sawdust, the kind you get from sawing a shed door."),
                    C("Glitter", "Pink glitter", "Party glitter, still sparkling on the windowsill."),
                    C("Pomade", "Greasy smudge", "A hair-pomade smudge on the hall mirror. Smells of limes."),
                    C("Icing", "Icing sugar", "A dusting of icing sugar on the doorknob."),
                    C("SpareKey", "Spare key", "The spare key from under the flowerpot, left on the rug."),
                    C("Soil", "Potting soil", "Rich potting soil from the vegetable patch, trodden indoors."),
                    C("Locket", "Gold locket", "A gold locket with a tiny photo of the cottage inside."),
                    C("TeaLeaves", "Spilled tea leaves", "Chamomile tea leaves, scattered as if the pot leapt by itself."),
                },
                Gossip = new[]
                {
                    "I saw {0} by the garden shed after dark. With a torch!",
                    "{0} asked me how much a cottage like this would fetch. Odd question, isn't it?",
                    "Between you and me, {0} was the last one to touch that teapot.",
                    "{0} knows where the spare key is. Everybody knows {0} knows.",
                },
            },
            new Spec
            {
                HouseId = "HollowCreekFarm",
                CaseName = "The Sabotaged Prize Display",
                Recovered = "The prize display is mended and the judges can come in the morning.",
                ArcClue = "The saboteur says someone with ink-stained fingers left the mask on their porch with a note: \"For one night only.\"",
                Rumours = new[] { "The farm's entering the county fair again. They always win the blue rosette.", "There's something big and spooky in the Hollow Creek cornfield. I'm not going back there." },
                Premise = "Someone wrecked the farm's prize pumpkin display the night before judging, and the scarecrow keeps moving.",
                Motives = new[]
                {
                    "to hide that the prize pumpkin was bought in town, not grown",
                    "to make the farm lose, so it sells and she can leave for the city",
                    "to scare the Hatchers into selling the corn maze for his car park",
                    "to make sure her own pie stand takes best in show",
                },
                MaxSeededClues = 2,
                MaxAccusations = 2,
                LeakChanceMultiplier = 1.15f,
                Suspects = new[]
                {
                    S("Abel Hatcher", "Farmer", "Runs the farm with his sister and swears the scarecrow moved on its own.",
                      "Says he was mending the Windmill until it got dark.", "Windmill"),
                    S("Clementine Hatcher", "Harvest Queen", "Won the county fair three years running and wants to sell the farm and move to the city.",
                      "Claims she was rehearsing her parade wave in the Parlor.", "Parlor"),
                    S("Silas Crane", "Land developer", "Wants to turn the corn maze into a car park, if only the farm were 'too spooky' to keep.",
                      "Insists he was at the Post Office in town, mailing plans to the county.", "Post Office"),
                    S("Ma Jessup", "Runs the pie stand", "Sells pies at the farm gate and hears every bit of gossip in the county.",
                      "Says she was baking apple pies in the Farm Kitchen for the Harvest Festival.", "Farm Kitchen"),
                },
                TraitNames = new[] { "Hay seeds", "Pageant glitter", "Surveyor's chalk", "Apple peel", "Barn key", "Corn husks", "Rodeo buckle", "Tractor grease" },
                Clues = new[]
                {
                    C("HaySeeds", "Hay seeds", "Seeds from the very top of the hayloft, stuck in a boot tread."),
                    C("PageantGlitter", "Gold glitter", "Gold pageant glitter on the ladder rungs."),
                    C("Chalk", "Surveyor's chalk", "Bright blue chalk, the kind used to mark out building plots."),
                    C("AppleParing", "Apple peel", "A long curl of apple peel, still fresh."),
                    C("BarnKey", "Barn key", "The big iron key to the barn, dropped in the straw."),
                    C("CornHusk", "Corn husks", "Husks from the maze, tucked into a pocket and dropped."),
                    C("Buckle", "Rodeo belt buckle", "A shiny silver buckle shaped like a horseshoe."),
                    C("Grease", "Tractor grease", "Black grease on the hayloft hatch. Someone's been near an engine."),
                },
                Gossip = new[]
                {
                    "I saw {0} up in the hayloft after milking time. Nobody goes up there!",
                    "{0} keeps asking how deep the corn maze goes. What for, I wonder?",
                    "{0} said they never set foot in the barn tonight. Then why the straw on their sleeve?",
                    "Mark my words, {0} wants this farm empty by the first frost.",
                },
            },
            new Spec
            {
                HouseId = "WillowLaneVictorian",
                CaseName = "The Interrupted Recital",
                Recovered = "The donation tin is found and Lavinia's recital goes on, music box and all.",
                ArcClue = "The mask's box smells of lavender and old paper, exactly like the Historical Society reading room.",
                Rumours = new[] { "The music box at the Victorian plays by itself. My cousin heard it!", "Lavinia's recital is on Saturday. I hope they don't cancel it, she's been practising for ages." },
                Premise = "The nursery music box keeps cutting off Lavinia's charity recital, and the donation tin went missing in the fuss.",
                Motives = new[]
                {
                    "to hide that he'd borrowed from the donation tin to mend the family plot gate",
                    "to stop the recital before anyone counted the donation tin",
                    "to frighten Lavinia into finally selling him the music box",
                    "to slip the donation tin away while everyone stared at the music box",
                },
                MaxSeededClues = 2,
                MaxAccusations = 2,
                LeakChanceMultiplier = 1f,
                Suspects = new[]
                {
                    S("Ezra Cole", "Caretaker", "Has kept the Ashcombe garden and family plot tidy since he was a boy.",
                      "Says he was raking leaves in the Family Plot until the candles burned down.", "Family Plot"),
                    S("Lavinia Ashcombe", "The last Ashcombe", "Lives alone in the big house and hasn't slept since the music box started playing.",
                      "Claims she was locked in the Master Bedroom with the radio on.", "Master Bedroom"),
                    S("Dr. Felix Marlowe", "Music-box collector", "Has offered three times to buy the nursery's music box. Three times he was refused.",
                      "Insists he was at the Bookshop in town until closing.", "Bookshop"),
                    S("Agnes Pratt", "Housekeeper", "Knows every creaky floorboard and every secret door in the house.",
                      "Says she was polishing the silver in the Dining Room for Sunday.", "Dining Room"),
                },
                TraitNames = new[] { "Hedge clippings", "Violet perfume", "Pipe tobacco", "Silver polish", "Skeleton key", "Graveyard dirt", "Velvet thread", "Candle wax" },
                Clues = new[]
                {
                    C("Clippings", "Hedge clippings", "Fresh clippings from the front hedge, tracked up the stairs."),
                    C("Violets", "Scent of violets", "Violet perfume, faint but unmistakable, in the nursery."),
                    C("Tobacco", "Pipe tobacco", "A pinch of cherry pipe tobacco on the windowsill."),
                    C("Polish", "Silver polish", "A smear of silver polish on the music box's key."),
                    C("SkeletonKey", "Skeleton key", "An old skeleton key that opens the nursery door."),
                    C("GraveDirt", "Graveyard dirt", "Dark soil from the family plot, still damp."),
                    C("Velvet", "Velvet thread", "A thread of plum velvet caught on the trapdoor."),
                    C("Wax", "Candle wax", "Drips of black candle wax leading to the tower stairs."),
                },
                Gossip = new[]
                {
                    "I heard {0} on the tower stairs when the music box began. I'm sure of it.",
                    "{0} has wanted that music box for years. Years!",
                    "{0} knows the nursery better than anyone alive.",
                    "Ask {0} why the candles in the family plot were lit tonight.",
                },
            },
            new Spec
            {
                HouseId = "HistoricalSociety",
                CaseName = "The Mask Keeper",
                Recovered = "The Hollow Creek Mask is back in its case with the other four, and the museum stays open.",
                ArcClue = "The last page of the case book: the Mask Keeper is unmasked, and every folklore mask is home under glass.",
                Rumours = new[] { "The museum's lights are on really late tonight. Somebody's in there.", "The oldest mask of all, the Hollow Creek Mask, is gone from its case! Everyone's talking about it." },
                Premise = "Someone at the Historical Society has been lending out the town's folklore masks, and tonight the oldest of them all, the Hollow Creek Mask, is missing from its case.",
                Motives = new[]
                {
                    "so the town would believe in the old legends again, and the museum he has guarded for thirty years would stay open",
                    "to bring the crowds back before the museum closed for good, one haunting at a time",
                    "to frighten the board into selling the building, masks and all, to his collector friend in the city",
                    "to make the Halloween fundraiser the busiest night her little tea room had ever seen",
                },
                MaxAccusations = 2,
                AlibiChecks = 2,
                Suspects = new[]
                {
                    S("Walter Finch", "Night watchman", "Has guarded the museum for thirty years and knows every creaky board and every key.",
                      "Says he was doing his rounds in the Archive all night.", "Archive"),
                    S("Edie Wren", "Curator", "Runs the museum on a shoestring and gives out full-size candy bars. Her fingers are always inky.",
                      "Claims she was cataloguing in the Reading Room until late.", "Reading Room"),
                    S("Mortimer Vane", "Society treasurer", "Keeps the books, and keeps telling the board the building should be sold.",
                      "Insists he left the board meeting and spent the evening at the Diner.", "Diner"),
                    S("Rosa Delgado", "Tea room volunteer", "Bakes for every fundraiser and runs the museum's little tea corner in the Gift Shop.",
                      "Says she was in the Gift Shop pricing raffle prizes.", "Gift Shop"),
                },
                TraitNames = new[] { "Brass keys", "Ink stains", "Ledger pages", "Cake crumbs", "Old paper dust", "Lantern oil", "Fountain pen", "Raffle tickets" },
                Clues = new[]
                {
                    C("WatchKeys", "Ring of brass keys", "The watchman's keys, every door in the building, dropped in a hurry."),
                    C("InkBlot", "Inky fingerprint", "A fresh, inky fingerprint on the glass of the mask case."),
                    C("LedgerPage", "Torn ledger page", "A page from the society's accounts, columns of sums circled in red."),
                    C("Crumbs", "Cake crumbs", "Crumbs of lemon drizzle cake, all the way along the gallery rope."),
                    C("PaperDust", "Old paper dust", "Grey dust from very old paper, the kind that lives in the archive and the reading room."),
                    C("LampOil", "Lantern oil", "A drip of lantern oil, from the kind of lamp you carry on rounds or into a cold storeroom."),
                    C("PenNib", "Fountain pen nib", "A gold fountain pen nib, snapped off. Only a few people here still write with one."),
                    C("Raffle", "Raffle tickets", "A strip of raffle tickets from the Halloween fundraiser, numbers 101 to 110."),
                },
                Gossip = new[]
                {
                    "I saw {0} by the mask cases after closing. They had a torch and a key.",
                    "{0} has been very interested in what the masks are worth lately.",
                    "Between you and me, {0} was the last one in the archive tonight.",
                    "{0} said they'd do anything to keep this place open. Anything!",
                },
            },
            // ---- Return visits: once a house's first case is solved, it calls again with a new mystery.
            // Same neighbours (same slots and outfits), new alibis, clues, gossip and motives. ----
            new Spec
            {
                HouseId = "PembertonCottage",
                Visit = 2,
                CaseName = "The Lost Love Letters",
                Recovered = "The letters are back in the Study desk, blue ribbon and all, and Mrs. Pemberton reads one aloud to the club.",
                Rumours = new[] { "Mrs. Pemberton's garden gnomes all turned round to face the window. All of them!", "My gran says Mrs. Pemberton had a secret admirer once. Ew." },
                Premise = "A bundle of letters from the late Mr. Pemberton has vanished from the Study desk, and every night since, the garden gnomes have turned to face the window.",
                Motives = new[]
                {
                    "to hide that the letters mention the money Mr. Pemberton lent him and never got back",
                    "to read what Grandma never told anyone about where the family's money went",
                    "to find the letter that promises the cottage to the town before it ruins his sale",
                    "because half the letters were written by her, and she'd rather nobody ever knew",
                },
                Suspects = new[]
                {
                    S("Hank Moody", "Handyman", "Back to fix the shed roof he 'definitely' fixed last time. Owes money all over town.",
                      "Says he was clearing leaves in the Back Garden until dark.", "Back Garden"),
                    S("Daisy Pemberton", "Granddaughter", "Staying the week to help Grandma, and asking a lot of questions about the old days.",
                      "Claims she was at the Bookshop in town choosing a birthday present.", "Bookshop"),
                    S("Leonard Crisp", "Estate agent", "Has a buyer lined up for the cottage the moment Mrs. Pemberton says yes.",
                      "Insists he was at the Post Office sending off the sale papers.", "Post Office"),
                    S("Beatrice Hollis", "Next-door neighbour", "Mrs. Pemberton's friend for fifty years. Keeps a lot of secrets, and keeps them well.",
                      "Says she was in the Living Room keeping Mrs. Pemberton company.", "Living Room"),
                },
                TraitNames = new[] { "Leaf mould", "Bookshop bag", "Sealing wax", "Rosewater", "Shed key", "Garden twine", "Postage stamps", "Fountain pen ink" },
                Clues = new[]
                {
                    C("LeafMould", "Leaf mould", "Damp black leaf mould trodden into the Study rug."),
                    C("BookshopBag", "Bookshop bag", "A crumpled paper bag from the Bookshop on Main Street."),
                    C("SealingWax", "Sealing wax", "A chip of red sealing wax, the kind used on official papers."),
                    C("Rosewater", "Rosewater", "The desk drawer smells of old-fashioned rosewater."),
                    C("ShedKey", "Shed key", "The little brass key to the garden shed, left in the desk."),
                    C("Twine", "Garden twine", "A length of green garden twine, like the bundle was tied with."),
                    C("Stamps", "Postage stamps", "A strip of new stamps, torn off in a hurry."),
                    C("Ink", "Fountain pen ink", "Blue-black ink on the blotter, still wet."),
                },
                Gossip = new[]
                {
                    "{0} was in that Study far too long this afternoon, if you ask me.",
                    "I'm sure I heard {0} reading something out loud. Something with 'my dearest' in it.",
                    "{0} always did want to know what was in that desk.",
                    "Ask {0} why they were so interested in the old postmarks.",
                },
            },
            new Spec
            {
                HouseId = "HollowCreekFarm",
                Visit = 2,
                CaseName = "The Stolen Seed Corn",
                Recovered = "The seed corn is back in the Barn, and next year's harvest is safe.",
                Rumours = new[] { "The scarecrow in the corn maze turns its head when you walk past. I SAW it.", "Mr. Hatcher says if they lose the seed corn, they lose the farm." },
                Premise = "The Hatchers' prize seed corn, saved from every harvest for a hundred years, has been stolen from the Barn, and the scarecrow in the maze now turns its head to watch whoever walks by.",
                Motives = new[]
                {
                    "to sell the seed corn quietly and pay off the debts he hasn't told his family about",
                    "to plant it on her own patch and win next year's ribbon all by herself",
                    "to ruin next year's harvest so the farm would have to sell to him",
                    "because only cornmeal from the old seed corn makes her prize muffins rise",
                },
                Suspects = new[]
                {
                    S("Abel Hatcher", "Farmer", "Worried about money since the prize display. Works later every night.",
                      "Says he was stacking bales in the Hayloft.", "Hayloft"),
                    S("Clementine Hatcher", "Harvest Queen", "Keeps her crown on even to feed the chickens. Wants a farm of her own one day.",
                      "Claims she was in the Sewing Room finishing her parade cape.", "Sewing Room"),
                    S("Silas Crane", "Land developer", "Still trying to buy the farm. Brought a new offer, and new shoes.",
                      "Insists he was at the Hardware store in town buying fence wire.", "Hardware"),
                    S("Ma Jessup", "Runs the pie stand", "Bakes for half the county and buys her cornmeal from nobody but the Hatchers.",
                      "Says she was at the Diner dropping off muffins.", "Diner"),
                },
                TraitNames = new[] { "Hay dust", "Sequins", "Fence wire", "Cornmeal", "Barn key", "Seed husks", "Satin ribbon", "Diner napkin" },
                Clues = new[]
                {
                    C("HayDust", "Hay dust", "A thick layer of hay dust on the seed bin's lid."),
                    C("Sequins", "Sequins", "Gold sequins scattered across the Barn floor."),
                    C("FenceWire", "Fence wire", "A coil of shiny new fence wire, never used."),
                    C("Cornmeal", "Cornmeal", "A trail of fine yellow cornmeal by the door."),
                    C("BarnKey", "Barn key", "The spare barn key, left in the padlock."),
                    C("SeedHusks", "Seed husks", "Husks from the old seed corn, caught in a cuff."),
                    C("Ribbon", "Satin ribbon", "A scrap of red satin ribbon on a nail."),
                    C("Napkin", "Diner napkin", "A paper napkin from the Diner with sums scribbled on it."),
                },
                Gossip = new[]
                {
                    "{0} was out by the Barn after dark. I saw a lantern.",
                    "Ask {0} what they'd do with a whole farm's worth of seed corn.",
                    "{0} has been counting money at the kitchen table all week.",
                    "I wouldn't trust {0} near that seed bin, not for a minute.",
                },
            },
            new Spec
            {
                HouseId = "WillowLaneVictorian",
                Visit = 2,
                CaseName = "The Silver Christening Cup",
                Recovered = "The christening cup is back in the Nursery, and the cradle has finally stopped rocking.",
                Rumours = new[] { "The cradle in that big house on Willow Lane rocks all by itself. Every. Night.", "Somebody stole a silver cup from the Ashcombes. It's two hundred years old!" },
                Premise = "The Ashcombe christening cup, solid silver and two hundred years old, is gone from the Nursery, and every night since, the empty cradle has rocked by itself.",
                Motives = new[]
                {
                    "to pawn it and pay for new headstones in the Family Plot, since nobody else would",
                    "to have it engraved with her own name before the family could argue over it",
                    "to add it to his collection, where it belongs, in his opinion",
                    "to hide the dent she put in it while polishing, before anyone noticed",
                },
                Suspects = new[]
                {
                    S("Ezra Cole", "Caretaker", "Looks after the house and the Family Plot. Says the old stones are crumbling.",
                      "Says he was in the Gazebo stringing up lanterns.", "Gazebo"),
                    S("Lavinia Ashcombe", "The last Ashcombe", "Has started labelling the family silver with her initials, 'just in case'.",
                      "Claims she was in the Tower Study writing letters.", "Tower Study"),
                    S("Dr. Felix Marlowe", "Music-box collector", "Came back for the music box, stayed for the silver.",
                      "Insists he was at the Library in town reading about silver marks.", "Library"),
                    S("Agnes Pratt", "Housekeeper", "Has polished the Ashcombe silver every Sunday for thirty years.",
                      "Says she was in the Kitchen polishing the rest of the silver.", "Kitchen"),
                },
                TraitNames = new[] { "Lantern soot", "Lilac powder", "Jeweller's loupe", "Polishing rag", "Nursery key", "Candle stubs", "Engraving dust", "Velvet lining" },
                Clues = new[]
                {
                    C("Soot", "Lantern soot", "Black soot smudged on the cradle's rail."),
                    C("Powder", "Lilac powder", "A dusting of lilac face powder on the windowsill."),
                    C("Loupe", "Jeweller's loupe", "A little magnifying eyepiece, the kind for reading hallmarks."),
                    C("Rag", "Polishing rag", "A grey polishing rag, stiff with silver polish."),
                    C("NurseryKey", "Nursery key", "The Nursery key, hung back on the wrong hook."),
                    C("Stubs", "Candle stubs", "Two burnt-down candle stubs under the cradle."),
                    C("Engraving", "Engraving dust", "Fine silver dust, like someone tried an engraving tool."),
                    C("Velvet", "Velvet lining", "A strip of blue velvet torn from the cup's case."),
                },
                Gossip = new[]
                {
                    "I heard {0} in the Nursery when the cradle started rocking.",
                    "{0} has been eyeing that cup since the day they arrived.",
                    "{0} knows exactly what the Ashcombe silver is worth. Exactly.",
                    "Ask {0} why the Nursery key was on the wrong hook.",
                },
            },
            new Spec
            {
                HouseId = "BlackwoodManor",
                Visit = 2,
                CaseName = "The Vanishing Portrait",
                Recovered = "Lady Blackwood's portrait is back in the Portrait Gallery, and the organ in the Cellar is quiet at last.",
                Rumours = new[] { "There's an organ in the Blackwood cellar that plays at midnight. Nobody's touched it in fifty years.", "A whole painting disappeared from the manor. Right off the wall!" },
                Premise = "Lady Blackwood's portrait has vanished from the Portrait Gallery, leaving a pale square on the wallpaper, and the old organ in the Cellar plays by itself at midnight.",
                Motives = new[]
                {
                    "to get at the wall safe behind it, where he swears his unpaid wages are kept",
                    "to hide that the portrait shows the pearl necklace she has already sold",
                    "to sell the painting to his buyer in the city, frame and all",
                    "to find the recipe book Lady Blackwood hid behind the frame years ago",
                },
                Suspects = new[]
                {
                    S("Gus Thornbury", "Groundskeeper", "Forty years on the grounds and, he says, ten years of wages owed.",
                      "Says he was raking leaves in the Cemetery.", "Cemetery"),
                    S("Vivian Blackwood", "Heiress", "Owns the manor now. Owns slightly less of what's in it than she used to.",
                      "Claims she was in the Master Bedroom with a headache.", "Master Bedroom"),
                    S("Reginald Pike", "Rival antiques dealer", "Has a buyer in the city who wants 'anything old and Blackwood'.",
                      "Insists he was at the Barber in town having a shave.", "Barber"),
                    S("Martha Bunce", "Cook", "Has been looking for Lady Blackwood's lost recipe book her whole life.",
                      "Says she was in the Cellar fetching jars of preserves.", "Cellar"),
                },
                TraitNames = new[] { "Wet leaves", "Face powder", "Picture wire", "Jam stains", "Gallery key", "Cellar cobwebs", "Gilt flakes", "Brass screws" },
                Clues = new[]
                {
                    C("WetLeaves", "Wet leaves", "Wet autumn leaves on the gallery floor."),
                    C("FacePowder", "Face powder", "A smudge of pale face powder on the empty wall."),
                    C("PictureWire", "Picture wire", "A cut length of new picture wire."),
                    C("Jam", "Jam stains", "Sticky blackberry jam on the skirting board."),
                    C("GalleryKey", "Gallery key", "The Portrait Gallery key, left in the lock."),
                    C("Cobwebs", "Cellar cobwebs", "Thick cellar cobwebs caught on the picture hook."),
                    C("Gilt", "Gilt flakes", "Flakes of gold leaf from a heavy frame."),
                    C("Screws", "Brass screws", "Two brass screws, unscrewed from the frame's back."),
                },
                Gossip = new[]
                {
                    "{0} was in the Portrait Gallery at dusk. I'd swear to it.",
                    "{0} has always hated that painting. Always.",
                    "Ask {0} about the safe. Go on, ask.",
                    "{0} came up from the Cellar covered in cobwebs. Explain that.",
                },
            },
        };

        static readonly Dictionary<string, Spec> byId = new();

        /// <summary>
        /// A case by id: a house id ("PembertonCottage") is that house's first case, "PembertonCottage#2"
        /// its return visit. Falls back to the house's first case, then to Blackwood Manor's.
        /// </summary>
        public static Spec For(string caseId)
        {
            if (byId.Count == 0)
                foreach (var s in All) byId[s.CaseId] = s;
            if (!string.IsNullOrEmpty(caseId))
            {
                if (byId.TryGetValue(caseId, out var found)) return found;
                if (byId.TryGetValue(HouseOf(caseId), out found)) return found;
            }
            return byId[DefaultHouse];
        }

        /// <summary>The house a case is set in: "PembertonCottage#2" -> "PembertonCottage".</summary>
        public static string HouseOf(string caseId)
        {
            if (string.IsNullOrEmpty(caseId)) return caseId;
            int hash = caseId.IndexOf('#');
            return hash < 0 ? caseId : caseId.Substring(0, hash);
        }

        /// <summary>
        /// Which case a house's call is about: its first case, then (once that's solved) the next visit.
        /// When every visit is solved it's the last one again, so a house can always be replayed.
        /// </summary>
        public static string NextCase(string houseId, System.Func<string, bool> isSolved)
        {
            string last = houseId;
            for (int visit = 1; visit <= 9; visit++)
            {
                string id = visit == 1 ? houseId : houseId + "#" + visit;
                if (visit > 1 && !HasCase(id)) break;
                last = id;
                if (!isSolved(id)) return id;
            }
            return last;
        }

        static bool HasCase(string id)
        {
            if (byId.Count == 0) For(DefaultHouse);
            return byId.ContainsKey(id);
        }

        /// <summary>The keepsake each solved case leaves on the HQ shelf.</summary>
        public static string KeepsakeOf(string houseId) => houseId switch
        {
            "PembertonCottage" => "the Harvest Lantern's spare wick",
            "HollowCreekFarm" => "a blue prize rosette",
            "WillowLaneVictorian" => "a recital programme",
            "BlackwoodManor" => "a copy of the ledger's first page",
            "HistoricalSociety" => "the Hollow Creek Mask's old museum label",
            _ => "a souvenir",
        };

        // ---- The Mask Keeper: the story that runs through every case ----

        /// <summary>Shown in the case book while the arc is still open.</summary>
        public const string ArcQuestion =
            "Four masks, four culprits, and none of them took a mask on their own. Who has been lending out Hollow Creek's folklore masks?";

        /// <summary>The fifth call: it only appears on the call board once the other four cases are solved.</summary>
        public const string FinaleCase = "HistoricalSociety";

        /// <summary>The four cases that each give a clue to the Mask Keeper.</summary>
        public static readonly string[] ArcCases = { "PembertonCottage", "HollowCreekFarm", "WillowLaneVictorian", "BlackwoodManor" };

        /// <summary>Told once the four cases are solved: every clue points to one place.</summary>
        public const string ArcFinale =
            "Every clue points the same way: a loan tag, inky fingers, lavender and old paper, a key to the back door. " +
            "The Mask Keeper is someone at the Hollow Creek Historical Society, and tonight the oldest mask of all has gone missing. " +
            "A new call is on the board: The Mask Keeper, 1 Founders Way.";

        /// <summary>Told once the Mask Keeper is unmasked.</summary>
        public const string ArcEpilogue =
            "THE MASK KEEPER IS UNMASKED. All five masks are back under glass, the museum stays open, and the plaque by the " +
            "gallery door has a new line on it: the names of the Mystery Club.";

        /// <summary>The intro case: the first call of a new club is always this one.</summary>
        public const string FirstCase = "PembertonCottage";

        /// <summary>Why this suspect wore the mask at this house ("" if the case has no motives).</summary>
        public static string MotiveOf(string houseId, string suspectId)
        {
            var spec = For(houseId);
            int i = System.Array.IndexOf(Slots, suspectId);
            return spec.Motives != null && i >= 0 && i < spec.Motives.Length ? spec.Motives[i] : "";
        }

        /// <summary>How the Suspect Board names a trait at this house.</summary>
        public static string TraitName(string houseId, Trait trait)
        {
            int i = System.Array.IndexOf(Bits, trait);
            var spec = For(houseId);
            return i >= 0 && i < spec.TraitNames.Length ? spec.TraitNames[i] : trait.ToString();
        }

        /// <summary>Builds the playable case for a house (server).</summary>
        public static CaseDefinition Build(string houseId)
        {
            var spec = For(houseId);
            var c = ScriptableObject.CreateInstance<CaseDefinition>();
            c.name = "Case_" + spec.CaseId.Replace('#', '_');
            c.CaseName = spec.CaseName;
            c.MaxSeededClues = spec.MaxSeededClues;
            c.MaxAccusations = spec.MaxAccusations;
            c.AlibiChecks = spec.AlibiChecks;
            c.LeakChanceMultiplier = spec.LeakChanceMultiplier;

            for (int i = 0; i < Slots.Length; i++)
            {
                var p = spec.Suspects[i];
                var s = ScriptableObject.CreateInstance<SuspectDefinition>();
                s.name = Slots[i];
                s.Id = Slots[i];
                s.DisplayName = p.Name;
                s.Occupation = p.Job;
                s.Bio = p.Bio;
                s.Alibi = p.Alibi;
                s.AlibiRoom = p.AlibiRoom;
                s.Traits = SlotTraits[i];
                c.Suspects.Add(s);
            }

            // Unique traits (bits 0-3) are the smoking guns: not hidden at the start, so they mostly
            // come from the Haunter's own slip-ups. Shared traits (bits 4-7) take two to be sure.
            for (int i = 0; i < Bits.Length; i++)
            {
                var q = spec.Clues[i];
                var clue = ScriptableObject.CreateInstance<ClueDefinition>();
                clue.name = q.Id;
                clue.Id = q.Id;
                clue.DisplayName = q.Name;
                clue.Description = q.Description;
                clue.Traits = Bits[i];
                clue.CanBeSeeded = i >= 4;
                c.Clues.Add(clue);
            }
            return c;
        }
    }
}
