# Screaming Frog export columns

Generated from a real crawl of a demo e-commerce site (about 26,000 URLs) with Screaming Frog 24.3 and the author's configuration. Exports whose filters are not configured, or not available in this config, are listed in `skipped-not-exported.txt`. Custom Extraction, Custom JavaScript, Custom Search and AI filters need configuring first. Exports shown by file name (ending .csv) are real exports whose name could not be matched back to an option.

- Exports mapped: 589  (tab filters and bulk exports)
- Distinct columns: 320
- Exports not mapped: 942

## Tab exports (`--export-tabs`)

**1 export(s)**: `AI:All`

7 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | Crawl Timestamp

**18 export(s)**: `AMP:All`, `AMP:Contains Disallowed HTML`, `AMP:Indexable`, `AMP:Missing <body> Tag`, `AMP:Missing <head> Tag`, `AMP:Missing <html amp> Tag` and 12 more

18 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | Title 1 | Title 1 Length | Title 1 Pixel Width | H1-1 | H1-1 Length | Canonical Link Element 1 | Size (Bytes) | Word Count | Text Ratio | Crawl Depth | Link Score | Response Time

**57 export(s)**: `Accessibility:<blink> Elements Deprecated & Must Not Be Used`, `Accessibility:<dl> Must Only Have Ordered <dt> & <dd> Groups`, `Accessibility:<dt> & <dd> Elements Must Be Contained by <dl>`, `Accessibility:<object> Elements Require Alternate Text`, `Accessibility:<th> Element Requires Associated Data Cells`, `Accessibility:<video> Elements Require <track> For Captions` and 51 more

9 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | All Violations | WCAG 2.0 A Violations | PSI Request Status

**29 export(s)**: `Accessibility:ARIA Dialog & Alertdialog Require Accessible Name`, `Accessibility:ARIA Role Should Be Appropriate For Element`, `Accessibility:ARIA Treeitem Nodes Require Accessible Name`, `Accessibility:Accesskey Attribute Value Must Be Unique`, `Accessibility:All Page Content Must Be Contained By Landmarks`, `Accessibility:Alt Text Should Not Be Repeated As Text` and 23 more

9 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | All Violations | Best Practice Violations | PSI Request Status

**4 export(s)**: `Accessibility:Accessibility Score Good`, `Accessibility:Accessibility Score Needs Improvement`, `Accessibility:Accessibility Score Poor`, `Accessibility:All`

14 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | All Violations | Best Practice Violations | WCAG 2.0 A Violations | WCAG 2.0 AA Violations | WCAG 2.0 AAA Violations | WCAG 2.1 AA Violations | WCAG 2.2 AA Violations | PSI Request Status

**3 export(s)**: `Accessibility:Autocomplete Attribute Must Be Used Correctly`, `Accessibility:Inline Text Spacing Must Be Adjustable`, `accessibility_wcag_2_1_aa_violation.csv`

9 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | All Violations | WCAG 2.1 AA Violations | PSI Request Status

**4 export(s)**: `Accessibility:Delayed Meta Refresh Must Not Be Used`, `Accessibility:Links With Same Accessible Name`, `Accessibility:Text Requires Higher Color Contrast Ratio`, `Accessibility:WCAG 2.0 AAA Violation`

9 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | All Violations | WCAG 2.0 AAA Violations | PSI Request Status

**4 export(s)**: `Accessibility:Lang Attribute Requires Valid Value`, `Accessibility:Meta Viewport Zoom & Scaling Disabled`, `Accessibility:Text Requires Higher Color Contrast to Background`, `accessibility_wcag_2_0_aa_violation.csv`

9 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | All Violations | WCAG 2.0 AA Violations | PSI Request Status

**2 export(s)**: `Accessibility:Touch Targets Require Sufficient Size & Spacing`, `accessibility_wcag_2_2_aa_violation.csv`

9 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | All Violations | WCAG 2.2 AA Violations | PSI Request Status

**18 export(s)**: `Analytics:All`, `Analytics:Bounce Rate Above 70%`, `Analytics:No GA Data`, `Analytics:Non-Indexable with GA Data`, `Analytics:Orphan URLs`, `Analytics:Sessions Above 0` and 12 more

5 columns: Address | Status Code | Title 1 | Indexability | Indexability Status

