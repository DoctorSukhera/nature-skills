from __future__ import annotations
from pathlib import Path
from hashlib import sha256
import re

TEXT_SUFFIXES = {'.md', '.txt', '.yaml', '.yml'}


def _read_limited(path: Path, limit: int) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='replace')[:limit]
    except Exception:
        return ''


def load_skill(root: Path, name: str) -> str | None:
    """Load a Nature Skill as an executable workflow bundle.

    v8 reads SKILL.md plus the small textual references actually shipped with the
    skill. This makes the repository materially useful instead of treating each
    skill as only a one-file prompt. Binary/static assets and scripts are not
    inlined into the model context.
    """
    d = root / 'skills' / name
    skill = d / 'SKILL.md'
    if not skill.exists():
        return None

    blocks = [f'### {name}/SKILL.md\n{_read_limited(skill, 45000)}']
    budget = 28000

    manifest = d / 'manifest.yaml'
    if manifest.exists() and budget > 0:
        txt = _read_limited(manifest, min(6000, budget))
        if txt:
            blocks.append(f'### {name}/manifest.yaml\n{txt}')
            budget -= len(txt)

    refs = d / 'references'
    if refs.exists() and budget > 0:
        # Prefer files explicitly named in SKILL.md, then fill with a few small refs.
        skill_text = blocks[0]
        candidates = [p for p in refs.rglob('*') if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES]
        named = []
        other = []
        for p in sorted(candidates):
            rel = p.relative_to(d).as_posix()
            if rel in skill_text or p.name in skill_text:
                named.append(p)
            else:
                other.append(p)
        selected = named + other[:3]
        seen = set()
        for p in selected:
            if budget <= 0 or p in seen:
                break
            seen.add(p)
            txt = _read_limited(p, min(9000, budget))
            if txt:
                blocks.append(f'### {name}/{p.relative_to(d).as_posix()}\n{txt}')
                budget -= len(txt)

    return '\n\n'.join(blocks)


def load_skills(root: Path, names: list[str]) -> dict[str, str | None]:
    return {name: load_skill(root, name) for name in names}


def combine_skills(skills: dict[str, str | None], names: list[str], global_limit: int = 170000) -> str:
    blocks = []
    used = 0
    for name in names:
        text = skills.get(name)
        if text:
            block = f'\n\n===== {name} WORKFLOW BUNDLE =====\n{text}'
            if used + len(block) > global_limit:
                block = block[:max(0, global_limit-used)]
            if block:
                blocks.append(block)
                used += len(block)
            if used >= global_limit:
                break
    return ''.join(blocks).strip()


def manifest(skills: dict[str, str | None]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, text in skills.items():
        if text:
            out[name] = sha256(text.encode('utf-8')).hexdigest()[:16]
    return out
