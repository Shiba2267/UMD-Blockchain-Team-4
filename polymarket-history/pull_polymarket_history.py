"""Pull historical Polymarket data for the weekly "#1 / #2 song" markets.

Outputs (in ./data):
  markets.csv              one row per song market
  prices_<family>.csv      "Yes" price every 10 minutes for every market
  top10_traders.csv        top 10 wallets by USD volume across these markets
  top10_trades.csv         every fill those 10 wallets made in these markets

Standard library only:  python pull_polymarket_history.py
Raw API responses for closed markets are cached in ./cache, so re-running
each week only downloads what is new.
"""
import csv
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
DATA = "https://data-api.polymarket.com/v2"
MUSIC_TAG_ID = 100
FIDELITY_MIN = 10          # price resolution in minutes
CHUNK_SEC = 7 * 86400      # prices-history rejects long windows
TOP_N = 10
WORKERS = 8

HERE = Path(__file__).resolve().parent
OUT = HERE / "data"
CACHE = HERE / "cache"


# ---------------------------------------------------------------- http

def get(url, tries=6):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "curl/8.4.0", "Accept": "*/*",
                "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return json.loads(body)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == tries - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == tries - 1:
                raise
        time.sleep(1.5 * 2 ** attempt)


def get_all(url):
    """Follow Data API v2 cursor pagination."""
    rows, cursor = [], None
    while True:
        page = get(url + ("&cursor=" + urllib.parse.quote(cursor) if cursor else ""))
        rows += page["data"]
        if not page["pagination"].get("has_more"):
            return rows
        cursor = page["pagination"]["next_cursor"]


def cached(name, final, fetch):
    """Cache `fetch()` on disk, but only once the market is closed (`final`)."""
    path = CACHE / name
    if path.exists():
        return json.loads(path.read_text())
    result = fetch()
    if final:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result))
    return result


# ---------------------------------------------------------------- helpers

def ts(s):
    """Parse the several ISO-ish timestamp formats Gamma uses -> epoch seconds."""
    if not s:
        return None
    s = s.strip().replace(" ", "T").replace("Z", "+00:00")
    s = re.sub(r"\.\d+", "", s)
    s = re.sub(r"([+-]\d\d)$", r"\1:00", s)
    return int(datetime.fromisoformat(s).timestamp())


