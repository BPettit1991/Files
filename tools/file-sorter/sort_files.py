"""Sort the files in one folder into subfolders.

Dry run by default. Pass --apply to move the files.

Examples:
  python sort_files.py ~/Downloads                 # preview, group by type
  python sort_files.py ~/Downloads --apply         # move files by type
  python sort_files.py ~/Photos --by date --apply  # move into YYYY/MM folders
"""

from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sys
from pathlib import Path

CATEGORIES: dict[str, set[str]] = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic", ".tif", ".tiff"},
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".pages"},
    "Spreadsheets": {".xls", ".xlsx", ".ods", ".csv", ".numbers"},
    "Presentations": {".ppt", ".pptx", ".odp", ".key"},
    "Audio": {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"},
    "Video": {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".webm"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".iso"},
    "Code": {".py", ".cs", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yml", ".yaml", ".sh", ".ps1"},
    "Installers": {".exe", ".msi", ".dmg", ".pkg", ".deb", ".appx", ".msix"},
}
OTHER = "Other"


def category_for(path: Path) -> str:
    suffix = path.suffix.lower()
    for name, suffixes in CATEGORIES.items():
        if suffix in suffixes:
            return name
    return OTHER


def destination_folder(path: Path, mode: str) -> Path:
    if mode == "date":
        modified = dt.datetime.fromtimestamp(path.stat().st_mtime)
        return Path(f"{modified:%Y}") / f"{modified:%m}"
    return Path(category_for(path))


def unique_target(target: Path, reserved: set[Path]) -> Path:
    candidate = target
    counter = 1
    while candidate.exists() or candidate in reserved:
        candidate = target.with_name(f"{target.stem} ({counter}){target.suffix}")
        counter += 1
    return candidate


def plan_moves(root: Path, mode: str) -> list[tuple[Path, Path]]:
    moves: list[tuple[Path, Path]] = []
    reserved: set[Path] = set()
    for item in sorted(root.iterdir()):
        if not item.is_file() or item.name.startswith("."):
            continue
        target_dir = root / destination_folder(item, mode)
        target = unique_target(target_dir / item.name, reserved)
        reserved.add(target)
        moves.append((item, target))
    return moves


def main() -> int:
    parser = argparse.ArgumentParser(description="Sort files in a folder into subfolders.")
    parser.add_argument("folder", type=Path, help="Folder whose top-level files should be sorted.")
    parser.add_argument("--by", choices=["type", "date"], default="type", help="Grouping rule (default: type).")
    parser.add_argument("--apply", action="store_true", help="Move the files. Without this flag, only preview.")
    args = parser.parse_args()

    root = args.folder.expanduser().resolve()
    if not root.is_dir():
        print(f"Not a folder: {root}", file=sys.stderr)
        return 1

    moves = plan_moves(root, args.by)
    if not moves:
        print("No files to sort.")
        return 0

    for source, target in moves:
        print(f"{source.name} -> {target.relative_to(root)}")

    if not args.apply:
        print(f"\nDry run: {len(moves)} file(s). Re-run with --apply to move them.")
        return 0

    for source, target in moves:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
    print(f"\nMoved {len(moves)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
