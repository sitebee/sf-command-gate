"""Optional module: the resource profiler.

Switch it on by adding "profile" to STAGES in gate.py. While the crawl runs it samples
the Screaming Frog process (and everything it starts): CPU, RAM, threads, processes,
TCP connections and network traffic. When the crawl ends it combines that with the crawl
data, the Screaming Frog log and (optionally) a small probe of the site, and writes
resource_profile.md and resource_profile.json next to the crawl.

Needs psutil for the live measurements (pip install psutil). Without it the report still
covers requests, bytes, timing, technologies, CDN and WAF.

You shouldn't need to edit this file. The switches are in gate.py, section 7.
"""

import csv
import json
import platform
import re
import socket
import ssl
import statistics
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:  # the report still works without live measurements
    psutil = None


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ROOT = ROOT / "output"
LOG_FOLDER = ROOT / "logs"
PROBE_USER_AGENT = "Mozilla/5.0 (compatible; CommandGateProfiler/1.0)"


def available():
    return psutil is not None


def supported():
    """The profiler is built and tested on Windows only."""
    return sys.platform == "win32"


UNSUPPORTED_MESSAGE = ("The profiler is built and tested on Windows only, so this stage was skipped. "
                       "macOS and Linux users can write their own: see docs/profiler.md.")


# ============================================================
# 1. LIVE SAMPLING (runs in a thread while the crawl runs)
# ============================================================

class Sampler(threading.Thread):
    """Samples a process and all its children once per interval, until stopped."""

    def __init__(self, pid, interval=1.0):
        super().__init__(daemon=True)
        self.pid = pid
        self.interval = max(0.2, float(interval))
        self.samples = []
        self.connection_keys = set()          # distinct (process, local, remote) connections seen
        self.remote_ips = Counter()           # remote IP -> times seen across samples
        self.started = time.time()
        self.ended = None
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        try:
            root = psutil.Process(self.pid)
        except psutil.Error:
            return
        known = {}
        psutil.cpu_percent(None)
        last_net, last_disk = psutil.net_io_counters(), psutil.disk_io_counters()
        self.started = time.time()

        while not self._stop_event.is_set():
            tick = time.time()
            try:
                tree = [root] + root.children(recursive=True)
            except psutil.Error:
                break
            sample = self._measure(tree, known)

            net, disk = psutil.net_io_counters(), psutil.disk_io_counters()
            sample["rx_bytes"] = net.bytes_recv - last_net.bytes_recv
            sample["tx_bytes"] = net.bytes_sent - last_net.bytes_sent
            sample["disk_read"] = (disk.read_bytes - last_disk.read_bytes) if disk else 0
            sample["disk_write"] = (disk.write_bytes - last_disk.write_bytes) if disk else 0
            last_net, last_disk = net, disk

            sample["t"] = round(tick - self.started, 2)
            sample["sys_cpu"] = psutil.cpu_percent(None)
            sample["sys_ram_gb"] = round(psutil.virtual_memory().used / 2**30, 2)
            self.samples.append(sample)
            self._stop_event.wait(max(0.0, self.interval - (time.time() - tick)))
        self.ended = time.time()

    def _measure(self, tree, known):
        names, name_rss = Counter(), Counter()
        rss = threads = 0
        cpu = 0.0
        states, ports, remotes = Counter(), Counter(), set()

        for found in tree:
            try:
                # children() hands back new objects every tick, but cpu_percent only works when the
                # same object is asked each time, so keep the first one we saw for each process.
                is_new = found.pid not in known
                process = known.setdefault(found.pid, found)
                if is_new:
                    process.cpu_percent(None)   # the first call only primes the counter
                    cpu_now = 0.0
                else:
                    cpu_now = process.cpu_percent(None)
                memory = process.memory_info().rss
                name = process.name()
                names[name] += 1
                name_rss[name] += memory
                rss += memory
                threads += process.num_threads()
                cpu += cpu_now
                connections = getattr(process, "net_connections", None) or process.connections
                for connection in connections(kind="tcp"):
                    if connection.status == "LISTEN" or not connection.raddr:
                        continue
                    states[connection.status] += 1
                    ports[connection.raddr.port] += 1
                    remotes.add(connection.raddr.ip)
                    self.remote_ips[connection.raddr.ip] += 1
                    self.connection_keys.add((process.pid, connection.laddr, connection.raddr))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return {
            "processes": len(names) and sum(names.values()),
            "process_names": dict(names),
            "name_rss_mb": {name: round(value / 2**20, 1) for name, value in name_rss.items()},
            "threads": threads,
            "rss_mb": round(rss / 2**20, 1),
            "cpu": round(cpu, 1),
            "tcp_total": sum(states.values()),
            "tcp_established": states.get("ESTABLISHED", 0),
            "tcp_time_wait": states.get("TIME_WAIT", 0),
            "tcp_close_wait": states.get("CLOSE_WAIT", 0),
            "port_443": ports.get(443, 0),
            "port_80": ports.get(80, 0),
            "port_other": sum(ports.values()) - ports.get(443, 0) - ports.get(80, 0),
            "remote_hosts": len(remotes),
        }


# ============================================================
# 2. SMALL HELPERS
# ============================================================

def summarise(values):
    """min / avg / p95 / max for a list of numbers."""
    values = [v for v in values if v is not None]
    if not values:
        return {"min": 0, "avg": 0, "p95": 0, "max": 0}
    ordered = sorted(values)
    return {"min": round(ordered[0], 2), "avg": round(statistics.mean(ordered), 2),
            "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 2), "max": round(ordered[-1], 2)}


def to_float(value):
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return 0.0


def human_bytes(value):
    value = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(value) < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


def human_duration(seconds):
    seconds = int(round(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}h {minutes}m {secs}s" if hours else (f"{minutes}m {secs}s" if minutes else f"{secs}s")


def file_family(content_type):
    """Group content types into the file types people think in."""
    ct = (content_type or "").split(";")[0].strip().lower()
    if not ct:
        return "No content type"
    if "html" in ct:
        return "HTML"
    if ct == "text/css":
        return "CSS"
    if "javascript" in ct or "ecmascript" in ct:
        return "JavaScript"
    if ct.startswith("image/"):
        return "Images"
    if "font" in ct or "woff" in ct:
        return "Fonts"
    if ct == "application/pdf":
        return "PDF"
    if "json" in ct:
        return "JSON"
    if "xml" in ct or "rss" in ct or "atom" in ct:
        return "XML"
    if ct.startswith(("video/", "audio/")):
        return "Media"
    if ct.startswith("text/"):
        return "Text"
    return "Other"


def machine_info():
    info = {"os": f"{platform.system()} {platform.release()} ({platform.version()})", "python": platform.python_version(),
            "cpu_name": platform.processor() or "unknown"}
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                info["cpu_name"] = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    if psutil:
        info.update({"cpu_cores": psutil.cpu_count(logical=False), "cpu_threads": psutil.cpu_count(logical=True),
                     "ram_gb": round(psutil.virtual_memory().total / 2**30, 1)})
    return info


# ============================================================
# 3. THE CRAWL DATA (raw Internal:All export)
# ============================================================

def read_crawl_rows(folder):
    """Rows from the raw Internal:All export. Falls back to the preprocessed one (fewer columns)."""
    for name in ("internal_all.csv", "internal_all_preprocessed.csv"):
        path = folder / name
        if path.exists():
            with path.open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))
            if name.endswith("_preprocessed.csv"):  # map the tidy names back to the raw ones we use
                rename = {"address": "Address", "content_type": "Content Type", "status_code": "Status Code", "status": "Status",
                          "title": "Title 1", "size_bytes": "Size (Bytes)", "response_time": "Response Time",
                          "http_version": "HTTP Version"}
                rows = [{rename.get(key, key): value for key, value in row.items()} for row in rows]
            return rows, name
    return [], None


CHALLENGE_TITLES = re.compile(
    r"just a moment|attention required|access denied|pardon our interruption|verify(ing)? you are (a )?human|"
    r"are you a robot|robot or human|security check|checking your browser|request blocked|captcha|ddos protection|"
    r"you have been blocked|error 1020|unusual traffic|press (&|and) hold", re.I)
BLOCKING_CODES = {403: "Forbidden", 429: "Too Many Requests", 503: "Service Unavailable", 999: "Request denied (999)",
                  520: "Cloudflare: unknown error", 521: "Cloudflare: web server down", 522: "Cloudflare: connection timed out",
                  523: "Cloudflare: origin unreachable", 524: "Cloudflare: timeout", 525: "Cloudflare: SSL handshake failed",
                  526: "Cloudflare: invalid SSL certificate", 527: "Cloudflare: railgun error", 530: "Cloudflare: origin DNS error"}


