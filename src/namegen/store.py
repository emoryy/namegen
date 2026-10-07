"""Per-project state in <project>/.namegen/: used.json (claimed names), avoid.txt (never propose) and NOTES.md (naming rules)."""

import datetime
import json


class ProjectStore:
    def __init__(self, root):
        self.root = root
        self.dir = root / ".namegen"
        self.used_path = self.dir / "used.json"
        self.avoid_path = self.dir / "avoid.txt"
        self.notes_path = self.dir / "NOTES.md"

    def notes(self):
        return self.notes_path.read_text(encoding="utf-8") if self.notes_path.exists() else None

    def used(self):
        if not self.used_path.exists():
            return []
        return json.loads(self.used_path.read_text(encoding="utf-8"))

    def avoid(self):
        if not self.avoid_path.exists():
            return []
        lines = self.avoid_path.read_text(encoding="utf-8").splitlines()
        return [l.strip() for l in lines if l.strip() and not l.startswith("#")]

    def taken_names(self):
        return [e["name"] for e in self.used()] + self.avoid()

    def taken(self):
        return {n.lower() for n in self.taken_names()}

    def claim(self, name, profile, role, note):
        entries = self.used()
        if any(e["name"].lower() == name.lower() for e in entries):
            raise ValueError(f"{name} is already claimed in {self.used_path}")
        entries.append({
            "name": name,
            "profile": profile,
            "role": role,
            "note": note,
            "date": datetime.date.today().isoformat(),
        })
        self.dir.mkdir(exist_ok=True)
        self.used_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def add_avoid(self, names):
        self.dir.mkdir(exist_ok=True)
        current = set(n.lower() for n in self.avoid())
        new = [n for n in names if n.lower() not in current]
        if not self.avoid_path.exists():
            self.avoid_path.write_text("# Names the generator must never propose (existing or rejected names).\n")
        with open(self.avoid_path, "a", encoding="utf-8") as f:
            for n in new:
                f.write(n + "\n")
        return new
