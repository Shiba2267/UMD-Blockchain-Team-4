# Polymarket history: weekly #1 / #2 song markets

Historical Polymarket data for the weekly "top song" markets, plus the top 10
traders in them by volume. Pulled 2026-11-13.

## Coverage

Polymarket only started these markets in Nov 2025, so this is everything that
exists (about 1 year, not 2).

| family | rank | weekly events | first week ending | last week ending |
|---|---|---|---|---|
| `spotify_global` | #1 | 48 | 2025-11-21 | 2026-11-13 |
| `spotify_global` | #2 | 16 | 2026-07-24 | 2026-11-13 |
| `spotify_us` | #1 | 46 | 2025-12-18 | 2026-11-13 |
| `spotify_us` | #2 | 16 | 2026-07-24 | 2026-11-13 |
| `billboard_hot100` | #1 | 43 | 2026-01-13 | 2026-11-17 |
| `billboard_hot100` | #2 | 19 | 2026-04-20 | 2026-11-17 |

188 weekly events, 3,496 song markets. Each event is one week of one chart; each
market inside it is one song ("Will X be the #1 song?"). The 6 events for the
current week were still open when this was pulled.

## Files (`data/`)

### `markets.csv` — one row per song market
| column | meaning |
|---|---|
| `family`, `rank` | which chart, and whether it is the #1 or #2 market |
| `event_id`, `event_title`, `event_slug` | the weekly event the market belongs to |
| `week_end_date` | scheduled end date of the event (UTC) |
| `market_id`, `condition_id`, `yes_token_id` | Polymarket identifiers |
| `label`, `song`, `artist` | outcome name as listed, and a best-effort split |
| `open_time_utc`, `close_time_utc` | when trading opened / the market resolved |
| `closed` | 1 if resolved |
| `won` | 1 if this song won, 0 if not, blank if still open |
| `last_yes_price` | final (or latest) Yes price |
| `volume_shares` | Polymarket's reported volume, in shares (not USD) |

About 1,870 rows are unused placeholder slots ("Song C", "Song D", ...) that
Polymarket pre-creates. They have `volume_shares = 0` and no price history;
filter them out with `volume_shares > 0`.

### `prices_<family>.csv` — Yes price every 10 minutes
`timestamp_utc`, `ts` (epoch seconds), `market_id`, `rank`, `week_end_date`,
`label`, `yes_price` (0–1, i.e. the implied probability). Join to `markets.csv`
on `market_id`. Covers each market from open to close. 1.63M rows in total.

### `top10_traders.csv` — top 10 wallets by USD volume across all markets above
| column | meaning |
|---|---|
| `volume_usd` | sum of price × size over every fill, maker and taker side |
| `buy_usd`, `sell_usd` | the same, split by side |
| `fills`, `markets_traded`, `weeks_traded` | activity counts |
| `polymarket_reported_pnl_usd` | sum of `total_pnl` from Polymarket's positions API for these events |
| `volume_usd_<family>` | volume split by chart |

### `top10_trades.csv` — every fill by those 10 wallets (14,637 rows)
`timestamp_utc`, `ts`, `volume_rank`, `wallet`, `username`, `family`, `rank`,
`week_end_date`, `market_id`, `label`, `side` (BUY/SELL), `outcome` (Yes/No token),
`price`, `size_shares`, `usd`, `transaction_hash`.

## Caveats

- **Volume counts both sides.** A wallet gets credit for a fill whether it was
  the maker or the taker, so wallet volumes summed across everyone are 2× market volume.
- **Ranks 2 and 4 look like one-off outliers.** `anasheDispatch` and `crawMetox`
  each have ~$215k volume from only 13–14 fills, with buys ≈ sells, ending at the
  same second. They are probably not useful as "smart money" signals.
- **PnL is Polymarket's number, not recomputed.** These are neg-risk markets
  where positions can be converted without a trade, so treat it as approximate.
- **Price points are Polymarket's sampled price series**, not individual trades
  or order-book quotes. Thin markets can show stale prices.

## Refreshing

```bash
python pull_polymarket_history.py
```

Python 3.10+, standard library only. Responses for closed markets are cached in
`cache/` (git-ignored), so a weekly re-run only downloads new markets. A full
pull from scratch takes about 3 minutes.

APIs used: Gamma (`/events`, market discovery), CLOB (`/prices-history`),
Data API v2 (`/trades`, `/positions`).
