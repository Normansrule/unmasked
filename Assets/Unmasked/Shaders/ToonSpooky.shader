// Unmasked/ToonSpooky: the game's look. Cel-shaded light (soft bands instead of a smooth falloff), a
// rim light that picks silhouettes out of the dark, and a surface pattern (siding, shingles, brick,
// stone, floorboards, grass...) laid over the colour in world space, so boards and bricks are the
// same size on every wall. Built-in render pipeline surface shader; every generated material uses
// it (see TestRoomBuilder.Mat and Editor/Surfaces.cs).
//
// The storybook lighting pass (round 33) adds, driven by globals that Spooky/StoryLight.cs sets:
//  - teal shadows: the dark side of a band leans teal instead of going grey (_StoryShadowTint)
//  - a painted light edge: where a lamp's light gives out, a thin warmer, brighter stripe, like a
//    watercolour wash drying at its edge (_StoryEdge)
//  - creek mist: a low teal mist that pools near the ground and thickens with distance, which lit
//    windows and lanterns shine through (_StoryMist*)
//  - the haunting: rims and mist drift to violet as _StoryHaunt goes from 0 to 1. Violet means a
//    haunting is happening, and nothing else in the world uses it.
Shader "Unmasked/ToonSpooky"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _MainTex ("Albedo", 2D) = "white" {}
        [HDR] _EmissionColor ("Emission", Color) = (0,0,0,0)
        _Bands ("Light bands", Range(2, 6)) = 3
        _RimColor ("Rim colour", Color) = (0.55, 0.78, 0.86, 1)
        _RimPower ("Rim sharpness", Range(0.5, 8)) = 3
        _RimStrength ("Rim strength", Range(0, 2)) = 0.35
        [NoScaleOffset] _PatternTex ("Surface pattern (grey = no change)", 2D) = "gray" {}
        _PatternTile ("Pattern tile size (metres)", Float) = 2
        _PatternStrength ("Pattern strength", Range(0, 1)) = 0
        _PatternSwap ("Swap x and z on top faces", Float) = 0
        _Glossiness ("Unused (kept for Standard compatibility)", Range(0, 1)) = 0.15
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" }
        LOD 200

        CGPROGRAM
        #pragma surface surf Toon fullforwardshadows addshadow finalcolor:Mist
        #pragma target 3.0

        sampler2D _MainTex;
        sampler2D _PatternTex;
        fixed4 _Color;
        half4 _EmissionColor;
        fixed4 _RimColor;
        half _Bands, _RimPower, _RimStrength;

        // Globals from Spooky/StoryLight.cs (all zero means the plain look, so nothing breaks without it)
        half4 _StoryShadowTint;     // rgb: tint for the unlit side of a band, a: how much
        half _StoryEdge;            // strength of the painted light edge
        half4 _StoryMistColor;      // rgb: the creek mist
        half _StoryMistHeight;      // metres the mist rises before it thins out
        half _StoryMistDensity;     // how fast it thickens with distance
        half _StoryHaunt;           // 0 = an ordinary night, 1 = a haunting in full swing
        half4 _StoryHauntColor;     // the haunting's violet
        float _PatternTile, _PatternStrength, _PatternSwap;

        struct Input
        {
            float2 uv_MainTex;
            float3 viewDir;
            float3 worldPos;
            float3 worldNormal;
            INTERNAL_DATA
        };

        half4 LightingToon(SurfaceOutput s, half3 lightDir, half atten)
        {
            half lit = saturate(dot(s.Normal, lightDir)) * atten;
            half b = lit * _Bands;
            half stepped = (floor(b) + smoothstep(0.4, 0.6, frac(b))) / _Bands;
            // A thin, warmer stripe where the light runs out (only where it's actually lighting something).
            half edge = smoothstep(0.02, 0.12, lit) * (1.0 - smoothstep(0.12, 0.3, lit));
            half3 warm = _LightColor0.rgb * half3(1.15, 1.0, 0.8);
            half4 c;
            c.rgb = s.Albedo * (_LightColor0.rgb * stepped + warm * edge * _StoryEdge);
            // The unlit side of the band leans teal rather than going flat grey. Only the main (moon)
            // pass: an extra lamp's pass covers its whole object, lit or not, and would wash it teal.
        #ifndef UNITY_PASS_FORWARDADD
            c.rgb += s.Albedo * _StoryShadowTint.rgb * _StoryShadowTint.a * (1.0 - stepped) * Luminance(_LightColor0.rgb) * 0.35;
        #endif
            c.a = s.Alpha;
            return c;
        }

        // World-space triplanar: walls use (horizontal, height), floors and roofs use (x, z).
        half Pattern(float3 p, float3 n)
        {
            float3 w = pow(abs(n), 8);
            w /= (w.x + w.y + w.z + 1e-5);
            float inv = 1.0 / _PatternTile;
            float2 top = lerp(p.xz, p.zx, _PatternSwap);
            half px = tex2D(_PatternTex, float2(p.z, p.y) * inv).r;
            half py = tex2D(_PatternTex, top * inv).r;
            half pz = tex2D(_PatternTex, float2(p.x, p.y) * inv).r;
            return px * w.x + py * w.y + pz * w.z;
        }

        void surf(Input IN, inout SurfaceOutput o)
        {
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            float3 n = WorldNormalVector(IN, float3(0, 0, 1));
            if (_PatternStrength > 0.001)
                c.rgb *= 1.0 + _PatternStrength * (2.0 * Pattern(IN.worldPos, n) - 1.0);
            o.Albedo = c.rgb;
            o.Alpha = c.a;
            o.Normal = float3(0, 0, 1); // tangent space, so viewDir below is too
            half rim = 1.0 - saturate(dot(normalize(IN.viewDir), o.Normal));
            half3 rimColor = lerp(_RimColor.rgb, _StoryHauntColor.rgb, saturate(_StoryHaunt));
            half rimBoost = 1.0 + saturate(_StoryHaunt) * 0.8;
            o.Emission = _EmissionColor.rgb + rimColor * pow(rim, _RimPower) * _RimStrength * rimBoost * (0.4 + 0.6 * c.rgb);
        }

        // Creek mist, after lighting: thick near the ground and far away, thin up high and close by.
        // Glowing things (windows, jack-o'-lanterns) shine through it. Additive light passes add no mist.
        void Mist(Input IN, SurfaceOutput o, inout fixed4 color)
        {
        #ifndef UNITY_PASS_FORWARDADD
            if (_StoryMistDensity > 0.0001)
            {
                float dist = distance(IN.worldPos, _WorldSpaceCameraPos);
                half low = exp(-max(0.0, IN.worldPos.y) / max(0.1, _StoryMistHeight));
                half amount = (1.0 - exp(-dist * _StoryMistDensity)) * low;
                amount *= 1.0 - saturate(Luminance(o.Emission) * 1.5);
                half3 mist = lerp(_StoryMistColor.rgb, _StoryHauntColor.rgb * 0.6, saturate(_StoryHaunt) * 0.7);
                color.rgb = lerp(color.rgb, mist, saturate(amount));
            }
        #endif
        }
        ENDCG
    }
    FallBack "Diffuse"
}