**13 export(s)**: `Canonicals:All`, `Canonicals:Canonical Is Relative`, `Canonicals:Canonicalised`, `Canonicals:Contains Canonical`, `Canonicals:Contains Fragment URL`, `Canonicals:Invalid Attribute In Annotation` and 7 more

12 columns: Address | Occurrences | Indexability | Indexability Status | Canonical Link Element 1 | HTTP Canonical | Meta Robots 1 | X-Robots-Tag 1 | rel="next" 1 | rel="prev" 1 | HTTP rel="next" 1 | HTTP rel="prev" 1

**1 export(s)**: `Change Detection:All`

25 columns: Address | Current Indexability | Previous Indexability | Current Page Title | Previous Page Title | Current Meta Description | Previous Meta Description | Current H1 | Previous H1 | Current Word Count | Previous Word Count | Current Crawl Depth | Previous Crawl Depth | Current Inlinks | Previous Inlinks | Current Unique Inlinks | Previous Unique Inlinks | Current Outlinks | Previous Outlinks | Current Unique Outlinks | Previous Unique Outlinks | Current External Outlinks | Previous External Outlinks | Current Unique External Outlinks | Previous Unique External Outlinks

**1 export(s)**: `Change Detection:Content`

10 columns: Address | Similarity Match % | Change % | Current Word Count | Previous Word Count | Current Indexability | Current Indexability Status | Previous Indexability | Previous Indexability Status | Crawl Timestamp

**1 export(s)**: `Change Detection:Crawl Depth`

6 columns: Address | Previous Crawl Depth | Current Crawl Depth | Change | Change % | Crawl Timestamp

**1 export(s)**: `Change Detection:External Outlinks`

6 columns: Address | Current External Outlinks | Previous External Outlinks | Change | Change % | Crawl Timestamp

**1 export(s)**: `Change Detection:H1`

8 columns: Address | Current H1 | Previous H1 | Current Indexability | Current Indexability Status | Previous Indexability | Previous Indexability Status | Crawl Timestamp

**1 export(s)**: `Change Detection:Indexability`

9 columns: Address | Status Code | Current Indexability | Current Indexability Status | Previous Indexability | Previous Indexability Status | Canonical Link Element 1 | Meta Robots 1 | Crawl Timestamp

**1 export(s)**: `Change Detection:Inlinks`

6 columns: Address | Current Inlinks | Previous Inlinks | Change | Change % | Crawl Timestamp

**1 export(s)**: `Change Detection:Internal Outlinks`

6 columns: Address | Current Outlinks | Previous Outlinks | Change | Change % | Crawl Timestamp

**1 export(s)**: `Change Detection:Meta Description`

8 columns: Address | Current Meta Description | Previous Meta Description | Current Indexability | Current Indexability Status | Previous Indexability | Previous Indexability Status | Crawl Timestamp

**1 export(s)**: `Change Detection:Page Titles`

8 columns: Address | Current Page Title | Previous Page Title | Current Indexability | Current Indexability Status | Previous Indexability | Previous Indexability Status | Crawl Timestamp

**1 export(s)**: `Change Detection:Structured Data Unique Types`

6 columns: Address | Current Unique Types | Previous Unique Types | Change | Change % | Crawl Timestamp

**1 export(s)**: `Change Detection:Unique External Outlinks`

6 columns: Address | Current Unique External Outlinks | Previous Unique External Outlinks | Change | Change % | Crawl Timestamp

**1 export(s)**: `Change Detection:Unique Inlinks`

6 columns: Address | Current Unique Inlinks | Previous Unique Inlinks | Change | Change % | Crawl Timestamp

**1 export(s)**: `Change Detection:Unique Internal Outlinks`

6 columns: Address | Current Unique Outlinks | Previous Unique Outlinks | Change | Change % | Crawl Timestamp

**1 export(s)**: `Change Detection:Word Count`

10 columns: Address | Current Word Count | Previous Word Count | Change | Change % | Current Indexability | Current Indexability Status | Previous Indexability | Previous Indexability Status | Crawl Timestamp

**1 export(s)**: `Content:All`

19 columns: Address | Word Count | Sentence Count | Average Words Per Sentence | Flesch Reading Ease Score | Readability | Closest Near Duplicate Match | No. Near Duplicates | Closest Semantically Similar Address | Semantic Similarity Score | No. Semantically Similar | Semantic Relevance Score | Total Language Errors | Spelling Errors | Grammar Errors | Language | Hash | Indexability | Indexability Status

