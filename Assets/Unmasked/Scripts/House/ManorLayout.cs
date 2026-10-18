using System;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Blackwood Manor as data: Assets/Unmasked/Resources/BlackwoodManor.json, written by
    /// Docs/tools/make_manor.py. The editor builds the 3D level from it (Unmasked > Build Blackwood
    /// Manor), the README renderer draws it, and at runtime it answers "which room am I in?".
    /// </summary>
    [Serializable]
    public class ManorLayout
    {
        /// <summary>sf: the surface pattern (siding, shingle, brick, stone, planks, grass, road...; see Docs/tools/make_textures.py).</summary>
        [Serializable] public class Box { public string n; public string t; public float[] p; public float[] s; public float[] r; public float[] c; public string m; public int l; public string g; public string sf; }
        [Serializable] public class Door { public string n; public float[] p; public float ry; public float w; public float h; public int l; }
        [Serializable] public class Trapdoor { public string n; public float[] p; public float[] drop; }
        [Serializable] public class Possessable { public string n; public string t; public float[] p; public float[] s; public float[] c; public bool phys; public int l; }
        [Serializable] public class LightSpec { public string n; public float[] p; public float[] c; public float range; public float intensity; public int l; public string ft; public float[] fo; public float[] fs; public float[] fc; }
        [Serializable] public class Suspect { public string id; public float[] p; public float[] c; public float ry; }
        /// <summary>A Halloween prop from Costumes.json: k is its id (jack, pumpkin, candle, cobweb, scarecrow...).</summary>
        [Serializable] public class Decor { public string k; public float[] p; public float ry; public float sc = 1f; public int l; }
        /// <summary>A flickering decorative light (jack-o'-lantern trail, candles, wisps). Not possessable.</summary>
        [Serializable] public class Glow { public float[] p; public float[] c; public float range; public float intensity; public int l; }
        [Serializable] public class Point { public float[] p; }
        [Serializable] public class Room { public string n; public int l; public float[] min; public float[] max; }

        public string name;
        /// <summary>Houses in Hollow Creek (make_houses.py) also carry these; the manor leaves them empty.</summary>
        public string id, style, size, blurb;
        public int floors;
        public Box[] boxes;
        public Door[] doors;
        public Trapdoor[] trapdoors;
        public Possessable[] possessables;
        public LightSpec[] lights;
        public Suspect[] suspects;
        public Point[] clueSpots;
        public Point[] trapPieces;
        public Point trapSite;
        public Point[] solverSpawns;
        public Point haunterSpawn;
        public Room[] rooms;
        public Decor[] decor;
        public Glow[] glows;

        public const string ResourceName = "BlackwoodManor";

        static ManorLayout cached;
        static bool triedLoading;

        /// <summary>The manor layout, or null if the JSON isn't in Resources.</summary>
        public static ManorLayout Current
        {
            get
            {
                if (!triedLoading)
                {
                    triedLoading = true;
                    var text = Resources.Load<TextAsset>(ResourceName);
                    if (text != null) cached = JsonUtility.FromJson<ManorLayout>(text.text);
                }
                return cached;
            }
        }

        public static ManorLayout Parse(string json) => JsonUtility.FromJson<ManorLayout>(json);

        public static Vector3 V(float[] a) => a != null && a.Length >= 3 ? new Vector3(a[0], a[1], a[2]) : Vector3.zero;
        public static Color C(float[] a) => a != null && a.Length >= 3 ? new Color(a[0], a[1], a[2]) : Color.white;

        /// <summary>The smallest room containing the point (rooms nest: the greenhouse is inside the grounds).</summary>
        public Room RoomAt(Vector3 point)
        {
            Room best = null;
            float bestVolume = float.MaxValue;
            if (rooms == null) return null;
            foreach (var room in rooms)
            {
                Vector3 min = V(room.min), max = V(room.max);
                if (point.x < min.x || point.y < min.y - 0.5f || point.z < min.z || point.x > max.x || point.y > max.y || point.z > max.z) continue;
                float volume = (max.x - min.x) * (max.y - min.y) * (max.z - min.z);
                if (volume < bestVolume) { best = room; bestVolume = volume; }
            }
            return best;
        }

        public static string FloorName(int level) => level switch
        {
            -1 => "Cellar",
            0 => "Ground floor",
            1 => "Upstairs",
            9 => "Outside",
            _ => ""
        };

        /// <summary>Just the room's name ("Library", or around Hollow Creek "Bookshop"); "" if none.</summary>
        public static string RoomNameAt(Vector3 point)
        {
            if (TownDirector.Instance != null && TownLayout.Current != null) return TownLayout.Current.RoomNameAt(point);
            return Current?.RoomAt(point)?.n ?? "";
        }

        /// <summary>"Library, ground floor", or "" when there's no layout or no room there.</summary>
        public static string Describe(Vector3 point)
        {
            // In Hollow Creek every house has its own layout; the town knows which lot you're on.
            if (TownDirector.Instance != null && TownLayout.Current != null) return TownLayout.Current.Describe(point);
            var room = Current?.RoomAt(point);
            if (room == null) return "";
            if (room.l == 9 || room.l == -1) return room.n;
            return $"{room.n}, {FloorName(room.l).ToLowerInvariant()}";
        }
    }
}
