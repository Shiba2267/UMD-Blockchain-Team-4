"""
run_all.py - run every platform, save results, and report what happened.

    py run_all.py                          # every platform, once
    py run_all.py --only deezerLiveFetch melonLiveFetch     # just these
    py run_all.py --every 30 --hours 30    # repeat every 30 min for 30 hours

One platform failing never stops the others.
"""
import argparse
import importlib
import time

from common import PlatformUnavailable, log, save, setup_logging

# Each name is a file in platforms/. Order = the order they run in.
PLATFORMS = [
    # Working
    "youtubeMusicLiveFetch", "spotifyLiveFetch", "appleMusicLiveFetch", "deezerLiveFetch",
    "tencentLiveFetch", "melonLiveFetch", "jiosaavnLiveFetch", "kkboxLiveFetch", "tiktokLiveFetch",
    # Not possible right now (each file explains why)
    "amazonMusicLiveFetch", "tidalLiveFetch", "instagramLiveFetch", "iheartRadioLiveFetch",
    "anghamiLiveFetch", "lineMusicLiveFetch",
]



def run_platform(name):
    """Run one platform. Returns (status, detail) and never raises."""
    try:
        module = importlib.import_module(f"platforms.{name}")
        charts = module.fetch()  # {"chart_name": [rows], ...}
    except PlatformUnavailable as e:
        return "UNAVAILABLE", str(e)
    except Exception as e:  # anything else: this run failed, try again next time
        log.exception("%s failed", name)
        return "ERROR", f"{type(e).__name__}: {e}"

    parts = []
    for chart, rows in charts.items():
        if not rows:
            parts.append(f"{chart}: 0 rows (format may have changed)")
            continue
        changed = save(name.removesuffix("LiveFetch"), chart, rows)
        parts.append(f"{chart}: {len(rows)} rows, {'CHANGED' if changed else 'no change'}")
    return "OK", "; ".join(parts)


def run_once(names):
    log.info("=== run started: %d platforms ===", len(names))
    for name in names:
        status, detail = run_platform(name)
        log.info("%-22s %-11s %s", name, status, detail)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="+", choices=PLATFORMS, help="run only these platforms")
    parser.add_argument("--every", type=float, help="repeat every N minutes")
    parser.add_argument("--hours", type=float, default=24, help="with --every: stop after N hours")
    args = parser.parse_args()

    setup_logging()
    names = args.only or PLATFORMS

    if not args.every:
        run_once(names)
        return

    deadline = time.time() + args.hours * 3600
    while time.time() < deadline:
        run_once(names)
        time.sleep(max(0, min(args.every * 60, deadline - time.time())))
    log.info("finished after %.1f hours", args.hours)


if __name__ == "__main__":
    main()
