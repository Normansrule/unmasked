// Unmasked/ToonSpooky: the game's look. Cel-shaded light (soft bands instead of a smooth falloff), a
// violet rim light that picks silhouettes out of the dark, and a surface pattern (siding, shingles,
// brick, stone, floorboards, grass...) laid over the colour in world space, so boards and bricks are
// the same size on every wall. Built-in render pipeline surface shader; every generated material uses
// it (see TestRoomBuilder.Mat and Editor/Surfaces.cs).
Shader "Unmasked/ToonSpooky"
{
    Properties
    {
        _Color ("Color", Color) = (1,1,1,1)
        _MainTex ("Albedo", 2D) = "white" {}
        [HDR] _EmissionColor ("Emission", Color) = (0,0,0,0)
        _Bands ("Light bands", Range(2, 6)) = 3
        _RimColor ("Rim colour", Color) = (0.55, 0.4, 1, 1)
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
        #pragma surface surf Toon fullforwardshadows addshadow
        #pragma target 3.0

        sampler2D _MainTex;
        sampler2D _PatternTex;
        fixed4 _Color;
        half4 _EmissionColor;
        fixed4 _RimColor;
        half _Bands, _RimPower, _RimStrength;
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
            half4 c;
            c.rgb = s.Albedo * _LightColor0.rgb * stepped;
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
            o.Emission = _EmissionColor.rgb + _RimColor.rgb * pow(rim, _RimPower) * _RimStrength * (0.4 + 0.6 * c.rgb);
        }
        ENDCG
    }
    FallBack "Diffuse"
}
