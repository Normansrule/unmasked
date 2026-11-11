using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The painted night behind the first menu (round 40): a storybook sky that slowly breathes, a
    /// moon with a soft halo, three layers of hills drifting at different speeds (the middle one
    /// carries a crooked manor and its lit window), a band of ground fog, fireflies and a little
    /// paper grain. Everything is generated here from code, so there are no image files to licence.
    /// With Reduce motion on (Club Book > Settings) the picture holds still.
    /// </summary>
    public static class MenuBackdrop
    {
        static Texture2D sky, moon, glow, grain, vignette, fog;
        static readonly Texture2D[] hills = new Texture2D[3];

        // far to near: colour, how fast it drifts (texture widths per second), height on screen
        static readonly Color[] HillTint =
        {
            new(0.20f, 0.14f, 0.26f), new(0.12f, 0.085f, 0.15f), new(0.055f, 0.04f, 0.065f),
        };
        static readonly float[] HillSpeed = { 0.0035f, 0.007f, 0.013f };
        static readonly float[] HillHeight = { 0.34f, 0.30f, 0.24f };
        const float ManorWindowU = 747f / 1024f; // where the window sits along the middle hill's texture

        public static void Draw()
        {
            Build();
            float W = UITheme.W, H = UITheme.H;
            float t = UITheme.ReduceMotion ? 0f : Time.unscaledTime;

            GUI.DrawTexture(new Rect(0, 0, W, H), sky, ScaleMode.StretchToFill);

            // The moon, upper right, breathing a little.
            float m = Mathf.Min(W, H) * 0.16f;
            float breathe = 1f + Mathf.Sin(t * 0.6f) * 0.04f;
            var mc = new Vector2(W * 0.74f, H * 0.24f);
            Tinted(new Rect(mc.x - m * 2.2f * breathe, mc.y - m * 2.2f * breathe, m * 4.4f * breathe, m * 4.4f * breathe), glow, new Color(1f, 0.85f, 0.6f, 0.22f));
            Tinted(new Rect(mc.x - m / 2, mc.y - m / 2, m, m), moon, new Color(1f, 0.95f, 0.84f, 1f));

            // Hills, far to near. Each texture tiles left to right, so drifting is a u offset.
            for (int i = 0; i < hills.Length; i++)
            {
                float h = H * HillHeight[i];
                float y = H - h - (2 - i) * H * 0.07f;
                float span = W * 1.4f; // one tile is wider than the screen, so the repeat is rare
                float u = t * HillSpeed[i];
                var old = GUI.color;
                GUI.color = HillTint[i];
                GUI.DrawTextureWithTexCoords(new Rect(0, y, W, h), hills[i], new Rect(u, 0, W / span, 1));
                GUI.color = old;
                // The ground under the hills, so no sky shows below them.
                if (y + h < H) UITheme.Rect(new Rect(0, y + h - 1, W, H - y - h + 1), HillTint[i]);
                if (i == 1)
                {
                    // The manor's one lit window, drawn on top so it can glow (the hill is tinted dark).
                    float wx = Mathf.Repeat(ManorWindowU - u, 1f) * span;
                    if (wx < W)
                    {
                        float flicker = 0.85f + 0.15f * Mathf.Sin(t * 3.1f) * Mathf.Sin(t * 1.7f);
                        float wy = y + h * (1f - 0.65f), ws = Mathf.Max(3f, h / 128f * 6f);
                        Tinted(new Rect(wx - ws * 3, wy - ws * 3, ws * 6, ws * 6), glow, new Color(1f, 0.7f, 0.35f, 0.35f * flicker));
                        UITheme.Rect(new Rect(wx - ws / 2, wy - ws / 2, ws, ws), new Color(1f, 0.8f, 0.45f, flicker));
                    }
                }
                if (i == 1)
                {
                    // Ground fog drifting the other way between the middle and near hills.
                    float fu = -t * 0.01f;
                    var o = GUI.color;
                    GUI.color = new Color(0.75f, 0.7f, 0.85f, 0.16f + Mathf.Sin(t * 0.3f) * 0.03f);
                    GUI.DrawTextureWithTexCoords(new Rect(0, y + h * 0.35f, W, h * 0.5f), fog, new Rect(fu, 0, 1.6f, 1));
                    GUI.color = o;
                }
            }

            // Fireflies: slow loops, each with its own rhythm, blinking softly.
            for (int i = 0; i < 22; i++)
            {
                float a = i * 2.39996f; // golden angle spreads them out
                float px = Mathf.Repeat(0.07f + i * 0.0457f + Mathf.Sin(t * 0.13f + a) * 0.03f, 1f) * W;
                float py = H * (0.62f + 0.3f * Mathf.Repeat(i * 0.618f, 1f)) + Mathf.Sin(t * (0.4f + i % 5 * 0.07f) + a) * 14f;
                float on = UITheme.ReduceMotion ? 0.6f : Mathf.Clamp01(0.35f + Mathf.Sin(t * (1.1f + i % 3 * 0.4f) + a));
                float s = 14f + i % 4 * 3f;
                Tinted(new Rect(px - s / 2, py - s / 2, s, s), glow, new Color(1f, 0.82f, 0.42f, 0.55f * on));
                UITheme.Rect(new Rect(px - 1, py - 1, 2, 2), new Color(1f, 0.93f, 0.7f, 0.9f * on));
            }

            // Paper grain (it shifts a few times a second, like film) and a soft vignette.
            float g = UITheme.ReduceMotion ? 0f : Mathf.Floor(t * 8f) * 0.37f;
            var og = GUI.color;
            GUI.color = new Color(1f, 1f, 1f, 0.06f);
            GUI.DrawTextureWithTexCoords(new Rect(0, 0, W, H), grain, new Rect(g, g * 1.7f, W / 160f, H / 160f));
            GUI.color = og;
            GUI.DrawTexture(new Rect(0, 0, W, H), vignette, ScaleMode.StretchToFill);
        }

        static void Tinted(Rect r, Texture2D tex, Color c)
        {
            var old = GUI.color;
            GUI.color = c;
            GUI.DrawTexture(r, tex, ScaleMode.StretchToFill);
            GUI.color = old;
        }

        // ---- the pictures, made once ----------------------------------------------------------

        static Texture2D New(int w, int h, TextureWrapMode wrap) =>
            new(w, h, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave, wrapMode = wrap, filterMode = FilterMode.Bilinear };

        static void Build()
        {
            if (sky != null) return;

            // Sky: deep violet overhead, warming to an ember glow at the horizon.
            sky = New(1, 256, TextureWrapMode.Clamp);
            Color zenith = new(0.06f, 0.05f, 0.11f), mid = new(0.16f, 0.1f, 0.2f), low = new(0.45f, 0.24f, 0.2f);
            for (int y = 0; y < 256; y++)
            {
                float v = y / 255f; // 0 = bottom of the texture = bottom of the screen
                Color c = v < 0.45f ? Color.Lerp(low, mid, Mathf.SmoothStep(0, 1, v / 0.45f)) : Color.Lerp(mid, zenith, Mathf.SmoothStep(0, 1, (v - 0.45f) / 0.55f));
                sky.SetPixel(0, y, c);
            }
            sky.Apply();

            // Moon: a disc with a few soft craters; glow: a round falloff used for halo and fireflies.
            moon = New(128, 128, TextureWrapMode.Clamp);
            glow = New(64, 64, TextureWrapMode.Clamp);
            for (int y = 0; y < 128; y++)
                for (int x = 0; x < 128; x++)
                {
                    float dx = (x - 63.5f) / 63.5f, dy = (y - 63.5f) / 63.5f, d = Mathf.Sqrt(dx * dx + dy * dy);
                    float edge = Mathf.Clamp01((1f - d) * 40f);
                    float crater = Crater(dx, dy, 0.3f, 0.2f, 0.22f) + Crater(dx, dy, -0.35f, -0.25f, 0.16f) + Crater(dx, dy, 0.1f, -0.45f, 0.1f);
                    float shade = 1f - crater * 0.12f - Mathf.Max(0, dx + dy) * 0.06f;
                    moon.SetPixel(x, y, new Color(shade, shade, shade, edge));
                }
            moon.Apply();
            for (int y = 0; y < 64; y++)
                for (int x = 0; x < 64; x++)
                {
                    float dx = (x - 31.5f) / 31.5f, dy = (y - 31.5f) / 31.5f;
                    float a = Mathf.Clamp01(1f - Mathf.Sqrt(dx * dx + dy * dy));
                    glow.SetPixel(x, y, new Color(1, 1, 1, a * a));
                }
            glow.Apply();

            // Hills: white silhouettes (tinted when drawn) from sines with whole periods, so they tile.
            for (int i = 0; i < 3; i++)
            {
                const int w = 1024, h = 128;
                var tex = New(w, h, TextureWrapMode.Repeat);
                var px = new Color[w * h];
                for (int x = 0; x < w; x++)
                {
                    float u = x / (float)w * Mathf.PI * 2f;
                    float top = 0.55f + 0.18f * Mathf.Sin(u * (2 + i) + i) + 0.09f * Mathf.Sin(u * (5 + i * 2) + 1.3f * i) + 0.04f * Mathf.Sin(u * 13 + i);
                    if (i == 1) top = Mathf.Max(top, Manor(x / (float)w)); // the crooked manor on the middle ridge
                    if (i == 2) top = Mathf.Max(top, Trees(x, w));          // ragged pines along the near hill
                    int ty = Mathf.Clamp(Mathf.RoundToInt(top * h), 0, h);
                    for (int y = 0; y < h; y++)
                    {
                        float a = y < ty ? 1f : y == ty ? 0.5f : 0f;
                        px[y * w + x] = new Color(1, 1, 1, a);
                    }
                }
                tex.SetPixels(px);
                tex.Apply();
                hills[i] = tex;
            }

            // Fog: a soft band that tiles left to right.
            fog = New(256, 32, TextureWrapMode.Repeat);
            for (int y = 0; y < 32; y++)
                for (int x = 0; x < 256; x++)
                {
                    float u = x / 256f * Mathf.PI * 2f, v = y / 31f;
                    float a = Mathf.Sin(v * Mathf.PI) * (0.6f + 0.4f * Mathf.Sin(u * 3) * Mathf.Sin(u * 7 + 1));
                    fog.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(a)));
                }
            fog.Apply();

            // Grain: fixed noise (seeded, so every machine gets the same paper).
            grain = New(160, 160, TextureWrapMode.Repeat);
            var rng = new System.Random(40);
            for (int y = 0; y < 160; y++)
                for (int x = 0; x < 160; x++)
                {
                    float n = (float)rng.NextDouble();
                    grain.SetPixel(x, y, new Color(n, n, n, 1));
                }
            grain.Apply();

            // Vignette: dark corners pull the eye to the middle and to the menu.
            vignette = New(128, 128, TextureWrapMode.Clamp);
            for (int y = 0; y < 128; y++)
                for (int x = 0; x < 128; x++)
                {
                    float dx = (x - 63.5f) / 63.5f, dy = (y - 63.5f) / 63.5f;
                    float a = Mathf.Clamp01((dx * dx + dy * dy - 0.35f) * 0.55f);
                    vignette.SetPixel(x, y, new Color(0, 0, 0, a));
                }
            vignette.Apply();
        }

        static float Crater(float x, float y, float cx, float cy, float r)
        {
            float d = Mathf.Sqrt((x - cx) * (x - cx) + (y - cy) * (y - cy)) / r;
            return d < 1f ? 1f - d * d : 0f;
        }

        /// <summary>The manor's outline (texture-height fraction) at u along the middle ridge, or 0 off it.</summary>
        static float Manor(float u)
        {
            float x = (u - 0.70f) * 1024f; // pixels from the manor's left wall
            if (x < 0 || x > 84) return 0f;
            float h = 0.70f;                                        // the main house
            if (x > 8 && x < 76) h = Mathf.Max(h, 0.80f - Mathf.Abs(x - 42) / 34f * 0.1f); // its roof
            if (x > 52 && x < 64) h = Mathf.Max(h, 0.92f);          // the tower
            if (x > 50 && x < 66) h = Mathf.Max(h, 0.92f + (8 - Mathf.Abs(x - 58)) / 8f * 0.07f); // its leaning spire
            if (x > 16 && x < 20) h = Mathf.Max(h, 0.86f);          // a chimney
            return h;
        }

        /// <summary>Ragged pines along the near hill, a few per tile, deterministic.</summary>
        static float Trees(int x, int w)
        {
            float best = 0f;
            for (int k = 0; k < 7; k++)
            {
                int cx = (k * 149 + 60) % w;
                int dx = Mathf.Abs(x - cx);
                float height = 0.78f + (k % 3) * 0.06f;
                if (dx <= 1) best = Mathf.Max(best, height);                     // trunk
                else if (dx < 11) best = Mathf.Max(best, height - 0.03f - dx * 0.026f - ((dx + k) % 4 == 0 ? 0.02f : 0f)); // a ragged pine
            }
            return best;
        }
    }

    /// <summary>
    /// A short dip through dark when the screen changes a lot (round 40): leaving the menu for the
    /// town, or coming back to it. Others can call <see cref="Kick"/> too. It draws on top of every
    /// other OnGUI. With Reduce motion on it is a quick plain fade.
    /// </summary>
    public class ScreenFade : MonoBehaviour
    {
        static float start = -10f, length = 0.7f;
        bool wasPlaying;

        public static void Ensure(GameObject host)
        {
            if (host.GetComponent<ScreenFade>() == null) host.AddComponent<ScreenFade>();
        }

        /// <summary>Start a dip to dark and back over the given seconds.</summary>
        public static void Kick(float seconds = 0.7f)
        {
            start = Time.unscaledTime;
            length = UITheme.ReduceMotion ? Mathf.Min(seconds, 0.3f) : seconds;
        }

        void Update()
        {
            var net = NetworkManager.Singleton;
            bool playing = net != null && (net.IsClient || net.IsServer);
            if (playing != wasPlaying) Kick();
            wasPlaying = playing;
        }

        void OnGUI()
        {
            float k = (Time.unscaledTime - start) / length;
            if (k < 0f || k > 1f) return;
            GUI.depth = -1000; // lowest depth draws last, so on top
            GUI.matrix = Matrix4x4.identity;
            // Quick in, slower out: the new screen eases up out of the dark.
            // Both halves ease out (fast start, gentle landing): an ease-in would hold back the very moment you're watching.
            float a = k < 0.3f ? 1f - (1f - k / 0.3f) * (1f - k / 0.3f) : Mathf.Pow(1f - (k - 0.3f) / 0.7f, 3f);
            var old = GUI.color;
            GUI.color = new Color(0.04f, 0.03f, 0.05f, a);
            GUI.DrawTexture(new Rect(0, 0, Screen.width, Screen.height), Texture2D.whiteTexture);
            GUI.color = old;
        }
    }
}
