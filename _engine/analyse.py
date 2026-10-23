"""Stage 3 machinery: turn the preprocessed crawl into a report.

Writes crawl_analysis.md (for people) and crawl_analysis.json (for LLMs).
You shouldn't need to edit this file. The report switches, thresholds and
alert rules are in gate.py.
"""

import csv
import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "output"
SOURCE_FILENAME = "internal_all_preprocessed.csv"
ISSUES_FILENAME = "issues_overview_report_preprocessed.csv"   # from the Issues:All export
MARKDOWN_FILENAME = "crawl_analysis.md"
JSON_FILENAME = "crawl_analysis.json"

# These come from gate.py (section 6, THE REPORT). configure() copies them in below.
REPORT_SETTINGS = [
    "INCLUDE_EXECUTIVE_SUMMARY", "INCLUDE_CRAWL_SCOPE", "INCLUDE_TECHNICAL_HEALTH",
    "INCLUDE_INDEXABILITY", "INCLUDE_ON_PAGE", "INCLUDE_CONTENT_QUALITY", "INCLUDE_PERFORMANCE",
    "INCLUDE_SITE_ARCHITECTURE", "INCLUDE_PRIORITISED_ACTIONS", "INCLUDE_ISSUES_OVERVIEW", "ISSUES_LIMIT",
    "SLOW_PAGE_SECONDS", "THIN_CONTENT_WORDS", "SHORT_TITLE_CHARACTERS", "LONG_TITLE_CHARACTERS",
    "SHORT_META_DESCRIPTION_CHARACTERS", "LONG_META_DESCRIPTION_CHARACTERS", "TOP_PAGES_LIMIT",
    "ACTION_RULES",
]


def configure(settings):
    missing = [key for key in REPORT_SETTINGS if key not in settings]
    if missing:
        raise ValueError(f"gate.py is missing report settings: {missing}")
    globals().update({key: settings[key] for key in REPORT_SETTINGS})


def find_source(folder=None) -> Path:
    """The given crawl folder, otherwise the newest crawl that has the file."""
    if folder:
        source = Path(folder) / SOURCE_FILENAME
        if not source.exists():
            raise FileNotFoundError(f"{SOURCE_FILENAME} not found in {folder}. Does the recipe include Internal:All?")
        return source

    files = list(OUTPUT_ROOT.rglob(SOURCE_FILENAME))
    if not files:
        raise FileNotFoundError(f"No {SOURCE_FILENAME} found under {OUTPUT_ROOT}")
    return max(files, key=lambda path: path.stat().st_mtime)


def is_html(row):
    return row.get("content_type", "").lower().startswith("text/html")


def as_number(value):
    try:
        return float((value or "").replace(",", ""))
    except ValueError:
        return 0.0


def as_int(value):
    return int(as_number(value))


def percent(value, total):
    return round(value / total * 100, 1) if total else 0.0


def urls(rows, limit=None):
    return [row["address"] for row in rows[:limit or TOP_PAGES_LIMIT] if row.get("address")]


def stats(rows, field):
    values = [as_number(row.get(field)) for row in rows if row.get(field, "").strip()]
    if not values:
        return {"count": 0, "min": 0, "median": 0, "mean": 0, "max": 0}
    return {"count": len(values), "min": round(min(values), 2),
            "median": round(statistics.median(values), 2),
            "mean": round(statistics.mean(values), 2), "max": round(max(values), 2)}


def duplicates(rows, field):
    grouped = {}
    for row in rows:
        value = row.get(field, "").strip()
        if value:
            grouped.setdefault(value, []).append(row)
    return {value: group for value, group in grouped.items() if len(group) > 1}


def normalise_url(value):
    if not value:
        return ""
    parsed = urlsplit(value.strip())
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, parsed.query, ""))


def issue(name, priority, affected, rationale):
    return {"priority": priority, "action": name, "affected_urls": len(affected),
            "rationale": rationale, "sample_urls": urls(affected)}


