using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Small signs of life on the shape-built faces (make_costumes.py face()): the eyelids blink every
    /// few seconds (the lashes riding on them), the eyes glance at whoever is nearest the camera, and
    /// the lips move and the brows lift a little while someone talks. Works on every outfit under
    /// this object, so it follows a suspect's outfit swaps. Purely
    /// cosmetic and local; PawnAnimator adds it to every pawn and townsfolk can add it themselves.
    /// </summary>
    public class FaceLife : MonoBehaviour
    {
        class Feature
        {
            public Transform T;
            public Vector3 Pos, Scale;
        }

        readonly List<Feature> lids = new(), lashes = new(), eyes = new(), lips = new(), brows = new();
        float nextBlink, blinkAt = -10f, talkFrom = -10f, talkUntil = -10f, nextScan;
        Vector2 look, lookTarget;
        float nextGlance;

        const float BlinkTime = 0.14f;

        void Start()
        {
            Scan();
            nextBlink = Time.time + Random.Range(1f, 4f);
        }

        /// <summary>Find the face parts again (outfits get switched on and off).</summary>
        void Scan()
        {
            lids.Clear();
            lashes.Clear();
            eyes.Clear();
            lips.Clear();
            brows.Clear();
            foreach (var t in GetComponentsInChildren<Transform>(false))
            {
                string n = t.name;
                var list = n == "LidL" || n == "LidR" ? lids
                    : n == "LashL" || n == "LashR" ? lashes
                    : n == "EyeL" || n == "EyeR" || n == "IrisL" || n == "IrisR" || n == "PupilL" || n == "PupilR" || n == "GlintL" || n == "GlintR" ? eyes
                    : n == "Lips" ? lips
                    : n == "BrowL" || n == "BrowR" ? brows : null;
                if (list != null) list.Add(new Feature { T = t, Pos = t.localPosition, Scale = t.localScale });
            }
            nextScan = Time.time + 3f;
        }

        /// <summary>Lips move for a while, starting after a delay (after the hesitation before an answer).</summary>
        public void Talk(float seconds, float delay = 0f)
        {
            talkFrom = Time.time + delay;
            talkUntil = talkFrom + seconds;
        }

        void LateUpdate()
        {
            if (Time.time >= nextScan) Scan();
            float now = Time.time;

            // Blink: a quick close and open, sometimes twice in a row.
            if (now >= nextBlink)
            {
                blinkAt = now;
                nextBlink = now + (Random.value < 0.15f ? 0.3f : Random.Range(2.2f, 5.5f));
            }
            float b = Mathf.Clamp01((now - blinkAt) / BlinkTime);
            float closed = b < 1f ? Mathf.Sin(b * Mathf.PI) : 0f;
            foreach (var f in lids)
            {
                if (f.T == null) continue;
                // The lid sits just above the eye: slide it down over the eye and stretch it to cover.
                f.T.localPosition = f.Pos + Vector3.down * 0.024f * closed;
                f.T.localScale = Vector3.Scale(f.Scale, new Vector3(1f, 1f + 1.2f * closed, 1.1f));
            }
            // The lashes ride on the lid's lower edge.
            foreach (var f in lashes)
                if (f.T != null) f.T.localPosition = f.Pos + Vector3.down * 0.034f * closed;

            // Glances: look at the camera when it's close, otherwise wander now and then.
            var cam = Camera.main;
            if (now >= nextGlance)
            {
                nextGlance = now + Random.Range(1.2f, 3.5f);
                lookTarget = Random.insideUnitCircle * 0.7f;
                if (cam != null && Vector3.Distance(cam.transform.position, transform.position) < 9f)
                {
                    var local = transform.InverseTransformPoint(cam.transform.position);
                    lookTarget = new Vector2(Mathf.Clamp(local.x * 0.4f, -1f, 1f), Mathf.Clamp((local.y - 1.7f) * 0.4f, -1f, 1f));
                }
            }
            look = Vector2.Lerp(look, lookTarget, 1f - Mathf.Exp(-14f * Time.deltaTime));
            var offset = new Vector3(look.x * 0.012f, look.y * 0.008f, 0f);
            foreach (var f in eyes)
                if (f.T != null) f.T.localPosition = f.Pos + offset;

            // Talking: the lips open and close in an uneven rhythm. They're a capsule turned on its
            // side, so its local x is the mouth's height.
            bool talking = now >= talkFrom && now < talkUntil;
            float open = talking ? Mathf.Abs(Mathf.Sin(now * 13f) * 0.6f + Mathf.Sin(now * 7.3f) * 0.4f) : 0f;
            foreach (var f in lips)
                if (f.T != null) f.T.localScale = Vector3.Scale(f.Scale, new Vector3(1f + 1.6f * open, 1f, 1f));
            foreach (var f in brows)
                if (f.T != null) f.T.localPosition = f.Pos + Vector3.up * 0.006f * open;
        }
    }
}
