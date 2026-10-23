"""Change detection: what changed since the previous crawl of this site.

Runs as the "changes" stage. It compares this crawl with the one before it using the CSV
files the gate already keeps in output/, so it needs nothing from Screaming Frog's saved
crawls. It writes change_report.md, change_report.json and changes.csv (every change, one
per line) into the new crawl's folder.

You shouldn't need to edit this file. The switches and thresholds are in gate.py, section 8.
"""

import csv
import json
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = ROOT / "output"

# Raw Screaming Frog column -> tidy name. The preprocessed file already uses the tidy names.
RAW_TO_TIDY = {
    "Address": "address", "Content Type": "content_type", "Status Code": "status_code", "Status": "status",
    "Indexability": "indexability", "Indexability Status": "indexability_status", "Title 1": "title",
    "Meta Description 1": "meta_description", "H1-1": "h1", "Canonical Link Element 1": "canonical_url",
    "Size (Bytes)": "size_bytes", "Word Count": "word_count", "Crawl Depth": "crawl_depth", "Folder Depth": "folder_depth",
    "Inlinks": "inlinks", "Response Time": "response_time", "Redirect URL": "redirect_url", "Hash": "content_hash",
}
SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
ERROR_BUCKETS = {"client error", "server error", "no response"}


def to_float(value):
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return 0.0


def clean(text):
    return " ".join((text or "").split())


def short(text, length=70):
    text = clean(text)
    return text if len(text) <= length else text[:length - 1] + "…"


# ============================================================
# 1. FINDING THE TWO CRAWLS
# ============================================================

def crawl_folders():
    """Crawl folders that have an Internal:All export, oldest first (folder names are timestamps)."""
    if not OUTPUT_ROOT.exists():
        return []
    return sorted(p for p in OUTPUT_ROOT.iterdir() if p.is_dir() and
                  ((p / "internal_all.csv").exists() or (p / "internal_all_preprocessed.csv").exists()))


def site_of(folder):
    """The host most URLs in this crawl belong to, so we only compare a site with itself."""
    for name in ("internal_all_preprocessed.csv", "internal_all.csv"):
        path = folder / name
        if path.exists():
            with path.open(encoding="utf-8-sig", newline="") as file:
                hosts = Counter()
                for position, row in enumerate(csv.DictReader(file)):
                    hosts[urlsplit(row.get("address") or row.get("Address") or "").hostname] += 1
                    if position >= 200:
                        break
            return hosts.most_common(1)[0][0] if hosts else None
    return None


def find_previous(current, against="previous"):
    """The crawl to compare against: a named folder, or the newest earlier crawl of the same site."""
    if against and against != "previous":
        folder = Path(against) if Path(against).exists() else OUTPUT_ROOT / against
        if not folder.exists():
            raise FileNotFoundError(f"Can't find the crawl to compare with: {against}")
        return folder
    site = site_of(current)
    for folder in reversed([f for f in crawl_folders() if f.name < current.name]):
        if site_of(folder) == site:
            return folder
    return None


