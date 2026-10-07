"""Build the place-name training corpora in corpora/ from GeoNames dumps.

Download first (CC-BY 4.0, https://www.geonames.org):
    cd data/raw && for c in GB FI EE IE; do curl -sSO https://download.geonames.org/export/dump/$c.zip && unzip -oq $c.zip $c.txt; done
"""

import re
from pathlib import Path

from unidecode import unidecode

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "corpora"

WORD = re.compile(r"^[A-Za-z]{4,12}$")


def places(country):
    with open(RAW / f"{country}.txt", encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            if c[6] != "P":
                continue
            yield {
                "name": c[1],
                "lat": float(c[4]),
                "lon": float(c[5]),
                "admin1": c[10],
                "pop": int(c[14] or 0),
            }


def single_words(rows, max_pop=None, transliterate=False):
    out = set()
    for r in rows:
        if max_pop is not None and r["pop"] > max_pop:
            continue
        name = unidecode(r["name"]) if transliterate else r["name"]
        if WORD.match(name):
            out.add(name.capitalize())
    return out


def write(name, words, header):
    OUT.mkdir(exist_ok=True)
    lines = [f"# {header}", "# Source: GeoNames (CC-BY 4.0), populated places, single-word names only."]
    (OUT / f"{name}.txt").write_text("\n".join(lines + sorted(words)) + "\n", encoding="utf-8")
    print(f"{name}: {len(words)}")


def main():
    gb = list(places("GB"))
    eng = [r for r in gb if r["admin1"] == "ENG"]
    write("england-hamlets", single_words(eng, max_pop=5000), "English villages and hamlets (population <= 5000)")
    write("cornwall", single_words(r for r in eng if r["lon"] < -4.2 and r["lat"] < 50.95),
          "Cornish places (old tin-mining country)")
    write("fenland", single_words(r for r in eng if 52.2 < r["lat"] < 53.4 and -0.5 < r["lon"] < 1.8),
          "East Anglian fens and Lincolnshire")
    write("highlands", single_words(r for r in gb if r["admin1"] == "SCT" and r["lat"] > 56.4 and r["lon"] < -3.5),
          "Scottish Highlands and islands (anglicised Gaelic)")
    write("ireland", single_words(places("IE"), max_pop=5000), "Irish villages (anglicised Irish)")
    write("finnic", single_words(list(places("FI")) + list(places("EE")), max_pop=2000, transliterate=True),
          "Finnish and Estonian villages, transliterated to ASCII")


if __name__ == "__main__":
    main()
