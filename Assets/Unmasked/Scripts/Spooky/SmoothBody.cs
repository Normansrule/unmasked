using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;
using UnityEngine.Rendering;

namespace Unmasked
{
    /// <summary>
    /// One smooth skin for a person (round 45), instead of a stack of separate capsules and spheres that
    /// read as toy pieces. The body's own parts (torso, shoulders, arms, legs, neck, head, jaw, cheeks,
    /// ears, skirt tiers) are melted together with a smooth union of their distance fields and meshed
    /// with surface nets, so an arm flows into its shoulder and a jaw into its head. Every bit of the
    /// skin keeps the material of the part it's closest to, so clothes keep their colours. Faces, hair,
    /// hands, shoes and accessories stay as their own parts on top.
    ///
    /// The builders add this to an outfit's root with <see cref="Attach"/>. The original part objects
    /// stay (hats still find "Head"); only their renderers are switched off while this is enabled, so
    /// removing the script brings the old look straight back. The skin mesh is made in code when the
    /// outfit is enabled, never saved, and shared by every outfit with the same parts.
    /// Docs/tools/smoothbody.py does exactly the same for the pictures.
    ///
    /// Round 46: the nose, the palm and thumb, and the hair melt in too, each limb is meshed on its own
    /// grid, and the head, hair and hands use a grid twice as fine so small shapes keep their form.
    /// </summary>
    [ExecuteAlways]
    public class SmoothBody : MonoBehaviour
    {
        /// <summary>Grid spacing in metres: fine enough for a chin, coarse enough to build in a blink.</summary>
        public const float Cell = 0.012f;
        const float KHead = 0.04f, KBody = 0.042f, KSkirt = 0.07f, Margin = 0.08f;
        const float KNose = 0.012f, KHand = 0.008f, KHair = 0.03f; // round 46: a nose grown out of the face, one-piece palms, soft hair

        static readonly Regex BodyName = new Regex(@"^(Chest|ShoulderLine|Shoulders|Waist|Hips|Belly|Neck|Head|Jaw|Chin|Cheek[LR]|Ear[LR]|" +
                                                   @"Shoulder[LR]|UpperArm[LR]|Elbow[LR]|Forearm[LR]|Wrist[LR]|Thigh[LR]|Shin[LR]|Ankle[LR]|\w+Tier\d|Nose|NoseBridge|NoseWing[LR]|Hand[LR](?:Knuckles|Thumb)?|" +
                                                   @"Hair(?:Crown|Back|Front|Long|Fall|Sweep|Part|Curtain[LR]|Temple[LR]|Strand[LR]|Tuft\d|Flyaway)|" +
                                                   @"Fringe|Sideburn[LR]|SideHair[LR]|Bun|Updo|Bouffant|Ponytail|Braid|Curls?|Curl[LR\d]+)$");
        static readonly Regex NoseName = new Regex(@"^(Nose|NoseBridge|NoseWing[LR])$");
        static readonly Regex HandName = new Regex(@"^Hand([LR])(?:Knuckles|Thumb)?$");
        static readonly Regex HairName = new Regex(@"^(Hair\w*|Fringe|Sideburn[LR]|SideHair[LR]|Bun|Updo|Bouffant|Ponytail|Braid|Curls?|Curl[LR\d]+)$");
        static readonly Regex HeadName = new Regex(@"^(Head|Jaw|Chin|Cheek[LR]|Ear[LR])$");
        static readonly Regex ArmName = new Regex(@"^(Shoulder|UpperArm|Elbow|Forearm|Wrist)([LR])$");
        static readonly Regex LegName = new Regex(@"^(Thigh|Shin|Ankle)([LR])$");

        const int Torso = 1, HeadG = 2, ArmL = 4, ArmR = 8, LegL = 16, LegR = 32, Skirt = 64, HandL = 128, HandR = 256, Hair = 512;
        const int Fine = HeadG | Hair | HandL | HandR; // small, detailed limbs get a grid twice as fine

        /// <summary>One part that melts into the skin: 0 sphere, 1 capsule, 2 cylinder.</summary>
        [System.Serializable]
        public class Piece
        {
            public Transform t;
            public Renderer r;
            public int shape;
        }

        public List<Piece> pieces = new List<Piece>();

        class Built
        {
            public Mesh mesh;
            public Material[] mats;
        }

        static readonly Dictionary<string, Built> cache = new Dictionary<string, Built>();
        GameObject skin;

