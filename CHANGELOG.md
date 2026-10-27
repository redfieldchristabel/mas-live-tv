## 2026-10-28 (02:00 curator run)

- Refreshed signed CDN tokens for 47 tvmalay channels via headless CDP re-capture.
- Al Jazeera Arabic + HD day 5/7, kept (removal in 2 days if still dead).
- 47 channels ok. Football 8, news 13, radio 13, malaysia 17, stable 6.
## 2026-10-27 (02:00 curator run)

- Refreshed signed CDN tokens for 47 tvmalay channels via headless CDP re-capture.
- **Removed Euronews** — dead 7 consecutive days (since 2026-10-21), per the retention rule.
- Al Jazeera Arabic + HD day 4/7, kept.
- 46 channels ok. Football 7, news 11, radio 13, malaysia 17, stable 6.
## 2026-10-26 (02:00 curator run)

- Refreshed signed CDN tokens for 47 tvmalay channels via headless CDP re-capture.
- **Removed TVS** — dead 7 consecutive days (since 2026-10-20), per the retention rule in AGENTS.md.
- Euronews day 6/7 (removal tomorrow if still dead); Al Jazeera Arabic + HD day 3/7, kept.
- 46 channels ok. Football 7, news 13, radio 13, malaysia 16, stable 6.
## 2026-10-25 (02:00 curator run)

- Refreshed signed CDN tokens for 47 tvmalay channels via headless CDP re-capture.
- TVS day 6/7 (removal likely tomorrow), Euronews day 5/7, Al Jazeera Arabic + HD day 2/7. All kept.
- 47 channels ok. Football 7, news 13, radio 13, malaysia 17, stable 6.
## 2026-10-24 (02:00 curator run)

- Fixed `check_streams.py`: channels whose signed token has expired are now SKIPPED instead of marked dead — last night's GitHub Action ran 5h after the token refresh and wrongly flipped 41 live channels to dead (expired tokens 403 regardless of stream health). All 41 restored.
- Refreshed tokens for 47 tvmalay channels via headless CDP re-capture; all verified ok.
- Al Jazeera Arabic + Arabic HD went dead (day 1 of 7, kept); Euronews day 4/7; TVS day 5/7 — both near removal.
- 47 channels ok. Football 7, news 13, radio 13, malaysia 17, stable 6.
## 2026-10-23 (02:00 curator run)

- Refreshed signed CDN tokens for 47 tvmalay channels via headless CDP re-capture.
- PPA KL Cup went dead (no stream on revisit) — day 1 of 7, kept.
- Euronews still dead (day 3/7), TVS still dead (day 4/7).
- 48 channels ok. Football 7, news 15, radio 13, malaysia 17, stable 6.
## 2026-10-22 (02:00 curator run)

- Refreshed signed CDN tokens for 46 tvmalay channels via headless CDP re-capture.
- Fly FM failed to re-capture (no m3u8 on revisit) — dead day 2 of 7, kept.
- Euronews still dead (day 2/7), TVS still dead (day 3/7). All kept per retention rule.
- 48 channels ok. Football 8, news 15, radio 12, malaysia 17, stable 6.
## 2026-10-21 (proxy release)

- Added self-hosted token proxy (`proxy/`): headless Chromium re-captures tvmalay signed URLs every 20 min, serves /tvmalay.m3u, /stable.m3u, /all.m3u. Published to ghcr.io via .github/workflows/publish-proxy.yml on push to proxy/. docker-compose.yml included.
- build.py now generates playlists/stable.m3u (6 token-free channels) for the no-setup source.
- README rewritten around the two-source model: stable (zero setup) vs self-hosted proxy (full list, recommended).
## 2026-10-21 (02:00 curator run)

- Refreshed signed CDN tokens for 47 tvmalay channels via headless CDP re-capture (30-min expiry policy).
- Euronews stream failed to re-capture (page loads no m3u8 on revisit) — dead day 1 of 7, kept.
- TVS still dead (day 2 of 7), kept.
- 49 channels ok: 27 FHD, 4 HD. Football 8, news 15, radio 13, malaysia 17.
## 2026-10-21 (late)

- Token expiry discovered: tvmalay.my CDN tokens die after ~30 min. Refreshed all 46 via headless CDP re-capture (commit 2a65079).
- FIFA+ swapped to a stable Pluto TV link (jmp2.uk short-url, no short-lived tokens) + FIFA+ French (wurl CDN) added.
- Added Real Madrid TV (official Akamai live) and beIN SPORTS XTRA (Amagi FAST) — both token-free and stable.
- Football playlist now 8 channels. euronews + fly-fm dropped (no stream on revisit); TVS still dead.
## 2026-10-20

- Added 47 channels from tvmalay.my discovery (headless Chromium capture): 17 MY TV, 5 football, 15 world news, 13 radio. All verified ok except TVS (dead, kept 7 days).
- Fixed `build.py` to emit `#EXTVLCOPT:http-origin` — tvmalay.my CDN (b-cdn.net) rejects requests without an Origin header.
- `scrape_tvmalay.py` raw-HTML scan found 0 streams (player is JS-signed); agent used CDP network capture instead. 6 channels have no stream yet: bernama-tv, hot-fm, ikim-fm, kool-fm, minnal-fm, molek-fm.
- Best resolution: 25 channels at FHD 1920x1080, 2 at HD 720p (MPL Malaysia, PPA KL Cup).

# Changelog

## 2026-10-20
- Scaffolding: data model, categories, scraper, checker, builder, daily workflow, AGENTS.md.

## Needs review
- (empty)
