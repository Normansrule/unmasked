using UnityEngine;

namespace Unmasked
{
    public enum SpookyFxKind : byte { PumpkinBurst, Wail, Wisps, Hex, Unmask, Hoofbeats, ClueFound, AlibiHolds, AlibiBroken, TrapSting }

    /// <summary>
    /// One-shot particle bursts (cosmetic, local to each machine). The level builders put one of these in
    /// the scene with the particle materials it needs; MysteryGameManager.PlayFx triggers it everywhere.
    /// </summary>
    public class SpookyFX : MonoBehaviour
    {
        public static SpookyFX Instance { get; private set; }

        [Tooltip("Additive soft dot: embers, sparks, wisps.")]
        public Material Glow;
        [Tooltip("Alpha-blended soft dot: smoke and mist.")]
        public Material Smoke;

        void Awake() => Instance = this;

        public static void Play(SpookyFxKind kind, Vector3 at)
        {
            PlaySound(kind, at);
            if (Instance == null) return;
            switch (kind)
            {
                case SpookyFxKind.PumpkinBurst:
                    Instance.Burst(at, new Color(1f, 0.55f, 0.1f), new Color(1f, 0.85f, 0.3f), 70, 6f, 0.9f, 0.25f, Instance.Glow, -4f);
                    Instance.Burst(at, new Color(0.2f, 0.12f, 0.1f, 0.6f), new Color(0.35f, 0.2f, 0.15f, 0.4f), 20, 1.5f, 2.2f, 1.2f, Instance.Smoke, 0.3f);
                    Instance.Flash(at, new Color(1f, 0.55f, 0.15f), 8f, 4f, 0.5f);
                    break;
                case SpookyFxKind.Wail:
                    Instance.Ring(at, new Color(0.5f, 1f, 1f), 90, 9f, 1.2f);
                    Instance.Flash(at, new Color(0.5f, 1f, 1f), 14f, 3f, 0.8f);
                    break;
                case SpookyFxKind.Wisps:
                    Instance.Burst(at, new Color(0.6f, 1f, 0.5f), new Color(1f, 0.8f, 0.3f), 40, 2f, 1.6f, 0.2f, Instance.Glow, 0.5f);
                    break;
                case SpookyFxKind.Hex:
                    Instance.Burst(at, new Color(0.75f, 1f, 0.3f), new Color(0.6f, 0.2f, 0.8f), 50, 2.5f, 1.4f, 0.18f, Instance.Glow, 1.2f);
                    Instance.Flash(at, new Color(0.7f, 1f, 0.3f), 6f, 3f, 0.5f);
                    break;
                case SpookyFxKind.Unmask:
                    Instance.Burst(at, new Color(1f, 0.95f, 0.5f), new Color(1f, 0.5f, 0.9f), 120, 7f, 1.6f, 0.15f, Instance.Glow, -3f);
                    break;
            }
        }

        static void PlaySound(SpookyFxKind kind, Vector3 at)
        {
            switch (kind)
            {
                case SpookyFxKind.PumpkinBurst: Sfx.Play("pumpkin_burst", at, 1f, 35f); break;
                case SpookyFxKind.Wail: Sfx.Play("banshee_wail", at, 1f, 60f); break;
                case SpookyFxKind.Wisps: Sfx.Play("wisp_chime", at, 0.8f, 30f); break;
                case SpookyFxKind.Hex: Sfx.Play("hex", at, 0.9f, 30f); break;
                case SpookyFxKind.Unmask: Sfx.Play2D("unmask", 0.9f); break;
                case SpookyFxKind.Hoofbeats: Sfx.Play("hoofbeats", at, 1f, 50f); break;
                case SpookyFxKind.ClueFound: Sfx.Play2D("clue_chime", 0.6f); break;
                case SpookyFxKind.AlibiHolds: Sfx.Play2D("alibi_holds", 0.6f); break;
                case SpookyFxKind.AlibiBroken: Sfx.Play2D("alibi_broken", 0.8f); break;
                case SpookyFxKind.TrapSting: Sfx.Play2D("trap_sting", 0.85f); break;
            }
        }

        ParticleSystem NewSystem(Vector3 at, Material material, float lifetime)
        {
            var go = new GameObject("FX");
            go.transform.position = at;
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.duration = 0.2f;
            main.loop = false;
            main.startLifetime = new ParticleSystem.MinMaxCurve(lifetime * 0.6f, lifetime);
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            var emission = ps.emission;
            emission.rateOverTime = 0f;
            var size = ps.sizeOverLifetime;
            size.enabled = true;
            size.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 1f, 1f, 0f));
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = material;
            Destroy(go, lifetime + 0.5f);
            return ps;
        }

        void Burst(Vector3 at, Color a, Color b, int count, float speed, float lifetime, float particleSize, Material material, float gravity)
        {
            if (material == null) return;
            var ps = NewSystem(at, material, lifetime);
            var main = ps.main;
            main.startColor = new ParticleSystem.MinMaxGradient(a, b);
            main.startSpeed = new ParticleSystem.MinMaxCurve(speed * 0.3f, speed);
            main.startSize = new ParticleSystem.MinMaxCurve(particleSize * 0.5f, particleSize);
            main.gravityModifier = gravity / Physics.gravity.y;
            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Sphere;
            shape.radius = 0.2f;
            ps.emission.SetBursts(new[] { new ParticleSystem.Burst(0f, (short)count) });
            ps.Play();
        }

        void Ring(Vector3 at, Color color, int count, float speed, float lifetime)
        {
            if (Glow == null) return;
            var ps = NewSystem(at, Glow, lifetime);
            var main = ps.main;
            main.startColor = color;
            main.startSpeed = speed;
            main.startSize = 0.3f;
            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Circle;
            shape.radius = 0.3f;
            shape.rotation = new Vector3(90f, 0f, 0f);
            ps.emission.SetBursts(new[] { new ParticleSystem.Burst(0f, (short)count) });
            ps.Play();
        }

        void Flash(Vector3 at, Color color, float range, float intensity, float seconds)
        {
            var go = new GameObject("FX Flash");
            go.transform.position = at;
            var light = go.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = color;
            light.range = range;
            light.intensity = intensity;
            go.AddComponent<FadeLight>().Seconds = seconds;
        }
    }

    /// <summary>Fades a light out and removes it.</summary>
    public class FadeLight : MonoBehaviour
    {
        public float Seconds = 0.5f;
        Light lamp;
        float start, from;

        void Start()
        {
            lamp = GetComponent<Light>();
            start = Time.time;
            from = lamp.intensity;
        }

        void Update()
        {
            float u = (Time.time - start) / Seconds;
            lamp.intensity = from * (1f - u);
            if (u >= 1f) Destroy(gameObject);
        }
    }
}
