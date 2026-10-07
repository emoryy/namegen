# namegen

Procedural name candidates for worldbuilding, so that an LLM **curates** names instead of inventing them. LLMs collapse onto a handful of names (Elara, Elias, Pell, Veyl, Lantern...); here the randomness comes from corpora, phonology rules and WordNet, and the model only picks from the list.

## Install

```bash
git clone git@github.com:emoryy/namegen.git && cd namegen && ./install.sh
```

Needs `uv` and `node`. `install.sh` sets up the Python and Node dependencies and the NLTK data, links `~/.local/bin/namegen`, and links the Claude Code skill into `${CLAUDE_CONFIG_DIR:-~/.claude}/skills/namegen`. It is safe to re-run after a `git pull`.

## Usage

```bash
namegen context                               # project naming notes, claimed and avoided names
namegen profiles                              # list profiles
namegen gen anglo-hamlet -n 100               # candidates (random seed, printed in the header)
namegen gen lex-learned -n 60 --seed 42       # reproducible
namegen gen concord --starts-with ca --max-len 8
namegen check Veyra Hollin                    # pronunciation, sound-alikes, attractor and usage checks
namegen claim Brask --profile pit-and-pump --role "mining moon" --note "..."
namegen claim Hollin --profile manual --role "old capital" --force   # a name not from namegen, despite warnings
namegen avoid Veyra Hollin Pell               # never offer these in this project
namegen used                                  # claimed and avoided names
```

`--project DIR` selects the project (default: the git root of the current directory). Per-project state lives in `<project>/.namegen/`:

| File | What |
|---|---|
| `NOTES.md` | Naming rules of this world (medium, register, constraints); the skill reads it first |
| `used.json` | Claimed names with role, profile and note |
| `avoid.txt` | Names never to offer: existing ones and rejected ones |
| `profiles/*.toml` | Project profiles; they override global ones with the same name |

## Example session

A cold archipelago colony, named from scratch. All output below is real and reproducible with the given seed in a fresh project. Edits are cosmetic only: the project path is shortened, long glosses and repeated `check` lines are cut to `...`, and the two `bra` lists are printed on one line without their `sounds like` notes.

### One slot, several registers

Settler towns could sound Cornish, Highland or Finnish. Generating a short list from each lets the user hear the difference before choosing a register:

```console
$ namegen gen cornish-tin -n 8 --seed 2027
# cornish-tin (markov), seed 2027, project ~/worlds/demo
# 8 candidates from 64 raw; rejected: real place in a corpus 3, real English word 2, not English-pronounceable 1
Braddam
Woodacombe
Trencuke
Mevarah
Crosenford
Ennick   (sounds like: nick, eric, epic)
Sladra
Angoland

$ namegen gen highland -n 8 --seed 2026
# highland (markov), seed 2026, project ~/worlds/demo
# 8 candidates from 64 raw; rejected: real English word 4, real place in a corpus 3, not English-pronounceable 2, homophone of a common word 1
Litote
Fass   (sounds like: last, face, fast)
Keolas
Geoch   (sounds like: each, reach, beach)
Ardvasgo
Ioch   (sounds like: fuck, luck, suck)
Steinish   (sounds like: stylish)
Shipoll   (sounds like: nipple, ripple)

$ namegen gen finnic -n 8 --seed 2026
# finnic (markov), seed 2026, project ~/worlds/demo
# 8 candidates from 64 raw; rejected: real place in a corpus 1, not English-pronounceable 1
Tause   (sounds like: house, town, tower)
Reva   (sounds like: eva, raven, rave)
Taiskula
Aerukolda
Udraka
Krooki
Hoseva
Hamaki
```

The header says what the filters threw away: real places from the training corpus, real English words, exact homophones of common words, spellings an English reader would stumble on, LLM attractors and rude words. The `sounds like` notes are for the curator: `Ioch` and `Shipoll` pass the filters, but read aloud they are poor picks.

### Invented languages for peoples

Two `lexifer` phonologies for two very different peoples, a gentle trading folk and a mining camp, plus the learned Latinate `concord` register:

