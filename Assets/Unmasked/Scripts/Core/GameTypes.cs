using System;
using Unity.Collections;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    public enum MatchPhase : byte
    {
        WaitingToStart,
        /// <summary>The Haunter secretly picks which suspect they really are.</summary>
        Setup,
        /// <summary>
        /// Hollow Creek only: a call came in. The Solvers drive the van from HQ to the haunted house;
        /// the investigation starts when the first one steps onto the lot.
        /// </summary>
        Dispatch,
        /// <summary>Solvers hunt clues until dawn.</summary>
        Investigation,
        /// <summary>Right suspect named: build the trap and catch the costumed Haunter.</summary>
        Trap,
        /// <summary>The Haunter is caught and the mask comes off.</summary>
        Unmasking,
        Ended
    }

    public enum PlayerSide : byte { Solver, Haunter }

    public enum SolverRole : byte { Sleuth, Techie, Brawn, Snacker }

    /// <summary>
    /// The legend the Haunter dresses up as. Public: everyone sees the costume. Who is under it is the secret.
    /// Names, legends and models live in Resources/Costumes.json (Docs/tools/make_costumes.py).
    /// </summary>
    public enum VillainKind : byte { HeadlessHorseman, Banshee, StingyJack, BabaYaga }

    /// <summary>
    /// A special night, rolled when a call comes in (Hollow Creek). Public: the HUD announces it.
    /// Names and blurbs live in Resources/HollowCreek.json (Docs/tools/make_town.py).
    /// </summary>
    public enum NightEvent : byte { None, BloodMoon, Thunderstorm, PeaSoupFog, PowerOutage, HarvestFestival }

    public enum MatchWinner : byte { None, Solvers, Haunter }

    public enum MatchEndReason : byte { None, Unmasked, Dawn, WrongAccusations, SolversScaredOut, Escaped }

    /// <summary>
    /// Suspect habits and belongings. A clue points at every suspect sharing one of its traits,
    /// so overlapping traits are what make Solvers deduce instead of guess.
    /// </summary>
    [Flags]
    public enum Trait
    {
        None = 0,
        MuddyBoots = 1 << 0,
        Perfume = 1 << 1,
        CigarAsh = 1 << 2,
        Flour = 1 << 3,
        MasterKeys = 1 << 4,
        Gardening = 1 << 5,
        Jewelry = 1 << 6,
        LeatherGloves = 1 << 7
    }

    /// <summary>Everything a player may know about a suspect. Never says who the culprit is.</summary>
    public struct SuspectInfo : INetworkSerializable, IEquatable<SuspectInfo>
    {
        public FixedString32Bytes Id;
        public FixedString64Bytes Name;
        public FixedString64Bytes Occupation;
        public FixedString512Bytes Bio;
        public FixedString512Bytes Alibi;
        /// <summary>The room their alibi puts them in (in the house or around town); empty if it can't be checked.</summary>
        public FixedString32Bytes AlibiRoom;
        public int Traits;

        public void NetworkSerialize<T>(BufferSerializer<T> serializer) where T : IReaderWriter
        {
            serializer.SerializeValue(ref Id);
            serializer.SerializeValue(ref Name);
            serializer.SerializeValue(ref Occupation);
            serializer.SerializeValue(ref Bio);
            serializer.SerializeValue(ref Alibi);
            serializer.SerializeValue(ref AlibiRoom);
            serializer.SerializeValue(ref Traits);
        }

        public bool Equals(SuspectInfo other) => Id == other.Id && Traits == other.Traits;
    }

    /// <summary>
    /// A clue the Solvers found. Clue contents only reach clients once discovered, and whether
    /// it was a planted fake never leaves the server.
    /// </summary>
    public struct DiscoveredClue : INetworkSerializable, IEquatable<DiscoveredClue>
    {
        public int InstanceId;
        public FixedString32Bytes ClueId;
        public FixedString64Bytes Name;
        public FixedString512Bytes Description;
        public int Traits;
        public Vector3 Location;
        public float DiscoveredAt;
        public ulong DiscoveredBy;

        public void NetworkSerialize<T>(BufferSerializer<T> serializer) where T : IReaderWriter
        {
            serializer.SerializeValue(ref InstanceId);
            serializer.SerializeValue(ref ClueId);
            serializer.SerializeValue(ref Name);
            serializer.SerializeValue(ref Description);
            serializer.SerializeValue(ref Traits);
            serializer.SerializeValue(ref Location);
            serializer.SerializeValue(ref DiscoveredAt);
            serializer.SerializeValue(ref DiscoveredBy);
        }

        public bool Equals(DiscoveredClue other) => InstanceId == other.InstanceId;
    }

    /// <summary>What a suspect said in an interview. The culprit lies.</summary>
    public struct InterviewNote : INetworkSerializable, IEquatable<InterviewNote>
    {
        public FixedString32Bytes SpeakerId;
        public FixedString32Bytes SuspiciousOfId;
        public FixedString512Bytes Statement;
        public ulong Interviewer;
        /// <summary>Server time the answer was given (MysteryGameManager.NightClock turns it into a time of night).</summary>
        public float At;

        public void NetworkSerialize<T>(BufferSerializer<T> serializer) where T : IReaderWriter
        {
            serializer.SerializeValue(ref SpeakerId);
            serializer.SerializeValue(ref SuspiciousOfId);
            serializer.SerializeValue(ref Statement);
            serializer.SerializeValue(ref Interviewer);
            serializer.SerializeValue(ref At);
        }

        public bool Equals(InterviewNote other) => SpeakerId == other.SpeakerId && Statement == other.Statement;
    }
}
