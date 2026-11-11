using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unmasked
{
    /// <summary>
    /// The club camera (round 37). Press P to take a snapshot: a flash, a shutter click, and the
    /// picture develops on a little instant-photo card in the corner. If one of the album's thirteen
    /// sights is in the frame (each landmark, a neighbour, a will-o'-the-wisp, the Hook Board, your
    /// porch of jack-o'-lanterns), the photo goes in the Club Book's Snapshots tab under its name.
    /// Neighbours in the frame turn to the camera and smile; suspects look startled, all alike.
    ///
    /// Photos are small (320 x 180) PNGs in the game's save folder, one per sight (a newer photo of
    /// the same sight replaces the old one). Your own computer only.
    /// </summary>
    public class Snapshots : MonoBehaviour
    {
        public const int ThumbW = 320, ThumbH = 180;
        public static Snapshots Instance { get; private set; }

        /// <summary>The album: id, the name on the card, and a hint for the empty frame.</summary>
        /// <summary>How many frames the album has: the eight landmarks, five more, and the six haunted places past town.</summary>
        public const int SightCount = 19;

        public static List<(string id, string name, string hint)> Sights
        {
            get
            {
                var list = new List<(string, string, string)>();
                var marks = TownLayout.Current?.landmarks;
                if (marks != null)
                    foreach (var l in marks) list.Add(("place:" + l.n, l.n, "somewhere in " + l.district));
                list.Add(("neighbour", "A neighbour", "anyone you know in town, up close"));
                list.Add(("wisp", "A will-o'-the-wisp", "a light over the creek, once you've found three lanterns"));
                list.Add(("hooks", "The Hook Board", "outside the Historical Society"));
                list.Add(("porch", "Your porch", "carve a jack-o'-lantern at HQ first"));
                list.Add(("lamplighter", "The lamplighter", "Tobias Wick, on his bench by the bridge"));
                var regions = TownLayout.Current?.regions;
                if (regions != null)
                    foreach (var r in regions) list.Add(("region:" + r.id, r.n, "past the edge of town"));
                return list;
            }
        }

        static string Folder => Path.Combine(Application.persistentDataPath, "Snapshots");
        static string FileFor(string id) => Path.Combine(Folder, id.Replace(':', '_').Replace(' ', '_').Replace('\'', '_') + ".png");

        readonly Dictionary<string, Texture2D> cache = new();
        Texture2D card;
        string cardName;
        float cardAt = -10f, flashAt = -10f;
        bool busy;

        /// <summary>Called by GameHUD: one camera per game.</summary>
        public static void Ensure(GameObject host)
        {
            if (Instance == null && host.GetComponent<Snapshots>() == null) host.AddComponent<Snapshots>();
        }

        void Awake() => Instance = this;
        void OnDestroy() { if (Instance == this) Instance = null; }

        void Update()
        {
            var kb = Keyboard.current;
            if (kb == null || busy || !kb.pKey.wasPressedThisFrame || GUIUtility.keyboardControl != 0) return;
            if (SolverController.Local == null || ClubBook.IsOpen || CarvingBench.IsOpen || TownMap.IsOpen) return;
            StartCoroutine(Snap());
        }

        IEnumerator Snap()
        {
            busy = true;
            var cam = Camera.main;
            if (cam == null) { busy = false; yield break; }
            var (id, name, subjects) = WhatsInFrame(cam);
            foreach (var t in subjects) t.Pose(cam.transform.position);
            if (id == "lamplighter") Lamplighter.Instance?.Pose(cam.transform.position);
            // Suspects are camera-shy, every one of them alike (a face never gives the culprit away).
            foreach (var npc in SuspectNPC.All)
                if (npc != null && InFrame(cam, npc.transform.position + Vector3.up * 1.7f, 10f))
                    npc.GetComponent<FaceLife>()?.Feel(FaceLife.Mood.Surprised, 1.8f);
            if (subjects.Count > 0) yield return new WaitForSeconds(0.6f); // a moment to turn and smile

            yield return new WaitForEndOfFrame(); // before the flash is drawn
            var shot = ScreenCapture.CaptureScreenshotAsTexture();
            var thumb = Shrink(shot);
            Destroy(shot);
            flashAt = Time.unscaledTime;
            Sfx.Play2D("knock", 0.35f, 2.4f); // a shutter click

            if (card != null && !cache.ContainsValue(card)) Destroy(card);
            card = thumb;
            cardAt = Time.unscaledTime;
            cardName = id != null ? name : "Nothing for the album, but a nice one";
            if (id != null)
            {
                try
                {
                    Directory.CreateDirectory(Folder);
                    File.WriteAllBytes(FileFor(id), thumb.EncodeToPNG());
                }
                catch (IOException) { }
                if (cache.TryGetValue(id, out var old) && old != null && old != thumb) Destroy(old);
                cache[id] = thumb;
                ClubBook.Snapped(id, name);
            }
            busy = false;
        }

        static Texture2D Shrink(Texture2D src)
        {
            var rt = RenderTexture.GetTemporary(ThumbW, ThumbH, 0);
            // Crop to 16:9 from the middle, then scale down.
            float aspect = src.width / (float)src.height, want = ThumbW / (float)ThumbH;
            var scale = aspect > want ? new Vector2(want / aspect, 1f) : new Vector2(1f, aspect / want);
            Graphics.Blit(src, rt, scale, (Vector2.one - scale) * 0.5f);
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var t = new Texture2D(ThumbW, ThumbH, TextureFormat.RGB24, false);
            t.ReadPixels(new Rect(0, 0, ThumbW, ThumbH), 0, 0);
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
            PrintLook(t);
            return t;
        }

        // A 4x4 ordered-dither (Bayer) threshold map, 0..15.
        static readonly int[] Bayer = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 };

        /// <summary>
        /// Makes the photo look printed (round 41): colours settle onto a few ink steps with an
        /// ordered dot pattern, blacks lift to warm ink and whites to cream paper, and the corners
        /// fall off a touch like an instant camera. Steps stay fine enough that faces read clearly.
        /// </summary>
        static void PrintLook(Texture2D t)
        {
            const float Steps = 8f;
            Color ink = new(0.06f, 0.045f, 0.06f), paper = new(1f, 0.96f, 0.88f);
            var px = t.GetPixels();
            int w = t.width, h = t.height;
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    int i = y * w + x;
                    float dither = (Bayer[(y & 3) * 4 + (x & 3)] + 0.5f) / 16f - 0.5f;
                    var c = px[i];
                    c.r = Mathf.Round(c.r * Steps + dither) / Steps;
                    c.g = Mathf.Round(c.g * Steps + dither) / Steps;
                    c.b = Mathf.Round(c.b * Steps + dither) / Steps;
                    c = new Color(Mathf.Lerp(ink.r, paper.r, c.r), Mathf.Lerp(ink.g, paper.g, c.g), Mathf.Lerp(ink.b, paper.b, c.b));
                    float dx = (x - w * 0.5f) / (w * 0.5f), dy = (y - h * 0.5f) / (h * 0.5f);
                    float fall = 1f - Mathf.Clamp01((dx * dx + dy * dy - 0.55f) * 0.35f);
                    px[i] = c * fall;
                }
            t.SetPixels(px);
            t.Apply();
        }

        /// <summary>Is a point near the middle of the picture, close enough, and not behind a wall?</summary>
        static bool InFrame(Camera cam, Vector3 p, float maxDistance)
        {
            var v = cam.WorldToViewportPoint(p);
            if (v.z <= 0.5f || v.z > maxDistance || v.x < 0.12f || v.x > 0.88f || v.y < 0.1f || v.y > 0.9f) return false;
            var from = cam.transform.position;
            var dir = p - from;
            float dist = dir.magnitude;
            return !Physics.Raycast(from, dir / dist, out var hit, dist, ~0, QueryTriggerInteraction.Ignore) || hit.distance > dist - 2.5f;
        }

        /// <summary>The best album sight in the frame (the closest to the middle wins), and any neighbours in it.</summary>
        static (string id, string name, List<Townsperson> subjects) WhatsInFrame(Camera cam)
        {
            string id = null, name = null;
            float best = float.MaxValue;
            var subjects = new List<Townsperson>();
            void Consider(string i, string n, Vector3 p, float maxD)
            {
                if (!InFrame(cam, p, maxD)) return;
                var v = cam.WorldToViewportPoint(p);
                float off = (new Vector2(v.x, v.y) - new Vector2(0.5f, 0.5f)).sqrMagnitude;
                if (off < best) { best = off; id = i; name = n; }
            }

            foreach (var t in Townsperson.All)
            {
                if (t == null) continue;
                var head = t.transform.position + Vector3.up * 1.7f;
                if (InFrame(cam, head, 10f)) { subjects.Add(t); Consider("neighbour", "A neighbour: " + t.DisplayName, head, 10f); }
            }
            var w = Wisp.Instance;
            if (w != null && w.Out) Consider("wisp", "A will-o'-the-wisp", w.Position, 25f);
            var hooks = HookBoard.Instance;
            if (hooks != null) Consider("hooks", "The Hook Board", hooks.transform.position + Vector3.up * 1.6f, 25f);
            var bench = CarvingBench.Instance;
            if (bench != null && bench.PorchHasPumpkins) Consider("porch", "Your porch", bench.PorchPoint, 15f);
            var tobias = Lamplighter.Instance;
            if (tobias != null) Consider("lamplighter", "The lamplighter", tobias.HeadPoint, 12f);
            var marks = TownLayout.Current?.landmarks;
            if (marks != null)
                foreach (var l in marks) Consider("place:" + l.n, l.n, l.Center + Vector3.up * 2f, 70f);
            var regions = TownLayout.Current?.regions;
            if (regions != null)
                foreach (var r in regions)
                    if (r.look != null && r.look.Length >= 3) Consider("region:" + r.id, r.n, new Vector3(r.look[0], r.look[1], r.look[2]), 140f);
            // A neighbour named on the card keeps the album id "neighbour".
            if (name != null && id == "neighbour") name = "A neighbour";
            return (id, name, subjects);
        }

        /// <summary>The saved photo of a sight, or null.</summary>
        public Texture2D PhotoOf(string id)
        {
            if (cache.TryGetValue(id, out var t)) return t;
            t = null;
            try
            {
                var path = FileFor(id);
                if (File.Exists(path))
                {
                    t = new Texture2D(2, 2, TextureFormat.RGB24, false);
                    if (!t.LoadImage(File.ReadAllBytes(path))) { Destroy(t); t = null; }
                }
            }
            catch (IOException) { t = null; }
            cache[id] = t;
            return t;
        }

        void OnGUI()
        {
            float now = Time.unscaledTime;
            float flash = 1f - (now - flashAt) / 0.35f;
            if (flash > 0f && !UITheme.ReduceMotion)
            {
                GUI.color = new Color(1f, 1f, 1f, flash * 0.85f);
                GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), Texture2D.whiteTexture);
                GUI.color = Color.white;
            }
            float age = now - cardAt;
            if (card == null || age > 4f) return;
            UITheme.Begin();
            // An instant photo: a cream frame with a deeper bottom edge, slightly tilted, that
            // slides in, develops from white, and slides away.
            float slide = UITheme.ReduceMotion ? 1f : Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(age / 0.35f)) * Mathf.SmoothStep(0f, 1f, Mathf.Clamp01((4f - age) / 0.4f));
            float w = 240f, h = w * ThumbH / ThumbW;
            var frame = new Rect(UITheme.W - w - 40f, UITheme.H - h - 110f + (1f - slide) * 80f, w + 20f, h + 52f);
            var m = GUI.matrix;
            GUIUtility.RotateAroundPivot(-3f, frame.center);
            UITheme.Rect(new Rect(frame.x + 2, frame.y + 4, frame.width, frame.height), UITheme.Shadow);
            UITheme.Rect(frame, new Color(0.96f, 0.93f, 0.86f));
            var pic = new Rect(frame.x + 10, frame.y + 10, w, h);
            GUI.DrawTexture(pic, card, ScaleMode.ScaleAndCrop);
            float develop = UITheme.ReduceMotion ? 0f : 1f - Mathf.Clamp01((age - 0.2f) / 1.4f);
            if (develop > 0f) UITheme.Rect(pic, new Color(0.96f, 0.95f, 0.92f, develop));
            GUI.Label(new Rect(frame.x + 10, pic.yMax + 6, w, 30), UITheme.Tint(cardName, UITheme.InkOnAccent), UITheme.Small);
            GUI.matrix = m;
        }
    }
}
