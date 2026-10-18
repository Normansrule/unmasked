#pragma warning disable CS0067, CS0108, CS0114 // stub file: unused events / hiding are irrelevant
// Stub of Netcode for GameObjects 2.1.1 public API (only the surface this project touches, plus close neighbours).
// SOURCE: Unity-Technologies/com.unity.netcode.gameobjects tag ngo/2.1.1, files
//   Runtime/Core/NetworkBehaviour.cs, NetworkObject.cs, NetworkManager.cs, Runtime/NetworkVariable/*.cs,
//   Runtime/NetworkVariable/Collections/NetworkList.cs, Runtime/Messaging/RpcAttributes.cs, RpcParams.cs,
//   RpcTargets/RpcTarget.cs (SendTo enum), Runtime/Serialization/BufferSerializer.cs, NetworkObjectReference.cs,
//   Runtime/Components/NetworkTransform.cs, NetworkRigidbody*.cs, Runtime/Configuration/*.cs,
//   Runtime/Transports/UTP/UnityTransport.cs.
// Signatures are copied from those files (REAL) unless marked "GUESSED/SIMPLIFIED".
// NOT checked here (done by NGO's IL post-processor inside Unity): RPC method naming (must end in "Rpc"),
// serializability of RPC parameter / NetworkVariable<T> types. check.sh greps for the naming rule separately.
using System;
using System.Collections;
using System.Collections.Generic;
using Unity.Collections;
using UnityEngine;

namespace Unity.Netcode
{
    // ---- Serialization -------------------------------------------------------------------
    public interface IReaderWriter { bool IsReader { get; } bool IsWriter { get; } }   // SIMPLIFIED (real has SerializeValue overloads too)
    public interface INetworkSerializable { void NetworkSerialize<T>(BufferSerializer<T> serializer) where T : IReaderWriter; }
    public interface INetworkSerializeByMemcpy { }
    public struct FastBufferReader : IDisposable { public void Dispose() { } }   // SIMPLIFIED
    public struct FastBufferWriter : IDisposable                                  // SIMPLIFIED (only the overload-selector tag structs are real)
    {
        public void Dispose() { }
        public struct ForPrimitives { }
        public struct ForEnums { }
        public struct ForStructs { }
        public struct ForNetworkSerializable { }
        public struct ForFixedStrings { }
        public struct ForGeneric { }
    }
    public ref struct BufferSerializer<TReaderWriter> where TReaderWriter : IReaderWriter
    {
        public bool IsReader => throw null;
        public bool IsWriter => throw null;
        public FastBufferReader GetFastBufferReader() => throw null;
        public FastBufferWriter GetFastBufferWriter() => throw null;
        public void SerializeValue(ref string s, bool oneByteChars = false) { }
        public void SerializeValue(ref byte value) { }
        public void SerializeValue<T>(ref T value, FastBufferWriter.ForPrimitives unused = default) where T : unmanaged, IComparable, IConvertible, IComparable<T>, IEquatable<T> { }
        public void SerializeValue<T>(ref T[] value, FastBufferWriter.ForPrimitives unused = default) where T : unmanaged, IComparable, IConvertible, IComparable<T>, IEquatable<T> { }
        public void SerializeValue<T>(ref T value, FastBufferWriter.ForEnums unused = default) where T : unmanaged, Enum { }
        public void SerializeValue<T>(ref T[] value, FastBufferWriter.ForEnums unused = default) where T : unmanaged, Enum { }
        public void SerializeValue<T>(ref T value, FastBufferWriter.ForStructs unused = default) where T : unmanaged, INetworkSerializeByMemcpy { }
        public void SerializeValue<T>(ref T[] value, FastBufferWriter.ForStructs unused = default) where T : unmanaged, INetworkSerializeByMemcpy { }
        public void SerializeValue<T>(ref NativeArray<T> value, Allocator allocator, FastBufferWriter.ForGeneric unused = default) where T : unmanaged { }
        public void SerializeValue<T>(ref T value, FastBufferWriter.ForNetworkSerializable unused = default) where T : INetworkSerializable, new() { }
        public void SerializeValue<T>(ref T[] value, FastBufferWriter.ForNetworkSerializable unused = default) where T : INetworkSerializable, new() { }
        public void SerializeValue(ref Vector2 value) { }
        public void SerializeValue(ref Vector2[] value) { }
        public void SerializeValue(ref Vector3 value) { }
        public void SerializeValue(ref Vector3[] value) { }
        public void SerializeValue(ref Vector2Int value) { }
        public void SerializeValue(ref Vector2Int[] value) { }
        public void SerializeValue(ref Vector3Int value) { }
        public void SerializeValue(ref Vector3Int[] value) { }
        public void SerializeValue(ref Vector4 value) { }
        public void SerializeValue(ref Vector4[] value) { }
        public void SerializeValue(ref Quaternion value) { }
        public void SerializeValue(ref Quaternion[] value) { }
        public void SerializeValue(ref Color value) { }
        public void SerializeValue(ref Color[] value) { }
        public void SerializeValue(ref Color32 value) { }
        public void SerializeValue(ref Color32[] value) { }
        public void SerializeValue(ref Ray value) { }
        public void SerializeValue(ref Ray[] value) { }
        public void SerializeValue(ref Ray2D value) { }
        public void SerializeValue(ref Ray2D[] value) { }
        public void SerializeValue<T>(ref T value, FastBufferWriter.ForFixedStrings unused = default) where T : unmanaged, INativeList<byte>, IUTF8Bytes { }
        public void SerializeValue<T>(ref NativeArray<T> value, Allocator allocator) where T : unmanaged, INativeList<byte>, IUTF8Bytes { }
        public void SerializeNetworkSerializable<T>(ref T value) where T : INetworkSerializable, new() { }
    }

