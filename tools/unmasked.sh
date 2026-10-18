#!/usr/bin/env bash
# UNMASKED helper. Works from any directory once installed (`unmasked help`).
#
#   unmasked setup             install git, git-lfs, GitHub CLI, zip; add the `unmasked` command
#   unmasked publish [name]    first upload: create the GitHub repo (private) and push everything
#   unmasked save "message"    commit everything and push
#   unmasked status            progress: milestones, recent commits, last compile check
#   unmasked open              open the project in the Unity editor
#   unmasked check             compile the project headless and list any errors
#   unmasked world             rebuild the 3D manor (layout script + Unity scene) headless
#   unmasked build             build players into Builds/ and zip them
#   unmasked play [n]          launch the built game n times (default 1; 2 = host + friend)
#   unmasked secrets           give GitHub Actions your Unity license so it can build downloads
#   unmasked release v0.1.0    tag a version: GitHub builds it and publishes the downloads
#   unmasked install-unity     (native Ubuntu) install Unity Hub + the matching editor
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

find_unity() {
  if [[ -n "${UNITY_PATH:-}" ]]; then UNITY="$UNITY_PATH"; return; fi
  local candidates=(
    "$HOME/Unity/Hub/Editor/$UNITY_VERSION/Editor/Unity"
    "/opt/unity/Editor/Unity"
    "/mnt/c/Program Files/Unity/Hub/Editor/$UNITY_VERSION/Editor/Unity.exe"
  )
  for c in "${candidates[@]}"; do [[ -x "$c" || -f "$c" ]] && { UNITY="$c"; return; }; done
  # Any Unity 6 install will do.
  for c in "$HOME"/Unity/Hub/Editor/6000.*/Editor/Unity "/mnt/c/Program Files/Unity/Hub/Editor/"6000.*/Editor/Unity.exe; do
    [[ -f "$c" ]] && { UNITY="$c"; warn "Using $c (project wants $UNITY_VERSION)"; return; }
  done
  die "Unity $UNITY_VERSION not found. Install it with Unity Hub (Windows) or 'unmasked install-unity' (Ubuntu), or set UNITY_PATH=/path/to/Unity."
}

# Run Unity headless; keeps the log in Logs/<name>.log and streams the interesting lines.
unity_batch() {
  local name="$1"; shift
  find_unity
  mkdir -p Logs
  local log="$PROJECT_DIR/Logs/$name.log"
  bold "Running Unity headless ($name). The first run imports packages and can take a while..."
  set +e
  "$UNITY" -batchmode -nographics -quit -projectPath "$(native_path "$PROJECT_DIR")" -logFile "$(native_path "$log")" "$@"
  local code=$?
  set -e
  grep -E "error CS|warning CS|\[Unmasked\]|Build (succeeded|failed)|Exiting batchmode" "$log" | sort -u | tail -n 60 || true
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
  echo "Next: 'unmasked secrets' so GitHub can build downloadable versions."
}

cmd_save() {
  [[ -d .git ]] || die "No repo yet. Run 'unmasked publish' first."
  ensure_git_identity
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
  bold "Opening the project in Unity $UNITY_VERSION..."
  if $IS_WSL && [[ "$UNITY" == *.exe ]]; then
    ("$UNITY" -projectPath "$(native_path "$PROJECT_DIR")" >/dev/null 2>&1 &)
  else
    nohup "$UNITY" -projectPath "$PROJECT_DIR" >/dev/null 2>&1 &
  fi
  ok "Unity is starting. In it: Unmasked > Build Hollow Creek (town), then press Play and click Host. (Blackwood Manor on its own: Unmasked > Build Blackwood Manor.)"
}

cmd_check() {
  if unity_batch check; then :; fi
  local errors; errors=$(grep -c "error CS" Logs/check.log || true)
  if [[ "$errors" == 0 ]]; then ok "Compiles cleanly."; else warn "$errors compile error(s). Full log: Logs/check.log"; return 1; fi
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
  unity_batch build -executeMethod Unmasked.EditorTools.BuildScript.BuildAll || die "Build failed. See Logs/build.log"
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

cmd_help() { sed -n '2,17p' "$SCRIPT_PATH" | sed 's/^# \{0,1\}//'; }

case "${1:-help}" in
  setup) cmd_setup ;;
  publish) shift; cmd_publish "$@" ;;
  save) shift; cmd_save "$@" ;;
  status|progress) cmd_status ;;
  open) cmd_open ;;
  check) cmd_check ;;
  world|room) cmd_world ;;
  build) cmd_build ;;
  play) shift; cmd_play "$@" ;;
  secrets) cmd_secrets ;;
  release) shift; cmd_release "$@" ;;
  install-unity) cmd_install_unity ;;
  where) echo "$PROJECT_DIR" ;;
  *) cmd_help ;;
esac