        /// <summary>
        /// Adds a smooth skin to an outfit just built from Costumes.json parts under root, whose first
        /// non-mask part is root's child number firstChild. Returns null (and adds nothing) for anything
        /// that isn't a person: it needs a head and a chest, waist or shoulders.
        /// </summary>
        public static SmoothBody Attach(Transform root, Costumes.Part[] parts, int firstChild = 0)
        {
            if (root == null || parts == null) return null;
            var list = new List<Piece>();
            bool head = false, trunk = false;
            int child = firstChild;
            foreach (var q in parts)
            {
                if (q.k == "mask") continue;
                if (child < root.childCount && root.GetChild(child).name == "Mask" && q.n != "Mask") child++;
                if (child >= root.childCount) break;
                var t = root.GetChild(child++);
                if (!BodyName.IsMatch(q.n) || q.m != "solid" || q.s == null || q.s.Length < 3) continue;
                if (Mathf.Min(Mathf.Abs(q.s[0]), Mathf.Abs(q.s[1]), Mathf.Abs(q.s[2])) < 0.03f) continue; // blush and other paint stays on top
                int shape = q.t switch { "sphere" => 0, "capsule" => 1, "cyl" or "rcyl" => 2, _ => -1 };
                if (shape < 0) continue;
                var r = t.GetComponent<Renderer>();
                if (r == null) continue;
                list.Add(new Piece { t = t, r = r, shape = shape });
                head |= q.n == "Head";
                trunk |= q.n == "Chest" || q.n == "Waist" || q.n == "Shoulders";
            }
            if (!head || !trunk) return null;
            var sb = root.gameObject.AddComponent<SmoothBody>();
            sb.pieces = list;
            if (sb.isActiveAndEnabled) sb.OnEnable(); // the pieces arrive after AddComponent's own OnEnable
            return sb;
        }

        void OnEnable()
        {
            if (pieces == null || pieces.Count == 0) return;
            var b = Get(pieces);
            if (b == null) return;
            if (skin == null)
            {
                skin = new GameObject("SmoothSkin") { hideFlags = HideFlags.DontSave };
                skin.transform.SetParent(transform, false);
                skin.AddComponent<MeshFilter>();
                skin.AddComponent<MeshRenderer>();
            }
            skin.GetComponent<MeshFilter>().sharedMesh = b.mesh;
            skin.GetComponent<MeshRenderer>().sharedMaterials = b.mats;
            foreach (var p in pieces)
                if (p != null && p.r != null) p.r.enabled = false;
        }

        void OnDisable()
        {
            if (pieces != null)
                foreach (var p in pieces)
                    if (p != null && p.r != null) p.r.enabled = true;
            if (skin != null)
            {
                if (Application.isPlaying) Destroy(skin);
                else DestroyImmediate(skin);
                skin = null;
            }
        }

        static Built Get(List<Piece> ps)
        {
            var key = new StringBuilder();
            foreach (var p in ps)
            {
                if (p == null || p.t == null || p.r == null || p.r.sharedMaterial == null) return null;
                key.Append(p.shape).Append(p.t.name).Append(p.t.localPosition.ToString("F3")).Append(p.t.localEulerAngles.ToString("F1"))
                   .Append(p.t.localScale.ToString("F3")).Append(p.r.sharedMaterial.GetInstanceID()).Append('|');
            }
            string k = key.ToString();
            if (cache.TryGetValue(k, out var hit) && hit.mesh != null) return hit;
            return cache[k] = Make(ps);
        }

        // ---- the distance field ------------------------------------------------------------------

        struct Shape
        {
            public int kind, groups;
            public Vector3 pos, scale;
            public Quaternion inv;
            public float k;
            public Vector3 lo, hi;
        }

        static int GroupsOf(string name)
        {
            var hand = HandName.Match(name);
            if (hand.Success) return hand.Groups[1].Value == "L" ? HandL : HandR;
            if (HairName.IsMatch(name)) return Hair;
            if (NoseName.IsMatch(name)) return HeadG;
            var arm = ArmName.Match(name);
            if (arm.Success) return arm.Groups[2].Value == "L" ? ArmL : ArmR;
            var leg = LegName.Match(name);
            if (leg.Success) return leg.Groups[2].Value == "L" ? LegL : LegR;
            if (name.Contains("Tier")) return Skirt;
            if (HeadName.IsMatch(name)) return HeadG;
            if (name == "Neck") return HeadG | Torso;
            if (name == "Chest" || name == "ShoulderLine" || name == "Shoulders") return Torso | ArmL | ArmR;
            if (name == "Hips" || name == "Waist") return Torso | LegL | LegR;
            return Torso;
        }

