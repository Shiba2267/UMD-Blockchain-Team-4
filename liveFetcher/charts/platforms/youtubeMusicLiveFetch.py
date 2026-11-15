"""
YouTube Music - same as YouTube.

NOTE: YouTube Music and YouTube share one chart site: charts.youtube.com IS
YouTube Music's chart site. So this one file covers both - there is no
separate YouTube file.

Method: the same hidden `browse` request the charts page makes (see
youtube_basic.py). No key or login needed.
"""
from common import find_list, http_post, make_row

# ---- Settings ----
COUNTRY = "global"  # global, us, gb, in, kr, jp, br ...
CHARTS = [          # (chart type, period)
    ("TRACKS", "WEEKLY"),   # top songs
    ("VIDEOS", "DAILY"),    # top music videos, daily
    ("ARTISTS", "WEEKLY"),  # top artists
]

URL = "https://charts.youtube.com/youtubei/v1/browse?alt=json"
LIST_KEY = {"TRACKS": "trackViews", "VIDEOS": "videoViews", "ARTISTS": "artistViews"}


def fetch():
    results = {}
    for chart_type, period in CHARTS:
        payload = {
            "context": {"client": {"clientName": "WEB_MUSIC_ANALYTICS", "clientVersion": "2.0",
                                   "hl": "en", "gl": "US"}},
            "browseId": "FEmusic_analytics_charts_home",
            "query": (f"perspective=CHART_DETAILS&chart_params_country_code={COUNTRY}"
                      f"&chart_params_chart_type={chart_type}&chart_params_period_type={period}"),
        }
        data = http_post(URL, json=payload).json()
        rows = []
        for entry in find_list(data, LIST_KEY[chart_type]) or []:
            meta = entry.get("chartEntryMetadata", {})
            name = entry.get("name") or entry.get("title")
            if chart_type == "ARTISTS":
                artists = [name]
            else:
                artists = [a.get("name", "") for a in entry.get("artists", [])]
            video_id = entry.get("encryptedVideoId")
            rows.append(make_row(
                rank=meta.get("currentPosition"), title=name, artists=artists,
                metric=entry.get("viewCount"), metric_name="views",
                url=f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
            ))
        results[f"{COUNTRY}_{chart_type.lower()}_{period.lower()}"] = rows
    return results
