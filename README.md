# Mas Live TV

Curated **free** Malaysian TV, radio and football live channels as M3U
playlists. An AI curator refreshes the list daily (see `AGENTS.md`), and a
GitHub Action re-checks streams and rebuilds playlists every night at
04:00 MYT.

## Two ways to use this repo

tvmalay.my signs its stream URLs with ~30-minute tokens, so the static
playlists below go stale within half an hour. Pick the source that fits:

### Source 1 — Stable (zero setup, recommended starting point)

Channels that never need tokens: Berita RTM, Sukan RTM, FIFA+, FIFA+ FR,
Real Madrid TV, beIN SPORTS XTRA, world news, and more.

```
https://raw.githubusercontent.com/redfieldchristabel/mas-live-tv/main/playlists/stable.m3u
```

### Source 2 — Self-hosted proxy (recommended for the full list)

Run the proxy container (see `proxy/README.md`) and it keeps a headless
Chromium re-capturing fresh tvmalay tokens every 20 minutes:

```bash
curl -O https://raw.githubusercontent.com/redfieldchristabel/mas-live-tv/main/data/channels.json
mkdir -p data && mv channels.json data/
docker compose up -d
# then add in Nuvio:  http://<your-host>:8080/tvmalay.m3u
```

Image: `ghcr.io/redfieldchristabel/mas-live-tv/proxy:latest` (built by GitHub
Actions on every push to `proxy/`).

### Static playlists (convenience — tvmalay entries expire ~30 min after each nightly build)

| File | What's in it |
|---|---|
| `playlists/stable.m3u` | Token-free channels only (always works) |
| `playlists/all.m3u` | Everything |
| `playlists/malaysia.m3u` | Malaysian TV (news, entertainment, religion, education, regional, sport) |
| `playlists/football.m3u` | Malaysian sport + football (local, clubs, global) |
| `playlists/news.m3u` | Malaysian + world news |
| `playlists/radio.m3u` | Malaysian radio |

Raw link pattern:

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