        static float Ell3(Vector3 p, Vector3 r)
        {
            var a = new Vector3(p.x / r.x, p.y / r.y, p.z / r.z);
            var b = new Vector3(a.x / r.x, a.y / r.y, a.z / r.z);
            float k0 = a.magnitude, k1 = b.magnitude;
            return k1 > 1e-9f ? k0 * (k0 - 1f) / k1 : -Mathf.Min(r.x, Mathf.Min(r.y, r.z));
        }

        static float Ell2(float x, float z, float rx, float rz)
        {
            float ax = x / rx, az = z / rz, bx = ax / rx, bz = az / rz;
            float k0 = Mathf.Sqrt(ax * ax + az * az), k1 = Mathf.Sqrt(bx * bx + bz * bz);
            return k1 > 1e-9f ? k0 * (k0 - 1f) / k1 : -Mathf.Min(rx, rz);
        }

        /// <summary>Signed distance in metres, measured in the part's own stretched space.</summary>
        static float Sdf(in Shape s, Vector3 P)
        {
            var L = s.inv * (P - s.pos);
            if (s.kind == 0) return Ell3(L, s.scale * 0.5f);
            if (s.kind == 1)
            {
                L.y -= Mathf.Clamp(L.y / s.scale.y, -0.5f, 0.5f) * s.scale.y;
                return Ell3(L, s.scale * 0.5f);
            }
            float a = Ell2(L.x, L.z, s.scale.x * 0.5f, s.scale.z * 0.5f);
            float b = Mathf.Abs(L.y) - s.scale.y;
            float ma = Mathf.Max(a, 0f), mb = Mathf.Max(b, 0f);
            return Mathf.Min(Mathf.Max(a, b), 0f) + Mathf.Sqrt(ma * ma + mb * mb);
        }

        static float Smin(float a, float b, float k)
        {
            float h = Mathf.Clamp01(0.5f + 0.5f * (b - a) / k);
            return b + (a - b) * h - k * h * (1f - h);
        }

        static Built Make(List<Piece> ps)
        {
            int n = ps.Count;
            var shapes = new Shape[n];
            Vector3 lo = Vector3.one * 1e9f, hi = Vector3.one * -1e9f;
            for (int i = 0; i < n; i++)
            {
                var t = ps[i].t;
                var sc = t.localScale;
                var s = new Shape
                {
                    kind = ps[i].shape,
                    groups = GroupsOf(t.name),
                    pos = t.localPosition,
                    inv = Quaternion.Inverse(t.localRotation),
                    scale = new Vector3(Mathf.Max(Mathf.Abs(sc.x), 1e-4f), Mathf.Max(Mathf.Abs(sc.y), 1e-4f), Mathf.Max(Mathf.Abs(sc.z), 1e-4f)),
                };
                s.k = NoseName.IsMatch(t.name) ? KNose : HandName.IsMatch(t.name) ? KHand : HairName.IsMatch(t.name) ? KHair
                    : HeadName.IsMatch(t.name) ? KHead : t.name.Contains("Tier") ? KSkirt : KBody;
                float hy = s.kind == 0 ? 0.5f : 1f;
                Vector3 a = Vector3.one * 1e9f, b = Vector3.one * -1e9f;
                for (int c = 0; c < 8; c++)
                {
                    var corner = Vector3.Scale(new Vector3((c & 1) != 0 ? 0.5f : -0.5f, (c & 2) != 0 ? hy : -hy, (c & 4) != 0 ? 0.5f : -0.5f), s.scale);
                    var w = t.localRotation * corner + s.pos;
                    a = Vector3.Min(a, w);
                    b = Vector3.Max(b, w);
                }
                s.lo = a;
                s.hi = b;
                lo = Vector3.Min(lo, a);
                hi = Vector3.Max(hi, b);
                shapes[i] = s;
            }
            // each limb gets its own grid round just its parts; the limbs' skins overlap where they meet
            var verts = new List<Vector3>();
            var normals = new List<Vector3>();
            var tris = new List<int>();
            int all = 0;
            foreach (var s in shapes) all |= s.groups;
            for (int g = 1; g <= Hair; g <<= 1)
            {
                if ((all & g) == 0) continue;
                float cell = (g & Fine) != 0 ? Cell * 0.5f : Cell;
                Vector3 glo = Vector3.one * 1e9f, ghi = Vector3.one * -1e9f;
                foreach (var s in shapes)
                    if ((s.groups & g) != 0) { glo = Vector3.Min(glo, s.lo); ghi = Vector3.Max(ghi, s.hi); }
                glo -= Vector3.one * Margin;
                ghi += Vector3.one * Margin;
                int nx = Mathf.CeilToInt((ghi.x - glo.x) / cell) + 1, ny = Mathf.CeilToInt((ghi.y - glo.y) / cell) + 1, nz = Mathf.CeilToInt((ghi.z - glo.z) / cell) + 1;
                var F = new float[nx * ny * nz];
                for (int i = 0; i < F.Length; i++) F[i] = 1f;
                foreach (var s in shapes)
                {
                    if ((s.groups & g) == 0) continue;
                    float pad = s.k + 0.03f;
                    int x0 = Mathf.Max(Mathf.FloorToInt((s.lo.x - pad - glo.x) / cell), 0), x1 = Mathf.Min(Mathf.CeilToInt((s.hi.x + pad - glo.x) / cell) + 1, nx);
                    int y0 = Mathf.Max(Mathf.FloorToInt((s.lo.y - pad - glo.y) / cell), 0), y1 = Mathf.Min(Mathf.CeilToInt((s.hi.y + pad - glo.y) / cell) + 1, ny);
                    int z0 = Mathf.Max(Mathf.FloorToInt((s.lo.z - pad - glo.z) / cell), 0), z1 = Mathf.Min(Mathf.CeilToInt((s.hi.z + pad - glo.z) / cell) + 1, nz);
                    for (int x = x0; x < x1; x++)
                        for (int y = y0; y < y1; y++)
                            for (int z = z0; z < z1; z++)
                            {
                                int id = (x * ny + y) * nz + z;
                                F[id] = Smin(Sdf(s, glo + new Vector3(x, y, z) * cell), F[id], s.k);
                            }
                }
                Polygonise(F, glo, cell, nx, ny, nz, verts, normals, tris);
            }
            return Finish(ps, shapes, verts, normals, tris);
        }