    public struct NetworkObjectReference : INetworkSerializable, IEquatable<NetworkObjectReference>
    {
        public ulong NetworkObjectId { get => throw null; internal set => throw null; }
        public NetworkObjectReference(NetworkObject networkObject) => throw null;
        public NetworkObjectReference(GameObject gameObject) => throw null;
        public bool TryGet(out NetworkObject networkObject, NetworkManager networkManager = null) => throw null;
        public bool Equals(NetworkObjectReference other) => throw null;
        public override bool Equals(object obj) => throw null;
        public override int GetHashCode() => throw null;
        public void NetworkSerialize<T>(BufferSerializer<T> serializer) where T : IReaderWriter { }
        public static implicit operator NetworkObject(NetworkObjectReference networkObjectRef) => throw null;
        public static implicit operator NetworkObjectReference(NetworkObject networkObject) => throw null;
        public static implicit operator GameObject(NetworkObjectReference networkObjectRef) => throw null;
        public static implicit operator NetworkObjectReference(GameObject gameObject) => throw null;
    }

    // ---- RPCs ---------------------------------------------------------------------------
    public enum SendTo { Owner, NotOwner, Server, NotServer, Me, NotMe, Everyone, ClientsAndHost, Authority, NotAuthority, SpecifiedInParams }
    public enum RpcDelivery { Reliable, Unreliable }
    public enum LocalDeferMode { Default, Defer, SendImmediate }
    public abstract class BaseRpcTarget : IDisposable { public virtual void Dispose() { } }   // SIMPLIFIED
    public class RpcTarget { public BaseRpcTarget Everyone, Owner, NotOwner, Server, NotServer, ClientsAndHost, Me, NotMe, Authority, NotAuthority; } // SIMPLIFIED
    [AttributeUsage(AttributeTargets.Method)]
    public class RpcAttribute : Attribute
    {
        public RpcDelivery Delivery = RpcDelivery.Reliable;
        public bool RequireOwnership;
        public bool DeferLocal;
        public bool AllowTargetOverride;
        public RpcAttribute(SendTo target) { }
    }
    [AttributeUsage(AttributeTargets.Method)]
    public class ServerRpcAttribute : RpcAttribute { public new bool RequireOwnership; public ServerRpcAttribute() : base(SendTo.Server) { } }
    [AttributeUsage(AttributeTargets.Method)]
    public class ClientRpcAttribute : RpcAttribute { public ClientRpcAttribute() : base(SendTo.NotServer) { } }
    public struct RpcSendParams
    {
        public BaseRpcTarget Target; public LocalDeferMode LocalDeferMode;
        public static implicit operator RpcSendParams(BaseRpcTarget target) => throw null;
        public static implicit operator RpcSendParams(LocalDeferMode deferMode) => throw null;
    }
    public struct RpcReceiveParams { public ulong SenderClientId; }
    public struct RpcParams
    {
        public RpcSendParams Send; public RpcReceiveParams Receive;
        public static implicit operator RpcParams(RpcSendParams send) => throw null;
        public static implicit operator RpcParams(BaseRpcTarget target) => throw null;
        public static implicit operator RpcParams(LocalDeferMode deferMode) => throw null;
        public static implicit operator RpcParams(RpcReceiveParams receive) => throw null;
    }
    public struct ServerRpcReceiveParams { public ulong SenderClientId; }
    public struct ServerRpcSendParams { }
    public struct ServerRpcParams { public ServerRpcSendParams Send; public ServerRpcReceiveParams Receive; }
    public struct ClientRpcSendParams { public IReadOnlyList<ulong> TargetClientIds; }
    public struct ClientRpcReceiveParams { }
    public struct ClientRpcParams { public ClientRpcSendParams Send; public ClientRpcReceiveParams Receive; }

