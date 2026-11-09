using UnityEngine;
using UnityEngine.Rendering.PostProcessing;

namespace Unmasked
{
    /// <summary>
    /// The storybook lighting pass (round 33): the night's mood, set every frame from what's happening
    /// to you. It follows the colour rules in Docs/ART_DIRECTION.md:
    ///  - <b>teal</b> is the night itself: teal shadows and a low creek mist (always on);
    ///  - <b>amber</b> is welcome: a warmer, softer picture near Mystery Club HQ and while picking a call;
    ///  - <b>violet</b> is a haunting and nothing else: it creeps into rims, mist and the grade as your
    ///    fear rises, while you're on the lot of a house being haunted, and always a little for whoever
    ///    is playing the Haunter (so they see the world the way the haunting does);
    ///  - <b>gold</b> is the unmasking: a warm swell when the mask comes off.
    ///
    /// It drives the ToonSpooky shader's _Story* globals and three post-processing volumes it makes at
    /// runtime, on top of the base "Spooky Post FX" profile the editor builds. It never touches
    /// RenderSettings (NightEventFX and the map own those), so the night events still work as before.
    /// Since round 34 the mist also settles lower as lanterns go back on the Hook Board.
    /// Everything eases in and out over a second or two; with reduced motion the gold swell stays at
    /// half strength.
    /// </summary>
    public class StoryLight : MonoBehaviour
    {
        public static StoryLight Instance { get; private set; }

        [Header("The night (teal)")]
        public Color ShadowTint = new(0.2f, 0.55f, 0.62f, 1f);
        [Range(0, 1)] public float PaintedEdge = 0.35f;
        public Color Mist = new(0.11f, 0.2f, 0.24f, 1f);
        public float MistHeight = 2.2f;
        public float MistDensity = 0.012f;

        [Header("The haunting (violet)")]
        public Color Haunt = new(0.62f, 0.42f, 1f, 1f);
        [Tooltip("How much violet whoever plays the Haunter always sees.")]
        [Range(0, 1)] public float HaunterView = 0.35f;

        /// <summary>0 to 1: how haunted the picture is right now (eased).</summary>
        public float HauntAmount { get; private set; }
        public float HomeAmount { get; private set; }
        public float GoldAmount { get; private set; }

        PostProcessVolume hauntVolume, homeVolume, goldVolume;
        float unmaskedAt = -100f;
        MatchPhase lastPhase;

        static readonly int ShadowTintId = Shader.PropertyToID("_StoryShadowTint");
        static readonly int EdgeId = Shader.PropertyToID("_StoryEdge");
        static readonly int MistColorId = Shader.PropertyToID("_StoryMistColor");
        static readonly int MistHeightId = Shader.PropertyToID("_StoryMistHeight");
        static readonly int MistDensityId = Shader.PropertyToID("_StoryMistDensity");
        static readonly int HauntId = Shader.PropertyToID("_StoryHaunt");
        static readonly int HauntColorId = Shader.PropertyToID("_StoryHauntColor");

        /// <summary>Called by GameHUD: one StoryLight per game.</summary>
        public static void Ensure(GameObject host)
        {
            if (Instance == null && host.GetComponent<StoryLight>() == null) host.AddComponent<StoryLight>();
        }

        void Awake()
        {
            Instance = this;
            hauntVolume = MakeVolume("Story: haunting", HauntProfile(), 2f);
            homeVolume = MakeVolume("Story: home", HomeProfile(), 2f);
            goldVolume = MakeVolume("Story: unmasking", GoldProfile(), 3f);
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
            Shader.SetGlobalFloat(HauntId, 0f);
            Shader.SetGlobalFloat(MistDensityId, 0f);
        }

        PostProcessVolume MakeVolume(string name, PostProcessProfile profile, float priority)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var v = go.AddComponent<PostProcessVolume>();
            v.isGlobal = true;
            v.priority = priority;
            v.profile = profile;
            v.weight = 0f;
            return v;
        }

        static PostProcessProfile HauntProfile()
        {
            var p = ScriptableObject.CreateInstance<PostProcessProfile>();
            var grade = p.AddSettings<ColorGrading>();
            grade.enabled.Override(true);
            grade.colorFilter.Override(new Color(0.86f, 0.78f, 1f));
            grade.saturation.Override(-8f);
            grade.tint.Override(14f);
            var vignette = p.AddSettings<Vignette>();
            vignette.enabled.Override(true);
            vignette.intensity.Override(0.55f);
            vignette.color.Override(new Color(0.12f, 0.02f, 0.2f));
            var ca = p.AddSettings<ChromaticAberration>();
            ca.enabled.Override(true);
            ca.intensity.Override(0.18f);
            return p;
        }

