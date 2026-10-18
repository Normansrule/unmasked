#pragma warning disable CS0067, CS0108, CS0114 // stub file: unused events / hiding are irrelevant
// AUTO-GENERATED stub of Unity.Collections FixedStringNBytes (com.unity.collections 2.2.1, Unity.Collections/FixedString.gen.cs
// via needle-mirror). Public members/operators/conversions mirror the real file; Rune/FixedList/unsafe-pointer members omitted.
// INativeList<T>/IUTF8Bytes/IIndexable<T> are reduced to marker interfaces (only used as generic constraints by NGO).
using System;
using System.Collections;
namespace Unity.Collections {
  public interface IIndexable<T> where T : unmanaged { }
  public interface INativeList<T> : IIndexable<T> where T : unmanaged { }
  public interface IUTF8Bytes { }
  [Serializable] [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential, Size=32)]
  public partial struct FixedString32Bytes : INativeList<byte>, IUTF8Bytes, IComparable<String>, IEquatable<String>, IComparable<FixedString32Bytes>, IEquatable<FixedString32Bytes>, IComparable<FixedString64Bytes>, IEquatable<FixedString64Bytes>, IComparable<FixedString128Bytes>, IEquatable<FixedString128Bytes>, IComparable<FixedString512Bytes>, IEquatable<FixedString512Bytes>, IComparable<FixedString4096Bytes>, IEquatable<FixedString4096Bytes> {
    ushort utf8LengthInBytes; byte _pad; // keeps it an unmanaged struct
    public static int UTF8MaxLengthInBytes => throw null;
    public string Value => throw null;
    public int Length { get => throw null; set => throw null; }
    public int Capacity { get => throw null; set => throw null; }
    public bool TryResize(int newLength, NativeArrayOptions clearOptions = NativeArrayOptions.ClearMemory) => throw null;
    public readonly bool IsEmpty => throw null;
    public byte this[int index] { get => throw null; set => throw null; }
    public ref byte ElementAt(int index) => throw null;
    public void Clear() => throw null;
    public void Add(in byte value) => throw null;
    public int CompareTo(String other) => throw null;
    public bool Equals(String other) => throw null;
    public FixedString32Bytes(String source) => throw null;
    public int CompareTo(FixedString32Bytes other) => throw null;
    public FixedString32Bytes(in FixedString32Bytes other) => throw null;
    public static bool operator ==(in FixedString32Bytes a, in FixedString32Bytes b) => throw null;
    public static bool operator !=(in FixedString32Bytes a, in FixedString32Bytes b) => throw null;
    public bool Equals(FixedString32Bytes other) => throw null;
    public int CompareTo(FixedString64Bytes other) => throw null;
    public FixedString32Bytes(in FixedString64Bytes other) => throw null;
    public static bool operator ==(in FixedString32Bytes a, in FixedString64Bytes b) => throw null;
    public static bool operator !=(in FixedString32Bytes a, in FixedString64Bytes b) => throw null;
    public bool Equals(FixedString64Bytes other) => throw null;
    public static implicit operator FixedString64Bytes(in FixedString32Bytes fs) => throw null;
    public int CompareTo(FixedString128Bytes other) => throw null;
    public FixedString32Bytes(in FixedString128Bytes other) => throw null;
    public static bool operator ==(in FixedString32Bytes a, in FixedString128Bytes b) => throw null;
    public static bool operator !=(in FixedString32Bytes a, in FixedString128Bytes b) => throw null;
    public bool Equals(FixedString128Bytes other) => throw null;
    public static implicit operator FixedString128Bytes(in FixedString32Bytes fs) => throw null;
    public int CompareTo(FixedString512Bytes other) => throw null;
    public FixedString32Bytes(in FixedString512Bytes other) => throw null;
    public static bool operator ==(in FixedString32Bytes a, in FixedString512Bytes b) => throw null;
    public static bool operator !=(in FixedString32Bytes a, in FixedString512Bytes b) => throw null;
    public bool Equals(FixedString512Bytes other) => throw null;
    public static implicit operator FixedString512Bytes(in FixedString32Bytes fs) => throw null;
    public int CompareTo(FixedString4096Bytes other) => throw null;
    public FixedString32Bytes(in FixedString4096Bytes other) => throw null;
    public static bool operator ==(in FixedString32Bytes a, in FixedString4096Bytes b) => throw null;
    public static bool operator !=(in FixedString32Bytes a, in FixedString4096Bytes b) => throw null;
    public bool Equals(FixedString4096Bytes other) => throw null;
    public static implicit operator FixedString4096Bytes(in FixedString32Bytes fs) => throw null;
    public static implicit operator FixedString32Bytes(string b) => throw null;
    public override String ToString() => throw null;
    public override int GetHashCode() => throw null;
    public override bool Equals(object obj) => throw null;
  }
  [Serializable] [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential, Size=64)]
  public partial struct FixedString64Bytes : INativeList<byte>, IUTF8Bytes, IComparable<String>, IEquatable<String>, IComparable<FixedString32Bytes>, IEquatable<FixedString32Bytes>, IComparable<FixedString64Bytes>, IEquatable<FixedString64Bytes>, IComparable<FixedString128Bytes>, IEquatable<FixedString128Bytes>, IComparable<FixedString512Bytes>, IEquatable<FixedString512Bytes>, IComparable<FixedString4096Bytes>, IEquatable<FixedString4096Bytes> {
    ushort utf8LengthInBytes; byte _pad; // keeps it an unmanaged struct
    public static int UTF8MaxLengthInBytes => throw null;
    public string Value => throw null;
    public int Length { get => throw null; set => throw null; }
    public int Capacity { get => throw null; set => throw null; }
    public bool TryResize(int newLength, NativeArrayOptions clearOptions = NativeArrayOptions.ClearMemory) => throw null;
    public readonly bool IsEmpty => throw null;
    public byte this[int index] { get => throw null; set => throw null; }
    public ref byte ElementAt(int index) => throw null;
    public void Clear() => throw null;
    public void Add(in byte value) => throw null;
    public int CompareTo(String other) => throw null;
    public bool Equals(String other) => throw null;
    public FixedString64Bytes(String source) => throw null;
    public int CompareTo(FixedString32Bytes other) => throw null;
    public FixedString64Bytes(in FixedString32Bytes other) => throw null;
    public static bool operator ==(in FixedString64Bytes a, in FixedString32Bytes b) => throw null;
    public static bool operator !=(in FixedString64Bytes a, in FixedString32Bytes b) => throw null;
    public bool Equals(FixedString32Bytes other) => throw null;
    public int CompareTo(FixedString64Bytes other) => throw null;
    public FixedString64Bytes(in FixedString64Bytes other) => throw null;
    public static bool operator ==(in FixedString64Bytes a, in FixedString64Bytes b) => throw null;
    public static bool operator !=(in FixedString64Bytes a, in FixedString64Bytes b) => throw null;
    public bool Equals(FixedString64Bytes other) => throw null;
    public int CompareTo(FixedString128Bytes other) => throw null;
    public FixedString64Bytes(in FixedString128Bytes other) => throw null;
    public static bool operator ==(in FixedString64Bytes a, in FixedString128Bytes b) => throw null;
    public static bool operator !=(in FixedString64Bytes a, in FixedString128Bytes b) => throw null;
    public bool Equals(FixedString128Bytes other) => throw null;
    public static implicit operator FixedString128Bytes(in FixedString64Bytes fs) => throw null;
    public int CompareTo(FixedString512Bytes other) => throw null;
    public FixedString64Bytes(in FixedString512Bytes other) => throw null;
    public static bool operator ==(in FixedString64Bytes a, in FixedString512Bytes b) => throw null;
    public static bool operator !=(in FixedString64Bytes a, in FixedString512Bytes b) => throw null;
    public bool Equals(FixedString512Bytes other) => throw null;
    public static implicit operator FixedString512Bytes(in FixedString64Bytes fs) => throw null;
    public int CompareTo(FixedString4096Bytes other) => throw null;
    public FixedString64Bytes(in FixedString4096Bytes other) => throw null;
    public static bool operator ==(in FixedString64Bytes a, in FixedString4096Bytes b) => throw null;
    public static bool operator !=(in FixedString64Bytes a, in FixedString4096Bytes b) => throw null;
    public bool Equals(FixedString4096Bytes other) => throw null;
    public static implicit operator FixedString4096Bytes(in FixedString64Bytes fs) => throw null;
    public static implicit operator FixedString64Bytes(string b) => throw null;
    public override String ToString() => throw null;
    public override int GetHashCode() => throw null;
    public override bool Equals(object obj) => throw null;
  }
  [Serializable] [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential, Size=128)]
  public partial struct FixedString128Bytes : INativeList<byte>, IUTF8Bytes, IComparable<String>, IEquatable<String>, IComparable<FixedString32Bytes>, IEquatable<FixedString32Bytes>, IComparable<FixedString64Bytes>, IEquatable<FixedString64Bytes>, IComparable<FixedString128Bytes>, IEquatable<FixedString128Bytes>, IComparable<FixedString512Bytes>, IEquatable<FixedString512Bytes>, IComparable<FixedString4096Bytes>, IEquatable<FixedString4096Bytes> {
    ushort utf8LengthInBytes; byte _pad; // keeps it an unmanaged struct
    public static int UTF8MaxLengthInBytes => throw null;
    public string Value => throw null;
    public int Length { get => throw null; set => throw null; }
    public int Capacity { get => throw null; set => throw null; }
    public bool TryResize(int newLength, NativeArrayOptions clearOptions = NativeArrayOptions.ClearMemory) => throw null;
    public readonly bool IsEmpty => throw null;
    public byte this[int index] { get => throw null; set => throw null; }
    public ref byte ElementAt(int index) => throw null;
    public void Clear() => throw null;
    public void Add(in byte value) => throw null;
    public int CompareTo(String other) => throw null;
    public bool Equals(String other) => throw null;
    public FixedString128Bytes(String source) => throw null;
    public int CompareTo(FixedString32Bytes other) => throw null;
    public FixedString128Bytes(in FixedString32Bytes other) => throw null;
    public static bool operator ==(in FixedString128Bytes a, in FixedString32Bytes b) => throw null;
    public static bool operator !=(in FixedString128Bytes a, in FixedString32Bytes b) => throw null;
    public bool Equals(FixedString32Bytes other) => throw null;
    public int CompareTo(FixedString64Bytes other) => throw null;
    public FixedString128Bytes(in FixedString64Bytes other) => throw null;
    public static bool operator ==(in FixedString128Bytes a, in FixedString64Bytes b) => throw null;
    public static bool operator !=(in FixedString128Bytes a, in FixedString64Bytes b) => throw null;
    public bool Equals(FixedString64Bytes other) => throw null;
    public int CompareTo(FixedString128Bytes other) => throw null;
    public FixedString128Bytes(in FixedString128Bytes other) => throw null;
    public static bool operator ==(in FixedString128Bytes a, in FixedString128Bytes b) => throw null;
    public static bool operator !=(in FixedString128Bytes a, in FixedString128Bytes b) => throw null;
    public bool Equals(FixedString128Bytes other) => throw null;
    public int CompareTo(FixedString512Bytes other) => throw null;
    public FixedString128Bytes(in FixedString512Bytes other) => throw null;
    public static bool operator ==(in FixedString128Bytes a, in FixedString512Bytes b) => throw null;
    public static bool operator !=(in FixedString128Bytes a, in FixedString512Bytes b) => throw null;
    public bool Equals(FixedString512Bytes other) => throw null;
    public static implicit operator FixedString512Bytes(in FixedString128Bytes fs) => throw null;
    public int CompareTo(FixedString4096Bytes other) => throw null;
    public FixedString128Bytes(in FixedString4096Bytes other) => throw null;
    public static bool operator ==(in FixedString128Bytes a, in FixedString4096Bytes b) => throw null;
    public static bool operator !=(in FixedString128Bytes a, in FixedString4096Bytes b) => throw null;
    public bool Equals(FixedString4096Bytes other) => throw null;
    public static implicit operator FixedString4096Bytes(in FixedString128Bytes fs) => throw null;
    public static implicit operator FixedString128Bytes(string b) => throw null;
    public override String ToString() => throw null;
    public override int GetHashCode() => throw null;
    public override bool Equals(object obj) => throw null;
  }
  [Serializable] [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential, Size=512)]
  public partial struct FixedString512Bytes : INativeList<byte>, IUTF8Bytes, IComparable<String>, IEquatable<String>, IComparable<FixedString32Bytes>, IEquatable<FixedString32Bytes>, IComparable<FixedString64Bytes>, IEquatable<FixedString64Bytes>, IComparable<FixedString128Bytes>, IEquatable<FixedString128Bytes>, IComparable<FixedString512Bytes>, IEquatable<FixedString512Bytes>, IComparable<FixedString4096Bytes>, IEquatable<FixedString4096Bytes> {
    ushort utf8LengthInBytes; byte _pad; // keeps it an unmanaged struct
    public static int UTF8MaxLengthInBytes => throw null;
    public string Value => throw null;
    public int Length { get => throw null; set => throw null; }
    public int Capacity { get => throw null; set => throw null; }
    public bool TryResize(int newLength, NativeArrayOptions clearOptions = NativeArrayOptions.ClearMemory) => throw null;
    public readonly bool IsEmpty => throw null;
    public byte this[int index] { get => throw null; set => throw null; }
    public ref byte ElementAt(int index) => throw null;
    public void Clear() => throw null;
    public void Add(in byte value) => throw null;
    public int CompareTo(String other) => throw null;
    public bool Equals(String other) => throw null;
    public FixedString512Bytes(String source) => throw null;
    public int CompareTo(FixedString32Bytes other) => throw null;
    public FixedString512Bytes(in FixedString32Bytes other) => throw null;
    public static bool operator ==(in FixedString512Bytes a, in FixedString32Bytes b) => throw null;
    public static bool operator !=(in FixedString512Bytes a, in FixedString32Bytes b) => throw null;
    public bool Equals(FixedString32Bytes other) => throw null;
    public int CompareTo(FixedString64Bytes other) => throw null;
    public FixedString512Bytes(in FixedString64Bytes other) => throw null;
    public static bool operator ==(in FixedString512Bytes a, in FixedString64Bytes b) => throw null;
    public static bool operator !=(in FixedString512Bytes a, in FixedString64Bytes b) => throw null;
    public bool Equals(FixedString64Bytes other) => throw null;
    public int CompareTo(FixedString128Bytes other) => throw null;
    public FixedString512Bytes(in FixedString128Bytes other) => throw null;
    public static bool operator ==(in FixedString512Bytes a, in FixedString128Bytes b) => throw null;
    public static bool operator !=(in FixedString512Bytes a, in FixedString128Bytes b) => throw null;
    public bool Equals(FixedString128Bytes other) => throw null;
    public int CompareTo(FixedString512Bytes other) => throw null;
    public FixedString512Bytes(in FixedString512Bytes other) => throw null;
    public static bool operator ==(in FixedString512Bytes a, in FixedString512Bytes b) => throw null;
    public static bool operator !=(in FixedString512Bytes a, in FixedString512Bytes b) => throw null;
    public bool Equals(FixedString512Bytes other) => throw null;
    public int CompareTo(FixedString4096Bytes other) => throw null;
    public FixedString512Bytes(in FixedString4096Bytes other) => throw null;
    public static bool operator ==(in FixedString512Bytes a, in FixedString4096Bytes b) => throw null;
    public static bool operator !=(in FixedString512Bytes a, in FixedString4096Bytes b) => throw null;
    public bool Equals(FixedString4096Bytes other) => throw null;
    public static implicit operator FixedString4096Bytes(in FixedString512Bytes fs) => throw null;
    public static implicit operator FixedString512Bytes(string b) => throw null;
    public override String ToString() => throw null;
    public override int GetHashCode() => throw null;
    public override bool Equals(object obj) => throw null;
  }
  [Serializable] [System.Runtime.InteropServices.StructLayout(System.Runtime.InteropServices.LayoutKind.Sequential, Size=4096)]
  public partial struct FixedString4096Bytes : INativeList<byte>, IUTF8Bytes, IComparable<String>, IEquatable<String>, IComparable<FixedString32Bytes>, IEquatable<FixedString32Bytes>, IComparable<FixedString64Bytes>, IEquatable<FixedString64Bytes>, IComparable<FixedString128Bytes>, IEquatable<FixedString128Bytes>, IComparable<FixedString512Bytes>, IEquatable<FixedString512Bytes>, IComparable<FixedString4096Bytes>, IEquatable<FixedString4096Bytes> {
    ushort utf8LengthInBytes; byte _pad; // keeps it an unmanaged struct
    public static int UTF8MaxLengthInBytes => throw null;
    public string Value => throw null;
    public int Length { get => throw null; set => throw null; }
    public int Capacity { get => throw null; set => throw null; }
    public bool TryResize(int newLength, NativeArrayOptions clearOptions = NativeArrayOptions.ClearMemory) => throw null;
    public readonly bool IsEmpty => throw null;
    public byte this[int index] { get => throw null; set => throw null; }
    public ref byte ElementAt(int index) => throw null;
    public void Clear() => throw null;
    public void Add(in byte value) => throw null;
    public int CompareTo(String other) => throw null;
    public bool Equals(String other) => throw null;
    public FixedString4096Bytes(String source) => throw null;
    public int CompareTo(FixedString32Bytes other) => throw null;
    public FixedString4096Bytes(in FixedString32Bytes other) => throw null;
    public static bool operator ==(in FixedString4096Bytes a, in FixedString32Bytes b) => throw null;
    public static bool operator !=(in FixedString4096Bytes a, in FixedString32Bytes b) => throw null;
    public bool Equals(FixedString32Bytes other) => throw null;
    public int CompareTo(FixedString64Bytes other) => throw null;
    public FixedString4096Bytes(in FixedString64Bytes other) => throw null;
    public static bool operator ==(in FixedString4096Bytes a, in FixedString64Bytes b) => throw null;
    public static bool operator !=(in FixedString4096Bytes a, in FixedString64Bytes b) => throw null;
    public bool Equals(FixedString64Bytes other) => throw null;
    public int CompareTo(FixedString128Bytes other) => throw null;
    public FixedString4096Bytes(in FixedString128Bytes other) => throw null;
    public static bool operator ==(in FixedString4096Bytes a, in FixedString128Bytes b) => throw null;
    public static bool operator !=(in FixedString4096Bytes a, in FixedString128Bytes b) => throw null;
    public bool Equals(FixedString128Bytes other) => throw null;
    public int CompareTo(FixedString512Bytes other) => throw null;
    public FixedString4096Bytes(in FixedString512Bytes other) => throw null;
    public static bool operator ==(in FixedString4096Bytes a, in FixedString512Bytes b) => throw null;
    public static bool operator !=(in FixedString4096Bytes a, in FixedString512Bytes b) => throw null;
    public bool Equals(FixedString512Bytes other) => throw null;
    public int CompareTo(FixedString4096Bytes other) => throw null;
    public FixedString4096Bytes(in FixedString4096Bytes other) => throw null;
    public static bool operator ==(in FixedString4096Bytes a, in FixedString4096Bytes b) => throw null;
    public static bool operator !=(in FixedString4096Bytes a, in FixedString4096Bytes b) => throw null;
    public bool Equals(FixedString4096Bytes other) => throw null;
    public static implicit operator FixedString4096Bytes(string b) => throw null;
    public override String ToString() => throw null;
    public override int GetHashCode() => throw null;
    public override bool Equals(object obj) => throw null;
  }
}
