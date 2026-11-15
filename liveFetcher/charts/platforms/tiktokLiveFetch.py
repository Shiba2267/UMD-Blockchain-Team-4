"""
TikTok Creative Center - trending songs and hashtags.
(ads.tiktok.com/business/creativecenter, TikTok's free trend tool for advertisers)

Why this one is harder: the Creative Center adds a cryptographic signature to
every data request, computed by JavaScript in the page. We can't easily make
that signature in Python. So instead we run a real (invisible) Chrome with
Playwright, let the page make its own signed request, and copy the answer.

One-time setup (PowerShell):
    py -m pip install playwright
    py -m playwright install chromium

If nothing comes back, TikTok may be showing a captcha: set HEADLESS = False
below to watch the browser and solve it once.
"""
from common import PlatformUnavailable, make_row

HEADLESS = True
BASE = "https://ads.tiktok.com/business/creativecenter/inspiration/popular"
PAGES = {
    # chart name: (page to open, piece of the data request's address to watch for)
    "songs": (f"{BASE}/music/pc/en", "popular_trend/sound/rank_list"),
    "hashtags": (f"{BASE}/hashtag/pc/en", "popular_trend/hashtag/list"),
}


def _rows(chart, items):
    rows = []
    for i, it in enumerate(items, start=1):
        if chart == "songs":
            rows.append(make_row(rank=it.get("rank") or i, title=it.get("title"),
                                 artists=it.get("author"), url=it.get("link")))
        else:
            tag = it.get("hashtag_name", "")
            rows.append(make_row(rank=it.get("rank") or i, title="#" + tag, artists=[],
                                 metric=it.get("publish_cnt"), metric_name="posts",
                                 url=f"https://www.tiktok.com/tag/{tag}"))
    return rows


def fetch():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise PlatformUnavailable(
            "Unable to do yet: needs Playwright. Run  py -m pip install playwright  "
            "then  py -m playwright install chromium")

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page(locale="en-US")
        for chart, (url, marker) in PAGES.items():
            # expect_response waits for the page's own data request and hands us its answer.
            with page.expect_response(lambda r: marker in r.url and r.ok, timeout=45_000) as caught:
                page.goto(url)
            body = caught.value.json()
            items = (body.get("data") or {}).get("list") or (body.get("data") or {}).get("sound_list") or []
            results[chart] = _rows(chart, items)
        browser.close()
    return results