**1 export(s)**: `Content:Exact Duplicates`

4 columns: Address | Hash | Indexability | Indexability Status

**1 export(s)**: `Content:Grammar Errors`

5 columns: Address | Grammar Errors | Language | Indexability | Indexability Status

**1 export(s)**: `Content:Lorem Ipsum Placeholder`

4 columns: Address | Occurrences | Indexability | Indexability Status

**1 export(s)**: `Content:Low Content Pages`

4 columns: Address | Word Count | Indexability | Indexability Status

**1 export(s)**: `Content:Low Relevance Content`

4 columns: Address | Semantic Relevance Score | Indexability | Indexability Status

**1 export(s)**: `Content:Near Duplicates`

6 columns: Address | Closest Near Duplicate Match | No. Near Duplicates | Indexability | Indexability Status | Canonical Link Element 1

**2 export(s)**: `Content:Readability Difficult`, `Content:Readability Very Difficult`

8 columns: Address | Word Count | Sentence Count | Average Words Per Sentence | Flesch Reading Ease Score | Readability | Indexability | Indexability Status

**1 export(s)**: `Content:Semantically Similar`

6 columns: Address | Closest Semantically Similar Address | Semantic Similarity Score | No. Semantically Similar | Indexability | Indexability Status

**1 export(s)**: `Content:Soft 404 Pages`

11 columns: Address | Title 1 | Title 1 Length | Title 1 Pixel Width | H1-1 | H1-1 Length | H2-1 | H2-1 Length | Word Count | Indexability | Indexability Status

**1 export(s)**: `Content:Spelling Errors`

5 columns: Address | Spelling Errors | Language | Indexability | Indexability Status

**1 export(s)**: `Custom Extraction:All`

3 columns: Address | Status Code | Status

**2 export(s)**: `Custom JavaScript:All`, `Custom Search:All`

4 columns: Address | Content Type | Status Code | Status

**18 export(s)**: `Directives:All`, `Directives:Follow`, `Directives:Index`, `Directives:Max-Image-Preview`, `Directives:Max-Snippet`, `Directives:Max-Video-Preview` and 12 more

9 columns: Address | Occurrences | Meta Robots 1 | X-Robots-Tag 1 | Meta Refresh 1 | Canonical Link Element 1 | HTTP Canonical | Indexability | Indexability Status

**12 export(s)**: `External:All`, `External:CSS`, `External:Fonts`, `External:HTML`, `External:Images`, `External:JavaScript` and 6 more

6 columns: Address | Content Type | Status Code | Status | Crawl Depth | Inlinks

**7 export(s)**: `H1:All`, `H1:Alt Text in H1`, `H1:Duplicate`, `H1:Missing`, `H1:Multiple`, `H1:Non-Sequential` and 1 more

6 columns: Address | Occurrences | H1-1 | H1-1 Length | Indexability | Indexability Status

**6 export(s)**: `H2:All`, `H2:Duplicate`, `H2:Missing`, `H2:Multiple`, `H2:Non-Sequential`, `H2:Over X Characters`

8 columns: Address | Occurrences | H2-1 | H2-1 Length | H2-2 | H2-2 Length | Indexability | Indexability Status

**2 export(s)**: `Hreflang:All`, `Hreflang:Contains hreflang`

51 columns: Address | Title 1 | Occurrences | HTML hreflang 1 | HTML hreflang 1 URL | HTTP hreflang 1 | HTTP hreflang 1 URL | Sitemap hreflang 1 | Sitemap hreflang 1 URL | Indexability | Indexability Status | HTML hreflang 2 | HTML hreflang 2 URL | HTML hreflang 3 | HTML hreflang 3 URL | HTML hreflang 4 | HTML hreflang 4 URL | HTML hreflang 5 | HTML hreflang 5 URL | HTML hreflang 6 | HTML hreflang 6 URL | HTML hreflang 7 | HTML hreflang 7 URL | HTML hreflang 8 | HTML hreflang 8 URL | HTML hreflang 9 | HTML hreflang 9 URL | HTML hreflang 10 | HTML hreflang 10 URL | HTML hreflang 11 | HTML hreflang 11 URL | Sitemap hreflang 2 | Sitemap hreflang 2 URL | Sitemap hreflang 3 | Sitemap hreflang 3 URL | Sitemap hreflang 4 | Sitemap hreflang 4 URL | Sitemap hreflang 5 | Sitemap hreflang 5 URL | Sitemap hreflang 6 | Sitemap hreflang 6 URL | Sitemap hreflang 7 | Sitemap hreflang 7 URL | Sitemap hreflang 8 | Sitemap hreflang 8 URL | Sitemap hreflang 9 | Sitemap hreflang 9 URL | Sitemap hreflang 10 | Sitemap hreflang 10 URL | Sitemap hreflang 11 | Sitemap hreflang 11 URL

