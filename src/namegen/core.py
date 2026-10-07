import collections
import random

from . import engines, filters
from .profiles import load

PSEUDO = {"markov", "lexifer"}
OVERGENERATE = 8


def _case(name, mode):
    if mode == "title":
        return "-".join(p[:1].upper() + p[1:].lower() for p in name.split("-"))
    if mode == "upper":
        return name.upper()
    if mode == "lower":
        return name.lower()
    return name


class Generator:
    def __init__(self, project_root, store, seed):
        self.project_root = project_root
        self.store = store
        self.seed = seed
        self.rng = random.Random(seed)
        self.taken = store.taken() if store else set()
        self.stats = {}

    def generate(self, profile_name, n, opts=None, top=True):
        opts = opts or {}
        profile = load(profile_name, self.project_root)
        engine = profile["engine"]
        pseudo = engine in PSEUDO
        flt = profile.get("filters", {})
        phonotactics = flt.get("phonotactics", pseudo)
        max_zipf = flt.get("max_zipf", 2.5 if pseudo else None)
        sound_check = flt.get("sound_check", pseudo)
        allow_attractors = flt.get("allow_attractors", False)
        reject_corpus = flt.get("reject_corpus_words", engine == "markov")
        corpus = engines.all_corpus_words() if reject_corpus else frozenset()
        min_len = opts.get("min_len") or profile.get("min_len")
        max_len = opts.get("max_len") or profile.get("max_len")
        starts = (opts.get("starts_with") or "").lower()
        case = profile.get("case", "upper" if engine == "backronym" else "title")

        sub = lambda name, k: self.generate(name, k, top=False)
        raw = engines.run(profile, n * OVERGENERATE if pseudo else n * 2, self.rng, opts, sub)

        accepted, seen = [], set()
        rejected = collections.Counter()
        for cand in raw:
            name = _case(cand["name"], case)
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            core = key.replace(" ", "").replace("-", "")
            reason = None
            if min_len and len(core) < min_len or max_len and len(core) > max_len:
                reason = "length"
            elif starts and not key.startswith(starts):
                reason = "prefix"
            elif key in self.taken:
                reason = "used in project"
            elif key in corpus:
                reason = "real place in a corpus"
            elif not allow_attractors and (filters.attractor_hit(key) if " " not in key else None):
                reason = "LLM attractor"
            elif phonotactics and filters.english_phonotactics(key):
                reason = "not English-pronounceable"
            elif max_zipf is not None and filters.real_word(key, max_zipf):
                reason = "real English word"
            if reason is None and sound_check:
                pron, exact, near = filters.sounds_like(name)
                if exact:
                    reason = "homophone of a common word"
                else:
                    cand = {**cand, "pron": " ".join(pron)}
                    if near:
                        cand["sounds_like"] = near[:3]
            if reason:
                rejected[reason] += 1
                continue
            accepted.append({**cand, "name": name})
            if len(accepted) >= n:
                break
        if top:
            self.stats = {"profile": profile_name, "engine": engine, "seed": self.seed, "raw": len(raw),
                          "accepted": len(accepted), "rejected": dict(rejected),
                          "description": profile.get("description", "")}
        return accepted