def iso(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if t else ""


def classify(event):
    """Return (family, rank) for a weekly song event, else None."""
    title = event["title"]
    m = re.match(r"Billboard Hot 100 #([12]) Song Week of", title)
    if m:
        return "billboard_hot100", int(m.group(1))
    m = re.match(r"#([12]) .*song.*this week\?", title)
    if m and "Spotify" in (title + (event.get("description") or "")):
        us = re.search(r"\bUS\b", title) is not None
        return ("spotify_us" if us else "spotify_global"), int(m.group(1))
    return None


def split_song(label):
    for sep in (" – ", " - ", " by "):
        if sep in label:
            song, artist = label.rsplit(sep, 1) if sep == " by " else label.split(sep, 1)
            return song.strip(), artist.strip()
    return label.strip(), ""


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  wrote {path.name}: {len(rows):,} rows, {path.stat().st_size / 1e6:.1f} MB")


# ---------------------------------------------------------------- steps

def discover():
    events = []
    for closed in ("true", "false"):
        offset = 0
        while True:
            page = get(f"{GAMMA}/events?tag_id={MUSIC_TAG_ID}&closed={closed}&limit=50&offset={offset}")
            if not page:
                break
            events += page
            offset += 50
    markets = []
    for e in events:
        fam = classify(e)
        if not fam:
            continue
        for m in e.get("markets", []):
            if not m.get("clobTokenIds"):
                continue
            label = m.get("groupItemTitle") or m["question"]
            song, artist = split_song(label)
            closed = bool(m.get("closed"))
            start = ts(m.get("startDate") or e.get("startDate"))
            end = ts(m.get("closedTime")) if closed else int(time.time())
            end = end or ts(m.get("endDate") or e.get("endDate"))
            prices = json.loads(m.get("outcomePrices") or "[]")
            markets.append({
                "family": fam[0], "rank": fam[1],
                "event_id": e["id"], "event_title": e["title"], "event_slug": e["slug"],
                "week_end_date": (e.get("endDate") or "")[:10],
                "market_id": m["id"], "condition_id": m["conditionId"],
                "yes_token_id": json.loads(m["clobTokenIds"])[0],
                "label": label, "song": song, "artist": artist,
                "open_time_utc": iso(start), "close_time_utc": iso(end) if closed else "",
                "closed": int(closed),
                "won": (int(float(prices[0]) > 0.5) if closed and prices else ""),
                "last_yes_price": prices[0] if prices else "",
                "volume_shares": round(float(m.get("volume") or 0), 2),
                "_start": start, "_end": end,
            })
    markets.sort(key=lambda r: (r["family"], r["rank"], r["week_end_date"], -r["volume_shares"]))
    return markets


def fetch_prices(mk):
    def fetch():
        pts, t = [], mk["_start"]
        while t < mk["_end"]:
            t2 = min(t + CHUNK_SEC, mk["_end"])
            pts += get(f"{CLOB}/prices-history?market={mk['yes_token_id']}"
                       f"&startTs={t}&endTs={t2}&fidelity={FIDELITY_MIN}")["history"]
            t = t2
        return sorted({p["t"]: p["p"] for p in pts}.items())
    if not mk["_start"] or not mk["_end"] or mk["_end"] <= mk["_start"]:
        return []
    return cached(f"prices/{mk['market_id']}.json", mk["closed"], fetch)


def fetch_trades(event_id, final):
    # taker_only=false returns one row per wallet per fill (maker AND taker side)
    return cached(f"trades/{event_id}.json", final, lambda: get_all(
        f"{DATA}/trades?event_id={event_id}&limit=1000&taker_only=false"))


def fetch_pnl(wallet, event_ids):
    total = 0.0
    for i in range(0, len(event_ids), 20):
        ids = ",".join(event_ids[i:i + 20])
        for status in ("OPEN", "CLOSED", "REDEEMABLE", "REDEEMABLE_LOST"):
            for p in get_all(f"{DATA}/positions?user={wallet}&event_id={ids}"
                             f"&status={status}&limit=1000"):
                total += p.get("total_pnl") or 0
    return round(total, 2)


def main():
    OUT.mkdir(exist_ok=True)
    print("1/4 discovering markets")
    markets = discover()
    by_cid = {m["condition_id"]: m for m in markets}
    events = {}
    for m in markets:
        events.setdefault(m["event_id"], []).append(m)
    print(f"  {len(events)} weekly events, {len(markets)} song markets")
    cols = [c for c in markets[0] if not c.startswith("_")]
    write_csv(OUT / "markets.csv", cols, [[m[c] for c in cols] for m in markets])

    print("2/4 price history")
    with ThreadPoolExecutor(WORKERS) as ex:
        histories = list(ex.map(fetch_prices, markets))
    for fam in sorted({m["family"] for m in markets}):
        rows = [(iso(t), t, m["market_id"], m["rank"], m["week_end_date"], m["label"], p)
                for m, h in zip(markets, histories) if m["family"] == fam for t, p in h]
        write_csv(OUT / f"prices_{fam}.csv",
                  ["timestamp_utc", "ts", "market_id", "rank", "week_end_date", "label", "yes_price"], rows)

    print("3/4 trades")
    ev_final = {eid: all(m["closed"] for m in ms) for eid, ms in events.items()}
    with ThreadPoolExecutor(WORKERS) as ex:
        trade_lists = list(ex.map(lambda eid: fetch_trades(eid, ev_final[eid]), events))
    trades = [t for lst in trade_lists for t in lst if t["condition_id"] in by_cid]
    print(f"  {len(trades):,} fills (maker + taker rows)")

    print("4/4 top traders")
    agg = defaultdict(lambda: {"usd": 0.0, "n": 0, "mk": set(), "ev": set(), "name": "",
                               "buy": 0.0, "sell": 0.0, "first": 1e18, "last": 0,
                               "fam": defaultdict(float)})
    for t in trades:
        a, mk = agg[t["proxy_wallet"]], by_cid[t["condition_id"]]
        usd = t["size"] * t["price"]
        a["usd"] += usd
        a["buy" if t["side"] == "BUY" else "sell"] += usd
        a["n"] += 1
        a["mk"].add(t["condition_id"])
        a["ev"].add(mk["event_id"])
        a["fam"][mk["family"]] += usd
        a["name"] = t.get("name") or t.get("pseudonym") or a["name"]
        a["first"], a["last"] = min(a["first"], t["timestamp"]), max(a["last"], t["timestamp"])
    top = sorted(agg.items(), key=lambda kv: -kv[1]["usd"])[:TOP_N]
    fams = sorted({m["family"] for m in markets})
    rows = []
    for i, (w, a) in enumerate(top, 1):
        try:
            pnl = fetch_pnl(w, sorted(a["ev"]))
        except Exception as e:  # PnL is a nice-to-have; never lose the pull over it
            print(f"  pnl lookup failed for {w}: {e}", file=sys.stderr)
            pnl = ""
        rows.append([i, w, a["name"], round(a["usd"], 2), round(a["buy"], 2), round(a["sell"], 2),
                     a["n"], len(a["mk"]), len(a["ev"]), iso(a["first"]), iso(a["last"]), pnl,
                     *[round(a["fam"][f], 2) for f in fams], f"https://polymarket.com/profile/{w}"])
    write_csv(OUT / "top10_traders.csv",
              ["volume_rank", "wallet", "username", "volume_usd", "buy_usd", "sell_usd", "fills",
               "markets_traded", "weeks_traded", "first_trade_utc", "last_trade_utc",
               "polymarket_reported_pnl_usd", *[f"volume_usd_{f}" for f in fams], "profile_url"], rows)

    rank = {w: i for i, (w, _) in enumerate(top, 1)}
    rows = []
    for t in sorted(trades, key=lambda t: t["timestamp"]):
        if t["proxy_wallet"] not in rank:
            continue
        mk = by_cid[t["condition_id"]]
        rows.append([iso(t["timestamp"]), t["timestamp"], rank[t["proxy_wallet"]], t["proxy_wallet"],
                     t.get("name") or t.get("pseudonym") or "", mk["family"], mk["rank"],
                     mk["week_end_date"], mk["market_id"], mk["label"], t["side"], t["outcome"],
                     t["price"], t["size"], round(t["size"] * t["price"], 4), t["transaction_hash"]])
    write_csv(OUT / "top10_trades.csv",
              ["timestamp_utc", "ts", "volume_rank", "wallet", "username", "family", "rank",
               "week_end_date", "market_id", "label", "side", "outcome", "price", "size_shares",
               "usd", "transaction_hash"], rows)
    print("done")


if __name__ == "__main__":
    main()