**13 export(s)**: `Hreflang:Inconsistent Language & Region Return Links`, `Hreflang:Incorrect Language & Region Codes`, `Hreflang:Missing`, `Hreflang:Missing Return Links`, `Hreflang:Missing Self Reference`, `Hreflang:Missing X-Default` and 7 more

51 columns: Address | Title 1 | Occurrences | HTML hreflang 1 | HTML hreflang 1 URL | HTTP hreflang 1 | HTTP hreflang 1 URL | Sitemap hreflang 1 | Sitemap hreflang 1 URL | Indexability | Indexability Status | HTML hreflang 2 | HTML hreflang 2 URL | HTML hreflang 3 | HTML hreflang 3 URL | HTML hreflang 4 | HTML hreflang 4 URL | HTML hreflang 5 | HTML hreflang 5 URL | HTML hreflang 6 | HTML hreflang 6 URL | Sitemap hreflang 2 | Sitemap hreflang 2 URL | Sitemap hreflang 3 | Sitemap hreflang 3 URL | Sitemap hreflang 4 | Sitemap hreflang 4 URL | Sitemap hreflang 5 | Sitemap hreflang 5 URL | Sitemap hreflang 6 | Sitemap hreflang 6 URL | HTML hreflang 7 | HTML hreflang 7 URL | HTML hreflang 8 | HTML hreflang 8 URL | HTML hreflang 9 | HTML hreflang 9 URL | HTML hreflang 10 | HTML hreflang 10 URL | HTML hreflang 11 | HTML hreflang 11 URL | Sitemap hreflang 7 | Sitemap hreflang 7 URL | Sitemap hreflang 8 | Sitemap hreflang 8 URL | Sitemap hreflang 9 | Sitemap hreflang 9 URL | Sitemap hreflang 10 | Sitemap hreflang 10 URL | Sitemap hreflang 11 | Sitemap hreflang 11 URL

**8 export(s)**: `Images:All`, `Images:Alt Text Over X Characters`, `Images:Background Images`, `Images:Incorrectly Sized Images`, `Images:Missing Alt Attribute`, `Images:Missing Alt Text` and 2 more

7 columns: Address | Content Type | Size (Bytes) | IMG Inlinks | Indexability | Indexability Status | Dimensions

**12 export(s)**: `Internal:All`, `Internal:CSS`, `Internal:Fonts`, `Internal:HTML`, `Internal:Images`, `Internal:JavaScript` and 6 more

72 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | Title 1 | Title 1 Length | Title 1 Pixel Width | Meta Description 1 | Meta Description 1 Length | Meta Description 1 Pixel Width | Meta Keywords 1 | Meta Keywords 1 Length | H1-1 | H1-1 Length | H2-1 | H2-1 Length | H2-2 | H2-2 Length | Meta Robots 1 | X-Robots-Tag 1 | Meta Refresh 1 | Canonical Link Element 1 | rel="next" 1 | rel="prev" 1 | HTTP rel="next" 1 | HTTP rel="prev" 1 | amphtml Link Element | Size (Bytes) | Transferred (Bytes) | Total Transferred (Bytes) | CO2 (mg) | Carbon Rating | Word Count | Sentence Count | Average Words Per Sentence | Flesch Reading Ease Score | Readability | Text Ratio | Crawl Depth | Folder Depth | Link Score | Inlinks | Unique Inlinks | Unique JS Inlinks | % of Total | Outlinks | Unique Outlinks | Unique JS Outlinks | External Outlinks | Unique External Outlinks | Unique External JS Outlinks | Closest Near Duplicate Match | No. Near Duplicates | Spelling Errors | Grammar Errors | Hash | Response Time | Last Modified | Redirect URL | Redirect Type | Cookies | Language | HTTP Version | Mobile Alternate Link | Closest Semantically Similar Address | Semantic Similarity Score | No. Semantically Similar | Semantic Relevance Score | URL Encoded Address | Crawl Timestamp

