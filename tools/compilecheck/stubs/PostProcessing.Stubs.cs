#pragma warning disable CS0067, CS0108, CS0114 // stub file: unused events / hiding are irrelevant
// AUTO-GENERATED stub of com.unity.postprocessing 3.4.0 (needle-mirror, PostProcessing/Runtime/*). Effect parameter
// fields, enums, PostProcessLayer/Volume/Profile/EffectSettings/ParameterOverride members are copied from real source;
// spline/texture-curve fields and rendering internals are omitted.
using System; using System.Collections.Generic; using UnityEngine;
namespace UnityEngine.Rendering.PostProcessing {
  public abstract class ParameterOverride { public bool overrideState; public abstract int GetHash(); public T GetValue<T>() => throw null; }
  public class ParameterOverride<T> : ParameterOverride { public T value; public ParameterOverride() { } public ParameterOverride(T value) { } public ParameterOverride(T value, bool overrideState) { }
    public virtual void Interp(T from, T to, float t) { } public void Override(T x) { } public override int GetHash() => throw null; public static implicit operator T(ParameterOverride<T> prop) => throw null; }
  public sealed class FloatParameter : ParameterOverride<float> { }
  public sealed class IntParameter : ParameterOverride<int> { }
  public sealed class BoolParameter : ParameterOverride<bool> { }
  public sealed class ColorParameter : ParameterOverride<Color> { public static implicit operator Vector4(ColorParameter prop) => throw null; }
  public sealed class Vector2Parameter : ParameterOverride<Vector2> { }
  public sealed class Vector3Parameter : ParameterOverride<Vector3> { }
  public sealed class Vector4Parameter : ParameterOverride<Vector4> { }
  public sealed class TextureParameter : ParameterOverride<Texture> { }
  public class PostProcessEffectSettings : ScriptableObject { public bool active = true; public BoolParameter enabled; public void SetAllOverridesTo(bool state, bool excludeEnabled = true) { } public int GetHash() => throw null; }
  public sealed class PostProcessResources : ScriptableObject { }
  public sealed class PostProcessProfile : ScriptableObject {
    public List<PostProcessEffectSettings> settings; public bool isDirty = true;
    public T AddSettings<T>() where T : PostProcessEffectSettings => throw null;
    public PostProcessEffectSettings AddSettings(Type type) => throw null;
    public PostProcessEffectSettings AddSettings(PostProcessEffectSettings effect) => throw null;
    public void RemoveSettings<T>() where T : PostProcessEffectSettings { } public void RemoveSettings(Type type) { }
    public bool HasSettings<T>() where T : PostProcessEffectSettings => throw null; public bool HasSettings(Type type) => throw null;
    public T GetSetting<T>() where T : PostProcessEffectSettings => throw null;
    public bool TryGetSettings<T>(out T outSetting) where T : PostProcessEffectSettings => throw null; }
  public sealed class PostProcessLayer : MonoBehaviour {
    public enum Antialiasing { None, FastApproximateAntialiasing, SubpixelMorphologicalAntialiasing, TemporalAntialiasing }
    public Transform volumeTrigger; public LayerMask volumeLayer; public bool stopNaNPropagation = true; public bool finalBlitToCameraTarget;
    public Antialiasing antialiasingMode; public bool breakBeforeColorGrading;
    public void Init(PostProcessResources resources) { } public void InitBundles() { } public void ResetHistory() { }
    public T GetSettings<T>() where T : PostProcessEffectSettings => throw null; }
  public sealed class PostProcessVolume : MonoBehaviour { public PostProcessProfile sharedProfile; public bool isGlobal; public float blendDistance; public float weight = 1f; public float priority;
    public PostProcessProfile profile { get => throw null; set => throw null; } public bool HasInstantiatedProfile() => throw null; }
  public sealed class Bloom : PostProcessEffectSettings { public FloatParameter intensity; public FloatParameter threshold; public FloatParameter softKnee; public FloatParameter clamp; public FloatParameter diffusion; public FloatParameter anamorphicRatio; public ColorParameter color; public BoolParameter fastMode; public TextureParameter dirtTexture; public FloatParameter dirtIntensity; }
  public enum VignetteMode { Classic, Masked }
  public sealed class VignetteModeParameter : ParameterOverride<VignetteMode> { }
  public sealed class Vignette : PostProcessEffectSettings { public VignetteModeParameter mode; public ColorParameter color; public Vector2Parameter center; public FloatParameter intensity; public FloatParameter smoothness; public FloatParameter roundness; public BoolParameter rounded; public TextureParameter mask; public FloatParameter opacity; }
  public enum GradingMode { LowDefinitionRange, HighDefinitionRange, External }
  public enum Tonemapper { None, Neutral, ACES, Custom }
  public sealed class GradingModeParameter : ParameterOverride<GradingMode> { }
  public sealed class TonemapperParameter : ParameterOverride<Tonemapper> { }
  public sealed class ColorGrading : PostProcessEffectSettings { public GradingModeParameter gradingMode; public TextureParameter externalLut; public TonemapperParameter tonemapper; public FloatParameter toneCurveToeStrength; public FloatParameter toneCurveToeLength; public FloatParameter toneCurveShoulderStrength; public FloatParameter toneCurveShoulderLength; public FloatParameter toneCurveShoulderAngle; public FloatParameter toneCurveGamma; public TextureParameter ldrLut; public FloatParameter ldrLutContribution; public FloatParameter temperature; public FloatParameter tint; public ColorParameter colorFilter; public FloatParameter hueShift; public FloatParameter saturation; public FloatParameter brightness; public FloatParameter postExposure; public FloatParameter contrast; public FloatParameter mixerRedOutRedIn; public FloatParameter mixerRedOutGreenIn; public FloatParameter mixerRedOutBlueIn; public FloatParameter mixerGreenOutRedIn; public FloatParameter mixerGreenOutGreenIn; public FloatParameter mixerGreenOutBlueIn; public FloatParameter mixerBlueOutRedIn; public FloatParameter mixerBlueOutGreenIn; public FloatParameter mixerBlueOutBlueIn; public Vector4Parameter lift; public Vector4Parameter gamma; public Vector4Parameter gain; }
  public enum AmbientOcclusionMode { ScalableAmbientObscurance, MultiScaleVolumetricObscurance }
  public enum AmbientOcclusionQuality { Lowest, Low, Medium, High, Ultra }
  public sealed class AmbientOcclusionModeParameter : ParameterOverride<AmbientOcclusionMode> { }
  public sealed class AmbientOcclusionQualityParameter : ParameterOverride<AmbientOcclusionQuality> { }
  public sealed class AmbientOcclusion : PostProcessEffectSettings { public AmbientOcclusionModeParameter mode; public FloatParameter intensity; public ColorParameter color; public BoolParameter ambientOnly; public FloatParameter noiseFilterTolerance; public FloatParameter blurTolerance; public FloatParameter upsampleTolerance; public FloatParameter thicknessModifier; public FloatParameter zBias; public FloatParameter directLightingStrength; public FloatParameter radius; public AmbientOcclusionQualityParameter quality; }
  public sealed class Grain : PostProcessEffectSettings { public BoolParameter colored; public FloatParameter intensity; public FloatParameter size; public FloatParameter lumContrib; }
}
