using System.Linq;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Server: each villain's signature power (key 6 or Q), shared by a player Haunter and the AI Director.
    ///   Headless Horseman: Pumpkin Toss. A flaming jack-o'-lantern arcs at the nearest Solver in sight and bursts.
    ///   Banshee: Wail. Heard through walls: everyone near is scared, flashlights die and lamps go out.
    ///   Stingy Jack: Wisp Lure. Three will-o'-the-wisps drift out and hunt Solvers. Flashlights pop them.
    ///   Baba Yaga: Hex. The nearest Solver is cursed: a fear spike and a draining flashlight.
    /// Returns false (and the Ectoplasm is refunded) when there was nobody to use it on.
    /// </summary>
    public static class VillainPowers
    {
        public static bool Use(VillainKind villain, Vector3 from, float fear, float radius, float duration, Transform ignore)
        {
            var game = MysteryGameManager.Instance;
            switch (villain)
            {
                case VillainKind.HeadlessHorseman:
                {
                    Vector3 launch = from + Vector3.up * 1.9f;
                    var target = Nearest(from, radius, s => Clear(launch, s, ignore));
                    if (target == null || game.PumpkinPrefab == null) return false;
                    var go = Object.Instantiate(game.PumpkinPrefab, launch, Quaternion.identity);
                    go.GetComponent<PumpkinProjectile>().Initialize(target.transform.position + Vector3.up * 0.5f, fear, 3.5f);
                    go.GetComponent<NetworkObject>().Spawn(true);
                    game.PlayFx(SpookyFxKind.Hoofbeats, from);
                    return true;
                }

                case VillainKind.Banshee:
                {
                    int heard = FearMeter.ScareSolversInRadius(from, radius, fear, ignore, false);
                    if (heard == 0) return false;
                    foreach (var s in SolverController.All)
                        if (Vector3.Distance(s.transform.position, from) <= radius)
                        {
                            s.Flashlight?.ForceOff();
                            PlayerAgent.ForClient(s.OwnerClientId)?.Tell("A BANSHEE WAILS! Your flashlight dies in your hand.");
                        }
                    foreach (var lamp in Object.FindObjectsByType<PossessableLight>(FindObjectsSortMode.None))
                        if (Vector3.Distance(lamp.transform.position, from) <= radius * 0.6f) lamp.ServerCutPower();
                    game.PlayFx(SpookyFxKind.Wail, from + Vector3.up * 1.6f);
                    return true;
                }

                case VillainKind.StingyJack:
                {
                    if (game.WispPrefab == null || Nearest(from, radius * 1.5f, null) == null) return false;
                    for (int i = 0; i < 3; i++)
                    {
                        float a = i * Mathf.PI * 2f / 3f;
                        Vector3 at = from + new Vector3(Mathf.Cos(a), 1.2f, Mathf.Sin(a)) * 1.2f;
                        var go = Object.Instantiate(game.WispPrefab, at, Quaternion.identity);
                        go.GetComponent<PhantomIllusion>().Initialize(fear * 0.6f, duration * 1.5f, radius);
                        go.GetComponent<NetworkObject>().Spawn(true);
                    }
                    game.PlayFx(SpookyFxKind.Wisps, from + Vector3.up * 1.2f);
                    return true;
                }

                case VillainKind.BabaYaga:
                {
                    var target = Nearest(from, radius, null);
                    if (target == null) return false;
                    target.Fear.AddFear(fear, from);
                    target.Flashlight?.AddBattery(-40f);
                    PlayerAgent.ForClient(target.OwnerClientId)?.Tell("Baba Yaga hexed you! Your flashlight is dying...");
                    game.PlayFx(SpookyFxKind.Hex, target.EyePosition);
                    return true;
                }
            }
            return false;
        }

        static SolverController Nearest(Vector3 from, float radius, System.Func<SolverController, bool> extra) =>
            SolverController.All
                .Where(s => s != null && s.IsSpawned && !s.IsPanicked && Vector3.Distance(s.transform.position, from) <= radius && (extra == null || extra(s)))
                .OrderBy(s => Vector3.Distance(s.transform.position, from))
                .FirstOrDefault();

        static bool Clear(Vector3 from, SolverController s, Transform ignore)
        {
            Vector3 to = s.EyePosition - from;
            foreach (var hit in Physics.RaycastAll(from, to.normalized, to.magnitude, ~0, QueryTriggerInteraction.Ignore))
            {
                var root = hit.transform.root;
                if (root == s.transform.root || (ignore != null && root == ignore.root)) continue;
                return false;
            }
            return true;
        }
    }
}
