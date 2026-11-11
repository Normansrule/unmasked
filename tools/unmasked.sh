#!/usr/bin/env bash
# UNMASKED helper. Works from any directory once installed (`unmasked help`).
#
#   unmasked setup             install git, git-lfs, GitHub CLI, zip; add the `unmasked` command
#   unmasked publish [name]    first upload: create the GitHub repo (private) and push everything
#   unmasked save "message"    commit everything and push
#   unmasked status            progress: milestones, recent commits, last compile check
#   unmasked site              preview the website (site/) at http://localhost:8000
#   unmasked pages             turn on GitHub Pages so the website goes live
#   unmasked open              open the project in the Unity editor
#   unmasked check             compile the project headless and list any errors
#   unmasked smoke             play one whole night headless by itself and report where it breaks
#   unmasked world             rebuild the 3D manor (layout script + Unity scene) headless
#   unmasked build             build players into Builds/ and zip them
#   unmasked play [n]          launch the built game n times (default 1; 2 = host + friend)
#   unmasked secrets           give GitHub Actions your Unity license so it can build downloads
#   unmasked release v0.1.0    tag a version: GitHub builds it and publishes the downloads
#   unmasked install-unity     (native Ubuntu) install Unity Hub + the matching editor
#   unmasked doctor            check git, WSL, Unity version; print the fix for anything missing
#   unmasked import [--apply]  bring CC0 models and sounds from Incoming/ into the game (shows the plan first)
#   unmasked where             print the project folder
set -euo pipefail

# ---------------------------------------------------------------------------
# Where things are
# ---------------------------------------------------------------------------
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
PROJECT_DIR="${UNMASKED_DIR:-$(dirname "$(dirname "$SCRIPT_PATH")")}"
cd "$PROJECT_DIR"

IS_WSL=false
grep -qi microsoft /proc/version 2>/dev/null && IS_WSL=true

UNITY_VERSION="$(sed -n 's/^m_EditorVersion: //p' ProjectSettings/ProjectVersion.txt)"
UNITY_CHANGESET="$(sed -n 's/^m_EditorVersionWithRevision: .*(\(.*\))/\1/p' ProjectSettings/ProjectVersion.txt)"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '\033[32m✔\033[0m %s\n' "$*"; }
warn() { printf '\033[33m!\033[0m %s\n' "$*"; }
repeat() { local i; for ((i = 0; i < $2; i++)); do printf '%s' "$1"; done; }
die()  { printf '\033[31m✘\033[0m %s\n' "$*" >&2; exit 1; }

# Paths handed to a Windows Unity.exe must be Windows paths.
native_path() { if $IS_WSL && [[ "${UNITY:-}" == *.exe ]]; then wslpath -w "$1"; else echo "$1"; fi; }

# ---------------------------------------------------------------------------
# WSL: Windows programs (Unity.exe, the built game) only start from Ubuntu when WSL "interop"
# is registered. Ubuntu's systemd-binfmt sometimes wipes that registration, and then every .exe
# fails with "cannot execute binary file: Exec format error".
# ---------------------------------------------------------------------------
INTEROP_LINE=':WSLInterop:M::MZ::/init:PF'

interop_ok() {
  [[ -e /proc/sys/fs/binfmt_misc/WSLInterop || -e /proc/sys/fs/binfmt_misc/WSLInterop-late ]] && return 0
  # Some WSL versions register it under another name: just try a harmless Windows command.
  command -v cmd.exe >/dev/null 2>&1 && timeout 15 cmd.exe /c ver >/dev/null 2>&1
}

interop_fix_text() {
  cat <<EOF
  Fix (once, in Ubuntu):
    sudo sh -c 'echo $INTEROP_LINE > /usr/lib/binfmt.d/WSLInterop.conf'
    sudo sh -c 'echo $INTEROP_LINE > /proc/sys/fs/binfmt_misc/register'
  If it still fails, restart WSL from Windows PowerShell:   wsl --shutdown
  and check /etc/wsl.conf doesn't contain  [interop] enabled=false
EOF
}

