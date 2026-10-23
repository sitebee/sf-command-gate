"""Errors and redirects: broken pages, redirect chains, and who links to them.

The tab exports list the broken or redirecting URLs. The bulk exports list the
links pointing at them, so you know which pages to fix.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "4xx, 5xx, redirects, redirect chains and loops, plus the links that point at them"
REQUIRES = []

RESPONSES = {
    "Address": "address",
    "Status Code": "status_code",
    "Status": "status",
    "Inlinks": "inlinks",
    "Response Time": "response_time",
    "Redirect URL": "redirect_url",
    "Redirect Type": "redirect_type",
}

# The links pointing at a URL: which page (Source) links to the problem URL (Destination).
LINKS_TO_PROBLEMS = {
    "Source": "source",
    "Destination": "destination",
    "Anchor": "anchor",
    "Status Code": "status_code",
    "Status": "status",
    "Link Position": "link_position",
    # "Follow": "follow",
    # "Link Path": "link_path",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "Response Codes:Client Error (4xx)": RESPONSES,
    "Response Codes:Server Error (5xx)": RESPONSES,
    "Response Codes:No Response": RESPONSES,
    "Response Codes:Blocked Resource": RESPONSES,
    "Response Codes:Redirection (3xx)": RESPONSES,
    "Response Codes:Redirection (JavaScript)": RESPONSES,
    "Response Codes:Redirection (Meta Refresh)": RESPONSES,
    "Response Codes:Redirection (HTTP Refresh)": RESPONSES,
    "Response Codes:Internal Redirect Chain": RESPONSES,
    "Response Codes:Internal Redirect Loop": RESPONSES,
    # "Response Codes:Success (2xx)": RESPONSES,     # every working URL, large
}

BULK = {
    "Response Codes:Internal & External:Client Error (4xx) Inlinks": LINKS_TO_PROBLEMS,
    "Response Codes:Internal & External:Server Error (5xx) Inlinks": LINKS_TO_PROBLEMS,
    "Response Codes:Internal & External:No Response Inlinks": LINKS_TO_PROBLEMS,
    "Response Codes:Internal & External:Redirection (3xx) Inlinks": LINKS_TO_PROBLEMS,
    # "Response Codes:Internal:Internal Redirect Chain Inlinks": LINKS_TO_PROBLEMS,
    # "Response Codes:Internal:Internal Redirect Loop Inlinks": LINKS_TO_PROBLEMS,
}
