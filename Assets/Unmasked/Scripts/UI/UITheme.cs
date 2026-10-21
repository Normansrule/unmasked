using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// One look for every on-screen panel (HUD, Suspect Board, town map, Handbook), so colours, type
    /// sizes, spacing and motion are decided once instead of per call.
    ///
    /// Call <see cref="Begin"/> at the top of an OnGUI: it applies the skin and the resolution scale.
    /// Everything is then laid out in a virtual screen of <see cref="W"/> x <see cref="H"/> points.
    ///
    /// The look is the Case Book: the club's own paperwork under a lamp at night. Warm dark paper,
    /// a corkboard for the Suspect Board, and evidence-tag red as the one accent (pins, string, the
    /// main button, anything that is evidence). Violet is kept for the Haunter only, so it always
    /// means "haunted". Names and headings are set in Fraunces, everything you read in Atkinson
    /// Hyperlegible (both under the SIL Open Font License, in Resources/Fonts). The website in site/
    /// uses the same tokens in its dark mode.
    /// Motion: only things that arrive on their own (toasts, hint cards) slide in, quickly and with
    /// an ease-out. Panels opened from the keyboard (Tab, M, F1) appear instantly. Pinned cards
    /// swing a little on their pin when you act on them (a damped spring), unless motion is reduced.
    /// </summary>
    public static class UITheme
    {
        // ---- Colour tokens (site/styles.css, dark mode) -----------------------------------------
        public static readonly Color Ground = new(0.086f, 0.071f, 0.055f, 0.95f);   // #16120e
        public static readonly Color Raised = new(0.141f, 0.114f, 0.09f, 1f);       // #241d17, a sheet
        public static readonly Color RaisedHover = new(0.18f, 0.149f, 0.118f, 1f);  // #2e261e
        public static readonly Color RaisedDown = new(0.106f, 0.086f, 0.067f, 1f);
        public static readonly Color Cork = new(0.231f, 0.173f, 0.125f, 0.98f);     // #3b2c20
        public static readonly Color TagWash = new(0.243f, 0.133f, 0.11f, 1f);      // #3e221c, an evidence tag
        public static readonly Color Ink = new(0.953f, 0.918f, 0.859f);             // #f3eadb
        public static readonly Color InkMuted = new(0.804f, 0.749f, 0.671f);        // #cdbfab
        public static readonly Color InkFaint = new(0.635f, 0.576f, 0.498f);        // #a2937f
        public static readonly Color InkOnAccent = new(0.114f, 0.071f, 0.051f);     // #1d120d
        public static readonly Color Accent = new(0.937f, 0.424f, 0.357f);          // #ef6c5b, evidence-tag red
        public static readonly Color AccentHover = new(0.957f, 0.533f, 0.478f);
        public static readonly Color AccentDown = new(0.847f, 0.337f, 0.275f);
        public static readonly Color Haunt = new(0.675f, 0.6f, 0.949f);             // #ac99f2, the Haunter only
        public static readonly Color Danger = new(0.937f, 0.424f, 0.357f);          // same red: alarm is evidence too
        public static readonly Color DangerFill = new(0.42f, 0.12f, 0.1f, 1f);
        public static readonly Color Good = new(0.51f, 0.812f, 0.624f);             // #82cf9f
        public static readonly Color Scrim = new(0f, 0f, 0f, 0.72f);
        public static readonly Color ScrimDeep = new(0f, 0f, 0f, 0.85f);
        /// <summary>The shadow under anything pinned: one point right, three down.</summary>
        public static readonly Color Shadow = new(0f, 0f, 0f, 0.38f);

        // ---- Type and spacing ----------------------------------------------------------------
        public const int SizeDisplay = 30, SizeTitle = 19, SizeBody = 15, SizeSmall = 13;
        public const float S1 = 4, S2 = 8, S3 = 12, S4 = 16, S5 = 24, S6 = 32, S7 = 48;
        /// <summary>Distance from the screen edge for every corner panel.</summary>
        public const float Edge = 16;

        // ---- Preferences (saved per machine; set from the Handbook page) -----------------------
        public const string TextSizeKey = "Unmasked.TextSize", ReduceMotionKey = "Unmasked.ReduceMotion";
        public static readonly float[] TextSizes = { 0.85f, 1f, 1.2f, 1.45f };
        public static readonly string[] TextSizeNames = { "Small", "Default", "Large", "Larger" };
        public static int TextSize { get; private set; } = -1;
        public static bool ReduceMotion { get; private set; }

        public static void SetTextSize(int index)
        {
            TextSize = Mathf.Clamp(index, 0, TextSizes.Length - 1);
            PlayerPrefs.SetInt(TextSizeKey, TextSize);
            PlayerPrefs.Save();
        }

        public static void SetReduceMotion(bool on)
        {
            ReduceMotion = on;
            PlayerPrefs.SetInt(ReduceMotionKey, on ? 1 : 0);
            PlayerPrefs.Save();
        }

        // ---- Scale -------------------------------------------------------------------------------
        /// <summary>Points to pixels: 1 at 900 px tall, so 1080p is a little larger and 4K is not tiny.</summary>
        public static float Scale { get; private set; } = 1f;
        public static float W => Screen.width / Scale;
        public static float H => Screen.height / Scale;

        /// <summary>A screen pixel position (bottom-left origin, as the Input System gives it) in GUI points.</summary>
        public static Vector2 ToGui(Vector2 screen) => new(screen.x / Scale, (Screen.height - screen.y) / Scale);

        // ---- Styles ------------------------------------------------------------------------------
        public static GUISkin Skin { get; private set; }
        public static GUIStyle Panel, Card, Display, Title, Body, BodyWrap, Muted, MutedWrap, Small, SmallCenter, Center, TitleCenter,
            DisplayCenter, Primary, DangerButton, Chip, Timer, TimerLow, Key, Strong, CardName, CardButton, AccuseButton;

        /// <summary>Fraunces at display and text optical sizes, Atkinson Hyperlegible regular and bold. Null before Build, or if missing.</summary>
        public static Font SerifDisplay, SerifTitle, Sans, SansBold;

        /// <summary>Apply the skin and the scale. Call first thing in every OnGUI.</summary>
        public static void Begin()
        {
            if (TextSize < 0)
            {
                TextSize = Mathf.Clamp(PlayerPrefs.GetInt(TextSizeKey, 1), 0, TextSizes.Length - 1);
                ReduceMotion = PlayerPrefs.GetInt(ReduceMotionKey, 0) == 1;
            }
            Scale = Mathf.Clamp(Screen.height / 900f, 0.75f, 2.5f) * TextSizes[TextSize];
            if (Skin == null) Build();
            GUI.skin = Skin;
            GUI.matrix = Matrix4x4.Scale(new Vector3(Scale, Scale, 1f));
        }

        static Texture2D Tex(Color c)
        {
            var t = new Texture2D(1, 1, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave };
            t.SetPixel(0, 0, c);
            t.Apply();
            return t;
        }

        static void Fill(GUIStyle s, Color normal, Color hover, Color active, Color text, Color? textActive = null)
        {
            s.normal.background = Tex(normal);
            s.hover.background = Tex(hover);
            s.active.background = Tex(active);
            s.focused.background = s.normal.background;
            s.onNormal.background = s.normal.background;
            s.onHover.background = s.hover.background;
            s.onActive.background = s.active.background;
            s.normal.textColor = s.hover.textColor = s.focused.textColor = text;
            s.active.textColor = textActive ?? text;
            s.onNormal.textColor = s.onHover.textColor = s.onActive.textColor = text;
            s.border = new RectOffset(0, 0, 0, 0);
        }

        static GUIStyle Text(GUIStyle from, int size, Color color, FontStyle weight = FontStyle.Normal, bool wrap = false, TextAnchor align = TextAnchor.UpperLeft)
        {
            var s = new GUIStyle(from) { fontSize = size, fontStyle = weight, wordWrap = wrap, alignment = align, richText = true };
            s.normal.textColor = s.hover.textColor = s.active.textColor = color;
            s.padding = new RectOffset(0, 0, 2, 2);
            s.margin = new RectOffset(0, 0, 2, 2);
            return s;
        }

        static void Build()
        {
            Skin = Object.Instantiate(GUI.skin);
            Skin.hideFlags = HideFlags.HideAndDontSave;
            SerifDisplay = Resources.Load<Font>("Fonts/Fraunces-Display");
            SerifTitle = Resources.Load<Font>("Fonts/Fraunces-Title");
            Sans = Resources.Load<Font>("Fonts/Atkinson-Regular");
            SansBold = Resources.Load<Font>("Fonts/Atkinson-Bold");
            if (Sans != null) Skin.font = Sans;

            Skin.label = Text(Skin.label, SizeBody, Ink);
            Skin.box = new GUIStyle(Skin.box) { fontSize = SizeBody, alignment = TextAnchor.UpperCenter, padding = new RectOffset(16, 16, 12, 12) };
            Fill(Skin.box, Ground, Ground, Ground, Ink);

            // Buttons press visibly: a darker tone and the label drops a point (feedback without motion).
            Skin.button = new GUIStyle(Skin.button) { fontSize = SizeBody, alignment = TextAnchor.MiddleCenter, wordWrap = true,
                padding = new RectOffset(12, 12, 7, 7), margin = new RectOffset(0, 0, 3, 3), fixedHeight = 0 };
            Fill(Skin.button, Raised, RaisedHover, RaisedDown, Ink);
            Skin.button.active.textColor = Ink;
            Skin.button.contentOffset = Vector2.zero;
            // Toggles drawn with the button style: the chosen one is a light sheet with dark ink, so it
            // reads as picked without borrowing the red of the main action.
            Skin.button.onNormal.background = Tex(Ink);
            Skin.button.onHover.background = Tex(Ink);
            Skin.button.onActive.background = Tex(InkMuted);
            Skin.button.onNormal.textColor = Skin.button.onHover.textColor = Skin.button.onActive.textColor = InkOnAccent;

            Skin.textField = new GUIStyle(Skin.textField) { fontSize = SizeBody, padding = new RectOffset(8, 8, 6, 6) };
            Fill(Skin.textField, RaisedDown, RaisedDown, RaisedDown, Ink);
            Skin.textField.focused.background = Tex(Raised);
            Skin.settings.cursorColor = Accent;
            Skin.settings.selectionColor = new Color(Accent.r, Accent.g, Accent.b, 0.35f);

            Skin.verticalScrollbar = new GUIStyle(Skin.verticalScrollbar) { fixedWidth = 8, border = new RectOffset(0, 0, 0, 0), margin = new RectOffset(6, 0, 0, 0) };
            Skin.verticalScrollbar.normal.background = Tex(RaisedDown);
            Skin.verticalScrollbarThumb = new GUIStyle(Skin.verticalScrollbarThumb) { fixedWidth = 8, border = new RectOffset(0, 0, 0, 0) };
            Skin.verticalScrollbarThumb.normal.background = Tex(RaisedHover);
            Skin.scrollView = new GUIStyle(Skin.scrollView);

            Panel = Skin.box;
            Card = new GUIStyle(Skin.box) { padding = new RectOffset(14, 14, 10, 10), margin = new RectOffset(0, 0, 0, 8) };
            Fill(Card, Raised, Raised, Raised, Ink);

            Display = Serif(Text(Skin.label, SizeDisplay, Ink, FontStyle.Bold, true), SerifDisplay);
            DisplayCenter = Serif(Text(Skin.label, SizeDisplay, Ink, FontStyle.Bold, true, TextAnchor.UpperCenter), SerifDisplay);
            Title = Serif(Text(Skin.label, SizeTitle, Ink, FontStyle.Bold, true), SerifTitle);
            TitleCenter = Serif(Text(Skin.label, SizeTitle, Ink, FontStyle.Bold, true, TextAnchor.UpperCenter), SerifTitle);
            CardName = Serif(Text(Skin.label, SizeTitle + 1, Ink, FontStyle.Bold, false), SerifTitle);
            Body = Text(Skin.label, SizeBody, Ink);
            BodyWrap = Text(Skin.label, SizeBody, Ink, FontStyle.Normal, true);
            Center = Text(Skin.label, SizeBody, Ink, FontStyle.Normal, true, TextAnchor.UpperCenter);
            Muted = Text(Skin.label, SizeBody, InkMuted);
            MutedWrap = Text(Skin.label, SizeBody, InkMuted, FontStyle.Normal, true);
            Small = Text(Skin.label, SizeSmall, InkMuted, FontStyle.Normal, true);
            SmallCenter = Text(Skin.label, SizeSmall, InkMuted, FontStyle.Normal, true, TextAnchor.UpperCenter);
            // The time left is in the serif's lining figures; it turns red in the last minute.
            Timer = Serif(Text(Skin.label, SizeTitle, Ink, FontStyle.Bold, false, TextAnchor.UpperRight), SerifTitle);
            TimerLow = Serif(Text(Skin.label, SizeTitle, Accent, FontStyle.Bold, false, TextAnchor.UpperRight), SerifTitle);
            Key = Bold(Text(Skin.label, SizeBody, Ink, FontStyle.Bold));
            Strong = Bold(Text(Skin.label, SizeBody, Ink, FontStyle.Bold, true));

            Primary = Bold(new GUIStyle(Skin.button) { fontStyle = FontStyle.Bold });
            Fill(Primary, Accent, AccentHover, AccentDown, InkOnAccent);
            // Buttons on a card sit one step lighter than the card itself.
            CardButton = new GUIStyle(Skin.button) { fontSize = SizeSmall + 1 };
            Fill(CardButton, RaisedHover, new Color(0.235f, 0.196f, 0.157f), RaisedDown, Ink);
            CardButton = Bold(CardButton);
            // Accuse on a card: red text on the card button, filling red when pressed. Four filled
            // red buttons on one board would shout; the one main action per panel is Primary.
            AccuseButton = new GUIStyle(CardButton);
            Fill(AccuseButton, RaisedHover, new Color(0.235f, 0.196f, 0.157f), Accent, Accent, InkOnAccent);
            DangerButton = new GUIStyle(Skin.button);
            Fill(DangerButton, DangerFill, new Color(0.52f, 0.16f, 0.13f), new Color(0.34f, 0.09f, 0.08f), Ink);
            Chip = Bold(new GUIStyle(Skin.label) { fontSize = SizeSmall, fontStyle = FontStyle.Bold, padding = new RectOffset(8, 8, 3, 3), alignment = TextAnchor.MiddleCenter });
            Fill(Chip, Raised, Raised, Raised, InkMuted);
        }

        /// <summary>The serif, at its own weight (the static instance is already bold, so no faux bold on top).</summary>
        static GUIStyle Serif(GUIStyle s, Font f)
        {
            if (f == null) return s;
            s.font = f;
            s.fontStyle = FontStyle.Normal;
            return s;
        }

        /// <summary>Atkinson Hyperlegible Bold as its own file, so the bold is drawn, not smeared.</summary>
        static GUIStyle Bold(GUIStyle s)
        {
            if (SansBold == null) return s;
            s.font = SansBold;
            s.fontStyle = FontStyle.Normal;
            return s;
        }

        // ---- Drawing helpers -----------------------------------------------------------------------
        public static void Rect(Rect r, Color c)
        {
            var old = GUI.color;
            GUI.color = c * old;
            GUI.DrawTexture(r, Texture2D.whiteTexture);
            GUI.color = old;
        }

        /// <summary>A meter: a raised track with a filled part in the given colour.</summary>
        /// <summary>A frame of the given thickness drawn `gap` points outside r: the keyboard focus ring.</summary>
        public static void Outline(Rect r, float gap, float thickness, Color c)
        {
            var o = new Rect(r.x - gap - thickness, r.y - gap - thickness, r.width + 2 * (gap + thickness), r.height + 2 * (gap + thickness));
            Rect(new Rect(o.x, o.y, o.width, thickness), c);
            Rect(new Rect(o.x, o.yMax - thickness, o.width, thickness), c);
            Rect(new Rect(o.x, o.y, thickness, o.height), c);
            Rect(new Rect(o.xMax - thickness, o.y, thickness, o.height), c);
        }

        public static void Meter(Rect r, float fraction, Color fill)
        {
            Rect(r, Raised);
            Rect(new Rect(r.x, r.y, r.width * Mathf.Clamp01(fraction), r.height), fill);
        }

        /// <summary>Text with a colour, without allocating a style.</summary>
        public static string Tint(string text, Color c) => $"<color=#{ColorUtility.ToHtmlStringRGB(c)}>{text}</color>";

        /// <summary>A key to press, in bold ink: "<b>E</b> get out". Red stays for evidence.</summary>
        public static string KeyCap(string key) => $"<b>{Tint(key, Ink)}</b>";

        // ---- The Case Book: cork, pins, red string, a real strikethrough ----------------------------
        static Texture2D pinTex, grainTex;

        /// <summary>A round pin: a filled circle with a soft edge, a highlight and a little shadow.</summary>
        public static void Pin(Vector2 centre, float size = 14f) => Pin(centre, size, Accent);

        public static void Pin(Vector2 centre, float size, Color colour)
        {
            if (pinTex == null)
            {
                const int n = 48;
                pinTex = new Texture2D(n, n, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave, filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
                for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float dx = (x + 0.5f) / n * 2f - 1f, dy = (y + 0.5f) / n * 2f - 1f;
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    float a = Mathf.Clamp01((1f - d) * n * 0.5f);
                    // Lit from the top left (texture y runs up): lighter there, darker at the bottom right.
                    float shade = Mathf.Lerp(1.12f, 0.78f, Mathf.Clamp01((dx - dy) * 0.5f + 0.5f));
                    pinTex.SetPixel(x, y, new Color(shade, shade, shade, a));
                }
                pinTex.Apply();
            }
            var old = GUI.color;
            GUI.color = new Color(0f, 0f, 0f, Shadow.a * old.a);
            GUI.DrawTexture(new Rect(centre.x - size / 2f + 1f, centre.y - size / 2f + 2f, size, size), pinTex);
            GUI.color = colour * old;
            GUI.DrawTexture(new Rect(centre.x - size / 2f, centre.y - size / 2f, size, size), pinTex);
            GUI.color = old;
        }

        /// <summary>Red string from pin to pin, sagging a little under its own weight (a few straight pieces along a curve).</summary>
        public static void RedString(Vector2 a, Vector2 b, float alpha = 1f, float thickness = 2f)
        {
            float len = Vector2.Distance(a, b);
            if (len < 1f) return;
            var control = new Vector2((a.x + b.x) / 2f, Mathf.Max(a.y, b.y) + Mathf.Min(40f, len * 0.12f));
            const int pieces = 10;
            Vector2 prev = a;
            var old = GUI.color;
            GUI.color = new Color(Accent.r, Accent.g, Accent.b, alpha * old.a);
            for (int i = 1; i <= pieces; i++)
            {
                float t = i / (float)pieces;
                Vector2 p = (1 - t) * (1 - t) * a + 2 * (1 - t) * t * control + t * t * b;
                Line(prev, p, thickness);
                prev = p;
            }
            GUI.color = old;
        }

        /// <summary>A straight line of the given thickness in the current GUI colour.</summary>
        public static void Line(Vector2 a, Vector2 b, float thickness)
        {
            Vector2 d = b - a;
            float angle = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg;
            var keep = GUI.matrix;
            GUIUtility.RotateAroundPivot(angle, a);
            GUI.DrawTexture(new Rect(a.x, a.y - thickness / 2f, d.magnitude + 0.5f, thickness), Texture2D.whiteTexture);
            GUI.matrix = keep;
        }

        /// <summary>
        /// A label with a real strikethrough when <paramref name="struck"/> (IMGUI rich text has none):
        /// a red line drawn across the text at mid-height.
        /// </summary>
        public static void Struck(Rect r, string text, GUIStyle style, bool struck)
        {
            GUI.Label(r, text, style);
            if (!struck) return;
            float w = Mathf.Min(style.CalcSize(new GUIContent(text)).x, r.width);
            float y = r.y + style.padding.top + style.fontSize * 0.62f;
            var old = GUI.color;
            GUI.color = Accent * old;
            GUI.DrawTexture(new Rect(r.x - 2f, y, w + 4f, 2.5f), Texture2D.whiteTexture);
            GUI.color = old;
        }

        /// <summary>The corkboard: a flat colour with a fine grain on top (tiled noise, no gradient).</summary>
        public static void CorkRect(Rect r)
        {
            Rect(r, Cork);
            if (grainTex == null)
            {
                const int n = 128;
                grainTex = new Texture2D(n, n, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave, wrapMode = TextureWrapMode.Repeat };
                var rng = new System.Random(7);
                for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float v = (float)rng.NextDouble();
                    grainTex.SetPixel(x, y, v > 0.5f ? new Color(1f, 0.9f, 0.75f, (v - 0.5f) * 0.12f) : new Color(0f, 0f, 0f, (0.5f - v) * 0.22f));
                }
                grainTex.Apply();
            }
            GUI.DrawTextureWithTexCoords(r, grainTex, new Rect(0, 0, r.width / 128f, r.height / 128f));
        }

        /// <summary>
        /// A card hanging from its pin: a damped spring around its resting tilt. Push it when the
        /// player acts on it; it swings and settles in about a second. Reduced motion never swings.
        /// </summary>
        public class Swing
        {
            const float Stiff = 140f, Damp = 7.5f;
            public float Angle, Speed;
            float lastStep = -1f;

            public void Push(float speed) { if (!ReduceMotion) Speed = Mathf.Clamp(Speed + speed, -70f, 70f); }

            /// <summary>Advance once per frame (call on the Repaint event) and return the current angle in degrees.</summary>
            public float Step()
            {
                float now = Time.unscaledTime;
                float dt = lastStep < 0f ? 0f : Mathf.Min(0.032f, now - lastStep);
                lastStep = now;
                if (Angle == 0f && Speed == 0f) return 0f;
                Speed += (-Stiff * Angle - Damp * Speed) * dt;
                Angle += Speed * dt;
                if (Mathf.Abs(Angle) < 0.03f && Mathf.Abs(Speed) < 0.08f) Angle = Speed = 0f;
                return Angle;
            }
        }

        // ---- Motion --------------------------------------------------------------------------------
        public const float EnterSeconds = 0.18f, ExitSeconds = 0.14f;

        /// <summary>Strong ease-out (quint): moves at once, settles gently.</summary>
        public static float EaseOut(float t) { t = Mathf.Clamp01(t); return 1f - Mathf.Pow(1f - t, 5f); }

        /// <summary>
        /// How far an arriving element is in: alpha (0..1) and a rise in points to add to its y.
        /// <paramref name="shownAt"/> is when it appeared, <paramref name="hideAt"/> when it goes.
        /// Reduce motion keeps the fade and drops the travel.
        /// </summary>
        public static (float alpha, float rise) Arrive(float shownAt, float hideAt, float distance = 8f)
        {
            float now = Time.unscaledTime;
            float enter = EaseOut((now - shownAt) / EnterSeconds);
            float exit = hideAt > 0 ? Mathf.Clamp01((hideAt - now) / ExitSeconds) : 1f;
            float alpha = Mathf.Min(enter, exit);
            float rise = ReduceMotion ? 0f : (1f - enter) * distance;
            return (alpha, rise);
        }
    }
}