# Make sure Windows programs can run; offer to repair it, otherwise explain exactly how.
ensure_interop() {
  $IS_WSL || return 0
  interop_ok && return 0
  warn "WSL can't start Windows programs right now (that's the 'Exec format error')."
  if grep -qiE '^[[:space:]]*enabled[[:space:]]*=[[:space:]]*false' /etc/wsl.conf 2>/dev/null; then
    warn "/etc/wsl.conf switches interop off. Remove 'enabled=false' under [interop], then run 'wsl --shutdown' in Windows PowerShell."
  fi
  local answer=n
  if [[ -t 0 ]]; then read -rp "Fix it now? It needs sudo. [Y/n] " answer || answer=n; answer="${answer:-y}"; fi
  if [[ "$answer" =~ ^[Yy] ]]; then
    mountpoint -q /proc/sys/fs/binfmt_misc 2>/dev/null || sudo mount -t binfmt_misc binfmt_misc /proc/sys/fs/binfmt_misc || true
    # Persist it so systemd-binfmt puts it back on every boot, then register it for this session.
    sudo mkdir -p /usr/lib/binfmt.d && sudo sh -c "echo '$INTEROP_LINE' > /usr/lib/binfmt.d/WSLInterop.conf" || true
    [[ -e /proc/sys/fs/binfmt_misc/WSLInterop ]] || sudo sh -c "echo '$INTEROP_LINE' > /proc/sys/fs/binfmt_misc/register" || true
    if interop_ok; then ok "Fixed: Ubuntu can start Windows programs again (and will after restarts)."; return 0; fi
    warn "That didn't take yet."
  fi
  interop_fix_text >&2
  die "Unity didn't start. Run the fix above, then try again."
}

# ---------------------------------------------------------------------------
# Finding Unity. Best: exactly the version in ProjectSettings/ProjectVersion.txt. Next best: any
# 6000.0.x (same Unity 6.0 line, patch updates are safe). A newer Unity 6 (6000.1+) also works but
# upgrades the project files the first time it opens them, so we ask first.
# ---------------------------------------------------------------------------
UNITY_HUB_LINK="unityhub://$UNITY_VERSION/$UNITY_CHANGESET"

unity_installs() {
  local c
  for c in "$HOME"/Unity/Hub/Editor/6000.*/Editor/Unity "/mnt/c/Program Files/Unity/Hub/Editor/"6000.*/Editor/Unity.exe; do
    [[ -f "$c" ]] && echo "$c"
  done
}

editor_version() { local d; d="$(dirname "$(dirname "$1")")"; basename "$d"; }

install_hint() {
  echo "  Install Unity $UNITY_VERSION next to it: open this link (Windows: paste it into the Start menu's Run box, Win+R):"
  echo "    $UNITY_HUB_LINK"
  echo "  or in Unity Hub: Installs > Install Editor > Archive > download archive, pick $UNITY_VERSION."
  $IS_WSL || echo "  On Ubuntu: unmasked install-unity"
}

