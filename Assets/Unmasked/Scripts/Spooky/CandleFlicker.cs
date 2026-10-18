using UnityEngine;

namespace Unmasked
{
    /// <summary>A jack-o'-lantern, candle or wisp light that breathes and flickers. Cosmetic.</summary>
    [RequireComponent(typeof(Light))]
    public class CandleFlicker : MonoBehaviour
    {
        [Range(0f, 1f)] public float Amount = 0.25f;
        public float Speed = 7f;
        [Tooltip("Wisps also drift up and down.")]
        public float Bob;
        [Tooltip("Switched off beyond this distance from the camera (Hollow Creek has well over a hundred). 0 = always on.")]
        public float CullDistance = 70f;

        Light lamp;
        float baseIntensity, seed, nextCull;
        Vector3 rest;

        void Awake()
        {
            lamp = GetComponent<Light>();
            baseIntensity = lamp.intensity;
            seed = Random.value * 100f;
            rest = transform.localPosition;
        }

        void Update()
        {
            if (CullDistance > 0f && Time.time >= nextCull)
            {
                nextCull = Time.time + 0.5f + seed * 0.001f;
                var cam = Camera.main;
                lamp.enabled = cam == null || (cam.transform.position - transform.position).sqrMagnitude < CullDistance * CullDistance;
            }
            if (!lamp.enabled) return;
            float n = Mathf.PerlinNoise(seed, Time.time * Speed);
            lamp.intensity = baseIntensity * (1f - Amount + Amount * 2f * n);
            if (Bob > 0f) transform.localPosition = rest + Vector3.up * Mathf.Sin(Time.time * 1.3f + seed) * Bob;
        }
    }
}
