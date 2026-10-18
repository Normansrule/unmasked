using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The sound of the night, on every machine: wind and crickets always, rain on Thunderstorm
    /// nights, a low drone under the Blood Moon, crows and owls now and then, the music box in the
    /// Willow Lane nursery, the van's engine, and your own heartbeat as fear rises. Creates itself
    /// when a scene loads, so no scene or builder changes are needed.
    /// </summary>
    public class Ambience : MonoBehaviour
    {
        public static Ambience Instance { get; private set; }

        AudioSource wind, crickets, rain, drone, engine, musicBox;
        AudioListener listener;
        float nextCritter, nextBeat;
        Vector3 lastVanPosition;
        float vanSpeed;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Create()
        {
            if (Instance != null) return;
            var go = new GameObject("Ambience");
            DontDestroyOnLoad(go);
            go.AddComponent<Ambience>();
        }

        void Awake()
        {
            Instance = this;
            wind = Sfx.Loop("wind", transform, 0.32f, false);
            crickets = Sfx.Loop("crickets", transform, 0.22f, false);
            rain = Sfx.Loop("rain", transform, 0f, false);
            drone = Sfx.Loop("drone", transform, 0f, false);
            nextCritter = Time.time + Random.Range(6f, 15f);
        }

        void Update()
        {
            EnsureListener();
            var game = MysteryGameManager.Instance;
            NightEvent evt = game != null && game.IsSpawned && game.Phase.Value >= MatchPhase.Dispatch ? game.Event.Value : NightEvent.None;

            Fade(rain, evt == NightEvent.Thunderstorm ? 0.5f : 0f);
            Fade(crickets, evt == NightEvent.Thunderstorm ? 0f : 0.22f);
            Fade(drone, evt == NightEvent.BloodMoon ? 0.35f : 0f);
            Fade(wind, evt == NightEvent.PeaSoupFog ? 0.18f : 0.32f);

            Vector3 here = listener != null ? listener.transform.position : Vector3.zero;
            if (Time.time >= nextCritter)
            {
                nextCritter = Time.time + Random.Range(12f, 35f);
                Vector2 off = Random.insideUnitCircle.normalized * Random.Range(10f, 22f);
                Sfx.Play(Random.value < 0.6f ? "crow" : "owl", here + new Vector3(off.x, 6f, off.y), 0.55f, 40f, Random.Range(0.92f, 1.08f));
            }

            Heartbeat();
            VanEngine();
            MusicBox();
        }

        void EnsureListener()
        {
            if (listener != null && listener.isActiveAndEnabled) return;
            listener = FindAnyObjectByType<AudioListener>();
            if (listener == null && Camera.main != null) listener = Camera.main.gameObject.AddComponent<AudioListener>();
        }

        static void Fade(AudioSource s, float target)
        {
            if (s == null) return;
            s.volume = Mathf.MoveTowards(s.volume, target * Sfx.Volume, Time.deltaTime * 0.4f);
        }

        /// <summary>Your own heart, once fear passes a third: faster and louder the closer you are to panic.</summary>
        void Heartbeat()
        {
            SolverController me = null;
            foreach (var s in SolverController.All) if (s != null && s.IsOwner) { me = s; break; }
            if (me == null || me.Fear == null) return;
            float f = me.Fear.Fear / Mathf.Max(1f, me.Fear.MaxFear);
            if (f < 0.35f || Time.time < nextBeat) return;
            float k = Mathf.InverseLerp(0.35f, 1f, f);
            nextBeat = Time.time + Mathf.Lerp(1.1f, 0.42f, k);
            Sfx.Play2D("heartbeat", Mathf.Lerp(0.25f, 0.85f, k));
        }

        void VanEngine()
        {
            var van = MysteryVan.Instance;
            if (van == null) { if (engine != null) Destroy(engine.gameObject); engine = null; return; }
            if (engine == null)
            {
                engine = Sfx.Loop("van_engine", van.transform, 0.5f, true, 35f);
                lastVanPosition = van.transform.position;
            }
            if (engine == null) return;
            float dt = Mathf.Max(Time.deltaTime, 0.0001f);
            Vector3 d = van.transform.position - lastVanPosition;
            lastVanPosition = van.transform.position;
            vanSpeed = Mathf.Lerp(vanSpeed, d.magnitude / dt, 4f * dt);
            engine.pitch = 0.8f + Mathf.Clamp(vanSpeed / 14f, 0f, 1.2f);
            engine.volume = (0.35f + Mathf.Clamp01(vanSpeed / 14f) * 0.35f) * Sfx.Volume;
        }

        /// <summary>The Willow Lane nursery's music box plays by itself, all night.</summary>
        void MusicBox()
        {
            if (musicBox != null || TownDirector.Instance == null || TownLayout.Current?.lots == null) return;
            foreach (var lot in TownLayout.Current.lots)
            {
                if (lot.id != "WillowLaneVictorian") continue;
                var layout = TownLayout.HouseLayout(lot);
                if (layout?.rooms == null) return;
                foreach (var room in layout.rooms)
                {
                    if (room.n != "Nursery") continue;
                    var at = new GameObject("MusicBox").transform;
                    at.SetParent(transform, false);
                    at.position = lot.Offset + (ManorLayout.V(room.min) + ManorLayout.V(room.max)) * 0.5f;
                    musicBox = Sfx.Loop("music_box", at, 0.45f, true, 16f);
                    return;
                }
            }
        }
    }
}
