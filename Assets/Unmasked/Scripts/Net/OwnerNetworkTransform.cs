using Unity.Netcode.Components;

namespace Unmasked
{
    /// <summary>
    /// Owner-driven transform sync so player movement feels instant. The server still checks
    /// anything that matters (interaction range, tagging, trap catches) against these positions.
    /// TODO(Online milestone): add server-side speed checks / movement correction.
    /// </summary>
    public class OwnerNetworkTransform : NetworkTransform
    {
        protected override bool OnIsServerAuthoritative() => false;
    }
}
