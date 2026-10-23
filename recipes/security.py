"""Security: HTTPS, mixed content, missing security headers, unsafe links.

Covers the checks in Screaming Frog's Security tab, plus the bulk exports that
say which page loads each insecure resource.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "HTTP URLs, mixed content, insecure forms and missing security headers"
REQUIRES = []

SECURITY = {
    "Address": "address",
    "Content Type": "content_type",
    "Status Code": "status_code",
    "HTTP Version": "http_version",
    "Indexability": "indexability",
    # "Status": "status",
    # "Indexability Status": "indexability_status",
    # "Canonical Link Element 1": "canonical_url",
    # "Meta Robots 1": "meta_robots",
    # "X-Robots-Tag 1": "x_robots_tag",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "Security:HTTP URLs": SECURITY,
    "Security:Mixed Content": SECURITY,
    "Security:Form on HTTP URL": SECURITY,
    "Security:Form URL Insecure": SECURITY,
    "Security:Missing HSTS Header": SECURITY,
    "Security:Missing Content-Security-Policy Header": SECURITY,
    "Security:Missing X-Content-Type-Options Header": SECURITY,
    "Security:Missing X-Frame-Options Header": SECURITY,
    "Security:Missing Secure Referrer-Policy Header": SECURITY,
    "Security:Bad Content Type": SECURITY,
    "Security:Protocol-Relative Resource Links": SECURITY,
    "Security:Unsafe Cross-Origin Links": SECURITY,
    # "Security:HTTPS URLs": SECURITY,     # every secure URL, large
}

# Which page (Source) loads which insecure resource (Destination).
BULK = {
    "Security:Mixed Content": {
        "Type": "type",
        "Source": "source",
        "Destination": "destination",
    },
    "Security:Form URL Insecure": {
        "Source": "source",
        "Form Action Link": "form_action_link",
    },
    "Security:Unsafe Cross-Origin Links": {
        "Source": "source",
        "Destination": "destination",
        "Anchor": "anchor",
        "Target": "target",
        "Rel": "rel",
    },
}
