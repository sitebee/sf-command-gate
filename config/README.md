# Your Screaming Frog configuration

Put your saved Screaming Frog configuration in this folder, named
`weekly-crawl.seospiderconfig` (or change `CONFIG_FILE` in `gate.py` to match your name).

## How to make one

1. Open the Screaming Frog SEO Spider app.
2. Set up the crawl the way you want it: threads, speed limits, user agent, what to crawl and
   extract, JavaScript rendering, and so on.
3. Choose **File > Configuration > Save As...** and save it here.

The gate passes this file to every crawl with `--config`, so a scheduled crawl behaves exactly like the
one you set up by hand.

## Things to decide before you crawl

- **User agent.** Use one that is honest about who is crawling, or one you are permitted to use for
  that site. Presenting as a search engine's bot (Googlebot, Bingbot, DuckDuckBot and so on) is not
  something to do on sites you don't own or have permission to test that way.
- **Speed.** Threads and URLs-per-second limits decide how hard the crawl hits the site. Start gentle on
  sites that aren't yours.
- **Features the recipes need.** Some recipes depend on features switched on in this file, for example
  crawling images for the `images` recipe, or sitemaps for parts of `indexability`. Each recipe lists
  what it needs in `REQUIRES`, and the gate stops you before the crawl if an export is not available.
- **Storage mode.** Database storage keeps RAM use low on big crawls and writes heavily to disk, so use
  fast storage. The profiler (Windows) shows how a crawl behaves in your setup.

## Don't commit it

`.gitignore` excludes `config/*.seospiderconfig` so your settings don't end up in a public repository.
