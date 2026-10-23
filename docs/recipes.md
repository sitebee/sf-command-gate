# Recipes

A recipe is one small Python file in `recipes/`. It says which exports to pull from a crawl and which
columns to keep from each. Pick one with `RECIPE = "..."` in `gate.py`, or for a single run with
`python gate.py --recipe on-page`.

## The format

```python
"""On-page: page titles and meta descriptions."""

from _shared import INTERNAL_CORE

DESCRIPTION = "Titles and meta descriptions: missing, duplicate, too long or short"
REQUIRES = []

TITLES = {
    "Address": "address",
    "Title 1": "title",
    "Title 1 Length": "title_length",
    # "Title 1 Pixel Width": "title_pixel_width",
}

TABS = {
    "Internal:All": INTERNAL_CORE,
    "Page Titles:Missing": TITLES,
    "Page Titles:Duplicate": TITLES,
    # "Page Titles:Over X Pixels": TITLES,
}

BULK = {
}
```

| Part | What it is |
| --- | --- |
| `DESCRIPTION` | One line, shown by `python gate.py recipes`. |
| `REQUIRES` | What the recipe needs. An entry starting `--use-` (for example `--use-pagespeed`) is checked: if that API isn't switched on in `gate.py`, the run stops before the crawl. Any other entry is a note shown at the start of the run. |
| a column set | A dictionary of `"Screaming Frog column": "tidy name"`. Comment a column out to leave it out. |
| `TABS` | Exports for `--export-tabs`. The name on the left is exactly what the CLI expects. |
| `BULK` | Exports for `--bulk-export`. |

**One line, one export.** Comment an export out and it disappears from the crawl command **and** from
preprocessing. There is no second list to keep in step.

**`None` as the column set** exports a file but doesn't preprocess it: `"Response Codes:All": None`.

**Every recipe should include `"Internal:All": INTERNAL_CORE`.** The analysis report and change detection are
built from it. `INTERNAL_CORE` lives in `recipes/_shared.py`, and the report depends on the columns switched on there.

## Build your own

1. `python gate.py new my-recipe` copies the template.
2. Find exports in `_engine/reference/export-tabs.md` and `_engine/reference/bulk-exports.md`. They are the full lists
   the Screaming Frog CLI accepts.
3. See an export's columns: `python gate.py columns "Response Codes:Client Error (4xx)"`. It prints a line to
   paste into `TABS` (or `BULK`), with every column commented out. Take the `#` off the ones you want.
4. `python gate.py check my-recipe` catches typos and columns that don't exist, without crawling.
5. `python gate.py --dry-run --recipe my-recipe` shows the command it would run.

If you have already crawled with an export, `columns` reads the header from your own crawl. Otherwise it uses
the reference map.

## Naming rules worth knowing

- **Thresholds use a literal `X`.** The export is `Page Titles:Over X Characters`, not `Over 60 Characters`. The number
  comes from your Screaming Frog config and appears in the file name, for example `page_titles_over_60_characters.csv`.
  The gate matches names ignoring those numbers.
- **24 names exist as both a tab export and a bulk export**, with different columns (for example
  `Images:Incorrectly Sized Images`). That is why `TABS` and `BULK` are separate.
- **Bulk exports often drop the group name from the file.** `Links:All Inlinks` writes `all_inlinks.csv`. The gate tries
  both forms.
- **`Issues:All`** writes `issues_overview_report.csv` (and a URL list for each issue in an `issues_reports/` folder).
  It is matched by a built-in alias.

## Limits

- The column lists in `_engine/reference/` came from **one crawl, with one configuration, on Screaming Frog 24.3.** Columns that
  depend on integrations (PageSpeed, Search Console, GA4) or on features you have switched on may differ in yours.
- Filters for features that need setting up first (Custom Search, Custom Extraction, Custom JavaScript, AI) are listed but weren't
  mapped. If you use them, `python gate.py columns` will read the header from your own crawl.
- Screaming Frog rejects an export whose feature isn't enabled in your config, and the crawl stops at startup with a message
  naming it (see [troubleshooting](troubleshooting.md)).
- Link-level bulk exports (all inlinks, all outlinks, anchor text) are one row per link. On a big site they run to millions of
  rows, so they start switched off.
- An empty export is normal. It means that check found no issues.

## Sharing a recipe

A good recipe has a clear `DESCRIPTION`, lists real needs in `REQUIRES`, keeps only the columns people use, and passes
`python gate.py check`. If you contribute one, say which Screaming Frog version and config features you tested it with.