def load_issues(source):
    """Screaming Frog's own Issues Overview, ranked by priority then URLs. None if the recipe didn't export it."""
    found = list(source.parent.rglob(ISSUES_FILENAME))
    if not found:
        return None
    with min(found, key=lambda path: len(path.parts)).open("r", encoding="utf-8-sig", newline="") as file:
        rows = [row for row in csv.DictReader(file) if as_int(row.get("urls")) > 0]

    rank = {"High": 0, "Medium": 1, "Low": 2}
    rows.sort(key=lambda row: (rank.get(row.get("issue_priority"), 3), -as_int(row.get("urls"))))
    return {
        "total_issues": len(rows),
        "by_type": dict(Counter(row["issue_type"] for row in rows)),
        "by_priority": dict(Counter(row["issue_priority"] for row in rows)),
        "issues": [{"name": row["issue_name"], "type": row["issue_type"], "priority": row["issue_priority"],
                    "urls": as_int(row["urls"]), "percent_of_total": as_number(row["percent_of_total"]),
                    "description": row["description"], "how_to_fix": row["how_to_fix"], "help_url": row["help_url"]}
                   for row in rows],
    }


def build_report(source):
    with source.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    html = [row for row in rows if is_html(row)]
    errors = [row for row in rows if as_int(row.get("status_code")) >= 400]
    redirects = [row for row in rows if 300 <= as_int(row.get("status_code")) < 400]
    non_indexable = [row for row in html if row.get("indexability", "") != "Indexable"]
    missing_title = [row for row in html if not row.get("title", "").strip()]
    missing_meta = [row for row in html if not row.get("meta_description", "").strip()]
    missing_h1 = [row for row in html if not row.get("h1", "").strip()]
    missing_canonical = [row for row in html if not row.get("canonical_url", "").strip()]
    non_self_canonical = [row for row in html if row.get("canonical_url", "").strip() and normalise_url(row["address"]) != normalise_url(row["canonical_url"])]
    title_duplicates = duplicates(html, "title")
    meta_duplicates = duplicates(html, "meta_description")
    h1_duplicates = duplicates(html, "h1")
    short_titles = [row for row in html if row.get("title", "").strip() and as_int(row.get("title_length")) < SHORT_TITLE_CHARACTERS]
    long_titles = [row for row in html if as_int(row.get("title_length")) > LONG_TITLE_CHARACTERS]
    short_metas = [row for row in html if row.get("meta_description", "").strip() and as_int(row.get("meta_description_length")) < SHORT_META_DESCRIPTION_CHARACTERS]
    long_metas = [row for row in html if as_int(row.get("meta_description_length")) > LONG_META_DESCRIPTION_CHARACTERS]
    slow = sorted([row for row in html if as_number(row.get("response_time")) >= SLOW_PAGE_SECONDS], key=lambda row: as_number(row.get("response_time")), reverse=True)
    thin = sorted([row for row in html if 0 < as_int(row.get("word_count")) < THIN_CONTENT_WORDS], key=lambda row: as_int(row.get("word_count")))
    zero_words = [row for row in html if as_int(row.get("word_count")) == 0]
    orphans = [row for row in html if as_int(row.get("inlinks")) == 0]
    largest = sorted(html, key=lambda row: as_number(row.get("size_bytes")), reverse=True)
    deepest = sorted(html, key=lambda row: as_int(row.get("folder_depth")), reverse=True)

    candidates = [
        ("http_errors", issue("Fix HTTP errors", "Critical", errors, "Broken responses can interrupt user journeys and waste crawl resource.")),
        ("non_indexable_html", issue("Review non-indexable HTML pages", "High", non_indexable, "Confirm each exclusion is intentional; valuable pages should be indexable.")),
        ("missing_titles", issue("Add missing title tags", "High", missing_title, "Titles are a core relevance and search-snippet signal.")),
        ("duplicate_titles", issue("Resolve duplicate title tags", "Medium", [x for group in title_duplicates.values() for x in group], "Distinct titles help search engines and people differentiate pages.")),
        ("missing_meta_descriptions", issue("Add missing meta descriptions", "Medium", missing_meta, "Descriptions support clear and consistent search snippets.")),
        ("duplicate_meta_descriptions", issue("Review duplicate meta descriptions", "Low", [x for group in meta_duplicates.values() for x in group], "Unique descriptions better explain each page's value.")),
        ("missing_h1s", issue("Add missing H1 headings", "Medium", missing_h1, "An H1 provides a clear primary topic and page structure.")),
        ("duplicate_h1s", issue("Review duplicate H1 headings", "Low", [x for group in h1_duplicates.values() for x in group], "Distinct H1s reinforce each page's purpose.")),
        ("missing_canonicals", issue("Add missing canonical URLs", "Medium", missing_canonical, "Canonicals help consolidate duplicate or closely related URLs.")),
        ("non_self_referencing_canonicals", issue("Validate non-self-referencing canonicals", "Medium", non_self_canonical, "These may be intentional, but decide which URL search engines can index.")),
        ("slow_pages", issue(f"Improve pages taking {SLOW_PAGE_SECONDS:g}s or more", "Medium", slow, "Slow responses affect user experience and may constrain crawling.")),
        ("thin_content", issue(f"Review pages below {THIN_CONTENT_WORDS} words", "Low", thin, "Consider improving, consolidating, or intentionally excluding thin pages.")),
        ("orphan_pages", issue("Review HTML pages with zero inlinks", "Medium", orphans, "Pages without discovered internal links are harder for crawlers and visitors to reach.")),
    ]
    actions = [item for key, item in candidates if ACTION_RULES.get(key) and item["affected_urls"]]
    rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    actions.sort(key=lambda item: (rank[item["priority"]], -item["affected_urls"]))

    return {
        "report_metadata": {"generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source_file": str(source), "source_modified_at_utc": datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"), "scope": "Latest preprocessed Screaming Frog Internal:All export"},
        "executive_summary": {"total_urls": len(rows), "html_pages": len(html), "indexable_html_pages": len(html) - len(non_indexable), "non_indexable_html_pages": len(non_indexable), "http_errors": len(errors), "redirects": len(redirects), "priority_actions": len(actions)},
        "crawl_scope": {"content_types": dict(Counter(row.get("content_type", "Unknown") or "Unknown" for row in rows)), "status_codes": dict(Counter(row.get("status_code", "Unknown") or "Unknown" for row in rows))},
        "technical_health": {"http_errors": {"count": len(errors), "sample_urls": urls(errors)}, "redirects": {"count": len(redirects), "sample_urls": urls(redirects)}, "response_time_seconds": stats(html, "response_time"), "page_size_bytes": stats(html, "size_bytes")},
        "indexability": {"by_status": dict(Counter(row.get("indexability", "Unknown") or "Unknown" for row in html)), "non_indexable": {"count": len(non_indexable), "sample_urls": urls(non_indexable)}},
        "on_page": {"titles": {"missing": len(missing_title), "duplicate_groups": len(title_duplicates), "duplicate_urls": sum(map(len, title_duplicates.values())), "short": len(short_titles), "long": len(long_titles)}, "meta_descriptions": {"missing": len(missing_meta), "duplicate_groups": len(meta_duplicates), "duplicate_urls": sum(map(len, meta_duplicates.values())), "short": len(short_metas), "long": len(long_metas)}, "h1s": {"missing": len(missing_h1), "duplicate_groups": len(h1_duplicates), "duplicate_urls": sum(map(len, h1_duplicates.values()))}, "canonicals": {"missing": len(missing_canonical), "non_self_referencing": len(non_self_canonical)}},
        "content_quality": {"word_count": stats(html, "word_count"), "thin_pages": {"count": len(thin), "sample_urls": urls(thin)}, "zero_word_count_pages": {"count": len(zero_words), "sample_urls": urls(zero_words)}},
        "performance": {"slow_page_threshold_seconds": SLOW_PAGE_SECONDS, "slow_pages": {"count": len(slow), "pages": [{"address": row["address"], "response_time_seconds": as_number(row.get("response_time"))} for row in slow[:TOP_PAGES_LIMIT]]}},
        "site_architecture": {"folder_depth": dict(sorted(Counter(as_int(row.get("folder_depth")) for row in html).items())), "orphan_pages": {"count": len(orphans), "sample_urls": urls(orphans)}, "deepest_pages": [{"address": row["address"], "folder_depth": as_int(row.get("folder_depth"))} for row in deepest[:TOP_PAGES_LIMIT]], "largest_pages": [{"address": row["address"], "size_bytes": as_int(row.get("size_bytes"))} for row in largest[:TOP_PAGES_LIMIT]]},
        "priority_actions": actions,
        "screaming_frog_issues": load_issues(source),
    }


def table(lines, rows):
    lines.extend(["| Metric | Value |", "| --- | ---: |"])
    lines.extend(f"| {name} | {value} |" for name, value in rows)
    lines.append("")


def write_issues(lines, issues):
    """Screaming Frog's own issues: a ranked table, then the fix for each high-priority one."""
    lines.extend(["## Screaming Frog issues overview", ""])
    if not issues:
        lines.extend(['No Issues Overview found. Add `"Issues:All"` to BULK in your recipe.', ""])
        return

    plural = lambda word, count: word if count == 1 else (word[:-1] + "ies" if word.endswith("y") else word + "s")
    by_type = ", ".join(f"{count} {plural(kind.lower(), count)}" for kind, count in issues["by_type"].items())
    lines.extend([f"{issues['total_issues']} issues found ({by_type}), ranked by priority.", "",
                  "| Priority | Type | Issue | URLs | % of total |", "| --- | --- | --- | ---: | ---: |"])
    shown = issues["issues"][:ISSUES_LIMIT]
    lines.extend(f"| {i['priority']} | {i['type']} | {i['name'].replace('|', '/')} | {i['urls']} | {i['percent_of_total']:.1f}% |" for i in shown)
    if len(issues["issues"]) > len(shown):
        lines.append(f"\n...and {len(issues['issues']) - len(shown)} more in crawl_analysis.json")
    lines.append("")

    high = [i for i in shown if i["priority"] == "High"]
    if high:
        lines.extend(["### How to fix the high-priority issues", ""])
        lines.extend(f"- **{i['name']}** ({i['urls']} URLs): {' '.join(i['how_to_fix'].split())}" for i in high)
        lines.append("")


def write_markdown(data, path):
    summary, on_page = data["executive_summary"], data["on_page"]
    lines = ["# Crawl intelligence summary", "", f"**Source:** `{data['report_metadata']['source_file']}`", f"**Generated:** {data['report_metadata']['generated_at_utc']}", ""]
    if INCLUDE_EXECUTIVE_SUMMARY:
        lines.extend(["## Executive summary", ""])
        table(lines, [("URLs crawled", summary["total_urls"]), ("HTML pages", summary["html_pages"]), ("Indexable HTML pages", f"{summary['indexable_html_pages']} ({percent(summary['indexable_html_pages'], summary['html_pages'])}%)"), ("Non-indexable HTML pages", summary["non_indexable_html_pages"]), ("HTTP errors", summary["http_errors"]), ("Redirects", summary["redirects"]), ("Prioritised actions", summary["priority_actions"])])
    if INCLUDE_PRIORITISED_ACTIONS:
        lines.extend(["## Prioritised actions", ""])
        if not data["priority_actions"]: lines.append("No enabled alert rules found an issue.\n")
        for action in data["priority_actions"]:
            lines.extend([f"### {action['priority']}: {action['action']} ({action['affected_urls']})", action["rationale"], ""])
            lines.extend(f"- {url}" for url in action["sample_urls"])
            if action["affected_urls"] > len(action["sample_urls"]): lines.append(f"- ...and {action['affected_urls'] - len(action['sample_urls'])} more")
            lines.append("")
    if INCLUDE_ISSUES_OVERVIEW:
        write_issues(lines, data["screaming_frog_issues"])
    if INCLUDE_CRAWL_SCOPE:
        lines.extend(["## Crawl scope", ""])
        table(lines, [(f"HTTP {key}", value) for key, value in sorted(data["crawl_scope"]["status_codes"].items())])
        table(lines, list(data["crawl_scope"]["content_types"].items()))
    if INCLUDE_TECHNICAL_HEALTH:
        health = data["technical_health"]; timing = health["response_time_seconds"]
        lines.extend(["## Technical health", ""])
        table(lines, [("HTTP errors", health["http_errors"]["count"]), ("Redirects", health["redirects"]["count"]), ("Median response time", f"{timing['median']:.2f}s"), ("Average response time", f"{timing['mean']:.2f}s"), ("Slowest response", f"{timing['max']:.2f}s")])
    if INCLUDE_INDEXABILITY:
        lines.extend(["## Indexability", ""]); table(lines, list(data["indexability"]["by_status"].items()))
    if INCLUDE_ON_PAGE:
        lines.extend(["## On-page signals", ""])
        table(lines, [("Missing titles", on_page["titles"]["missing"]), ("Duplicate title groups", on_page["titles"]["duplicate_groups"]), (f"Titles under {SHORT_TITLE_CHARACTERS} characters", on_page["titles"]["short"]), (f"Titles over {LONG_TITLE_CHARACTERS} characters", on_page["titles"]["long"]), ("Missing meta descriptions", on_page["meta_descriptions"]["missing"]), ("Duplicate meta-description groups", on_page["meta_descriptions"]["duplicate_groups"]), (f"Meta descriptions under {SHORT_META_DESCRIPTION_CHARACTERS} characters", on_page["meta_descriptions"]["short"]), (f"Meta descriptions over {LONG_META_DESCRIPTION_CHARACTERS} characters", on_page["meta_descriptions"]["long"]), ("Missing H1s", on_page["h1s"]["missing"]), ("Duplicate H1 groups", on_page["h1s"]["duplicate_groups"]), ("Missing canonicals", on_page["canonicals"]["missing"]), ("Non-self-referencing canonicals", on_page["canonicals"]["non_self_referencing"])])
    if INCLUDE_CONTENT_QUALITY:
        quality = data["content_quality"]; word_count = quality["word_count"]
        lines.extend(["## Content quality", ""]); table(lines, [("Median word count", word_count["median"]), ("Average word count", word_count["mean"]), (f"Pages under {THIN_CONTENT_WORDS} words", quality["thin_pages"]["count"]), ("Pages with zero words", quality["zero_word_count_pages"]["count"])])
    if INCLUDE_PERFORMANCE:
        lines.extend(["## Slow pages", ""])
        slow_pages = data["performance"]["slow_pages"]["pages"]
        lines.extend(f"- {page['address']} - {page['response_time_seconds']:.2f}s" for page in slow_pages)
        lines.append("No HTML pages met the slow-page threshold." if not slow_pages else "")
    if INCLUDE_SITE_ARCHITECTURE:
        architecture = data["site_architecture"]
        lines.extend(["## Site architecture", ""])
        table(lines, [("HTML pages with zero inlinks", architecture["orphan_pages"]["count"]), *[(f"Folder depth {depth}", count) for depth, count in architecture["folder_depth"].items()]])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(settings, folder=None):
    configure(settings)
    source_file = find_source(folder)
    report = build_report(source_file)
    markdown_path = source_file.with_name(MARKDOWN_FILENAME)
    json_path = source_file.with_name(JSON_FILENAME)
    write_markdown(report, markdown_path)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Created human summary: {markdown_path}")
    print(f"Created LLM summary: {json_path}")
