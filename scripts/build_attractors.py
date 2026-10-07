"""Collect LLM name attractors from naming-experiment result JSONs into data/attractors.txt.

Usage: uv run python scripts/build_attractors.py ~/Projektek/ASMR-experiment/vilag/kiserlet-nevek
Every name and alternative is split into words; a word counts as an attractor when the
model produced it at least twice and it is not a common English word (Station, Gap, ...).
"""

import collections
import glob
import json
import re
import sys
from pathlib import Path

from wordfreq import zipf_frequency

OUT = Path(__file__).resolve().parent.parent / "data" / "attractors.txt"


def names_in(path):
    d = json.load(open(path))
    if "result" in d:
        t = d["result"]
        d = json.loads(t[t.index("{"):t.rindex("}") + 1])
    for slot in d.values():
        yield slot["name"]
        yield from slot.get("alternatives", [])


def main(dirs):
    counts = collections.Counter()
    for d in dirs:
        for f in glob.glob(f"{d}/**/*.json", recursive=True):
            try:
                for name in names_in(f):
                    for w in re.findall(r"[A-Za-z]+", name.replace("'s", "")):
                        counts[w.lower()] += 1
            except (ValueError, KeyError, AttributeError):
                continue
    keep = [(w, c) for w, c in counts.most_common() if c >= 2 and len(w) > 2 and zipf_frequency(w, "en") < 4.5]
    lines = ["# LLM attractor words from naming experiments: word<TAB>count. Generated, do not edit by hand."]
    lines += [f"{w}\t{c}" for w, c in keep]
    OUT.write_text("\n".join(lines) + "\n")
    print(f"{len(keep)} attractors -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
