"""Candidate checks: English phonotactics, real words, LLM attractors, and what a name sounds like."""

import functools
import pickle
import re
import warnings

from wordfreq import zipf_frequency

from .paths import CACHE, DATA

VOWELS = set("aeiouy")

ONSETS = set("""bl br ch cl cr dr dw fl fr gl gr gw kl kn kr ph pl pr sc sh sk sl sm sn sp st sw th tr tw wh wr
scr shr spl spr str thr chr sch""".split())
CODAS = set("""ch ck ct ff ft ld lf lk ll lm ln lp lt mb mp nd ng nk ns nt pt rb rc rd rf rg rk rl rm rn rp rs rt sh sk
sp ss st th tt wn ws wl wk ls ms ts ks ds gs nx rx lch lsh ght nch rch tch rth rst lth nth ngs nds nts rds rks rns""".split())
BAD_DOUBLES = {"hh", "jj", "kk", "qq", "vv", "ww", "xx", "yy"}
BAD_VOWEL_PAIRS = {"aa", "ii", "uu", "yy", "iy", "yi", "uy", "yu", "uo", "iu"}


def _clusters(word):
    """Split into alternating consonant/vowel runs; initial y and w after a vowel count as consonant/vowel."""
    runs, cur, cur_is_v = [], "", None
    for i, ch in enumerate(word):
        is_v = ch in VOWELS and not (ch == "y" and i == 0)
        if ch == "w" and i > 0 and word[i - 1] in "aeo":
            is_v = True
        if cur and is_v != cur_is_v:
            runs.append((cur, cur_is_v))
            cur = ""
        cur += ch
        cur_is_v = is_v
    if cur:
        runs.append((cur, cur_is_v))
    return runs


def _medial_ok(c):
    if len(c) == 1:
        return True
    if len(c) == 2:
        if c in BAD_DOUBLES or c[1] in "qx" or c[0] in "qjx" or (c[0] == "h" and c != "ht"):
            return False
        return True
    if len(c) == 3:
        return (c[1:] in ONSETS) or (c[:2] in CODAS) or (c[:2] in ("ng", "nk", "ck") and len(c[2:]) == 1)
    return False


ROMAN = re.compile(r"^[IVXLC]+$")


def english_phonotactics(name):
    w = name.lower()
    if not w.isalpha():
        # designations like 'Keythley 923 b' or 'Alama Holm IV': judge each word, skip numbers, letters, numerals
        parts = [re.sub(r"\d+", "", p) for p in re.split(r"[\s\-/]+", name) if p]
        if not all(p.isalpha() for p in parts if p):
            return "non-letters"
        for p in parts:
            if len(p) <= 1 or ROMAN.match(p):
                continue
            problem = english_phonotactics(p)
            if problem:
                return f"{problem} in '{p}'"
        return None
    if re.search(r"q(?!u)", w):
        return "q without u"
    runs = _clusters(w)
    for i, (run, is_v) in enumerate(runs):
        first, last = i == 0, i == len(runs) - 1
        if is_v:
            if len(run) >= 3 or (len(run) == 2 and run in BAD_VOWEL_PAIRS):
                return f"vowels '{run}'"
            continue
        if first and last:
            return "no vowel"
        if first:
            if len(run) > 1 and run not in ONSETS:
                return f"onset '{run}'"
        elif last:
            if len(run) > 1 and run not in CODAS:
                return f"coda '{run}'"
        elif not _medial_ok(run):
            return f"cluster '{run}'"
    return None


