#!/usr/bin/env python3
"""Mas Live TV token proxy.

Serves two playlists:
  /stable.m3u   — channels that need no tokens (RTM CDN, FIFA+, clubs, FAST).
  /tvmalay.m3u  — tvmalay.my channels with FRESH signed URLs, fetched on demand.

How tvmalay refresh works:
  tvmalay.my signs each stream URL with a ~30-minute token. The proxy keeps a
  headless Chromium open, visits each channel page on a schedule (default every
  20 minutes), captures the .m3u8 request the player makes, and caches the
  signed URL. When a player (Nuvio, VLC) requests the playlist, the proxy
  rewrites the stored URLs with the freshest capture.

The proxy NEVER edits the repo: it reads data/channels.json mounted at runtime.
"""
import json
import re
import subprocess
import urllib
import urllib.request
import http.client
import threading
import time
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlparse

DATA_PATH = Path(os.environ.get("CHANNELS_PATH", "/data/channels.json"))
PORT = int(os.environ.get("PORT", "8080"))
REFRESH_SECONDS = int(os.environ.get("REFRESH_SECONDS", "1200"))  # 20 min
PAGE_SECONDS = int(os.environ.get("PAGE_SECONDS", "12"))
CDP_PORT = int(os.environ.get("CDP_PORT", "9222"))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"

STABLE_SOURCES = re.compile(r"iptv-org|amagi|wurl|pluto", re.I)

# How much traffic goes through this box for tvmalay channels:
#   off      - playlist points straight at the CDN with the Origin header in
#              #EXTVLCOPT; the player fetches everything itself (~0 bandwidth)
#   playlist - HLS playlists go through /s/ (Origin injected), video segments
#              are fetched by the player straight from the CDN (a few KB/min)
#   full     - playlists AND segments go through /s/ (the full stream)
RELAY = os.environ.get("RELAY", "off").strip().lower()
if RELAY not in ("off", "playlist", "full"):
    RELAY = "off"
TVMALAY_ORIGIN = "https://tvmalay.my"

lock = threading.Lock()
captured = {}      # slug -> [m3u8 urls, freshest last]
slug_of = {}       # channel id -> slug
doc = None


def load_channels():
    global doc, slug_of
    doc = json.loads(DATA_PATH.read_text())
    slug_of = {}
    for c in doc["channels"]:
        m = re.search(r"tvmalay\.my/([a-z0-9-]+)", c.get("notes", "") or "")
        if not m:
            # derive from id: strip tld, re-hyphenate known slugs
            base = c["id"].split(".")[0]
            slug_of[c["id"]] = base
        # note: proper slug mapping comes from the slug map file if present
    smap = Path(os.environ.get("SLUG_MAP", "/data/slug_map.json"))
    if smap.exists():
        for cid, slug in json.loads(smap.read_text()).items():
            slug_of[cid] = slug


def cdp_send(ws, method, params=None, mid_box=None):
    import json as j
    mid_box[0] += 1
    ws.send(j.dumps({"id": mid_box[0], "method": method, "params": params or {}}))
    return mid_box[0]


def cdp_wait(ws, mid, timeout=30):
    import json as j
    ws.settimeout(timeout)
    deadline = time.time() + timeout
    buf = b""
    while time.time() < deadline:
        try:
            b1 = ws.recv(1)
            if not b1:
                raise RuntimeError("ws closed")
            buf += b1
            if len(buf) < 2:
                continue
            ln = buf[1] & 0x7F
            hdr = 2
            if ln == 126:
                while len(buf) < 4:
                    buf += ws.recv(4 - len(buf))
                ln = int.from_bytes(buf[2:4], "big")
                hdr = 4
            elif ln == 127:
                while len(buf) < 10:
                    buf += ws.recv(10 - len(buf))
                ln = int.from_bytes(buf[2:10], "big")
                hdr = 10
            while len(buf) < hdr + ln:
                buf += ws.recv(min(65536, hdr + ln - len(buf)))
            frame, buf = buf[hdr:hdr + ln], buf[hdr + ln:]
            msg = j.loads(frame.decode("utf-8", "replace"))
            if msg.get("id") == mid:
                return msg.get("result", {})
            if msg.get("method") == "Network.requestWillBeSent":
                u = msg["params"]["request"]["url"]
                if u.split("?")[0].endswith(".m3u8"):
                    slug = msg["params"].get("_slug")
                    # handled via global cur below
                    pass
        except Exception:
            continue
    return {}


