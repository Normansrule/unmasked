namespace Unmasked
{
    /// <summary>
    /// Anything a Solver can press E on: clues, doors, lamps, trap parts, suspects, a panicking friend.
    /// Interact only ever runs on the server, after SolverController has checked range, line of sight
    /// and rate limits. Put it on the same GameObject as the NetworkObject (or a parent of the collider).
    /// </summary>
    public interface IInteractable
    {
        bool CanInteract(SolverController solver);
        string GetPrompt(SolverController solver);
        void Interact(SolverController solver);
    }

    /// <summary>
    /// Hollow Creek: anything in a house (or the van) that must go back to how it was when the club
    /// drives back to HQ for another night. Server only; MysteryGameManager.StartNextNight calls it.
    /// </summary>
    public interface INewNight
    {
        void ServerNewNight();
    }
}
