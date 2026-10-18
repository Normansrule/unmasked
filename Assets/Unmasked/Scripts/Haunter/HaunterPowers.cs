using System;
using System.Collections.Generic;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    public enum HaunterPower
    {
        /// <summary>Every door near the Haunter slams shut and jams.</summary>
        SlamDoors,
        /// <summary>A spooky fog bank rolls in; fear creeps up inside it.</summary>
        Fog,
        /// <summary>Opens a trapdoor under a nearby Solver: down they go.</summary>
        Trapdoor,
        /// <summary>A fake ghost floats at the nearest Solver. A flashlight beam pops it.</summary>
        PhantomIllusion,
        /// <summary>Put on the costume and physically hunt Solvers for a while.</summary>
        CostumeChase,
        /// <summary>Tonight's villain's own power (see VillainPowers): Pumpkin Toss, Wail, Wisp Lure or Hex.</summary>
        Signature
    }

    [Serializable]
    public class HaunterPowerSpec
    {
        public HaunterPower Power;
        public float Cost = 15f;
        public float Cooldown = 12f;
        public float Fear = 15f;
        [Tooltip("How far from the Haunter the power reaches.")]
        public float Radius = 12f;
        [Range(0f, 1f), Tooltip("Chance that using this leaves a true clue behind.")]
        public float LeakChance = 0.1f;
        [Tooltip("For lasting powers (fog, phantom, chase): how long they last.")]
        public float Duration = 15f;

        public HaunterPowerSpec(HaunterPower power, float cost, float cooldown, float fear, float radius, float leak, float duration)
        {
            Power = power; Cost = cost; Cooldown = cooldown; Fear = fear; Radius = radius; LeakChance = leak; Duration = duration;
        }
    }

    /// <summary>
    /// The Haunter's spectral powers: five shared ones (keys 1-5) and the villain's signature power
    /// (key 6 or Q). Costs, cooldowns and phase rules are enforced on the server; every use risks leaking a clue.
    /// </summary>
    public class HaunterPowers : NetworkBehaviour
    {
        public List<HaunterPowerSpec> Powers = new()
        {
            //                   power                           cost  cd   fear  radius leak   duration
            new HaunterPowerSpec(HaunterPower.SlamDoors,        15f, 12f, 15f,  12f, 0.10f,  8f),
            new HaunterPowerSpec(HaunterPower.Fog,              20f, 25f,  3f,   6f, 0.10f, 20f),
            new HaunterPowerSpec(HaunterPower.Trapdoor,         25f, 20f, 30f,  15f, 0.15f,  3f),
            new HaunterPowerSpec(HaunterPower.PhantomIllusion,  25f, 20f, 25f,  15f, 0.00f, 12f),
            new HaunterPowerSpec(HaunterPower.CostumeChase,     40f, 60f, 35f,   0f, 0.20f, 20f),
            new HaunterPowerSpec(HaunterPower.Signature,        30f, 25f, 30f,  18f, 0.15f, 10f),
        };

        /// <summary>What the power in this slot is called tonight (the signature power takes the villain's name for it).</summary>
        public string DisplayName(HaunterPowerSpec spec)
        {
            if (spec.Power != HaunterPower.Signature) return spec.Power.ToString();
            var game = MysteryGameManager.Instance;
            return game != null ? Costumes.PowerOf(game.Villain.Value) : "Signature";
        }

        NetworkList<double> readyTimes;
        HaunterController haunter;
        float lastRequestTime = -1000f;

        void Awake()
        {
            haunter = GetComponent<HaunterController>();
            readyTimes = new NetworkList<double>();
        }

        public override void OnNetworkSpawn()
        {
            if (!IsServer) return;
            for (int i = 0; i < Powers.Count; i++) readyTimes.Add(0);
        }

        public float CooldownRemaining(int slot)
        {
            if (slot < 0 || slot >= readyTimes.Count || MysteryGameManager.Instance == null) return 0f;
            return Mathf.Max(0f, (float)(readyTimes[slot] - MysteryGameManager.Instance.Now));
        }

        /// <summary>Allowed in the current phase and form? (Ignores cost and cooldown.)</summary>
        public bool IsAllowedNow(HaunterPowerSpec spec)
        {
            var game = MysteryGameManager.Instance;
            if (game == null || haunter.IsStunned || haunter.IsPossessing) return false;
            return game.Phase.Value switch
            {
                MatchPhase.Investigation => spec.Power != HaunterPower.CostumeChase || !haunter.IsPhysical,
                // During the trap hunt the Haunter is stuck in costume, but can still cause chaos.
                MatchPhase.Trap => spec.Power != HaunterPower.CostumeChase,
                _ => false
            };
        }

        /// <summary>Owner</summary>
        public void Activate(int slot)
        {
            if (slot >= 0 && slot < Powers.Count && CooldownRemaining(slot) <= 0f) ActivateRpc(slot);
        }

        [Rpc(SendTo.Server)]
        void ActivateRpc(int slot, RpcParams p = default)
        {
            if (p.Receive.SenderClientId != OwnerClientId || Time.time - lastRequestTime < 0.15f) return;
            lastRequestTime = Time.time;

            if (slot < 0 || slot >= Powers.Count) return;
            var spec = Powers[slot];
            if (CooldownRemaining(slot) > 0f || !IsAllowedNow(spec) || !haunter.Ectoplasm.TrySpend(spec.Cost)) return;

            if (!Execute(spec))
            {
                haunter.Ectoplasm.Add(spec.Cost);
                return;
            }

            readyTimes[slot] = MysteryGameManager.Instance.Now + spec.Cooldown;
            MysteryGameManager.Instance.Mystery.TryLeakClue(transform.position, spec.LeakChance, PlayerAgent.ForClient(OwnerClientId));
        }

        bool Execute(HaunterPowerSpec spec)
        {
            switch (spec.Power)
            {
                case HaunterPower.SlamDoors:
                {
                    int slammed = 0;
                    foreach (var door in FindObjectsByType<HouseDoor>(FindObjectsSortMode.None))
                    {
                        if (Vector3.Distance(door.transform.position, transform.position) > spec.Radius) continue;
                        door.SlamShut(spec.Duration);
                        FearMeter.ScareSolversInRadius(door.transform.position, 7f, spec.Fear, door.transform, false);
                        slammed++;
                    }
                    return slammed > 0;
                }

                case HaunterPower.Fog:
                {
                    var go = Instantiate(MysteryGameManager.Instance.FogPrefab, transform.position, Quaternion.identity);
                    go.GetComponent<FogCloud>().Initialize(spec.Radius, spec.Fear, spec.Duration);
                    go.GetComponent<NetworkObject>().Spawn(true);
                    return true;
                }

                case HaunterPower.Trapdoor:
                    foreach (var trapdoor in FindObjectsByType<Trapdoor>(FindObjectsSortMode.None))
                        if (Vector3.Distance(trapdoor.transform.position, transform.position) <= spec.Radius && trapdoor.Spring(spec.Fear, spec.Duration))
                            return true;
                    return false;

                case HaunterPower.PhantomIllusion:
                {
                    var go = Instantiate(MysteryGameManager.Instance.PhantomPrefab, transform.position + Vector3.up, Quaternion.identity);
                    go.GetComponent<PhantomIllusion>().Initialize(spec.Fear, spec.Duration, spec.Radius);
                    go.GetComponent<NetworkObject>().Spawn(true);
                    return true;
                }

                case HaunterPower.CostumeChase:
                    if (haunter.IsPhysical) return false;
                    haunter.EnterPhysicalForm(spec.Duration, spec.Fear);
                    return true;

                case HaunterPower.Signature:
                    return VillainPowers.Use(MysteryGameManager.Instance.Villain.Value, transform.position, spec.Fear, spec.Radius, spec.Duration, transform);
            }
            return false;
        }
    }
}
