"""
Deezer

Method: Deezer's OFFICIAL public API (api.deezer.com). No key or login.

Two charts:
  * "Top Worldwide" - Deezer's own editorial global chart, published as a playlist.
  * "chart" endpoint - Deezer's top tracks. Deezer may tailor this one to the
    country your internet connection appears to be in.

Quirk worth knowing: when something goes wrong, Deezer still answers "200 OK"
but puts an {"error": {...}} object in the body. raise_for_status() can't catch
that, so _get() checks for it by hand.

Limits: no stream counts. The "rank" number Deezer includes is a popularity
score, not a chart position, so it's stored as the metric "popularity".
"""
from common import http_get, make_row

TOP_WORLDWIDE_PLAYLIST = "3155776842"  # deezer.com/playlist/3155776842
LIMIT = 100


def _get(path):
    data = http_get(f"https://api.deezer.com/{path}", params={"limit": LIMIT}).json()
    if "error" in data:
        raise RuntimeError(f"Deezer API error: {data['error']}")
    return data.get("data", [])


def _rows(tracks):
    return [
        make_row(rank=i, title=t.get("title"), artists=(t.get("artist") or {}).get("name"),
                 metric=t.get("rank"), metric_name="popularity", url=t.get("link"))
        for i, t in enumerate(tracks, start=1)
    ]


def fetch():
    return {
        "top_worldwide": _rows(_get(f"playlist/{TOP_WORLDWIDE_PLAYLIST}/tracks")),
        "top_tracks": _rows(_get("chart/0/tracks")),  # 0 = all genres
    }
