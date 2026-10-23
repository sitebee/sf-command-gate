# Using the data downstream

Command Gate is the **crawl wrapper**. Its job is to run a Screaming Frog crawl reliably, the same way every time, and leave
tidy, predictable files behind. **What you do with those files is up to you.** It doesn't ship integrations, and it doesn't
try to guess your stack. This guide shows the shape of the output and a few common destinations, as examples to copy and adapt.

The code in this guide is example code. It is not part of Command Gate, and you are free to ignore all of it.

## The files you get

Every crawl lands in its own timestamped folder in `output/`:

| File | Format | Good for |
| --- | --- | --- |
| `internal_all_preprocessed.csv` and one `*_preprocessed.csv` per export | CSV, only the columns your recipe keeps, tidy names | Spreadsheets, BI tools, databases |
| `changes.csv` | CSV, one change per line: `severity, change, url, field, before, after` | A to-do list per URL, tickets, spreadsheets |
| `change_report.json` | JSON, findings ranked by severity, plus issue changes | Alerts, automations, LLMs |
| `crawl_analysis.json` | JSON, summary, prioritised actions, Screaming Frog's issues with fix text | Dashboards, LLMs |
| `crawl_analysis.md`, `change_report.md` | Markdown for people | Email, chat, a wiki, a pull request |
| `resource_profile.json` / `.md` (Windows, optional) | Timings, resources, scaling estimates | Capacity planning |

## What you can rely on

- **Folder names are timestamps** (`YYYY.MM.DD.HH.MM.SS`), so the newest crawl sorts last.
- **The last line of a run** is `Crawl folder: <path>`, so a script knows where to look.
- **The file names above** are the ones the docs describe, and the JSON keys are documented in [automation.md](automation.md).
  New keys may be added over time, so read the ones you need and ignore the rest.
- **Crawl folders aren't edited after the run**, apart from re-running a later stage on one with `--folder`. If you load them into something,
  de-duplicate on the folder name.

## Where it can go

### Spreadsheets and BI tools

The CSVs open directly in Excel, Google Sheets, Looker Studio, Power BI or Tableau. Point a folder or file connector at `output/`, or import
`changes.csv` for a ready-made to-do list sorted by severity. If you chart things over time, keep the recipe's columns the same between crawls.

### A database

A small standard-library script that loads each crawl into SQLite. Any database works the same way: one table, one extra column for the crawl.

```python
import csv, sqlite3, sys
from pathlib import Path

folder = Path(sys.argv[1])                      # the "Crawl folder:" from the last line
db = sqlite3.connect("crawls.db")
with (folder / "internal_all_preprocessed.csv").open(encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
columns = list(rows[0])

db.execute(f'CREATE TABLE IF NOT EXISTS pages (crawl TEXT, {", ".join(f"{c} TEXT" for c in columns)})')
db.executemany(f'INSERT INTO pages VALUES (?, {", ".join("?" for _ in columns)})',
               [(folder.name, *row.values()) for row in rows])
db.commit()
```

Then you can ask questions across every crawl you have kept:

```sql
-- indexable pages per crawl
SELECT crawl, COUNT(*) FROM pages WHERE indexability = 'Indexable' GROUP BY crawl;

-- status codes in the latest crawl
SELECT status_code, COUNT(*) FROM pages WHERE crawl = (SELECT MAX(crawl) FROM pages) GROUP BY status_code;
```

Keep the recipe's columns the same between crawls, or the table won't match.

### Chat and email alerts

Alert only when something serious changed. This builds a message from `change_report.json` and posts it to a chat webhook (Slack's incoming
webhooks accept this shape). Keep the webhook address in your scheduler's or tool's secret storage, not in a file you share.

```python
import json, sys, urllib.request
from pathlib import Path

WEBHOOK = "https://hooks.slack.com/services/XXX/YYY/ZZZ"      # your own webhook, kept secret
folder = Path(sys.argv[1])
report_file = folder / "change_report.json"
if not report_file.exists():
    sys.exit(0)                                               # first crawl: nothing to compare yet

report = json.loads(report_file.read_text(encoding="utf-8"))
serious = [f for f in report["findings"] if f["severity"] in ("Critical", "High")]
if serious:
    lines = [f"*{f['severity']}*: {f['change']} ({f['count']})" for f in serious]
    text = f"Crawl changes for {report['current']['folder']}:\n" + "\n".join(lines)
    request = urllib.request.Request(WEBHOOK, data=json.dumps({"text": text}).encode(),
                                     headers={"Content-Type": "application/json"})
    urllib.request.urlopen(request)
```

The message-building part of this was tested. Sending depends on your webhook, so test it with your own.

### Tickets and task tools

Create one ticket per Critical or High finding in `change_report.json`. `findings[].examples` gives a few URLs with before and after, and
`changes.csv` has every URL if you want to attach the full list. The same pattern fits Jira, Asana, Linear, Trello, GitHub issues and others.
Call their API from your own script or workflow tool.

### An LLM

Give the model the JSON, not the CSVs. `crawl_analysis.json` was about 40 KB for a crawl of 26,000 URLs, and `change_report.json` a few KB.
Both are structured, and the issues carry Screaming Frog's own explanation and fix. A prompt as simple as this works:

```
Here is this week's crawl analysis and the changes since last week. Summarise what matters in five bullets,
list anything Critical or High first, and suggest an order to fix things in.
```

Remember a hosted model receives your crawl data. If the site is a client's, make sure that is allowed.

### Archiving and backup

Copy finished crawl folders somewhere safe and clear them off the crawling machine. With tools you may already use:

```
rclone copy output/2026.10.23.16.24.31 remote:seo-crawls/example-com/2026.10.23.16.24.31
aws s3 sync output s3://my-bucket/seo-crawls/example-com/
```

These are patterns, not tested here. Check them against your own setup first.

## In a workflow tool

In n8n or a similar tool, each of the above is a step after the crawl: read the file, branch on severity, then send, store or create.
See [automation.md](automation.md) for how to run the crawl itself, from the tool or from a scheduler.

## Keep in mind

- **Crawl data can be sensitive.** URLs, titles and structure of a client's site may be confidential. Check where you send it.
- **Don't put secrets in `gate.py` or a recipe.** Use your scheduler's or tool's secret storage for webhooks and API keys.
- **Mind the size.** `internal_all.csv` was about 18 MB for 26,000 URLs. Don't paste whole files into tools that weren't built for them.
- **Read what you need.** The JSON files are designed to be read selectively.