find_unity() {
  if [[ -n "${UNITY_PATH:-}" ]]; then UNITY="$UNITY_PATH"; return; fi
  local all=() c v
  mapfile -t all < <(unity_installs)
  for c in "${all[@]}"; do [[ "$(editor_version "$c")" == "$UNITY_VERSION" ]] && { UNITY="$c"; return; }; done
  # Same 6000.0 line: newest patch first.
  local same; same="$(for c in "${all[@]}"; do v="$(editor_version "$c")"; [[ "$v" == 6000.0.* ]] && echo "$v|$c"; done | sort -t'|' -k1,1V | tail -n1 | cut -d'|' -f2-)"
  if [[ -n "$same" ]]; then UNITY="$same"; warn "Using Unity $(editor_version "$same") (project made with $UNITY_VERSION; same 6.0 line, that's fine)."; return; fi
  # A newer Unity 6: works, but opening the project upgrades it.
  local newer; newer="$(for c in "${all[@]}"; do v="$(editor_version "$c")"; echo "$v|$c"; done | sort -t'|' -k1,1V | tail -n1 | cut -d'|' -f2-)"
  if [[ -n "$newer" ]]; then
    UNITY="$newer"
    local nv; nv="$(editor_version "$newer")"
    warn "Only Unity $nv is installed; this project is made with $UNITY_VERSION."
    if [[ "${UNMASKED_ALLOW_UPGRADE:-}" != 1 ]]; then
      echo "  Unity $nv will upgrade the project the first time it opens it (one-way, but git keeps the old files)."
      install_hint
      local answer=n
      if [[ -t 0 ]]; then read -rp "Use Unity $nv anyway and upgrade the project? [y/N] " answer || answer=n; fi
      [[ "$answer" =~ ^[Yy] ]] || die "Stopped. Install $UNITY_VERSION (above), or run with UNMASKED_ALLOW_UPGRADE=1 to use $nv."
    fi
    return
  fi
  if [[ -x /opt/unity/Editor/Unity ]]; then UNITY=/opt/unity/Editor/Unity; warn "Using /opt/unity (version unknown; project wants $UNITY_VERSION)."; return; fi
  echo "  No Unity 6 found in ~/Unity/Hub/Editor, /opt/unity or C:\\Program Files\\Unity\\Hub\\Editor." >&2
  install_hint >&2
  die "Unity $UNITY_VERSION not found. (Installed somewhere else? Set UNITY_PATH=/path/to/Unity or Unity.exe)"
}

# Start a Unity (or any) program, checking first that it can actually run here.
can_launch() {
  local exe="$1"
  [[ -f "$exe" ]] || die "Not found: $exe"
  if $IS_WSL && [[ "$exe" == *.exe || "$exe" == *.EXE ]]; then ensure_interop; fi
}

# Run Unity headless; keeps the log in Logs/<name>.log and streams the interesting lines.
LAST_LOG=""
unity_batch() {
  local name="$1"; shift
  find_unity
  can_launch "$UNITY"
  mkdir -p Logs
  local log="$PROJECT_DIR/Logs/$name.log"
  LAST_LOG="$log"
  rm -f "$log"
  bold "Running Unity $(editor_version "$UNITY") headless ($name). The first run imports packages and can take a while..."
  set +e
  "$UNITY" -batchmode -nographics -quit -projectPath "$(native_path "$PROJECT_DIR")" -logFile "$(native_path "$log")" "$@"
  local code=$?
  set -e
  if [[ ! -f "$log" ]]; then
    warn "Unity didn't start (exit $code), so there's no log. Run 'unmasked doctor' to see why."
    return 2
  fi
  grep -E "error CS|warning CS|\[Unmasked\]|Build (succeeded|failed)|Exiting batchmode|[Ll]icense" "$log" | sort -u | tail -n 60 || true
  [[ $code == 0 ]] || warn "Unity exited with code $code. Full log: $log"
  return $code
}

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
cmd_setup() {
  bold "Installing git, git-lfs, zip, curl and the GitHub CLI (needs sudo)"
  sudo apt-get update -y
  sudo apt-get install -y git git-lfs zip unzip curl ca-certificates
  if ! command -v gh >/dev/null; then
    sudo mkdir -p -m 755 /etc/apt/keyrings
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
    sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
    sudo apt-get update -y && sudo apt-get install -y gh
  fi
  git lfs install --skip-repo
  # Windows folders seen from WSL need these or git complains about ownership and file modes.
  git config --global --add safe.directory "$PROJECT_DIR" || true
  git config --global init.defaultBranch main

  mkdir -p "$HOME/.local/bin"
  ln -sf "$SCRIPT_PATH" "$HOME/.local/bin/unmasked"
  chmod +x "$SCRIPT_PATH" 2>/dev/null || true
  grep -q '.local/bin' "$HOME/.bashrc" 2>/dev/null || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
  ok "Done. Open a new terminal (or run: source ~/.bashrc) and type: unmasked help"
}

