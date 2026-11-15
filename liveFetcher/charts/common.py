"""
common.py - the code every platform shares.

A platform file only knows how to GET its own chart. Everything else lives
here, written once:
  * PlatformUnavailable  - how a platform says "I can't be collected, here's why"
  * http_get / http_post - web requests with a timeout and polite retries
  * make_row             - the one row format every platform returns
  * find_list            - dig a named list out of deeply nested JSON
  * save                 - write latest.json + history.csv, only when the chart changed
  * setup_logging        - log to the screen and to output/charts.log
"""
import csv
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "output"

# Many sites refuse requests that don't look like a browser, so we send a normal
# Chrome-on-Windows "User-Agent" header with every request.
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

log = logging.getLogger("charts")


# ---------------------------------------------------------------------------
# 1. "This platform can't be done" - a special kind of error
# ---------------------------------------------------------------------------
class PlatformUnavailable(Exception):
    """Raised by a platform that can't be collected. The message explains why.

    It's a separate error type so run_all.py can tell "this platform is
    impossible / not set up" apart from "something broke this time".
    """


# ---------------------------------------------------------------------------
# 2. Web requests with retries
# ---------------------------------------------------------------------------
# A Session reuses the same connection for repeated requests to a site (faster)
# and lets us set the User-Agent once for every request.
_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT

# Status codes that mean "try again later" rather than "you asked for something wrong".
RETRY_STATUSES = {429, 500, 502, 503, 504}


def http_request(method, url, *, retries=3, timeout=30, **kwargs):
    """Send a request. Retry on network errors and "try later" statuses, waiting longer each time."""
    for attempt in range(1, retries + 1):
        wait = 2 ** attempt  # 2 s, 4 s, 8 s ...
        try:
            response = _session.request(method, url, timeout=timeout, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as e:
            error = e
        else:
            if response.status_code not in RETRY_STATUSES:
                response.raise_for_status()  # 4xx like 403/404: retrying won't help, stop now
                return response
            error = requests.HTTPError(f"HTTP {response.status_code}", response=response)
            # A 429 often says how long to wait in a "Retry-After" header. Respect it (max 60 s).
            retry_after = response.headers.get("Retry-After", "")
            if retry_after.isdigit():
                wait = min(int(retry_after), 60)
        if attempt == retries:
            raise error
        log.warning("%s %s failed (%s) - retry %d of %d in %d s",
                    method, url, error, attempt, retries - 1, wait)
        time.sleep(wait)


def http_get(url, **kwargs):
    return http_request("GET", url, **kwargs)


def http_post(url, **kwargs):
    return http_request("POST", url, **kwargs)


# ---------------------------------------------------------------------------
# 3. The one row format
# ---------------------------------------------------------------------------
def to_int(value):
    """'1,234,567' -> 1234567; None/'' -> None. Sites send numbers in many shapes."""
    if value is None or value == "":
        return None
    try:
        return int(str(value).replace(",", "").split(".")[0])
    except ValueError:
        return None


def make_row(rank, title, artists, metric=None, metric_name=None, url=None):
    """Every platform returns a list of these, so saving and comparing work the same everywhere."""
    if isinstance(artists, str):
        artists = [artists]
    return {
        "rank": to_int(rank),
        "title": (title or "").strip(),
        "artists": ", ".join(a.strip() for a in artists if a and a.strip()),
        "metric": to_int(metric),
        "metric_name": metric_name,  # what the number means: "streams", "views", ...
        "url": url,
    }


# ---------------------------------------------------------------------------
# 4. Dig a list out of nested JSON (same idea as in youtube_basic.py)
# ---------------------------------------------------------------------------
def find_list(node, key):
    """Return the first list stored under `key`, however deep it's nested. None if absent."""
    if isinstance(node, dict):
        if isinstance(node.get(key), list):
            return node[key]
        children = node.values()
    elif isinstance(node, list):
        children = node
    else:
        return None
    for child in children:
        found = find_list(child, key)
        if found:
            return found
    return None


# ---------------------------------------------------------------------------
# 5. Saving: output/<platform>/<chart>_latest.json and <chart>_history.csv
# ---------------------------------------------------------------------------
CSV_FIELDS = ["fetched_at", "rank", "title", "artists", "metric_name", "metric", "url"]


def save(platform, chart, rows):
    """Save one chart. Returns True if it changed since last time, False if identical.

    "Last time" is read from latest.json on disk, not from memory, so this works
    whether the program loops for days or runs once on a schedule.
    """
    folder = OUTPUT_DIR / platform
    folder.mkdir(parents=True, exist_ok=True)
    latest = folder / f"{chart}_latest.json"
    history = folder / f"{chart}_history.csv"

    if latest.exists():
        try:
            previous = json.loads(latest.read_text(encoding="utf-8"))["rows"]
        except (ValueError, KeyError):
            previous = None  # file damaged? treat as changed and overwrite it
        if previous == rows:
            return False

    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # History FIRST. If the CSV is locked (open in Excel) this raises, latest.json
    # isn't updated, and the next run sees "changed" again and retries. Nothing lost.
    is_new_file = not history.exists()
    with history.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new_file:
            writer.writeheader()
        for row in rows:
            writer.writerow({"fetched_at": fetched_at, **row})

    # Then latest.json: write a temp file and swap it in, so it's never half-written.
    tmp = latest.with_suffix(".tmp")
    tmp.write_text(json.dumps({"platform": platform, "chart": chart,
                               "fetched_at": fetched_at, "rows": rows},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, latest)
    return True


# ---------------------------------------------------------------------------
# 6. Logging
# ---------------------------------------------------------------------------
def setup_logging():
    OUTPUT_DIR.mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    to_file = logging.FileHandler(OUTPUT_DIR / "charts.log", encoding="utf-8")
    to_screen = logging.StreamHandler()
    for handler in (to_file, to_screen):
        handler.setFormatter(fmt)
        log.addHandler(handler)
    log.setLevel(logging.INFO)
