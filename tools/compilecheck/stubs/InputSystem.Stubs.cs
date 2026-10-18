#pragma warning disable CS0067, CS0108, CS0114 // stub file: unused events / hiding are irrelevant
// AUTO-GENERATED from Unity-Technologies/InputSystem tag 1.11.2 (Devices/Keyboard.cs, Mouse.cs, Pointer.cs,
// Controls/ButtonControl.cs, Vector2Control.cs, InputControl.cs). Member names/types are REAL; bodies are stubs.
// Class hierarchy is simplified (AxisControl/DeltaControl/IntegerControl kept, internals dropped).
using UnityEngine;
namespace UnityEngine.InputSystem.Controls {
  public class AxisControl : UnityEngine.InputSystem.InputControl<float> { }
  public class ButtonControl : AxisControl { public float pressPoint; public bool isPressed => throw null; public bool wasPressedThisFrame => throw null; public bool wasReleasedThisFrame => throw null; }
  public class KeyControl : ButtonControl { public UnityEngine.InputSystem.Key keyCode => throw null; public int scanCode => throw null; }
  public class AnyKeyControl : ButtonControl { }
  public class IntegerControl : InputControl<int> { }
  public class Vector2Control : InputControl<Vector2> { public AxisControl x { get => throw null; set => throw null; } public AxisControl y { get => throw null; set => throw null; } }
  public class DeltaControl : Vector2Control { public ButtonControl up => throw null; public ButtonControl down => throw null; public ButtonControl left => throw null; public ButtonControl right => throw null; }
}
namespace UnityEngine.InputSystem {
  using UnityEngine.InputSystem.Controls;
  public abstract class InputControl<TValue> : InputControl where TValue : struct { public TValue ReadValue() => throw null; public TValue ReadValueFromPreviousFrame() => throw null; }
  public abstract class InputControl { public string name => throw null; public string path => throw null; public InputDevice device => throw null; }
  public class InputDevice : InputControl { public bool enabled => throw null; public bool added => throw null; public int deviceId => throw null; }
  public enum Key {
    None,
    Space,
    Enter,
    Tab,
    Backquote,
    Quote,
    Semicolon,
    Comma,
    Period,
    Slash,
    Backslash,
    LeftBracket,
    RightBracket,
    Minus,
    Equals,
    A,
    B,
    C,
    D,
    E,
    F,
    G,
    H,
    I,
    J,
    K,
    L,
    M,
    N,
    O,
    P,
    Q,
    R,
    S,
    T,
    U,
    V,
    W,
    X,
    Y,
    Z,
    Digit1,
    Digit2,
    Digit3,
    Digit4,
    Digit5,
    Digit6,
    Digit7,
    Digit8,
    Digit9,
    Digit0,
    LeftShift,
    RightShift,
    LeftAlt,
    RightAlt,
    AltGr = RightAlt,
    LeftCtrl,
    RightCtrl,
    LeftMeta,
    RightMeta,
    LeftWindows = LeftMeta,
    RightWindows = RightMeta,
    LeftApple = LeftMeta,
    RightApple = RightMeta,
    LeftCommand = LeftMeta,
    RightCommand = RightMeta,
    ContextMenu,
    Escape,
    LeftArrow,
    RightArrow,
    UpArrow,
    DownArrow,
    Backspace,
    PageDown,
    PageUp,
    Home,
    End,
    Insert,
    Delete,
    CapsLock,
    NumLock,
    PrintScreen,
    ScrollLock,
    Pause,
    NumpadEnter,
    NumpadDivide,
    NumpadMultiply,
    NumpadPlus,
    NumpadMinus,
    NumpadPeriod,
    NumpadEquals,
    Numpad0,
    Numpad1,
    Numpad2,
    Numpad3,
    Numpad4,
    Numpad5,
    Numpad6,
    Numpad7,
    Numpad8,
    Numpad9,
    F1,
    F2,
    F3,
    F4,
    F5,
    F6,
    F7,
    F8,
    F9,
    F10,
    F11,
    F12,
    OEM1,
    OEM2,
    OEM3,
    OEM4,
    OEM5,
    IMESelected,
  }
  public class Keyboard : InputDevice {
    public static Keyboard current { get => throw null; private set => throw null; }
    public AnyKeyControl anyKey { get => throw null; protected set => throw null; }
    public ButtonControl shiftKey { get => throw null; protected set => throw null; }
    public ButtonControl ctrlKey { get => throw null; protected set => throw null; }
    public ButtonControl altKey { get => throw null; protected set => throw null; }
    public KeyControl this[Key key] => throw null;
    public KeyControl spaceKey => throw null;
    public KeyControl enterKey => throw null;
    public KeyControl tabKey => throw null;
    public KeyControl backquoteKey => throw null;
    public KeyControl quoteKey => throw null;
    public KeyControl semicolonKey => throw null;
    public KeyControl commaKey => throw null;
    public KeyControl periodKey => throw null;
    public KeyControl slashKey => throw null;
    public KeyControl backslashKey => throw null;
    public KeyControl leftBracketKey => throw null;
    public KeyControl rightBracketKey => throw null;
    public KeyControl minusKey => throw null;
    public KeyControl equalsKey => throw null;
    public KeyControl aKey => throw null;
    public KeyControl bKey => throw null;
    public KeyControl cKey => throw null;
    public KeyControl dKey => throw null;
    public KeyControl eKey => throw null;
    public KeyControl fKey => throw null;
    public KeyControl gKey => throw null;
    public KeyControl hKey => throw null;
    public KeyControl iKey => throw null;
    public KeyControl jKey => throw null;
    public KeyControl kKey => throw null;
    public KeyControl lKey => throw null;
    public KeyControl mKey => throw null;
    public KeyControl nKey => throw null;
    public KeyControl oKey => throw null;
    public KeyControl pKey => throw null;
    public KeyControl qKey => throw null;
    public KeyControl rKey => throw null;
    public KeyControl sKey => throw null;
    public KeyControl tKey => throw null;
    public KeyControl uKey => throw null;
    public KeyControl vKey => throw null;
    public KeyControl wKey => throw null;
    public KeyControl xKey => throw null;
    public KeyControl yKey => throw null;
    public KeyControl zKey => throw null;
    public KeyControl digit1Key => throw null;
    public KeyControl digit2Key => throw null;
    public KeyControl digit3Key => throw null;
    public KeyControl digit4Key => throw null;
    public KeyControl digit5Key => throw null;
    public KeyControl digit6Key => throw null;
    public KeyControl digit7Key => throw null;
    public KeyControl digit8Key => throw null;
    public KeyControl digit9Key => throw null;
    public KeyControl digit0Key => throw null;
    public KeyControl leftShiftKey => throw null;
    public KeyControl rightShiftKey => throw null;
    public KeyControl leftAltKey => throw null;
    public KeyControl rightAltKey => throw null;
    public KeyControl leftCtrlKey => throw null;
    public KeyControl rightCtrlKey => throw null;
    public KeyControl leftMetaKey => throw null;
    public KeyControl rightMetaKey => throw null;
    public KeyControl leftWindowsKey => throw null;
    public KeyControl rightWindowsKey => throw null;
    public KeyControl leftAppleKey => throw null;
    public KeyControl rightAppleKey => throw null;
    public KeyControl leftCommandKey => throw null;
    public KeyControl rightCommandKey => throw null;
    public KeyControl contextMenuKey => throw null;
    public KeyControl escapeKey => throw null;
    public KeyControl leftArrowKey => throw null;
    public KeyControl rightArrowKey => throw null;
    public KeyControl upArrowKey => throw null;
    public KeyControl downArrowKey => throw null;
    public KeyControl backspaceKey => throw null;
    public KeyControl pageDownKey => throw null;
    public KeyControl pageUpKey => throw null;
    public KeyControl homeKey => throw null;
    public KeyControl endKey => throw null;
    public KeyControl insertKey => throw null;
    public KeyControl deleteKey => throw null;
    public KeyControl capsLockKey => throw null;
    public KeyControl scrollLockKey => throw null;
    public KeyControl numLockKey => throw null;
    public KeyControl printScreenKey => throw null;
    public KeyControl pauseKey => throw null;
    public KeyControl numpadEnterKey => throw null;
    public KeyControl numpadDivideKey => throw null;
    public KeyControl numpadMultiplyKey => throw null;
    public KeyControl numpadMinusKey => throw null;
    public KeyControl numpadPlusKey => throw null;
    public KeyControl numpadPeriodKey => throw null;
    public KeyControl numpadEqualsKey => throw null;
    public KeyControl numpad0Key => throw null;
    public KeyControl numpad1Key => throw null;
    public KeyControl numpad2Key => throw null;
    public KeyControl numpad3Key => throw null;
    public KeyControl numpad4Key => throw null;
    public KeyControl numpad5Key => throw null;
    public KeyControl numpad6Key => throw null;
    public KeyControl numpad7Key => throw null;
    public KeyControl numpad8Key => throw null;
    public KeyControl numpad9Key => throw null;
    public KeyControl f1Key => throw null;
    public KeyControl f2Key => throw null;
    public KeyControl f3Key => throw null;
    public KeyControl f4Key => throw null;
    public KeyControl f5Key => throw null;
    public KeyControl f6Key => throw null;
    public KeyControl f7Key => throw null;
    public KeyControl f8Key => throw null;
    public KeyControl f9Key => throw null;
    public KeyControl f10Key => throw null;
    public KeyControl f11Key => throw null;
    public KeyControl f12Key => throw null;
    public KeyControl oem1Key => throw null;
    public KeyControl oem2Key => throw null;
    public KeyControl oem3Key => throw null;
    public KeyControl oem4Key => throw null;
    public KeyControl oem5Key => throw null;
  }
  public class Pointer : InputDevice {
    public static Pointer current { get => throw null; internal set => throw null; }
    public Vector2Control position { get => throw null; protected set => throw null; }
    public DeltaControl delta { get => throw null; protected set => throw null; }
    public AxisControl pressure { get => throw null; protected set => throw null; }
    public ButtonControl press { get => throw null; protected set => throw null; }
  }
  public class Mouse : Pointer {
    public new static Mouse current { get => throw null; private set => throw null; }
    public ButtonControl leftButton { get => throw null; protected set => throw null; }
    public ButtonControl middleButton { get => throw null; protected set => throw null; }
    public ButtonControl rightButton { get => throw null; protected set => throw null; }
    public ButtonControl backButton { get => throw null; protected set => throw null; }
    public ButtonControl forwardButton { get => throw null; protected set => throw null; }
    public DeltaControl scroll { get => throw null; protected set => throw null; }
    public IntegerControl clickCount { get => throw null; protected set => throw null; }
  }
}