ensure_git_identity() {
  git config user.name >/dev/null || git config --global user.name "$(gh api user -q .login 2>/dev/null || echo "$USER")"
  git config user.email >/dev/null || git config --global user.email "$(gh api user -q .id 2>/dev/null || echo 0)+$(gh api user -q .login 2>/dev/null || echo "$USER")@users.noreply.github.com"
}

cmd_publish() {
  local name="${1:-unmasked}" visibility="--private"
  [[ "${2:-}" == "--public" ]] && visibility="--public"
  command -v gh >/dev/null || die "Run 'unmasked setup' first."
  gh auth status >/dev/null 2>&1 || { bold "Log in to GitHub (pick GitHub.com, HTTPS, browser):"; gh auth login --git-protocol https --web; }
  gh auth setup-git

  if [[ ! -d .git ]]; then git init -b main; fi
  $IS_WSL && git config core.fileMode false
  git config core.autocrlf input
  git lfs install
  ensure_git_identity
  git add -A
  git commit -m "UNMASKED: initial upload" || true

  if git remote get-url origin >/dev/null 2>&1; then
    git push -u origin main
  else
    gh repo create "$name" $visibility --source . --remote origin --push \
      --description "Asymmetric 'meddling kids' mystery game made in Unity"
  fi
  ok "Uploaded: $(gh repo view --json url -q .url)"
  cmd_pages || true
  echo "Next: 'unmasked secrets' so GitHub can build downloadable versions."
}

# The website is plain files in site/, deployed by .github/workflows/pages.yml.
cmd_pages() {
  command -v gh >/dev/null || die "Run 'unmasked setup' first."
  local repo; repo="$(gh repo view --json nameWithOwner -q .nameWithOwner)" || die "No GitHub repo yet. Run 'unmasked publish' first."
  if gh api "repos/$repo/pages" >/dev/null 2>&1 || gh api -X POST "repos/$repo/pages" -f build_type=workflow >/dev/null 2>&1; then
    gh workflow run pages.yml >/dev/null 2>&1 || true
    ok "Website: https://${repo%%/*}.github.io/${repo#*/}/ (live a minute or two after the Website workflow finishes)"
  else
    warn "GitHub Pages couldn't be turned on. On a free account the repo has to be public: 'gh repo edit --visibility public --accept-visibility-change-consequences', then 'unmasked pages' again."
    return 1
  fi
}

cmd_site() {
  command -v python3 >/dev/null || die "The preview needs python3 (sudo apt install python3)."
  python3 Docs/tools/make_site_data.py
  bold "Website preview: http://localhost:8000  (Ctrl+C to stop)"
  python3 -m http.server 8000 --bind 127.0.0.1 --directory site
}

cmd_save() {
  [[ -d .git ]] || die "No repo yet. Run 'unmasked publish' first."
  ensure_git_identity
  # Python caches got committed once (round 37); .gitignore skips them now, this untracks the old ones.
  git rm -r -q --cached --ignore-unmatch Docs/tools/__pycache__ >/dev/null 2>&1 || true
  git add -A
  git commit -m "${1:-Update UNMASKED}" || warn "Nothing new to commit."
  git push
  ok "Pushed."
}