def _read_list(path):
    if not path.exists():
        return []
    return [l.split("\t")[0].strip() for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


@functools.cache
def attractors():
    return {w.lower() for w in _read_list(DATA / "attractors.txt") + _read_list(DATA / "blacklist.txt")}


@functools.cache
def blacklist_patterns():
    return [re.compile(p, re.I) for p in _read_list(DATA / "blacklist-patterns.txt")]


def attractor_hit(name):
    low = name.lower()
    if low in attractors():
        return f"attractor '{low}'"
    for p in blacklist_patterns():
        if p.search(low):
            return f"attractor pattern /{p.pattern}/"
    return None


def words(name):
    """Alphabetic tokens of a name, lowercased: 'Keythley 923 b' -> ['keythley', 'b']."""
    return re.findall(r"[a-z]+", name.lower())


PROFANITY_NEAR_MIN_PHONES = 4
KNOWN_WORD_ZIPF = 1.5


@functools.cache
def _profanity():
    stems = [s.lower() for s in _read_list(DATA / "profanity-stems.txt")]
    whole = {w.lower() for w in _read_list(DATA / "profanity-words.txt")}
    prons = {}
    for w in whole:
        for p in _prons(w):
            prons.setdefault(_strip_stress(p), w)
    return stems, whole, prons


def profanity_hit(name, pron=None):
    """Rude whole word; for invented words also a rude stem anywhere or a pronunciation equal to (or one phone
    from) a rude word. Known English words skip the last two, so slate, crepe or wristwatch stay allowed."""
    stems, whole, prons = _profanity()
    low = name.lower()
    tokens = words(name)
    for w in tokens:
        if w in whole:
            return f"rude word '{w}'"
    if tokens and all(zipf_frequency(w, "en") >= KNOWN_WORD_ZIPF for w in tokens):
        return None
    for s in stems:
        if s in low:
            return f"contains '{s}'"
    if pron is None:
        if not name.isalpha():
            return None
        pron = _strip_stress(pronounce(name))
    if pron in prons:
        return f"sounds like '{prons[pron]}'"
    for p, w in prons.items():
        if len(p) >= PROFANITY_NEAR_MIN_PHONES and _edit1(pron, p):
            return f"sounds like '{w}'"
    return None


def project_prons(names):
    """Pronunciations of a project's distinctive name words (not numbers, single letters or common words)."""
    out = {}
    for name in names:
        for w in words(name):
            if len(w) >= 3 and zipf_frequency(w, "en") < 3.0:
                out.setdefault(_strip_stress(pronounce(w)), name)
    return out


def close_to_project(name, taken_prons):
    """Project names that a word of this name matches or is one phone away from."""
    hits = []
    for w in words(name):
        if len(w) < 3:
            continue
        pron = _strip_stress(pronounce(w))
        for p, owner in taken_prons.items():
            if (pron == p or _edit1(pron, p)) and owner not in hits:
                hits.append(owner)
    return hits


def real_word(name, max_zipf):
    z = zipf_frequency(name.lower(), "en")
    return f"real word (zipf {z:.1f})" if z > max_zipf else None


# --- pronunciation -----------------------------------------------------------------

SOUND_INDEX_MIN_ZIPF = 3.0


def _strip_stress(phones):
    return tuple(re.sub(r"\d", "", p) for p in phones)


def _deletion_keys(phones):
    yield phones
    for i in range(len(phones)):
        yield phones[:i] + phones[i + 1:]


@functools.cache
def _sound_index():
    """Maps pronunciation (and every one-phone deletion of it) to common English words and names."""
    path = CACHE / f"sound_index_{SOUND_INDEX_MIN_ZIPF}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    exact, near = {}, {}
    for word, prons in _cmu().items():
        if not word.isalpha():
            continue
        z = zipf_frequency(word, "en")
        if z < SOUND_INDEX_MIN_ZIPF:
            continue
        for pron in prons:
            p = _strip_stress(pron)
            exact.setdefault(p, []).append((z, word))
            for k in _deletion_keys(p):
                near.setdefault(k, set()).add(word)
    exact = {k: [w for _, w in sorted(v, reverse=True)] for k, v in exact.items()}
    index = (exact, near)
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pickle.dumps(index))
    return index


@functools.cache
def _cmu():
    import cmudict
    return cmudict.dict()


def _prons(word):
    return _cmu().get(word, [])


def _edit1(a, b):
    """True when phone sequences a and b differ by at most one substitution, insertion or deletion."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    if len(a) > len(b):
        a, b = b, a
    return any(a == b[:i] + b[i + 1:] for i in range(len(b)))


@functools.cache
def _g2p():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from g2p_en import G2p
    return G2p()


@functools.lru_cache(maxsize=65536)
def pronounce(name):
    return tuple(p for p in _g2p()(name) if p.strip())


def english_pron(word):
    """Stress-free ARPAbet as an English reader would say the word."""
    return _strip_stress(pronounce(word))


def sounds_like(name):
    """Returns (pronunciation, exact homophones, near matches one phone away)."""
    exact_idx, near_idx = _sound_index()
    pron = _strip_stress(pronounce(name))
    exact = [w for w in exact_idx.get(pron, []) if w != name.lower()]
    near = set()
    for k in _deletion_keys(pron):
        near |= near_idx.get(k, set())
    near -= set(exact) | {name.lower()}
    near = {w for w in near if any(_edit1(pron, _strip_stress(p)) for p in _prons(w))}
    near = sorted(near, key=lambda w: (-zipf_frequency(w, "en"), w))
    return pron, exact, near
