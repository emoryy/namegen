import collections
import random

from . import engines, filters, foreign
from .profiles import load

PSEUDO = {"markov", "lexifer"}
COMPOSITE = {"template", "backronym"}
OVERGENERATE = 8
ROUNDS = 6


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
        self.languages = store.languages() if store else foreign.DEFAULT_LANGUAGES
        self._taken_prons = None
        self.stats = {}

    @property
    def taken_prons(self):
        if self._taken_prons is None:
            self._taken_prons = filters.project_prons(self.store.taken_names()) if self.store else {}
        return self._taken_prons

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

        profanity = flt.get("profanity", True)
        project_sound = flt.get("project_sound", True)
        spread = flt.get("spread", engine not in COMPOSITE)
        accepted_prons = {}

        def reject_reason(cand, name, key):
            core = key.replace(" ", "").replace("-", "")
            if cand.get("reject"):
                return cand["reject"]
            if min_len and len(core) < min_len or max_len and len(core) > max_len:
                return "length"
            if starts and not key.startswith(starts):
                return "prefix"
            if key in self.taken:
                return "used in project"
            if key in corpus:
                return "real place in a corpus"
            if not allow_attractors and " " not in key and filters.attractor_hit(key):
                return "LLM attractor"
            if phonotactics and filters.english_phonotactics(name):
                return "not English-pronounceable"
            if max_zipf is not None and filters.real_word(key, max_zipf):
                return "real English word"
            if sound_check and filters.sounds_like(name)[1]:
                return "homophone of a common word"
            if profanity and filters.profanity_hit(name):
                return "rude"
            if profanity and foreign.rude_hit(name, self.languages):
                return "rude in another language"
            if project_sound and self.taken_prons and filters.close_to_project(name, self.taken_prons):
                return "sounds like a project name"
            if spread and accepted_prons and filters.close_to_project(name, accepted_prons):
                return "too close to another candidate"
            return None

        sub = lambda name, k: self.generate(name, k, top=False)
        batch = n * OVERGENERATE if pseudo else n * 2

        accepted, seen = [], set()
        rejected = collections.Counter()
        raw_total = 0
        # filters (or --starts-with) can eat most of a batch, so draw more until n are found or a round adds nothing new
        for _ in range(ROUNDS):
            raw = engines.run(profile, batch, self.rng, opts, sub)
            raw_total += len(raw)
            fresh = 0
            for cand in raw:
                name = _case(cand["name"], case)
                key = name.lower()
                if key in seen:
                    continue
                seen.add(key)
                fresh += 1
                reason = reject_reason(cand, name, key)
                if reason:
                    rejected[reason] += 1
                    continue
                if sound_check:
                    pron, _, near = filters.sounds_like(name)
                    cand = {**cand, "pron": " ".join(pron)}
                    if near:
                        cand["sounds_like"] = near[:3]
                cand = {k: v for k, v in cand.items() if k != "reject"}
                plain = foreign.plain_words(name, self.languages)
                if plain:
                    cand["word_in"] = [foreign.language_name(l) for l in plain]
                accepted.append({**cand, "name": name})
                if spread:
                    accepted_prons.update(filters.project_prons([name]))
                if len(accepted) >= n:
                    break
            if len(accepted) >= n or fresh == 0:
                break
        if top:
            self.stats = {"profile": profile_name, "engine": engine, "seed": self.seed, "raw": raw_total,
                          "accepted": len(accepted), "rejected": dict(rejected),
                          "description": profile.get("description", "")}
        return accepted
