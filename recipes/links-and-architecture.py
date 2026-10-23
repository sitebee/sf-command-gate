"""Links and architecture: crawl depth, internal linking, anchor text.

The tab exports are one row per page. The bulk exports are one row per link and
can be very large on big sites, so they start switched off.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "Crawl depth, internal linking, nofollow, anchor text and link-level exports"
REQUIRES = []

LINK_METRICS = {
    "Address": "address",
    "Indexability": "indexability",
    # "Indexability Status": "indexability_status",
    "Crawl Depth": "crawl_depth",
    "Link Score": "link_score",
    "Inlinks": "inlinks",
    "Unique Inlinks": "unique_inlinks",
    # "Unique JS Inlinks": "unique_js_inlinks",
    # "% of Total": "percent_of_total",
    "Outlinks": "outlinks",
    "Unique Outlinks": "unique_outlinks",
    # "Unique JS Outlinks": "unique_js_outlinks",
    "External Outlinks": "external_outlinks",
    # "Unique External Outlinks": "unique_external_outlinks",
    # "Unique External JS Outlinks": "unique_external_js_outlinks",
}

# One row per link: which page (Source) links to which URL (Destination), with what anchor.
LINKS = {
    "Source": "source",
    "Destination": "destination",
    "Anchor": "anchor",
    "Status Code": "status_code",
    "Follow": "follow",
    "Link Position": "link_position",
    # "Type": "type",
    # "Alt Text": "alt_text",
    # "Target": "target",
    # "Rel": "rel",
    # "Path Type": "path_type",
    # "Link Path": "link_path",
    # "Link Origin": "link_origin",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "Links:Pages With High Crawl Depth": LINK_METRICS,
    "Links:Pages Without Internal Outlinks": LINK_METRICS,
    "Links:Pages With High Internal Outlinks": LINK_METRICS,
    "Links:Pages With High External Outlinks": LINK_METRICS,
    "Links:Non-Indexable Page Inlinks Only": LINK_METRICS,
    "Links:Internal Nofollow Inlinks Only": LINK_METRICS,
    "Links:Follow & Nofollow Internal Inlinks To Page": LINK_METRICS,
    "Links:Pages With Uncrawlable Internal Outlinks": LINK_METRICS,
    "Links:Outlinks To Localhost": LINK_METRICS,
    "Links:Non-Descriptive Anchor Text In Internal Outlinks": LINK_METRICS,
    # "Links:Internal Outlinks With No Anchor Text": LINK_METRICS,
    # "Links:Internal Nofollow Outlinks": LINK_METRICS,
    # "Links:All": LINK_METRICS,                      # every page, large
}

# Link-level exports. On a big site these run to millions of rows, so switch them on deliberately.
BULK = {
    # "Links:All Inlinks": LINKS,
    # "Links:All Outlinks": LINKS,
    # "Links:All Anchor Text": LINKS,
    # "Links:External Links": LINKS,
}