cmd_status() {
  bold "UNMASKED  ($PROJECT_DIR)"
  echo
  bold "Milestones"
  sed -n '/<!-- progress:start -->/,/<!-- progress:end -->/p' Docs/PROGRESS.md | grep -E '^\s*- \[' || true
  local done total
  done=$(grep -cE '^\s*- \[x\]' Docs/PROGRESS.md || true); total=$(grep -cE '^\s*- \[[ x]\]' Docs/PROGRESS.md || true)
  local width=30 filled=$(( total > 0 ? done * 30 / total : 0 ))
  printf '\nOverall  [%s%s] %d/%d tasks\n\n' "$(repeat '#' "$filled")" "$(repeat '-' $((width - filled)))" "$done" "$total"

  bold "Code"
  printf '  %s C# scripts, %s lines\n' "$(find Assets -name '*.cs' | wc -l)" "$(find Assets -name '*.cs' -exec cat {} + | wc -l)"
  if [[ -f Logs/check.log ]]; then
    local errors; errors=$(grep -c "error CS" Logs/check.log || true)
    if [[ "$errors" == 0 ]]; then ok "Last compile check: clean ($(date -r Logs/check.log '+%F %H:%M'))"
    else warn "Last compile check: $errors error(s). Run 'unmasked check' to see them."; fi
  else
    warn "Never compile-checked here. Run 'unmasked check'."
  fi
  [[ -d Builds ]] && printf '  Builds: %s\n' "$(ls Builds 2>/dev/null | tr '\n' ' ')"
  local shots; shots=$(ls Docs/screenshots/*.png 2>/dev/null | wc -l || true)
  printf '  Screenshots (F12 in game): %s\n\n' "$shots"

  if [[ -d .git ]]; then
    bold "Recent commits"
    git --no-pager log --oneline -n 8 || true
    git remote get-url origin >/dev/null 2>&1 && command -v gh >/dev/null && {
      echo; bold "Cloud builds"; gh run list --limit 3 2>/dev/null || true; }
  else
    warn "Not on GitHub yet. Run 'unmasked publish'."
  fi
}

cmd_open() {
  find_unity
  can_launch "$UNITY"
  bold "Opening the project in Unity $(editor_version "$UNITY")..."
  if $IS_WSL && [[ "$UNITY" == *.exe ]]; then
    ("$UNITY" -projectPath "$(native_path "$PROJECT_DIR")" >/dev/null 2>&1 &)
  else
    nohup "$UNITY" -projectPath "$PROJECT_DIR" >/dev/null 2>&1 &
  fi
  ok "Unity is starting. In it: Unmasked > Build Hollow Creek (town), then press Play and click Host. (Blackwood Manor on its own: Unmasked > Build Blackwood Manor.)"
}

cmd_check() {
  local code=0
  unity_batch check || code=$?
  [[ $code == 2 ]] && die "Compile check didn't run."
  local errors; errors=$(grep -c "error CS" Logs/check.log || true)
  if [[ "$errors" == 0 ]]; then ok "Compiles cleanly."; else warn "$errors compile error(s). Full log: Logs/check.log"; return 1; fi
}

cmd_smoke() {
  # No -quit: Unity has to stay open in play mode until SmokeTest finishes and exits with 0 (pass) or 1.
  find_unity
  can_launch "$UNITY"
  mkdir -p Logs
  local log="$PROJECT_DIR/Logs/smoke.log"
  rm -f "$log"
  rm -f Logs/smoke-test.txt
  bold "Playing one night headless (builds the town first if needed). This can take a few minutes..."
  set +e
  timeout 900 "$UNITY" -batchmode -nographics -projectPath "$(native_path "$PROJECT_DIR")" -logFile "$(native_path "$log")" \
    -executeMethod Unmasked.EditorTools.SelfTest.RunBatch
  local code=$?
  set -e
  if [[ ! -f "$log" ]]; then die "Unity didn't start (exit $code), so there's no log. Run 'unmasked doctor'."; fi
  if [[ -f Logs/smoke-test.txt ]]; then cat Logs/smoke-test.txt
  else grep -E "error CS|\[Unmasked\]|Exception" "$log" | tail -n 30 || true; fi
  if [[ $code == 0 ]]; then ok "Smoke test passed."
  elif [[ $code == 124 ]]; then warn "Unity didn't finish within 15 minutes. Full log: Logs/smoke.log"; return 1
  else warn "Smoke test failed (exit $code). Full log: Logs/smoke.log"; return 1; fi
}

cmd_world() {
  # Everything in the world is generated from small Python scripts (no Unity needed for those):
  #   Docs/tools/make_textures.py -> Textures/Surfaces/*.png      siding, shingles, brick, stone, grass... patterns
  #   Docs/tools/make_sounds.py   -> Resources/Sounds/*.wav       wind, crows, wails, hoofbeats, thunder, the van...
  #   Docs/tools/make_costumes.py -> Resources/Costumes.json      characters, villains, Halloween and town props
  #   Docs/tools/make_manor.py    -> Resources/BlackwoodManor.json the big manor
  #   Docs/tools/make_houses.py   -> Resources/Houses/*.json       the cottage, the farm and the Victorian
  #   Docs/tools/make_town.py     -> Resources/HollowCreek.json    the town, HQ, roads and house lots
  if command -v python3 >/dev/null; then
    python3 Docs/tools/make_textures.py && python3 Docs/tools/make_sounds.py && python3 Docs/tools/make_costumes.py && python3 Docs/tools/make_manor.py && \
      python3 Docs/tools/make_houses.py && python3 Docs/tools/make_town.py || die "A world script failed (see above)."
  fi
  unity_batch world -executeMethod Unmasked.EditorTools.ManorBuilder.Build && ok "Blackwood Manor rebuilt (Assets/Unmasked/Scenes/BlackwoodManor.unity)."
  unity_batch town -executeMethod Unmasked.EditorTools.TownBuilder.Build && ok "Hollow Creek rebuilt (Assets/Unmasked/Scenes/HollowCreek.unity)."
}

cmd_build() {
  local code=0
  unity_batch build -executeMethod Unmasked.EditorTools.BuildScript.BuildAll || code=$?
  if [[ $code == 2 ]]; then die "Build didn't run: Unity never started."; fi
  if [[ $code != 0 ]]; then die "Build failed. Full log: $LAST_LOG"; fi
  ls -d Builds/*/ >/dev/null 2>&1 || die "Unity finished but made no builds. Full log: $LAST_LOG"
  for d in Builds/*/; do
    local n; n=$(basename "$d")
    (cd "$d" && zip -qr "../Unmasked-$n.zip" .) && ok "Builds/Unmasked-$n.zip"
  done
}

cmd_play() {
  local n="${1:-1}" exe=""
  if $IS_WSL && [[ -f Builds/Windows/Unmasked.exe ]]; then exe="Builds/Windows/Unmasked.exe"
  elif [[ -f Builds/Linux/Unmasked.x86_64 ]]; then exe="Builds/Linux/Unmasked.x86_64"; chmod +x "$exe"
  else die "No build yet. Run 'unmasked build' first."; fi
  can_launch "$exe"
  for _ in $(seq 1 "$n"); do ("./$exe" -screen-fullscreen 0 -screen-width 1280 -screen-height 720 >/dev/null 2>&1 &); sleep 1; done
  ok "Launched $n window(s). Click Host in one and Join (127.0.0.1) in the others."
}

cmd_secrets() {
  command -v gh >/dev/null || die "Run 'unmasked setup' first."
  local lic=""
  for c in "$HOME/.local/share/unity3d/Unity/Unity_lic.ulf" "/mnt/c/ProgramData/Unity/Unity_lic.ulf"; do [[ -f "$c" ]] && lic="$c"; done
  [[ -n "$lic" ]] || die "No Unity license file found. Sign in to Unity Hub once and activate a Personal license, then retry."
  gh secret set UNITY_LICENSE < "$lic"
  read -rp "Unity account email: " email; gh secret set UNITY_EMAIL --body "$email"
  read -rsp "Unity account password (stored as an encrypted GitHub secret): " pass; echo; gh secret set UNITY_PASSWORD --body "$pass"
  ok "Secrets saved. The next push builds Windows, macOS and Linux versions (Actions tab)."
}

cmd_release() {
  local tag="${1:?Usage: unmasked release v0.1.0}"
  git tag -a "$tag" -m "UNMASKED $tag" && git push origin "$tag"
  ok "Tagged $tag. When the cloud build finishes, downloads appear at: $(gh repo view --json url -q .url 2>/dev/null)/releases/latest"
}

cmd_install_unity() {
  $IS_WSL && die "You're in WSL: install Unity Hub on Windows (https://unity.com/download) and add Unity $UNITY_VERSION there."
  if ! command -v unityhub >/dev/null; then
    wget -qO - https://hub.unity3d.com/linux/keys/public | gpg --dearmor | sudo tee /usr/share/keyrings/Unity_Technologies_ApS.gpg >/dev/null
    echo "deb [signed-by=/usr/share/keyrings/Unity_Technologies_ApS.gpg] https://hub.unity3d.com/linux/repos/deb stable main" \
      | sudo tee /etc/apt/sources.list.d/unityhub.list >/dev/null
    sudo apt-get update -y && sudo apt-get install -y unityhub
  fi
  unityhub --headless install --version "$UNITY_VERSION" --changeset "$UNITY_CHANGESET" \
    --module windows-mono --module mac-mono || warn "If that failed, open Unity Hub, sign in, and install $UNITY_VERSION from Installs."
  ok "Unity $UNITY_VERSION installed. Run: unmasked open"
}

# Everything the other commands need, checked in one go.
cmd_doctor() {
  bold "UNMASKED doctor  ($PROJECT_DIR)"
  local c
  for c in git git-lfs gh python3 zip; do
    if command -v "$c" >/dev/null 2>&1; then ok "$c"; else warn "$c missing (run: unmasked setup)"; fi
  done
  if $IS_WSL; then
    if interop_ok; then ok "WSL can start Windows programs"
    else warn "WSL can't start Windows programs (Exec format error)"; interop_fix_text; fi
  fi
  echo "Project wants Unity $UNITY_VERSION ($UNITY_CHANGESET)"
  local found=0
  while read -r c; do [[ -n "$c" ]] && { found=1; echo "  found $(editor_version "$c"): $c"; }; done < <(unity_installs)
  [[ -n "${UNITY_PATH:-}" ]] && echo "  UNITY_PATH=$UNITY_PATH"
  if [[ $found == 0 && -z "${UNITY_PATH:-}" ]]; then warn "No Unity 6 found."; install_hint
  elif [[ "$(unity_installs)" != *"/$UNITY_VERSION/"* ]]; then warn "Not the exact version."; install_hint
  else ok "Unity $UNITY_VERSION installed"; fi
  [[ -f Logs/build.log ]] && echo "Last build log: $PROJECT_DIR/Logs/build.log ($(date -r Logs/build.log '+%F %H:%M'))"
  return 0
}

cmd_help() { sed -n '2,20p' "$SCRIPT_PATH" | sed 's/^# \{0,1\}//'; }

case "${1:-help}" in
  setup) cmd_setup ;;
  publish) shift; cmd_publish "$@" ;;
  save) shift; cmd_save "$@" ;;
  status|progress) cmd_status ;;
  site) cmd_site ;;
  pages) cmd_pages ;;
  open) cmd_open ;;
  check) cmd_check ;;
  smoke|test) cmd_smoke ;;
  world|room) cmd_world ;;
  build) cmd_build ;;
  play) shift; cmd_play "$@" ;;
  secrets) cmd_secrets ;;
  release) shift; cmd_release "$@" ;;
  install-unity) cmd_install_unity ;;
  where) echo "$PROJECT_DIR" ;;
  doctor) cmd_doctor ;;
  import) shift; mkdir -p "$PROJECT_DIR/Incoming"; python3 "$PROJECT_DIR/tools/import_incoming.py" "$@" ;;
  *) cmd_help ;;
esac