```console
$ namegen gen soft-harbour -n 8 --seed 2026
# soft-harbour (lexifer), seed 2026, project ~/worlds/demo
# 8 candidates from 64 raw; rejected: real English word 3, length 1
Monbow
Selo   (sounds like: self, sell, cell)
Dasow   (sounds like: das, paso)
Rilmen
Samola   (sounds like: samoa)
Talin   (sounds like: rollin, collin)
Minen   (sounds like: minute, mission, linen)
Misen   (sounds like: listen, mission, mason)

$ namegen gen pit-and-pump -n 8 --seed 2026
# pit-and-pump (lexifer), seed 2026, project ~/worlds/demo
# 8 candidates from 64 raw; rejected: real English word 4
Brugast
Krenuck
Stant   (sounds like: stand, stan, stance)
Dukast
Tuld   (sounds like: told, tailed, tully)
Tist   (sounds like: just, list, test)
Drock   (sounds like: rock, drop, iraq)
Brerk

$ namegen gen concord -n 8 --seed 2026
# concord (lexifer), seed 2026, project ~/worlds/demo
# 8 candidates from 64 raw; rejected: homophone of a common word 1
Vilent   (sounds like: violent, villain, villains)
Apintum   (sounds like: opinion)
Nenure
Sponence
Dariction   (sounds like: direction)
Celance   (sounds like: silence)
Bepanence
Pralary
```

### Real words with a meaning

`lexicon` profiles return rare real words from a WordNet field, with the gloss and the word frequency. Ship names, ores, institutions:

```console
$ namegen gen lex-instrument -n 5 --seed 2026
# lex-instrument (lexicon), seed 2026, project ~/worlds/demo
# 5 candidates from 98 raw; rejected: length 1
Gunsight [zipf 1.6] : a sight used for aiming a gun
Asdic [zipf 1.3] : a measuring instrument that sends out an acoustic pulse in water and measures distances in terms of the time for the echo of the pulse to return
Synchronizer [zipf 1.8] : an instrument that indicates whether two periodic motions are synchronous ...
Altimeter [zipf 2.5] : an instrument that measures the height above ground; used in navigation
Hygrometer [zipf 1.9] : measuring instrument for measuring the relative humidity of the atmosphere

$ namegen gen lex-mineral -n 5 --seed 2026
# lex-mineral (lexicon), seed 2026, project ~/worlds/demo
# 5 candidates from 168 raw; rejected: none
Rhinestone [zipf 2.6] : an imitation diamond made from rock crystal or glass or paste
Hematite [zipf 2.5] : the principal form of iron ore; consists of ferric oxide in crystalline form; occurs in a red earthy form
Girasol [zipf 1.1] : an opal with flaming orange and yellow and red colors
Chrysolite [zipf 1.1] : a brown or yellow-green olivine found in igneous and metamorphic rocks and used as a gemstone
Anorthite [zipf 1.1] : rare plagioclastic feldspar occurring in many igneous rocks
```

### Designations and acronyms

`template` builds catalogue numbers around generated names; `backronym` finds a real word that works as an acronym and writes its expansion:

```console
$ namegen gen survey-catalogue -n 6 --seed 2026
# survey-catalogue (template), seed 2026, project ~/worlds/demo
# 6 candidates from 12 raw; rejected: none
Larley 247
Blackton 630
Plumblack 115
Rowlhill-1706e
Luct-3544b
Abberford 34 III

$ namegen gen backronym-maintenance -n 5 --seed 2026
# backronym-maintenance (backronym), seed 2026, project ~/worlds/demo
# 5 candidates from 10 raw; rejected: none
HUCK = Hydraulic Upkeep and Civil Keeping
GORGE = General Orbital Reserve and Grade Execution
BALM = Bulk Abrasion Level Monitoring
WOOF = Works Order and Orbital Fulfilment
PASTE = Preventive Ambient Substrate and Thermal Execution
```

### Narrowing down

`--starts-with` steers the generator itself, not only a filter on its output, so a rare prefix still fills the list:

```console
$ namegen gen cornish-tin -n 6 --starts-with pol --seed 2026
# cornish-tin (markov), seed 2026, project ~/worlds/demo
# 6 candidates from 48 raw; rejected: real place in a corpus 3, real English word 2, not English-pronounceable 1
Polmarrow
Polletshop
Polbere   (sounds like: polar)
Polyphan   (sounds like: polygon)
Polbastant
Polkerrick
```

`--json` gives the same candidates with the pronunciation (ARPAbet), sound-alikes, gloss and frequency as fields, for scripts.

### What the skill does with it

The model never writes a name of its own. It reads the project notes, generates from the profiles that fit, and shortlists from the printed candidates with a reason for each. For the harbour town above, a shortlist could look like this:

