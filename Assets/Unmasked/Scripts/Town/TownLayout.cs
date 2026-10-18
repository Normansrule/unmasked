using System;
using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Hollow Creek as data: Assets/Unmasked/Resources/HollowCreek.json, written by
    /// Docs/tools/make_town.py. The town geometry uses the same format as the houses (ManorLayout);
    /// this class reads the parts only the town has: the house lots, Mystery Club HQ and the night
    /// events. The editor builds the town from it (Unmasked > Build Hollow Creek), the in-game map
    /// draws its pins from it, and it answers "where am I?" anywhere in town.
    /// </summary>
    [Serializable]
    public class TownLayout
    {
        [Serializable] public class Area { public float[] min; public float[] max; }
        [Serializable] public class Placed { public float[] p; public float ry; }

        /// <summary>One haunted house on its lot. offset is where the house's own origin sits in town.</summary>
        [Serializable]
        public class Lot
        {
            public string id, resource, name, style, size, blurb, street;
            public int difficulty, floors, rooms, pieces, area;
            public float[] offset, center, arrival;
            public Area lot;
            public Afterglow afterglow;

            public Vector3 Offset => ManorLayout.V(offset);
            public Vector3 Center => ManorLayout.V(center);
            public Vector3 Arrival => ManorLayout.V(arrival);
            public Vector2 Min => new(lot.min[0], lot.min[1]);
            public Vector2 Max => new(lot.max[0], lot.max[1]);
            public bool Contains(Vector3 p) => p.x >= lot.min[0] && p.x <= lot.max[0] && p.z >= lot.min[1] && p.z <= lot.max[1];
        }

        /// <summary>The street remembers (HouseMood): the front-yard party once the house's case is solved.</summary>
        [Serializable]
        public class Afterglow
        {
            [Serializable] public class Item { public string k; public float[] p; public float ry, sc; }
            public Item[] items;
            public float[] banner, haunt;
            public float bannerWidth;
            public string bannerText;
        }

        [Serializable] public class EventInfo { public string id, name, blurb; public float[] color; }

        [Serializable]
        public class Hq
        {
            public ManorLayout.Point[] spawns;
            public ManorLayout.Point haunter;
            public Placed van;
            public Placed board;
            public Placed trunk;
            /// <summary>Where each case's keepsake sits on the HQ shelf.</summary>
            public Keepsake[] keepsakes;
        }

        [Serializable] public class Keepsake { public string house; public float[] p; }

        /// <summary>What lies beyond the edge of the map (Horizon.cs builds it).</summary>
        [Serializable]
        public class HorizonInfo
        {
            [Serializable] public class Ring { public float radius; public float[] color; public float @base; public float[] waves; }
            [Serializable] public class Landmark { public string kind, name; public float angle, size; public int ring; }
            [Serializable] public class Lights { public int count, seed; public float[] colors; }
            [Serializable] public class Road { public string name, sign; public float[] from, to; }
            [Serializable] public class Forest { public float inner, outer; public int count, seed; public float[] town; }
            public Ring[] rings;
            public Landmark[] landmarks;
            public Lights lights;
            public Road[] roads;
            public float roadWidth, lampEvery;
            public Forest forest;
        }

        /// <summary>Life in town (TownLife.cs): trick-or-treaters, cars on the roads out, a far-off train.</summary>
        [Serializable]
        public class LifeInfo
        {
            [Serializable] public class Walk { public string name; public float[] from, to; public float side; }
            [Serializable] public class Costume { public string kind; public float[] body, accent; }
            [Serializable] public class Train { public float radius, y, from, to, speed; public int cars; }
            public Walk[] walks;
            public int groups, seed, cars, carSeed;
            public Costume[] costumes;
            public string[] rumours;
            public float[] carSpeed;
            public Train train;
        }

        /// <summary>
        /// A grown-up out in town tonight (Townsperson.cs): what they say, and the errand they give the
        /// club. item is a prop id from Costumes.json, itemP where it ended up.
        /// </summary>
        [Serializable]
        public class Folk
        {
            public string id, name, job, item, itemName, ask, thanks;
            /// <summary>Their thank-you gift: a piece of the Lantern Watch costume (MysteryGameManager.WatchPieces).</summary>
            public string piece, pieceName, pieceBlurb;
            public float[] p, itemP;
            public float ry, itemRy;
            public string[] lines;
        }

        public string name;
        public LifeInfo life;
        public Folk[] folk;
        public Lot[] lots;
        public EventInfo[] events;
        public Hq hq;
        public HorizonInfo horizon;
        public ManorLayout.Room[] rooms;
        public float creekZ;

        public const string ResourceName = "HollowCreek";

        static TownLayout cached;
        static bool triedLoading;
        static readonly Dictionary<string, ManorLayout> houses = new();

        /// <summary>One of the townsfolk by id, or null.</summary>
        public Folk FolkById(string id)
        {
            if (folk != null)
                foreach (var f in folk)
                    if (f.id == id) return f;
            return null;
        }

        public static TownLayout Current
        {
            get
            {
                if (!triedLoading)
                {
                    triedLoading = true;
                    var text = Resources.Load<TextAsset>(ResourceName);
                    if (text != null) cached = Parse(text.text);
                }
                return cached;
            }
        }

        public static TownLayout Parse(string json) => JsonUtility.FromJson<TownLayout>(json);

        public Lot FindLot(string id)
        {
            if (lots == null || string.IsNullOrEmpty(id)) return null;
            foreach (var lot in lots) if (lot.id == id) return lot;
            return null;
        }

        public Lot LotAt(Vector3 point)
        {
            if (lots == null) return null;
            foreach (var lot in lots) if (lot.Contains(point)) return lot;
            return null;
        }

        /// <summary>A house's own layout (room names, floors), loaded from Resources once.</summary>
        public static ManorLayout HouseLayout(Lot lot)
        {
            if (lot == null) return null;
            if (houses.TryGetValue(lot.id, out var layout)) return layout;
            var text = Resources.Load<TextAsset>(lot.resource);
            layout = text != null ? ManorLayout.Parse(text.text) : null;
            houses[lot.id] = layout;
            return layout;
        }

        public EventInfo For(NightEvent e)
        {
            if (events == null) return null;
            string id = e.ToString();
            foreach (var info in events) if (info.id == id) return info;
            return null;
        }

        public static string EventName(NightEvent e) => Current?.For(e)?.name ?? e.ToString();
        public static string EventBlurb(NightEvent e) => Current?.For(e)?.blurb ?? "";

        /// <summary>"Kitchen, ground floor (Pemberton Cottage)", "Town Square" or "".</summary>
        public string Describe(Vector3 point)
        {
            var lot = LotAt(point);
            if (lot != null)
            {
                var room = HouseLayout(lot)?.RoomAt(point - lot.Offset);
                if (room == null) return lot.name;
                string floor = room.l == 9 || room.l == -1 ? "" : ", " + ManorLayout.FloorName(room.l).ToLowerInvariant();
                return $"{room.n}{floor} ({lot.name})";
            }

            return TownRoomAt(point)?.n ?? "";
        }

        /// <summary>The smallest town place (street, shop, square) containing the point, seen from above.</summary>
        public ManorLayout.Room TownRoomAt(Vector3 point)
        {
            ManorLayout.Room best = null;
            float bestArea = float.MaxValue;
            if (rooms != null)
                foreach (var room in rooms)
                {
                    if (point.x < room.min[0] || point.x > room.max[0] || point.z < room.min[2] || point.z > room.max[2]) continue;
                    float area = (room.max[0] - room.min[0]) * (room.max[2] - room.min[2]);
                    if (area < bestArea) { best = room; bestArea = area; }
                }
            return best;
        }

        /// <summary>Just the room's name ("Kitchen", "Bookshop"), in a house or around town; "" if none.</summary>
        public string RoomNameAt(Vector3 point)
        {
            var lot = LotAt(point);
            if (lot != null) return HouseLayout(lot)?.RoomAt(point - lot.Offset)?.n ?? "";
            return TownRoomAt(point)?.n ?? "";
        }
    }
}