        // ---- surface nets --------------------------------------------------------------------------

        /// <summary>Surface nets: adds one limb's skin (corners, normals, triangles) to the lists.</summary>
        static void Polygonise(float[] F, Vector3 lo, float Cell, int nx, int ny, int nz, List<Vector3> verts, List<Vector3> normals, List<int> tris)
        {
            int cx = nx - 1, cy = ny - 1, cz = nz - 1;
            int first = verts.Count;
            var vid = new int[cx * cy * cz];
            var v = new float[8];
            for (int x = 0; x < cx; x++)
                for (int y = 0; y < cy; y++)
                    for (int z = 0; z < cz; z++)
                    {
                        int cell = (x * cy + y) * cz + z, inside = 0;
                        vid[cell] = -1;
                        for (int c = 0; c < 8; c++)
                        {
                            v[c] = F[((x + (c & 1)) * ny + y + ((c >> 1) & 1)) * nz + z + ((c >> 2) & 1)];
                            if (v[c] < 0f) inside |= 1 << c;
                        }
                        if (inside == 0 || inside == 255) continue;
                        Vector3 sum = Vector3.zero;
                        int count = 0;
                        for (int a = 0; a < 8; a++)
                            for (int bit = 1; bit <= 4; bit <<= 1)
                            {
                                if ((a & bit) != 0) continue;
                                int b = a | bit;
                                if (((inside >> a) & 1) == ((inside >> b) & 1)) continue;
                                float t = v[a] / (v[a] - v[b]);
                                var pa = new Vector3(a & 1, (a >> 1) & 1, (a >> 2) & 1);
                                var pb = new Vector3(b & 1, (b >> 1) & 1, (b >> 2) & 1);
                                sum += pa + (pb - pa) * t;
                                count++;
                            }
                        vid[cell] = verts.Count;
                        verts.Add(lo + (new Vector3(x, y, z) + sum / count) * Cell);
                    }

            // the normal at each corner: the field's slope, measured two cells apart so it doesn't ripple with the grid
            for (int i = first; i < verts.Count; i++)
            {
                var g = (verts[i] - lo) / Cell;
                Vector3 X = Vector3.right * 2f, Y = Vector3.up * 2f, Z = Vector3.forward * 2f;
                normals.Add(new Vector3(Sample(F, g + X, nx, ny, nz) - Sample(F, g - X, nx, ny, nz),
                                        Sample(F, g + Y, nx, ny, nz) - Sample(F, g - Y, nx, ny, nz),
                                        Sample(F, g + Z, nx, ny, nz) - Sample(F, g - Z, nx, ny, nz)).normalized);
            }

            // one quad round every grid edge the surface crosses
            int[] dims = { nx, ny, nz };
            for (int x = 0; x < nx; x++)
                for (int y = 0; y < ny; y++)
                    for (int z = 0; z < nz; z++)
                    {
                        bool here = F[(x * ny + y) * nz + z] < 0f;
                        int[] c = { x, y, z };
                        for (int ax = 0; ax < 3; ax++)
                        {
                            if (c[ax] + 1 >= dims[ax]) continue;
                            int[] d = { x, y, z };
                            d[ax]++;
                            if ((F[(d[0] * ny + d[1]) * nz + d[2]] < 0f) == here) continue;
                            int o1 = (ax + 1) % 3, o2 = (ax + 2) % 3;
                            if (c[o1] < 1 || c[o2] < 1 || c[o1] > dims[o1] - 2 || c[o2] > dims[o2] - 2) continue;
                            int q0 = CellAt(vid, c, o1, o2, 1, 1, cy, cz), q1 = CellAt(vid, c, o1, o2, 0, 1, cy, cz);
                            int q2 = CellAt(vid, c, o1, o2, 0, 0, cy, cz), q3 = CellAt(vid, c, o1, o2, 1, 0, cy, cz);
                            if (q0 < 0 || q1 < 0 || q2 < 0 || q3 < 0) continue;
                            Add(tris, verts, normals, q0, q1, q2);
                            Add(tris, verts, normals, q0, q2, q3);
                        }
                    }
        }

