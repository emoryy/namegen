---
name: namegen
description: Procedural name generator for worldbuilding (planets, moons, stars, stations, ships, places, factions, machines, organisations, acronyms). Claude picks from generated candidates instead of inventing names, which avoids LLM mode collapse (Elara, Elias, Pell, Veyl, Lantern...). Use when the user asks for a name or names, renaming, "nevet", "átnevezés", "elnevezés", naming a planet / moon / ship / faction / unit / building, or when worldbuilding work needs a new proper noun.
argument-hint: "[what to name] [--project DIR]"
allowed-tools: Bash(namegen:*)
---

# namegen

Never invent a proper name yourself. LLM-made names converge on the same few attractors across runs and across users; in one naming test, Claude produced "Pell" for the same moon in 37 of 51 clean runs. All names come from `namegen`; your job is to choose, rank, and explain.

```bash
namegen context                      # project naming notes, claimed and avoided names: read this first
namegen profiles                     # available profiles
namegen gen <profile> -n 80          # candidates; the header shows seed and rejection counts
namegen check <name>...              # pronunciation, sound-alikes, attractor, already used?
namegen claim <name> --profile <p> --role "<what it names>" --note "<why>"   # refuses attractors, rude or sound-alike names without --force
namegen avoid <name>...              # existing or rejected names, never offered again
```

`--project DIR` goes before the subcommand; by default it is the git root of the current directory. Project state lives in `<project>/.namegen/`: `NOTES.md` (naming rules for this world), `used.json`, `avoid.txt`, and optional project profiles in `profiles/`.

## Workflow

1. Run `namegen context` and read the project's lore for the thing being named.
   - If there is no `NOTES.md` yet, offer to write one: language and medium (spoken by TTS? translated?), register, existing names, which profiles fit.
   - If there is no avoid list yet, offer to add the project's existing invented names with `avoid`.
2. Pick 2 to 4 profiles that fit the register, and generate from each (`-n 60` to `-n 150`). When the user is unsure about the register, cast wide: several profiles, a shortlist from each, so they can compare sounds.
3. Shortlist 5 to 12 per slot **only from the printed candidates**. For each, give one line: why it fits (sound, meaning for `lexicon` glosses, how it reads aloud), plus any `sounds like` warning.
4. Allowed edits:
   - adding a generic English word (`Brask Station`, `the Treswin Gap`);
   - a one-letter spelling tweak, if you say so and re-run `check` on the result.

   Not allowed: blending two candidates, or "improving" a candidate into a new name.
5. When the user decides, `claim` it with a role and note. Names the user rejects go to `avoid`. If `claim` refuses a name, tell the user why; pass `--force` only when they still want it. Names that did not come from namegen (existing canon) use `--profile manual`.
6. Never reuse a seed across requests unless reproducing a list; the default seed is random.

If no profile fits, write a project profile in `<project>/.namegen/profiles/<name>.toml`. It can be:
- a `markov` corpus;
- a `lexifer` `.def`;
- WordNet `roots` for `lexicon`;
- a `template`.

The format is in the namegen README (`readlink -f $(which namegen)` leads to the repo). Generating from the new profile is still the source of the names.
