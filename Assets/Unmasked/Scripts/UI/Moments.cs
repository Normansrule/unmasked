using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The two moments of the night the interface plays out instead of just showing, the same ones
    /// the website tells by scrolling:
    /// - An hour card: a pinned note that drops in under the phase bar when the night moves on (the
    ///   van, the house, every hour of the investigation, the trap), swings on its pin, and goes.
    /// - The unmasking: the mask holds for a beat, dips, then flies up and away, and the culprit's
    ///   name types itself in under it.
    /// Reduced motion keeps both as fades. Drawn from <see cref="GameHUD"/> after the top bar.
    /// </summary>
    public static class Moments
    {
        const float CardSeconds = 4.2f, CardWidth = 360f;

        static MatchPhase lastPhase = MatchPhase.WaitingToStart;
        static string lastHour = "";
        static float phaseShownAt, cardShownAt = -100f;
        static string cardTime = "", cardTitle = "", cardText = "";
        static readonly UITheme.Swing cardSwing = new();
        static Texture2D maskTex;

        // What each hour of the investigation is for. Short, and in the club's voice.
        static readonly (string title, string text)[] Hours =
        {
            ("Clues", "Things that glow in your flashlight are clues. Each fits one or two suspects."),
            ("The Suspect Board", "Tab opens it. Cross off whoever doesn't fit and check the alibis that are left."),
            ("Witnesses", "Anyone who saw a scare remembers where it came from. That can break an alibi."),
            ("Midnight", "The Haunter gets bolder from here. Stick together."),
            ("The accusation", "Two tries. A wrong name costs time and makes the Haunter braver."),
            ("The small hours", "If the clues all point one way, it's time to say the name."),
            ("Still dark", "Every house on the street has gone quiet but this one."),
            ("Almost morning", "The sky is getting lighter. Whatever happens, it happens before dawn."),
            ("Last hour", "Dawn at six. If the Haunter is still in the mask then, they win."),
        };

        /// <summary>Call once per OnGUI, after the top bar. Watches the phase and the night clock and plays the hour card (kept hidden while a full-screen page is open).</summary>
        public static void HourCard(MysteryGameManager game, PlayerAgent agent, bool draw = true)
        {
            var phase = game.Phase.Value;
            if (phase != lastPhase)
            {
                lastPhase = phase;
                phaseShownAt = Time.unscaledTime;
                lastHour = "";
                bool haunter = agent != null && agent.Side.Value == PlayerSide.Haunter;
                switch (phase)
                {
                    case MatchPhase.Setup when game.InTown:
                        Show("7:30 PM", "Mystery Club HQ", haunter ? "Pick your disguise. Nobody else knows which neighbour you are." : "The host picks tonight's call from the board.");
                        break;
                    case MatchPhase.Dispatch:
                        Show("7:45 PM", "The van", $"Someone takes the wheel. M opens the map, and the arrow points to {game.HouseName}.");
                        break;
                    case MatchPhase.Investigation:
                        Show(game.NightClock(game.Now), game.HouseName, haunter ? "You are one of the four neighbours. Scare them, but don't get caught." : "Four neighbours are already here, each with an alibi and a reason to want the mask.");
                        lastHour = HourOf(game.NightClock(game.Now));
                        break;
                    case MatchPhase.Trap:
                        Show(game.NightClock(game.Now), "The trap", haunter ? "They know. Stay out of the trap until dawn."
                            : game.HaunterAgent == null ? "The culprit is in costume now. Build the trap, then step back: it won't come near a trap someone is guarding."
                            : "Carry the pieces to the trap site, build it and lure the Haunter in.");
                        break;
                }
            }
            else if (phase == MatchPhase.Investigation)
            {
                // A new hour on the night clock: the next card.
                string clock = game.NightClock(game.Now), hour = HourOf(clock);
                if (hour.Length > 0 && hour != lastHour)
                {
                    lastHour = hour;
                    int index = HoursSinceNine(clock);
                    if (index >= 0 && index < Hours.Length) Show(clock, Hours[index].title, Hours[index].text);
                }
            }
            if (draw) DrawCard();
        }

        static void Show(string time, string title, string text)
        {
            cardTime = time; cardTitle = title; cardText = text;
            cardShownAt = Time.unscaledTime;
            cardSwing.Push(cardSwing.Angle >= 0f ? 34f : -34f);
        }

        static string HourOf(string clock)
        {
            int colon = clock.IndexOf(':');
            return colon > 0 ? clock.Substring(0, colon) + clock.Substring(clock.Length - 2) : "";
        }

        /// <summary>"9:00 PM" is 0, "10:15 PM" is 1, … "5:40 AM" is 8.</summary>
        static int HoursSinceNine(string clock)
        {
            int colon = clock.IndexOf(':');
            if (colon <= 0 || !int.TryParse(clock.Substring(0, colon), out int h)) return -1;
            bool pm = clock.EndsWith("PM");
            int h24 = (h % 12) + (pm ? 12 : 0);
            int since = (h24 - 21 + 24) % 24;
            return since <= 8 ? since : -1;
        }

        static void DrawCard()
        {
            float now = Time.unscaledTime, age = now - cardShownAt;
            if (age > CardSeconds || cardTitle.Length == 0) return;

            var (alpha, _) = UITheme.Arrive(cardShownAt, cardShownAt + CardSeconds, 0f);
            // It drops onto its pin from a little above, overshooting slightly, like paper on a string.
            float drop = UITheme.ReduceMotion ? 0f : (1f - Back(Mathf.Clamp01(age / 0.42f))) * -28f;
            float angle = Event.current.type == EventType.Repaint ? cardSwing.Step() : cardSwing.Angle;

            float textH = UITheme.BodyWrap.CalcHeight(new GUIContent(cardText), CardWidth - 40f);
            var r = new Rect(UITheme.W / 2f - CardWidth / 2f, UITheme.Edge + 104f + drop, CardWidth, 74f + textH);
            var pin = new Vector2(r.center.x, r.y + 6f);

            var keepColour = GUI.color;
            var keepMatrix = GUI.matrix;
            GUI.color = new Color(1f, 1f, 1f, alpha);
            GUIUtility.RotateAroundPivot(-1.2f + angle, pin);
            UITheme.Rect(new Rect(r.x + 2f, r.y + 6f, r.width, r.height), UITheme.Shadow);
            UITheme.Rect(r, UITheme.Raised);
            GUI.Label(new Rect(r.x + 20f, r.y + 18f, r.width - 40f, 20f), cardTime, UITheme.Timer);
            GUI.Label(new Rect(r.x + 20f, r.y + 38f, r.width - 40f, 30f), cardTitle, UITheme.Title);
            GUI.Label(new Rect(r.x + 20f, r.y + 68f, r.width - 40f, textH), cardText, UITheme.BodyWrap);
            UITheme.Pin(pin);
            GUI.matrix = keepMatrix;
            GUI.color = keepColour;
        }

        /// <summary>Ease out with a small overshoot past the end ("back").</summary>
        static float Back(float t)
        {
            const float c = 1.7f;
            float u = t - 1f;
            return 1f + (c + 1f) * u * u * u + c * u * u;
        }

        /// <summary>
        /// The big reveal. 0–0.25 s the band fades in with the mask on it; 0.25–0.6 s it holds, then
        /// dips and squashes (the anticipation); 0.6–1.3 s it flies up and to the right, turning and
        /// fading; from 0.8 s the name types itself in, then the reason fades up under it.
        /// </summary>
        public static void Unmasking(string name, string line)
        {
            float t = Time.unscaledTime - phaseShownAt;
            bool still = UITheme.ReduceMotion;
            float y = UITheme.H * 0.22f;

            var keepColour = GUI.color;
            GUI.color = new Color(1f, 1f, 1f, UITheme.EaseOut(t / 0.25f));
            UITheme.Rect(new Rect(0, y - UITheme.S5, UITheme.W, 150), UITheme.Scrim);
            GUI.color = keepColour;

            // The mask.
            float maskAlpha, dx = 0f, dy = 0f, turn = 0f, sx = 1f, sy = 1f;
            if (still)
            {
                maskAlpha = 1f - Mathf.Clamp01((t - 0.4f) / 0.5f);
            }
            else
            {
                maskAlpha = Mathf.Clamp01(t / 0.2f) * (1f - Mathf.Clamp01((t - 1.0f) / 0.3f));
                float dip = Mathf.Clamp01((t - 0.3f) / 0.18f) * (1f - Mathf.Clamp01((t - 0.48f) / 0.12f));
                dy = 10f * Mathf.Sin(dip * Mathf.PI * 0.5f);
                sx = 1f + 0.06f * dip; sy = 1f - 0.08f * dip;
                float fly = Mathf.Clamp01((t - 0.6f) / 0.7f);
                float e = fly * fly; // accelerates away, like it was flung
                dx = 260f * e; dy += -320f * e; turn = -42f * e;
                sx *= 1f - 0.25f * e; sy *= 1f - 0.25f * e;
            }
            if (maskAlpha > 0f) DrawMask(new Vector2(UITheme.W / 2f + dx, y + 22f + dy), 220f, turn, sx, sy, maskAlpha);

            // The name types itself in after the mask has gone.
            string full = $"Unmasked. It was {name}.";
            float typeStart = still ? 0.5f : 0.8f;
            int shown = still ? (t > typeStart ? full.Length : 0) : Mathf.Clamp((int)((t - typeStart) * 34f), 0, full.Length);
            if (shown > 0) GUI.Label(new Rect(0, y, UITheme.W, 44), full.Substring(0, shown), UITheme.DisplayCenter);
            float lineAlpha = Mathf.Clamp01((t - typeStart - full.Length / 34f) / 0.4f);
            if (lineAlpha > 0f)
            {
                GUI.color = new Color(1f, 1f, 1f, lineAlpha);
                GUI.Label(new Rect(UITheme.W / 2f - 320, y + 52, 640, 70), line, UITheme.Center);
                GUI.color = keepColour;
            }
        }

        static void DrawMask(Vector2 centre, float width, float angle, float sx, float sy, float alpha)
        {
            if (maskTex == null) maskTex = BuildMask();
            float w = width * sx, h = width * 0.42f * sy;
            var keepMatrix = GUI.matrix;
            var keepColour = GUI.color;
            if (Mathf.Abs(angle) > 0.01f) GUIUtility.RotateAroundPivot(angle, centre);
            GUI.color = new Color(0f, 0f, 0f, UITheme.Shadow.a * alpha);
            GUI.DrawTexture(new Rect(centre.x - w / 2f + 3f, centre.y - h / 2f + 6f, w, h), maskTex);
            GUI.color = new Color(UITheme.Haunt.r, UITheme.Haunt.g, UITheme.Haunt.b, alpha);
            GUI.DrawTexture(new Rect(centre.x - w / 2f, centre.y - h / 2f, w, h), maskTex);
            GUI.matrix = keepMatrix;
            GUI.color = keepColour;
        }

        /// <summary>A domino mask, drawn once into a texture: two rounded lobes joined over the nose, with eye holes.</summary>
        static Texture2D BuildMask()
        {
            const int W = 240, H = 100;
            var tex = new Texture2D(W, H, TextureFormat.RGBA32, false) { hideFlags = HideFlags.HideAndDontSave, filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
            for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
            {
                float u = (x + 0.5f) / W * 2f - 1f, v = (y + 0.5f) / H * 2f - 1f; // v runs up
                float lobe = Mathf.Min(Ellipse(u, v, -0.46f, 0.02f, 0.52f, 0.86f), Ellipse(u, v, 0.46f, 0.02f, 0.52f, 0.86f));
                float bridge = Ellipse(u, v, 0f, 0.38f, 0.4f, 0.42f);
                float shape = Mathf.Min(lobe, bridge);
                // The nose notch along the bottom, and the eyes.
                shape = Mathf.Max(shape, -Ellipse(u, v, 0f, -0.86f, 0.2f, 0.62f));
                shape = Mathf.Max(shape, -Ellipse(u, v, -0.44f, 0.08f, 0.2f, 0.3f));
                shape = Mathf.Max(shape, -Ellipse(u, v, 0.44f, 0.08f, 0.2f, 0.3f));
                float a = Mathf.Clamp01(0.5f - shape * W * 0.25f);
                float shade = Mathf.Lerp(1.08f, 0.82f, Mathf.Clamp01(0.5f - v * 0.5f));
                tex.SetPixel(x, y, new Color(shade, shade, shade, a));
            }
            tex.Apply();
            return tex;
        }

        /// <summary>Roughly signed distance to an ellipse (negative inside), good enough for a soft edge.</summary>
        static float Ellipse(float u, float v, float cx, float cy, float rx, float ry)
        {
            float du = (u - cx) / rx, dv = (v - cy) / ry;
            return (Mathf.Sqrt(du * du + dv * dv) - 1f) * Mathf.Min(rx, ry);
        }
    }
}
