using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Dresses a Solver for their role: the model has one child per role (Sleuth, Techie, Brawn, Snacker)
    /// and only the right one is shown. Cosmetic: reads the owner's replicated role.
    /// </summary>
    public class RoleOutfit : MonoBehaviour
    {
        public Transform Outfits;

        NetworkObject net;
        SolverRole? shown;

        void Awake() => net = GetComponent<NetworkObject>();

        void Update()
        {
            if (Outfits == null || net == null || !net.IsSpawned) return;
            var agent = PlayerAgent.ForClient(net.OwnerClientId);
            var role = agent != null ? agent.Role.Value : SolverRole.Sleuth;
            if (shown == role) return;
            shown = role;
            foreach (Transform child in Outfits)
                child.gameObject.SetActive(child.name == role.ToString());
        }
    }
}
