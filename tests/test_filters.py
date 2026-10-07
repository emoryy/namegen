import pytest

from namegen import filters


@pytest.mark.parametrize("name, reason", [
    ("Cuntix", "contains 'cunt'"),
    ("TURD", "rude word 'turd'"),
    ("Shitaka", "contains 'shit'"),
    ("Fukker", "sounds like 'fucker'"),
    ("Slete", "sounds like 'slut'"),
])
def test_rude_invented_names_are_caught(name, reason):
    assert filters.profanity_hit(name) == reason


@pytest.mark.parametrize("name", ["Tytti"])
def test_rude_sound_alike_is_caught(name):
    assert filters.profanity_hit(name)


@pytest.mark.parametrize("name", ["Slate", "Sleet", "Crepe", "Wristwatch", "Scunthorpe", "Kant", "Titan", "Kit",
                                  "Cockburn", "Brugast"])
def test_known_words_and_clean_names_pass(name):
    assert filters.profanity_hit(name) is None


@pytest.mark.parametrize("name", ["Keythley 923 b", "Blackton 72 VII", "Alama Holm IV", "SILT / RECORDS 15",
                                  "Rowlhill-1706e"])
def test_designations_are_judged_word_by_word(name):
    assert filters.english_phonotactics(name) is None


def test_lowercase_roman_numeral_is_not_skipped():
    # only an upper-case token counts as a numeral; 'vii' in running text is a spelling problem
    assert filters.english_phonotactics("blackton vii")


def test_attractors():
    assert filters.attractor_hit("elara")
    assert filters.attractor_hit("veyra")
    assert filters.attractor_hit("tregon") is None


def test_close_to_project():
    prons = filters.project_prons(["Tregon", "Keythley 845"])
    assert filters.close_to_project("Tregone", prons) == ["Tregon"]
    assert filters.close_to_project("Keythley 923 b", prons) == ["Keythley 845"]
    assert filters.close_to_project("Solban", prons) == []


def test_project_prons_skip_numbers_letters_and_common_words():
    prons = filters.project_prons(["Alama Sound 7 b"])
    assert list(prons.values()) == ["Alama Sound 7 b"]
    assert len(prons) == 1
