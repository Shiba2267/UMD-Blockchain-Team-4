"""
Melon (melon.com) - South Korea's biggest music service.

Method: Melon builds its chart pages on the server, so - unlike YouTube - the
songs ARE in the HTML. We download the page and pull values out of it with
BeautifulSoup, which turns HTML into something Python can search.

How the page is laid out (find it yourself: F12 > Elements on melon.com/chart):
  * each song is a <tr> row; ranks 1-50 have class "lst50", 51-100 "lst100"
  * the row's  data-song-no="..."  attribute is the song's ID
  * <span class="rank">        -> the rank number
  * <div class="ellipsis rank01"> -> contains the title link
  * <div class="ellipsis rank02"> -> contains the artist link(s)
If Melon redesigns the page, these class names are what you'd update.
"""
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
from common import PlatformUnavailable, http_get, make_row

CHARTS = {
    "top100_realtime": "https://www.melon.com/chart/index.htm",
    "daily": "https://www.melon.com/chart/day/index.htm",
    "weekly": "https://www.melon.com/chart/week/index.htm",
}


def fetch():
    if BeautifulSoup is None:
        raise PlatformUnavailable(
            "Unable to do yet: needs BeautifulSoup. Run  py -m pip install beautifulsoup4")
    results = {}
    for chart, url in CHARTS.items():
        soup = BeautifulSoup(http_get(url).text, "html.parser")
        rows = []
        for tr in soup.select("tr.lst50, tr.lst100"):  # comma = "either one"
            title = tr.select_one(".ellipsis.rank01 a")
            # The artist cell often contains the same link twice (one hidden), so de-duplicate
            # while keeping order: dict.fromkeys() keeps the first copy of each name.
            artists = list(dict.fromkeys(a.get_text(strip=True) for a in tr.select(".ellipsis.rank02 a")))
            rank = tr.select_one("span.rank")
            song_id = tr.get("data-song-no")
            rows.append(make_row(
                rank=rank.get_text(strip=True) if rank else None,
                title=title.get_text(strip=True) if title else None,
                artists=artists,
                url=f"https://www.melon.com/song/detail.htm?songId={song_id}" if song_id else None,
            ))
        results[chart] = rows
    return results
