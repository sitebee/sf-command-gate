"""URL hygiene: parameters, uppercase, underscores, long and messy URLs.

Finds URL patterns that cause duplicate content, wasted crawl budget or
tracking noise.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "Parameters, uppercase, underscores, spaces, long and repetitive URLs"
REQUIRES = []

URLS = {
    "Address": "address",
    "Status Code": "status_code",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
    "Length": "url_length",
    "Canonical Link Element 1": "canonical_url",
    # "Content Type": "content_type",
    # "Status": "status",
    # "Hash": "content_hash",
    # "URL Encoded Address": "url_encoded_address",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "URL:Parameters": URLS,
    "URL:Uppercase": URLS,
    "URL:Underscores": URLS,
    "URL:Multiple Slashes": URLS,
    "URL:Contains Space": URLS,
    "URL:Non ASCII Characters": URLS,
    "URL:Over X Characters": URLS,
    "URL:Repetitive Path": URLS,
    "URL:Internal Search": URLS,
    "URL:GA Tracking Parameters": URLS,
    "URL:Broken Bookmark": URLS,
    # "URL:All": URLS,     # every URL, large
}

BULK = {
}