**1 export(s)**: `JavaScript:All`

30 columns: Address | Status Code | Status | HTML Word Count | Rendered HTML Word Count | Word Count Change | JS Word Count % | HTML Title | Rendered HTML Title | HTML H1 | Rendered HTML H1 | HTML Meta Description | Rendered HTML Meta Description | HTML Canonical | Rendered HTML Canonical | Unique Inlinks | Unique JS Inlinks | Unique Outlinks | Unique JS Outlinks | Unique External Outlinks | Unique External JS Outlinks | HTML Meta Robots 1 | Rendered HTML Meta Robots 1 | Pretty URL | Ugly URL | JS Error | JS Warning | JS Info | JS Debug | JS Issue

**2 export(s)**: `JavaScript:Canonical Mismatch`, `JavaScript:Canonical Only in Rendered HTML`

7 columns: Address | HTML Canonical | Rendered HTML Canonical | Indexability | Indexability Status | Status Code | Status

**1 export(s)**: `JavaScript:Contains JavaScript Content`

9 columns: Address | HTML Word Count | Rendered HTML Word Count | Word Count Change | JS Word Count % | Indexability | Indexability Status | Status Code | Status

**1 export(s)**: `JavaScript:Contains JavaScript Links`

11 columns: Address | Unique Inlinks | Unique JS Inlinks | Unique Outlinks | Unique JS Outlinks | Unique External Outlinks | Unique External JS Outlinks | Indexability | Indexability Status | Status Code | Status

**2 export(s)**: `JavaScript:H1 Only in Rendered HTML`, `JavaScript:H1 Updated by JavaScript`

7 columns: Address | HTML H1 | Rendered HTML H1 | Indexability | Indexability Status | Status Code | Status

**2 export(s)**: `JavaScript:Meta Description Only in Rendered HTML`, `JavaScript:Meta Description Updated by JavaScript`

7 columns: Address | HTML Meta Description | Rendered HTML Meta Description | Indexability | Indexability Status | Status Code | Status

**2 export(s)**: `JavaScript:Nofollow Only in Original HTML`, `JavaScript:Noindex Only in Original HTML`

7 columns: Address | HTML Meta Robots 1 | Rendered HTML Meta Robots 1 | Indexability | Indexability Status | Status Code | Status

**2 export(s)**: `JavaScript:Page Title Only in Rendered HTML`, `JavaScript:Page Title Updated by JavaScript`

7 columns: Address | HTML Title | Rendered HTML Title | Indexability | Indexability Status | Status Code | Status

**33 export(s)**: `JavaScript:Pages with Blocked Resources`, `Response Codes:All`, `Response Codes:Blocked Resource`, `Response Codes:Client Error (4xx)`, `Response Codes:External All`, `Response Codes:External Blocked Resource` and 27 more

10 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | Inlinks | Response Time | Redirect URL | Redirect Type

**3 export(s)**: `JavaScript:Pages with Chrome Issues`, `JavaScript:Pages with JavaScript Errors`, `JavaScript:Pages with JavaScript Warnings`

8 columns: Address | Indexability | Indexability Status | Status Code | Status | JS Error | JS Warning | JS Issue

**2 export(s)**: `JavaScript:Uses Old AJAX Crawling Scheme Meta Fragment Tag`, `JavaScript:Uses Old AJAX Crawling Scheme URLs`

4 columns: Pretty URL | Ugly URL | Status Code | Status

**1 export(s)**: `Link Metrics:All`

3 columns: Address | Status Code | Title 1

**13 export(s)**: `Links:All`, `Links:Follow & Nofollow Internal Inlinks To Page`, `Links:Internal Nofollow Inlinks Only`, `Links:Internal Nofollow Outlinks`, `Links:Internal Outlinks With No Anchor Text`, `Links:Non-Descriptive Anchor Text In Internal Outlinks` and 7 more

15 columns: Address | Indexability | Indexability Status | Crawl Depth | Link Score | Inlinks | Unique Inlinks | Unique JS Inlinks | % of Total | Outlinks | Unique Outlinks | Unique JS Outlinks | External Outlinks | Unique External Outlinks | Unique External JS Outlinks

