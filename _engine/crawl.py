"""Stage 1 machinery: build, check, show and run the Screaming Frog command.

You shouldn't need to edit this file. The options are in gate.py.
"""

import difflib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import recipes


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FOLDER = ROOT / "output"
LOG_FOLDER = ROOT / "logs"

DEFAULT_EXECUTABLE = {
    "win32": r"C:\Program Files (x86)\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe",
    "darwin": "/Applications/Screaming Frog SEO Spider.app/Contents/MacOS/ScreamingFrogSEOSpiderLauncher",
}.get(sys.platform, "screamingfrogseospider")


class CrawlFailed(RuntimeError):
    pass


def joined(flag, items):
    """['--flag', 'a,b,c'] from a list, or nothing if the list is empty."""
    return [flag, ",".join(items)] if items else []


def build_command(settings, recipe):
    """The options in gate.py, plus the exports from the recipe."""
    return [
        settings.get("SCREAMING_FROG") or DEFAULT_EXECUTABLE,
        *settings["CRAWL"],
        *settings["APIS"],
        *joined("--export-tabs", recipe.EXPORT_TABS),
        *joined("--bulk-export", recipe.BULK_EXPORTS),
        "--export-format", "csv",
        "--output-folder", str(OUTPUT_FOLDER),
    ]


def unknown_exports(label, items, listing):
    """Problems for any export name the CLI doesn't accept, with a closest-match suggestion."""
    valid = recipes.valid_names(listing)
    if valid is None:
        return []  # no reference list: Screaming Frog will validate at startup
    problems = []
    for item in items:
        if item not in valid:
            close = difflib.get_close_matches(item, sorted(valid), n=1, cutoff=0.6)
            hint = f" Did you mean '{close[0]}'?" if close else ""
            problems.append(f"{label}: '{item}' is not a valid export name.{hint}")
    return problems


def value_after(command, flag):
    return command[command.index(flag) + 1] if flag in command and command.index(flag) + 1 < len(command) else None


def check(command, recipe):
    """Return a list of plain-English problems. Empty list means good to go."""
    problems = []
    problems += unknown_exports(f"{recipe.NAME} TABS", recipe.EXPORT_TABS, "export-tabs.txt")
    problems += unknown_exports(f"{recipe.NAME} BULK", recipe.BULK_EXPORTS, "bulk-exports.txt")

    actions = [flag for flag in ("--crawl", "--crawl-list") if flag in command]
    if len(actions) != 1:
        problems.append(f"Choose exactly ONE action in gate.py: --crawl or --crawl-list (currently {len(actions)} switched on).")

    organisation = [flag for flag in ("--timestamped-output", "--overwrite") if flag in command]
    if len(organisation) != 1:
        problems.append(f"Choose exactly ONE of --timestamped-output or --overwrite in gate.py (currently {len(organisation)} switched on).")

    config = value_after(command, "--config")
    if "--config" in command and not (config and Path(config).exists()):
        problems.append(f"Config file not found: {config}")

    url_list = value_after(command, "--crawl-list")
    if "--crawl-list" in command and not (url_list and Path(url_list).exists() and Path(url_list).read_text().strip()):
        problems.append(f"URL list is missing or empty: {url_list}")

    for flag in recipes.api_flags(recipe):
        if flag not in command:
            problems.append(f"Recipe '{recipe.NAME}' needs {flag}. Switch it on in APIS in gate.py.")

    executable = command[0]
    if Path(executable).is_absolute() and not Path(executable).exists():
        problems.append(f"Screaming Frog not found: {executable}. Set SCREAMING_FROG in gate.py.")

    return problems


def show(command):
    """Print the command with one flag per line so it reads like a recipe."""
    quote = lambda text: f'"{text}"' if " " in text else text
    lines = [quote(command[0])]
    for token in command[1:]:
        if token.startswith("--"):
            lines.append("  " + token)
        else:
            lines[-1] += " " + quote(token)
    print("\n".join(lines))


def run_folders():
    return {p for p in OUTPUT_FOLDER.iterdir() if p.is_dir()} if OUTPUT_FOLDER.exists() else set()


class CrawlResult:
    """What the crawl stage hands on: where the crawl went, its log, and (if profiling) the live samples."""

    def __init__(self, folder, log_path, sampler=None):
        self.folder, self.log_path, self.sampler = folder, log_path, sampler


def run(command, profile_interval=None):
    """Run the crawl. Returns a CrawlResult (folder is None if the new crawl folder can't be told apart).

    Give profile_interval (seconds) to sample CPU, RAM and connections while it runs.
    """
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    LOG_FOLDER.mkdir(exist_ok=True)
    log_path = LOG_FOLDER / f"screaming-frog-{datetime.now():%Y%m%d-%H%M%S}.log"
    before = run_folders()

    print(f"\nCrawling... detailed output: {log_path}", flush=True)
    sampler = None
    with log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(command, stdout=log_file, stderr=subprocess.STDOUT)
        if profile_interval:
            from . import profiler
            if not profiler.supported():
                pass   # the profile stage explains this, so the crawl itself carries on untouched
            elif profiler.available():
                sampler = profiler.Sampler(process.pid, profile_interval)
                sampler.start()
                print(f"Profiling: sampling resources every {profile_interval}s.", flush=True)
            else:
                print("Profiling: psutil isn't installed, so no live CPU, RAM or connection samples. Install it with: pip install psutil", flush=True)
        returncode = process.wait()
        if sampler:
            sampler.stop()
            sampler.join(timeout=10)

    if returncode != 0:
        tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-15:])
        raise CrawlFailed(f"Screaming Frog failed (exit code {returncode}). Last lines of the log:\n{tail}")

    print("Crawl complete.")
    new = run_folders() - before
    return CrawlResult(new.pop() if len(new) == 1 else None, log_path, sampler)
