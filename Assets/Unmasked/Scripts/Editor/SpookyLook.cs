using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.PostProcessing;

namespace Unmasked.EditorTools
{
    /// <summary>
    /// The Halloween-night look, built from code like everything else: an indigo sky with a moon, violet
    /// ambient light and fog, post-processing (bloom so every jack-o'-lantern glows, a vignette, a purple
    /// and orange colour grade, ambient occlusion, film grain), particle mist, fireflies, embers and bats.
    /// Inspired by LA's "Nights of the Jack" trail and stylized Halloween art (see Docs/ART_DIRECTION.md).
    /// </summary>
    internal static class SpookyLook
    {
        const string Dir = TestRoomBuilder.Root + "/Look";

        static Material glow, smoke;

        /// <summary>Lights, sky, fog, post-processing and the FX helper for the open scene.</summary>
        internal static void Apply(float fogDensity)
        {
            Directory.CreateDirectory(Dir);

            // Sky: a procedural skybox tinted to a deep indigo. The moon light doubles as its "sun" disc.
            var sky = new Material(Shader.Find("Skybox/Procedural"));
            sky.SetFloat("_SunDisk", 2f);
            sky.SetFloat("_SunSize", 0.07f);
            sky.SetFloat("_SunSizeConvergence", 4f);
            sky.SetFloat("_AtmosphereThickness", 0.35f);
            sky.SetColor("_SkyTint", new Color(0.32f, 0.2f, 0.55f));
            sky.SetColor("_GroundColor", new Color(0.08f, 0.05f, 0.1f));
            sky.SetFloat("_Exposure", 0.3f);
            Save(sky, "NightSky");
            RenderSettings.skybox = sky;

            // Violet ambient: brighter from the sky, almost black from the ground.
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.17f, 0.11f, 0.3f);
            RenderSettings.ambientEquatorColor = new Color(0.11f, 0.07f, 0.16f);
            RenderSettings.ambientGroundColor = new Color(0.04f, 0.03f, 0.05f);
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Exponential;
            RenderSettings.fogColor = new Color(0.1f, 0.05f, 0.15f);
            RenderSettings.fogDensity = fogDensity;

            var moon = new GameObject("Moonlight").AddComponent<Light>();
            moon.type = LightType.Directional;
            moon.color = new Color(0.62f, 0.56f, 1f);
            moon.intensity = 0.35f;
            moon.shadows = LightShadows.Soft;
            moon.shadowStrength = 0.8f;
            moon.transform.rotation = Quaternion.Euler(38, 155, 0);
            RenderSettings.sun = moon;

            // Many small lights (jack-o'-lantern arches, string lights, porch displays) look best lit per
            // pixel. The lawns and roads are split into tiles, so each tile only pays for the lights near it.
            QualitySettings.pixelLightCount = Mathf.Max(QualitySettings.pixelLightCount, 12);
            QualitySettings.shadowDistance = Mathf.Max(QualitySettings.shadowDistance, 80f);

            var cam = Camera.main;
            if (cam != null)
            {
                cam.clearFlags = CameraClearFlags.Skybox;
                cam.allowHDR = true;
                cam.farClipPlane = 400f;
                AddPostProcessing(cam);
            }

            var fx = new GameObject("SpookyFX").AddComponent<SpookyFX>();
            fx.Glow = GlowMaterial();
            fx.Smoke = SmokeMaterial();
        }

