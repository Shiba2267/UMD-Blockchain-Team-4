"""
Offline test: no internet needed. Each platform gets a fake response shaped
like the real site's, so we can check the parsing, saving and runner logic.

    py tests/test_offline.py

This proves the code handles the expected format. It can't prove the sites
still answer that way - only a real run can.
"""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import common  # noqa: E402

common.OUTPUT_DIR = ROOT / "tests" / "_output"  # keep test files away from real output
shutil.rmtree(common.OUTPUT_DIR, ignore_errors=True)


class Fake:
    """Stands in for a requests.Response."""
    def __init__(self, data=None, text=""):
        self._data, self.text, self.encoding = data, text, None

    def json(self):
        return self._data


def check(name, rows, expect_first):
    assert rows, f"{name}: no rows"
    first = {k: rows[0][k] for k in expect_first}
    assert first == expect_first, f"{name}: got {first}"
    print(f"  OK  {name:<28} {len(rows)} rows, #1 = {rows[0]['title']} - {rows[0]['artists']}")


# ---------------- YouTube ----------------
from platforms import youtubeMusicLiveFetch as youtube  # noqa: E402
youtube.http_post = lambda url, **k: Fake({"a": {"b": [{"trackViews": [
    {"name": "Dai Dai", "artists": [{"name": "Shakira"}, {"name": "Burna Boy"}], "viewCount": "41023456",
     "encryptedVideoId": "abc", "chartEntryMetadata": {"currentPosition": 1}}],
    "videoViews": [{"title": "POKITO", "artists": [{"name": "Daddy Yankee"}], "viewCount": "9",
                    "chartEntryMetadata": {"currentPosition": 1}}],
    "artistViews": [{"name": "Arijit Singh", "viewCount": "5", "chartEntryMetadata": {"currentPosition": 1}}]}]}})
yt = youtube.fetch()
check("youtube tracks", yt["global_tracks_weekly"], {"rank": 1, "artists": "Shakira, Burna Boy", "metric": 41023456})
check("youtube artists", yt["global_artists_weekly"], {"title": "Arijit Singh", "artists": "Arijit Singh"})

# ---------------- Spotify (kworb fallback) ----------------
from platforms import spotifyLiveFetch as spotify  # noqa: E402
os.environ.pop("SPOTIFY_CHARTS_TOKEN", None)
kworb_html = """<table><thead><tr><th>Pos</th><th>P+</th><th>Artist and Title</th><th>Days</th><th>Pk</th>
<th>(x?)</th><th>Streams</th><th>Streams+</th></tr></thead><tbody>
<tr><td>1</td><td>=</td><td><a href="../artist/x.html">KAROL G</a> - <a href="https://open.spotify.com/track/123">BbY WOW</a></td>
<td>20</td><td>1</td><td></td><td>5,123,456</td><td>+1</td></tr></tbody></table>"""
spotify.http_get = lambda url, **k: Fake(text=kworb_html)
sp = spotify.fetch()
check("spotify daily (kworb)", sp["global_daily"], {"rank": 1, "title": "BbY WOW", "artists": "KAROL G",
                                                    "metric": 5123456, "url": "https://open.spotify.com/track/123"})
# official route
os.environ["SPOTIFY_CHARTS_TOKEN"] = "eyJfake"
seen = {}
def fake_official(url, headers=None, **k):
    seen["auth"] = headers["Authorization"]
    return Fake({"entries": [{"chartEntryData": {"currentRank": 1, "rankingMetric": {"value": 999}},
                              "trackMetadata": {"trackName": "Housewife", "trackUri": "spotify:track:xyz",
                                                "artists": [{"name": "Tate McRae"}]}}]})
spotify.http_get = fake_official
check("spotify daily (official)", spotify.fetch()["global_daily"], {"metric": 999, "url": "https://open.spotify.com/track/xyz"})
assert seen["auth"] == "Bearer eyJfake", seen
os.environ.pop("SPOTIFY_CHARTS_TOKEN")

# ---------------- Apple Music ----------------
from platforms import appleMusicLiveFetch as apple_music  # noqa: E402
apple_music.http_get = lambda url, **k: Fake({"feed": {"results": [
    {"name": "Choosin' Texas", "artistName": "Ella Langley", "url": "https://music.apple.com/x"},
    {"name": "Ordinary", "artistName": "Alex Warren"}]}})
check("apple_music", apple_music.fetch()["us_top_songs"], {"rank": 1, "title": "Choosin' Texas"})

# ---------------- Deezer (incl. the error-inside-200 quirk) ----------------
from platforms import deezerLiveFetch as deezer  # noqa: E402
deezer.http_get = lambda url, **k: Fake({"data": [{"title": "Babydoll", "artist": {"name": "Jamie Miller"},
                                                   "rank": 912345, "link": "https://deezer.com/track/1"}]})
dz = deezer.fetch()
check("deezer top_worldwide", dz["top_worldwide"], {"rank": 1, "metric": 912345, "metric_name": "popularity"})
deezer.http_get = lambda url, **k: Fake({"error": {"type": "DataException", "code": 800}})
try:
    deezer.fetch()
    raise AssertionError("deezer error not caught")
except RuntimeError as e:
    print(f"  OK  deezer error-in-200 caught  ({e})")

