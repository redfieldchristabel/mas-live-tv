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
