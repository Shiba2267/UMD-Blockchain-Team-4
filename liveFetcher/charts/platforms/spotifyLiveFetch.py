"""
Spotify Charts (charts.spotify.com)

The chart site only shows data to logged-in users, so there are two routes:

 1. OFFICIAL (full top 200 + stream counts) - needs a login token you copy yourself:
    log in at charts.spotify.com, press F12 > Network, click any chart, find a
    request to charts-spotify-com-service.spotify.com, copy the value of its
    `authorization` header (it starts "Bearer "), then in PowerShell:
        $env:SPOTIFY_CHARTS_TOKEN = "Bearer eyJ..."
    Tokens expire after about an hour, so this suits one-off runs, not 30-hour loops.

 2. FALLBACK (no login) - kworb.net, a long-running fan site that republishes
    Spotify's daily and weekly charts with stream counts. Used automatically
    when no token is set.
"""
import os

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from common import PlatformUnavailable, http_get, make_row


# ---- Settings ----
REGION = "global"  # global, us, gb, kr, jp, br ... (lowercase)
PERIODS = ["daily", "weekly"]

API = "https://charts-spotify-com-service.spotify.com/auth/v0/charts"


def fetch():
    token = os.environ.get("SPOTIFY_CHARTS_TOKEN")
    results = {}
    for period in PERIODS:
        if token:
            results[f"{REGION}_{period}"] = _from_official(period, token)
        else:
            results[f"{REGION}_{period}"] = _from_kworb(period)
    return results


def _from_official(period, token):
    if not token.lower().startswith("bearer "):
        token = "Bearer " + token
    data = http_get(f"{API}/regional-{REGION}-{period}/latest",
                    headers={"Authorization": token}).json()
    rows = []
    for entry in data.get("entries", []):
        chart, track = entry.get("chartEntryData", {}), entry.get("trackMetadata", {})
        track_id = track.get("trackUri", "").split(":")[-1]
        rows.append(make_row(
            rank=chart.get("currentRank"), title=track.get("trackName"),
            artists=[a.get("name", "") for a in track.get("artists", [])],
            metric=(chart.get("rankingMetric") or {}).get("value"), metric_name="streams",
            url=f"https://open.spotify.com/track/{track_id}" if track_id else None,
        ))
    return rows


def _from_kworb(period):
    if BeautifulSoup is None:
        raise PlatformUnavailable(
            "Unable to do yet: needs BeautifulSoup. Run  py -m pip install beautifulsoup4")
    response = http_get(f"https://kworb.net/spotify/country/{REGION}_{period}.html")
    response.encoding = "utf-8"  # the page doesn't declare it clearly; without this, accents break
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")
    headers = [th.get_text(strip=True) for th in table.find_all("th")]
    col = {name: i for i, name in enumerate(headers)}  # find columns by name, not position

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        artist, _, title = cells[col["Artist and Title"]].partition(" - ")
        link = tr.find("a", href=lambda h: h and "/track/" in h)
        rows.append(make_row(
            rank=cells[col["Pos"]], title=title, artists=artist,
            metric=cells[col["Streams"]], metric_name="streams",
            url=link["href"] if link else None,
        ))
    return rows
