# Change detection

The `changes` stage compares each crawl with the previous crawl **of the same site** and tells you what changed, most
serious first. It runs inside the gate, using the CSV files already in `output/`. It does not need `--save-crawl`, so
you don't pay for the large saved-crawl files.

```
python gate.py changes                          newest crawl vs the one before it
python gate.py changes --against 2026.10.01.09.00.00     vs a specific earlier crawl
```

It is a stage in `STAGES` in `gate.py`, so a normal run does it automatically after the report.

## Which crawl is "previous"?

The newest earlier crawl folder in `output/` (folder names are timestamps) whose URLs belong to the same site. A different
site in the same `output/` folder is skipped. With `--against`, or `CHANGES_AGAINST` in `gate.py`, you name the crawl yourself.

The first crawl of a site has nothing to compare with. The stage says so and carries on without error.

## What is compared

For URLs in both crawls, and only for pages that worked both times unless noted:

| Severity | Change | When it is flagged |
| --- | --- | --- |
| Critical | New errors | Worked before, now 4xx, 5xx or no response |
| High | Indexable pages no longer found | An indexable HTML page from the last crawl is missing now |
| High | Became non-indexable | Indexable before, not now (noindex, canonicalised and so on) |
| High | Canonical changed | The canonical URL is different |
| High | Became an orphan page | Had internal links, now has none |
| High | Newly blocked by robots.txt | Could be crawled, now blocked |
| Medium | Title, meta description or H1 changed | The text is different |
| Medium | Word count changed | Moved by more than `CHANGES_WORD_COUNT_PERCENT` (and at least 25 words) |
| Medium | Content changed | The content hash differs **and** the word count or size moved too |
| Medium | Redirect target changed | A redirect now points elsewhere |
| Medium | Lost internal links | Had 10 or more internal links, now half or fewer |
| Medium | Status changed, no longer blocked by robots.txt | Moved between status types |
| Low | Slower responses | Slower by `CHANGES_RESPONSE_SECONDS` and at least twice as slow |
| Low | Page size changed | Changed by more than `CHANGES_SIZE_PERCENT` (and at least 5 KB) |
| Low | Pushed deeper in the site | Two or more clicks further from the start |
| Low | Other URLs no longer found | Non-page URLs that disappeared |
| Info | New URLs found, Errors fixed, Became indexable | Usually good news |

It also compares **Screaming Frog's Issues Overview** when both crawls have one (the `quick-health` recipe exports it): issues that are
new, resolved, worse or better, with the change in the number of URLs.

Headline numbers (URLs, indexable pages, errors, redirects, robots.txt blocks, average response time and word count, total size) are shown
side by side.

## Why content hashes aren't trusted alone

A content hash changes whenever any byte of the page changes, and many pages carry a token or timestamp that changes on every request. On the
site this was developed on, **44% of pages (11,380 of about 25,800) had a different hash between two crawls 40 minutes apart**, while the word
count, size, titles and everything else were identical. Reporting those as content changes would make the report useless.

So a page only counts as "content changed" if the hash differs **and** the word count or size moved too. Pages with only a hash difference
are counted in one note at the bottom of the report.

## Settings (section 8 of `gate.py`)

```python
CHANGES_AGAINST = "previous"        # or the name of a crawl folder in output/

CHANGES_WATCH = {                   # set one to False to ignore that kind of change
    "status": True, "indexability": True, "titles": True, "meta_descriptions": True,
    "h1s": True, "canonicals": True, "redirects": True, "content": True,
    "links": True, "depth": True, "response_time": True, "size": True,
}

CHANGES_WORD_COUNT_PERCENT = 20
CHANGES_SIZE_PERCENT = 30
CHANGES_RESPONSE_SECONDS = 0.5
CHANGES_SAMPLE_LIMIT = 10           # example URLs per change in the report (changes.csv has them all)
```

## What it writes

Into the new crawl's folder:

- `change_report.md`: a summary, headline numbers, then each kind of change with example URLs (before and after) and the issue comparison.
- `change_report.json`: the same findings for scripts and LLMs.
- `changes.csv`: every change, one per line (`severity, change, url, field, before, after`). Open it in a spreadsheet to filter.

An illustrative excerpt (the domain is a placeholder):

```
### Critical: New errors (3)
Pages that worked in the last crawl and now return an error or no response.

| URL | Before | After |
| --- | --- | --- |
| https://example.com/collections/accessories | 200 OK | 404 Not Found |
| https://example.com/collections/new-in | 200 OK | 404 Not Found |
```

## Limits

- **Both crawls should use the same settings.** If the scope or config changed, thousands of URLs show as added or removed and the rest is noisy.
  The report reminds you.
- It reads the raw `internal_all.csv` when it is there (the default, `KEEP_ORIGINAL_FILES = True`), so it can compare the most fields.
  With only the trimmed file, it compares the fields both crawls have.
- URLs are matched exactly as Screaming Frog reports them. A site that changes its URL format will show everything as removed and added.
- It sees what the Internal:All export holds. It cannot see changes Screaming Frog doesn't export.
- The thresholds are starting points. Tune them to how noisy your site is.

## Using it in automation

See [automation.md](automation.md) for an alert script that exits non-zero when anything Critical or High changed.
