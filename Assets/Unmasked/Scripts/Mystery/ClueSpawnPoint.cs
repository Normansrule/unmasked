using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Place plenty of these around a level. At the start of the night the server hides clues at a
    /// random subset, so placement changes every match.
    /// </summary>
    public class ClueSpawnPoint : MonoBehaviour
    {
        void OnDrawGizmos()
        {
            Gizmos.color = new Color(1f, 0.9f, 0.2f);
            Gizmos.DrawWireCube(transform.position + Vector3.up * 0.15f, Vector3.one * 0.3f);
        }
    }
}