        static PostProcessProfile HomeProfile()
        {
            var p = ScriptableObject.CreateInstance<PostProcessProfile>();
            var grade = p.AddSettings<ColorGrading>();
            grade.enabled.Override(true);
            grade.temperature.Override(14f);
            grade.colorFilter.Override(new Color(1f, 0.95f, 0.86f));
            grade.saturation.Override(6f);
            var vignette = p.AddSettings<Vignette>();
            vignette.enabled.Override(true);
            vignette.intensity.Override(0.28f);
            vignette.color.Override(new Color(0.1f, 0.05f, 0.02f));
            return p;
        }

        static PostProcessProfile GoldProfile()
        {
            var p = ScriptableObject.CreateInstance<PostProcessProfile>();
            var grade = p.AddSettings<ColorGrading>();
            grade.enabled.Override(true);
            grade.temperature.Override(24f);
            grade.postExposure.Override(0.35f);
            grade.colorFilter.Override(new Color(1f, 0.9f, 0.7f));
            var bloom = p.AddSettings<Bloom>();
            bloom.enabled.Override(true);
            bloom.intensity.Override(6f);
            bloom.color.Override(new Color(1f, 0.82f, 0.5f));
            return p;
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            Targets(out float haunt, out float home, out float gold);
            HauntAmount = Mathf.MoveTowards(HauntAmount, haunt, dt * (haunt > HauntAmount ? 0.6f : 0.35f));
            HomeAmount = Mathf.MoveTowards(HomeAmount, home, dt * 0.5f);
            GoldAmount = Mathf.MoveTowards(GoldAmount, gold, dt * (gold > GoldAmount ? 1.5f : 0.4f));

            // Haunting and welcome don't mix: the violet wins.
            hauntVolume.weight = HauntAmount;
            homeVolume.weight = HomeAmount * (1f - HauntAmount);
            goldVolume.weight = GoldAmount;

            Shader.SetGlobalColor(ShadowTintId, ShadowTint);
            Shader.SetGlobalFloat(EdgeId, PaintedEdge);
            Shader.SetGlobalColor(MistColorId, Color.Lerp(Mist, RenderSettings.fogColor, 0.35f)); // a foggy or blood-red night tints the mist too
            // Every lantern back on the Hook Board pushes the creek mist down a little (HookBoard.cs);
            // with all twenty-four home it lies low and thin for good.
            float hooks = Mathf.Clamp01(ClubBook.HooksFilled / (float)HookBoard.Hooks);
            Shader.SetGlobalFloat(MistHeightId, MistHeight * (1f - 0.45f * hooks));
            Shader.SetGlobalFloat(MistDensityId, MistDensity * (1f - 0.6f * GoldAmount) * (1f - 0.5f * hooks)); // the mist lifts when the mask comes off
            Shader.SetGlobalFloat(HauntId, HauntAmount);
            Shader.SetGlobalColor(HauntColorId, Haunt);
        }

        /// <summary>Where each mood should be heading, from the match and from where you're standing.</summary>
        void Targets(out float haunt, out float home, out float gold)
        {
            haunt = home = gold = 0f;
            var game = MysteryGameManager.Instance;
            var agent = PlayerAgent.Local;
            if (game == null || !game.IsSpawned) return;
            var phase = game.Phase.Value;

            if (phase != lastPhase)
            {
                if (phase == MatchPhase.Unmasking) unmaskedAt = Time.unscaledTime;
                lastPhase = phase;
            }

            bool onCase = phase == MatchPhase.Investigation || phase == MatchPhase.Trap;
            if (agent != null && agent.Side.Value == PlayerSide.Haunter && onCase) haunt = HaunterView;

            var me = SolverController.Local;
            if (me != null)
            {
                if (me.Fear != null && me.Fear.MaxFear > 0f) haunt = Mathf.Max(haunt, Mathf.Clamp01(me.Fear.Fear / me.Fear.MaxFear) * 0.9f);
                var site = game.ActiveSite;
                if (onCase && site != null && OnLot(site, me.transform.position, 4f)) haunt = Mathf.Max(haunt, phase == MatchPhase.Trap ? 0.4f : 0.22f);
                var hq = TownDirector.Instance != null ? TownDirector.Instance.HQ : null;
                if (hq != null && OnLot(hq, me.transform.position, 18f)) home = 1f;
            }
            if (phase == MatchPhase.Setup || phase == MatchPhase.WaitingToStart) home = Mathf.Max(home, 0.6f);

            // The gold swell: up as the mask comes off, then easing back down over a few seconds.
            float age = Time.unscaledTime - unmaskedAt;
            if (phase == MatchPhase.Unmasking || (phase == MatchPhase.Ended && game.Winner.Value == MatchWinner.Solvers))
            {
                gold = age < 4f ? 1f : Mathf.Lerp(1f, 0.25f, Mathf.Clamp01((age - 4f) / 4f));
                if (UITheme.ReduceMotion) gold = Mathf.Min(gold, 0.5f);
                haunt = 0f;
            }
        }

        static bool OnLot(HouseSite site, Vector3 p, float margin) =>
            p.x > site.LotMin.x - margin && p.x < site.LotMax.x + margin && p.z > site.LotMin.y - margin && p.z < site.LotMax.y + margin;
    }
}
