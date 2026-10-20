# Mas Live TV

Curated **free** Malaysian TV, radio and football live channels as M3U
playlists. An AI curator refreshes the list daily (see `AGENTS.md`), and a
GitHub Action re-checks streams and rebuilds playlists every night at
04:00 MYT.

## Playlists

| File | What's in it |
|---|---|
| `playlists/all.m3u` | Everything |
| `playlists/malaysia.m3u` | Malaysian TV (news, entertainment, religion, education, regional, sport) |
| `playlists/football.m3u` | Malaysian sport + football (local, clubs, global) |
| `playlists/news.m3u` | Malaysian + world news |
| `playlists/radio.m3u` | Malaysian radio |

Raw link pattern (works once the repo is public):

```
https://raw.githubusercontent.com/redfieldchristabel/mas-live-tv/main/playlists/all.m3u
```

In Nuvio Legacy: Live TV settings > add source > M3U > paste the link.

## Layout

```
data/channels.json     source of truth (edit this)
data/categories.json   category names, order, playlist mapping
data/candidates.json   scraper output, reviewed by the agent (not published)
scripts/scrape_tvmalay.py  discover streams on tvmalay.my
scripts/check_streams.py   probe urls, update status
scripts/build.py           generate playlists/*.m3u
.github/workflows/daily.yml  nightly check + build
```

## Local run

```bash
python scripts/scrape_tvmalay.py
python scripts/check_streams.py
python scripts/build.py
```

Stdlib Python 3.10+ only, no dependencies.

## Scope

Only free-to-air, official free, or free ad-supported streams. No
restreams of Astro, sooka or other subscription services. This repo hosts
no video, only links to publicly available streams.
