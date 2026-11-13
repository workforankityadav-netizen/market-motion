#!/usr/bin/env bash
# market-motion installer (macOS and Linux; on Windows use WSL).
#   From a clone:   ./install.sh
#   Options:        --no-deps   copy the skill only, skip installing tools
#                   --allow     also allow the pipeline's commands in Claude Code without permission prompts
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/skill/market-motion"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/market-motion"
DEPS=1; ALLOW=0
for a in "$@"; do
  case "$a" in
    --no-deps) DEPS=0 ;;
    --allow) ALLOW=1 ;;
    *) echo "unknown option: $a"; exit 2 ;;
  esac
done

[ -d "$SRC" ] || { echo "Run this from the market-motion repo folder (skill/market-motion not found)."; exit 1; }
command -v python3 >/dev/null || { echo "Python 3 is required. macOS: install Xcode command line tools or Homebrew python. Linux: apt install python3."; exit 1; }

echo "1/3  installing the skill to $DEST"
mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -R "$SRC" "$DEST"

if [ "$DEPS" = 1 ]; then
  echo "2/3  checking and installing tools (ffmpeg, Node.js, whisper.cpp, Whisper model, Hyperframes)"
  python3 "$DEST/engine/check_setup.py" --install
else
  echo "2/3  skipped tool install (--no-deps). Run later: python3 \"$DEST/engine/check_setup.py\" --install"
fi

if [ "$ALLOW" = 1 ]; then
  echo "3/3  allowing the pipeline's commands in ~/.claude/settings.json"
  python3 - "$DEST" <<'PY'
import json, os, sys
p = os.path.expanduser("~/.claude/settings.json")
s = json.load(open(p)) if os.path.exists(p) else {}
allow = s.setdefault("permissions", {}).setdefault("allow", [])
eng = sys.argv[1] + "/engine"
for rule in [f"Bash(python3 {eng}/mm.py:*)", f"Bash(python3 -I {eng}/mm.py:*)", "Bash(ffmpeg:*)", "Bash(ffprobe:*)",
             "Bash(npx --yes hyperframes@0.9.7:*)", "Bash(whisper-cli:*)"]:
    if rule not in allow:
        allow.append(rule)
os.makedirs(os.path.dirname(p), exist_ok=True)
json.dump(s, open(p, "w"), indent=2)
print("  added", len(allow), "allow rules")
PY
else
  echo "3/3  (optional) re-run with --allow to skip permission prompts for the pipeline's commands"
fi

echo
echo "Done. Open Claude Code in any folder, share a raw video (.mp4/.mov) or a voiceover (.mp3/.wav) and say:"
echo "  \"Edit this in market motion style\""
