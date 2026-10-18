using UnityEngine;

namespace Unmasked
{
    /// <summary>Where pawns appear. Place a few; Haunter-only points are used for the Haunter first.</summary>
    public class SpawnPoint : MonoBehaviour
    {
        public bool HaunterSpawn;

        void OnDrawGizmos()
        {
            Gizmos.color = HaunterSpawn ? new Color(0.5f, 1f, 0.6f) : new Color(1f, 0.8f, 0.3f);
            Gizmos.DrawWireSphere(transform.position + Vector3.up, 0.5f);
        }
    }
}
