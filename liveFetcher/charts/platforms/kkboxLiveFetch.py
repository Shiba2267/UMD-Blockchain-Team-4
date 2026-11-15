"""
KKBOX - the leading music service in Taiwan and Hong Kong.

Method: KKBOX's OFFICIAL Open API. It needs a free developer account:
  1. Sign up at https://developer.kkbox.com/ and create an app.
  2. Copy its Client ID and Client Secret, then in PowerShell:
        $env:KKBOX_CLIENT_ID = "..."
        $env:KKBOX_CLIENT_SECRET = "..."

How the login works ("client credentials" - a pattern many official APIs use):
  * We send our ID + secret to KKBOX's token address and get back an
    "access token" - a temporary pass, valid about an hour.
  * Every data request then carries  Authorization: Bearer <token>.
  The secret itself never goes to the data API, only the temporary pass does.

In KKBOX, each chart is a playlist: /charts lists them, then we read a chart's tracks.
"""
import os

from common import PlatformUnavailable, http_get, http_post, make_row

TERRITORY = "TW"  # TW, HK, SG, MY, JP
MAX_CHARTS = 3
API = "https://api.kkbox.com/v1.1"


def _token():
    client_id = os.environ.get("KKBOX_CLIENT_ID")
    secret = os.environ.get("KKBOX_CLIENT_SECRET")
    if not (client_id and secret):
        raise PlatformUnavailable(
            "Unable to do yet: needs free KKBOX developer keys. Create an app at "
            "developer.kkbox.com, then set KKBOX_CLIENT_ID and KKBOX_CLIENT_SECRET.")
    response = http_post("https://account.kkbox.com/oauth2/token",
                         data={"grant_type": "client_credentials"},
                         auth=(client_id, secret))  # auth= sends them as a standard "Basic" login header
    return response.json()["access_token"]


def fetch():
    headers = {"Authorization": f"Bearer {_token()}"}
    charts = http_get(f"{API}/charts", params={"territory": TERRITORY}, headers=headers).json()

    results = {}
    for chart in charts.get("data", [])[:MAX_CHARTS]:
        tracks = http_get(f"{API}/charts/{chart['id']}/tracks",
                          params={"territory": TERRITORY, "limit": 100}, headers=headers).json()
        key = f"{TERRITORY.lower()}_{chart['id']}"
        results[key] = [
            make_row(rank=i, title=t.get("name"),
                     artists=((t.get("album") or {}).get("artist") or {}).get("name"),
                     url=t.get("url"))
            for i, t in enumerate(tracks.get("data", []), start=1)
        ]
    return results
