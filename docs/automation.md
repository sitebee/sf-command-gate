# Automation and scheduled crawls

**Command Gate is the crawl wrapper.** It runs a Screaming Frog crawl reliably, the same way every time, and leaves tidy, predictable
files behind. **How you build automations around it, and what you do with the data, is up to you.** This guide shows what an automation
can rely on and how to run a crawl from cron, Windows Task Scheduler or a workflow tool such as n8n. What happens to the output afterwards
is in [downstream.md](downstream.md).

## What an automation can rely on

**It never prompts.** Crawls run headless, and every choice lives in `gate.py`.

**Exit codes.**

| Exit code | Meaning |
| --- | --- |
| `0` | Everything you asked for completed. |
| `1` | Something stopped it: a failed check, a failed crawl, a missing file, an unknown stage or recipe. The reason is printed. |

`python gate.py check` also exits `1` if any recipe fails its check, so it works as a gate in a code review.

**The last line.** When a run produces or uses a crawl folder, the final line printed is:

```
Crawl folder: C:\path\to\command-gate\output\2026.10.23.15.47.08
```

Read the last line of the output and you know where the results are.

**Folder names are timestamps** (`YYYY.MM.DD.HH.MM.SS`), so the newest crawl always sorts last.

**Every report has a JSON twin**, plus a CSV of every change:

| File | Use it for |
| --- | --- |
| `change_report.json` | Alerting. `findings` is a list of `{change, severity, count, examples}`, ordered most serious first. Severities are `Critical`, `High`, `Medium`, `Low`, `Info`. `issues` lists Screaming Frog issues that are `new`, `resolved`, `worse` or `better`. |
| `changes.csv` | Every individual change, one per line: `severity, change, url, field, before, after`. |
| `crawl_analysis.json` | Dashboards and LLMs. Executive summary, prioritised actions, and `screaming_frog_issues` with each issue's description and how to fix it. |
| `resource_profile.json` | Capacity planning (Windows). Timings, resources by phase, scaling estimates. |

**Validate before you wait.** `python gate.py --dry-run` runs every check and prints the command in a few seconds. Run it when you set up a
schedule, and again whenever you edit `gate.py` or a recipe.

## Run it from cron or Task Scheduler

