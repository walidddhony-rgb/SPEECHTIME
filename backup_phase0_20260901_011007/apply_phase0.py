#!/usr/bin/env python3
"""
SpeechScribe (SPEECHTIME) - Phase 0 patch tool
==============================================
1) Creates a full local backup of the project (backup_phase0_YYYYMMDD_HHMMSS/)
2) Rewrites every reference of the old repository
   walidddhony-rgb/SPEECHTIME  ->  walidddhony-rgb/SPEECHTIME
   in ALL text files (README.md, README_ar.md, CHANGELOG.md,
   CONTRIBUTING.md, docs/, and any .py/.toml/.json file that mentions it)
3) Prints a detailed report and verifies nothing is left behind

Run it ONCE from the project root:
    python apply_phase0.py
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

OLD_REPO = "walidddhony-rgb/SPEECHTIME"
NEW_REPO = "walidddhony-rgb/SPEECHTIME"
OLD_URL = "https://github.com/" + OLD_REPO
NEW_URL = "https://github.com/" + NEW_REPO

# Order matters: most specific patterns are applied first.
REPLACEMENTS = [
    (OLD_URL + ".git", NEW_URL + ".git"),
    (OLD_URL, NEW_URL),
    ("github.com/" + OLD_REPO, "github.com/" + NEW_REPO),
    (OLD_REPO, NEW_REPO),
    ("cd SPEECHTIME", "cd SPEECHTIME"),
]

TEXT_SUFFIXES = {".md", ".rst", ".toml", ".cfg", ".ini", ".txt",
                 ".py", ".yml", ".yaml", ".json", ".bib", ".spec"}

SKIP_DIRS = {".git", ".venv", "venv", "env", "ENV", "__pycache__",
             "build", "dist", ".pytest_cache", ".mypy_cache", ".ruff_cache",
             ".hypothesis", "htmlcov", ".tox", ".nox", "node_modules",
             ".idea", ".vscode", "Export", "exports", "results",
             "models", "logs", "temp", "tmp"}


def rewrite(text: str) -> tuple[str, int]:
    """Apply all link replacements; return (new_text, total_hits)."""
    hits = 0
    for old, new in REPLACEMENTS:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            hits += n
    return text, hits


def make_backup(root: Path) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dest = root / ("backup_phase0_" + stamp)
    ignore = shutil.ignore_patterns(*SKIP_DIRS, "backup_phase0_*")
    shutil.copytree(root, dest, dirs_exist_ok=True, ignore=ignore)
    return dest


def iter_text_files(root: Path, exclude: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if exclude in path.parents:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def main() -> int:
    root = Path.cwd()
    if not (root / "pyproject.toml").exists():
        print("ERROR: pyproject.toml not found - run this script from the project root.")
        return 1

    print("=" * 62)
    print("SpeechScribe (SPEECHTIME) - Phase 0: repository link fixes")
    print("=" * 62)

    print("\n[1/3] Creating backup ...")
    backup = make_backup(root)
    print("      OK -> ./" + backup.name)

    print("\n[2/3] Rewriting links ...")
    changed = {}
    for path in iter_text_files(root, exclude=backup):
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        new_text, hits = rewrite(original)
        if hits:
            path.write_text(new_text, encoding="utf-8")
            changed[str(path.relative_to(root)).replace("\\", "/")] = hits

    if changed:
        for p, n in sorted(changed.items()):
            print("      {:3d} replacement(s)  {}".format(n, p))
        print("      TOTAL: {} replacements in {} file(s)".format(
            sum(changed.values()), len(changed)))
    else:
        print("      No old references found (already patched?)")

    print("\n[3/3] Final verification ...")
    leftovers = []
    for path in iter_text_files(root, exclude=backup):
        try:
            if OLD_REPO in path.read_text(encoding="utf-8"):
                leftovers.append(str(path.relative_to(root)))
        except (UnicodeDecodeError, PermissionError):
            continue

    if not leftovers:
        print("      PASS: no 'walidddhony-rgb/SPEECHTIME' references remain.")
    else:
        print("      FAIL: old references still found - check manually:")
        for p in leftovers:
            print("        - " + p)

    print("\nNext steps:")
    print('  git grep -n "slam-prog"     # should print nothing')
    print("  git add -A")
    print('  git commit -m "fix: update all repository links to '
          'walidddhony-rgb/SPEECHTIME and extend .gitignore (closes #4)"')
    return 0 if not leftovers else 2


if __name__ == "__main__":
    sys.exit(main())