**9 export(s)**: `Meta Description:All`, `Meta Description:Below X Characters`, `Meta Description:Below X Pixels`, `Meta Description:Duplicate`, `Meta Description:Missing`, `Meta Description:Multiple` and 3 more

7 columns: Address | Occurrences | Meta Description 1 | Meta Description 1 Length | Meta Description 1 Pixel Width | Indexability | Indexability Status

**4 export(s)**: `Meta Keywords:All`, `Meta Keywords:Duplicate`, `Meta Keywords:Missing`, `Meta Keywords:Multiple`

6 columns: Address | Occurrences | Meta Keywords 1 | Meta Keywords 1 Length | Indexability | Indexability Status

**1 export(s)**: `Mobile:All`

3 columns: Address | PSI Request Status | Mobile Alternate Link

**9 export(s)**: `Mobile:Contains Unsupported Plugins`, `Sitemaps:All`, `Sitemaps:Non-Indexable URLs in Sitemap`, `Sitemaps:Orphan URLs`, `Sitemaps:URLs in Multiple Sitemaps`, `Sitemaps:URLs in Sitemap` and 3 more

6 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status

**6 export(s)**: `Mobile:Content Not Sized Correctly`, `Mobile:Illegible Font Size`, `Mobile:Target Size`, `Mobile:Viewport Not Set`, `PageSpeed:All`, `PageSpeed:Request Errors`

2 columns: Address | PSI Request Status

**1 export(s)**: `Mobile:Mobile Alternate Link`

7 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | Mobile Alternate Link

**10 export(s)**: `Page Titles:All`, `Page Titles:Below X Characters`, `Page Titles:Below X Pixels`, `Page Titles:Duplicate`, `Page Titles:Missing`, `Page Titles:Multiple` and 4 more

7 columns: Address | Occurrences | Title 1 | Title 1 Length | Title 1 Pixel Width | Indexability | Indexability Status

**19 export(s)**: `PageSpeed:Avoid Enormous Network Payloads`, `PageSpeed:Document Request Latency`, `PageSpeed:Duplicated JavaScript`, `PageSpeed:Font Display`, `PageSpeed:Forced Reflow`, `PageSpeed:Improve Image Delivery` and 13 more

1 columns: Address

**11 export(s)**: `Pagination:All`, `Pagination:Contains Pagination`, `Pagination:First Page`, `Pagination:Multiple Pagination URLs`, `Pagination:Non-200 Pagination URLs`, `Pagination:Non-Indexable` and 5 more

11 columns: Address | Indexability | Indexability Status | rel="next" 1 | HTTP rel="next" 1 | rel="prev" 1 | HTTP rel="prev" 1 | Canonical Link Element 1 | HTTP Canonical | Meta Robots 1 | X-Robots-Tag 1

**3 export(s)**: `Response Codes:Blocked by Robots.txt`, `Response Codes:External Blocked by Robots.txt`, `Response Codes:Internal Blocked by Robots.txt`

5 columns: Address | Status Code | Status | Inlinks | Matched Robots.txt Line

**14 export(s)**: `Security:All`, `Security:Bad Content Type`, `Security:Form URL Insecure`, `Security:Form on HTTP URL`, `Security:HTTP URLs`, `Security:HTTPS URLs` and 8 more

10 columns: Address | Content Type | Status Code | Status | HTTP Version | Indexability | Indexability Status | Canonical Link Element 1 | Meta Robots 1 | X-Robots-Tag 1

**12 export(s)**: `Structured Data:All`, `Structured Data:Contains Structured Data`, `Structured Data:JSON-LD URLs`, `Structured Data:Microdata URLs`, `Structured Data:Missing`, `Structured Data:Parse Errors` and 6 more

36 columns: Address | Errors | Warnings | Rich Result Errors | Rich Result Warnings | Rich Result Features | Feature-1 | Total Types | Unique Types | Type-1 | Type-2 | Type-3 | Type-4 | Type-5 | Type-6 | Type-7 | Type-8 | Type-9 | Type-10 | Type-11 | Type-12 | Type-13 | Type-14 | Type-15 | Type-16 | Type-17 | Type-18 | Type-19 | Type-20 | Type-21 | Type-22 | Type-23 | Type-24 | Type-25 | Indexability | Indexability Status