    // ---- NetworkVariables ---------------------------------------------------------------
    public enum NetworkVariableReadPermission { Everyone, Owner }
    public enum NetworkVariableWritePermission { Server, Owner }
    public abstract class NetworkVariableBase : IDisposable
    {
        public const NetworkVariableReadPermission DefaultReadPerm = NetworkVariableReadPermission.Everyone;
        public const NetworkVariableWritePermission DefaultWritePerm = NetworkVariableWritePermission.Server;
        protected NetworkVariableBase(NetworkVariableReadPermission readPerm = DefaultReadPerm, NetworkVariableWritePermission writePerm = DefaultWritePerm) { }
        public string Name { get => throw null; internal set => throw null; }
        public readonly NetworkVariableReadPermission ReadPerm;
        public NetworkVariableWritePermission WritePerm => throw null;
        public NetworkBehaviour GetBehaviour() => throw null;
        public virtual void SetDirty(bool isDirty) { }
        public virtual void ResetDirty() { }
        public virtual bool IsDirty() => throw null;
        public bool CanClientRead(ulong clientId) => throw null;
        public bool CanClientWrite(ulong clientId) => throw null;
        public abstract void WriteDelta(FastBufferWriter writer);
        public abstract void WriteField(FastBufferWriter writer);
        public abstract void ReadField(FastBufferReader reader);
        public abstract void ReadDelta(FastBufferReader reader, bool keepDirtyDelta);
        public virtual void Dispose() { }
    }
    public class NetworkVariable<T> : NetworkVariableBase
    {
        public delegate void OnValueChangedDelegate(T previousValue, T newValue);
        public OnValueChangedDelegate OnValueChanged;
        public NetworkVariable(T value = default, NetworkVariableReadPermission readPerm = DefaultReadPerm, NetworkVariableWritePermission writePerm = DefaultWritePerm) : base(readPerm, writePerm) { }
        public void Reset(T value = default) { }
        public virtual T Value { get => throw null; set => throw null; }
        public bool CheckDirtyState(bool forceCheck = false) => throw null;
        public override void WriteDelta(FastBufferWriter writer) { }
        public override void WriteField(FastBufferWriter writer) { }
        public override void ReadField(FastBufferReader reader) { }
        public override void ReadDelta(FastBufferReader reader, bool keepDirtyDelta) { }
    }
    public struct NetworkListEvent<T>
    {
        public enum EventType : byte { Add, Insert, Remove, RemoveAt, Value, Clear, Full }
        public EventType Type; public T Value; public T PreviousValue; public int Index;
    }
    public class NetworkList<T> : NetworkVariableBase where T : unmanaged, IEquatable<T>
    {
        public delegate void OnListChangedDelegate(NetworkListEvent<T> changeEvent);
        public event OnListChangedDelegate OnListChanged;
        public NetworkList() { }
        public NetworkList(IEnumerable<T> values = default, NetworkVariableReadPermission readPerm = DefaultReadPerm, NetworkVariableWritePermission writePerm = DefaultWritePerm) : base(readPerm, writePerm) { }
        public IEnumerator<T> GetEnumerator() => throw null;   // NOTE: real NetworkList does NOT implement IEnumerable<T> (no LINQ)
        public void Add(T item) { }
        public void Clear() { }
        public bool Contains(T item) => throw null;
        public bool Remove(T item) => throw null;
        public int Count => throw null;
        public int IndexOf(T item) => throw null;
        public void Insert(int index, T item) { }
        public void RemoveAt(int index) { }
        public T this[int index] { get => throw null; set => throw null; }
        public int LastModifiedTick => throw null;
        public override void WriteDelta(FastBufferWriter writer) { }
        public override void WriteField(FastBufferWriter writer) { }
        public override void ReadField(FastBufferReader reader) { }
        public override void ReadDelta(FastBufferReader reader, bool keepDirtyDelta) { }
    }

