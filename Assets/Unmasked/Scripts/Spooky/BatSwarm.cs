using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Bats circling the manor roof. Each child is a bat with WingL and WingR children. Cosmetic and local.
    /// </summary>
    public class BatSwarm : MonoBehaviour
    {
        public float Radius = 14f;
        public float Height = 3f;
        public float Speed = 0.35f;
        public float FlapSpeed = 18f;

        Transform[] bats;
        float[] offsets;

        void Start()
        {
            bats = new Transform[transform.childCount];
            offsets = new float[bats.Length];
            for (int i = 0; i < bats.Length; i++)
            {
                bats[i] = transform.GetChild(i);
                offsets[i] = i * 2.399f; // golden angle spreads them out
            }
        }

        void Update()
        {
            float t = Time.time;
            for (int i = 0; i < bats.Length; i++)
            {
                float o = offsets[i];
                float a = t * Speed * (1f + 0.15f * Mathf.Sin(o)) + o;
                float r = Radius * (0.7f + 0.3f * Mathf.Sin(t * 0.3f + o * 1.7f));
                var p = new Vector3(Mathf.Cos(a) * r, Height * Mathf.Sin(t * 0.7f + o), Mathf.Sin(a) * r);
                var bat = bats[i];
                Vector3 next = new(Mathf.Cos(a + 0.05f) * r, p.y, Mathf.Sin(a + 0.05f) * r);
                bat.localPosition = p;
                bat.localRotation = Quaternion.LookRotation(next - p, Vector3.up);
                float flap = Mathf.Sin(t * FlapSpeed + o * 3f) * 55f;
                if (bat.childCount >= 2)
                {
                    bat.GetChild(0).localRotation = Quaternion.Euler(0f, 0f, flap);
                    bat.GetChild(1).localRotation = Quaternion.Euler(0f, 0f, -flap);
                }
            }
        }
    }
}