| Candidate | Profile | Why |
|---|---|---|
| Braddam | cornish-tin | two plain syllables, no sound-alikes, reads like an old harbour |
| Crosenford | cornish-tin | an English *-ford* shape that is not a real place |
| Ardvasgo | highland | long and stately, reads unambiguously |
| Taiskula | finnic | clearly foreign, still easy for an English voice |
| Rilmen | soft-harbour | if the town should belong to the islanders instead of the settlers |

Allowed edits are adding a generic word (`Braddam Quay`) or a one-letter spelling change that is re-checked. Blending two candidates or "improving" one into a new name is not.

### Project memory

Claimed and avoided names shape every later run:

```console
$ namegen avoid Hollin Pell
added 2 name(s) to ~/worlds/demo/.namegen/avoid.txt

$ namegen claim Braddam --profile cornish-tin --role "harbour town" --note "two plain syllables, no sound-alikes"
claimed Braddam as harbour town in ~/worlds/demo/.namegen/used.json

$ namegen claim Braddon --profile cornish-tin --role "second town"
not claimed: Braddon: sounds like project name(s): Braddam (pass --force to claim anyway)

$ namegen claim Elara --profile manual --role "a moon"
not claimed: Elara: attractor 'elara' (pass --force to claim anyway)

$ namegen claim Kestrel --profile nonsense --role "a ship"
unknown profile: nonsense (see `namegen profiles`; use --profile manual for a name that did not come from namegen)
```

After the claim, generation drops names too close to `Braddam`. The same seed in an empty project and in this one:

```console
$ namegen gen cornish-tin -n 8 --starts-with bra --seed 2     # empty project
# 8 candidates from 64 raw; rejected: real place in a corpus 2, real English word 1, homophone of a common word 1
Braddon  Brazion  Bradworgan  Bradston  Braze  Brancott  Braddoc  Bradstock

$ namegen gen cornish-tin -n 8 --starts-with bra --seed 2     # after claiming Braddam
# 8 candidates from 64 raw; rejected: real place in a corpus 3, sounds like a project name 2, homophone of a common word 2, real English word 1
Brazion  Bradworgan  Bradston  Braze  Brancott  Bradstock  Bradforder  Bradda
```

`check` explains any single name:

```console
$ namegen check Elara Braddoc Brugast
Elara
  pronunciation: EH L AA R AH
  homophones: -; one phone away: lara
  English phonotactics: ok
  real word: real word (zipf 1.4)
  LLM attractor: attractor 'elara'
  rude: no
  used/avoided in demo: no
  sounds like a project name: no
Braddoc
  pronunciation: B R AE D AH K
  ...
  sounds like a project name: Braddam
Brugast
  pronunciation: B R AH G AH S T
  homophones: -; one phone away: -
  English phonotactics: ok
  real word: no
  LLM attractor: no
  rude: no
  used/avoided in demo: no
  sounds like a project name: no
```

### A project profile

When no built-in register fits, the project gets its own. A phonology for the native islanders (`.namegen/profiles/frost-tongue.def`):

```
C = k:3 s:3 v:2 t:2 n:2 r:2 h:1 l:2 j:1
V = i:4 e:4 a:3 u:2 y:1
F = n:3 s:2 r:1
words: CVCV:4 CVCVF:3 VCV:1 CVCVCV:2 CVF:1
reject: (..+)\1 ([aeiouy])\1 ^j[^aeiou] y[aeiou]
```

and a template that uses it for sea-chart labels (`island-chart.toml`):

```toml
engine = "template"
case = "keep"
patterns = ["{name} {feature}", "{feature} of {name}"]
[slots]
name = { profile = "frost-tongue" }
feature = ["Skerry", "Holm", "Sound", "Reach", "Shoals"]
```

```console
$ namegen gen frost-tongue -n 8 --seed 2026
# frost-tongue (lexifer), seed 2026, project ~/worlds/demo
# 8 candidates from 64 raw; rejected: length 3
Niku   (sounds like: nick, nikki, knicks)
Jiti   (sounds like: bt, genie, gigi)
Taku   (sounds like: taco)
Kesyr   (sounds like: lesser, keller, kessler)
Nase   (sounds like: days, name, news)
Hiru   (sounds like: hero)
Tusi   (sounds like: lucy, juicy, lucie)
Vike   (sounds like: like, via, mike)

$ namegen gen island-chart -n 6 --seed 2026
# island-chart (template), seed 2026, project ~/worlds/demo
# 6 candidates from 12 raw; rejected: none
Kesyr Holm
Sini Skerry
Sound of Setiru
Tiri Reach
Shoals of Tusi
Vike Reach
```

