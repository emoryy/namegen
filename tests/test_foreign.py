import pytest

from namegen import foreign


def test_hungarian_reader_assimilates_voicing():
    assert foreign.read_hu("baszd") == ("B", "AA", "Z", "D")
    assert foreign.read_hu("geci") == ("G", "EH", "T", "S", "IH")


def test_german_reader():
    assert foreign.read_de("scheiße") == ("SH", "AY", "S", "AH")
    assert foreign.read_de("arsch") == ("AA", "R", "SH")


@pytest.mark.parametrize("name, lang, word, how", [
    ("Fass", "hu", "fasz", "sounds like"),
    ("Getsy", "hu", "geci", "sounds like"),
    ("Peena", "hu", "pina", "sounds like"),
    ("Kurvalia", "hu", "kurva", "spelled"),
    ("Shysa", "de", "scheisse", "sounds like"),
    ("Arsh", "de", "arsch", "sounds like"),
])
def test_rude_in_other_languages(name, lang, word, how):
    assert foreign.rude_hit(name, ["en", "hu", "de"]) == (lang, word, how)


@pytest.mark.parametrize("name", ["Rossick", "Balas", "Bost", "Braddam", "Tregon", "Solban", "Segment", "Pin",
                                  "Fuss", "Woodacombe"])
def test_weak_or_known_matches_pass(name):
    assert foreign.rude_hit(name, ["en", "hu", "de"]) is None


def test_english_only_disables_it():
    assert foreign.rude_hit("Getsy", ["en"]) is None


def test_plain_words():
    assert foreign.plain_words("Fuss", ["en", "hu"]) == ["hu"]
    assert foreign.plain_words("Braddam", ["en", "hu"]) == []
