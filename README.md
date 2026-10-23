# Python Command Gate for Screaming Frog CLI

Open **one file**, switch options on and off with `#`, and run it. The gate builds, checks and runs
the Screaming Frog command for you, keeps only the columns you care about, writes a report, and
tells you what changed since the last crawl.

```
python gate.py --dry-run     check everything and print the command, crawl nothing
python gate.py               crawl, trim the exports, write the reports
```

## Why I built this

Screaming Frog's command line is powerful, but a real command quickly turns into one very long line:
the crawl target, the config, a list of tab exports, bulk exports, the output folder, project and task
names, API switches. It is hard to read, easy to break, and impossible to hand to someone else.

I built this so the heavy lifting lives in Python and the part you touch stays short and readable. You
switch options on and off with a `#`, and the gate does the rest. I'm building it for the community I'm
involved in, so the rules were: one file to edit, nothing to learn beyond "`#` off, `#` on", and plain-English
errors when something is wrong.

I also mapped every export and column Screaming Frog offers, so recipes use real names, and a typo is
caught before a crawl starts instead of twenty minutes into one.

## Why use it with automations and scheduled crawls

A crawl you run by hand once is a snapshot. A crawl that runs on a schedule, gets compared with the last
one, and tells you when something breaks is monitoring. The gate is built for that second case:

- **Repeatable.** The same command runs every time. A recipe says what to pull, and every run lands in
  its own timestamped folder, so you build a history without doing anything.
- **Made for schedulers.** It runs headless, never prompts, exits `0` on success and `1` on any problem,
  and its last line is `Crawl folder: <path>`, so a scheduler or workflow tool can find the results.
- **Fails early.** `--dry-run` and `check` validate the command and every recipe in seconds, before a
  crawl that takes 20 minutes or more.
- **Change detection turns a schedule into monitoring.** Each crawl is compared with the previous one:
  new errors, pages that became non-indexable, canonical changes, vanished pages, new or resolved
  Screaming Frog issues. Alert on Critical and High, ignore the rest.
- **Machine-readable output.** Every report has a JSON twin, including Screaming Frog's own issues with
  their fix text. Feed it to n8n, a ticketing system, a dashboard or an LLM without parsing anything.
- **Capacity planning (Windows).** The optional profiler records what a crawl cost: CPU, RAM, connections,
  bandwidth, time, and how long a bigger crawl would take. That tells you how big a machine to schedule
  it on and how long a window to leave.
- **Safe to share.** No secrets live in these files. API sign-ins stay inside the Screaming Frog app.

See [docs/automation.md](docs/automation.md) for scheduling on Windows, Linux and macOS, an n8n pattern,
and an alerting example.

## What you get

| Output | What it is |
| --- | --- |
| `internal_all_preprocessed.csv` and one CSV per export | Only the columns you chose, with tidy names |
| `crawl_analysis.md` / `.json` | Technical summary, prioritised actions, and Screaming Frog's issues with fixes |
| `change_report.md` / `.json` / `changes.csv` | What changed since the previous crawl, most serious first |
| `resource_profile.md` / `.json` | What the crawl cost, and what the site runs on (optional, Windows) |

## Quick start

**You need:** Python 3.9 or newer, and Screaming Frog SEO Spider with a paid licence (the command line
needs one). `pip install psutil` only if you want the profiler.

1. Save a Screaming Frog configuration as `config/weekly-crawl.seospiderconfig`
   (see [config/README.md](config/README.md)).
2. Open `gate.py` and set `CRAWL_URL`, `PROJECT_NAME` and `TASK_NAME`. Only crawl sites you own or have
   permission to crawl.
3. Check, then run:

```
python gate.py --dry-run
python gate.py
```

The first run of a site has nothing to compare with, so the change report says so. Run it again later
and it shows what changed.

## How it works

```
gate.py  ->  crawl  ->  profile  ->  preprocess  ->  analyse  ->  changes
 (you)      Screaming   (optional)   keep the        report       compare with the
            Frog                     columns                      previous crawl
```

Every option in `gate.py` is **one line**. Take the `#` off to switch it on, put it back to switch it
off. A flag and its value share a line, so you can't half-comment an option and break the command.

```python
CRAWL = [
    # ACTION - choose ONE
    "--crawl", CRAWL_URL,
    # "--crawl-list", URL_LIST,

    "--headless",
    "--config", CONFIG_FILE,
    # "--save-crawl",
    ...
]
```

Before anything runs, the gate checks the command, tells you in plain English what's wrong, and prints
the final command one flag per line:

```
Cannot run yet:
  - on-page TABS: 'Page Titles:Over 60 Characters' is not a valid export name.
                  Did you mean 'Page Titles:Over X Characters'?
```

### What's in `gate.py`

