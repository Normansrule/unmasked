using System.Collections.Generic;
using Unity.Collections;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// One per connected player (Netcode's player prefab). Holds public per-player state and carries
    /// the match-level requests. The pawn (Solver or Haunter) is spawned separately by
    /// MysteryGameManager. The Haunter's secret identity is deliberately NOT stored here; only the
    /// Haunter's own machine is told, through an owner-only RPC.
    /// </summary>
    public class PlayerAgent : NetworkBehaviour, INewNight
    {
        public static PlayerAgent Local { get; private set; }
        public static readonly List<PlayerAgent> All = new();

        public static PlayerAgent ForClient(ulong clientId) => All.Find(a => a.OwnerClientId == clientId);

        public readonly NetworkVariable<PlayerSide> Side = new();
        public readonly NetworkVariable<SolverRole> Role = new();
        public readonly NetworkVariable<int> PanicCount = new();
        public readonly NetworkVariable<bool> ScaredOut = new();
        public readonly NetworkVariable<int> CluesFound = new();
        public readonly NetworkVariable<int> CarriedTrapPieces = new();

        /// <summary>Server only: the pawn this player currently controls.</summary>
        public NetworkObject Pawn { get; set; }

        /// <summary>Server only: anti-spam bookkeeping.</summary>
        public float LastAccusationTime { get; set; } = -1000f;

        /// <summary>Only ever set on the Haunter's own machine.</summary>
        public string LocalSecretIdentity { get; private set; }
        public float LastClueLeakTime { get; private set; } = -1000f;

        float lastRequestTime = -1000f;

        public override void OnNetworkSpawn()
        {
            All.Add(this);
            if (IsOwner) Local = this;
            if (IsServer && MysteryGameManager.Instance != null && MysteryGameManager.Instance.IsSpawned)
                MysteryGameManager.Instance.OnPlayerJoined(this);
        }

        public override void OnNetworkDespawn()
        {
            All.Remove(this);
            if (Local == this) Local = null;
            if (IsServer && MysteryGameManager.Instance != null)
                MysteryGameManager.Instance.OnPlayerLeft(this);
        }

        bool Accept(RpcParams p)
        {
            // Only the owning client may speak for this player, and not too often.
            if (p.Receive.SenderClientId != OwnerClientId) return false;
            if (Time.time - lastRequestTime < 0.2f) return false;
            lastRequestTime = Time.time;
            return true;
        }

        [Rpc(SendTo.Server)]
        public void RequestSideRpc(PlayerSide side, RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleSideRequest(this, side);
        }

        [Rpc(SendTo.Server)]
        public void RequestRoleRpc(SolverRole role, RpcParams p = default)
        {
            if (Accept(p) && MysteryGameManager.Instance.Phase.Value <= MatchPhase.Setup) Role.Value = role;
        }

        [Rpc(SendTo.Server)]
        public void ChooseIdentityRpc(FixedString32Bytes suspectId, RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleIdentityChoice(this, suspectId.ToString());
        }

        [Rpc(SendTo.Server)]
        public void ChooseVillainRpc(VillainKind villain, RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleVillainChoice(this, villain);
        }

        /// <summary>Hollow Creek: pick tonight's call on the HQ call board.</summary>
        [Rpc(SendTo.Server)]
        public void ChooseCallRpc(FixedString32Bytes houseId, RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleCallChoice(this, houseId.ToString());
        }

        /// <summary>Hollow Creek, host only: stop waiting at HQ and send the van now.</summary>
        [Rpc(SendTo.Server)]
        public void LeaveNowRpc(RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleLeaveNow(this);
        }

        /// <summary>Hollow Creek, host only, at HQ: wipe the saved progress and start the town over.</summary>
        [Rpc(SendTo.Server)]
        public void StartOverRpc(RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleStartOver(this);
        }

        [Rpc(SendTo.Server)]
        public void AccuseRpc(FixedString32Bytes suspectId, RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleAccusation(this, suspectId.ToString());
        }

        [Rpc(SendTo.Server)]
        public void CheckAlibiRpc(FixedString32Bytes suspectId, RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleAlibiCheck(this, suspectId.ToString());
        }

        [Rpc(SendTo.Server)]
        public void SetSuspectClearedRpc(FixedString32Bytes suspectId, bool cleared, RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleBoardMark(this, suspectId.ToString(), cleared);
        }

        /// <summary>Server: a fresh night at HQ. Sides and roles stay; tonight's tallies start over.</summary>
        public void ServerNewNight()
        {
            if (!IsServer) return;
            PanicCount.Value = 0;
            ScaredOut.Value = false;
            CluesFound.Value = 0;
            CarriedTrapPieces.Value = 0;
            SendSecretIdentity(null);
        }

        /// <summary>Host only: after a case, drive back to HQ and wait for the next call.</summary>
        [Rpc(SendTo.Server)]
        public void NextNightRpc(RpcParams p = default)
        {
            if (Accept(p)) MysteryGameManager.Instance.HandleNextNight(this);
        }

        /// <summary>Server: tell this player (only) who they secretly are.</summary>
        public void SendSecretIdentity(string suspectId) => SecretIdentityRpc(suspectId ?? string.Empty);

        [Rpc(SendTo.Owner)]
        void SecretIdentityRpc(FixedString32Bytes suspectId)
        {
            LocalSecretIdentity = suspectId.ToString();
        }

        /// <summary>Server: one of this Haunter's actions left a clue behind.</summary>
        public void NotifyClueLeaked(Vector3 where) => ClueLeakedRpc(where);

        [Rpc(SendTo.Owner)]
        void ClueLeakedRpc(Vector3 where)
        {
            LastClueLeakTime = Time.time;
        }

        /// <summary>Server: a short message for this player only.</summary>
        public void Tell(string message) => TellRpc(message);

        [Rpc(SendTo.Owner)]
        void TellRpc(FixedString128Bytes message)
        {
            GameHUD.Toast(message.ToString());
        }
    }
}
