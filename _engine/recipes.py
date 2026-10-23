"""Recipes: loading them, matching export names to files, and checking them.

You shouldn't need to edit this file. Recipes live in the recipes/ folder.
"""

import csv
import importlib.util
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RECIPES_FOLDER = ROOT / "recipes"
REFERENCE_FOLDER = Path(__file__).resolve().parent / "reference"


def available():
    """Recipe names, ignoring files that start with an underscore (template and shared parts)."""
    return sorted(path.stem for path in RECIPES_FOLDER.glob("*.py") if not path.name.startswith("_"))


def load(name):
    """Load a recipe file and return it as a module with these filled in:

    NAME, DESCRIPTION, REQUIRES     about the recipe
    TABS, BULK                      {export name: columns to keep} as written in the file
    EXPORT_TABS, BULK_EXPORTS       just the names, for --export-tabs and --bulk-export
    EXPORTS                         [(kind, name, columns)] for every export, tabs first
    """
    path = RECIPES_FOLDER / f"{name}.py"
    if name.startswith("_") or not path.exists():
        sys.exit(f"Recipe '{name}' not found. Available: {', '.join(available()) or 'none'}")

    sys.path.insert(0, str(RECIPES_FOLDER))  # lets recipes use: from _shared import ...
    try:
        spec = importlib.util.spec_from_file_location(f"recipe_{name.replace('-', '_')}", path)
        recipe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recipe)
    finally:
        sys.path.remove(str(RECIPES_FOLDER))

    recipe.NAME = name
    recipe.DESCRIPTION = getattr(recipe, "DESCRIPTION", "")
    recipe.REQUIRES = getattr(recipe, "REQUIRES", [])
    recipe.TABS = getattr(recipe, "TABS", {})
    recipe.BULK = getattr(recipe, "BULK", {})
    recipe.EXPORT_TABS = list(recipe.TABS)
    recipe.BULK_EXPORTS = list(recipe.BULK)
    recipe.EXPORTS = [("tab", export, columns) for export, columns in recipe.TABS.items()] + \
                     [("bulk", export, columns) for export, columns in recipe.BULK.items()]

    problems = []
    if not recipe.EXPORTS:
        problems.append("it exports nothing (TABS and BULK are both empty)")
    for kind, export, columns in recipe.EXPORTS:
        if columns is not None and not isinstance(columns, dict):
            problems.append(f"{export}: columns must be a {{...}} dictionary (or None to export without preprocessing)")
    if problems:
        sys.exit(f"Recipe '{name}' has a problem: " + "; ".join(problems))

    return recipe


def api_flags(recipe):
    """The API switches a recipe needs, e.g. ['--use-pagespeed']. Other REQUIRES entries are notes."""
    return [item.split()[0] for item in recipe.REQUIRES if item.startswith("--use-")]


def describe(recipe):
    """Short summary for the top of a run."""
    line = f"Recipe: {recipe.NAME}"
    if recipe.DESCRIPTION:
        line += f" - {recipe.DESCRIPTION}"
    line += f"\n        {len(recipe.TABS)} tab exports, {len(recipe.BULK)} bulk exports"
    if recipe.REQUIRES:
        line += f"\n        Needs: {', '.join(recipe.REQUIRES)} (must be enabled in your Screaming Frog config)"
    return line


# ============================================================
# Matching an export name to the CSV file Screaming Frog wrote
# ============================================================

def squash(text):
    """Compare names ignoring case, punctuation and threshold numbers.

    Screaming Frog writes the threshold into the file name: "Over X Characters" becomes
    over_60_characters.csv. So a standalone X, and standalone numbers, are ignored.
    Numbers that belong to a word stay (h1, h2, 4xx, 5xx, Non-200), and so does X-Default.
    """
    text = text.lower()
    text = re.sub(r"(?<![a-z0-9-])x(?![a-z0-9-])", "", text)
    text = re.sub(r"(?<![a-z0-9-])\d+(?![a-z0-9-])", "", text)
    return re.sub(r"[^a-z0-9]", "", text)


# Exports whose file name can't be worked out from the export name.
# Issues:All writes issues_overview_report.csv, plus a copy of each issue's URL list in issues_reports/.
FILE_ALIASES = {
    ("bulk", "Issues:All"): "issuesoverviewreport",
}