# ---------------- QQ Music ----------------
from platforms import tencentLiveFetch as qq  # noqa: E402
qq.http_get = lambda url, **k: Fake({"songlist": [
    {"data": {"songname": "目及皆是你", "singer": [{"name": "小蓝背心"}], "songmid": "001"}}]})
check("tencent", qq.fetch()["hot_songs"], {"rank": 1, "title": "目及皆是你",
                                                    "url": "https://y.qq.com/n/ryqq/songDetail/001"})

# ---------------- Melon ----------------
from platforms import melonLiveFetch as melon  # noqa: E402
melon_html = """<table><tbody>
<tr class="lst50" data-song-no="111"><td><span class="rank">1</span></td>
 <td><div class="ellipsis rank01"><span><a>Drip</a></span></div>
     <div class="ellipsis rank02"><a>ATEEZ</a><span class="checkEllipsis"><a>ATEEZ</a></span></div></td></tr>
<tr class="lst100" data-song-no="222"><td><span class="rank">51</span></td>
 <td><div class="ellipsis rank01"><a>Song B</a></div><div class="ellipsis rank02"><a>A</a><a>B</a></div></td></tr>
</tbody></table>"""
melon.http_get = lambda url, **k: Fake(text=melon_html)
m = melon.fetch()["top100_realtime"]
check("melon", m, {"rank": 1, "title": "Drip", "artists": "ATEEZ"})
assert m[1]["rank"] == 51 and m[1]["artists"] == "A, B", m[1]

# ---------------- JioSaavn ----------------
from platforms import jiosaavnLiveFetch as jiosaavn  # noqa: E402
def fake_saavn(url, params=None, **k):
    if params["__call"] == "content.getCharts":
        return Fake([{"id": "110858205", "title": "Trending Today"}])
    return Fake({"list": [{"title": "Tu Mil Jaaye &amp; More", "perma_url": "https://jiosaavn.com/s/1",
                           "more_info": {"artistMap": {"primary_artists": [{"name": "Arijit Singh"}]}}}]})
jiosaavn.http_get = fake_saavn
check("jiosaavn", jiosaavn.fetch()["trending_today"], {"title": "Tu Mil Jaaye & More", "artists": "Arijit Singh"})

# ---------------- KKBOX (no keys -> UNAVAILABLE; with keys -> rows) ----------------
from platforms import kkboxLiveFetch as kkbox  # noqa: E402
os.environ.pop("KKBOX_CLIENT_ID", None)
try:
    kkbox.fetch()
    raise AssertionError("kkbox should need keys")
except common.PlatformUnavailable:
    print("  OK  kkbox without keys -> UNAVAILABLE")
os.environ.update(KKBOX_CLIENT_ID="id", KKBOX_CLIENT_SECRET="secret")
kkbox.http_post = lambda url, **k: Fake({"access_token": "tok"})
def fake_kk(url, **k):
    assert k["headers"]["Authorization"] == "Bearer tok"
    if url.endswith("/charts"):
        return Fake({"data": [{"id": "4mJSYXvueA8t0odsny"}]})
    return Fake({"data": [{"name": "Golden", "album": {"artist": {"name": "HUNTR/X"}}, "url": "https://kkbox.com/x"}]})
kkbox.http_get = fake_kk
check("kkbox with keys", kkbox.fetch()["tw_4mJSYXvueA8t0odsny"], {"title": "Golden", "artists": "HUNTR/X"})
for v in ("KKBOX_CLIENT_ID", "KKBOX_CLIENT_SECRET"):
    os.environ.pop(v)

# ---------------- TikTok rows (browser part can't run offline) ----------------
from platforms import tiktokLiveFetch as tiktok  # noqa: E402
check("tiktok row builder", tiktok._rows("hashtags", [{"hashtag_name": "dance", "publish_cnt": 1200}]),
      {"title": "#dance", "metric": 1200, "url": "https://www.tiktok.com/tag/dance"})

# ---------------- save(): change detection + history ----------------
rows = [common.make_row(1, "A", ["X"]), common.make_row(2, "B", ["Y"])]
assert common.save("demo", "chart", rows) is True
assert common.save("demo", "chart", rows) is False          # identical -> not saved again
assert common.save("demo", "chart", rows[::-1]) is True     # order changed -> saved
history = (common.OUTPUT_DIR / "demo" / "chart_history.csv").read_text(encoding="utf-8-sig").splitlines()
assert len(history) == 1 + 4, history                      # header + 2 versions x 2 rows
latest = json.loads((common.OUTPUT_DIR / "demo" / "chart_latest.json").read_text(encoding="utf-8"))
assert latest["rows"][0]["title"] == "B"
print("  OK  save(): skips unchanged, appends changed, latest.json updated")

# ---------------- runner: one failure doesn't stop the rest ----------------
import run_all  # noqa: E402
assert run_all.run_platform("instagramLiveFetch")[0] == "UNAVAILABLE"
assert run_all.run_platform("amazonMusicLiveFetch")[1].startswith("Unable to do for this reason")
apple_music.http_get = lambda url, **k: (_ for _ in ()).throw(ConnectionError("no internet"))
status, detail = run_all.run_platform("appleMusicLiveFetch")
assert status == "ERROR" and "no internet" in detail, (status, detail)
print("  OK  run_all: UNAVAILABLE and ERROR reported, nothing crashes")

shutil.rmtree(common.OUTPUT_DIR)
print("\nAll offline tests passed.")
