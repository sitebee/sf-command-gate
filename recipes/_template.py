"""One line: what is this recipe for?"""

from _shared import INTERNAL_CORE

DESCRIPTION = "Describe this recipe in a few words"

# Integrations the recipe depends on, e.g. ["PageSpeed API", "Search Console"].
# They must be enabled in your Screaming Frog config. Leave empty if none.
REQUIRES = []

# A column set: the columns to keep from an export, and what to call them.
# Print the real columns for any export with:  python gate.py columns "Page Titles:Missing"
TITLES = {
    "Address": "address",
    "Title 1": "title",
    "Title 1 Length": "title_length",
    # "Title 1 Pixel Width": "title_pixel_width",
}

# One line per export: the export name, then its column set.
# Comment a line out to skip it, in the crawl and in preprocessing.
# Every export you can use is listed in reference/export-tabs.md and reference/bulk-exports.md
TABS = {
    "Internal:All": INTERNAL_CORE,
    "Page Titles:Missing": TITLES,
    # "Page Titles:Duplicate": TITLES,
}

BULK = {
    # "Links:All Inlinks": {"Source": "source", "Destination": "destination", "Anchor": "anchor"},
}
