using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// What tonight's special event looks like, on every machine: a red Blood Moon, thunder and rain,
    /// pea-soup fog, a blacked-out street, or the warm glow of the Harvest Festival. Gameplay effects
    /// (scares, ectoplasm, batteries, lamps) are on the server in MysteryGameManager.
    /// </summary>
    public class NightEventFX : MonoBehaviour
    {
        static NightEventFX instance;

        NightEvent shown = NightEvent.None;
        bool captured;
        float baseFog, baseMoonIntensity;
        Color baseFogColor, baseSky, baseEquator, baseGround, baseMoonColor;
        ParticleSystem rain;
        float flash;

        void Awake() => instance = this;

        void Capture()
        {
            captured = true;
            baseFog = RenderSettings.fogDensity;
            baseFogColor = RenderSettings.fogColor;
            baseSky = RenderSettings.ambientSkyColor;
            baseEquator = RenderSettings.ambientEquatorColor;
            baseGround = RenderSettings.ambientGroundColor;
            if (RenderSettings.sun != null)
            {
                baseMoonColor = RenderSettings.sun.color;
                baseMoonIntensity = RenderSettings.sun.intensity;
            }
        }

        /// <summary>Thunderstorm: a flash of lightning (the server calls this on every machine).</summary>
        public static void Lightning(float strength)
        {
            if (instance != null) instance.flash = Mathf.Max(instance.flash, strength);
            Sfx.Play2D("thunder", Mathf.Clamp01(0.5f + strength * 0.4f), Random.Range(0.85f, 1.1f));
        }

        void Update()
        {
            var game = MysteryGameManager.Instance;
            if (!captured) Capture();
            var wanted = game != null && game.IsSpawned && game.Phase.Value >= MatchPhase.Dispatch ? game.Event.Value : NightEvent.None;
            if (wanted != shown) Apply(wanted);

            var moon = RenderSettings.sun;
            if (moon != null)
            {
                float target = MoonIntensity(shown);
                moon.intensity = target + flash * 3f;
                RenderSettings.ambientSkyColor = SkyFor(shown) + Color.white * (flash * 0.5f);
            }
            flash = Mathf.MoveTowards(flash, 0f, Time.deltaTime * 4f);

            if (rain != null && Camera.main != null)
                rain.transform.position = Camera.main.transform.position + Vector3.up * 12f;
        }

        void Apply(NightEvent e)
        {
            shown = e;
            RenderSettings.fogDensity = baseFog;
            RenderSettings.fogColor = baseFogColor;
            RenderSettings.ambientEquatorColor = baseEquator;
            RenderSettings.ambientGroundColor = baseGround;
            if (RenderSettings.sun != null) RenderSettings.sun.color = baseMoonColor;
            if (rain != null) rain.gameObject.SetActive(false);

            switch (e)
            {
                case NightEvent.BloodMoon:
                    if (RenderSettings.sun != null) RenderSettings.sun.color = new Color(1f, 0.28f, 0.22f);
                    RenderSettings.fogColor = new Color(0.22f, 0.04f, 0.06f);
                    RenderSettings.ambientEquatorColor = baseEquator * 0.7f + new Color(0.18f, 0.02f, 0.02f);
                    break;
                case NightEvent.Thunderstorm:
                    RenderSettings.fogDensity = baseFog * 1.6f;
                    RenderSettings.fogColor = new Color(0.08f, 0.08f, 0.12f);
                    MakeRain();
                    break;
                case NightEvent.PeaSoupFog:
                    RenderSettings.fogDensity = baseFog * 3.5f + 0.02f;
                    RenderSettings.fogColor = new Color(0.32f, 0.38f, 0.33f);
                    break;
                case NightEvent.PowerOutage:
                    RenderSettings.ambientEquatorColor = baseEquator * 0.55f;
                    RenderSettings.ambientGroundColor = baseGround * 0.5f;
                    break;
                case NightEvent.HarvestFestival:
                    RenderSettings.fogColor = new Color(0.2f, 0.09f, 0.08f);
                    RenderSettings.ambientEquatorColor = baseEquator + new Color(0.08f, 0.04f, 0f);
                    break;
            }
        }

        float MoonIntensity(NightEvent e) => e switch
        {
            NightEvent.BloodMoon => baseMoonIntensity * 1.2f,
            NightEvent.Thunderstorm => baseMoonIntensity * 0.4f,
            NightEvent.PeaSoupFog => baseMoonIntensity * 0.7f,
            NightEvent.PowerOutage => baseMoonIntensity * 0.8f,
            _ => baseMoonIntensity
        };

        Color SkyFor(NightEvent e) => e switch
        {
            NightEvent.BloodMoon => baseSky * 0.6f + new Color(0.25f, 0.03f, 0.03f),
            NightEvent.Thunderstorm => baseSky * 0.6f,
            NightEvent.PowerOutage => baseSky * 0.6f,
            NightEvent.HarvestFestival => baseSky + new Color(0.06f, 0.03f, 0f),
            _ => baseSky
        };

        void MakeRain()
        {
            if (rain == null)
            {
                var go = new GameObject("Rain");
                go.transform.SetParent(transform, false);
                rain = go.AddComponent<ParticleSystem>();
                rain.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
                var main = rain.main;
                main.loop = true;
                main.startLifetime = 1.1f;
                main.startSpeed = 22f;
                main.startSize = 0.05f;
                main.startColor = new Color(0.7f, 0.8f, 1f, 0.45f);
                main.maxParticles = 3000;
                main.simulationSpace = ParticleSystemSimulationSpace.World;
                var emission = rain.emission;
                emission.rateOverTime = 1800f;
                var shape = rain.shape;
                shape.shapeType = ParticleSystemShapeType.Box;
                shape.scale = new Vector3(40f, 40f, 1f); // local z points down once rotated
                go.transform.rotation = Quaternion.Euler(90f, 0f, 0f); // emit downwards
                var renderer = go.GetComponent<ParticleSystemRenderer>();
                renderer.renderMode = ParticleSystemRenderMode.Stretch;
                renderer.lengthScale = 6f;
                if (SpookyFX.Instance != null && SpookyFX.Instance.Glow != null) renderer.sharedMaterial = SpookyFX.Instance.Glow;
            }
            rain.gameObject.SetActive(true);
            rain.Play();
        }
    }
}
