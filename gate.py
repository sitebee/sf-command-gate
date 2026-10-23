"""PYTHON COMMAND GATE FOR SCREAMING FROG CLI

THE ONE FILE YOU EDIT.

Comment a line out with #, or take the # off to switch it on.
Every option sits on ONE line, so a single # is always safe.

    python gate.py                       run everything below
    python gate.py --dry-run             check and print the command, run nothing
    python gate.py --recipe on-page      use a different recipe for this run
    python gate.py preprocess analyse    run only these stages on the newest crawl
    python gate.py profile               resource report for the newest crawl (section 7)
    python gate.py changes               what changed since the previous crawl (section 8)

    python gate.py recipes               list the recipes you can use
    python gate.py check                 check every recipe (no crawl)
    python gate.py new my-recipe         start your own recipe
    python gate.py columns "Internal:All"    print a column picker for any export
"""

from pathlib import Path

HERE = Path(__file__).parent


# ============================================================
# 1. THE SITE
# ============================================================

CRAWL_URL = "https://example.com/"
PROJECT_NAME = "My First Crawl"
TASK_NAME = "Weekly Crawl"


# ============================================================
# 2. THE RECIPE - what to pull from the crawl
#    Run  python gate.py recipes  to see them all.
# ============================================================

RECIPE = "quick-health"


# ============================================================
# 3. THE CRAWL
# ============================================================

CONFIG_FILE = str(HERE / "config" / "weekly-crawl.seospiderconfig")   # save one from the Screaming Frog app
URL_LIST = str(HERE / "inputs" / "urls.txt")                          # only used in list mode

CRAWL = [
    # ACTION - choose ONE
    "--crawl", CRAWL_URL,
    # "--crawl-list", URL_LIST,

    "--headless",

    # Use your saved Screaming Frog configuration
    "--config", CONFIG_FILE,

    # Save the full crawl for the desktop app and MCP
    # "--save-crawl",

    # ORGANISATION - choose ONE
    "--timestamped-output",     # keep every run in its own folder
    # "--overwrite",            # replace the previous output

    "--project-name", PROJECT_NAME,
    "--task-name", TASK_NAME,
]


# ============================================================
# 4. APIS - switch on the ones you want during the crawl
#    Sign in to each one once in the Screaming Frog app. It keeps the credentials,
#    so nothing secret ever goes in this file.
#    A recipe that needs an API will tell you if it isn't switched on here.
# ============================================================

APIS = [
    # "--use-pagespeed",
    # "--use-google-search-console", "your@google-account.com", "https://example.com/",
    # "--use-google-analytics-4", "your@google-account.com", "account", "property", "data-stream",
    # "--use-majestic",
    # "--use-ahrefs",
    # "--use-mozscape",

    # AI (prompts are set up in the Screaming Frog app)
    # "--use-openai",
    # "--use-gemini",
    # "--use-ollama",
    # "--use-anthropic",
]


# ============================================================
# 5. THE PIPELINE
# ============================================================

STAGES = [
    "crawl",         # crawl with Screaming Frog
    "profile",       # OPTIONAL: resource report (CPU, RAM, connections, bandwidth, CDN, WAF). See section 7.
    "preprocess",    # keep and rename the columns the recipe asks for
    "analyse",       # write crawl_analysis.md and crawl_analysis.json
    "changes",       # what changed since the previous crawl of this site (section 8)
]

# True keeps the raw export files after preprocessing, so you can switch on more
# columns later without recrawling. False deletes them after a successful run.
KEEP_ORIGINAL_FILES = True

# Only if Screaming Frog is installed somewhere unusual:
SCREAMING_FROG = None
# SCREAMING_FROG = r"D:\Tools\Screaming Frog SEO Spider\ScreamingFrogSEOSpiderCli.exe"


# ============================================================
# 6. THE REPORT - what analyse writes
#    The report reads the Internal:All columns, so keep that export in your recipe.
# ============================================================

