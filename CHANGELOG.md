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
