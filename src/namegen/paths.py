import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
CORPORA = ROOT / "corpora"
PROFILES = ROOT / "profiles"
NODE_HELPER = ROOT / "node" / "gen.mjs"
CACHE = DATA / "cache"

os.environ.setdefault("NLTK_DATA", str(DATA / "nltk"))


def project_root(arg):
    if arg:
        return Path(arg).expanduser().resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()
