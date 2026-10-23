"""Quick health: the basics for every URL, plus Screaming Frog's own issues list.

A good first recipe. Internal:All (about 20 columns, everything the report needs)
and the Issues Overview: every issue found, its priority, how many URLs, and how to fix it.
"""

from _shared import INTERNAL_CORE, ISSUES_OVERVIEW

DESCRIPTION = "Internal:All plus Screaming Frog's Issues Overview"
REQUIRES = []

# One line per export: the export name, then the columns to keep.
# Comment a line out to skip it, in the crawl and in preprocessing.
# Every export you can use is listed in _engine/reference/export-tabs.md and bulk-exports.md
TABS = {
    "Internal:All": INTERNAL_CORE,
}

BULK = {
    # Also writes a URL list for every issue it finds, into an issues_reports/ folder.
    "Issues:All": ISSUES_OVERVIEW,
}
