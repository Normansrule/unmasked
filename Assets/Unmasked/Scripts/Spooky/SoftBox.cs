using UnityEngine;

namespace Unmasked
{
    /// <summary>
    /// A box (or cylinder) with soft, rounded edges (round 42), for the parts of a character that used to be hard
    /// cubes: boots and shoes, soles and heels, aprons, belts, bibs, collars, pockets. Costumes.json
    /// marks them "rbox"; the builders make a plain cube and add this, which swaps in the rounded mesh
    /// whenever it's enabled (in the editor too). The mesh is made once from code and shared, so
    /// there's no model file, and the cube is still there if this script is ever removed.
    /// </summary>
    [ExecuteAlways]
    [RequireComponent(typeof(MeshFilter))]
    public class SoftBox : MonoBehaviour
    {
        /// <summary>How round the edges are, as a share of the box (0.5 would be a ball).</summary>
        public const float Radius = 0.22f;
        const int Steps = 6; // grid cells per face edge: enough for a smooth curve, still tiny

        /// <summary>True for a soft cylinder ("rcyl"): a collar, cuff, belt or sock with rounded rims.</summary>
        public bool Cylinder;

        static Mesh shared, sharedCyl;

        void OnEnable()
        {
            var mf = GetComponent<MeshFilter>();
            if (mf != null) mf.sharedMesh = Cylinder ? CylMesh : Mesh;
        }

        public static Mesh Mesh => shared != null ? shared : shared = Build(Radius);
        public static Mesh CylMesh => sharedCyl != null ? sharedCyl : sharedCyl = BuildCylinder(0.14f);

        /// <summary>
        /// The same size as Unity's cylinder (radius 0.5, from y -1 to 1), turned on a lathe from a
        /// profile with rounded rims: flat top, a quarter circle, the straight side, a quarter circle.
        /// </summary>
        static Mesh BuildCylinder(float r)
        {
            const int Around = 28, Arc = 5;
            var prof = new System.Collections.Generic.List<(Vector2 p, Vector2 n)>();
            prof.Add((new Vector2(0f, 1f), Vector2.up));
            for (int i = 0; i <= Arc; i++)
            {
                float a = Mathf.PI / 2f * (1f - i / (float)Arc); // top rim: from straight up to straight out
                var n = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                prof.Add((new Vector2(0.5f - r, 1f - r) + n * r, n));
            }
            for (int i = 0; i <= Arc; i++)
            {
                float a = -Mathf.PI / 2f * (i / (float)Arc); // bottom rim: from straight out to straight down
                var n = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                prof.Add((new Vector2(0.5f - r, -1f + r) + n * r, n));
            }
            prof.Add((new Vector2(0f, -1f), Vector2.down));
            int rows = prof.Count, cols = Around + 1;
            var verts = new Vector3[rows * cols];
            var normals = new Vector3[rows * cols];
            for (int j = 0; j < rows; j++)
                for (int i = 0; i < cols; i++)
                {
                    float t = i / (float)Around * Mathf.PI * 2f, c = Mathf.Cos(t), s = Mathf.Sin(t);
                    var (p, n) = prof[j];
                    verts[j * cols + i] = new Vector3(p.x * c, p.y, p.x * s);
                    normals[j * cols + i] = new Vector3(n.x * c, n.y, n.x * s).normalized;
                }
            var tris = new System.Collections.Generic.List<int>();
            for (int j = 0; j < rows - 1; j++)
                for (int i = 0; i < Around; i++)
                {
                    int k = j * cols + i;
                    tris.AddRange(new[] { k, k + 1, k + cols, k + 1, k + cols + 1, k + cols });
                }
            var mesh = new Mesh { name = "SoftCylinder", hideFlags = HideFlags.DontSave, vertices = verts, normals = normals, triangles = tris.ToArray() };
            mesh.RecalculateBounds();
            return mesh;
        }

        /// <summary>
        /// A unit cube whose faces are subdivided, then every vertex pulled in onto a rounded box:
        /// clamp it to the inner box, and push it out by the radius along the direction it came from.
        /// The normal is that same direction, so the shading is smooth all the way round.
        /// </summary>
        static Mesh Build(float r)
        {
            int per = (Steps + 1) * (Steps + 1);
            var verts = new Vector3[per * 6];
            var normals = new Vector3[per * 6];
            var uvs = new Vector2[per * 6];
            var tris = new int[Steps * Steps * 6 * 6];
            Vector3[] faceN = { Vector3.right, Vector3.left, Vector3.up, Vector3.down, Vector3.forward, Vector3.back };
            float inner = 0.5f - r;
            int t = 0;
            for (int f = 0; f < 6; f++)
            {
                var n = faceN[f];
                var a = new Vector3(n.y, n.z, n.x); // two axes across the face
                var b = Vector3.Cross(n, a);
                for (int j = 0; j <= Steps; j++)
                    for (int i = 0; i <= Steps; i++)
                    {
                        var p = n * 0.5f + a * (i / (float)Steps - 0.5f) + b * (j / (float)Steps - 0.5f);
                        var q = new Vector3(Mathf.Clamp(p.x, -inner, inner), Mathf.Clamp(p.y, -inner, inner), Mathf.Clamp(p.z, -inner, inner));
                        var d = p - q;
                        var dir = d.sqrMagnitude > 1e-8f ? d.normalized : n;
                        int k = f * per + j * (Steps + 1) + i;
                        verts[k] = q + dir * r;
                        normals[k] = dir;
                        uvs[k] = new Vector2(i / (float)Steps, j / (float)Steps);
                    }
                for (int j = 0; j < Steps; j++)
                    for (int i = 0; i < Steps; i++)
                    {
                        int k = f * per + j * (Steps + 1) + i;
                        tris[t++] = k; tris[t++] = k + Steps + 1; tris[t++] = k + 1;
                        tris[t++] = k + 1; tris[t++] = k + Steps + 1; tris[t++] = k + Steps + 2;
                    }
            }
            var mesh = new Mesh { name = "SoftBox", hideFlags = HideFlags.DontSave, vertices = verts, normals = normals, uv = uvs, triangles = tris };
            mesh.RecalculateBounds();
            // Make sure every triangle faces outwards whichever way the face axes turned out.
            var tr = mesh.triangles;
            for (int i = 0; i < tr.Length; i += 3)
            {
                var v0 = verts[tr[i]]; var v1 = verts[tr[i + 1]]; var v2 = verts[tr[i + 2]];
                if (Vector3.Dot(Vector3.Cross(v1 - v0, v2 - v0), v0 + v1 + v2) < 0f) (tr[i + 1], tr[i + 2]) = (tr[i + 2], tr[i + 1]);
            }
            mesh.triangles = tr;
            return mesh;
        }
    }
}