        static Built Finish(List<Piece> ps, Shape[] shapes, List<Vector3> verts, List<Vector3> normals, List<int> tris)
        {
            // each triangle takes the material of the part nearest its middle
            var mats = new List<Material>();
            var subs = new List<List<int>>();
            for (int i = 0; i < tris.Count; i += 3)
            {
                var mid = (verts[tris[i]] + verts[tris[i + 1]] + verts[tris[i + 2]]) / 3f;
                int best = 0;
                float bd = float.MaxValue;
                for (int s = 0; s < shapes.Length; s++)
                {
                    float d = Sdf(shapes[s], mid);
                    if (d < bd) { bd = d; best = s; }
                }
                var mat = ps[best].r.sharedMaterial;
                int m = mats.IndexOf(mat);
                if (m < 0) { m = mats.Count; mats.Add(mat); subs.Add(new List<int>()); }
                subs[m].Add(tris[i]);
                subs[m].Add(tris[i + 1]);
                subs[m].Add(tris[i + 2]);
            }

            var mesh = new Mesh { name = "SmoothBody", hideFlags = HideFlags.DontSave };
            if (verts.Count > 65000) mesh.indexFormat = IndexFormat.UInt32;
            mesh.SetVertices(verts);
            mesh.SetNormals(normals);
            mesh.subMeshCount = subs.Count;
            for (int m = 0; m < subs.Count; m++) mesh.SetTriangles(subs[m], m);
            mesh.RecalculateBounds();
            return new Built { mesh = mesh, mats = mats.ToArray() };
        }

        static int CellAt(int[] vid, int[] c, int o1, int o2, int d1, int d2, int cy, int cz)
        {
            int[] q = { c[0], c[1], c[2] };
            q[o1] -= d1;
            q[o2] -= d2;
            return vid[(q[0] * cy + q[1]) * cz + q[2]];
        }

        /// <summary>Adds a triangle wound so its front faces the way the field's normals point.</summary>
        static void Add(List<int> tris, List<Vector3> verts, List<Vector3> normals, int a, int b, int c)
        {
            var face = Vector3.Cross(verts[b] - verts[a], verts[c] - verts[a]);
            if (Vector3.Dot(face, normals[a] + normals[b] + normals[c]) < 0f) (b, c) = (c, b);
            tris.Add(a);
            tris.Add(b);
            tris.Add(c);
        }

        static float Sample(float[] F, Vector3 g, int nx, int ny, int nz)
        {
            int x = Mathf.Clamp(Mathf.FloorToInt(g.x), 0, nx - 2), y = Mathf.Clamp(Mathf.FloorToInt(g.y), 0, ny - 2), z = Mathf.Clamp(Mathf.FloorToInt(g.z), 0, nz - 2);
            float fx = Mathf.Clamp01(g.x - x), fy = Mathf.Clamp01(g.y - y), fz = Mathf.Clamp01(g.z - z);
            float At(int i, int j, int k) => F[((x + i) * ny + y + j) * nz + z + k];
            float c00 = Mathf.Lerp(At(0, 0, 0), At(1, 0, 0), fx), c10 = Mathf.Lerp(At(0, 1, 0), At(1, 1, 0), fx);
            float c01 = Mathf.Lerp(At(0, 0, 1), At(1, 0, 1), fx), c11 = Mathf.Lerp(At(0, 1, 1), At(1, 1, 1), fx);
            return Mathf.Lerp(Mathf.Lerp(c00, c10, fy), Mathf.Lerp(c01, c11, fy), fz);
        }
    }
}
