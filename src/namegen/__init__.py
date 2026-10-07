"""namegen: procedural name candidates for worldbuilding, so an LLM curates instead of inventing."""

import argparse
import json
import os
import sys

from . import paths  # noqa: F401  (sets NLTK_DATA before nltk is imported)
from . import filters
from .core import Generator
from .profiles import load_all
from .store import ProjectStore


def _format(c):
    parts = [c["name"]]
    if "expansion" in c:
        parts.append(f"= {c['expansion']}")
    if "gloss" in c:
        parts.append(f": {c['gloss']}")
    if c.get("sounds_like"):
        parts.append(f"  (sounds like: {', '.join(c['sounds_like'])})")
    return " ".join(parts)


def cmd_gen(args):
    root = paths.project_root(args.project)
    seed = args.seed if args.seed is not None else int.from_bytes(os.urandom(4), "big")
    gen = Generator(root, ProjectStore(root), seed)
    opts = {"min_len": args.min_len, "max_len": args.max_len, "starts_with": args.starts_with}
    out = gen.generate(args.profile, args.n, opts)
    if args.json:
        print(json.dumps({"stats": gen.stats, "project": str(root), "candidates": out}, ensure_ascii=False, indent=1))
        return
    s = gen.stats
    rej = ", ".join(f"{k} {v}" for k, v in sorted(s["rejected"].items(), key=lambda kv: -kv[1])) or "none"
    print(f"# {s['profile']} ({s['engine']}), seed {s['seed']}, project {root}")
    print(f"# {s['accepted']} candidates from {s['raw']} raw; rejected: {rej}")
    for c in out:
        print(_format(c))


def cmd_check(args):
    root = paths.project_root(args.project)
    taken = ProjectStore(root).taken()
    for name in args.names:
        key = name.lower()
        pron, exact, near = filters.sounds_like(name)
        print(f"{name}")
        print(f"  pronunciation: {' '.join(pron)}")
        print(f"  homophones: {', '.join(exact) or '-'}; one phone away: {', '.join(near[:8]) or '-'}")
        print(f"  English phonotactics: {filters.english_phonotactics(key) or 'ok'}")
        print(f"  real word: {filters.real_word(key, 0.0) or 'no'}")
        print(f"  LLM attractor: {filters.attractor_hit(key) or 'no'}")
        print(f"  used/avoided in {root.name}: {'yes' if key in taken else 'no'}")


def cmd_claim(args):
    root = paths.project_root(args.project)
    ProjectStore(root).claim(args.name, args.profile, args.role, args.note)
    print(f"claimed {args.name} as {args.role} in {root}/.namegen/used.json")


def cmd_avoid(args):
    root = paths.project_root(args.project)
    new = ProjectStore(root).add_avoid(args.names)
    print(f"added {len(new)} name(s) to {root}/.namegen/avoid.txt")


def cmd_used(args):
    root = paths.project_root(args.project)
    store = ProjectStore(root)
    for e in store.used():
        print(f"{e['name']}\t{e['role']}\t{e['profile']}\t{e['date']}\t{e.get('note') or ''}")
    avoid = store.avoid()
    if avoid:
        print(f"# avoid list: {', '.join(avoid)}")


def cmd_context(args):
    root = paths.project_root(args.project)
    store = ProjectStore(root)
    print(f"# project: {root}")
    notes = store.notes()
    print(notes.rstrip() if notes else f"# no naming notes yet ({store.notes_path})")
    print()
    cmd_used(args)


def cmd_profiles(args):
    root = paths.project_root(args.project)
    for name, p in sorted(load_all(root).items()):
        tags = ",".join(p.get("projects", []))
        print(f"{name:22} {p['engine']:9} {p.get('description', '')}{f'  [{tags}]' if tags else ''}")


def main():
    ap = argparse.ArgumentParser(prog="namegen", description=__doc__)
    ap.add_argument("--project", help="project root holding .namegen/ (default: git root of cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gen", help="generate candidates from a profile")
    g.add_argument("profile")
    g.add_argument("-n", type=int, default=100)
    g.add_argument("--seed", type=int)
    g.add_argument("--min-len", type=int)
    g.add_argument("--max-len", type=int)
    g.add_argument("--starts-with")
    g.add_argument("--json", action="store_true")
    g.set_defaults(func=cmd_gen)

    c = sub.add_parser("check", help="pronunciation, sound-alikes, attractor and usage check for given names")
    c.add_argument("names", nargs="+")
    c.set_defaults(func=cmd_check)

    cl = sub.add_parser("claim", help="record a chosen name in the project")
    cl.add_argument("name")
    cl.add_argument("--profile", required=True)
    cl.add_argument("--role", required=True, help="what the name is for, e.g. 'gas giant'")
    cl.add_argument("--note")
    cl.set_defaults(func=cmd_claim)

    av = sub.add_parser("avoid", help="add names the project must never be offered (existing or rejected)")
    av.add_argument("names", nargs="+")
    av.set_defaults(func=cmd_avoid)

    sub.add_parser("used", help="list claimed and avoided names").set_defaults(func=cmd_used)
    sub.add_parser("context", help="project naming notes plus claimed and avoided names").set_defaults(func=cmd_context)
    sub.add_parser("profiles", help="list profiles").set_defaults(func=cmd_profiles)

    args = ap.parse_args()
    try:
        args.func(args)
    except ValueError as e:
        sys.exit(str(e))
