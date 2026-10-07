---
name: namegen
description: Procedural name generator for worldbuilding (planets, moons, stars, stations, ships, places, factions, machines, organisations, acronyms). Claude picks from generated candidates instead of inventing names, which avoids LLM mode collapse (Elara, Elias, Pell, Veyl, Lantern...). Use when the user asks for a name or names, renaming, "nevet", "átnevezés", "elnevezés", naming a planet / moon / ship / faction / unit / building, or when worldbuilding work needs a new proper noun.
argument-hint: "[what to name] [--project DIR]"
allowed-tools: Bash(~/src/emoryy/namegen/bin/namegen:*)
---

# namegen

Never invent a proper name yourself. LLM-made names converge on the same few attractors across runs and across users; in the ASMR-experiment naming test, Claude produced "Pell" for the same moon in 37 of 51 clean runs. All names come from `namegen`; your job is to choose, rank, and explain.

```bash
NG=~/src/emoryy/namegen/bin/namegen
$NG profiles                         # what exists (tagged with the project it was made for)
$NG gen <profile> -n 80              # candidates; the header shows seed and rejection counts
$NG check <name>...                  # pronunciation, sound-alikes, attractor, already used?
$NG claim <name> --profile <p> --role "<what it names>" --note "<why>"
$NG avoid <name>...                  # existing or rejected names, never offered again
$NG used                             # what this project already has
```

`--project DIR` goes before the subcommand; by default it is the git root of the current directory.

## Workflow

1. Read the project's naming context first (lore, existing names, `$NG used`). If the project has no `.namegen/avoid.txt` yet, offer to add its existing invented names with `avoid`.
2. Pick 2 to 4 profiles that fit the register, and generate from each (`-n 60` to `-n 150`). When the user is unsure about the register, cast wide: several profiles, a shortlist from each, so they can compare sounds.
3. Shortlist 5 to 12 per slot **only from the printed candidates**. For each, give one line: why it fits (sound, meaning for `lexicon` glosses, how it reads aloud), plus any `sounds like` warning.
4. Allowed edits: adding a generic English word (`Brask Station`, `the Treswin Gap`), and a one-letter spelling tweak if you say so and re-run `check` on the result. Not allowed: blending two candidates, or "improving" a candidate into a new name.
5. When the user decides, `claim` it with a role and note. Names the user rejects go to `avoid`.
6. Never reuse a seed across requests unless reproducing a list; the default seed is random.

If no profile fits, write a project profile in `<project>/.namegen/profiles/<name>.toml` (format in `~/src/emoryy/namegen/README.md`): a `markov` corpus, a `lexifer` `.def`, WordNet `roots` for `lexicon`, or a `template`. Generating from it is still the source of the names.

## Project notes

- **ASMR-experiment** (`~/Projektek/ASMR-experiment`): everything spoken is English, voiced by an English TTS and checked with Whisper, so prefer candidates without `sounds like` warnings (Whisper heard "Veyra" as "Vera"). Characters stay nameless; never offer personal names. Hungarian docs inflect names (Hollinon, Pellen), so mention awkward suffixation. Profiles: `anglo-hamlet` is closest to the current names; `cornish-tin`, `fenland`, `highland`, `irish-townland`, `finnic`, `pit-and-pump`, `soft-harbour` give other textures; `survey-catalogue` gives catalogue designations.
- **moons-of-september** (`~/src/emoryy/moons-of-september`): the world names things by function. Moons are real English words whose meaning puns on their role, machines are plain craft nouns, Silt centres are function plus number. Use `lex-*` profiles and match glosses to the role; `concord` for Concord-language pseudo-words; `backronym-maintenance` and `silt-designation` for the Silt side. Lowercase ids in `src/` are expensive to rename (saves, tests, assets); display names are cheap.
