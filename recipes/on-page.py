"""On-page: page titles, meta descriptions, H1s and H2s.

Pulls the issue lists (missing, duplicate, too long, too short, multiple) for the
four elements that most on-page audits start with.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "Titles, meta descriptions, H1s and H2s: missing, duplicate, too long or short"
REQUIRES = []

TITLES = {
    "Address": "address",
    "Occurrences": "occurrences",
    "Title 1": "title",
    "Title 1 Length": "title_length",
    "Title 1 Pixel Width": "title_pixel_width",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
}

DESCRIPTIONS = {
    "Address": "address",
    "Occurrences": "occurrences",
    "Meta Description 1": "meta_description",
    "Meta Description 1 Length": "meta_description_length",
    "Meta Description 1 Pixel Width": "meta_description_pixel_width",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
}

H1S = {
    "Address": "address",
    "Occurrences": "occurrences",
    "H1-1": "h1",
    "H1-1 Length": "h1_length",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
}

H2S = {
    "Address": "address",
    "Occurrences": "occurrences",
    "H2-1": "h2_1",
    "H2-1 Length": "h2_1_length",
    "H2-2": "h2_2",
    "H2-2 Length": "h2_2_length",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "Page Titles:Missing": TITLES,
    "Page Titles:Duplicate": TITLES,
    "Page Titles:Multiple": TITLES,
    "Page Titles:Over X Characters": TITLES,
    "Page Titles:Below X Characters": TITLES,
    "Page Titles:Same as H1": TITLES,
    # "Page Titles:Over X Pixels": TITLES,
    # "Page Titles:Below X Pixels": TITLES,
    # "Page Titles:Outside <head>": TITLES,

    "Meta Description:Missing": DESCRIPTIONS,
    "Meta Description:Duplicate": DESCRIPTIONS,
    "Meta Description:Multiple": DESCRIPTIONS,
    "Meta Description:Over X Characters": DESCRIPTIONS,
    "Meta Description:Below X Characters": DESCRIPTIONS,
    # "Meta Description:Over X Pixels": DESCRIPTIONS,
    # "Meta Description:Below X Pixels": DESCRIPTIONS,
    # "Meta Description:Outside <head>": DESCRIPTIONS,

    "H1:Missing": H1S,
    "H1:Duplicate": H1S,
    "H1:Multiple": H1S,
    "H1:Over X Characters": H1S,
    "H1:Non-Sequential": H1S,
    # "H1:Alt Text in H1": H1S,

    "H2:Missing": H2S,
    "H2:Duplicate": H2S,
    "H2:Multiple": H2S,
    "H2:Non-Sequential": H2S,
    # "H2:Over X Characters": H2S,
}

BULK = {
}
