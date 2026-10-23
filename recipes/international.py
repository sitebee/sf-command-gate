"""International: hreflang errors for multi-language and multi-region sites.

Checks return links, self references, language codes, x-default and whether
hreflang points at pages that work.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "Hreflang: missing return links, bad codes, no x-default, non-200 and non-canonical targets"
REQUIRES = []

# The export has 51 columns for up to 11 hreflang entries per page. These are the first entry;
# print the rest with:  python gate.py columns "Hreflang:Missing"
HREFLANG = {
    "Address": "address",
    "Occurrences": "occurrences",
    "HTML hreflang 1": "html_hreflang_1",
    "HTML hreflang 1 URL": "html_hreflang_1_url",
    "Sitemap hreflang 1": "sitemap_hreflang_1",
    "Sitemap hreflang 1 URL": "sitemap_hreflang_1_url",
    "Indexability": "indexability",
    # "Title 1": "title",
    # "HTTP hreflang 1": "http_hreflang_1",
    # "HTTP hreflang 1 URL": "http_hreflang_1_url",
    # "HTML hreflang 2": "html_hreflang_2",
    # "HTML hreflang 2 URL": "html_hreflang_2_url",
    # "Indexability Status": "indexability_status",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "Hreflang:Missing": HREFLANG,
    "Hreflang:Missing Return Links": HREFLANG,
    "Hreflang:Missing Self Reference": HREFLANG,
    "Hreflang:Missing X-Default": HREFLANG,
    "Hreflang:Incorrect Language & Region Codes": HREFLANG,
    "Hreflang:Inconsistent Language & Region Return Links": HREFLANG,
    "Hreflang:Non-200 hreflang URLs": HREFLANG,
    "Hreflang:Noindex Return Links": HREFLANG,
    "Hreflang:Non-Canonical Return Links": HREFLANG,
    "Hreflang:Not Using Canonical": HREFLANG,
    "Hreflang:Unlinked hreflang URLs": HREFLANG,
    "Hreflang:Outside <head>": HREFLANG,
    # "Hreflang:Multiple Entries": HREFLANG,
    # "Hreflang:Contains hreflang": HREFLANG,     # every page with hreflang, large
    # "Hreflang:All": HREFLANG,
}

BULK = {
}