    // ---- Core ---------------------------------------------------------------------------
    public struct NetworkTime   // SIMPLIFIED (real fields: Tick, TickOffset, Time, TimeAsFloat, FixedTime, TickRate...)
    {
        public double Time => throw null; public float TimeAsFloat => throw null; public double FixedTime => throw null;
        public int Tick => throw null; public uint TickRate => throw null; public double TickOffset => throw null;
    }
    public class NetworkClient { public bool IsServer => throw null; public bool IsClient => throw null; public bool IsHost => throw null; public ulong ClientId; public NetworkObject PlayerObject; public List<NetworkObject> OwnedObjects => throw null; }
    public class NetworkSpawnManager   // SIMPLIFIED
    {
        public readonly Dictionary<ulong, NetworkObject> SpawnedObjects = new Dictionary<ulong, NetworkObject>();
        public readonly HashSet<NetworkObject> SpawnedObjectsList = new HashSet<NetworkObject>();
        public NetworkObject GetPlayerNetworkObject(ulong clientId) => throw null;
        public NetworkObject GetLocalPlayerObject() => throw null;
    }
    public abstract class NetworkBehaviour : MonoBehaviour
    {
        public NetworkManager NetworkManager => throw null;
        public RpcTarget RpcTarget => throw null;
        public bool IsLocalPlayer { get => throw null; private set => throw null; }
        public bool IsOwner { get => throw null; internal set => throw null; }
        public bool IsServer { get => throw null; private set => throw null; }
        public bool HasAuthority { get => throw null; internal set => throw null; }
        public bool IsSessionOwner => throw null;
        public bool ServerIsHost { get => throw null; private set => throw null; }
        public bool IsClient { get => throw null; private set => throw null; }
        public bool IsHost { get => throw null; private set => throw null; }
        public bool IsOwnedByServer { get => throw null; internal set => throw null; }
        public bool IsSpawned { get => throw null; internal set => throw null; }
        public NetworkObject NetworkObject => throw null;
        public bool HasNetworkObject => throw null;
        public ulong NetworkObjectId { get => throw null; internal set => throw null; }
        public ushort NetworkBehaviourId { get => throw null; internal set => throw null; }
        public ulong OwnerClientId { get => throw null; internal set => throw null; }
        protected NetworkBehaviour GetNetworkBehaviour(ushort behaviourId) => throw null;
        protected NetworkObject GetNetworkObject(ulong networkId) => throw null;
        public virtual void OnDeferringDespawn(int despawnTick) { }
        protected virtual void OnNetworkPreSpawn(ref NetworkManager networkManager) { }
        public virtual void OnNetworkSpawn() { }
        protected virtual void OnNetworkPostSpawn() { }
        protected virtual void OnNetworkSessionSynchronized() { }
        protected virtual void OnInSceneObjectsSpawned() { }
        public virtual void OnNetworkDespawn() { }
        public virtual void OnGainedOwnership() { }
        protected virtual void OnOwnershipChanged(ulong previous, ulong current) { }
        public virtual void OnLostOwnership() { }
        public virtual void OnNetworkObjectParentChanged(NetworkObject parentNetworkObject) { }
        protected virtual void OnSynchronize<T>(ref BufferSerializer<T> serializer) where T : IReaderWriter { }
        public virtual void OnReanticipate(double lastRoundTripTime) { }
        public virtual void OnDestroy() { }
    }
    public sealed class NetworkObject : MonoBehaviour
    {
        public uint PrefabIdHash => throw null;
        public List<Unity.Netcode.Components.NetworkTransform> NetworkTransforms { get => throw null; private set => throw null; }
        public NetworkObject CurrentParent { get => throw null; private set => throw null; }
        public NetworkManager NetworkManager => throw null;
        public void DeferDespawn(int tickOffset, bool destroy = true) { }
        public bool HasAuthority => throw null;
        public ulong NetworkObjectId { get => throw null; internal set => throw null; }
        public ulong OwnerClientId { get => throw null; internal set => throw null; }
        public bool IsPlayerObject { get => throw null; internal set => throw null; }
        public bool AlwaysReplicateAsRoot;
        public bool SynchronizeTransform = true;
        public bool IsLocalPlayer => throw null;
        public bool IsOwner => throw null;
        public bool IsOwnedByServer => throw null;
        public bool IsSpawned { get => throw null; internal set => throw null; }
        public bool? IsSceneObject { get => throw null; internal set => throw null; }
        public void SetSceneObjectStatus(bool isSceneObject = false) { }
        public bool DestroyWithScene { get; set; }
        public bool ActiveSceneSynchronization;
        public bool SceneMigrationSynchronization = true;
        public bool SpawnWithObservers = true;
        public delegate bool VisibilityDelegate(ulong clientId);
        public VisibilityDelegate CheckObjectVisibility = null;
        public bool DontDestroyWithOwner;
        public bool AutoObjectParentSync = true;
        public HashSet<ulong>.Enumerator GetObservers() => throw null;
        public bool IsNetworkVisibleTo(ulong clientId) => throw null;
        public void NetworkShow(ulong clientId) { }
        public static void NetworkShow(List<NetworkObject> networkObjects, ulong clientId) { }
        public void NetworkHide(ulong clientId) { }
        public static void NetworkHide(List<NetworkObject> networkObjects, ulong clientId) { }
        public static NetworkObject InstantiateAndSpawn(GameObject networkPrefab, NetworkManager networkManager, ulong ownerClientId = NetworkManager.ServerClientId, bool destroyWithScene = false, bool isPlayerObject = false, bool forceOverride = false, Vector3 position = default, Quaternion rotation = default) => throw null;
        public NetworkObject InstantiateAndSpawn(NetworkManager networkManager, ulong ownerClientId = NetworkManager.ServerClientId, bool destroyWithScene = false, bool isPlayerObject = false, bool forceOverride = false, Vector3 position = default, Quaternion rotation = default) => throw null;
        public void Spawn(bool destroyWithScene = false) { }
        public void SpawnWithOwnership(ulong clientId, bool destroyWithScene = false) { }
        public void SpawnAsPlayerObject(ulong clientId, bool destroyWithScene = false) { }
        public void Despawn(bool destroy = true) { }
        public void RemoveOwnership() { }
        public void ChangeOwnership(ulong newOwnerClientId) { }
        public bool TrySetParent(Transform parent, bool worldPositionStays = true) => throw null;
        public bool TrySetParent(GameObject parent, bool worldPositionStays = true) => throw null;
        public bool TrySetParent(NetworkObject parent, bool worldPositionStays = true) => throw null;
        public bool TryRemoveParent(bool worldPositionStays = true) => throw null;
    }
    public class NetworkManager : MonoBehaviour
    {
        public static event Action<NetworkManager> OnInstantiated;
        public static event Action<NetworkManager> OnDestroying;
        public const ulong ServerClientId = 0;
        public ulong LocalClientId { get => throw null; internal set => throw null; }
        public IReadOnlyDictionary<ulong, NetworkClient> ConnectedClients => throw null;
        public IReadOnlyList<NetworkClient> ConnectedClientsList => throw null;
        public IReadOnlyList<ulong> ConnectedClientsIds => throw null;
        public NetworkClient LocalClient => throw null;
        public bool IsServer => throw null;
        public bool ServerIsHost => throw null;
        public bool IsClient => throw null;
        public bool IsHost => throw null;
        public string DisconnectReason => throw null;
        public bool IsListening => throw null;
        public bool IsConnectedClient => throw null;
        public bool IsApproved => throw null;
        public event Action OnTransportFailure { add { } remove { } }
        public Action<ConnectionApprovalRequest, ConnectionApprovalResponse> ConnectionApprovalCallback { get => throw null; set => throw null; }
        public event Action<ulong> OnClientConnectedCallback { add { } remove { } }
        public event Action<ulong> OnClientDisconnectCallback { add { } remove { } }
        public class ConnectionApprovalResponse { public bool Approved; public bool CreatePlayerObject; public uint? PlayerPrefabHash; public Vector3? Position; public Quaternion? Rotation; public bool Pending; public string Reason; }
        public struct ConnectionApprovalRequest { public byte[] Payload; public ulong ClientNetworkId; }
        public bool ShutdownInProgress => throw null;
        public NetworkConfig NetworkConfig;
        public NetworkTime LocalTime => throw null;
        public NetworkTime ServerTime => throw null;
        public bool RunInBackground = true;
        public static NetworkManager Singleton { get => throw null; private set => throw null; }
        public event Action OnServerStarted = null;
        public event Action OnClientStarted = null;
        public event Action<bool> OnServerStopped = null;
        public event Action<bool> OnClientStopped = null;
        public NetworkSpawnManager SpawnManager { get => throw null; private set => throw null; }
        public RpcTarget RpcTarget;
        public void SetSingleton() { }
        public void AddNetworkPrefab(GameObject prefab) { }
        public void RemoveNetworkPrefab(GameObject prefab) { }
        public bool StartServer() => throw null;
        public bool StartClient() => throw null;
        public bool StartHost() => throw null;
        public void DisconnectClient(ulong clientId) { }
        public void DisconnectClient(ulong clientId, string reason = null) { }
        public void Shutdown(bool discardMessageQueue = false) { }
    }

