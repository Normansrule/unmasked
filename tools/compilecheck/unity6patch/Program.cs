// Usage: Unity6Patch <srcDir> <outDir> <specFile>
// Copies every DLL from srcDir to outDir, then adds the members from specFile (bodies: `throw null`).
// Spec lines:  <Assembly.dll> <Namespace.Type> prop|sprop <ReturnType> <name> [get|getset]
//              <Assembly.dll> <Namespace.Type> method|smethod <ReturnType> <name> [<ParamType> <paramName>]...
// Types are full names (e.g. UnityEngine.Vector3, System.Single); arrays as T[].
using Mono.Cecil;
using Mono.Cecil.Cil;

var (src, dst, spec) = (args[0], args[1], args[2]);
Directory.CreateDirectory(dst);
foreach (var f in Directory.GetFiles(src, "*.dll")) File.Copy(f, Path.Combine(dst, Path.GetFileName(f)), true);

var resolver = new DefaultAssemblyResolver();
resolver.AddSearchDirectory(src);
var loaded = new Dictionary<string, AssemblyDefinition>();
AssemblyDefinition Load(string name) {
    if (!loaded.TryGetValue(name, out var a))
        loaded[name] = a = AssemblyDefinition.ReadAssembly(Path.Combine(src, name), new ReaderParameters { AssemblyResolver = resolver });
    return a;
}
TypeDefinition FindType(string full) {
    foreach (var f in Directory.GetFiles(src, "*.dll")) {
        var t = Load(Path.GetFileName(f)).MainModule.GetType(full);
        if (t != null) return t;
    }
    return null;
}
TypeReference Resolve(ModuleDefinition m, string name) {
    if (name.EndsWith("[]")) return new ArrayType(Resolve(m, name[..^2]));
    if (name == "void") return m.TypeSystem.Void;
    var sys = Type.GetType(name);
    if (sys != null && name.StartsWith("System.")) return m.ImportReference(sys);
    var t = m.GetType(name) ?? (TypeReference)FindType(name) ?? throw new Exception("type not found: " + name);
    return t.Module == m ? t : m.ImportReference(t);
}
MethodDefinition Stub(ModuleDefinition m, string name, TypeReference ret, MethodAttributes extra) {
    var md = new MethodDefinition(name, MethodAttributes.Public | MethodAttributes.HideBySig | extra, ret);
    var il = md.Body.GetILProcessor();
    il.Emit(OpCodes.Ldnull); il.Emit(OpCodes.Throw);
    return md;
}
var touched = new HashSet<string>();
int count = 0;
foreach (var raw in File.ReadAllLines(spec)) {
    var line = raw.Split('#')[0].Trim();
    if (line.Length == 0) continue;
    var p = line.Split((char[])null, StringSplitOptions.RemoveEmptyEntries);
    var asm = Load(p[0]); var m = asm.MainModule;
    var type = m.GetType(p[1]) ?? throw new Exception("type not found in " + p[0] + ": " + p[1]);
    var kind = p[2]; var ret = Resolve(m, p[3]); var name = p[4];
    bool isStatic = kind.StartsWith("s");
    var stat = isStatic ? MethodAttributes.Static : 0;
    if (kind.EndsWith("prop")) {
        if (type.Properties.Any(x => x.Name == name)) { Console.WriteLine($"  skip (exists) {p[1]}.{name}"); continue; }
        var prop = new PropertyDefinition(name, PropertyAttributes.None, ret);
        var get = Stub(m, "get_" + name, ret, MethodAttributes.SpecialName | stat);
        type.Methods.Add(get); prop.GetMethod = get;
        if (p.Length < 6 || p[5] == "getset") {
            var set = Stub(m, "set_" + name, m.TypeSystem.Void, MethodAttributes.SpecialName | stat);
            set.Parameters.Add(new ParameterDefinition("value", ParameterAttributes.None, ret));
            type.Methods.Add(set); prop.SetMethod = set;
        }
        if (!isStatic) { get.HasThis = true; if (prop.SetMethod != null) prop.SetMethod.HasThis = true; }
        type.Properties.Add(prop);
    } else {
        var md = Stub(m, name, ret, stat);
        for (int i = 5; i + 1 < p.Length; i += 2) md.Parameters.Add(new ParameterDefinition(p[i + 1], ParameterAttributes.None, Resolve(m, p[i])));
        type.Methods.Add(md);
    }
    touched.Add(p[0]); count++;
    Console.WriteLine($"  added {kind} {p[1]}.{name}");
}
foreach (var n in touched) loaded[n].Write(Path.Combine(dst, n));
Console.WriteLine($"Unity6Patch: {count} member(s) injected into {touched.Count} assembly(ies).");
