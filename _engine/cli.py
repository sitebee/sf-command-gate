"""The command line behind gate.py. You shouldn't need to edit this file.

    python gate.py                       run the stages in gate.py
    python gate.py --dry-run             check and print the command, run nothing
    python gate.py --recipe on-page      use a different recipe for this run
    python gate.py preprocess analyse    run only these stages, on the newest crawl
    python gate.py profile               resource report for the newest crawl (see section 7 in gate.py)
    python gate.py changes               what changed since the previous crawl (section 8 in gate.py)
    python gate.py changes --against X   compare with a specific earlier crawl folder instead
    python gate.py --folder output/X     run the later stages on a specific crawl

    python gate.py recipes               list recipes
    python gate.py check [name]          check recipes against the reference (no crawl)
    python gate.py new my-recipe         start your own recipe
    python gate.py columns "Internal:All"   print a column picker for an export
"""

import sys

from . import analyse, changes, columns, crawl, preprocess, recipes

STAGE_NAMES = ["crawl", "profile", "preprocess", "analyse", "changes"]


def take_option(args, name):
    """Remove '--name value' from args and return the value (or None)."""
    if name not in args:
        return None
    position = args.index(name)
    if position + 1 >= len(args):
        sys.exit(f"{name} needs a value.")
    value = args[position + 1]
    del args[position:position + 2]
    return value


def take_flag(args, name):
    if name in args:
        args.remove(name)
        return True
    return False


def pipeline(settings, recipe_name, stages, folder, dry_run, against=None):
    recipe = recipes.load(recipe_name)
    print(recipes.describe(recipe), end="\n\n")

    command = None
    if "crawl" in stages or dry_run:
        command = crawl.build_command(settings, recipe)
        problems = crawl.check(command, recipe)
        if problems:
            print("Cannot run yet:")
            for problem in problems:
                print(f"  - {problem}")
            sys.exit(1)
        crawl.show(command)

    if dry_run:
        print(f"\nDry run: all checks passed, nothing was executed. Stages: {', '.join(stages)}")
        return

    run_folder = folder
    crawl_result = None
    for stage in stages:
        print(f"\n=== {stage} ===", flush=True)
        try:
            if stage == "crawl":
                interval = settings.get("PROFILE_INTERVAL", 1.0) if "profile" in stages else None
                crawl_result = crawl.run(command, interval)
                run_folder = crawl_result.folder or run_folder
            elif stage == "profile":
                from . import profiler
                if not profiler.supported():
                    print(profiler.UNSUPPORTED_MESSAGE)
                    continue
                run_folder = profiler.run(settings, run_folder, crawl_result)
            elif stage == "preprocess":
                run_folder = preprocess.run(settings, recipe, run_folder)
            elif stage == "analyse":
                analyse.run(settings, run_folder)
            elif stage == "changes":
                run_folder = changes.run(settings, run_folder, against)
        except (FileNotFoundError, ValueError, crawl.CrawlFailed) as problem:
            print(f"\nStopped at {stage}: {problem}")
            sys.exit(1)

    print("\nAll stages complete.")
    if run_folder:
        print(f"Crawl folder: {run_folder}")   # always the last line, so automations can find the results


def main(settings, argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    recipe_name = take_option(args, "--recipe") or settings["RECIPE"]
    folder = take_option(args, "--folder")
    against = take_option(args, "--against")
    dry_run = take_flag(args, "--dry-run")

    if args and args[0] == "recipes":
        recipes.list_recipes(recipe_name)
    elif args and args[0] == "check":
        sys.exit(0 if recipes.check_all(args[1:]) else 1)
    elif args and args[0] == "new":
        if len(args) < 2:
            sys.exit("Give the recipe a name, e.g.  python gate.py new my-recipe")
        recipes.new_recipe(args[1])
    elif args and args[0] == "columns":
        columns.show(" ".join(args[1:]))
    else:
        unknown = [arg for arg in args if arg not in STAGE_NAMES]
        if unknown:
            sys.exit(f"Don't know '{' '.join(unknown)}'. Stages: {', '.join(STAGE_NAMES)}.\n{__doc__}")
        stages = args or settings["STAGES"]
        if not stages:
            sys.exit("STAGES in gate.py is empty. Switch at least one stage on.")
        pipeline(settings, recipe_name, stages, folder, dry_run, against)