def load_pages(folder):
    """{address: tidy row} from the raw Internal:All export, or the preprocessed one if that's all there is."""
    for name, mapping in (("internal_all.csv", RAW_TO_TIDY), ("internal_all_preprocessed.csv", None)):
        path = folder / name
        if path.exists():
            pages = {}
            with path.open(encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    tidy = {mapping[key]: value for key, value in row.items() if key in mapping} if mapping else row
                    if tidy.get("address"):
                        pages[tidy["address"]] = tidy
            return pages, name
    return {}, None


def load_issues(folder):
    """{issue name: {urls, type, priority}} from the preprocessed Issues Overview, or None."""
    files = sorted(folder.rglob("issues_overview_report_preprocessed.csv"), key=lambda p: len(p.parts))
    if not files:
        return None
    with files[0].open(encoding="utf-8-sig", newline="") as file:
        return {row["issue_name"]: {"urls": int(to_float(row["urls"])), "type": row["issue_type"], "priority": row["issue_priority"]}
                for row in csv.DictReader(file)}


# ============================================================
# 2. WHAT KIND OF PAGE IS IT
# ============================================================

def bucket(row):
    status = (row.get("status") or "").lower()
    code = int(to_float(row.get("status_code")))
    if status.startswith("blocked by robots"):
        return "blocked by robots.txt"
    if code == 0:
        return "no response"
    return "ok" if code < 300 else "redirect" if code < 400 else "client error" if code < 500 else "server error"


def is_html(row):
    return (row.get("content_type") or "").lower().startswith("text/html")


def describe_status(row):
    return f"{row.get('status_code') or '0'} {row.get('status') or ''}".strip()


def metrics(pages):
    """Headline numbers for one crawl."""
    html = [r for r in pages.values() if is_html(r)]
    buckets = Counter(bucket(r) for r in pages.values())
    times = [to_float(r.get("response_time")) for r in html if (r.get("response_time") or "").strip()]
    words = [to_float(r.get("word_count")) for r in html if (r.get("word_count") or "").strip()]
    return {
        "URLs in the crawl": len(pages), "HTML pages": len(html),
        "Indexable HTML pages": sum(1 for r in html if r.get("indexability") == "Indexable"),
        "Non-indexable HTML pages": sum(1 for r in html if r.get("indexability") != "Indexable"),
        "Client errors (4xx)": buckets["client error"], "Server errors (5xx)": buckets["server error"],
        "No response": buckets["no response"], "Redirects": buckets["redirect"],
        "Blocked by robots.txt": buckets["blocked by robots.txt"],
        "Average HTML response time (s)": round(statistics.mean(times), 3) if times else 0,
        "Average HTML word count": round(statistics.mean(words)) if words else 0,
        "Total size (MB)": round(sum(to_float(r.get("size_bytes")) for r in pages.values()) / 2**20, 1),
    }


# ============================================================
# 3. COMPARING PAGE BY PAGE
# ============================================================

def compare_pages(old, new, settings):
    """Every change between two crawls, as a list of dicts, plus a note about noisy content hashes."""
    watch = {key: True for key in ("status", "indexability", "titles", "meta_descriptions", "h1s", "canonicals", "redirects",
                                   "content", "links", "depth", "response_time", "size")}
    watch.update(settings.get("CHANGES_WATCH", {}))
    word_percent = settings.get("CHANGES_WORD_COUNT_PERCENT", 20)
    size_percent = settings.get("CHANGES_SIZE_PERCENT", 30)
    slower_by = settings.get("CHANGES_RESPONSE_SECONDS", 0.5)

    changes = []
    add = lambda url, severity, kind, field, before, after: changes.append(
        {"url": url, "severity": severity, "change": kind, "field": field, "before": before, "after": after})
    hash_only = 0

    for url in sorted(set(new) - set(old)):
        row = new[url]
        add(url, "Info", "New URLs found", "url", "", describe_status(row))
    for url in sorted(set(old) - set(new)):
        row = old[url]
        was_page = bucket(row) == "ok" and is_html(row) and row.get("indexability") == "Indexable"
        add(url, "High" if was_page else "Low", "Indexable pages no longer found" if was_page else "Other URLs no longer found",
            "url", describe_status(row), "not in this crawl")

    for url in sorted(set(old) & set(new)):
        before, after = old[url], new[url]
        old_bucket, new_bucket = bucket(before), bucket(after)

        if watch["status"] and old_bucket != new_bucket:
            if new_bucket in ERROR_BUCKETS and old_bucket not in ERROR_BUCKETS:
                add(url, "Critical", "New errors", "status", describe_status(before), describe_status(after))
            elif old_bucket in ERROR_BUCKETS and new_bucket not in ERROR_BUCKETS:
                add(url, "Info", "Errors fixed", "status", describe_status(before), describe_status(after))
            elif new_bucket == "blocked by robots.txt":
                add(url, "High", "Newly blocked by robots.txt", "status", describe_status(before), "blocked by robots.txt")
            elif old_bucket == "blocked by robots.txt":
                add(url, "Medium", "No longer blocked by robots.txt", "status", "blocked by robots.txt", describe_status(after))
            else:
                add(url, "Medium", "Status changed", "status", describe_status(before), describe_status(after))

        if watch["redirects"] and old_bucket == new_bucket == "redirect" and clean(before.get("redirect_url")) != clean(after.get("redirect_url")):
            add(url, "Medium", "Redirect target changed", "redirect_url", short(before.get("redirect_url")), short(after.get("redirect_url")))

        if old_bucket != "ok" or new_bucket != "ok":
            continue   # the rest only makes sense for pages that worked both times

        if watch["indexability"] and before.get("indexability") != after.get("indexability"):
            now_indexable = after.get("indexability") == "Indexable"
            detail = lambda row: f"{row.get('indexability')}" + (f" ({row['indexability_status']})" if row.get("indexability_status") else "")
            add(url, "Info" if now_indexable else "High", "Became indexable" if now_indexable else "Became non-indexable",
                "indexability", detail(before), detail(after))

        if is_html(after):
            for key, field, label in (("titles", "title", "Title changed"), ("meta_descriptions", "meta_description", "Meta description changed"),
                                      ("h1s", "h1", "H1 changed"), ("canonicals", "canonical_url", "Canonical changed")):
                if watch[key] and field in before and field in after and clean(before[field]) != clean(after[field]):
                    add(url, "High" if field == "canonical_url" else "Medium", label, field, short(before[field]), short(after[field]))

            if watch["content"]:
                old_words, new_words = to_float(before.get("word_count")), to_float(after.get("word_count"))
                moved_words = abs(new_words - old_words) >= 25 and old_words and abs(new_words - old_words) / old_words * 100 >= word_percent
                if moved_words:
                    add(url, "Medium", "Word count changed", "word_count", int(old_words), int(new_words))
                if before.get("content_hash") and after.get("content_hash") and before["content_hash"] != after["content_hash"]:
                    if moved_words or before.get("size_bytes") != after.get("size_bytes"):
                        add(url, "Medium", "Content changed", "content_hash", "different", "different")
                    else:
                        hash_only += 1

            if watch["links"] and "inlinks" in before and "inlinks" in after:
                old_in, new_in = to_float(before["inlinks"]), to_float(after["inlinks"])
                if old_in > 0 and new_in == 0:
                    add(url, "High", "Became an orphan page", "inlinks", int(old_in), 0)
                elif old_in >= 10 and new_in <= old_in / 2:
                    add(url, "Medium", "Lost internal links", "inlinks", int(old_in), int(new_in))

            if watch["depth"]:
                field = "crawl_depth" if "crawl_depth" in before and "crawl_depth" in after else "folder_depth"
                if field in before and field in after and (before[field] or "").strip() and (after[field] or "").strip() \
                        and to_float(after[field]) - to_float(before[field]) >= 2:
                    add(url, "Low", "Pushed deeper in the site", field, int(to_float(before[field])), int(to_float(after[field])))

        if watch["response_time"] and (before.get("response_time") or "").strip() and (after.get("response_time") or "").strip():
            old_time, new_time = to_float(before["response_time"]), to_float(after["response_time"])
            if new_time - old_time >= slower_by and new_time >= 2 * old_time:
                add(url, "Low", "Slower responses", "response_time", f"{old_time:.2f}s", f"{new_time:.2f}s")

        if watch["size"] and "size_bytes" in before and "size_bytes" in after:
            old_size, new_size = to_float(before["size_bytes"]), to_float(after["size_bytes"])
            if old_size and abs(new_size - old_size) >= 5120 and abs(new_size - old_size) / old_size * 100 >= size_percent:
                add(url, "Low", "Page size changed", "size_bytes", f"{old_size / 1024:.0f} KB", f"{new_size / 1024:.0f} KB")

    return changes, hash_only


def compare_issues(old, new):
    """New, resolved, worse and better issues between two Issues Overviews."""
    if old is None or new is None:
        return None
    result = {"new": [], "resolved": [], "worse": [], "better": []}
    for name in sorted(set(old) | set(new)):
        before, after = old.get(name, {}).get("urls", 0), new.get(name, {}).get("urls", 0)
        info = new.get(name) or old.get(name)
        row = {"issue": name, "type": info["type"], "priority": info["priority"], "before": before, "after": after}
        if before == 0 and after > 0:
            result["new"].append(row)
        elif before > 0 and after == 0:
            result["resolved"].append(row)
        elif after > before:
            result["worse"].append(row)
        elif after < before:
            result["better"].append(row)
    rank = {"High": 0, "Medium": 1, "Low": 2}
    for rows in result.values():
        rows.sort(key=lambda r: (rank.get(r["priority"], 3), -abs(r["after"] - r["before"])))
    return result


# ============================================================
# 4. RUNNING IT AND WRITING THE REPORT
# ============================================================

def group_findings(changes, limit):
    groups = {}
    for change in changes:
        group = groups.setdefault(change["change"], {"change": change["change"], "severity": change["severity"], "count": 0, "examples": []})
        group["count"] += 1
        if len(group["examples"]) < limit:
            group["examples"].append({key: change[key] for key in ("url", "before", "after")})
    return sorted(groups.values(), key=lambda g: (SEVERITY_ORDER[g["severity"]], -g["count"]))


DESCRIPTIONS = {
    "New errors": "Pages that worked in the last crawl and now return an error or no response.",
    "Errors fixed": "Pages that were returning errors and now work.",
    "Indexable pages no longer found": "Indexable pages from the last crawl that this crawl didn't reach. Removed, or no longer linked.",
    "Other URLs no longer found": "Other URLs from the last crawl that this crawl didn't reach.",
    "New URLs found": "URLs this crawl found that the last one didn't.",
    "Became non-indexable": "Pages that were indexable and now aren't (noindex, canonicalised, and so on).",
    "Became indexable": "Pages that weren't indexable and now are.",
    "Newly blocked by robots.txt": "URLs that can now no longer be crawled because of robots.txt.",
    "No longer blocked by robots.txt": "URLs that robots.txt now lets the crawler reach.",
    "Status changed": "Pages that moved between status types, such as working to redirecting.",
    "Redirect target changed": "Redirects that now point somewhere else.",
    "Canonical changed": "Pages whose canonical URL changed. This changes which URL search engines are told to index.",
    "Title changed": "Pages whose title tag changed.", "Meta description changed": "Pages whose meta description changed.",
    "H1 changed": "Pages whose first H1 changed.",
    "Content changed": "Pages whose content hash changed together with the word count or size.",
    "Word count changed": "Pages whose word count moved by more than the threshold in gate.py.",
    "Became an orphan page": "Pages that had internal links and now have none.",
    "Lost internal links": "Pages that lost at least half of their internal links.",
    "Pushed deeper in the site": "Pages that are now two or more clicks further from the start.",
    "Slower responses": "Pages that now respond much more slowly.", "Page size changed": "Pages whose size changed a lot.",
}


def signed(value):
    return f"+{value:,}" if value > 0 else f"{value:,}" if value < 0 else "0"


def table(lines, headers, rows):
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    lines.extend("| " + " | ".join(str(cell).replace("|", "/") for cell in row) + " |" for row in rows)
    lines.append("")


def render(report):
    current, previous = report["current"], report["previous"]
    lines = ["# Changes since the previous crawl", "",
             f"**This crawl:** `{current['folder']}` ({current['urls']:,} URLs)  ", f"**Compared with:** `{previous['folder']}` ({previous['urls']:,} URLs)  ",
             f"**Generated:** {report['generated_at']}", ""]

    findings = report["findings"]
    actionable = [g for g in findings if g["severity"] in ("Critical", "High")]
    if not findings:
        lines += ["No changes found between these two crawls.", ""]
    else:
        lines += ["## At a glance", ""]
        lines += [f"- **{g['severity']}**: {g['change']} ({g['count']:,})" for g in findings] + [""]
        if not actionable:
            lines += ["Nothing critical or high priority changed.", ""]

    table_rows = []
    for name, now in report["summary"]["now"].items():
        before = report["summary"]["before"][name]
        change = round(now - before, 3)
        table_rows.append((name, f"{before:,}", f"{now:,}", ("+" if change > 0 else "") + f"{change:,}" if change else "no change"))
    lines += ["## Headline numbers", ""]
    table(lines, ["Measure", "Previous", "Now", "Change"], table_rows)

    if findings:
        lines += ["## What changed", ""]
        for group in findings:
            lines += [f"### {group['severity']}: {group['change']} ({group['count']:,})", DESCRIPTIONS.get(group["change"], ""), ""]
            table(lines, ["URL", "Before", "After"], [(e["url"], e["before"], e["after"]) for e in group["examples"]])
            if group["count"] > len(group["examples"]):
                lines += [f"...and {group['count'] - len(group['examples']):,} more in changes.csv", ""]

    if report.get("content_hash_note"):
        lines += ["## A note on content hashes", "", report["content_hash_note"], ""]

    issues = report.get("issues")
    lines += ["## Screaming Frog issues", ""]
    if issues is None:
        lines += ["One of the two crawls has no Issues Overview, so issues weren't compared. Add `\"Issues:All\"` to BULK in your recipe.", ""]
    elif not any(issues.values()):
        lines += ["The same issues were found, with the same number of URLs each.", ""]
    else:
        for label, key in (("New issues", "new"), ("Resolved issues", "resolved"), ("Issues that got worse", "worse"), ("Issues that improved", "better")):
            if issues[key]:
                lines += [f"**{label}**", ""]
                table(lines, ["Priority", "Type", "Issue", "Before", "Now", "Change"],
                      [(r["priority"], r["type"], r["issue"], f"{r['before']:,}", f"{r['after']:,}", signed(r["after"] - r["before"])) for r in issues[key]])

    lines += ["## Notes", "",
              "- Both crawls are read from the Internal:All export in their folders, so the comparison covers what that export holds.",
              "- If a huge number of URLs were added or removed, the two crawls probably had different settings or scope, and the other results will be noisy.",
              "- Every change, one per line, is in changes.csv."]
    return "\n".join(lines)


def run(settings, folder=None, against=None):
    """Compare a crawl with the one before it. Returns the crawl folder used."""
    crawls = crawl_folders()
    if folder is None:
        if not crawls:
            raise FileNotFoundError(f"No crawls under {OUTPUT_ROOT}. Run a crawl first.")
        folder = crawls[-1]
    folder = Path(folder)

    previous = find_previous(folder, against or settings.get("CHANGES_AGAINST", "previous"))
    if previous is None:
        print("No earlier crawl of this site to compare with yet. Run again later and this will show what changed.")
        return folder

    new_pages, new_source = load_pages(folder)
    old_pages, old_source = load_pages(previous)
    if not new_pages or not old_pages:
        raise FileNotFoundError(f"Both crawls need an Internal:All export. Missing in {folder.name if not new_pages else previous.name}.")

    # If one crawl only has the preprocessed file, it has fewer columns. Every check below
    # only runs on fields both crawls actually have, so the two still compare fairly.
    changes, hash_only = compare_pages(old_pages, new_pages, settings)
    limit = settings.get("CHANGES_SAMPLE_LIMIT", 10)
    findings = group_findings(changes, limit)
    before, now = metrics(old_pages), metrics(new_pages)

    note = None
    if hash_only:
        note = (f"{hash_only:,} pages have a different content hash but the same word count and size. That usually means something dynamic in the "
                "page, like a token or a timestamp, rather than a real content change, so they're not listed as changes.")

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "current": {"folder": folder.name, "urls": len(new_pages)}, "previous": {"folder": previous.name, "urls": len(old_pages)},
        "summary": {"before": before, "now": now}, "findings": findings, "total_changes": len(changes),
        "content_hash_only_differences": hash_only, "content_hash_note": note,
        "issues": compare_issues(load_issues(previous), load_issues(folder)),
    }

    (folder / "change_report.md").write_text(render(report), encoding="utf-8")
    (folder / "change_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    with (folder / "changes.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["severity", "change", "url", "field", "before", "after"])
        writer.writeheader()
        writer.writerows(sorted(changes, key=lambda c: (SEVERITY_ORDER[c["severity"]], c["change"], c["url"])))

    print(f"Compared {folder.name} with {previous.name}: {len(changes):,} changes.")
    for group in findings[:6]:
        print(f"  {group['severity']:<8} {group['change']}: {group['count']:,}")
    print(f"Created change report: {folder / 'change_report.md'}")
    return folder