        static void AddPostProcessing(Camera cam)
        {
            var layer = cam.gameObject.AddComponent<PostProcessLayer>();
            var resources = AssetDatabase.LoadAssetAtPath<PostProcessResources>("Packages/com.unity.postprocessing/PostProcessing/PostProcessResources.asset");
            if (resources == null)
                foreach (var guid in AssetDatabase.FindAssets("t:PostProcessResources"))
                    resources = AssetDatabase.LoadAssetAtPath<PostProcessResources>(AssetDatabase.GUIDToAssetPath(guid));
            if (resources != null) layer.Init(resources);
            else Debug.LogWarning("[Unmasked] PostProcessResources not found: is com.unity.postprocessing installed?");
            layer.volumeLayer = 1; // the Default layer, where the volume below lives
            layer.volumeTrigger = cam.transform;
            layer.antialiasingMode = PostProcessLayer.Antialiasing.SubpixelMorphologicalAntialiasing;

            const string profilePath = Dir + "/SpookyNight.asset";
            AssetDatabase.DeleteAsset(profilePath);
            var profile = ScriptableObject.CreateInstance<PostProcessProfile>();

            var bloom = profile.AddSettings<Bloom>();
            bloom.enabled.Override(true);
            bloom.intensity.Override(3.5f);
            bloom.threshold.Override(0.85f);
            bloom.softKnee.Override(0.6f);
            bloom.diffusion.Override(7.5f);
            bloom.color.Override(new Color(1f, 0.78f, 0.6f));

            var vignette = profile.AddSettings<Vignette>();
            vignette.enabled.Override(true);
            vignette.intensity.Override(0.42f);
            vignette.smoothness.Override(0.45f);
            vignette.color.Override(new Color(0.06f, 0f, 0.1f));

            var grade = profile.AddSettings<ColorGrading>();
            grade.enabled.Override(true);
            grade.gradingMode.Override(GradingMode.LowDefinitionRange);
            grade.temperature.Override(-12f);
            grade.tint.Override(18f);
            grade.saturation.Override(12f);
            grade.contrast.Override(18f);
            grade.colorFilter.Override(new Color(0.92f, 0.86f, 1f));

            var ao = profile.AddSettings<AmbientOcclusion>();
            ao.enabled.Override(true);
            ao.mode.Override(AmbientOcclusionMode.ScalableAmbientObscurance);
            ao.intensity.Override(0.7f);
            ao.radius.Override(0.6f);

            var grain = profile.AddSettings<Grain>();
            grain.enabled.Override(true);
            grain.intensity.Override(0.22f);
            grain.size.Override(0.9f);

            AssetDatabase.CreateAsset(profile, profilePath);
            foreach (var s in profile.settings)
            {
                s.hideFlags = HideFlags.HideInInspector | HideFlags.HideInHierarchy;
                AssetDatabase.AddObjectToAsset(s, profile);
            }
            AssetDatabase.SaveAssets();

            var volume = new GameObject("Spooky Post FX").AddComponent<PostProcessVolume>();
            volume.isGlobal = true;
            volume.priority = 1f;
            volume.sharedProfile = profile;
        }

        // -------------------------------------------------------------------
        // Particle materials (a generated soft dot)
        // -------------------------------------------------------------------

