# The resource profiler

An optional report on what a crawl cost: CPU, RAM, processes, TCP connections, bandwidth, time, requests by file type,
the technologies the site runs on, any CDN or WAF it met, and what a bigger crawl would need. It is meant for sizing the
machine and the schedule for larger or repeated crawls.

> **The profiler works on Windows only.** It was built and tested on Windows. On macOS and Linux the stage skips itself
> with a message and the rest of the gate carries on. macOS and Linux users can write their own, and
> [the last section](#building-one-for-macos-or-linux) explains where to start.

## Switch it on

1. `pip install psutil` (the only extra package in the project).
2. In `gate.py`, take the `#` off `"profile"` in `STAGES`.
3. Optional, section 7: `PROFILE_INTERVAL` (seconds between samples, default 1.0) and `PROFILE_PROBE` (see below).

Each crawl then writes `resource_profile.md` (for people) and `resource_profile.json` (for scripts and LLMs, including the raw
samples) into the crawl folder. Re-run the report on an earlier crawl with `python gate.py profile --folder output/<crawl>`:
the requests, log and probe sections are rebuilt, and the live measurements are kept from the original run.

Without psutil the report still covers requests, bytes, timing, technologies, CDN and WAF. Only the live measurements are missing.

## Where each number comes from

| Source | What it gives | Needs |
| --- | --- | --- |
| **Live sampling** of the Screaming Frog process and everything it starts, once per interval | RAM, CPU, processes, threads, TCP connections, network and disk activity | psutil, Windows |
| **The crawl data** (`internal_all.csv`) | Requests and bytes by file type, response times, status codes, speed per minute, blocking and challenges, the long tail | nothing extra |
| **The Screaming Frog log** | Version, threads, rate limit, user agent, storage mode, max memory, URLs per second, queue length | nothing extra |
| **The probe** (optional) | Server, TLS, HTTP/2 and HTTP/3, compression, caching, rate-limit headers, technologies, CDN, WAF, third-party hosts | nothing extra |

Screaming Frog runs as a small launcher plus a Java process that holds the memory (with JavaScript rendering you'll also see Chrome
processes). The sampler follows the whole process tree.

## Reading the report

**Summary and phases.** A crawl isn't one steady load, so the report splits the run into startup, main crawl, long tail and wrap-up.
On the test site (about 26,000 URLs, 12,833 real requests, a 6-core 24 GB Windows machine) the run looked like this:

| Phase | Time | CPU (of machine) | RAM peak | Connections | Disk written |
| --- | --- | --- | --- | --- | --- |
| Startup | 6s | 37% | 0.34 GB | 0 | 20 MB |
| Main crawl | 8m 18s | 42% avg, 80% peak | 2.82 GB | 5 avg, 7 max | 11.4 GB |
| Long tail | 5m 40s | 19% | 2.84 GB | 0.4 avg | 1.3 GB |
| Wrap-up | 3m 58s | 17% | 2.86 GB | 0 | 0.7 GB |

What that told us: CPU was not the limit (so more threads could have helped, if the site tolerates them), disk writes dwarfed network
traffic, the memory peak came after the last request, and 40% of the run was a long tail of slow-arriving requests that were fast to answer.
Your numbers will differ. The point is that you can see them.

**CPU** is shown as a percentage of one core (it can pass 100) and of the whole machine.

**Requests and bytes by file type.** URLs blocked by robots.txt are counted separately because they cost no request. "Size" is uncompressed;
"Transferred" is what crossed the wire.

**TCP connections** can't be split by file type, because one connection carries many requests. They are sampled, so connections that open and
close between samples can be missed. The report shows open connections, HTTPS versus HTTP, distinct connections, which servers they went to,
and requests per connection. (If the server supports HTTP/2 but Screaming Frog crawled over HTTP/1.1, each thread holds its own connection,
and the report says so.)

**Network and disk** figures are for the whole machine, so other activity is included. In database storage mode Screaming Frog writes to disk
throughout the crawl.

**Technologies, CDN and WAF.** From the probe: the headers, cookies and page source of the homepage matched against known signatures. Cookies seen in
the crawl log are used too, but only if they belong to the crawled site's domain (the log also records Screaming Frog's own traffic). Cookie values are
never stored. "None identified" means none was recognised, not that none exists.

**Challenges met** counts 403, 429, 503, Cloudflare 52x and "Just a moment" style challenge pages in the crawl, with when they started.

**Scaling estimates** project the observed speed and bytes per request to 10,000, 100,000 and 1,000,000 requests, at both the overall speed and the
speed before any long tail. They are linear projections from one crawl. RAM isn't projected when Screaming Frog uses database storage, because it stays
roughly flat. Plan for disk instead.

## The probe

With `PROFILE_PROBE = True` the profiler sends **three requests to the site you crawl**: the homepage twice (once uncompressed, once with
compression to see the encoding and cache behaviour) and `robots.txt`. It also opens one TLS connection to read the certificate and negotiated protocol,
and looks up the server's IP. It identifies itself as `CommandGateProfiler/1.0`. Set `PROFILE_PROBE = False` if you don't want any extra requests.

## Limits

- Windows only, as above.
- It measures the crawl machine, not the site's server. Response times are what Screaming Frog saw.
- Disk and network counters are machine-wide.
- A site behind login, or that blocks the probe, will show less in the technologies section. The report says if the probe itself was blocked.
- Counts of connections are lower bounds.

## Building one for macOS or Linux

I haven't tested any of this on macOS or Linux, so treat it as a starting point. The profiler is one file, `_engine/profiler.py`, and most of it is not tied to Windows.

**Mostly portable already:**

- `Sampler` uses `psutil`, which supports macOS and Linux. It follows the process tree from the Screaming Frog process id.
- `analyse_requests`, `read_log`, `run_probe`, `analyse_samples`, `by_phase`, `scaling` and the report writers use the standard library only.

**What to look at:**

1. `supported()` returns `sys.platform == "win32"`. That is the only thing stopping the stage on other systems. Widen it for your platform.
2. `machine_info()` reads the CPU name from the Windows registry. On Linux read `/proc/cpuinfo`, on macOS `sysctl -n machdep.cpu.brand_string`.
3. TCP connections: `Process.net_connections()` may need elevated privileges on macOS. If it is denied, the connection numbers will be zero, so check.
4. Process names differ (the launcher and the Java process are named differently), so check the "By process" table looks right.
5. Disk counters (`psutil.disk_io_counters`) behave differently per platform. Compare with `iostat` or Activity Monitor.
6. Validate with a short crawl against `htop`, `top` or Activity Monitor before you trust the numbers. The fix for the CPU reading in this project came from checking
   the sampler against a synthetic load, and it caught a real bug.

If you build a macOS or Linux version, a pull request would be very welcome.
