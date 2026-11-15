# Music charts collector

```
charts/
├── common.py        shared code: requests + retries, row format, saving, logging
├── run_all.py       runs every platform; one failure never stops the rest
├── platforms/       one file per platform - only "how to get this chart"
└── tests/           offline test (no internet needed)
```

## Setup (Windows, PowerShell)
```powershell
py -m pip install requests beautifulsoup4
# only for TikTok:
py -m pip install playwright
py -m playwright install chromium
```

## Run
```powershell
cd path\to\charts
py run_all.py                          # every platform, once
py run_all.py --only deezerLiveFetch melonLiveFetch     # just some
py run_all.py --every 30 --hours 30    # repeat every 30 min for 30 hours
py tests\test_offline.py               # check the code without internet
```

Results go to `output\<platform>\<chart>_latest.json` (newest version) and
`<chart>_history.csv` (every version, appended only when the chart changes).
`output\charts.log` records every run.

## Status

### Can be accessed (9)

| Platform | File | Status | Method |
|---|---|---|---|
| YouTube Music (= YouTube) | youtubeMusicLiveFetch.py | Works | Hidden request the charts page makes |
| Spotify | spotifyLiveFetch.py | Works | kworb.net mirror; full official data with a token you copy |
| Apple Music | appleMusicLiveFetch.py | Works | Official public feed |
| Deezer | deezerLiveFetch.py | Works | Official public API |
| Tencent (QQ Music) | tencentLiveFetch.py | Works | Public web endpoint |
| Melon | melonLiveFetch.py | Works | Reads the chart page's HTML |
| JioSaavn | jiosaavnLiveFetch.py | Works (undocumented API) | Website's internal API |
| KKBOX | kkboxLiveFetch.py | Needs free developer keys | Official API |
| TikTok | tiktokLiveFetch.py | Needs Playwright | Real browser captures the page's own request |

**Note:** YouTube Music and YouTube share one chart site (charts.youtube.com), so youtubeMusicLiveFetch.py covers both.

**TikTok can be accessed.** The TikTok Creative Center publishes trending songs and hashtags
on a public page. It's harder than the others because the page signs its data requests in a
way Python can't easily copy, so tiktokLiveFetch.py opens a real hidden Chrome browser and
takes the data from the page. It needs the one-time Playwright install shown under Setup.

### Cannot be accessed (6)

These files exist, but they only print "Unable to do for this reason: ..." and stop.

| Platform | File | Why not |
|---|---|---|
| Instagram | instagramLiveFetch.py | No chart exists: "trending audio" is only inside the phone app, different for each user, with no public page or API |
| Amazon Music | amazonMusicLiveFetch.py | The official API needs approval from Amazon; the website's chart data comes from Amazon's internal requests |
| TIDAL | tidalLiveFetch.py | Its official API has no charts |
| iHeartRadio | iheartRadioLiveFetch.py | It's a radio network and doesn't publish a live song chart |
| Anghami | anghamiLiveFetch.py | Its chart API needs a key that's only given to business partners |
| LINE MUSIC | lineMusicLiveFetch.py | Its rankings are only inside the app |

### What the labels in the log mean

| Label | Meaning |
|---|---|
| OK | The chart was collected. "CHANGED" means it was saved; "no change" means it matched last time. |
| UNAVAILABLE | Not an error: either the platform can't be accessed (table above), or it needs setup (KKBOX keys, Playwright for TikTok). |
| ERROR | Something went wrong during this run, e.g. no internet or the site changed its format. Check `output\charts.log`. |

## Adding a platform
Create `platforms/<name>LiveFetch.py` with a `fetch()` function that returns
`{"chart_name": [make_row(...), ...]}`, then add `<name>LiveFetch` to `PLATFORMS` in run_all.py.