        static Texture2D SoftDot()
        {
            string path = Dir + "/SoftDot.png";
            var existing = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            if (existing != null) return existing;

            const int size = 64;
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(size / 2f, size / 2f)) / (size / 2f);
                    float a = Mathf.Clamp01(1f - d);
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, a * a));
                }
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(path);
            if (AssetImporter.GetAtPath(path) is TextureImporter importer)
            {
                importer.alphaIsTransparency = true;
                importer.wrapMode = TextureWrapMode.Clamp;
                importer.mipmapEnabled = false;
                importer.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        internal static Material GlowMaterial()
        {
            if (glow != null) return glow;
            var shader = Shader.Find("Legacy Shaders/Particles/Additive") ?? Shader.Find("Particles/Standard Unlit");
            glow = new Material(shader) { mainTexture = SoftDot() };
            if (glow.HasProperty("_TintColor")) glow.SetColor("_TintColor", new Color(0.5f, 0.5f, 0.5f, 0.5f));
            return glow = Save(glow, "FxGlow");
        }

        internal static Material SmokeMaterial()
        {
            if (smoke != null) return smoke;
            var shader = Shader.Find("Legacy Shaders/Particles/Alpha Blended") ?? Shader.Find("Particles/Standard Unlit");
            smoke = new Material(shader) { mainTexture = SoftDot() };
            if (smoke.HasProperty("_TintColor")) smoke.SetColor("_TintColor", new Color(0.5f, 0.5f, 0.5f, 0.5f));
            return smoke = Save(smoke, "FxSmoke");
        }

        /// <summary>Forget cached materials (they are re-made on every build).</summary>
        internal static void Reset()
        {
            glow = null;
            smoke = null;
        }

        static Material Save(Material mat, string name)
        {
            string path = $"{Dir}/{name}.mat";
            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(mat, path);
            return mat;
        }

        // -------------------------------------------------------------------
        // Ambient particles
        // -------------------------------------------------------------------

        /// <summary>A looping particle field filling a box: mist, fireflies, embers.</summary>
        internal static ParticleSystem Field(string name, Transform parent, Vector3 center, Vector3 size, bool additive,
            Color a, Color b, float rate, Vector2 lifetime, Vector2 particleSize, Vector2 speed, float rise, int max, float noise)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = center;
            go.layer = 1; // TransparentFX: the town map camera skips it
            var ps = go.AddComponent<ParticleSystem>();
            var main = ps.main;
            main.loop = true;
            main.prewarm = true;
            main.duration = 5f;
            main.startLifetime = new ParticleSystem.MinMaxCurve(lifetime.x, lifetime.y);
            main.startSize = new ParticleSystem.MinMaxCurve(particleSize.x, particleSize.y);
            main.startSpeed = new ParticleSystem.MinMaxCurve(speed.x, speed.y);
            main.startColor = new ParticleSystem.MinMaxGradient(a, b);
            main.maxParticles = max;
            main.gravityModifier = -rise / -Physics.gravity.y;
            main.simulationSpace = ParticleSystemSimulationSpace.World;

            var emission = ps.emission;
            emission.rateOverTime = rate;

            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = size;

            var fade = ps.colorOverLifetime;
            fade.enabled = true;
            var gradient = new Gradient();
            gradient.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
                             new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.3f), new GradientAlphaKey(1f, 0.7f), new GradientAlphaKey(0f, 1f) });
            fade.color = gradient;

            if (noise > 0f)
            {
                var n = ps.noise;
                n.enabled = true;
                n.strength = noise;
                n.frequency = 0.35f;
            }

            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = additive ? GlowMaterial() : SmokeMaterial();
            r.sortingFudge = additive ? 0f : 10f;
            return ps;
        }

        internal static void Mist(Transform parent, Vector3 center, Vector3 size) =>
            Field("Ground Mist", parent, center, size, false, new Color(0.5f, 0.42f, 0.68f, 0.14f), new Color(0.3f, 0.24f, 0.45f, 0.1f),
                  size.x * size.z / 220f, new Vector2(14f, 22f), new Vector2(6f, 11f), new Vector2(0.1f, 0.35f), 0f, 500, 0.2f);

        internal static void Fireflies(Transform parent, Vector3 center, Vector3 size, Color color) =>
            Field("Fireflies", parent, center, size, true, color, Color.Lerp(color, Color.white, 0.4f),
                  size.x * size.z / 30f, new Vector2(4f, 8f), new Vector2(0.06f, 0.14f), new Vector2(0f, 0.2f), 0.05f, 200, 0.8f);

        internal static void Embers(Transform parent, Vector3 center, Vector3 size) =>
            Field("Embers", parent, center, size, true, new Color(1f, 0.55f, 0.15f), new Color(1f, 0.8f, 0.35f),
                  size.x * size.z / 12f, new Vector2(2f, 4f), new Vector2(0.04f, 0.1f), new Vector2(0.1f, 0.4f), 0.5f, 300, 0.5f);

        /// <summary>Bats circling the roof (animated by BatSwarm).</summary>
        internal static void Bats(Transform parent, Vector3 center, float radius, int count)
        {
            var swarm = new GameObject("Bats");
            swarm.transform.SetParent(parent, false);
            swarm.transform.localPosition = center;
            var dark = TestRoomBuilder.ColorMaterial(new Color(0.06f, 0.04f, 0.08f), "solid");
            var eye = TestRoomBuilder.ColorMaterial(new Color(1f, 0.25f, 0.2f), "emissive", 3f);
            for (int i = 0; i < count; i++)
            {
                var bat = new GameObject($"Bat{i}").transform;
                bat.SetParent(swarm.transform, false);
                float s = 0.8f + 0.4f * ((i * 7) % 5) / 4f;
                bat.localScale = Vector3.one * s;
                foreach (int side in new[] { -1, 1 })
                {
                    var wing = new GameObject(side < 0 ? "WingL" : "WingR").transform;
                    wing.SetParent(bat, false);
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "Membrane", wing, new Vector3(side * 0.28f, 0f, -0.02f), new Vector3(0.5f, 0.02f, 0.26f), dark, false);
                    TestRoomBuilder.Shape(PrimitiveType.Cube, "Tip", wing, new Vector3(side * 0.5f, 0f, 0.05f), new Vector3(0.12f, 0.02f, 0.14f), dark, false)
                        .transform.localRotation = Quaternion.Euler(0, side * 30, 0);
                }
                TestRoomBuilder.Shape(PrimitiveType.Sphere, "Body", bat, Vector3.zero, new Vector3(0.14f, 0.12f, 0.24f), dark, false);
                TestRoomBuilder.Shape(PrimitiveType.Sphere, "Eyes", bat, new Vector3(0, 0.02f, 0.12f), new Vector3(0.08f, 0.025f, 0.02f), eye, false);
            }
            var anim = swarm.AddComponent<BatSwarm>();
            anim.Radius = radius;
        }
    }
}
