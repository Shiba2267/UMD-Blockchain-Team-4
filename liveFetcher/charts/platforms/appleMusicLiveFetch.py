"""
Apple Music - "Top Songs" (most played) chart.

Method: Apple's OFFICIAL public feed at rss.marketingtools.apple.com. It's meant
for websites and marketers to embed charts, so there's no key, no login and no
hidden request to reverse-engineer. The easiest platform on the list.

Limits: Apple publishes rank, title and artist only - no play counts.
"""
from common import http_get, make_row

# ---- Settings ----
COUNTRIES = ["us"]  # Apple storefront codes: us, gb, jp, kr, br, in, de, fr ...
LIMIT = 100         # the feed allows up to 100 songs


def fetch():
    results = {}
    for country in COUNTRIES:
        url = f"https://rss.marketingtools.apple.com/api/v2/{country}/music/most-played/{LIMIT}/songs.json"
        data = http_get(url).json()
        songs = data.get("feed", {}).get("results", [])
        # The list is already in chart order, so rank = position in the list.
        # enumerate(songs, start=1) gives (1, song), (2, song), ...
        results[f"{country}_top_songs"] = [
            make_row(rank=i, title=s.get("name"), artists=s.get("artistName"), url=s.get("url"))
            for i, s in enumerate(songs, start=1)
        ]
    return results