def analyse_requests(rows):
    """Requests, bytes and timing by file type, plus a per-minute timeline and any blocking seen."""
    if not rows:
        return None

    blocked_by_robots = [r for r in rows if (r.get("Status") or "").lower().startswith("blocked by robots")]
    blocked_ids = {id(r) for r in blocked_by_robots}
    requested = [r for r in rows if id(r) not in blocked_ids] if blocked_ids else rows
    transferred_column = "Total Transferred (Bytes)" if "Total Transferred (Bytes)" in rows[0] else "Transferred (Bytes)"

    families = defaultdict(lambda: {"requests": 0, "size_bytes": 0, "transferred_bytes": 0, "times": []})
    for row in requested:
        family = file_family(row.get("Content Type"))
        entry = families[family]
        entry["requests"] += 1
        entry["size_bytes"] += int(to_float(row.get("Size (Bytes)")))
        entry["transferred_bytes"] += int(to_float(row.get(transferred_column)))
        if (row.get("Response Time") or "").strip():
            entry["times"].append(to_float(row["Response Time"]))

    by_type = []
    for family, entry in sorted(families.items(), key=lambda item: -item[1]["requests"]):
        times = summarise(entry["times"])
        by_type.append({"file_type": family, "requests": entry["requests"], "share_percent": round(entry["requests"] / len(requested) * 100, 1),
                        "size_bytes": entry["size_bytes"], "transferred_bytes": entry["transferred_bytes"],
                        "avg_response_seconds": times["avg"], "p95_response_seconds": times["p95"]})

    codes = Counter()
    failures = Counter()
    for row in requested:
        code = int(to_float(row.get("Status Code")))
        codes[code] += 1
        if code == 0:
            failures[row.get("Status") or "No response"] += 1

    stamps = []
    for row in requested:
        try:
            stamps.append((datetime.strptime(row["Crawl Timestamp"], "%Y-%m-%d %H:%M:%S"), row))
        except (KeyError, ValueError):
            continue
    stamps.sort(key=lambda item: item[0])

    timeline, per_second = [], Counter()
    started = stamps[0][0] if stamps else None
    finished = stamps[-1][0] if stamps else None
    if stamps:
        per_minute = defaultdict(lambda: {"requests": 0, "errors": 0, "blocked": 0, "times": [], "bytes": 0})
        for moment, row in stamps:
            per_second[moment.replace(microsecond=0)] += 1
            bucket = per_minute[int((moment - started).total_seconds() // 60)]
            bucket["requests"] += 1
            code = int(to_float(row.get("Status Code")))
            bucket["errors"] += code >= 400 or code == 0
            bucket["blocked"] += code in (403, 429)
            bucket["bytes"] += int(to_float(row.get(transferred_column)))
            if (row.get("Response Time") or "").strip():
                bucket["times"].append(to_float(row["Response Time"]))
        for minute in sorted(per_minute):
            bucket = per_minute[minute]
            timeline.append({"minute": minute, "requests": bucket["requests"], "errors": bucket["errors"],
                             "blocked_403_429": bucket["blocked"], "avg_response_seconds": summarise(bucket["times"])["avg"],
                             "transferred_bytes": bucket["bytes"]})

    tail = None
    if len(stamps) > 100:
        cut = int(len(stamps) * 0.99)
        cut_time = stamps[cut - 1][0]
        after = stamps[cut:]
        span, whole = (finished - cut_time).total_seconds(), (finished - started).total_seconds()
        if span >= 120 and whole and span / whole >= 0.2:
            tail_times = [to_float(r["Response Time"]) for _, r in after if (r.get("Response Time") or "").strip()]
            waits = sorted(g for g in ((b[0] - a[0]).total_seconds() for a, b in zip(after, after[1:])) if g >= 5)
            kinds = Counter(file_family(r.get("Content Type")) for _, r in after)
            tail = {"requests": len(after), "minutes": round(span / 60, 1), "share_of_crawl_percent": round(span / whole * 100),
                    "starts_after_minutes": round((cut_time - started).total_seconds() / 60, 1),
                    "avg_response_seconds": summarise(tail_times)["avg"], "max_response_seconds": summarise(tail_times)["max"],
                    "file_types": dict(kinds.most_common(3)), "typical_wait_seconds": round(statistics.median(waits)) if waits else None,
                    "sample_urls": [r["Address"] for _, r in after[:3]]}

    blockers = []
    for moment, row in stamps or [(None, r) for r in requested]:
        code = int(to_float(row.get("Status Code")))
        title = row.get("Title 1") or row.get("title") or ""
        if code in BLOCKING_CODES or CHALLENGE_TITLES.search(title):
            blockers.append({"url": row.get("Address"), "status_code": code, "title": title[:80],
                             "time": moment.strftime("%H:%M:%S") if moment else ""})

    all_times = [to_float(r["Response Time"]) for r in requested if (r.get("Response Time") or "").strip()]
    return {
        "urls_in_export": len(rows),
        "blocked_by_robots_not_requested": len(blocked_by_robots),
        "http_requests": len(requested),
        "by_file_type": by_type,
        "status_codes": {str(code): count for code, count in sorted(codes.items())},
        "request_failures": dict(failures),
        "http_versions": dict(Counter((r.get("HTTP Version") or "none") for r in requested)),
        "response_seconds": summarise(all_times),
        "size_bytes": sum(f["size_bytes"] for f in by_type),
        "transferred_bytes": sum(f["transferred_bytes"] for f in by_type),
        "crawl_started": started.isoformat(sep=" ") if started else None,
        "crawl_finished": finished.isoformat(sep=" ") if finished else None,
        "crawl_seconds": (finished - started).total_seconds() if started else 0,
        "peak_requests_per_second": max(per_second.values()) if per_second else 0,
        "timeline": timeline,
        "long_tail": tail,
        "blocking": {"count": len(blockers),
                     "by_status": {str(code): sum(1 for b in blockers if b["status_code"] == code) for code in sorted({b["status_code"] for b in blockers})},
                     "first_seen": blockers[0]["time"] if blockers else None,
                     "samples": blockers[:5]},
    }


# ============================================================
# 4. THE SCREAMING FROG LOG
# ============================================================

def find_log(folder, hint=None):
    """The log for this crawl: the one just run, or the log whose start time is closest to the folder's."""
    if hint and Path(hint).exists():
        return Path(hint)
    try:
        started = datetime.strptime(folder.name, "%Y.%m.%d.%H.%M.%S")
    except ValueError:
        return None
    best = None
    for log in LOG_FOLDER.glob("screaming-frog-*.log") if LOG_FOLDER.exists() else []:
        try:
            moment = datetime.strptime(log.stem.removeprefix("screaming-frog-"), "%Y%m%d-%H%M%S")
        except ValueError:
            continue
        gap = abs((moment - started).total_seconds())
        if gap <= 120 and (best is None or gap < best[0]):
            best = (gap, log)
    return best[1] if best else None


def read_log(path):
    """Settings and throughput facts Screaming Frog wrote to its own log."""
    if not path:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    first = lambda pattern, flags=0: (m.group(1).strip() if (m := re.search(pattern, text, flags)) else None)

    progress = [(int(a), to_float(c), to_float(w)) for a, c, w in
                re.findall(r"SpiderProgress \[mActive=(\d+), mCompleted=([\d,]+), mWaiting=([\d,]+)", text)]
    current_rates = [to_float(v) for v in re.findall(r"mCurrentUrlsPerSecond=([\d.]+)", text)]
    average_rates = [to_float(v) for v in re.findall(r"mAverageUrlsPerSecond=([\d.]+)", text)]
    peak_memory = [int(v) for v in re.findall(r"mPeakMemoryUsage=(\d+)%", text)]

    levels = Counter()
    problems = Counter()
    for line in text.splitlines():
        match = re.match(r"\d{4}-\d\d-\d\d [\d:,]+ \[\d+\] \[[^\]]*\] (WARN|ERROR)\s+- (.*)", line)
        if match:
            levels[match.group(1)] += 1
            message = re.sub(r"(?i)(set-cookie:\s*[^=\s;]+)=[^;\"\s]+", r"\1=<value hidden>", match.group(2))   # never keep cookie values
            problems[re.sub(r"\d+", "N", message)[:110]] += 1
    cookies_seen = Counter(re.findall(r"(?i)set-cookie:\s*([^=\s;]+)=", text))
    cookie_domains = defaultdict(set)
    for name, domain in re.findall(r"(?i)set-cookie:\s*([^=\s;]+)=[^\n]*?domain=([^;\s\"]+)", text):
        cookie_domains[name].add(domain.lower())

    return {
        "log_file": path.name,
        "screaming_frog_version": first(r"Running: Screaming Frog SEO Spider ([\d.]+)"),
        "max_heap": first(r"-Xmx(\w+)"),
        "storage_mode": first(r"storageMode: (\w+)"),
        "configured_threads": int(first(r"mMaxThreads=(\d+)") or 0) or None,
        "rate_limit_on": (first(r"mLimitPerformance=(true|false)") == "true"),
        "rate_limit_urls_per_second": to_float(first(r"mUrlRequestsPerSecond=([\d.]+)") or 0) or None,
        "user_agent": first(r"mUserAgent=([^\n]+)"),
        "max_active_threads": max((p[0] for p in progress), default=0),
        "max_queue_waiting": int(max((p[2] for p in progress), default=0)),
        "urls_completed": int(max((p[1] for p in progress), default=0)),
        "peak_urls_per_second": max(current_rates, default=0),
        "average_urls_per_second": average_rates[-1] if average_rates else 0,
        "peak_java_heap_percent": max(peak_memory, default=0),
        "warnings_and_errors": dict(levels),
        "top_problems": problems.most_common(5),
        "cookie_names_in_log": sorted(cookies_seen),
        "cookie_domains_in_log": {name: sorted(domains) for name, domains in cookie_domains.items()},
    }


def technologies_from_log(log, site_host=None):
    """Technologies hinted at by cookies Screaming Frog logged while crawling (names only, never values).

    Cookies set for other domains are ignored: Screaming Frog's own traffic (for example its update
    check) shows up in the same log, and it says nothing about the site being crawled.
    """
    found = defaultdict(lambda: {"category": "", "evidence": []})
    for cookie in (log or {}).get("cookie_names_in_log", []):
        domains = (log.get("cookie_domains_in_log") or {}).get(cookie, [])
        if site_host and domains and not any(registrable(d.lstrip(".")) == registrable(site_host) for d in domains):
            continue
        for name, category, where, pattern in SIGNATURES:
            if where == "cookie" and re.search(pattern, cookie):
                found[name]["category"] = category
                domains = ", ".join((log.get("cookie_domains_in_log") or {}).get(cookie, []))
                found[name]["evidence"].append(f"cookie {cookie}" + (f" (domain {domains})" if domains else "") + " in the crawl log")
    return [{"name": name, "category": data["category"], "evidence": data["evidence"][:3]} for name, data in sorted(found.items())]


# ============================================================
# 5. THE PROBE (optional): technologies, CDN, WAF, TLS
# ============================================================

# (name, category, where, pattern). where: header (name present), server / powered (value of Server / X-Powered-By),
# via, cookie (cookie name), html (page source)
SIGNATURES = [
    ("Cloudflare", "CDN", "header", r"^cf-ray$"), ("Cloudflare", "CDN", "server", r"cloudflare"),
    ("Cloudflare bot management", "WAF / bot protection", "cookie", r"^(__cf_bm|cf_clearance)$"),
    ("Cloudflare challenge", "WAF / bot protection", "header", r"^cf-mitigated$"),
    ("Amazon CloudFront", "CDN", "header", r"^x-amz-cf-(id|pop)$"), ("Amazon CloudFront", "CDN", "via", r"cloudfront"),
    ("Akamai", "CDN", "header", r"^(x-akamai-.*|akamai-grn)$"), ("Akamai", "CDN", "server", r"akamai"),
    ("Akamai Bot Manager", "WAF / bot protection", "cookie", r"^(ak_bmsc|bm_sz|_abck)$"),
    ("Fastly", "CDN", "header", r"^(x-fastly-request-id|fastly-.*)$"), ("Fastly", "CDN", "header", r"^x-served-by$"),
    ("Imperva / Incapsula", "WAF / bot protection", "header", r"^x-iinfo$"),
    ("Imperva / Incapsula", "WAF / bot protection", "cookie", r"^(incap_ses_.*|visid_incap_.*)$"),
    ("Sucuri", "WAF / bot protection", "header", r"^x-sucuri-id$"), ("Sucuri", "WAF / bot protection", "server", r"sucuri"),
    ("DataDome", "WAF / bot protection", "cookie", r"^datadome$"), ("DataDome", "WAF / bot protection", "header", r"^x-datadome.*$"),
    ("HUMAN / PerimeterX", "WAF / bot protection", "cookie", r"^_px.*$"),
    ("AWS WAF", "WAF / bot protection", "header", r"^x-amzn-waf-action$"), ("AWS WAF", "WAF / bot protection", "cookie", r"^aws-waf-token$"),
    ("AWS load balancer", "Hosting", "cookie", r"^AWSALB.*$"),
    ("F5 BIG-IP", "WAF / bot protection", "cookie", r"^(BIGipServer.*|TS[0-9a-f]{6,}.*)$"),
    ("Azure Front Door", "CDN", "header", r"^x-azure-ref$"), ("Google Cloud", "Hosting", "via", r"google"),
    ("Vercel", "Hosting", "header", r"^x-vercel-id$"), ("Netlify", "Hosting", "header", r"^x-nf-request-id$"),
    ("BunnyCDN", "CDN", "server", r"bunnycdn"), ("KeyCDN", "CDN", "server", r"keycdn"),
    ("Varnish cache", "Cache", "header", r"^x-varnish$"), ("Varnish cache", "Cache", "via", r"varnish"),
    ("nginx", "Web server", "server", r"nginx"), ("Apache", "Web server", "server", r"apache"),
    ("LiteSpeed", "Web server", "server", r"litespeed"), ("Microsoft IIS", "Web server", "server", r"microsoft-iis"),
    ("OpenResty", "Web server", "server", r"openresty"), ("Caddy", "Web server", "server", r"caddy"),
    ("PHP", "Language", "powered", r"php"), ("ASP.NET", "Language", "powered", r"asp\.net"), ("Express (Node.js)", "Language", "powered", r"express"),
    ("WP Engine", "Hosting", "powered", r"wp engine"),
    ("Shopify", "Platform", "header", r"^(x-shopid|x-shopify-stage)$"), ("Shopify", "Platform", "html", r"cdn\.shopify\.com"),
    ("WordPress", "CMS", "html", r"/wp-content/|/wp-includes/"), ("WordPress", "CMS", "header", r"^x-pingback$"),
    ("WooCommerce", "Platform", "html", r"woocommerce"), ("Drupal", "CMS", "header", r"^x-drupal-.*$"),
    ("Drupal", "CMS", "html", r"drupal\.settings|/sites/default/files"), ("Joomla", "CMS", "html", r"/media/jui/|joomla"),
    ("Magento", "Platform", "html", r"/static/frontend/|mage/cookies|magento"), ("PrestaShop", "Platform", "html", r"prestashop"),
    ("BigCommerce", "Platform", "html", r"bigcommerce\.com"), ("Wix", "Platform", "html", r"wixstatic\.com"),
    ("Squarespace", "Platform", "html", r"squarespace"), ("Webflow", "Platform", "html", r"webflow"),
    ("Next.js", "Framework", "html", r"/_next/|__NEXT_DATA__"), ("Nuxt", "Framework", "html", r"/_nuxt/|__NUXT__"),
    ("Gatsby", "Framework", "html", r"___gatsby"), ("Angular", "Framework", "html", r"ng-version="), ("React", "Framework", "html", r"data-reactroot|react-dom"),
    ("jQuery", "Library", "html", r"jquery"), ("Bootstrap", "Library", "html", r"bootstrap"),
    ("Google Tag Manager", "Analytics / tags", "html", r"googletagmanager\.com"), ("Google Analytics", "Analytics / tags", "html", r"google-analytics\.com|gtag/js"),
    ("Meta Pixel", "Analytics / tags", "html", r"connect\.facebook\.net"), ("Hotjar", "Analytics / tags", "html", r"hotjar\.com"),
    ("Klaviyo", "Analytics / tags", "html", r"klaviyo\.com"), ("Cookiebot", "Consent", "html", r"cookiebot"), ("OneTrust", "Consent", "html", r"onetrust"),
    ("Stripe", "Payments", "html", r"js\.stripe\.com"), ("PayPal", "Payments", "html", r"paypal\.com/sdk|paypalobjects"),
    ("reCAPTCHA", "WAF / bot protection", "html", r"recaptcha"), ("hCaptcha", "WAF / bot protection", "html", r"hcaptcha"),
    ("Cloudflare Turnstile", "WAF / bot protection", "html", r"challenges\.cloudflare\.com"),
]

CDN_HOSTS = [(r"cloudfront\.net$", "Amazon CloudFront"), (r"akamai(hd|edge|technologies)?\.net$|edgekey\.net$|edgesuite\.net$", "Akamai"),
             (r"fastly(lb)?\.net$|fastly\.com$", "Fastly"), (r"cloudflare\.(com|net)$|cdnjs\.cloudflare\.com$", "Cloudflare"),
             (r"azureedge\.net$|azurefd\.net$", "Azure CDN / Front Door"), (r"b-cdn\.net$", "BunnyCDN"), (r"jsdelivr\.net$", "jsDelivr"),
             (r"cdn\.shopify\.com$|shopifycdn\.com$", "Shopify CDN"), (r"googleapis\.com$|gstatic\.com$", "Google"),
             (r"unpkg\.com$", "unpkg"), (r"wp\.com$", "WordPress.com CDN"), (r"stackpathcdn\.com$|stackpathdns\.com$", "StackPath")]


def target_url(settings):
    """The site being crawled: the --crawl URL, or the first URL in the list for list mode."""
    crawl = settings.get("CRAWL", [])
    if "--crawl" in crawl and crawl.index("--crawl") + 1 < len(crawl):
        return crawl[crawl.index("--crawl") + 1]
    if "--crawl-list" in crawl and crawl.index("--crawl-list") + 1 < len(crawl):
        path = Path(crawl[crawl.index("--crawl-list") + 1])
        if path.exists():
            lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
            return lines[0] if lines else None
    return None


def fetch(url, encoding="identity", read_bytes=300_000):
    """One GET. Returns status, headers, body text and timing. HTTP errors (403, 429...) are results, not failures."""
    request = urllib.request.Request(url, headers={"User-Agent": PROBE_USER_AGENT, "Accept-Encoding": encoding, "Accept": "text/html,*/*"})
    started = time.perf_counter()
    try:
        response = urllib.request.urlopen(request, timeout=20)
    except urllib.error.HTTPError as error:
        response = error
    except (urllib.error.URLError, OSError, ssl.SSLError) as error:
        return {"url": url, "error": str(getattr(error, "reason", error))}
    first_byte = time.perf_counter() - started
    body = b""
    try:
        body = response.read(read_bytes)
    except OSError:
        pass
    headers = {key.lower(): value for key, value in response.headers.items()}
    cookies = [c.split("=", 1)[0].strip() for c in response.headers.get_all("Set-Cookie") or []]
    return {"url": url, "final_url": response.geturl() if hasattr(response, "geturl") else url, "status": response.status if hasattr(response, "status") else response.code,
            "headers": headers, "cookies": cookies, "body": body.decode("utf-8", errors="replace"),
            "seconds_to_headers": round(first_byte, 3), "total_seconds": round(time.perf_counter() - started, 3)}


def probe_tls(host):
    try:
        context = ssl.create_default_context()
        context.set_alpn_protocols(["h2", "http/1.1"])
        with socket.create_connection((host, 443), timeout=10) as sock, context.wrap_socket(sock, server_hostname=host) as tls:
            certificate = tls.getpeercert()
            issuer = dict(item[0] for item in certificate.get("issuer", ()))
            return {"tls_version": tls.version(), "cipher": tls.cipher()[0], "negotiated_protocol": tls.selected_alpn_protocol() or "http/1.1",
                    "certificate_issuer": issuer.get("organizationName") or issuer.get("commonName"), "certificate_expires": certificate.get("notAfter"),
                    "alt_names": len(certificate.get("subjectAltName", ()))}
    except (OSError, ssl.SSLError) as error:
        return {"error": str(error)}


def registrable(host):
    parts = host.lower().split(".")
    if len(parts) >= 3 and parts[-2] in {"co", "com", "org", "net", "gov", "ac"} and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def run_probe(url):
    """A few requests to the homepage and robots.txt, to identify technologies, CDN and WAF."""
    parsed = urllib.parse.urlsplit(url)
    host, base = parsed.hostname, f"{parsed.scheme}://{parsed.netloc}"
    first = fetch(url)
    second = fetch(url, encoding="gzip, br")
    robots = fetch(base + "/robots.txt")
    if "error" in first:
        return {"url": url, "error": first["error"]}

    headers, cookies, html = first["headers"], first["cookies"], first.get("body", "")
    found = defaultdict(lambda: {"category": "", "evidence": []})
    for name, category, where, pattern in SIGNATURES:
        hit = None
        if where == "header":
            hit = next((f"header {key}" for key in headers if re.search(pattern, key)), None)
        elif where in ("server", "powered", "via"):
            key = {"server": "server", "powered": "x-powered-by", "via": "via"}[where]
            hit = f"{key}: {headers[key][:50]}" if key in headers and re.search(pattern, headers[key], re.I) else None
            if where == "via" and "x-served-by" in headers and re.search(pattern, headers["x-served-by"], re.I):
                hit = hit or f"x-served-by: {headers['x-served-by'][:50]}"
        elif where == "cookie":
            hit = next((f"cookie {c}" for c in cookies if re.search(pattern, c)), None)
        elif where == "html":
            match = re.search(pattern, html, re.I)
            hit = f"page source: {match.group(0)[:40]}" if match else None
        if hit:
            found[name]["category"] = category
            if hit not in found[name]["evidence"]:
                found[name]["evidence"].append(hit)

    generator = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html, re.I)
    if generator:
        found[generator.group(1)[:40]]["category"] = found[generator.group(1)[:40]]["category"] or "Generator tag"
        found[generator.group(1)[:40]]["evidence"].append("meta generator")
    versions = re.findall(r"jquery[.-](\d+\.\d+(?:\.\d+)?)", html, re.I)
    if versions and "jQuery" in found:
        found["jQuery"]["evidence"].append(f"version {versions[0]}")

    hosts = Counter(urllib.parse.urlsplit(u).hostname for u in re.findall(r'(?:src|href)=["\'](https?://[^"\']+)', html, re.I))
    hosts.pop(None, None)
    third_party = []
    for other, count in hosts.most_common(15):
        if registrable(other) != registrable(host):
            label = next((name for pattern, name in CDN_HOSTS if re.search(pattern, other)), "")
            third_party.append({"host": other, "references": count, "provider": label})

    try:
        ips = sorted({info[4][0] for info in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
    except OSError:
        ips = []
    reverse = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {ip: pool.submit(socket.gethostbyaddr, ip) for ip in ips[:3]}
        for ip, future in futures.items():
            try:
                reverse[ip] = future.result(timeout=3)[0]
            except Exception:
                reverse[ip] = None
    for ip, name in reverse.items():
        provider = next((label for pattern, label in CDN_HOSTS if name and re.search(pattern, name)), None)
        if provider:
            found[provider]["category"] = found[provider]["category"] or "CDN"
            found[provider]["evidence"].append(f"reverse DNS {name}")

    cache_headers = {key: headers[key] for key in ("cache-control", "age", "etag", "last-modified", "expires", "vary", "x-cache", "cf-cache-status",
                                                    "x-cache-hits", "x-served-by", "x-varnish") if key in headers}
    second_headers = second.get("headers", {})
    rate_headers = {key: value for key, value in {**headers, **second_headers}.items() if key.startswith(("x-ratelimit", "ratelimit", "retry-after"))}
    robots_text = robots.get("body", "") if robots.get("status") == 200 else ""
    delay = re.search(r"(?im)^crawl-delay:\s*([\d.]+)", robots_text)

    return {
        "url": url, "final_url": first.get("final_url"), "status": first.get("status"),
        "seconds_to_headers": first.get("seconds_to_headers"), "server": headers.get("server"), "powered_by": headers.get("x-powered-by"),
        "compression": second_headers.get("content-encoding") or "none offered", "http3_advertised": "h3" in headers.get("alt-svc", ""),
        "tls": probe_tls(host) if parsed.scheme == "https" else None,
        "ip_addresses": [{"ip": ip, "reverse_dns": reverse.get(ip)} for ip in ips],
        "cache": cache_headers, "second_request_cache": {key: second_headers[key] for key in ("age", "x-cache", "cf-cache-status") if key in second_headers},
        "rate_limit_headers": rate_headers, "robots_txt": {"status": robots.get("status"), "crawl_delay": float(delay.group(1)) if delay else None,
                                                          "sitemaps": re.findall(r"(?im)^sitemap:\s*(\S+)", robots_text)[:5]},
        "technologies": [{"name": name, "category": data["category"], "evidence": data["evidence"][:3]} for name, data in sorted(found.items(), key=lambda i: (i[1]["category"], i[0]))],
        "third_party_hosts": third_party,
        "blocked_by_waf": first.get("status") in (403, 429, 503) or "cf-mitigated" in headers,
    }


# ============================================================
# 6. PUTTING IT TOGETHER
# ============================================================

def analyse_samples(sampler_samples, machine):
    """Min / avg / p95 / max for everything the sampler measured."""
    if not sampler_samples:
        return None
    interval = (sampler_samples[-1]["t"] - sampler_samples[0]["t"]) / max(1, len(sampler_samples) - 1)
    logical = machine.get("cpu_threads") or 1
    cpu = summarise([s["cpu"] for s in sampler_samples])
    names = defaultdict(lambda: {"max_processes": 0, "peak_rss_mb": 0.0})
    for sample in sampler_samples:
        for name, count in sample["process_names"].items():
            names[name]["max_processes"] = max(names[name]["max_processes"], count)
            names[name]["peak_rss_mb"] = max(names[name]["peak_rss_mb"], sample["name_rss_mb"].get(name, 0))
    rx = [s["rx_bytes"] / interval for s in sampler_samples]
    tx = [s["tx_bytes"] / interval for s in sampler_samples]
    peak_index = max(range(len(sampler_samples)), key=lambda i: sampler_samples[i]["rss_mb"])
    return {
        "samples": len(sampler_samples), "interval_seconds": round(interval, 2), "duration_seconds": round(sampler_samples[-1]["t"], 1),
        "processes": summarise([s["processes"] for s in sampler_samples]), "threads": summarise([s["threads"] for s in sampler_samples]),
        "ram_mb": summarise([s["rss_mb"] for s in sampler_samples]), "peak_ram_at_seconds": sampler_samples[peak_index]["t"],
        "cpu_percent_of_one_core": cpu, "cpu_percent_of_machine": {k: round(v / logical, 2) for k, v in cpu.items()},
        "cpu_core_seconds": round(sum(s["cpu"] for s in sampler_samples) * interval / 100, 1),
        "system_cpu_percent": summarise([s["sys_cpu"] for s in sampler_samples]), "system_ram_gb": summarise([s["sys_ram_gb"] for s in sampler_samples]),
        "tcp_connections": summarise([s["tcp_total"] for s in sampler_samples]), "tcp_established": summarise([s["tcp_established"] for s in sampler_samples]),
        "tcp_time_wait_max": max(s["tcp_time_wait"] for s in sampler_samples), "tcp_close_wait_max": max(s["tcp_close_wait"] for s in sampler_samples),
        "https_connections_max": max(s["port_443"] for s in sampler_samples), "http_connections_max": max(s["port_80"] for s in sampler_samples),
        "other_port_connections_max": max(s["port_other"] for s in sampler_samples), "remote_hosts_max": max(s["remote_hosts"] for s in sampler_samples),
        "by_process_name": {name: {"max_processes": v["max_processes"], "peak_rss_mb": round(v["peak_rss_mb"], 1)} for name, v in names.items()},
        "network_received_bytes": sum(s["rx_bytes"] for s in sampler_samples), "network_sent_bytes": sum(s["tx_bytes"] for s in sampler_samples),
        "peak_download_mbit_s": round(max(rx) * 8 / 1e6, 2), "avg_download_mbit_s": round(statistics.mean(rx) * 8 / 1e6, 2), "peak_upload_mbit_s": round(max(tx) * 8 / 1e6, 2),
        "disk_read_bytes": sum(s["disk_read"] for s in sampler_samples), "disk_written_bytes": sum(s["disk_write"] for s in sampler_samples),
    }


def phases(run_meta, requests):
    """Startup, crawling and wrap-up, when we know when the run started and ended."""
    if not run_meta or not requests or not requests.get("crawl_started"):
        return None
    started = datetime.fromisoformat(run_meta["started"])
    first, last = datetime.fromisoformat(requests["crawl_started"]), datetime.fromisoformat(requests["crawl_finished"])
    total = run_meta["wall_seconds"]
    startup = max(0.0, (first - started).total_seconds())
    crawling = (last - first).total_seconds()
    return {"startup_seconds": round(startup, 1), "crawling_seconds": round(crawling, 1),
            "wrap_up_seconds": round(max(0.0, total - startup - crawling), 1), "total_seconds": total}


def by_phase(samples, phase, requests, machine):
    """Resource use in each phase of the run: startup, main crawl, long tail (if any), wrap-up."""
    if not samples or not phase:
        return None
    logical = machine.get("cpu_threads") or 1
    tail = (requests or {}).get("long_tail")
    start = phase["startup_seconds"]
    crawl_end = start + phase["crawling_seconds"]
    main_end = start + tail["starts_after_minutes"] * 60 if tail else crawl_end
    bounds = [("Startup", 0, start), ("Main crawl" + (" (until 99% of requests)" if tail else ""), start, main_end)]
    if tail:
        bounds.append(("Long tail", main_end, crawl_end))
    bounds.append(("Wrap-up (analysis and exports)", crawl_end, float("inf")))

    rows = []
    for name, low, high in bounds:
        part = [s for s in samples if low <= s["t"] < high]
        if not part:
            continue
        cpu = [s["cpu"] / logical for s in part]
        rows.append({"phase": name, "seconds": round(min(high, samples[-1]["t"]) - low), "cpu_avg_percent_of_machine": round(statistics.mean(cpu), 1),
                     "cpu_peak_percent_of_machine": round(max(cpu), 1), "ram_avg_gb": round(statistics.mean(s["rss_mb"] for s in part) / 1024, 2),
                     "ram_peak_gb": round(max(s["rss_mb"] for s in part) / 1024, 2), "connections_avg": round(statistics.mean(s["tcp_established"] for s in part), 1),
                     "connections_max": max(s["tcp_established"] for s in part), "disk_written_bytes": sum(s["disk_write"] for s in part)})
    return rows


def describe_tail(tail):
    """What the final stretch of the crawl was, and whether the server or the crawler was the wait."""
    kinds = ", ".join(f"{count} {kind}" for kind, count in tail["file_types"].items())
    text = (f"Long tail: the last {tail['requests']} requests (1%) took {tail['minutes']} minutes, {tail['share_of_crawl_percent']}% of the crawl. "
            f"They were mostly {kinds}")
    if tail["typical_wait_seconds"]:
        text += f", arriving in bursts about {tail['typical_wait_seconds']}s apart"
    if tail["avg_response_seconds"] < 1:
        text += (f". Their responses averaged {tail['avg_response_seconds']}s (slowest {tail['max_response_seconds']}s), so the server wasn't the delay: "
                 "the crawl was waiting between requests, not on the site.")
    else:
        text += f". Their responses averaged {tail['avg_response_seconds']}s, so slow or timed-out URLs stretched the crawl."
    return text


def observations(report):
    """Plain-English readings of the numbers, only where the numbers support them."""
    notes = []
    live, requests, log, machine = report.get("live"), report.get("requests"), report.get("log"), report["machine"]
    if requests and requests.get("long_tail"):
        notes.append(describe_tail(requests["long_tail"]))
    probe = report.get("probe") or {}
    if requests and (probe.get("tls") or {}).get("negotiated_protocol") == "h2" and set(requests["http_versions"]) <= {"1.1"}:
        notes.append("The server supports HTTP/2, but Screaming Frog crawled over HTTP/1.1, so each crawl thread uses its own connection. Open connections track the thread count.")
    phases_table = report.get("by_phase")
    main = next((row for row in phases_table or [] if row["phase"].startswith("Main crawl")), None)
    if main:
        threads = (log or {}).get("configured_threads")
        headroom = main["cpu_avg_percent_of_machine"] < 60 and main["cpu_peak_percent_of_machine"] < 95
        notes.append(f"During the main crawl Screaming Frog averaged {main['cpu_avg_percent_of_machine']:.0f}% of this machine's CPU (peak {main['cpu_peak_percent_of_machine']:.0f}%)"
                     + (f" with {threads} threads. " if threads else ". ")
                     + ("There is CPU headroom, so more threads could raise the speed if the site can take the extra load." if headroom
                        else "CPU is close to the limit, so more threads would need more cores."))
        written = main["disk_written_bytes"]
        downloaded = (live or {}).get("network_received_bytes") or 0
        if written > 5 * max(downloaded, 1):
            notes.append(f"The main crawl wrote {human_bytes(written)} to disk (whole machine) for {human_bytes(downloaded)} downloaded. "
                         "In DB storage mode Screaming Frog's database is the likely writer, so disk speed probably matters more here than network speed.")
    if live and phases_table:
        crawl_end = report["phases"]["startup_seconds"] + report["phases"]["crawling_seconds"] if report.get("phases") else None
        if crawl_end and live["peak_ram_at_seconds"] >= crawl_end - 5:
            notes.append(f"Peak RAM ({live['ram_mb']['max'] / 1024:.1f} GB) came after the last request, during post-crawl analysis and exports, not while crawling.")
    if live:
        if machine.get("ram_gb"):
            notes.append(f"Peak RAM was {live['ram_mb']['max'] / 1024:.1f} GB of {machine['ram_gb']} GB ({live['ram_mb']['max'] / 1024 / machine['ram_gb'] * 100:.0f}%).")
        if not phases_table:
            cpu_machine = live["cpu_percent_of_machine"]
            notes.append(f"CPU averaged {cpu_machine['avg']:.0f}% of this machine (peak {cpu_machine['max']:.0f}%).")
    if log:
        if log.get("configured_threads") and log.get("max_active_threads"):
            notes.append(f"Screaming Frog is set to {log['configured_threads']} threads and used up to {log['max_active_threads']}. "
                         + ("Throughput is capped by the thread setting." if log["max_active_threads"] >= log["configured_threads"] else ""))
        if log.get("rate_limit_on"):
            notes.append(f"A rate limit of {log['rate_limit_urls_per_second']} URLs/second is switched on, so speed is capped by it.")
        if log.get("storage_mode") == "DB":
            notes.append("Storage mode is DB (database): RAM stays roughly flat as the crawl grows, and disk use grows instead.")
        elif log.get("storage_mode"):
            notes.append(f"Storage mode is {log['storage_mode']}: RAM grows with the number of URLs, so the RAM figures scale with crawl size.")
    if requests and requests["blocking"]["count"]:
        notes.append(f"{requests['blocking']['count']} responses looked like blocking or challenges (first seen at {requests['blocking']['first_seen'] or 'an unknown time'}). See the WAF section.")
    elif requests:
        notes.append("No blocking responses (403, 429, 503, 52x) or challenge pages were seen during the crawl.")
    return notes


def scaling(report):
    """Linear projections. Honest about what does not scale linearly."""
    requests, log, live = report.get("requests"), report.get("log"), report.get("live")
    if not requests or not requests["http_requests"] or not requests["crawl_seconds"]:
        return None
    count = requests["http_requests"]
    rate = count / requests["crawl_seconds"]
    average_bytes = requests["transferred_bytes"] / count
    tail = requests.get("long_tail")
    fast_rate = (count - tail["requests"]) / (tail["starts_after_minutes"] * 60) if tail and tail["starts_after_minutes"] else None
    rows = []
    for target in (10_000, 100_000, 1_000_000):
        rows.append({"requests": target, "time_at_observed_rate": human_duration(target / rate), "transferred": human_bytes(average_bytes * target),
                     "time_at_speed_before_tail": human_duration(target / fast_rate) if fast_rate else None})
    result = {"observed_requests_per_second": round(rate, 2), "requests_per_second_before_tail": round(fast_rate, 2) if fast_rate else None,
              "average_transferred_bytes_per_request": round(average_bytes),
              "projections": rows, "caveat": "Linear projection from this one crawl. Real sites vary, and speed depends on the server and any rate limiting."}
    if live:
        result["peak_ram_mb_per_1000_requests"] = round(live["ram_mb"]["max"] / count * 1000, 1)
        result["ram_note"] = ("RAM is not projected: storage mode is DB, so it stays roughly flat. Plan for disk space instead."
                              if (log or {}).get("storage_mode") == "DB" else "In memory storage mode, RAM grows roughly with the number of URLs.")
    return result


def newest_crawl_folder():
    folders = [p for p in OUTPUT_ROOT.iterdir() if p.is_dir() and (p / "internal_all.csv").exists()] if OUTPUT_ROOT.exists() else []
    if not folders:
        raise FileNotFoundError(f"No crawl with an internal_all.csv under {OUTPUT_ROOT}. Run a crawl first.")
    return max(folders, key=lambda p: p.stat().st_mtime)


def folder_size(folder):
    return sum(p.stat().st_size for p in folder.rglob("*") if p.is_file() and not p.name.startswith("resource_profile"))


def run(settings, folder=None, crawl=None):
    """Build resource_profile.md and resource_profile.json for a crawl folder."""
    folder = Path(folder) if folder else newest_crawl_folder()
    json_path, markdown_path = folder / "resource_profile.json", folder / "resource_profile.md"

    # Live samples: from the crawl just run, or kept from an earlier profile of this same folder.
    samples, connections, run_meta = [], {}, {}
    sampler = getattr(crawl, "sampler", None)
    if sampler and sampler.samples:
        samples = sampler.samples
        connections = {"distinct_connections_observed": len(sampler.connection_keys), "distinct_remote_ips": len(sampler.remote_ips),
                       "remote_ips": dict(sampler.remote_ips.most_common(10))}
        run_meta = {"started": datetime.fromtimestamp(sampler.started).isoformat(timespec="seconds"),
                    "wall_seconds": round((sampler.ended or time.time()) - sampler.started, 1)}
    elif json_path.exists():
        kept = json.loads(json_path.read_text(encoding="utf-8")).get("raw", {})
        samples, connections, run_meta = kept.get("samples", []), kept.get("connections", {}), kept.get("run", {})

    machine = machine_info()
    rows, source = read_crawl_rows(folder)
    requests = analyse_requests(rows)
    log = read_log(find_log(folder, getattr(crawl, "log_path", None)))

    probe = None
    if settings.get("PROFILE_PROBE", True):
        url = target_url(settings)
        if url:
            print(f"Probing {url} (a few requests) for technologies, CDN and WAF...", flush=True)
            probe = run_probe(url)

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"), "crawl_folder": folder.name, "data_source": source,
        "machine": machine, "run": run_meta, "log": log, "requests": requests,
        "live": analyse_samples(samples, machine), "connections": connections or None, "probe": probe,
        "output_size_bytes": folder_size(folder),
    }
    if not available():
        report["live_note"] = "psutil is not installed, so there are no live CPU, RAM or connection measurements. Install it with: pip install psutil"
    elif not samples:
        report["live_note"] = "No live samples for this crawl. Add \"profile\" to STAGES in gate.py before the crawl runs to record them."
    site_host = urllib.parse.urlsplit(target_url(settings) or "").hostname
    report["technologies_seen_in_crawl_log"] = technologies_from_log(log, site_host)
    report["phases"] = phases(run_meta, requests)
    report["by_phase"] = by_phase(samples, report["phases"], requests, machine)
    report["observations"] = observations(report)
    report["scaling"] = scaling(report)

    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    report["raw"] = {"run": run_meta, "connections": connections, "samples": samples}
    json_path.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Created resource profile: {markdown_path}")
    print(f"Created resource data:    {json_path}")
    return folder


# ============================================================
# 7. THE MARKDOWN REPORT
# ============================================================

NUMBERLIKE = re.compile(r"^-?[\d,.]+( ?[A-Za-z%/]+)?$")


def md_table(lines, headers, rows):
    """A markdown table. A column is right-aligned only if every cell in it looks like a number."""
    rows = [[str(cell) for cell in row] for row in rows]
    numeric = [i > 0 and bool(rows) and all(NUMBERLIKE.match(row[i]) for row in rows) for i in range(len(headers))]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---:" if numeric[i] else "---" for i in range(len(headers))) + " |")
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    lines.append("")


def render_markdown(report):
    machine, live, requests, log, probe = report["machine"], report.get("live"), report.get("requests"), report.get("log"), report.get("probe")
    lines = ["# Crawl resource profile", "", f"**Crawl:** `{report['crawl_folder']}`  ", f"**Generated:** {report['generated_at']}", ""]

    lines += ["## Summary", ""]
    summary = []
    if requests:
        summary += [("Duration of the crawl", human_duration(requests["crawl_seconds"])), ("HTTP requests", f"{requests['http_requests']:,}"),
                    ("Average speed", f"{requests['http_requests'] / requests['crawl_seconds']:.1f} requests/second" if requests["crawl_seconds"] else "n/a"),
                    ("Data transferred", human_bytes(requests["transferred_bytes"]))]
        if requests.get("long_tail"):
            summary.append(("Time to finish 99% of requests", f"{requests['long_tail']['starts_after_minutes']} minutes"))
    phase = report.get("phases")
    if phase:
        summary += [("Startup before the first request", human_duration(phase["startup_seconds"])),
                    ("Wrap-up after the last request (exports, shutdown)", human_duration(phase["wrap_up_seconds"])),
                    ("Total run time, start to finish", human_duration(phase["total_seconds"]))]
    elif report["run"]:
        summary.append(("Total run time, start to finish", human_duration(report["run"]["wall_seconds"])))
    if live:
        summary += [("Peak RAM", f"{live['ram_mb']['max'] / 1024:.2f} GB"), ("Peak CPU", f"{live['cpu_percent_of_machine']['max']:.0f}% of the machine"),
                    ("Peak open connections", f"{live['tcp_connections']['max']:.0f}"), ("Most processes at once", f"{live['processes']['max']:.0f}")]
    md_table(lines, ["Measure", "Value"], summary)
    if report.get("observations"):
        lines += ["**What this tells you**", ""] + [f"- {note}" for note in report["observations"]] + [""]
    if report.get("live_note"):
        lines += [f"> {report['live_note']}", ""]

    lines += ["## This machine", ""]
    md_table(lines, ["Item", "Value"], [("CPU", machine.get("cpu_name")), ("Cores / threads", f"{machine.get('cpu_cores', '?')} / {machine.get('cpu_threads', '?')}"),
                                        ("RAM", f"{machine.get('ram_gb', '?')} GB"), ("OS", machine["os"]), ("Python", machine["python"])])
    if log:
        lines += ["## Screaming Frog settings used", ""]
        md_table(lines, ["Setting", "Value"], [("Version", log["screaming_frog_version"]), ("Storage mode", log["storage_mode"]), ("Max memory (heap)", log["max_heap"]),
                                               ("Threads set", log["configured_threads"]), ("Rate limit", f"{log['rate_limit_urls_per_second']} URLs/s" if log["rate_limit_on"] else "off"),
                                               ("User agent", log["user_agent"]),
                                               ("Peak URLs processed per second", f"{log['peak_urls_per_second']:.1f}"),
                                               ("Average URLs processed per second", f"{log['average_urls_per_second']:.1f}"),
                                               ("Most threads active at once", log["max_active_threads"]),
                                               ("Longest URL queue", f"{log['max_queue_waiting']:,}"), ("Peak Java heap used", f"{log['peak_java_heap_percent']}% of max")])
        lines += ["\"URLs processed\" counts every URL Screaming Frog handled, including URLs blocked by robots.txt, which cost no request. "
                  "Real requests per second are in the summary and the file type section.", ""]

    if live:
        lines += ["## Resources used (measured while the crawl ran)", "",
                  f"Sampled every {live['interval_seconds']}s, {live['samples']} samples over {human_duration(live['duration_seconds'])}. "
                  "The first seconds are Screaming Frog starting up, so minimums include that.", ""]
        row = lambda label, data, fmt: (label, fmt(data["min"]), fmt(data["avg"]), fmt(data["p95"]), fmt(data["max"]))
        md_table(lines, ["Resource", "Min", "Average", "95th percentile", "Max"], [
            row("RAM (Screaming Frog and its processes)", live["ram_mb"], lambda v: f"{v / 1024:.2f} GB"),
            row("CPU, % of one core (can pass 100)", live["cpu_percent_of_one_core"], lambda v: f"{v:.0f}%"),
            row("CPU, % of this machine", live["cpu_percent_of_machine"], lambda v: f"{v:.1f}%"),
            row("Processes", live["processes"], lambda v: f"{v:.0f}"), row("Operating system threads (all processes)", live["threads"], lambda v: f"{v:.0f}"),
            row("Whole-machine CPU", live["system_cpu_percent"], lambda v: f"{v:.0f}%"), row("Whole-machine RAM in use", live["system_ram_gb"], lambda v: f"{v:.1f} GB")])
        lines += [f"Peak RAM came {human_duration(live['peak_ram_at_seconds'])} into the run. Total CPU work: {live['cpu_core_seconds']:,.0f} core-seconds.", ""]
        md_table(lines, ["Process", "Most at once", "Peak RAM"], [(name, v["max_processes"], f"{v['peak_rss_mb']:.0f} MB") for name, v in
                                                                sorted(live["by_process_name"].items(), key=lambda i: -i[1]["peak_rss_mb"])])

        if report.get("by_phase"):
            lines += ["### By phase", "", "A crawl isn't one steady load. This splits the same samples into the phases of the run. Disk written is for the whole machine.", ""]
            md_table(lines, ["Phase", "Time", "CPU avg / peak (% of machine)", "RAM avg / peak", "Connections avg / max", "Disk written"],
                     [(row["phase"], human_duration(row["seconds"]), f"{row['cpu_avg_percent_of_machine']:.0f}% / {row['cpu_peak_percent_of_machine']:.0f}%",
                       f"{row['ram_avg_gb']:.2f} / {row['ram_peak_gb']:.2f} GB", f"{row['connections_avg']} / {row['connections_max']}", human_bytes(row["disk_written_bytes"]))
                      for row in report["by_phase"]])

        connection = report.get("connections") or {}
        lines += ["## TCP connections", "", "Sampled, so connections that opened and closed between samples can be missed. "
                  "TCP connections can't be split by file type, because one connection carries many requests. "
                  "Requests and bytes by file type are in the next section.", ""]
        md_table(lines, ["Measure", "Value"], [
            ("Open connections (min / avg / max)", f"{live['tcp_connections']['min']:.0f} / {live['tcp_connections']['avg']:.1f} / {live['tcp_connections']['max']:.0f}"),
            ("Established (avg / max)", f"{live['tcp_established']['avg']:.1f} / {live['tcp_established']['max']:.0f}"),
            ("Most to port 443 (HTTPS) at once", live["https_connections_max"]), ("Most to port 80 (HTTP) at once", live["http_connections_max"]),
            ("Most to other ports at once", live["other_port_connections_max"]), ("Most TIME_WAIT at once", live["tcp_time_wait_max"]),
            ("Distinct connections observed", connection.get("distinct_connections_observed", "n/a")), ("Distinct remote servers (IPs)", connection.get("distinct_remote_ips", "n/a")),
            ("Requests per observed connection", f"{requests['http_requests'] / connection['distinct_connections_observed']:.1f}" if requests and connection.get("distinct_connections_observed") else "n/a")])

        if connection.get("remote_ips"):
            target_ips = {i["ip"] for i in (probe or {}).get("ip_addresses", [])}
            total_seen = sum(connection["remote_ips"].values())
            lines += ["Servers the connections went to (share of all connection observations):", ""]
            md_table(lines, ["Server", "Share", "The crawled site?"],
                     [(ip, f"{count / total_seen * 100:.0f}%", "yes" if ip in target_ips else ("no" if target_ips else "unknown, the probe is off"))
                      for ip, count in connection["remote_ips"].items()])

        lines += ["## Network and disk", "", "Network and disk figures are for the whole machine during the crawl, so other activity is included. "
                  "In DB storage mode Screaming Frog writes to disk throughout the crawl.", ""]
        md_table(lines, ["Measure", "Value"], [("Downloaded", human_bytes(live["network_received_bytes"])), ("Uploaded", human_bytes(live["network_sent_bytes"])),
                                               ("Download speed (avg / peak)", f"{live['avg_download_mbit_s']} / {live['peak_download_mbit_s']} Mbit/s"),
                                               ("Peak upload speed", f"{live['peak_upload_mbit_s']} Mbit/s"), ("Disk read", human_bytes(live["disk_read_bytes"])),
                                               ("Disk written", human_bytes(live["disk_written_bytes"])), ("Size of the export files", human_bytes(report["output_size_bytes"]))])

    if requests:
        lines += ["## Requests and bytes by file type", "",
                  f"{requests['urls_in_export']:,} URLs in the export. {requests['blocked_by_robots_not_requested']:,} were blocked by robots.txt and never requested, "
                  f"so {requests['http_requests']:,} are real HTTP requests.", ""]
        md_table(lines, ["File type", "Requests", "Share", "Size (uncompressed)", "Transferred (on the wire)", "Avg response", "95th percentile"],
                 [(f["file_type"], f"{f['requests']:,}", f"{f['share_percent']}%", human_bytes(f["size_bytes"]), human_bytes(f["transferred_bytes"]),
                   f"{f['avg_response_seconds']:.3f}s", f"{f['p95_response_seconds']:.3f}s") for f in requests["by_file_type"]])
        md_table(lines, ["Measure", "Value"], [("Status codes", ", ".join(f"{code}: {count:,}" for code, count in requests["status_codes"].items())),
                                               ("HTTP versions", ", ".join(f"{v}: {c:,}" for v, c in requests["http_versions"].items())),
                                               ("Response time (avg / 95th / max)", f"{requests['response_seconds']['avg']:.3f}s / {requests['response_seconds']['p95']:.3f}s / {requests['response_seconds']['max']:.3f}s"),
                                               ("Peak requests in one second", requests["peak_requests_per_second"]),
                                               ("Failed requests", ", ".join(f"{k}: {v}" for k, v in requests["request_failures"].items()) or "none")])
        if requests["timeline"]:
            timeline = requests["timeline"]
            step = max(1, len(timeline) // 20)
            lines += ["## Speed over time", "", "Per minute of the crawl, from the crawl timestamps.", ""]
            md_table(lines, ["Minute", "Requests", "Errors", "403/429", "Avg response", "Transferred"],
                     [(t["minute"], f"{t['requests']:,}", t["errors"], t["blocked_403_429"], f"{t['avg_response_seconds']:.3f}s", human_bytes(t["transferred_bytes"])) for t in timeline[::step]])

    lines += ["## Technologies, CDN and WAF", ""]
    if not probe:
        lines += ["The probe is switched off (PROFILE_PROBE in gate.py).", ""]
    elif "error" in probe:
        lines += [f"The probe couldn't reach {probe['url']}: {probe['error']}", ""]
    else:
        md_table(lines, ["Item", "Value"], [("Probed", probe["final_url"]), ("Server header", probe["server"] or "hidden"), ("X-Powered-By", probe["powered_by"] or "hidden"),
                                            ("Time to first byte", f"{probe['seconds_to_headers']}s"), ("Compression offered", probe["compression"]),
                                            ("HTTP/3 advertised", "yes" if probe["http3_advertised"] else "no"),
                                            ("Protocol negotiated (TLS)", (probe["tls"] or {}).get("negotiated_protocol", "n/a")),
                                            ("TLS", f"{probe['tls'].get('tls_version')}, {probe['tls'].get('cipher')}" if probe.get("tls") and "error" not in probe["tls"] else "n/a"),
                                            ("Certificate", f"{probe['tls'].get('certificate_issuer')}, expires {probe['tls'].get('certificate_expires')}" if probe.get("tls") and "error" not in probe["tls"] else "n/a"),
                                            ("IP addresses", ", ".join(f"{i['ip']}" + (f" ({i['reverse_dns']})" if i["reverse_dns"] else "") for i in probe["ip_addresses"]) or "n/a"),
                                            ("robots.txt", f"status {probe['robots_txt']['status']}" + (f", crawl-delay {probe['robots_txt']['crawl_delay']}s" if probe["robots_txt"]["crawl_delay"] else ""))])
        if probe["technologies"]:
            md_table(lines, ["Technology", "Type", "Evidence"], [(t["name"], t["category"], "; ".join(t["evidence"])) for t in probe["technologies"]])
        else:
            lines += ["No known technologies were identified from the homepage headers or source.", ""]
        cdn = [t["name"] for t in probe["technologies"] if t["category"] in ("CDN",)]
        waf = [t["name"] for t in probe["technologies"] if t["category"] == "WAF / bot protection"]
        lines += [f"**CDN:** {', '.join(cdn) or 'none identified'}  ", f"**WAF / bot protection:** {', '.join(waf) or 'none identified'}  ",
                  f"**Cache:** {', '.join(f'{k}: {v}' for k, v in {**probe['cache'], **probe['second_request_cache']}.items() if k in ('x-cache', 'cf-cache-status', 'age', 'cache-control')) or 'no cache headers'}  ",
                  f"**Rate-limit headers:** {', '.join(f'{k}: {v}' for k, v in probe['rate_limit_headers'].items()) or 'none sent'}", ""]
        if probe["blocked_by_waf"]:
            lines += [f"> The probe itself was challenged or blocked (status {probe['status']}).", ""]
        if probe["third_party_hosts"]:
            lines += ["Other hosts the homepage loads from:", ""]
            md_table(lines, ["Host", "References", "Provider"], [(h["host"], h["references"], h["provider"]) for h in probe["third_party_hosts"][:10]])

    seen = report.get("technologies_seen_in_crawl_log")
    if seen:
        lines += ["Also seen while crawling (from cookies in the Screaming Frog log, names only):", ""]
        md_table(lines, ["Technology", "Type", "Evidence"], [(t["name"], t["category"], "; ".join(t["evidence"])) for t in seen])
        if not probe or "error" in probe or not any(t["category"] == "CDN" for t in probe.get("technologies", [])):
            lines += ["> The homepage probe didn't show this, but the crawl met it on other pages of your site.", ""]

    if requests:
        lines += ["## Challenges met during the crawl", ""]
        blocking = requests["blocking"]
        if blocking["count"]:
            lines += [f"{blocking['count']} responses looked like blocking or challenges, first at {blocking['first_seen'] or 'an unknown time'}.", ""]
            md_table(lines, ["Status", "Responses"], [(f"{code} {BLOCKING_CODES.get(int(code), 'challenge page')}", count) for code, count in blocking["by_status"].items()])
            md_table(lines, ["Time", "Status", "URL", "Title"], [(b["time"], b["status_code"], b["url"], b["title"]) for b in blocking["samples"]])
        else:
            lines += ["No 403, 429, 503, Cloudflare 52x or challenge pages were seen.", ""]
        if log and log["warnings_and_errors"]:
            lines += [f"The Screaming Frog log recorded {sum(log['warnings_and_errors'].values())} warnings and errors. The most common:", ""]
            lines += [f"- {count} x {message}" for message, count in log["top_problems"]] + [""]
        if log and log.get("user_agent"):
            lines += [f"Screaming Frog identified itself as `{log['user_agent']}`. Some CDNs and WAFs treat bot user agents differently from browsers.", ""]

    scale = report.get("scaling")
    if scale:
        lines += ["## Scaling estimates", "", f"Observed: {scale['observed_requests_per_second']} requests/second overall, {human_bytes(scale['average_transferred_bytes_per_request'])} per request."]
        if scale["requests_per_second_before_tail"]:
            lines += [f"Before the long tail the crawl ran at {scale['requests_per_second_before_tail']} requests/second. The overall speed includes the tail, and whether a tail "
                      "grows with a bigger site is something this one crawl can't show, so both are given.", ""]
            md_table(lines, ["Requests", "Time at overall speed", "Time at speed before the tail", "Data transferred"],
                     [(f"{p['requests']:,}", p["time_at_observed_rate"], p["time_at_speed_before_tail"], p["transferred"]) for p in scale["projections"]])
        else:
            lines.append("")
            md_table(lines, ["Requests", "Time at this speed", "Data transferred"], [(f"{p['requests']:,}", p["time_at_observed_rate"], p["transferred"]) for p in scale["projections"]])
        if "peak_ram_mb_per_1000_requests" in scale:
            lines += [f"Peak RAM was {scale['peak_ram_mb_per_1000_requests']} MB per 1,000 requests. {scale['ram_note']}", ""]
        lines += [f"*{scale['caveat']}*", ""]

    lines += ["## How this was measured", "",
              "- **Resources:** sampled with psutil from the Screaming Frog process and every process it started, once per interval.",
              "- **Requests, bytes, timing, challenges:** from the raw Internal:All export (crawl timestamps, sizes, response times, status codes and titles).",
              "- **Settings and speed:** from the Screaming Frog log.",
              "- **Technologies, CDN, WAF:** from a few requests to the homepage and robots.txt, matched against known headers, cookies and page source.",
              "- **Not measured:** connections per file type (not possible), and anything the site hides behind a login."]
    return "\n".join(lines)
