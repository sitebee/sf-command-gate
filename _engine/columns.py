"""Helper: print a column picker for any Screaming Frog export.

    python gate.py columns "Internal:All"
    python gate.py columns "Response Codes:Client Error (4xx)"

Prints a line to paste into TABS or BULK in your recipe, with every column
commented out. Take the # off the ones you want.

Columns come from your latest crawl in output/ if it has that export,
otherwise from the reference map (a real crawl, author's config).
"""

import csv
import difflib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from . import recipes


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = ROOT / "output"


def resolve(query, files, exports):
    """Turn an export name or file name into a file name, or None."""
    if query in exports:
        return exports[query]
    if query in files:
        return query
    wanted = recipes.squash(query.removesuffix(".csv"))
    for name in files:
        if recipes.squash(name.removesuffix(".csv")) == wanted:
            return name
    for export, name in exports.items():
        if recipes.squash(export) == wanted:
            return name
    # Same matching the recipes use, e.g. "Links:All Inlinks" -> all_inlinks.csv
    return recipes.find_export("tab", query, list(files)) or recipes.find_export("bulk", query, list(files))


def latest_header(file):
    """Header of this export in the newest crawl that has it, or (None, None)."""
    if not OUTPUT_ROOT.exists():
        return None, None
    found = list(OUTPUT_ROOT.rglob(file))
    if not found:
        return None, None
    newest = max(found, key=lambda path: path.stat().st_mtime)
    with newest.open(encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f), []), newest


def suggested_name(column, used):
    name = re.sub(r"[^a-z0-9]+", "_", column.lower()).strip("_") or "column"
    candidate, count = name, 2
    while candidate in used:
        candidate, count = f"{name}_{count}", count + 1
    used.add(candidate)
    return candidate


def show(query):
    if not query:
        print(__doc__)
        sys.exit(1)

    files = recipes.reference_columns()
    meta = recipes.reference_meta()
    exports = {export: file for file, (export, _) in meta.items() if export}
    file = resolve(query, files, exports)

    if not file:
        print(f"No export matches '{query}'.")
        close = difflib.get_close_matches(query, list(exports) + list(files), n=5, cutoff=0.5)
        if close:
            print("Closest:")
            for name in close:
                print(f"  {name}")
        sys.exit(1)

    columns, source = latest_header(file)
    origin = f"your crawl {source.parent.name}" if source else "the reference map"
    columns = columns or files[file]

    export, kind = meta[file]
    section = "BULK" if kind == "bulk" else "TABS"
    used = set()
    print(f"# Paste into {section} in your recipe. {len(columns)} columns from {origin}.")
    print(f'"{export or (query if ":" in query else file)}": {{')
    for column in columns:
        print(f"    # {json.dumps(column, ensure_ascii=False)}: {json.dumps(suggested_name(column, used))},")
    print("},")
