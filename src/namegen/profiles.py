import tomllib

from .paths import PROFILES


def profile_dirs(project):
    dirs = [PROFILES]
    if project is not None:
        dirs.append(project / ".namegen" / "profiles")
    return [d for d in dirs if d.is_dir()]


def load_all(project=None):
    """Project profiles override global ones with the same name."""
    out = {}
    for d in profile_dirs(project):
        for f in sorted(d.glob("*.toml")):
            p = tomllib.loads(f.read_text(encoding="utf-8"))
            p["name"] = f.stem
            p["_path"] = f
            out[f.stem] = p
    return out


def load(name, project=None):
    profiles = load_all(project)
    if name not in profiles:
        raise SystemExit(f"unknown profile: {name} (see `namegen profiles`)")
    return profiles[name]
