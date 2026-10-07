"""Candidate engines. Each returns a list of dicts: {"name": str, ...extra fields shown to the curator}."""

import functools
import json
import random
import re
import subprocess

from .paths import CORPORA, NODE_HELPER, ROOT


def _read_words(path):
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def corpus_words(profile):
    files = profile["corpus"] if isinstance(profile["corpus"], list) else [profile["corpus"]]
    words = []
    for f in files:
        words += _read_words(CORPORA / f if not f.startswith("/") else f)
    return words


@functools.cache
def all_corpus_words():
    return frozenset(w.lower() for f in CORPORA.glob("*.txt") for w in _read_words(f))


def _node(request):
    out = subprocess.run(["node", str(NODE_HELPER)], input=json.dumps(request), capture_output=True,
                         text=True, check=True)
    return json.loads(out.stdout)


def markov(profile, n, rng, opts):
    words = [w.lower() for w in corpus_words(profile)]
    raw = _node({
        "engine": "markov",
        "words": words,
        "n": n,
        "seed": rng.randrange(2**32),
        "order": profile.get("order", 3),
        "prior": profile.get("prior", 0.0),
        "backoff": profile.get("backoff", True),
        "minLength": opts.get("min_len") or profile.get("min_len", 4),
        "maxLength": opts.get("max_len") or profile.get("max_len", 10),
        "startsWith": (opts.get("starts_with") or "").lower(),
    })
    return [{"name": w} for w in raw]


def lexifer(profile, n, rng, opts):
    path = ROOT / "profiles" / profile["def"] if "def" in profile else profile["_path"].with_suffix(".def")
    raw = _node({"engine": "lexifer", "def": path.read_text(encoding="utf-8"), "n": n,
                 "seed": rng.randrange(2**32)})
    return [{"name": w} for w in raw]


@functools.cache
def _wordnet():
    from nltk.corpus import wordnet as wn
    wn.ensure_loaded()
    return wn


def _field_synsets(roots, exclude):
    wn = _wordnet()
    excluded = set()
    for r in exclude:
        s = wn.synset(r)
        excluded |= {s} | set(s.closure(lambda y: y.hyponyms()))
    syn = set()
    for r in roots:
        s = wn.synset(r)
        for x in [s] + list(s.closure(lambda y: y.hyponyms())):
            if x not in excluded:
                syn.add(x)
                syn.update(t for t in x.in_topic_domains() if t not in excluded)
    return syn


def lexicon_pool(profile):
    """All single lowercase words whose senses fall in the profile's WordNet field, with a gloss."""
    from wordfreq import zipf_frequency

    wn = _wordnet()
    syn = _field_synsets(profile["roots"], profile.get("exclude_roots", []))
    zmin, zmax = profile.get("zipf_min", 1.0), profile.get("zipf_max", 3.8)
    primary = profile.get("primary_sense", True)
    pool = {}
    for s in syn:
        for lemma in s.lemmas():
            w = lemma.name()
            if w in pool or not (w.isalpha() and w.islower()):
                continue
            if not zmin <= zipf_frequency(w, "en") <= zmax:
                continue
            senses = wn.synsets(w)
            if primary and senses and senses[0] not in syn:
                continue
            pool[w] = s.definition()
    return pool


def lexicon(profile, n, rng, opts):
    pool = lexicon_pool(profile)
    words = sorted(pool)
    rng.shuffle(words)
    from wordfreq import zipf_frequency

    return [{"name": w, "gloss": pool[w], "zipf": round(zipf_frequency(w, "en"), 1)} for w in words]


def _num(spec, rng):
    lo, hi = spec.split("-")
    width = len(lo) if lo.startswith("0") else 0
    return str(rng.randint(int(lo), int(hi))).zfill(width)


def template(profile, n, rng, opts, generate):
    """Patterns like "{survey} {num:2-999}{letter}". A slot is a word list or {profile = "..."}."""
    slots = profile.get("slots", {})
    filled = {}
    for key, spec in slots.items():
        if isinstance(spec, dict) and "profile" in spec:
            filled[key] = [c["name"] for c in generate(spec["profile"], n)]
        elif isinstance(spec, dict) and "file" in spec:
            filled[key] = _read_words(ROOT / spec["file"])
        else:
            filled[key] = list(spec)

    # deal slot values like cards, so one generated name does not fill half the list
    decks = {}

    def fill(m):
        key = m.group(1)
        if key.startswith("num:"):
            return _num(key[4:], rng)
        if not decks.get(key):
            decks[key] = filled[key][:]
            rng.shuffle(decks[key])
        return decks[key].pop()

    out = []
    for _ in range(n):
        pattern = rng.choice(profile["patterns"])
        out.append({"name": re.sub(r"\{([^}]+)\}", fill, pattern)})
    return out


def backronym(profile, n, rng, opts, generate):
    """An acronym word plus an expansion built from vocabulary lists, like SILT = Surface Integrity and Lifecycle Tending."""
    vocab = {k: _read_words(ROOT / f) for k, f in profile["vocab"].items()}
    by_letter = {k: {} for k in vocab}
    for k, words in vocab.items():
        for w in words:
            by_letter[k].setdefault(w[0].upper(), []).append(w)
    shapes = [s.split() for s in profile["shapes"]]
    glue = set(profile.get("glue", ["and", "of", "for"]))
    acronyms = [c["name"].upper() for c in generate(profile["acronyms"], n * 4)]

    out = []
    for acro in acronyms:
        fitting = [s for s in shapes if sum(1 for slot in s if slot not in glue) == len(acro)]
        rng.shuffle(fitting)
        for shape in fitting:
            letters = iter(acro)
            words = []
            for slot in shape:
                if slot in glue:
                    words.append(slot)
                    continue
                choices = [w for w in by_letter[slot].get(next(letters), []) if w not in words]
                if not choices:
                    break
                words.append(rng.choice(choices))
            else:
                out.append({"name": acro, "expansion": " ".join(words)})
                break
        else:
            out.append({"name": acro, "reject": "no expansion fits" if fitting else "no shape for its length"})
        if sum(1 for c in out if "reject" not in c) >= n:
            break
    return out


ENGINES = {"markov": markov, "lexifer": lexifer, "lexicon": lexicon}
COMPOSITE = {"template": template, "backronym": backronym}


def run(profile, n, rng, opts, generate):
    engine = profile["engine"]
    if engine in COMPOSITE:
        return COMPOSITE[engine](profile, n, rng, opts, generate)
    return ENGINES[engine](profile, n, rng, opts)