# Sections: comment out any you do not need.
INCLUDE_EXECUTIVE_SUMMARY = True
INCLUDE_CRAWL_SCOPE = True
INCLUDE_TECHNICAL_HEALTH = True
INCLUDE_INDEXABILITY = True
INCLUDE_ON_PAGE = True
INCLUDE_CONTENT_QUALITY = True
INCLUDE_PERFORMANCE = True
INCLUDE_SITE_ARCHITECTURE = True
INCLUDE_PRIORITISED_ACTIONS = True
INCLUDE_ISSUES_OVERVIEW = True       # Screaming Frog's own issues list. Needs "Issues:All" in the recipe.

# Thresholds: adjust these to match the site and your standards.
SLOW_PAGE_SECONDS = 2.0
THIN_CONTENT_WORDS = 300
SHORT_TITLE_CHARACTERS = 30
LONG_TITLE_CHARACTERS = 60
SHORT_META_DESCRIPTION_CHARACTERS = 70
LONG_META_DESCRIPTION_CHARACTERS = 160
TOP_PAGES_LIMIT = 10
ISSUES_LIMIT = None                  # None lists every Screaming Frog issue. Set a number (e.g. 15) for a shorter report.

# Alerts: set one to False to remove it from the prioritised actions.
ACTION_RULES = {
    "http_errors": True,
    "non_indexable_html": True,
    "missing_titles": True,
    "duplicate_titles": True,
    "missing_meta_descriptions": True,
    "duplicate_meta_descriptions": True,
    "missing_h1s": True,
    "duplicate_h1s": True,
    "missing_canonicals": True,
    "non_self_referencing_canonicals": True,
    "slow_pages": True,
    "thin_content": True,
    "orphan_pages": True,
}


# ============================================================
# 7. THE PROFILER - an optional resource report
#    Switch it on by taking the # off "profile" in STAGES (section 5). It records what the
#    crawl needed: CPU, RAM, processes, TCP connections, bandwidth, time, requests by file
#    type, plus the technologies, CDN and WAF it ran into. Handy for sizing a machine.
#    Live measurements need:  pip install psutil   (everything else works without it)
# ============================================================

PROFILE_INTERVAL = 1.0      # seconds between samples while the crawl runs
PROFILE_PROBE = True        # send 3 requests to the site (homepage twice, robots.txt) to spot its technologies, CDN and WAF


# ============================================================
# 8. CHANGE DETECTION - what changed since the last crawl
#    The "changes" stage in STAGES compares this crawl with the previous crawl of the same
#    site, using the CSV files already in output/. It writes change_report.md,
#    change_report.json and changes.csv (every change, one per line). The first crawl of a
#    site has nothing to compare with, so it just says so. It does not need --save-crawl.
# ============================================================

CHANGES_AGAINST = "previous"        # "previous", or the name of a crawl folder in output/ to compare with

# Which kinds of change to look for. Set one to False to ignore it.
CHANGES_WATCH = {
    "status": True,             # working -> error, newly blocked by robots.txt, status changes
    "indexability": True,       # became indexable or non-indexable
    "titles": True,
    "meta_descriptions": True,
    "h1s": True,
    "canonicals": True,
    "redirects": True,          # a redirect now points somewhere else
    "content": True,            # word count and content changes
    "links": True,              # lost internal links, became an orphan
    "depth": True,              # pushed deeper in the site
    "response_time": True,      # got much slower
    "size": True,               # page size changed a lot
}

CHANGES_WORD_COUNT_PERCENT = 20     # report a word count change bigger than this %
CHANGES_SIZE_PERCENT = 30           # report a page size change bigger than this %
CHANGES_RESPONSE_SECONDS = 0.5      # report a response that got this much slower (and at least 2x)
CHANGES_SAMPLE_LIMIT = 10           # example URLs shown per change in the report (changes.csv has them all)


if __name__ == "__main__":
    from _engine import cli

    cli.main({name: value for name, value in globals().items() if name.isupper()})
