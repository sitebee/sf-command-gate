# Troubleshooting

The gate checks as much as it can before it crawls and tells you in plain English what's wrong. Start with
`python gate.py --dry-run` and `python gate.py check`. Both run in seconds and don't crawl.

## Before the crawl

| You see | What it means | What to do |
| --- | --- | --- |
| `Screaming Frog not found: ...` | The default install location isn't right for your machine. | Set `SCREAMING_FROG` in section 5 of `gate.py`. |
| `Config file not found: ...` | `CONFIG_FILE` points at a file that isn't there. | Save your config into `config/` ([config/README.md](../config/README.md)) or fix the path. |
| `Choose exactly ONE action in gate.py: --crawl or --crawl-list` | Both or neither of the two lines is switched on. | Leave exactly one of `"--crawl"` and `"--crawl-list"` without a `#`. |
| `Choose exactly ONE of --timestamped-output or --overwrite` | Same, for the output mode. | Leave exactly one switched on. |
| `URL list is missing or empty` | List mode is on but `inputs/urls.txt` has no URLs. | Put one URL per line in the file. |
| `'...' is not a valid export name. Did you mean '...'?` | A typo, or a threshold written as a number. | Use the suggestion. Thresholds use a literal `X`: `Page Titles:Over X Characters`. |
| `Recipe '...' needs --use-pagespeed. Switch it on in APIS in gate.py.` | The recipe depends on an API that is off. | Take the `#` off that line in section 4, and sign in to the API once in the Screaming Frog app. |
| `Recipe '...' not found. Available: ...` | The name doesn't match a file in `recipes/`. | `python gate.py recipes` lists them. |
| `Don't know '...'. Stages: crawl, profile, preprocess, analyse, changes.` | A stage name was mistyped. | Use one of the stages listed. |
| `gate.py is missing report settings: [...]` | `gate.py` is older than the engine. | Copy the missing settings from the current `gate.py`, section 6. |
| `AttributeError: ... removesuffix` | Python older than 3.9. | Use Python 3.9 or newer. |

## During the crawl

| You see | What it means | What to do |
| --- | --- | --- |
| `Screaming Frog failed (exit code N). Last lines of the log:` | The crawl didn't start or stopped. The last log lines are printed. | Read them. The full log is in `logs/`. |
| `Unconfigured filter: ...` in the log | The export needs a feature that isn't switched on in your Screaming Frog config (images, sitemaps, structured data, an API, custom extraction...). | Enable the feature in the app and save the config, or comment that export out of the recipe. |
| `Using UNDEF as tab is not supported` | A tab name Screaming Frog doesn't accept. | Remove it from the recipe. |
| The crawl "finishes" but runs for minutes more | A long tail: the last handful of requests arrive in slow bursts, then Screaming Frog does post-crawl analysis and writes the exports. | Normal. The profiler (Windows) shows the split. Nothing to fix. |
| `Failed to clean directory ...\.ScreamingFrogSEOSpider\temp` in the log | A leftover from an earlier run in Screaming Frog's temp folder. | It didn't affect results in testing. Avoid running two crawls at the same time. |

## After the crawl

| You see | What it means | What to do |
| --- | --- | --- |
| `Cannot preprocess: ... no matching file ... Was it exported, and did Screaming Frog accept it?` | The recipe lists an export that didn't produce a file. | Usually the feature isn't enabled in your config (see `Unconfigured filter` above). |
| `Cannot preprocess: ... columns not found: [...]` | A column in your recipe isn't in that export. | `python gate.py columns "<export name>"` shows the real columns. |
| `No crawl under output has the export 'Internal:All'. Run a crawl first.` | A later stage was run with nothing to work on. | Run a crawl, or point at one with `--folder`. |
| `internal_all_preprocessed.csv not found ... Does the recipe include Internal:All?` | The report needs the Internal export. | Add `"Internal:All": INTERNAL_CORE` to the recipe. |
| `No earlier crawl of this site to compare with yet.` | Not an error. It's your first crawl of this site. | Run again later. |
| `Both crawls need an Internal:All export.` | One of the two crawls has no `internal_all.csv`. | Use `--against` to pick another crawl. |
| Change report shows thousands of URLs added or removed | The two crawls had different settings or scope. | Compare crawls made with the same config. |

## The profiler

| You see | What it means | What to do |
| --- | --- | --- |
| `The profiler is built and tested on Windows only, so this stage was skipped.` | You're on macOS or Linux. | See [profiler.md](profiler.md#building-one-for-macos-or-linux). |
| `psutil isn't installed, so no live CPU, RAM or connection samples` | The one optional package is missing. | `pip install psutil`. |
| CPU shows 0% | Should not happen on the current version. | Update the project. An older build had this bug. |
| `No live samples for this crawl` | You ran `profile` on a crawl made without the profile stage. | Switch the stage on before the crawl. |

## Scheduled runs

- **Works by hand, fails scheduled:** use full paths to Python and the folder. A scheduler's environment isn't your terminal's.
- **Nothing in the log file:** run once by hand first so the `logs` folder exists, or create it.
- **Overlapping runs:** make the gap between runs longer than a crawl takes.
- **Find the results:** the last line of output is `Crawl folder: <path>`.

## Still stuck?

Run `python gate.py --dry-run` and keep the printed command. Then open the newest file in `logs/`, which has the full Screaming Frog output.
Those two things are what anyone helping you will ask for.
