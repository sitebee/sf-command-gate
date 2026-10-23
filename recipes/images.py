"""Images: missing alt text, oversized images, wrong dimensions.

The tab exports list the image files. The bulk exports tell you which PAGE each
image is on, which is what you need to fix it.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "Missing alt text, heavy images, wrongly sized images, and the pages they sit on"
REQUIRES = ["Images crawled (Config > Spider > Crawl > Images)"]

IMAGES = {
    "Address": "address",
    "Size (Bytes)": "size_bytes",
    "IMG Inlinks": "img_inlinks",
    "Dimensions": "dimensions",
    "Indexability": "indexability",
    # "Content Type": "content_type",
    # "Indexability Status": "indexability_status",
}

# Which page (Source) holds which image (Destination).
IMAGE_LINKS = {
    "Source": "source",
    "Destination": "destination",
    "Alt Text": "alt_text",
}

IMAGE_LINKS_WITH_SIZE = {
    "Source": "source",
    "Destination": "destination",
    "Size (Bytes)": "size_bytes",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "Images:Missing Alt Text": IMAGES,
    "Images:Missing Alt Attribute": IMAGES,
    "Images:Alt Text Over X Characters": IMAGES,
    "Images:Over X kB": IMAGES,
    "Images:Incorrectly Sized Images": IMAGES,
    "Images:Missing Size Attributes": IMAGES,
    # "Images:Background Images": IMAGES,
    # "Images:All": IMAGES,
}

BULK = {
    "Images:Images Missing Alt Text Inlinks": IMAGE_LINKS,
    "Images:Images Missing Alt Attribute Inlinks": IMAGE_LINKS,
    "Images:Images Over X kB Inlinks": IMAGE_LINKS_WITH_SIZE,
    # "Images:Images with Alt Text Over X Characters": {"Source": "source", "Destination": "destination", "Alt Text": "alt_text", "Length": "length"},
}
