"""Stage 2 machinery: keep the columns the recipe asks for, with tidy names.

You shouldn't need to edit this file. The exports and columns are in your recipe.
"""

import csv
from pathlib import Path

from . import recipes


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = ROOT / "output"


def csv_files(folder):
    """Every export CSV under a crawl folder, as paths relative to it."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*.csv")
                  if not path.stem.endswith("_preprocessed"))


def find_run_folder(recipe):
    """The newest crawl that has this recipe's first export."""
    kind, export, _ = recipe.EXPORTS[0]
    folders = sorted((p for p in OUTPUT_ROOT.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True) \
        if OUTPUT_ROOT.exists() else []
    for folder in folders:
        if recipes.find_export(kind, export, csv_files(folder)):
            return folder
    raise FileNotFoundError(f"No crawl under {OUTPUT_ROOT} has the export '{export}'. Run a crawl first.")


def check(folder, recipe, matched):
    """Fail before writing anything if a file or column is missing."""
    problems = []
    for (kind, export), file in matched.items():
        if file is None:
            problems.append(f"{export}: no matching file in {folder}. Was it exported, and did Screaming Frog accept it?")
    for kind, export, columns in recipe.EXPORTS:
        file = matched[(kind, export)]
        if file and columns:
            with (folder / file).open("r", encoding="utf-8-sig", newline="") as input_file:
                headers = next(csv.reader(input_file), [])
            missing = [column for column in columns if column not in headers]
            if missing:
                problems.append(f"{export} ({file}): columns not found: {missing}")
    if problems:
        raise ValueError("Cannot preprocess:\n  " + "\n  ".join(problems))


def preprocess_one(source, columns):
    destination = source.with_name(f"{source.stem}_preprocessed.csv")
    with source.open("r", encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file)
        with destination.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=columns.values())
            writer.writeheader()
            for row in reader:
                writer.writerow({output: row[column] for column, output in columns.items()})
    return destination


def run(settings, recipe, folder=None):
    """Preprocess every export in the recipe that has columns. Returns the crawl folder used."""
    folder = Path(folder) if folder else find_run_folder(recipe)
    matched = recipes.match_all(recipe, csv_files(folder))
    check(folder, recipe, matched)

    for kind, export, columns in recipe.EXPORTS:
        if not columns:
            continue
        source = folder / matched[(kind, export)]
        destination = preprocess_one(source, columns)
        print(f"Preprocessed {export}: {source.name} -> {destination.name}")
        if not settings.get("KEEP_ORIGINAL_FILES", True):
            source.unlink()
            print(f"Removed original export: {source}")
    return folder
