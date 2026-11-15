# Spotify & YouTube daily data

Two files, each with **one row per song per day**, covering the past year. They were built to backtest predictions of Polymarket's *"#1 song on Spotify this week"* market. That market resolves on **Spotify's Global weekly chart**, which counts streams **Friday through Thursday**.

| File | What | Days | Rows |
|---|---|---|---|
| `spotify_daily.csv` | Spotify **Global Top 200**: streams per song per day | Oct 1 2025 → Nov 7 2026 (403 days) | 68,006 |
| `youtube_daily.csv` | YouTube **Top 200 music videos worldwide**: views per video per day | Oct 1 2025 → Nov 13 2026 (408 days) | 81,600 |

```python
import pandas as pd
spotify = pd.read_csv("data/spotify_daily.csv", parse_dates=["date"])
youtube = pd.read_csv("data/youtube_daily.csv", parse_dates=["date"])

spotify[spotify.date == "2026-01-01"].head(10)   # that day's top 10 songs
```

---

## `spotify_daily.csv`

| Column | Meaning |
|---|---|
| `date` | The day the streams happened |
| `rank` | Rank that day, by streams (1 = most streamed) |
| `official_rank` | Spotify's own published rank, when it's known (67% of rows) |
| `artist`, `title`, `featured` | The song; `featured` lists guest artists |
| `streams` | **Global Spotify streams that day** |
| `change_vs_prev_day` | Streams minus the same song's streams the day before (momentum) |
| `pct_change_vs_prev_day` | The same change as a % |
| `us_rank`, `us_streams` | US chart rank and streams. Only known for about 21% of rows, mostly a song's most recent month on the chart. |
| `polymarket_contender` | `True` if Polymarket ever listed this song as an outcome |
| `full_chart_day` | `True` if Spotify's complete Top 200 for that day was archived (see coverage) |
| `streams_source` | How the number was obtained (see below) |
| `track_id` | Spotify track ID; `https://open.spotify.com/track/<track_id>` opens it |

**Coverage**
- **175 days** have Spotify's complete Top 200 (`full_chart_day = True`). On those days `rank` matches Spotify's official rank 99.5% of the time; the rest are near-ties.
- On the other days, only songs that reached the Global Top 50 at some point are known, so the bottom of the list can be short. The median is 194 rows per day, 361 days have at least 50 songs, and every day has at least 14. **The top of the chart, where the #1 race happens, is there almost every day.**
- `change_vs_prev_day` is filled for 87% of rows. It's blank when the song's previous day isn't in the data.

**Where `streams` comes from** (`streams_source`): all values are Spotify's own daily chart numbers, as mirrored by kworb.net. kworb only keeps recent history, so the year was rebuilt from archived copies of its pages on the Wayback Machine (web.archive.org):

| Source | Meaning | Share |
|---|---|---|
| `chart_snapshot` | An archived copy of that day's full Global Top 200 | 40% |
| `archived_track_page` / `track_page` | The song's own kworb page, archived or current | 26% |
| `derived_prev_day` | From the next day's chart: streams minus the "change vs yesterday" | 20% |
| `derived_prev_week` | From the chart a week later: streams minus the "change vs a week ago" | 11% |
| `derived_7day_total` | One missing day solved from the chart's rolling 7-day total | 3% |

All three derived methods were checked against known values and match exactly. **There are no estimates in the Spotify file.**

---

## `youtube_daily.csv`

| Column | Meaning |
|---|---|
| `date` | The day |
| `rank` | Rank that day, by 24-hour views (1 = most viewed) |
| `video_title` | The YouTube video |
| `views_24h` | **YouTube views in 24 hours** |
| `change_vs_prev_day` | Views minus the same video's views the day before (momentum) |
| `pct_change_vs_prev_day` | The same change as a % |
| `likes_24h` | Likes in 24 hours (blank on estimated days) |
| `spotify_artist`, `spotify_title` | The matching song on Spotify's Global chart, when there is one |
| `polymarket_contender` | `True` if the video belongs to a song Polymarket listed |
| `estimated` | `True` if the row is an estimate, not real data (see coverage) |
| `as_of_eastern` | When the 24-hour number was taken (US Eastern time) |
| `video_id` | YouTube ID; `https://www.youtube.com/watch?v=<video_id>` opens it |
| `spotify_track_id` | Spotify track ID of the matching song |

**Coverage**
- Every day has exactly 200 videos. **331 days are real data.**
- **77 days are estimates** (`estimated = True`). No archived copy exists for those days, so each video's views are interpolated between the real days on either side. Almost all are single-day gaps. Drop them with `youtube[~youtube.estimated]` if you only want real numbers.
- **Oct 18, 2026 is missing.** The archive gap around it was too long to estimate.

**Things to know**
- **This is the worldwide YouTube chart, not just music that's big on Spotify.** About 21% of rows match a Spotify chart song. The rest are mostly Indian film music, K-pop and Latin videos. Filter with `youtube[youtube.spotify_title.notna()]`.
- **One song can have several videos** (official video, lyric video, audio), each as its own row. To get a song's total YouTube views per day, group by `date` + `spotify_title` and sum `views_24h`.
- **The 24 hours aren't exactly midnight to midnight.** The number is kworb.net's rolling 24-hour count, taken when its page was archived. That's usually within a couple of hours of the end of the day, but up to ~12 hours off; `as_of_eastern` shows the time.
- Song matching is automatic, by title plus artist name, so spot-check any surprising matches.

**Where it comes from:** kworb.net's "most viewed music videos in the past 24 hours" page, which reads YouTube's public view counts. History comes from the page's archived copies on the Wayback Machine.

---

## Limits that apply to both

- **Daily is the finest detail that exists for the past.** No public source has hourly Spotify or YouTube counts for past days. Spotify only publishes daily totals.
- Spotify numbers are **global**; US numbers are partial.
- **TikTok isn't included.** No free source keeps TikTok song history.

## Updating

Run `python run_all.py` from the project folder to rebuild both files with the newest days. To collect new data from now on, including hourly YouTube views, use `run_tracker.bat`, which writes to the `live/` folder (see the main `README.md`).
