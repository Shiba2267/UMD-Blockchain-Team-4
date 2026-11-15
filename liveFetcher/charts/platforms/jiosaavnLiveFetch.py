"""
JioSaavn (jiosaavn.com) - one of India's biggest music services.

Method: the website's internal `api.php` endpoint (the same one its own pages
call). No login. Two steps:
  1. content.getCharts      -> the list of charts (each one is really a playlist)
  2. playlist.getDetails    -> the songs in one chart

NOTE: this endpoint isn't documented. Its shape has changed before, so the
parsing below checks a few possible field names. If you get 0 rows, open
jiosaavn.com, F12 > Network, click a chart, and compare with what you see.
"""
import html

from common import http_get, make_row

MAX_CHARTS = 3  # JioSaavn has dozens of charts (per language); take the first few
API = "https://www.jiosaavn.com/api.php"
BASE = {"_format": "json", "_marker": "0", "api_version": "4", "ctx": "web6dot0"}


def _call(method, **params):
    return http_get(API, params={**BASE, "__call": method, **params}).json()


def _artists(song):
    info = song.get("more_info", {})
    primary = (info.get("artistMap") or {}).get("primary_artists") or []
    if primary:
        return [a.get("name", "") for a in primary]
    # older shape: one comma-separated string
    return (song.get("primary_artists") or song.get("subtitle") or "").split(", ")


def fetch():
    charts = _call("content.getCharts")
    if isinstance(charts, dict):  # sometimes wrapped as {"data": [...]}
        charts = charts.get("data") or charts.get("charts") or []

    results = {}
    for chart in charts[:MAX_CHARTS]:
        listid = chart.get("id") or chart.get("listid")
        name = html.unescape(chart.get("title") or chart.get("listname") or str(listid))
        details = _call("playlist.getDetails", listid=listid, n=100, p=1)
        songs = details.get("list") or details.get("songs") or []
        key = "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")
        results[key] = [
            make_row(rank=i,
                     title=html.unescape(s.get("title") or s.get("song") or ""),  # titles arrive HTML-escaped (&amp;)
                     artists=[html.unescape(a) for a in _artists(s)],
                     metric=s.get("play_count"), metric_name="plays",
                     url=s.get("perma_url"))
            for i, s in enumerate(songs, start=1)
        ]
    return results