**12 export(s)**: `URL:All`, `URL:Broken Bookmark`, `URL:Contains Space`, `URL:GA Tracking Parameters`, `URL:Internal Search`, `URL:Multiple Slashes` and 6 more

10 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | Hash | Length | Canonical Link Element 1 | URL Encoded Address

**11 export(s)**: `Validation:<body> Element Preceding <html>`, `Validation:<head> Not First In <html> Element`, `Validation:All`, `Validation:High Carbon Rating`, `Validation:Invalid HTML Elements in <head>`, `Validation:Missing <body> Tag` and 5 more

11 columns: Address | Content Type | Status Code | Status | Indexability | Indexability Status | Size (Bytes) | Transferred (Bytes) | Total Transferred (Bytes) | CO2 (mg) | Carbon Rating

## Bulk exports (`--bulk-export`)

**82 export(s)**: `AMP:Indexable Inlinks`, `AMP:Missing Canonical to Non-AMP Inlinks`, `AMP:Missing Non-AMP Return Link Inlinks`, `AMP:Non-200 Response Inlinks`, `AMP:Non-Indexable Inlinks`, `Canonicals:Canonical Is Relative Inlinks` and 76 more

16 columns: Type | Source | Destination | Size (Bytes) | Alt Text | Anchor | Status Code | Status | Crawlability | Follow | Target | Rel | Path Type | Link Path | Link Position | Link Origin

**14 export(s)**: `Accessibility:All Incomplete`, `Accessibility:All Violations`, `best_practice_all_incomplete.csv`, `best_practice_all_violations.csv`, `wcag_2_0_a_all_incomplete.csv`, `wcag_2_0_a_all_violations.csv` and 8 more

9 columns: Issue | Address | Location on Page | Guidelines | User Impact | Priority | Issue Description | How To Fix | Help URL

**1 export(s)**: `Content:Exact Duplicates`

5 columns: Address | Exact Duplicate Address | Similarity | Indexability | Indexability Status

**1 export(s)**: `Content:Near Duplicates`

5 columns: Address | Near Duplicate Address | Similarity | Indexability | Indexability Status

**1 export(s)**: `Content:Semantically Similar`

5 columns: Address | Closest Semantically Similar Address | Semantic Similarity Score | Indexability | Indexability Status

**1 export(s)**: `Images:All Image Inlinks`

19 columns: Type | Source | Destination | Size (Bytes) | Alt Text | Anchor | Status Code | Status | Follow | Target | Rel | Path Type | Link Path | Link Position | Link Origin | Real Dimensions | Dimensions in Attributes | Display Dimensions | Incorrectly Sized Images Potential Savings (Bytes)

**3 export(s)**: `Images:Images Missing Alt Attribute & Text Inlinks`, `Images:Images Missing Alt Attribute Inlinks`, `Images:Images Missing Alt Text Inlinks`

3 columns: Source | Destination | Alt Text

**1 export(s)**: `Images:Images Over X kB Inlinks`

4 columns: Type | Source | Destination | Size (Bytes)

**1 export(s)**: `Images:Images with Alt Text Over X Characters`

5 columns: Type | Source | Destination | Alt Text | Length

**1 export(s)**: `Images:Incorrectly Sized Images`

14 columns: Type | Source | Destination | Size (Bytes) | Alt Text | Length | Path Type | Link Path | Link Position | Link Origin | Real Dimensions | Dimensions in Attributes | Display Dimensions | Incorrectly Sized Images Potential Savings (Bytes)

**1 export(s)**: `Images:Missing Size Attributes`

12 columns: Type | Source | Destination | Alt Text | Length | Path Type | Link Path | Link Position | Link Origin | Real Dimensions | Dimensions in Attributes | Display Dimensions

**1 export(s)**: `JavaScript:Contains JavaScript Links`

13 columns: Type | Source | Destination | Alt Text | Anchor | Status Code | Status | Follow | Target | Rel | Path Type | Link Path | Link Position

**1 export(s)**: `JavaScript:Pages with Blocked Resources`

2 columns: Source | Destination

**1 export(s)**: `JavaScript:Pages with JavaScript Issues`

5 columns: Address | Level | Description | Stack Trace | Issue URL

**2 export(s)**: `Links:All Anchor Text`, `Links:External Links`