def find_export(kind, export, files, taken=()):
    """Which file is this export? Returns a file from `files`, or None.

    Tab exports match on the full name:   Page Titles:Missing     -> page_titles_missing.csv
    Bulk exports keep the group name sometimes and drop it other times, so both are tried:
        Links:All Inlinks     -> all_inlinks.csv
        H1:All Inlinks        -> h1_all_inlinks.csv
    Files already claimed by another export are skipped, and if two files match equally
    well (same folder depth), nothing is returned rather than guessing.
    """
    keys = [FILE_ALIASES.get((kind, export)) or squash(export)]
    if kind == "bulk" and (kind, export) not in FILE_ALIASES:
        keys.append(squash(export.rpartition(":")[2]))
        # some bulk exports are written with a "_report" ending, e.g. exact_duplicates_report.csv
        keys += [key + ending for key in list(keys) for ending in ("report", "detailedreport")]

    for key in keys:
        hits = [f for f in files if f not in taken and squash(Path(f).stem) == key]
        if hits:
            shallowest = min(len(Path(f).parts) for f in hits)
            hits = [f for f in hits if len(Path(f).parts) == shallowest]
            return hits[0] if len(hits) == 1 else None
    return None


def match_all(recipe, files):
    """{(kind, export): file or None} for a recipe. Tab exports claim their files first."""
    taken, matched = set(), {}
    for kind, export, _ in recipe.EXPORTS:
        found = find_export(kind, export, files, taken)
        matched[(kind, export)] = found
        if found:
            taken.add(found)
    return matched


# ============================================================
# Reference data and checking (python gate.py check)
# ============================================================

def reference_columns():
    """{file name: [columns]} from the reference map."""
    path = REFERENCE_FOLDER / "export-columns.csv"
    if not path.exists():
        sys.exit(f"Missing {path}")
    files = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            files.setdefault(row["file"], []).append(row["column"])
    return files


def reference_meta():
    """{file name: (export name, 'tab' or 'bulk')} from the reference map."""
    meta = {}
    with (REFERENCE_FOLDER / "export-columns.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            meta[row["file"]] = (row["export"], row["type"])
    return meta


def valid_names(listing):
    """Export names the CLI accepts ('export-tabs.txt' or 'bulk-exports.txt'), or None if the list is missing."""
    path = REFERENCE_FOLDER / listing
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()} if path.exists() else None


def check_recipe(recipe, known_files):
    """Plain-English problems for one recipe, checked against the reference (no crawl needed)."""
    problems = []
    valid = {"tab": valid_names("export-tabs.txt"), "bulk": valid_names("bulk-exports.txt")}
    matched = match_all(recipe, list(known_files))

    for kind, export, columns in recipe.EXPORTS:
        label = f"{'TABS' if kind == 'tab' else 'BULK'}['{export}']"
        if valid[kind] is not None and export not in valid[kind]:
            problems.append(f"{label}: not a valid {'--export-tabs' if kind == 'tab' else '--bulk-export'} name")
            continue
        file = matched[(kind, export)]
        if not file:
            problems.append(f"{label}: no matching file in the column map, so its columns can't be checked")
            continue
        if columns:
            missing = [column for column in columns if column not in known_files[file]]
            if missing:
                problems.append(f"{label} ({file}): columns not in this export: {missing}")
    return problems


def check_all(names):
    """Print OK/FAIL for each recipe. Returns True if every recipe passed."""
    known_files = reference_columns()
    failed = 0
    for name in names or available():
        problems = check_recipe(load(name), known_files)
        print(f"{'OK  ' if not problems else 'FAIL'} {name}")
        for problem in problems:
            print(f"       - {problem}")
        failed += bool(problems)
    return not failed


def list_recipes(active):
    print(f"Active: {active}\n")
    for name in available():
        recipe = load(name)
        print(f"  {name:<26} {len(recipe.TABS):>3} tabs {len(recipe.BULK):>3} bulk   {recipe.DESCRIPTION}")


def new_recipe(name):
    target = RECIPES_FOLDER / f"{name}.py"
    if target.exists():
        sys.exit(f"{target.name} already exists.")
    shutil.copy(RECIPES_FOLDER / "_template.py", target)
    print(f"Created {target}\nSet RECIPE = \"{name}\" in gate.py, or run:  python gate.py --recipe {name}")