| Section | What you set |
| --- | --- |
| 1. The site | URL, project name, task name |
| 2. The recipe | `RECIPE = "on-page"` |
| 3. The crawl | crawl or list mode, config file, timestamped or overwrite, optional `--save-crawl` |
| 4. APIs | one switch line per API |
| 5. The pipeline | which stages run, keep the raw exports or not |
| 6. The report | report sections, thresholds, alert rules |
| 7. The profiler | optional resource report (Windows) |
| 8. Change detection | what to watch for between crawls, and the thresholds |

### Folder layout

```
gate.py      the ONE file you edit
recipes/     what to pull from a crawl: pick one, or build your own
config/      your Screaming Frog configuration
docs/        guides
_engine/     the machinery. You don't need to touch it
output/      crawls and reports land here (created for you)
logs/        full Screaming Frog output for each run (created for you)
```

## Many websites: one copy per site

Command Gate is built around **one instance per website**. To scale across several sites, copy the folder
once per site, rename it, and configure that copy's gate and recipes:

```
seo-crawls/
  command-gate-example-com/       one site
  command-gate-another-site/      another site
  command-gate-client-shop/       and so on
```

1. **Copy and rename the folder**, for example `command-gate-example-com`. Leave out the `output/` and `logs/`
   folders from the original, so the copy starts with a clean history.
2. **Configure that copy's `gate.py`**: `CRAWL_URL`, `PROJECT_NAME`, `TASK_NAME`, `RECIPE`, and any API switch lines
   (a Search Console property, for example, is specific to one site).
3. **Give it its own Screaming Frog config** in its `config/` folder, so each site can have its own speed, user agent,
   rendering and extraction settings.
4. **Choose or build its recipes.** Keep the ones you use, trim the rest, and add site-specific ones in that copy's `recipes/`.
5. **Schedule each copy on its own**, and stagger the times. Aim to run one crawl at a time: don't run several concurrently unless you are confident
   the hardware can handle it.

Why one copy per site: each site gets its own settings, its own recipes and its own `output/` history, so the change report always
compares a site with its own previous crawl, and one site's setup can never break another's.

