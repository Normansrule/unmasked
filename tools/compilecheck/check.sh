#!/usr/bin/env bash
# Offline compile check for the Unmasked Unity project (no Unity install needed).
#   tools/compilecheck/check.sh            -> builds Runtime (Assembly-CSharp) and Editor (Assembly-CSharp-Editor)
# Env: CC_DEPS (default /tmp/cc/deps) where Unity reference DLLs are cached, CC_OUT (default /tmp/cc/artifacts) for bin/obj.
# Needs: dotnet SDK 8 (apt-get install -y dotnet-sdk-8.0) and, the first time, HTTPS access to api.nuget.org.
# Exit code: 0 = no errors, 1 = compile errors, 2 = setup problem.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SCRIPTS="$(cd "$HERE/../../Assets/Unmasked/Scripts" && pwd -P)"
DEPS="${CC_DEPS:-/tmp/cc/deps}"; export CC_DEPS="$DEPS"
export CC_OUT="${CC_OUT:-/tmp/cc/artifacts}"
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1

command -v dotnet >/dev/null || { echo "dotnet not found: apt-get install -y dotnet-sdk-8.0"; exit 2; }

fetch() { # id version
  local id="$1" ver="$2" dir="$DEPS/$1.$2"
  [ -d "$dir/lib" ] && return 0
  mkdir -p "$dir"
  echo "Downloading $id $ver from nuget.org ..."
  curl -fsSL "https://api.nuget.org/v3-flatcontainer/$id/$ver/$id.$ver.nupkg" -o "$dir.nupkg" || { echo "download failed: $id $ver"; exit 2; }
  (cd "$dir" && unzip -qo "$dir.nupkg") && rm -f "$dir.nupkg"
}
# Newest UnityEngine reference assemblies on nuget.org (2021.3.33 modules) + newest UnityEditor.dll (2021.1.14).
fetch unityengine.modules 2021.3.33
fetch unity3d.sdk 2021.1.14.1
fetch mono.cecil 0.11.5

# Inject Unity 6 members missing from the 2021.3 DLLs (re-done when unity6-members.txt or the patcher changes).
STAMP="$DEPS/patched/.stamp"
if [ ! -f "$STAMP" ] || [ "$HERE/unity6-members.txt" -nt "$STAMP" ] || [ "$HERE/unity6patch/Program.cs" -nt "$STAMP" ]; then
  rm -rf "$DEPS/patched"
  dotnet run --project "$HERE/unity6patch/Unity6Patch.csproj" -v:q -- "$DEPS/unityengine.modules.2021.3.33/lib/netstandard2.0" "$DEPS/patched" "$HERE/unity6-members.txt" || { echo "unity6patch failed"; exit 2; }
  touch "$STAMP"
fi

LOG="$CC_OUT/logs"; mkdir -p "$LOG"
build() { # project extra-args...
  local proj="$1"; shift
  dotnet build "$HERE/$proj" -nologo -v:q -clp:NoSummary -p:WarningLevel=4 "$@" > "$LOG/${proj%.csproj}.log" 2>&1
  local rc=$?
  # one line per diagnostic, deduplicated, paths made relative to the scripts folder
  grep -E ': (error|warning) [A-Z]+[0-9]+' "$LOG/${proj%.csproj}.log" | sed -E "s# \[[^]]*\.csproj\]\$##; s#^$SCRIPTS/##; s#^$HERE/#tools/compilecheck/#" | sort -u > "$LOG/${proj%.csproj}.diag"
  return $rc
}

build Runtime.csproj; RT=$?
if [ $RT -eq 0 ]; then build Editor.csproj; ED=$?
else
  build Editor.csproj -p:CcStandalone=true; ED=$?
  # runtime errors were already reported by the Runtime build; keep only Editor/ diagnostics
  grep -E '^Editor/|^tools/compilecheck/stubs/editor/' "$LOG/Editor.diag" > "$LOG/Editor.diag.tmp"; mv "$LOG/Editor.diag.tmp" "$LOG/Editor.diag"
  [ -s "$LOG/Editor.diag" ] && grep -q ': error ' "$LOG/Editor.diag" || ED=0
fi

# NGO's IL post-processor (not run here) rejects [Rpc]/[ServerRpc]/[ClientRpc] methods whose name doesn't end in "Rpc"/"ServerRpc"/"ClientRpc".
python3 -I - "$SCRIPTS" > "$LOG/rpcnames.diag" <<'PY'
import re, sys, pathlib
root = pathlib.Path(sys.argv[1])
for f in sorted(root.rglob('*.cs')):
    lines = f.read_text(encoding='utf-8', errors='replace').split('\n')
    for i, l in enumerate(lines):
        m = re.search(r'\[(Rpc|ServerRpc|ClientRpc)\b', l)
        if not m: continue
        for j in range(i + 1, min(i + 6, len(lines))):
            d = re.search(r'\b(\w+)\s*\(', lines[j])
            if d and not lines[j].strip().startswith('['):
                name = d.group(1); kind = m.group(1)
                suffix = {'Rpc': 'Rpc', 'ServerRpc': 'ServerRpc', 'ClientRpc': 'ClientRpc'}[kind]
                if not name.endswith(suffix):
                    print(f"{f.relative_to(root)}({j+1},1): error NGO-RPC: [{kind}] method '{name}' must end with '{suffix}'")
                if re.search(r'\bstatic\b', lines[j]):
                    print(f"{f.relative_to(root)}({j+1},1): error NGO-RPC: [{kind}] method '{name}' cannot be static")
                break
PY
RPC=0; [ -s "$LOG/rpcnames.diag" ] && RPC=1

for p in Runtime Editor; do
  e=$(grep -c ': error ' "$LOG/$p.diag" || true); w=$(grep -c ': warning ' "$LOG/$p.diag" || true)
  echo "== $p: $e error(s), $w warning(s)   (full log: $LOG/$p.log)"
  grep ': error ' "$LOG/$p.diag"
  [ "${CC_WARNINGS:-0}" = 1 ] && grep ': warning ' "$LOG/$p.diag"
done
echo "== NGO RPC naming check: $(wc -l < "$LOG/rpcnames.diag") problem(s)"; cat "$LOG/rpcnames.diag"
if [ $RT -ne 0 ] && ! grep -q ': error ' "$LOG/Runtime.diag"; then echo "Runtime build failed without compiler errors, see $LOG/Runtime.log"; exit 2; fi
[ $RT -eq 0 ] && [ $ED -eq 0 ] && [ $RPC -eq 0 ] && exit 0 || exit 1
