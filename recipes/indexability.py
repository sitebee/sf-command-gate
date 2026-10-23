"""Indexability: canonicals, directives, pagination, sitemaps and robots.txt.

Finds what search engines can and can't index, and where the signals disagree.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "Canonicals, noindex and robots directives, pagination, sitemaps, robots.txt blocks"
REQUIRES = ["XML sitemap crawling (for the Sitemaps exports)"]

CANONICALS = {
    "Address": "address",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
    "Canonical Link Element 1": "canonical_url",
    "HTTP Canonical": "http_canonical",
    "Meta Robots 1": "meta_robots",
    "X-Robots-Tag 1": "x_robots_tag",
}

DIRECTIVES = {
    "Address": "address",
    "Meta Robots 1": "meta_robots",
    "X-Robots-Tag 1": "x_robots_tag",
    "Meta Refresh 1": "meta_refresh",
    "Canonical Link Element 1": "canonical_url",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
}

PAGINATION = {
    "Address": "address",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
    'rel="next" 1': "rel_next",
    'rel="prev" 1': "rel_prev",
    "Canonical Link Element 1": "canonical_url",
}

SITEMAPS = {
    "Address": "address",
    "Status Code": "status_code",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
}

BLOCKED = {
    "Address": "address",
    "Status Code": "status_code",
    "Inlinks": "inlinks",
    "Matched Robots.txt Line": "matched_robots_txt_line",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "Canonicals:Missing": CANONICALS,
    "Canonicals:Canonicalised": CANONICALS,
    "Canonicals:Non-Indexable Canonical": CANONICALS,
    "Canonicals:Multiple": CANONICALS,
    "Canonicals:Multiple Conflicting": CANONICALS,
    "Canonicals:Canonical Is Relative": CANONICALS,
    "Canonicals:Outside <head>": CANONICALS,
    "Canonicals:Unlinked": CANONICALS,
    # "Canonicals:Self Referencing": CANONICALS,     # one row per indexable page, large
    # "Canonicals:Contains Canonical": CANONICALS,   # one row per page with a canonical, large

    "Directives:Noindex": DIRECTIVES,
    "Directives:Nofollow": DIRECTIVES,
    "Directives:None": DIRECTIVES,
    "Directives:Outside <head>": DIRECTIVES,
    # "Directives:NoArchive": DIRECTIVES,
    # "Directives:NoSnippet": DIRECTIVES,
    # "Directives:Refresh": DIRECTIVES,

    "Pagination:Non-Indexable": PAGINATION,
    "Pagination:Sequence Error": PAGINATION,
    "Pagination:Non-200 Pagination URLs": PAGINATION,
    "Pagination:Pagination Loop": PAGINATION,
    "Pagination:Unlinked Pagination URLs": PAGINATION,
    # "Pagination:Contains Pagination": PAGINATION,

    "Sitemaps:Non-Indexable URLs in Sitemap": SITEMAPS,
    "Sitemaps:Orphan URLs": SITEMAPS,
    "Sitemaps:URLs not in Sitemap": SITEMAPS,
    "Sitemaps:URLs in Multiple Sitemaps": SITEMAPS,
    # "Sitemaps:URLs in Sitemap": SITEMAPS,

    "Response Codes:Blocked by Robots.txt": BLOCKED,
}

BULK = {
}
