"""Other-language checks: rude words a reader of language X would see or hear in a name, and plain words of X.

Spelling is matched for every language with a list in data/rude/. Pronunciation is matched only for languages with
a rule-based reader below (hu, de): the name's English pronunciation is compared with the foreign word's, after
folding vowels into coarse classes, because vowel qualities never line up exactly across languages.
"""

import functools
import re

from unidecode import unidecode
from wordfreq import zipf_frequency

from .paths import DATA

LANGUAGE_NAMES = {"hu": "Hungarian", "de": "German", "fi": "Finnish", "fr": "French", "es": "Spanish",
                  "it": "Italian", "nl": "Dutch", "pl": "Polish", "pt": "Portuguese", "sv": "Swedish",
                  "cs": "Czech", "da": "Danish", "no": "Norwegian", "ru": "Russian", "tr": "Turkish"}
DEFAULT_LANGUAGES = ["en", "hu"]
PREFIX_MIN_LETTERS = 4
NEAR_MIN_PHONES = 4
WORD_ZIPF = 3.0
KNOWN_ENGLISH_ZIPF = 2.5


def language_name(code):
    return LANGUAGE_NAMES.get(code, code)


# --- rule-based readers: spelling -> ARPAbet ------------------------------------------------------------------

HU_MULTI = [("dzs", ["JH"]), ("cs", ["CH"]), ("dz", ["D", "Z"]), ("gy", ["JH"]), ("ly", ["Y"]), ("ny", ["N", "Y"]),
            ("sz", ["S"]), ("ty", ["T", "Y"]), ("zs", ["ZH"])]
HU_SINGLE = {"a": "AA", "á": "AA", "b": "B", "c": "T S", "d": "D", "e": "EH", "é": "EY", "f": "F", "g": "G",
             "h": "HH", "i": "IH", "í": "IY", "j": "Y", "k": "K", "l": "L", "m": "M", "n": "N", "o": "OW",
             "ó": "OW", "ö": "ER", "ő": "ER", "p": "P", "q": "K", "r": "R", "s": "SH", "t": "T", "u": "UH",
             "ú": "UW", "ü": "UW", "ű": "UW", "v": "V", "w": "V", "x": "K S", "y": "IY", "z": "Z"}

DE_MULTI = [("tsch", ["CH"]), ("sch", ["SH"]), ("chs", ["K", "S"]), ("ch", ["K"]), ("ck", ["K"]), ("ph", ["F"]),
            ("qu", ["K", "V"]), ("th", ["T"]), ("ei", ["AY"]), ("ey", ["AY"]), ("ai", ["AY"]), ("ie", ["IY"]),
            ("eu", ["OY"]), ("äu", ["OY"]), ("au", ["AW"]), ("ss", ["S"]), ("ß", ["S"]), ("tz", ["T", "S"]),
            ("pf", ["P", "F"]), ("ng", ["NG"])]
DE_SINGLE = {"a": "AA", "ä": "EH", "b": "B", "c": "K", "d": "D", "e": "EH", "f": "F", "g": "G", "h": "HH",
             "i": "IH", "j": "Y", "k": "K", "l": "L", "m": "M", "n": "N", "o": "OW", "ö": "ER", "p": "P",
             "r": "R", "s": "S", "t": "T", "u": "UH", "ü": "UW", "v": "F", "w": "V", "x": "K S", "y": "UW",
             "z": "T S"}
DE_FINAL_DEVOICE = {"B": "P", "D": "T", "G": "K", "Z": "S"}
VOWEL_PHONES = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}


def _read(word, multi, single):
    phones, i = [], 0
    while i < len(word):
        for graph, ph in multi:
            if word.startswith(graph, i):
                phones += ph
                i += len(graph)
                break
        else:
            phones += single.get(word[i], "").split()
            i += 1
    return phones


def _dedupe(phones):
    return [p for i, p in enumerate(phones) if i == 0 or p != phones[i - 1]]


VOICED = {"P": "B", "T": "D", "K": "G", "S": "Z", "SH": "ZH", "CH": "JH", "F": "V"}
UNVOICED = {v: k for k, v in VOICED.items()}


def _assimilate(phones):
    """Hungarian regressive voicing: an obstruent takes the voicing of the obstruent after it (baszd -> bazd)."""
    out = list(phones)
    for i in range(len(out) - 2, -1, -1):
        nxt = out[i + 1]
        if nxt in UNVOICED and nxt != "V" and out[i] in VOICED:
            out[i] = VOICED[out[i]]
        elif nxt in VOICED and out[i] in UNVOICED and out[i] != "V":
            out[i] = UNVOICED[out[i]]
    return out