# Simpler: reuse node for CDP (it worked reliably). Shell out to node per refresh cycle.
REFRESH_JS = Path(os.environ.get("REFRESH_JS", "/app/refresh_tokens.js"))


def refresh_cycle():
    """Run one capture pass over all tvmalay channels using the node CDP script."""
    global captured
    try:
        out = subprocess.run(
            ["node", str(REFRESH_JS), "--quiet"],
            capture_output=True, text=True, timeout=REFRESH_SECONDS - 60,
        )
        # refresh_tokens.js writes channels.json directly; we re-read it
        load_channels()
        with lock:
            captured = {c["id"]: c.get("url") for c in doc["channels"] if "tvmalay" in (c.get("source") or "")}
        log(f"refresh cycle done: {sum(1 for c in doc['channels'] if 'tvmalay' in (c.get('source') or '') and c.get('status')=='ok')} tvmalay ok")
    except Exception as e:
        log(f"refresh cycle error: {e}")


def log(msg):
    print(f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}", flush=True)


def esc(v):
    return str(v or "").replace('"', "'")


def relay_url(url):
    import base64
    return "/s/" + base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


def entry(ch, url_override=None):
    url = url_override or ch["url"]
    h = dict(ch.get("headers") or {})
    if "tvmalay" in (ch.get("source") or ""):
        # The tvmalay CDN wants Origin. Nuvio Legacy reads #EXTVLCOPT:http-origin
        # (src/m3u_parse.c), so in "off" mode the player sends it itself and
        # no video passes through here. Other modes route via /s/.
        h.setdefault("Origin", TVMALAY_ORIGIN)
        h.setdefault("Referer", TVMALAY_ORIGIN + "/")
        if RELAY != "off":
            url = relay_url(url)
    attrs = [
        f'tvg-id="{esc(ch.get("tvg_id"))}"',
        f'tvg-name="{esc(ch["name"])}"',
        f'tvg-logo="{esc(ch.get("logo"))}"',
        f'group-title="{esc(ch["category"])}"',
    ]
    lines = [f'#EXTINF:-1 {" ".join(attrs)},{ch["name"]}']
    if h.get("Referer"):
        lines.append(f"#EXTVLCOPT:http-referrer={h['Referer']}")
    if h.get("Origin"):
        lines.append(f"#EXTVLCOPT:http-origin={h['Origin']}")
    if h.get("User-Agent"):
        lines.append(f"#EXTVLCOPT:http-user-agent={h['User-Agent']}")
    lines.append(url)
    return "\n".join(lines)


