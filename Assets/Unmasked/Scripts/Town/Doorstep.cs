using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Trick-or-treat on the new streets: a front door you can knock on (HollowCreek.json "homes",
    /// placed by Docs/tools/worldgen.py). A lit porch light means somebody's home: knock (E) and the
    /// door opens a crack, a bowl of candy comes out, and they say something. Some tell one of the
    /// Stories of Hollow Creek (Tales.cs); some know where a lost lantern is. Each door gives a treat
    /// once a night, and which families are home changes from night to night. A family with a story
    /// you haven't heard is always in, so nobody's story can be missed.
    ///
    /// Like the lost lanterns, it all happens on your own computer (ILocalInteractable): nothing goes
    /// over the network, and the Club Book keeps the candy, the doors and the stories.
    /// </summary>
    public class Doorstep : MonoBehaviour, ILocalInteractable
    {
        const float LightDistance = 40f;
        const float AnswerDelay = 1.1f;
        const float OpenTime = 4.5f;

        public TownLayout.Home Home;
        public static readonly List<Doorstep> All = new();

        Light porchLight, doorway;
        Renderer bulb;
        Transform bowl;
        TextMesh bubble;
        Material bulbOn, bulbOff;
        bool busy;
        float bubbleUntil;
        int shownNight = -1;

        string Family => Home.family;

        /// <summary>Called by TownDirector: one doorstep per home.</summary>
        public static void Ensure(GameObject host)
        {
            var town = TownLayout.Current;
            if (town?.homes == null || host.transform.Find("Doorsteps") != null) return;
            var root = new GameObject("Doorsteps").transform;
            root.SetParent(host.transform, false);
            var on = Horizon.Lit("PorchBulbOn", new Color(1f, 0.82f, 0.5f), true);
            var off = Horizon.Lit("PorchBulbOff", new Color(0.28f, 0.26f, 0.24f));
            var candy = Horizon.Lit("CandyBowl", new Color(0.91f, 0.45f, 0.11f));
            var sweets = Horizon.Lit("Sweets", new Color(0.62f, 0.3f, 0.75f), true);
            foreach (var h in town.homes)
            {
                if (h.door == null || h.door.Length < 3) continue;
                var go = new GameObject("Doorstep_" + h.id);
                go.transform.SetParent(root, false);
                go.transform.SetPositionAndRotation(new Vector3(h.door[0], h.door[1], h.door[2]), Quaternion.Euler(0f, h.ry, 0f));
                var step = go.AddComponent<Doorstep>();
                step.Home = h;
                step.Build(on, off, candy, sweets);
            }
        }

        void Build(Material on, Material off, Material candy, Material sweets)
        {
            bulbOn = on;
            bulbOff = off;
            // What the camera finds when you look at the door (UpdateFocus casts against triggers too).
            var hit = gameObject.AddComponent<BoxCollider>();
            hit.isTrigger = true;
            hit.center = new Vector3(0f, 1.1f, 0.25f);
            hit.size = new Vector3(1.3f, 2.2f, 0.6f);

            // The porch light: a bulb in a little cage, beside the door.
            var lightAt = Home.light != null && Home.light.Length >= 3
                ? new Vector3(Home.light[0], Home.light[1], Home.light[2])
                : transform.position + transform.right * 0.75f + Vector3.up * 2.05f;
            var b = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            Destroy(b.GetComponent<Collider>());
            b.name = "PorchBulb";
            b.transform.SetParent(transform, false);
            b.transform.position = lightAt;
            b.transform.localScale = Vector3.one * 0.16f;
            bulb = b.GetComponent<Renderer>();
            porchLight = new GameObject("PorchLight").AddComponent<Light>();
            porchLight.transform.SetParent(transform, false);
            porchLight.transform.position = lightAt + transform.forward * 0.3f;
            porchLight.type = LightType.Point;
            porchLight.color = new Color(1f, 0.78f, 0.48f);
            porchLight.range = 6f;
            porchLight.intensity = 1.1f;
            porchLight.shadows = LightShadows.None;

            // Warm light spilling out of the open door.
            doorway = new GameObject("Doorway").AddComponent<Light>();
            doorway.transform.SetParent(transform, false);
            doorway.transform.localPosition = new Vector3(0f, 1.3f, 0.6f);
            doorway.type = LightType.Point;
            doorway.color = new Color(1f, 0.72f, 0.4f);
            doorway.range = 5f;
            doorway.intensity = 0f;
            doorway.shadows = LightShadows.None;
            doorway.enabled = false;

            // The candy bowl that comes out of the door.
            bowl = new GameObject("Bowl").transform;
            bowl.SetParent(transform, false);
            Part(bowl, PrimitiveType.Sphere, Vector3.zero, new Vector3(0.34f, 0.14f, 0.34f), candy);
            for (int i = 0; i < 5; i++)
            {
                float a = i / 5f * Mathf.PI * 2f;
                Part(bowl, PrimitiveType.Sphere, new Vector3(Mathf.Cos(a) * 0.07f, 0.06f, Mathf.Sin(a) * 0.07f), Vector3.one * 0.06f, i % 2 == 0 ? sweets : candy);
            }
            bowl.localPosition = new Vector3(0f, 1.0f, -0.1f);
            bowl.gameObject.SetActive(false);

            bubble = Horizon.MakeText(transform, "", new Vector3(0f, 2.75f, 0.5f), 0.03f, new Color(1f, 0.93f, 0.75f));
            bubble.gameObject.SetActive(false);
        }

        static void Part(Transform parent, PrimitiveType type, Vector3 pos, Vector3 scale, Material mat)
        {
            var go = GameObject.CreatePrimitive(type);
            Destroy(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localScale = scale;
            go.GetComponent<Renderer>().sharedMaterial = mat;
        }

        void OnEnable() => All.Add(this);
        void OnDisable() => All.Remove(this);

        /// <summary>Is anybody home tonight? Most families are, and which ones changes every night.</summary>
        public static bool AnswersTonight(TownLayout.Home h)
        {
            if (h == null) return false;
            if (h.tale >= 0 && !ClubBook.HeardTale(h.tale)) return true;
            unchecked
            {
                int x = ClubBook.DoorNight * 7919;
                foreach (char c in h.id) x = x * 31 + c;
                x ^= x >> 13;
                return (x & 0x7fffffff) % 10 < 7;
            }
        }

        // ---- IInteractable -------------------------------------------------------------------------

        public bool CanInteract(SolverController solver) => Home != null && !busy && solver != null && !solver.IsRiding;

        public string GetPrompt(SolverController solver)
        {
            if (!AnswersTonight(Home)) return $"Knock at {Family}' door ({Home.address}; the porch light's off)";
            return ClubBook.TreatedTonight(Home.id) ? $"Knock again at {Family}'" : $"Trick or treat at {Family}' ({Home.address})";
        }

        /// <summary>Only ever called on the server for networked things; a doorstep has no NetworkObject, so this never runs.</summary>
        public void Interact(SolverController solver) { }

        public void LocalInteract(SolverController solver)
        {
            if (busy) return;
            StartCoroutine(Knock());
        }

        IEnumerator Knock()
        {
            busy = true;
            Sfx.Play("knock", transform.position, 0.9f, 14f);
            yield return new WaitForSeconds(AnswerDelay);

            if (!AnswersTonight(Home))
            {
                Say(NoAnswer(), false);
                yield return new WaitForSeconds(1.5f);
                busy = false;
                yield break;
            }

            // The door opens a crack: light, a creak, the bowl.
            Sfx.Play("creak", transform.position, 0.5f, 12f, 1.3f);
            doorway.enabled = true;
            bowl.gameObject.SetActive(true);
            bool treat = ClubBook.Treat(Home.id, Home.street);
            string line = treat ? TreatLine() : AgainLine();
            if (Home.tale >= 0 && Home.tale < Tales.All.Length && ClubBook.HearTale(Home.tale))
            {
                var tale = Tales.All[Home.tale];
                line = $"{line} Have you heard about {LowerFirst(tale.Title)}? {tale.Text}";
            }
            else if (treat && LanternHint(out string hint))
                line = $"{line} {hint}";
            Say(line);

            float t = 0f;
            while (t < OpenTime)
            {
                t += Time.deltaTime;
                float open = Mathf.Clamp01(t / 0.6f) * Mathf.Clamp01((OpenTime - t) / 0.6f);
                doorway.intensity = 1.6f * open;
                bowl.localPosition = new Vector3(0f, 1.0f, Mathf.Lerp(-0.1f, 0.45f, open));
                yield return null;
            }
            doorway.enabled = false;
            bowl.gameObject.SetActive(false);
            busy = false;
        }

        void Say(string text, bool spoken = true)
        {
            bubble.text = TownLife.Wrap(text, 40);
            bubbleUntil = Time.time + Mathf.Clamp(text.Length * 0.06f, 4f, 12f);
            GameHUD.Toast(spoken ? $"{Capital(Family)}: {text}" : text);
        }

        void Update()
        {
            int night = ClubBook.DoorNight;
            if (night != shownNight || Time.frameCount % 30 == 0)
            {
                shownNight = night;
                bool home = AnswersTonight(Home);
                if (bulb != null) bulb.sharedMaterial = home ? bulbOn : bulbOff;
                if (porchLight != null) porchLight.intensity = home ? 1.1f : 0f;
            }
            var cam = Camera.main;
            if (porchLight != null)
                porchLight.enabled = porchLight.intensity > 0f && (cam == null || (cam.transform.position - transform.position).sqrMagnitude < LightDistance * LightDistance);
            bool show = Time.time < bubbleUntil;
            if (bubble.gameObject.activeSelf != show) bubble.gameObject.SetActive(show);
            if (show && cam != null) bubble.transform.rotation = Quaternion.LookRotation(bubble.transform.position - cam.transform.position);
        }

        // ---- What they say ---------------------------------------------------------------------------

        static readonly string[] Treats =
        {
            "Trick or treat! Take two, they're small.",
            "Oh, the Mystery Club! Here, have a handful.",
            "Look at you lot. Go on, take one for the dog too.",
            "Caramel apples are for the grandchildren. The toffees are for you.",
            "Is that a real flashlight? Very professional. Have a toffee.",
            "Mind the pumpkins on the step. Here you go.",
            "We've been saving the good ones for you.",
            "Candy corn. I know, I know. Take some anyway.",
            "The little ones were scared of the last lot. You look friendly. Here.",
            "You'll catch your death out there. Have a peppermint.",
        };

        static readonly string[] Again =
        {
            "You've had yours tonight! Come back next time.",
            "Nice try. One each, and you've had yours.",
            "Still out? Be careful down by the creek.",
        };

        static readonly string[] NoOne =
        {
            "Nobody comes. The porch light is off: they must be out tonight.",
            "Silence, and the creak of the porch swing. Try another night.",
            "A cat stares at you through the window. Nobody else is home.",
        };

        string TreatLine() => Treats[Pick(Treats.Length)];
        string AgainLine() => Again[Pick(Again.Length)];
        string NoAnswer() => NoOne[Pick(NoOne.Length)];

        int Pick(int n) => Mathf.Abs((Home.id.GetHashCode() * 17 + ClubBook.DoorNight * 31 + ClubBook.Get("treats"))) % n;

        /// <summary>Now and then a neighbour has seen one of the lost lanterns: the nearest one you haven't found.</summary>
        bool LanternHint(out string hint)
        {
            hint = null;
            var town = TownLayout.Current;
            if (town?.collectibles == null || Pick(3) != 0) return false;
            TownLayout.Collectible best = null;
            float bestD = float.MaxValue;
            foreach (var c in town.collectibles)
            {
                if (c.p == null || c.p.Length < 3 || ClubBook.Has("lantern:" + c.id)) continue;
                float d = (new Vector3(c.p[0], 0f, c.p[2]) - new Vector3(transform.position.x, 0f, transform.position.z)).sqrMagnitude;
                if (d < bestD) { bestD = d; best = c; }
            }
            if (best == null) return false;
            hint = $"Looking for the old tin lanterns? I'm sure I saw one. Try {best.where}.";
            return true;
        }

        static string LowerFirst(string s) => string.IsNullOrEmpty(s) ? s : char.ToLowerInvariant(s[0]) + s.Substring(1);
        static string Capital(string s) => string.IsNullOrEmpty(s) ? s : char.ToUpperInvariant(s[0]) + s.Substring(1);
    }
}