Use a full path to Python and to the folder, because a scheduler starts with a different environment from your terminal.
**Run `python gate.py` once by hand first**, then schedule it. The first run creates the `logs` folder that the examples below write their
own log into (create it yourself if you'd rather not crawl first).

### Linux and macOS (cron)

```
0 6 * * 1  cd /home/me/command-gate && /usr/bin/python3 gate.py >> logs/scheduled.log 2>&1
```

Add it with `crontab -e`. That runs the whole pipeline at 06:00 every Monday: crawl, trim, report, and compare with the last crawl. cron also
works on macOS, and `launchd` is the native alternative there.

To run only part of the pipeline, name the stages: `python gate.py preprocess analyse changes` skips the crawl and works on the newest one.

### Windows (Task Scheduler)

In `cmd` (the `^` continues the line):

```
schtasks /Create /TN "Command Gate weekly crawl" /SC WEEKLY /D MON /ST 06:00 ^
  /TR "cmd /c cd /d C:\SEO\command-gate && C:\Python311\python.exe gate.py >> logs\scheduled.log 2>&1"
```

Test it without waiting: `schtasks /Run /TN "Command Gate weekly crawl"`. On a server, tick "run whether the user is logged on or not" in the
Task Scheduler app.

These are standard scheduler commands, not something specific to this project, and I haven't included screenshots. Test with a manual run first.

### Leave room between runs

A crawl of about 26,000 URLs took around 18 minutes in testing, including about 4 minutes of wrap-up after the last request. Schedule well
apart. The profiler (Windows) records the real timings for your site so you can pick a sensible window.

## Run it from n8n (or a similar workflow tool)

Any tool that can run a command and read a file can drive this. There are two ways to wire it, and the difference matters because **a crawl
takes much longer than a typical workflow step**.

**A. The scheduler runs the crawl, the workflow picks up the results.** Cron or Task Scheduler runs `python gate.py`. A workflow then runs a little
after the crawl is due to finish (or when you trigger it), finds the newest folder in `output/`, and reads the JSON. This is the sturdier option
for long crawls, because the workflow never has to wait.

**B. The workflow runs the crawl.** One workflow does everything:

1. **Schedule Trigger**, for example weekly.
2. **Execute Command**: `cd /path/to/command-gate && python gate.py` (on Windows, `cd /d C:\path\to\command-gate && python gate.py`). The last line of
   the output is `Crawl folder: <path>`. This node can be disabled in some n8n setups, and a crawl may outlast your execution timeout, so check both.
3. **Read file**: `<crawl folder>/change_report.json`, parsed as JSON.
4. **IF**: any entry in `findings` has `severity` of `Critical` or `High`.
5. **Notify**: send the first few findings and examples wherever you work.
6. Optional: hand `crawl_analysis.json` to an LLM step to draft a summary or a task list.

Both use only the command, the exit code, the last line and the JSON files above. I haven't tested either end to end in n8n, so treat them as patterns.
What the workflow does with the data is covered in [downstream.md](downstream.md).

## Alerting on changes

Run the crawl, then look at the change report. A first crawl has no change report, so check the file exists.

**Python** (works anywhere):

```python
import json, pathlib, sys

folder = pathlib.Path(sys.argv[1])            # the "Crawl folder:" from the last line
report_file = folder / "change_report.json"
if not report_file.exists():
    sys.exit(0)                               # first crawl: nothing to compare yet

report = json.loads(report_file.read_text(encoding="utf-8"))
serious = [f for f in report["findings"] if f["severity"] in ("Critical", "High")]
for finding in serious:
    print(f'{finding["severity"]}: {finding["change"]} ({finding["count"]})')
    for example in finding["examples"][:3]:
        print("   ", example["url"], "|", example["before"], "->", example["after"])
sys.exit(2 if serious else 0)                 # a scheduler can alert on exit code 2
```

This was tested: it exits `0` on a quiet crawl or a first crawl, and `2` when Critical or High changes exist.

**jq**:

```
jq '[.findings[] | select(.severity=="Critical" or .severity=="High")] | length' change_report.json
```

Useful rules of thumb:

- Alert on **Critical** (new errors) and **High** (pages vanished, became non-indexable, canonical changes, orphans, newly blocked by robots.txt).
- Put **Medium** (titles, descriptions, H1s, content) in a weekly digest. They are often deliberate edits.
- Ignore **Info** (new URLs, fixed errors) unless you want the good news too.
- Tune what counts as a change in section 8 of `gate.py`.

## One crawl at a time

**Aim to run one crawl at a time.** Don't run several crawl instances concurrently unless you are confident the hardware can handle it.
Crawls share the machine's CPU, memory, disk and network, and the sites you crawl feel the combined load.

- **Stagger the schedule** so each crawl finishes before the next starts, with a margin. The profiler (Windows) shows how long yours really take.
- **If you want to overlap, size it first.** Run each crawl alone with the profiler and check that the peaks add up with headroom. In testing, a single
  crawl at 5 threads peaked at 80% of a 6-core machine's CPU, averaged 42% during the main crawl, and wrote about 11 GB to disk in 8 minutes
  (Screaming Frog's database mode writes heavily). Two like it at once would likely have competed for the CPU and the disk.
- **Watch the disk, not just CPU and RAM.** Heavy disk writes are what a slow disk turns into slow crawls.
- **Be kind to the sites.** Overlapping crawls of the same site double the load on it. Keep the thread and speed settings gentle on sites that
  aren't yours.
- **Never start a second crawl in the same copy while one is running.** They would share the same `output/` and `logs/` folders and Screaming Frog's
  working folders, and I haven't tested that it is safe.

## Many sites

`gate.py` holds one site, so to scale across websites you keep **one copy of the folder per site**. Copy the folder, rename it
(for example `command-gate-example-com`), and configure that copy's `gate.py` (`CRAWL_URL`, `PROJECT_NAME`, `TASK_NAME`, `RECIPE`, APIs),
`config/` and recipes. Start each copy with clean `output/` and `logs/` folders. The full steps are in the README under
"Many websites: one copy per site".

For automation this means:

- **Schedule each copy separately**, with its own entry in Task Scheduler or cron, running from that copy's folder.
- **Stagger the times**, as above, so crawls don't overlap.
- **Each copy keeps its own history**, so every change report compares a site with its own previous crawl.
- **Alert per site.** Run the same alert script against each copy's `Crawl folder:`, and put the site name in the message.
- **Housekeeping runs per copy too**, in each copy's `output/`.
- **To update the tool**, replace each copy's `_engine/` folder and leave its `gate.py`, `config/` and `output/` alone.

## Housekeeping

A crawl of about 26,000 URLs wrote around 100 MB (the exports, the trimmed CSVs and the reports). Weekly crawls add up, so clear out old ones now and
then. Change detection compares with the newest earlier crawl of the same site, so **always keep the latest one or two**.

PowerShell (preview first with `-WhatIf`, then remove it to delete):

```
Get-ChildItem output -Directory | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) } | Remove-Item -Recurse -Force -WhatIf
```

Linux and macOS:

```
find output -mindepth 1 -maxdepth 1 -type d -mtime +90 -exec rm -rf {} +
```

Two settings save space: `KEEP_ORIGINAL_FILES = False` in `gate.py` deletes the raw exports after preprocessing (change detection still works from the trimmed
files, with fewer fields to compare), and `--save-crawl` in the CRAWL list, which saves the full Screaming Frog crawl, is **off by default because those files
are large**.