The trade-off is that the engine is copied too. Everything site-specific lives in `gate.py`, `config/`, your own recipes and `output/`,
and `_engine/` is the same in every copy. To update a copy to a newer version, replace its `_engine/` folder (and any built-in
recipes you haven't customised), and leave your `gate.py`, `config/` and `output/` alone.

## Commands

```
python gate.py                       run the stages in gate.py
python gate.py --dry-run             check and print the command, run nothing
python gate.py --recipe on-page      use a different recipe for this run
python gate.py preprocess analyse    run only these stages on the newest crawl
python gate.py --folder output/X     run the later stages on a specific crawl

python gate.py changes               what changed since the previous crawl
python gate.py changes --against X   compare with a specific earlier crawl instead
python gate.py profile               resource report for a crawl (Windows)

python gate.py recipes               list the recipes
python gate.py check                 check every recipe against the reference (no crawl)
python gate.py new my-recipe         start your own recipe
python gate.py columns "Internal:All"    print a column picker for any export
```

## Recipes

A **recipe** says which exports to pull and which columns to keep. Each line is one export. Comment a line
out and that export is skipped by the crawl **and** by preprocessing, so there is only ever one place to
switch it.

```python
TABS = {
    "Internal:All": INTERNAL_CORE,
    "Page Titles:Missing": TITLES,
    "Page Titles:Duplicate": TITLES,
    # "Page Titles:Over X Pixels": TITLES,     <- switched off
}
```

| Recipe | What it finds |
| --- | --- |
| `quick-health` | The basics for every URL, plus Screaming Frog's Issues Overview: every issue found, its priority, how many URLs, and how to fix it. |
| `on-page` | Missing, duplicate, too long or too short titles, meta descriptions, H1s and H2s. |
| `indexability` | Canonicals, noindex and robots directives, pagination, sitemaps, robots.txt blocks. |
| `errors-and-redirects` | 4xx, 5xx, redirects, chains and loops, plus the links that point at them. |
| `links-and-architecture` | Crawl depth, internal linking, nofollow, anchor text. Link-level exports are off by default (they get huge). |
| `images` | Missing alt text, heavy and wrongly sized images, and which page each is on. |
| `content-quality` | Exact duplicates, thin content, readability, soft 404s. Near-duplicate and spelling checks are optional. |
| `security` | HTTP URLs, mixed content, insecure forms, missing security headers. |
| `url-hygiene` | Parameters, uppercase, underscores, spaces, long and repetitive URLs. |
| `structured-data` | Pages with and without schema, types used, validation and rich result errors. |
| `international` | Hreflang: missing return links, bad codes, no x-default, non-200 and non-canonical targets. |

Every recipe includes `Internal:All`, because the report is built from it. An empty export is normal: it
means that check found no issues. How to build your own is in [docs/recipes.md](docs/recipes.md).

## APIs

Section 4 of `gate.py` has a switch line for each API Screaming Frog can use during a crawl: PageSpeed,
Search Console, GA4, Majestic, Ahrefs, Moz, and the AI providers. Sign in to each one **once in the
Screaming Frog app**. It keeps the credentials, so nothing secret goes in these files. A recipe can say it
needs an API (`REQUIRES = ["--use-pagespeed"]`), and the check stops you before the crawl if it isn't
switched on.

## Automations

**Command Gate is the crawl wrapper.** It runs a Screaming Frog crawl reliably, the same way every time, and leaves tidy, predictable files behind.
**How you build automations around it is up to you.** It gives you the pieces: a command that runs headless and never prompts, exit codes
(`0` success, `1` a problem), a last line that names the results folder (`Crawl folder: <path>`), and a JSON file for every report.

Two common ways to automate it:

- **Cron or Windows Task Scheduler.** Run the crawl on a schedule.

  ```
  0 6 * * 1  cd /home/me/command-gate && /usr/bin/python3 gate.py >> logs/scheduled.log 2>&1
  ```

- **n8n, or a similar workflow tool.** Run the command from the tool (or let a scheduler run it), read `change_report.json` from the newest folder in
  `output/`, branch on severity, and notify. A crawl takes far longer than a typical workflow step, so the guide covers both ways of wiring it.

**Aim to run one crawl at a time.** Don't run several crawl instances concurrently unless you are confident the hardware can handle it: they share CPU,
memory, disk and network, and the sites you crawl feel the combined load. Stagger your schedules, and if you do want to overlap crawls, size it first
with the profiler (Windows).

Scheduling for Windows, Linux and macOS, an n8n pattern, an alert script, and housekeeping are in [docs/automation.md](docs/automation.md).

## Using the data downstream

What happens to the output is up to you. Command Gate stops at the files, and doesn't ship integrations or guess your stack. The files are built
to be easy to hand on:

| Destination | What to use |
| --- | --- |
| Spreadsheets and BI tools (Excel, Google Sheets, Looker Studio, Power BI) | The CSVs: `changes.csv`, `internal_all_preprocessed.csv` |
| A database | The preprocessed CSVs, one table with a crawl column |
| Chat or email alerts | `change_report.json`, filtered to Critical and High |
| Ticket and task tools | One ticket per finding in `change_report.json`, with `changes.csv` for the URL list |
| An LLM | `crawl_analysis.json` and `change_report.json` (small, structured, with fix text) |
| Archiving | The finished crawl folders, copied to cloud storage |

[docs/downstream.md](docs/downstream.md) has working examples: loading crawls into SQLite, posting an alert to a chat webhook, and feeding an LLM.
They are examples to adapt, not part of the tool.

## Platform support

- **Windows is where this was developed and tested** (Windows Server 2025, Python 3.11, Screaming Frog
  24.3). Crawls of about 26,000 URLs took around 18 minutes.
- **macOS and Linux:** the gate, recipes, preprocessing, report and change detection are plain Python with
  no Windows-specific code, and the default Screaming Frog locations for both systems are built in. They
  have not been tested there, so expect to adjust, and please report what you find.
- **The profiler works on Windows only.** macOS and Linux users can write their own. The stage skips itself
  with a message on those systems, and [docs/profiler.md](docs/profiler.md) explains how.
- Export names come from the command line help of the version above. Other versions may differ, and
  `python gate.py check` will tell you.

## Documentation

| Guide | What's in it |
| --- | --- |
| [docs/automation.md](docs/automation.md) | Scheduling with cron and Task Scheduler, n8n, exit codes, JSON outputs, alerting, one crawl at a time, housekeeping |
| [docs/downstream.md](docs/downstream.md) | Shipping the output into your own tools: spreadsheets, databases, chat, tickets, LLMs, archives |
| [docs/recipes.md](docs/recipes.md) | The recipe format, building your own, how names are matched |
| [docs/change-detection.md](docs/change-detection.md) | What is compared, severities, settings, output |
| [docs/profiler.md](docs/profiler.md) | The resource profiler, what each number means, building one for macOS or Linux |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Error messages and what to do about them |
| [config/README.md](config/README.md) | Making your Screaming Frog configuration |

## Responsible use

Only crawl sites you own or have permission to crawl, and keep the speed settings gentle on sites that
aren't yours. Use a user agent that is honest about who is crawling. The optional profiler probe sends
three requests to the site you crawl (the homepage twice, and robots.txt), and you can switch it off.

Screaming Frog SEO Spider is a product of Screaming Frog Ltd. This project is independent and not
affiliated with or endorsed by them. It calls the command line of your own licensed copy.