    // ---- Configuration ------------------------------------------------------------------
    public enum NetworkPrefabOverride { None, Prefab, Hash }
    public class NetworkPrefab
    {
        public NetworkPrefabOverride Override; public GameObject Prefab; public GameObject SourcePrefabToOverride;
        public uint SourceHashToOverride; public GameObject OverridingTargetPrefab;
        public bool Equals(NetworkPrefab other) => throw null;
        public bool Validate(int index = -1) => throw null;
    }
    public class NetworkPrefabsList : ScriptableObject
    {
        public IReadOnlyList<NetworkPrefab> PrefabList => throw null;
        public void Add(NetworkPrefab prefab) { }
        public void Remove(NetworkPrefab prefab) { }
        public bool Contains(GameObject prefab) => throw null;
        public bool Contains(NetworkPrefab prefab) => throw null;
    }
    public class NetworkPrefabs
    {
        public List<NetworkPrefabsList> NetworkPrefabsLists = new List<NetworkPrefabsList>();
        public IReadOnlyList<NetworkPrefab> Prefabs => throw null;
        public bool Add(NetworkPrefab networkPrefab) => throw null;
        public void Remove(NetworkPrefab prefab) { }
        public void Remove(GameObject prefab) { }
        public bool Contains(GameObject prefab) => throw null;
    }
    public class NetworkConfig   // SIMPLIFIED to the commonly used fields (all REAL names/types)
    {
        public NetworkTransport NetworkTransport = null;
        public GameObject PlayerPrefab;
        public NetworkPrefabs Prefabs = new NetworkPrefabs();
        public uint TickRate = 30;
        public int ClientConnectionBufferTimeout = 10;
        public bool ConnectionApproval = false;
        public byte[] ConnectionData = new byte[0];
        public bool EnableTimeResync = false;
        public bool EnsureNetworkVariableLengthSafety = false;
        public bool EnableSceneManagement = true;
        public bool ForceSamePrefabs = true;
        public bool RecycleNetworkIds = true;
        public float NetworkIdRecycleDelay = 120f;
        public int LoadSceneTimeOut = 120;
        public bool AutoSpawnPlayerPrefabClientSide = true;
    }
    public abstract class NetworkTransport : MonoBehaviour { }   // SIMPLIFIED (abstract members omitted)
}

