"""Structured data: schema coverage, validation errors, rich result eligibility.

Shows which pages have structured data, which types they use, and what fails
validation.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "Pages with and without schema, types used, validation and rich result errors"
REQUIRES = ["Structured data extraction (Config > Spider > Extraction > Structured Data)"]

STRUCTURED_DATA = {
    "Address": "address",
    "Errors": "errors",
    "Warnings": "warnings",
    "Rich Result Errors": "rich_result_errors",
    "Rich Result Warnings": "rich_result_warnings",
    "Rich Result Features": "rich_result_features",
    "Total Types": "total_types",
    "Unique Types": "unique_types",
    "Type-1": "type_1",
    "Type-2": "type_2",
    "Type-3": "type_3",
    "Indexability": "indexability",
    # "Feature-1": "feature_1",
    # "Type-4": "type_4",
    # "Type-5": "type_5",
    # "Indexability Status": "indexability_status",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "Structured Data:Missing": STRUCTURED_DATA,
    "Structured Data:Validation Errors": STRUCTURED_DATA,
    "Structured Data:Validation Warnings": STRUCTURED_DATA,
    "Structured Data:Parse Errors": STRUCTURED_DATA,
    "Structured Data:Rich Result Validation Errors": STRUCTURED_DATA,
    "Structured Data:Rich Result Validation Warnings": STRUCTURED_DATA,
    "Structured Data:Rich Result Feature Detected": STRUCTURED_DATA,
    "Structured Data:JSON-LD URLs": STRUCTURED_DATA,
    "Structured Data:Microdata URLs": STRUCTURED_DATA,
    "Structured Data:RDFa URLs": STRUCTURED_DATA,
    # "Structured Data:Contains Structured Data": STRUCTURED_DATA,   # every page with schema, large
    # "Structured Data:All": STRUCTURED_DATA,
}

BULK = {
}
