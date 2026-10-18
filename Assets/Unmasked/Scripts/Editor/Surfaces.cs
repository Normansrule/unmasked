using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Unmasked.EditorTools
{
    /// <summary>
    /// Surface detail for the generated levels: clapboard siding, shingles, brick, stone, floorboards,
    /// grass, asphalt and so on. Each is a small greyscale pattern (Assets/Unmasked/Textures/Surfaces,
    /// written by Docs/tools/make_textures.py) that the ToonSpooky shader lays over a box's colour in
    /// world space, so boards and bricks stay the same size on every wall.
    /// </summary>
    internal static class Surfaces
    {
        const string Dir = "Assets/Unmasked/Textures/Surfaces";

        [Serializable] class Entry { public string id; public string texture; public float tile = 2f; public float strength = 0.8f; public bool swapTop; }
        [Serializable] class Table { public Entry[] surfaces; }

        static Dictionary<string, Entry> table;
        static readonly Dictionary<string, Texture2D> textures = new();

        static Entry Find(string id)
        {
            if (table == null)
            {
                table = new Dictionary<string, Entry>();
                string path = Dir + "/surfaces.json";
                if (File.Exists(path))
                    foreach (var e in JsonUtility.FromJson<Table>(File.ReadAllText(path)).surfaces ?? new Entry[0])
                        table[e.id] = e;
                else
                    Debug.LogWarning($"[Unmasked] {path} is missing, so walls and roofs are plain. Run: python3 Docs/tools/make_textures.py");
            }
            return table.TryGetValue(id, out var found) ? found : null;
        }

        static Texture2D Texture(string name)
        {
            if (textures.TryGetValue(name, out var cached) && cached != null) return cached;
            string path = $"{Dir}/{name}.png";
            if (AssetImporter.GetAtPath(path) is TextureImporter importer)
            {
                // The patterns are data (mid-grey = no change), not colours, so no sRGB conversion.
                if (importer.sRGBTexture || importer.wrapMode != TextureWrapMode.Repeat || importer.anisoLevel < 4)
                {
                    importer.sRGBTexture = false;
                    importer.wrapMode = TextureWrapMode.Repeat;
                    importer.anisoLevel = 4;
                    importer.mipmapEnabled = true;
                    importer.SaveAndReimport();
                }
            }
            return textures[name] = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        /// <summary>Gives a ToonSpooky material the named surface pattern.</summary>
        internal static void Apply(Material mat, string id)
        {
            var e = Find(id);
            if (e == null || !mat.HasProperty("_PatternTex")) return;
            var tex = Texture(e.texture);
            if (tex == null) return;
            mat.SetTexture("_PatternTex", tex);
            mat.SetFloat("_PatternTile", Mathf.Max(0.05f, e.tile));
            mat.SetFloat("_PatternStrength", e.strength);
            mat.SetFloat("_PatternSwap", e.swapTop ? 1f : 0f);
        }
    }
}