namespace Unity.Netcode.Components
{
    public class NetworkTransform : NetworkBehaviour
    {
        public enum AuthorityModes { Server, Owner }
        public AuthorityModes AuthorityMode;
        public bool TickSyncChildren = false;
        public bool UseUnreliableDeltas = false;
        public bool SyncPositionX = true, SyncPositionY = true, SyncPositionZ = true;
        public bool SyncRotAngleX = true, SyncRotAngleY = true, SyncRotAngleZ = true;
        public bool SyncScaleX = true, SyncScaleY = true, SyncScaleZ = true;
        public float PositionThreshold, RotAngleThreshold, ScaleThreshold;
        public bool UseQuaternionSynchronization, UseQuaternionCompression, UseHalfFloatPrecision, InLocalSpace, SwitchTransformSpaceWhenParented;
        public bool Interpolate = true;
        public bool SlerpPosition = false;
        public bool CanCommitToTransform { get => throw null; protected set => throw null; }   // REAL name; accessor shape GUESSED
        public bool IsServerAuthoritative() => throw null;
        public void Teleport(Vector3 newPosition, Quaternion newRotation, Vector3 newScale) { }
        public void SetState(Vector3? posIn = null, Quaternion? rotIn = null, Vector3? scaleIn = null, bool teleportDisabled = true) { }
        protected virtual void OnTransformUpdated() { }
        protected virtual void OnBeforeUpdateTransformState() { }
        protected virtual void Awake() { }
        public override void OnNetworkSpawn() { }
        public override void OnNetworkDespawn() { }
        public override void OnDestroy() { }
        public override void OnLostOwnership() { }
        public override void OnGainedOwnership() { }
        protected override void OnOwnershipChanged(ulong previous, ulong current) { }
        public virtual void OnUpdate() { }
        public virtual void OnFixedUpdate() { }
        protected virtual bool OnIsServerAuthoritative() => throw null;
    }
    public abstract class NetworkRigidbodyBase : NetworkBehaviour { public bool UseRigidBodyForMotion; public bool AutoUpdateKinematicState = true; public bool AutoSetKinematicOnDespawn = true; }
    public class NetworkRigidbody : NetworkRigidbodyBase { }
}

namespace Unity.Netcode.Transports.UTP
{
    // UnityTransport ships inside the NGO package (Runtime/Transports/UTP/UnityTransport.cs)
    public partial class UnityTransport : NetworkTransport
    {
        [Serializable]
        public struct ConnectionAddressData { public string Address; public ushort Port; public string ServerListenAddress; }
        public ConnectionAddressData ConnectionData;
        public void SetRelayServerData(string ipv4Address, ushort port, byte[] allocationIdBytes, byte[] keyBytes, byte[] connectionDataBytes, byte[] hostConnectionDataBytes = null, bool isSecure = false) { }
        public void SetClientRelayData(string ipAddress, ushort port, byte[] allocationId, byte[] key, byte[] connectionData, byte[] hostConnectionData, bool isSecure = false) { }
        public void SetConnectionData(string ipv4Address, ushort port, string listenAddress = null) { }
    }
}
