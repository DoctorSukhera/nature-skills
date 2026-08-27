from __future__ import annotations
from pathlib import Path
from hashlib import sha256


def load_skill(root: Path, name: str) -> str | None:
    path = root / "skills" / name / "SKILL.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def load_skills(root: Path, names: list[str]) -> dict[str, str | None]:
    return {name: load_skill(root, name) for name in names}


def combine_skills(skills: dict[str, str | None], names: list[str]) -> str:
    blocks = []
    for name in names:
        text = skills.get(name)
        if text:
            blocks.append(f"\n\n===== {name} =====\n{text}")
    return "".join(blocks).strip()


def manifest(skills: dict[str, str | None]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, text in skills.items():
        if text:
            out[name] = sha256(text.encode("utf-8")).hexdigest()[:16]
    return out
