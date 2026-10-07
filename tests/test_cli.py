import json

import pytest


def names(out):
    return [l.split("   ")[0].split(" [")[0].split(" = ")[0] for l in out.splitlines() if not l.startswith("#")]


def header(out):
    return out.splitlines()[1]


def test_claim_unknown_profile_is_refused(cli):
    code, out = cli("claim", "Kestrel", "--profile", "nonsense", "--role", "ship")
    assert code == 1 and "unknown profile" in out


def test_claim_attractor_needs_force(cli, project):
    code, out = cli("claim", "Elara", "--profile", "manual", "--role", "moon")
    assert code == 1 and "attractor" in out
    code, out = cli("claim", "Elara", "--profile", "manual", "--role", "moon", "--force")
    assert code == 0 and "warning" in out
    assert json.loads((project / ".namegen" / "used.json").read_text())[0]["name"] == "Elara"


def test_claim_sound_alike_and_duplicate(cli):
    assert cli("claim", "Tregon", "--profile", "cornish-tin", "--role", "town")[0] == 0
    code, out = cli("claim", "Tregone", "--profile", "cornish-tin", "--role", "town")
    assert code == 1 and "Tregon" in out
    code, out = cli("claim", "tregon", "--profile", "cornish-tin", "--role", "town")
    assert code == 1 and "already claimed" in out


def test_check_reports_rude_and_project_sound(cli):
    cli("claim", "Tregon", "--profile", "cornish-tin", "--role", "town")
    code, out = cli("check", "Tregone", "Cuntix")
    assert "sounds like a project name: Tregon" in out
    assert "rude: contains 'cunt'" in out


def test_seed_is_reproducible(cli):
    a = cli("gen", "cornish-tin", "-n", "10", "--seed", "42")[1]
    b = cli("gen", "cornish-tin", "-n", "10", "--seed", "42")[1]
    assert names(a) == names(b) and len(names(a)) == 10


def test_claimed_and_avoided_names_are_not_offered(cli):
    first = names(cli("gen", "cornish-tin", "-n", "8", "--starts-with", "bra", "--seed", "2")[1])
    assert "Braddon" in first
    cli("claim", "Braddam", "--profile", "cornish-tin", "--role", "town")
    cli("avoid", "Brazion")
    out = cli("gen", "cornish-tin", "-n", "8", "--starts-with", "bra", "--seed", "2")[1]
    assert not {"Braddon", "Braddoc", "Brazion"} & set(names(out))
    assert "sounds like a project name" in header(out)


def test_starts_with_fills_the_list(cli):
    out = cli("gen", "fenland", "-n", "8", "--starts-with", "sl", "--seed", "3")[1]
    got = names(out)
    assert len(got) == 8 and all(n.lower().startswith("sl") for n in got)


def test_impossible_prefix_returns_nothing(cli):
    code, out = cli("gen", "fenland", "-n", "5", "--starts-with", "zq", "--seed", "1")
    assert code == 0 and names(out) == []


def test_template_deals_slot_values_without_repeats(cli):
    out = cli("gen", "survey-catalogue", "-n", "6", "--seed", "2026")[1]
    surveys = [n.split()[0].split("-")[0] for n in names(out)]
    assert len(surveys) == len(set(surveys))


def test_backronym_counts_failed_acronyms(cli, project):
    prof = project / ".namegen" / "profiles"
    prof.mkdir(parents=True)
    (project / "q.txt").write_text("Tidal\n")
    (project / "o.txt").write_text("Ice\n")
    (project / "a.txt").write_text("Logistics\n")
    (prof / "thin.toml").write_text(f'''engine = "backronym"
acronyms = "lex-acronym"
shapes = ["qualifier object action"]
[vocab]
qualifier = "{project}/q.txt"
object = "{project}/o.txt"
action = "{project}/a.txt"
''')
    out = cli("gen", "thin", "-n", "3", "--seed", "1")[1]
    assert "no expansion fits" in header(out) or "no shape for its length" in header(out)


def test_lexicon_shows_frequency(cli):
    data = json.loads(cli("gen", "lex-mineral", "-n", "3", "--seed", "1", "--json")[1])
    assert all("zipf" in c and c["zipf"] <= 3.2 for c in data["candidates"])


@pytest.mark.parametrize("profile", ["anglo-hamlet", "concord", "lex-learned", "survey-catalogue",
                                     "backronym-maintenance", "silt-designation"])
def test_profiles_generate(cli, profile):
    code, out = cli("gen", profile, "-n", "5", "--seed", "7")
    assert code == 0 and len(names(out)) == 5


def test_rude_acronyms_never_come_out(cli):
    for seed in range(1, 6):
        out = cli("gen", "lex-acronym", "-n", "60", "--seed", str(seed))[1]
        assert not {"Turd", "Crap", "Piss", "Skank"} & set(names(out))


def test_project_languages_from_config(cli, project):
    code, out = cli("check", "Getsy")
    assert "sounds like Hungarian 'geci'" in out
    (project / ".namegen").mkdir(exist_ok=True)
    (project / ".namegen" / "config.toml").write_text('languages = ["en"]\n')
    code, out = cli("check", "Getsy")
    assert "other languages" not in out
    assert cli("claim", "Getsy", "--profile", "manual", "--role", "x")[0] == 0


def test_claim_refuses_rude_in_other_language(cli):
    code, out = cli("claim", "Getsy", "--profile", "manual", "--role", "x")
    assert code == 1 and "Hungarian 'geci'" in out
