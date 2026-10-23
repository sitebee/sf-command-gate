"""Content quality: duplicates, thin pages, readability, soft 404s.

Exact duplicates, low content and readability work with a standard crawl.
Near duplicates, semantic similarity and spelling and grammar need extra
Screaming Frog features switched on, so they start commented out.
"""

from _shared import INTERNAL_CORE

DESCRIPTION = "Exact duplicates, thin content, readability, soft 404s (near-duplicate and spelling checks optional)"
REQUIRES = []

EXACT_DUPLICATES = {
    "Address": "address",
    "Hash": "content_hash",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
}

LOW_CONTENT = {
    "Address": "address",
    "Word Count": "word_count",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",
}

READABILITY = {
    "Address": "address",
    "Word Count": "word_count",
    "Sentence Count": "sentence_count",
    "Average Words Per Sentence": "average_words_per_sentence",
    "Flesch Reading Ease Score": "flesch_reading_ease_score",
    "Readability": "readability",
    "Indexability": "indexability",
}

SOFT_404 = {
    "Address": "address",
    "Title 1": "title",
    "H1-1": "h1",
    "Word Count": "word_count",
    "Indexability": "indexability",
}

PLACEHOLDER = {
    "Address": "address",
    "Occurrences": "occurrences",
    "Indexability": "indexability",
}

# Needs near-duplicate detection (Config > Content > Duplicates)
NEAR_DUPLICATES = {
    "Address": "address",
    "Closest Near Duplicate Match": "closest_near_duplicate_match",
    "No. Near Duplicates": "near_duplicate_count",
    "Indexability": "indexability",
    "Canonical Link Element 1": "canonical_url",
}

# Needs semantic similarity (Config > Content > Embeddings)
SEMANTIC = {
    "Address": "address",
    "Closest Semantically Similar Address": "closest_semantically_similar_address",
    "Semantic Similarity Score": "semantic_similarity_score",
    "No. Semantically Similar": "semantically_similar_count",
    "Indexability": "indexability",
}

# Needs spelling and grammar checking (Config > Content > Spelling & Grammar)
SPELLING = {
    "Address": "address",
    "Spelling Errors": "spelling_errors",
    "Language": "language",
    "Indexability": "indexability",
}

GRAMMAR = {
    "Address": "address",
    "Grammar Errors": "grammar_errors",
    "Language": "language",
    "Indexability": "indexability",
}

# One line per export. Comment a line out to skip it, in the crawl and in preprocessing.
TABS = {
    "Internal:All": INTERNAL_CORE,

    "Content:Exact Duplicates": EXACT_DUPLICATES,
    "Content:Low Content Pages": LOW_CONTENT,
    "Content:Readability Difficult": READABILITY,
    "Content:Readability Very Difficult": READABILITY,
    "Content:Soft 404 Pages": SOFT_404,
    "Content:Lorem Ipsum Placeholder": PLACEHOLDER,

    # "Content:Near Duplicates": NEAR_DUPLICATES,
    # "Content:Semantically Similar": SEMANTIC,
    # "Content:Spelling Errors": SPELLING,
    # "Content:Grammar Errors": GRAMMAR,
}

# Pairs of pages: which page (Address) duplicates which (Exact Duplicate Address).
BULK = {
    "Content:Exact Duplicates": {
        "Address": "address",
        "Exact Duplicate Address": "exact_duplicate_address",
        "Similarity": "similarity",
    },
    # "Content:Near Duplicates": {"Address": "address", "Near Duplicate Address": "near_duplicate_address", "Similarity": "similarity"},
}
