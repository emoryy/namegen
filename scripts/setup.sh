#!/usr/bin/env bash
# One-time setup on a new machine: Python env, Node deps, NLTK data. Corpora and blacklists are in git.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."
uv sync --quiet
(cd node && npm ci --silent)
NLTK_DATA="$PWD/data/nltk" uv run python -c "
import nltk
for p in ['wordnet', 'averaged_perceptron_tagger_eng', 'cmudict']:
    nltk.download(p, download_dir='data/nltk', quiet=True)
"
bin/namegen --project /tmp check Namegen >/dev/null
echo "namegen ready: $PWD/bin/namegen"
