# Mas Live TV — self-hosted token proxy

Serves **fresh** tvmalay.my playlists. tvmalay.my signs stream URLs with ~30-minute
tokens, so the static playlists in this repo go stale fast. This container keeps a
headless Chromium running, re-captures signed URLs every 20 minutes, and serves
always-fresh playlists on your LAN.

## Quick start

```bash
# 1. get the channel data
curl -O https://raw.githubusercontent.com/redfieldchristabel/mas-live-tv/main/data/channels.json
mkdir -p data && mv channels.json data/

# 2. run
docker compose up -d

# 3. use in Nuvio / VLC
#   Best (tvmalay, fresh tokens):  http://<host>:8080/tvmalay.m3u
#   Stable only (no tokens ever):  http://<host>:8080/stable.m3u
#   Everything:                    http://<host>:8080/all.m3u
```

## How it works

```
┌────────────────────────── container ──────────────────────────┐
│                                                               │
│  proxy.py (port 8080)          refresh_tokens.js              │
│  ┌──────────────────┐          ┌──────────────────┐           │
│  │ serves playlists │◄─reads───│ every 20 min:     │           │
│  │ from channels.json│         │ headless Chromium │           │
│  └──────────────────┘          │ visits each       │           │
│          ▲                     │ tvmalay.my page,  │           │
│          │                     │ captures the .m3u8│           │
└──────────┼─────────────────────┤ the player loads  ├───────────┘
           │                     └────────┬─────────┘
   Nuvio / VLC                      tvmalay.my
   on your LAN                (signed ~30-min tokens)
```

1. `refresh_tokens.js` opens each tvmalay.my channel page in headless Chromium,
   waits for the player to request its `.m3u8`, and captures the signed URL.
2. It writes the fresh URLs back into the mounted `data/channels.json`.
3. `proxy.py` serves playlists generated from that file — so every request you
   make to `/tvmalay.m3u` carries URLs that are at most ~20 minutes old.
4. Channels that don't need tokens (RTM CDN, FIFA+, Real Madrid TV, beIN XTRA)
   are served on `/stable.m3u` untouched.

## Playlists

| Endpoint | Contents | Token freshness |
|---|---|---|
| `/tvmalay.m3u` | tvmalay.my channels (TV1–TV9, 8TV, radio, etc.) | ≤ 20 min old |
| `/stable.m3u` | RTM CDN, FIFA+, clubs, FAST channels | permanent |
| `/all.m3u` | everything | mixed |
| `/health` | JSON status | — |

## Stremio addon (Nuvio, Stremio, any compatible client)

The proxy also speaks the Stremio addon protocol — no M3U import needed:

```
http://<host>:8080/manifest.json
```

Add that URL as an addon in Nuvio (or Stremio). You get one catalog per
category (MY | Berita, MY | Hiburan, Football | Global, Radio | Malaysia, …),
each channel as a tappable item that resolves to a live stream through the
proxy — token refresh and Origin-header injection handled for you.

Endpoints: `/manifest.json`, `/catalog/tv/{catalog}.json`,
`/catalog/tv/{catalog}/search={q}.json`, `/meta/tv/{id}.json`,
`/stream/tv/{id}.json`.

## Configuration (env)

| Var | Default | Meaning |
|---|---|---|
| `PORT` | 8080 | HTTP listen port |
| `REFRESH_SECONDS` | 1200 | seconds between capture cycles (tokens last ~30 min) |
| `PAGE_SECONDS` | 12 | seconds spent on each channel page |
| `CHANNELS_PATH` | /data/channels.json | channel data location |
| `RELAY` | off | tvmalay traffic through the proxy: `off` = direct CDN links + `#EXTVLCOPT:http-origin` (player sends the header, ~0 bandwidth); `playlist` = only `.m3u8` relayed, video direct; `full` = video relayed too |

## Notes

- First playlist request right after `up` may serve URLs from the mounted file
  (possibly stale) until the first capture cycle finishes (~10 min for 48 pages).
  Wait for `/health` to show `last_refresh`, or lower `PAGE_SECONDS`.
- The container needs outbound internet to tvmalay.my.
- `RELAY=off` relies on the player sending `Origin` itself. Nuvio Legacy reads
  `#EXTVLCOPT:http-origin`; if a player ignores it, switch to `playlist`, then `full`.
  Direct links also fail if the CDN binds tokens to the proxy's IP.
- RAM: Chromium idles around 300–500 MB.
