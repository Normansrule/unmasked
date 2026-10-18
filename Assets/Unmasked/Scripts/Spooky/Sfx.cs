using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Plays the game's sounds (Resources/Sounds/*.wav, made by Docs/tools/make_sounds.py) by name.
    /// Purely cosmetic and local to each machine: call it from code that already runs everywhere
    /// (client RPCs, SpookyFX, Update).
    /// </summary>
    public static class Sfx
    {
        /// <summary>Master volume for every sound (0..1).</summary>
        public static float Volume = 1f;

        static readonly Dictionary<string, AudioClip> clips = new();

        public static AudioClip Clip(string name)
        {
            if (string.IsNullOrEmpty(name)) return null;
            if (!clips.TryGetValue(name, out var clip))
            {
                clip = Resources.Load<AudioClip>("Sounds/" + name);
                clips[name] = clip;
            }
            return clip;
        }

        /// <summary>A one-shot in the world: louder close by, silent past range.</summary>
        public static AudioSource Play(string name, Vector3 at, float volume = 1f, float range = 30f, float pitch = 1f)
        {
            var clip = Clip(name);
            if (clip == null) return null;
            var go = new GameObject("Sfx_" + name);
            go.transform.position = at;
            var source = Setup(go.AddComponent<AudioSource>(), clip, volume, pitch, range, true);
            source.Play();
            Object.Destroy(go, clip.length / Mathf.Max(0.1f, pitch) + 0.1f);
            return source;
        }

        /// <summary>A one-shot everyone hears at full volume wherever they are (stings, thunder).</summary>
        public static AudioSource Play2D(string name, float volume = 1f, float pitch = 1f)
        {
            var clip = Clip(name);
            if (clip == null) return null;
            var go = new GameObject("Sfx2D_" + name);
            var source = Setup(go.AddComponent<AudioSource>(), clip, volume, pitch, 30f, false);
            source.Play();
            Object.Destroy(go, clip.length / Mathf.Max(0.1f, pitch) + 0.1f);
            return source;
        }

        /// <summary>A looping source on a transform (null parent = a 2D loop). Starts silent if volume is 0.</summary>
        public static AudioSource Loop(string name, Transform parent, float volume, bool spatial, float range = 30f)
        {
            var clip = Clip(name);
            if (clip == null) return null;
            var go = new GameObject("Loop_" + name);
            if (parent != null) go.transform.SetParent(parent, false);
            var source = Setup(go.AddComponent<AudioSource>(), clip, volume, 1f, range, spatial);
            source.loop = true;
            source.time = Random.Range(0f, clip.length * 0.9f); // two machines' loops don't line up
            source.Play();
            return source;
        }

        static AudioSource Setup(AudioSource s, AudioClip clip, float volume, float pitch, float range, bool spatial)
        {
            s.clip = clip;
            s.volume = Mathf.Clamp01(volume * Volume);
            s.pitch = pitch;
            s.playOnAwake = false;
            s.dopplerLevel = 0f;
            s.spatialBlend = spatial ? 1f : 0f;
            s.rolloffMode = AudioRolloffMode.Linear;
            s.minDistance = Mathf.Min(3f, range * 0.2f);
            s.maxDistance = range;
            return s;
        }

        /// <summary>What a possessed object sounds like.</summary>
        public static void PlayAction(PossessedAction action, Vector3 at)
        {
            switch (action)
            {
                case PossessedAction.Rattle: Play("rattle", at, 0.9f, 22f, Random.Range(0.9f, 1.15f)); break;
                case PossessedAction.Launch: Play("whoosh", at, 1f, 25f, Random.Range(0.9f, 1.1f)); break;
                case PossessedAction.Slam: Play("door_slam", at, 1f, 35f, Random.Range(0.9f, 1.05f)); break;
                case PossessedAction.Flicker: Play("buzz", at, 0.7f, 18f); break;
                case PossessedAction.CutPower: Play("power_down", at, 0.9f, 30f); break;
            }
        }
    }
}
