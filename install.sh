#!/usr/bin/env bash
# install.sh: set up namegen and link it into place (idempotent, never deletes).
#   - Python env (uv), Node deps (npm), NLTK data (WordNet, CMUdict, POS tagger) into data/nltk
#   - ~/.local/bin/namegen        -> bin/namegen
#   - <skills dir>/namegen        -> skill/namegen
#     an existing file or a link pointing elsewhere is moved to <config dir>/skill-backups first
#     (outside the skills dir, or Claude Code would load the backup as a duplicate skill)
# Usage: ./install.sh
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SKILLS="${CLAUDE_SKILLS_DIR:-$CONFIG/skills}"
BACKUPS="$CONFIG/skill-backups"
BIN="$HOME/.local/bin"
TS="$(date +%Y%m%d-%H%M%S)"

for tool in uv node npm; do
  command -v "$tool" >/dev/null || { echo "missing: $tool" >&2; exit 1; }
done

cd "$REPO"
uv sync --quiet
(cd node && npm ci --silent)
NLTK_DATA="$REPO/data/nltk" uv run python -c "
import nltk
for p in ['wordnet', 'averaged_perceptron_tagger', 'averaged_perceptron_tagger_eng', 'cmudict']:
    nltk.download(p, download_dir='data/nltk', quiet=True)
"

place_link() {
  local target="$1" link="$2" backup_dir="$3"
  if [ -L "$link" ] && [ "$(readlink -f "$link")" = "$(readlink -f "$target")" ]; then
    echo "ok      $link"
    return
  fi
  if [ -e "$link" ] || [ -L "$link" ]; then
    mkdir -p "$backup_dir"
    echo "backup  $link -> $backup_dir/$(basename "$link")-$TS"
    mv "$link" "$backup_dir/$(basename "$link")-$TS"
  fi
  mkdir -p "$(dirname "$link")"
  ln -s "$target" "$link"
  echo "link    $link -> $target"
}

place_link "$REPO/bin/namegen" "$BIN/namegen" "$BIN/.backups"
place_link "$REPO/skill/namegen" "$SKILLS/namegen" "$BACKUPS"

case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo "note: $BIN is not on PATH; add it, or the skill cannot call namegen" ;;
esac

"$REPO/bin/namegen" --project /tmp check Namegen >/dev/null
echo "namegen ready"
