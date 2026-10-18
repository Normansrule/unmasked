using System;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Every character and Halloween prop as data: Assets/Unmasked/Resources/Costumes.json, written by
    /// Docs/tools/make_costumes.py. The editor builds the models from it, the README renderer draws the
    /// same models, and at runtime it gives the villains their names, legends and powers.
    /// </summary>
    [Serializable]
    public class Costumes
    {
        /// <summary>One shape. t: box, sphere, cyl, capsule. m: solid, emissive, ghost. k: "mask" for the mask.</summary>
        [Serializable] public class Part { public string n; public string t; public float[] p; public float[] s; public float[] r; public float[] c; public string m; public float e; public string k; }

        [Serializable]
        public class Villain
        {
            public string id, name, origin, legend, power, powerBlurb;
            public float speed = 1f, hover;
            public float[] glow, mask;
            public Part[] parts;
        }

        [Serializable] public class Prop { public string id; public Part[] parts; public float[] glow; public float glowY; }
        [Serializable] public class Outfit { public string id; public Part[] parts; }

        public Villain[] villains;
        public Prop[] props;
        public Outfit[] suspects;
        public Outfit[] solvers;
        /// <summary>The Lantern Watch pieces for each Solver role: "Sleuth.Sash", "Brawn.Badge"...</summary>
        public Outfit[] watch;

        public const string ResourceName = "Costumes";

        static Costumes cached;
        static bool triedLoading;

        public static Costumes Current
        {
            get
            {
                if (!triedLoading)
                {
                    triedLoading = true;
                    var text = Resources.Load<TextAsset>(ResourceName);
                    if (text != null) cached = JsonUtility.FromJson<Costumes>(text.text);
                }
                return cached;
            }
        }

        public static Costumes Parse(string json) => JsonUtility.FromJson<Costumes>(json);

        public static Villain For(VillainKind kind)
        {
            var all = Current?.villains;
            if (all != null)
                foreach (var v in all)
                    if (v.id == kind.ToString()) return v;
            return null;
        }

        public static string NameOf(VillainKind kind) => For(kind)?.name ?? kind switch
        {
            VillainKind.HeadlessHorseman => "The Headless Horseman",
            VillainKind.Banshee => "The Banshee",
            VillainKind.StingyJack => "Stingy Jack",
            VillainKind.BabaYaga => "Baba Yaga",
            _ => kind.ToString()
        };

        public static string PowerOf(VillainKind kind) => For(kind)?.power ?? kind switch
        {
            VillainKind.HeadlessHorseman => "Pumpkin Toss",
            VillainKind.Banshee => "Wail",
            VillainKind.StingyJack => "Wisp Lure",
            VillainKind.BabaYaga => "Hex",
            _ => "Signature"
        };

        public Prop FindProp(string id)
        {
            if (props != null) foreach (var p in props) if (p.id == id) return p;
            return null;
        }

        public static Part[] FindOutfit(Outfit[] list, string id)
        {
            if (list != null) foreach (var o in list) if (o.id == id) return o.parts;
            return null;
        }
    }
}