## Engines

| Engine | Source | Output |
|---|---|---|
| `markov` | Character Markov chain (`@ksilvennoinen/markov-namegen`, Katz back-off) trained on a corpus in `corpora/` | New words in the style of the corpus |
| `lexifer` | Phonology rules in a `.def` file next to the profile ([Lexifer](https://github.com/bbrk24/lexifer-ts), [grammar](https://github.com/bbrk24/lexifer-ts/blob/master/docs/grammar.md)) | Words of an invented language |
| `lexicon` | WordNet: every single word under the profile's root synsets (hyponyms and topic-domain members), filtered by `wordfreq` Zipf range | Rare but real English words, with a gloss |
| `template` | Patterns with slots filled from lists, files or other profiles | Designations such as `Hurstown 418 c` |
| `backronym` | An acronym word from another profile plus an expansion from vocabulary lists | `SILT = Surface Integrity and Lifecycle Tending` |

## Filters

Applied to `markov` and `lexifer` output by default (override in a profile's `[filters]` table):

- `phonotactics`: rejects onsets, codas, clusters and vowel runs an English reader would stumble on.
- `max_zipf` (default 2.5): rejects real English words.
- `reject_corpus_words`: rejects names that exist verbatim in any corpus (real places).
- `sound_check`: rejects exact homophones of common words (Zipf >= 3, CMUdict), and annotates near misses one phone away (`Veyra` sounds like `vera`). Pronunciation of new words comes from `g2p_en`.
- `profanity` (default true, all engines): rejects rude whole words (`data/profanity-words.txt`, so acronyms like `TURD` too); for invented words also rude stems anywhere (`data/profanity-stems.txt`) and pronunciations equal to a rude word or one phone from a rude word of 4+ phones. Known English words (Zipf >= 1.5) are judged by the whole-word list only, so `slate` or `wristwatch` stay allowed.
- `project_sound` (default true, all engines): rejects candidates with a word that sounds the same as, or one phone away from, a distinctive word of a claimed or avoided name (`Tregone` after `Tregon` is claimed, `Keythley 923 b` after `Keythley 845`).
- `allow_attractors` (default false): rejects LLM attractors from `data/attractors.txt` (generated by `scripts/build_attractors.py` from naming experiments), `data/blacklist.txt` and the stem regexes in `data/blacklist-patterns.txt`.

When filters or `--starts-with` reject most of a batch, `gen` draws further batches (up to 6) until it has `n` names or a batch brings nothing new. `--starts-with` is also passed to the Markov generator itself. The header counts every rejection by reason, including backronym acronyms that no expansion fits.

`claim` refuses unknown profiles (use `--profile manual` for names that did not come from namegen) and names that are LLM attractors, rude, or sound like a project name, unless `--force` is given. `check` reports the same.

Lexicon candidates show their word frequency (`[zipf 2.8]`): above about 3 a word is common enough that readers will take it as the everyday word.

## Profile format

```toml
description = "One line shown by `namegen profiles`"
projects = ["moons-of-september"]   # informational
engine = "markov"                   # markov | lexifer | lexicon | template | backronym
corpus = "england-hamlets.txt"      # markov: file(s) in corpora/
order = 3                           # markov: model order
min_len = 4
max_len = 9
case = "title"                      # title | upper | lower | keep

# lexicon
roots = ["fabric.n.01", "needlework.n.01"]
exclude_roots = []
zipf_min = 1.0
zipf_max = 3.8
primary_sense = true                # keep a word only if its most common sense is inside the field

[filters]
max_zipf = 2.5
```

A `lexifer` profile reads `<profile>.def` next to the `.toml`. See `profiles/` for template and backronym examples.

## Rebuilding data

- Corpora: `scripts/build_corpora.py` (download instructions inside).
- Attractor list: `scripts/build_attractors.py <dir with naming-experiment JSONs>`.

## Data and licences

- Place-name corpora: [GeoNames](https://www.geonames.org) (CC-BY 4.0).
- WordNet 3.0 (Princeton WordNet licence) via NLTK; CMUdict (BSD); `wordfreq` (Apache-2.0 code, CC-BY-SA data).
- Lexifer TS and markov-namegen: MIT.
- namegen itself: MIT, see `LICENSE`.
