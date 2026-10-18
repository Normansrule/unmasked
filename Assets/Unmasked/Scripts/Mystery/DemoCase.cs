namespace Unmasked
{
    /// <summary>
    /// The Missing Blackwood Ledger, built in code so the game is playable before any case
    /// assets exist. The data lives in Cases.cs with the other houses' cases.
    /// </summary>
    public static class DemoCase
    {
        public static CaseDefinition BuildBlackwoodManor() => Cases.Build(Cases.DefaultHouse);
    }
}
