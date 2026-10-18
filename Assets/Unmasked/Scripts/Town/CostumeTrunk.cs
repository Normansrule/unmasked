using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// The dressing-up trunk at Mystery Club HQ. Once the townsfolk have given the club enough pieces
    /// of the homemade Lantern Watch costume (MysteryGameManager.WatchPieces), a Solver can put it on
    /// for everyone, or take it off again, between cases.
    /// </summary>
    public class CostumeTrunk : NetworkBehaviour, IInteractable
    {
        public bool CanInteract(SolverController solver)
        {
            var game = MysteryGameManager.Instance;
            return game != null && !solver.IsRiding && (game.Phase.Value == MatchPhase.Setup || game.Phase.Value == MatchPhase.Ended);
        }

        public string GetPrompt(SolverController solver)
        {
            var game = MysteryGameManager.Instance;
            if (game == null) return "Dressing-up trunk";
            if (game.WearingWatch.Value) return "Take off the Lantern Watch costume";
            int have = game.WatchPieceCount;
            return have >= MysteryGameManager.WatchPiecesNeeded
                ? $"Put on the Lantern Watch costume ({have} pieces)"
                : $"Dressing-up trunk: {have} of {MysteryGameManager.WatchPiecesNeeded} costume pieces";
        }

        public void Interact(SolverController solver)
        {
            if (IsServer) MysteryGameManager.Instance?.ToggleWatch(solver);
        }
    }
}