15 columns: Type | Source | Destination | Size (Bytes) | Alt Text | Anchor | Status Code | Status | Follow | Target | Rel | Path Type | Link Path | Link Position | Link Origin

**1 export(s)**: `Links:All Inlinks`

28 columns: Type | Source | Source Segments | Destination | Destination Segments | Form Action Link | Indexability | Indexability Status | hreflang | Size (Bytes) | Alt Text | Length | Anchor | Status Code | Status | Crawlability | Follow | Target | Rel | Path Type | Unlinked | Link Path | Link Position | Link Origin | Real Dimensions | Dimensions in Attributes | Display Dimensions | Incorrectly Sized Images Potential Savings (Bytes)

**1 export(s)**: `Links:Pages With Uncrawlable Internal Outlinks`

11 columns: Type | Source | Destination | Crawlability | Follow | Target | Rel | Path Type | Link Path | Link Position | Link Origin

**1 export(s)**: `Queued URLs`

2 columns: Crawl Depth | URL

**1 export(s)**: `Security:Form URL Insecure`

2 columns: Source | Form Action Link

**1 export(s)**: `Security:Mixed Content`

3 columns: Type | Source | Destination

**4 export(s)**: `Security:Protocol-Relative Outlinks`, `absolute_outlinks.csv`, `pathrelative_outlinks.csv`, `rootrelative_outlinks.csv`

6 columns: Type | Source | Destination | Anchor Text | Alt Text | Path Type

**1 export(s)**: `Security:Unsafe Cross-Origin Links`

6 columns: Source | Destination | Alt Text | Anchor | Target | Rel

**4 export(s)**: `Sitemaps:Non-Indexable URLs in Sitemap Inlinks`, `Sitemaps:Orphan URLs Inlinks`, `Sitemaps:URLs in Multiple Sitemaps Inlinks`, `Sitemaps:URLs in Sitemap Inlinks`

14 columns: Type | Source | Destination | Indexability | Indexability Status | Size (Bytes) | Status Code | Status | Target | Rel | Path Type | Link Path | Link Position | Link Origin

**6 export(s)**: `Structured Data:Contains Structured Data`, `Structured Data:JSON-LD URLs`, `Structured Data:Microdata URLs`, `Structured Data:RDFa URLs`, `Structured Data:Validation Errors`, `Structured Data:Validation Warnings`

36 columns: URL | Subject | Predicate | Object | Errors | Warnings | Validation Type 1 | Severity 1 | Issue 1 | Validation Type 2 | Severity 2 | Issue 2 | Validation Type 3 | Severity 3 | Issue 3 | Validation Type 4 | Severity 4 | Issue 4 | Validation Type 5 | Severity 5 | Issue 5 | Validation Type 6 | Severity 6 | Issue 6 | Validation Type 7 | Severity 7 | Issue 7 | Validation Type 8 | Severity 8 | Issue 8 | Validation Type 9 | Severity 9 | Issue 9 | Validation Type 10 | Severity 10 | Issue 10

**1 export(s)**: `URL Inspection:Referring Pages`

2 columns: Referring Page | Inspected URL

**1 export(s)**: `URL Inspection:Rich Results`

8 columns: Address | Indexability | Indexability Status | Rich Results | Rich Results Type | Severity | Item Name | Rich Results Issue Type

**1 export(s)**: `URL Inspection:Sitemaps`

2 columns: Inspected URL | Sitemap

**1 export(s)**: `Web:All Cookies`

8 columns: Address | Cookie Name | Cookie Value | Domain | Path | Expiration Time | Secure | HttpOnly

**2 export(s)**: `Web:All HTTP Request Headers`, `Web:All HTTP Response Headers`

1 columns: Address

**1 export(s)**: `issues_overview_report.csv`

8 columns: Issue Name | Issue Type | Issue Priority | URLs | % of Total | Description | How To Fix | Help URL

**1 export(s)**: `spelling_and_grammar_errors.csv`

11 columns: URL | Lang | Spelling Errors | Grammar Errors | Error Type | Error Count | Error | Error with Context | Error Detail | Suggestions | Page Section

**1 export(s)**: `spelling_and_grammar_errors_report_summary.csv`

7 columns: Error | Error Type | Error Count | URLs Affected | Coverage % | Error Detail | Sample URL
