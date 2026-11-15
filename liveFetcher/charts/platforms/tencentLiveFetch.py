"""
Tencent - QQ Music (y.qq.com), China's largest music app.

Method: QQ Music's older public web endpoint `fcg_v8_toplist_cp.fcg`. No login.
The newer endpoint the current website uses (`musicu.fcg`) is reported to reject
requests from data centres, so we use the older one, which returns the same chart.
It also wants a "Referer" header (the page the request supposedly came from),
otherwise it can refuse.

Not covered: Tencent Music also owns Kugou and Kuwo, which have separate charts.

Chart IDs (topid):
  26 = 热歌榜 Hot Songs, 27 = 新歌榜 New Songs, 62 = 飙升榜 Rising
"""
from common import http_get, make_row

TOPLISTS = {"hot_songs": 26, "new_songs": 27, "rising": 62}
URL = "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg"


def fetch():
    results = {}
    for chart, top_id in TOPLISTS.items():
        params = {"topid": top_id, "type": "top", "song_begin": 0, "song_num": 100,
                  "format": "json", "inCharset": "utf8", "outCharset": "utf-8",
                  "platform": "yqq.json", "needNewCode": 0, "g_tk": 5381}
        data = http_get(URL, params=params, headers={"Referer": "https://y.qq.com/"}).json()
        rows = []
        for i, item in enumerate(data.get("songlist", []), start=1):
            song = item.get("data", {})
            rows.append(make_row(
                rank=i,  # the list arrives in chart order
                title=song.get("songname"),
                artists=[s.get("name", "") for s in song.get("singer", [])],
                url=f"https://y.qq.com/n/ryqq/songDetail/{song['songmid']}" if song.get("songmid") else None,
            ))
        results[chart] = rows
    return results
