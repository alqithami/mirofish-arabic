from __future__ import annotations

import argparse
import shutil
from pathlib import Path

EXCLUDE_DIRS = {
    '.git', '.github', '.venv', 'venv', 'node_modules', 'dist', '__pycache__',
    '.pytest_cache', '.mypy_cache', '.ruff_cache', '.vite', 'logs', 'uploads'
}
EXCLUDE_FILES = {
    '.DS_Store',
}
EXCLUDE_SUFFIXES = {'.pyc', '.pyo', '.zip'}


def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = set(rel.parts)
    if parts & EXCLUDE_DIRS:
        return True
    if path.name in EXCLUDE_FILES:
        return True
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description='Create a clean release zip without local dependencies or caches.')
    parser.add_argument('--root', default='.', help='Repository root')
    parser.add_argument('--output', default='release/mirofish-arabic-release.zip', help='Output zip path')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    staging = output.with_suffix('')

    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    for path in root.rglob('*'):
        if should_skip(path, root):
            continue
        rel = path.relative_to(root)
        dest = staging / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)

    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    shutil.make_archive(str(output.with_suffix('')), 'zip', staging)
    shutil.rmtree(staging)
    print(output)


if __name__ == '__main__':
    main()
