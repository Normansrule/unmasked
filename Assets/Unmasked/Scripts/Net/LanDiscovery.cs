using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using Unity.Netcode;
using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// Finds games on the same Wi-Fi, so friends in one house can join without typing an address.
    /// A host says "here I am" once a second as a small UDP broadcast on <see cref="Port"/>; the
    /// connect menu listens and lists every host it heard in the last few seconds. Plain sockets, no
    /// extra packages and no internet involved. Driven from <see cref="GameHUD"/> through
    /// <see cref="Tick"/>; the socket work is non-blocking and stays on the main thread.
    /// </summary>
    public static class LanDiscovery
    {
        public const int Port = 47777;
        const string Magic = "UNMASKED1";
        const float AnnounceEvery = 1f, ForgetAfter = 4f;

        public class Game
        {
            public string Address, Name, Status, Version;
            public ushort GamePort;
            public int Players;
            public float LastHeard;
            public bool SameVersion => Version == Application.version;
        }

        static readonly Dictionary<string, Game> games = new();
        static UdpClient listener, sender;
        static float nextAnnounce;
        static bool listenFailed;

        /// <summary>Hosts heard recently, newest first.</summary>
        public static IEnumerable<Game> Games
        {
            get
            {
                var list = new List<Game>(games.Values);
                list.Sort((a, b) => b.LastHeard.CompareTo(a.LastHeard));
                return list;
            }
        }

        /// <summary>False if this network or firewall wouldn't let the game listen (the list stays empty).</summary>
        public static bool CanListen => !listenFailed;

        /// <summary>Every frame. In the connect menu it listens; while hosting it announces; otherwise it is quiet.</summary>
        public static void Tick(NetworkManager net, ushort gamePort)
        {
            if (net == null) return;
            bool inMenu = !net.IsClient && !net.IsServer;
            if (inMenu) { StopSending(); Listen(); }
            else
            {
                StopListening();
                if (net.IsServer && net.IsListening && Time.unscaledTime >= nextAnnounce)
                {
                    nextAnnounce = Time.unscaledTime + AnnounceEvery;
                    Announce(net, gamePort);
                }
            }
        }

        static void Listen()
        {
            if (listener == null && !listenFailed)
            {
                try
                {
                    listener = new UdpClient();
                    // Two copies of the game on one computer can both listen.
                    listener.Client.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
                    listener.Client.Bind(new IPEndPoint(IPAddress.Any, Port));
                }
                catch (SocketException e)
                {
                    Debug.LogWarning($"[Unmasked] Can't look for games on this network ({e.SocketErrorCode}). Type the host's address instead.");
                    listenFailed = true;
                    StopListening();
                    return;
                }
            }
            if (listener == null) return;

            try
            {
                while (listener.Available > 0)
                {
                    var from = new IPEndPoint(IPAddress.Any, 0);
                    byte[] data = listener.Receive(ref from);
                    Heard(from.Address, Encoding.UTF8.GetString(data));
                }
            }
            catch (SocketException) { /* a bad packet or a network change: try again next frame */ }

            float now = Time.unscaledTime;
            var stale = new List<string>();
            foreach (var kv in games) if (now - kv.Value.LastHeard > ForgetAfter) stale.Add(kv.Key);
            foreach (var key in stale) games.Remove(key);
        }

        /// <summary>"UNMASKED1 \t version \t name \t game port \t players \t status".</summary>
        static void Heard(IPAddress from, string message)
        {
            var f = message.Split('\t');
            if (f.Length < 6 || f[0] != Magic || !ushort.TryParse(f[3], out var gamePort)) return;
            int.TryParse(f[4], out int players);
            // The same computer shows up from several of its addresses; loopback is the one that always works.
            string address = IPAddress.IsLoopback(from) ? "127.0.0.1" : from.ToString();
            string key = f[2] + ":" + gamePort;
            if (games.TryGetValue(key, out var known) && known.Address == "127.0.0.1") address = "127.0.0.1";
            games[key] = new Game { Address = address, Version = f[1], Name = f[2], GamePort = gamePort, Players = players, Status = f[5], LastHeard = Time.unscaledTime };
        }

        static void Announce(NetworkManager net, ushort gamePort)
        {
            try
            {
                if (sender == null) sender = new UdpClient { EnableBroadcast = true };
                string name = Clean(SystemInfo.deviceName);
                int players = net.ConnectedClientsIds.Count;
                string message = string.Join("\t", Magic, Application.version, name, gamePort.ToString(), players.ToString(), Clean(StatusLine()));
                byte[] data = Encoding.UTF8.GetBytes(message);
                sender.Send(data, data.Length, new IPEndPoint(IPAddress.Broadcast, Port));
                sender.Send(data, data.Length, new IPEndPoint(IPAddress.Loopback, Port)); // a second window on this computer
            }
            catch (SocketException) { /* no network right now: the host keeps working, it just isn't listed */ }
        }

        static string StatusLine()
        {
            var game = MysteryGameManager.Instance;
            if (game == null || !game.IsSpawned) return "Starting";
            return game.Phase.Value switch
            {
                MatchPhase.Setup => game.InTown ? "At HQ, picking a call" : "Picking sides",
                MatchPhase.Dispatch => "Driving to " + game.HouseName,
                MatchPhase.Investigation or MatchPhase.Trap => "On a case at " + game.HouseName,
                MatchPhase.Unmasking or MatchPhase.Ended => "Finishing a case",
                _ => "Waiting for players",
            };
        }

        static string Clean(string s)
        {
            s = (s ?? "").Replace('\t', ' ').Trim();
            if (s.Length == 0) s = "A computer";
            return s.Length > 28 ? s.Substring(0, 28) : s;
        }

        static void StopListening()
        {
            listener?.Close();
            listener = null;
            games.Clear();
        }

        static void StopSending()
        {
            sender?.Close();
            sender = null;
        }

        /// <summary>When the game closes: let go of both sockets.</summary>
        public static void Shutdown()
        {
            StopListening();
            StopSending();
        }
    }
}