def build_playlist(tvmalay: bool) -> str:
    with lock:
        chans = list(doc["channels"])
    out = ["#EXTM3U"]
    for c in chans:
        if c.get("status") != "ok" or not c.get("url"):
            continue
        is_tv = "tvmalay" in (c.get("source") or "")
        if tvmalay and is_tv:
            out.append(entry(c))
        elif not tvmalay and not is_tv:
            out.append(entry(c))
    return "\n".join(out) + "\n"


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        # Some playlist checkers probe with HEAD first; answer like a GET
        # would (headers only) instead of the 501 default.
        p = urlparse(self.path).path
        if p in ("/stable.m3u", "/tvmalay.m3u", "/all.m3u"):
            self.send_response(200)
            self.send_header("Content-Type", "audio/x-mpegurl")
            self.end_headers()
        elif p in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        p = urlparse(self.path).path
        if p.startswith("/s/"):
            return self.do_stream(p[3:])
        if p in ("/", "/health"):
            body = json.dumps({
                "service": "mas-live-tv-proxy",
                "playlists": ["/stable.m3u", "/tvmalay.m3u", "/all.m3u"],
                "tvmalay_channels": sum(1 for c in (doc or {}).get("channels", []) if "tvmalay" in (c.get("source") or "") and c.get("status") == "ok"),
                "last_refresh": getattr(refresh_cycle, "last", None),
                "relay": RELAY,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        elif p == "/stable.m3u":
            self._m3u(build_playlist(tvmalay=False))
        elif p == "/tvmalay.m3u":
            self._m3u(build_playlist(tvmalay=True))
        elif p == "/all.m3u":
            with lock:
                chans = list(doc["channels"])
            out = ["#EXTM3U"]
            for c in chans:
                if c.get("status") == "ok" and c.get("url"):
                    out.append(entry(c))
            self._m3u("\n".join(out) + "\n")
        else:
            self.send_response(404)
            self.end_headers()

    def do_stream(self, cid_q):
        """Relay an upstream playlist or segment, injecting the Origin header
        the CDN demands. /s/<b64url-of-upstream-url>"""
        import base64
        cid = cid_q.split("?")[0]
        try:
            upstream = base64.urlsafe_b64decode(cid + "=" * (-len(cid) % 4)).decode()
        except Exception:
            self.send_response(400); self.end_headers(); return
        ch = None
        with lock:
            for c in (doc or {}).get("channels", []):
                if upstream.startswith(c["url"].split("?")[0]) or c.get("url") == upstream:
                    ch = c; break
        hdrs = {"User-Agent": UA}
        if ch and ch.get("headers"):
            hdrs.update(ch["headers"])
        if "Origin" not in hdrs and ("tvmalay" in upstream or "b-cdn.net" in upstream or (ch and "tvmalay" in (ch.get("source") or ""))):
            hdrs["Origin"] = "https://tvmalay.my"
        try:
            req = urllib.request.Request(upstream, headers=hdrs)
            upstream_host = urlparse(upstream).netloc
            # Read the whole body INSIDE the with: once it exits the response
            # is closed and read() returns b"", which cut every playlist and
            # segment to its first 4096 bytes.
            with urllib.request.urlopen(req, timeout=20) as r:
                ctype = r.headers.get("Content-Type", "")
                # The CDN sometimes drops long connections mid-body; read
                # until EOF and serve whatever arrived (players tolerate
                # short segments far better than a hung request).
                chunks = []
                while True:
                    try:
                        chunk = r.read(65536)
                    except Exception:
                        break
                    if not chunk:
                        break
                    chunks.append(chunk)
                body = b"".join(chunks)
            if b"#EXTM3U" in body[:4096] or "mpegurl" in ctype.lower():
                text = body.decode("utf-8", "replace")
                # A master playlist lists other playlists (always relayed so
                # Origin is injected); a media playlist lists segments, keys
                # and init maps, which only go through here in "full" mode.
                # Off-mode players never reach /s/, so treat it like full.
                master = "#EXT-X-STREAM-INF" in text
                relay_children = master or RELAY != "playlist"

                def fix(u):
                    absu = urljoin(upstream, u)
                    return relay_url(absu) if relay_children else absu

                def repl(line):
                    s = line.strip()
                    if not s:
                        return line
                    if s.startswith("#"):
                        # URI="..." in EXT-X-MEDIA / EXT-X-KEY / EXT-X-MAP
                        return re.sub(r'URI="([^"]+)"', lambda m: f'URI="{fix(m.group(1))}"', line)
                    return fix(s)
                text = "\n".join(repl(l) for l in text.splitlines()) + "\n"
                b = text.encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.apple.mpegurl")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)
            else:
                # segment: buffer fully then send with exact length — a
                # Content-Length mismatch kills cloudflare tunnel with EOF
                data = body
                self.send_response(200)
                self.send_header("Content-Type", ctype or "video/mp2t")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            log(f"relay error for {upstream[:80]}: {e}")
            try:
                self.send_response(502)
                self.end_headers()
            except Exception:
                pass

    def _m3u(self, body):
        b = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "audio/x-mpegurl")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, fmt, *args):
        pass


def main():
    load_channels()
    log(f"loaded {len(doc['channels'])} channels from {DATA_PATH}")
    t = threading.Thread(target=lambda: [refresh_cycle(), time.sleep(REFRESH_SECONDS)], daemon=True)
    # proper loop
    def loop():
        while True:
            refresh_cycle()
            refresh_cycle.last = datetime.now(timezone.utc).isoformat(timespec="seconds")
            time.sleep(REFRESH_SECONDS)
    threading.Thread(target=loop, daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    log(f"listening on :{PORT}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