def read_hu(word):
    return tuple(_dedupe(_assimilate(_read(word.lower(), HU_MULTI, HU_SINGLE))))


def read_de(word):
    w = word.lower()
    prefix = []
    if re.match(r"s[pt]", w):
        prefix, w = ["SH"], w[1:]
    elif re.match(r"s[aeiouäöü]", w):
        prefix, w = ["Z"], w[1:]
    final_er = w.endswith("er") and len(w) > 3
    if final_er:
        w = w[:-2]
    phones = prefix + _read(w, DE_MULTI, DE_SINGLE)
    # h after a vowel only lengthens it
    phones = [p for i, p in enumerate(phones) if not (p == "HH" and i > 0 and phones[i - 1] in VOWEL_PHONES)]
    if final_er:
        phones.append("ER")
    elif w.endswith("e") and phones and phones[-1] == "EH":
        phones[-1] = "AH"
    elif phones and phones[-1] in DE_FINAL_DEVOICE:
        phones[-1] = DE_FINAL_DEVOICE[phones[-1]]
    return tuple(_dedupe(phones))


READERS = {"hu": read_hu, "de": read_de}

VOWEL_CLASS = {"AA": "A", "AE": "A", "AH": "A", "AO": "O", "OW": "O", "EH": "E", "EY": "E", "IH": "I", "IY": "I",
               "UH": "U", "UW": "U"}


def fold(phones):
    """Coarse form for cross-language comparison: vowel classes, repeated phones merged."""
    return tuple(_dedupe([VOWEL_CLASS.get(p, p) for p in phones]))


FOLDED_VOWELS = set(VOWEL_CLASS.values()) | VOWEL_PHONES


def _near(a, b):
    """One position differs, and only by a vowel or by voicing (T/D, S/Z): consonants carry recognition."""
    if len(a) != len(b):
        return False
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    if len(diff) != 1:
        return False
    x, y = diff[0]
    return (x in FOLDED_VOWELS and y in FOLDED_VOWELS) or VOICED.get(x) == y or VOICED.get(y) == x


# --- word lists ---------------------------------------------------------------------------------------------

@functools.cache
def rude_words(lang):
    path = DATA / "rude" / f"{lang}.txt"
    if not path.exists():
        return ()
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        w = line.strip().lower()
        if w and not w.startswith("#") and " " not in w:
            out.append(w)
    return tuple(out)


@functools.cache
def _rude_prons(lang):
    reader = READERS.get(lang)
    if not reader:
        return {}
    return {fold(reader(w)): w for w in rude_words(lang)}


def _spelling_hit(tokens, lang, prefixes):
    for w in rude_words(lang):
        flat = unidecode(w)
        for t in tokens:
            if t == flat or (prefixes and len(flat) >= PREFIX_MIN_LETTERS and t.startswith(flat)):
                return w
    return None


def _sound_hit(mine, lang):
    prons = _rude_prons(lang)
    if mine in prons:
        return prons[mine]
    for theirs, w in prons.items():
        if len(theirs) >= NEAR_MIN_PHONES and (_near(mine, theirs) or mine[:len(theirs)] == theirs):
            return w
    return None


def rude_hit(name, languages):
    """(language, rude word, how) for the first other-language rude match, else None.

    Known English words (pin, pinafore) are matched as whole words only, like the English filter does."""
    from .filters import english_pron

    tokens = [unidecode(t) for t in re.findall(r"[^\W\d_]+", name.lower())]
    invented = [t for t in tokens if len(t) > 1 and zipf_frequency(t, "en") < KNOWN_ENGLISH_ZIPF]
    for lang in languages:
        if lang == "en":
            continue
        w = _spelling_hit(tokens, lang, prefixes=False) or _spelling_hit(invented, lang, prefixes=True)
        if w:
            return lang, w, "spelled"
        for t in invented:
            w = _sound_hit(fold(english_pron(t)), lang)
            if w:
                return lang, w, "sounds like"
    return None


def describe_rude(hit):
    lang, word, how = hit
    return f"{how} {language_name(lang)} '{word}'"


def plain_words(name, languages):
    """Languages (other than English) in which every word of the name is a common word."""
    tokens = re.findall(r"[^\W\d_]+", name.lower())
    if not tokens:
        return []
    return [lang for lang in languages if lang != "en"
            and all(zipf_frequency(t, lang) >= WORD_ZIPF for t in tokens)]
