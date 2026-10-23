#!/usr/bin/env python3
"""Probe every channel URL and update status/last_checked in channels.json.

ok   = HTTP 2xx and body looks like HLS/stream
dead = error, 4xx/5xx, or not a playlist
For HLS master playlists it also records the highest variant offered
("resolution", e.g. "1920x1080") and derives "quality" (SD/HD/FHD/4K).
Channels with status "todo" or empty url are skipped. Stdlib only.
"""
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "channels.json"
UA = "Mozilla/5.0 (SMART-TV; Linux; Tizen 10.0) MasLiveTV-check/1.0"
RES = re.compile(rb"RESOLUTION=(\d+)x(\d+)")


def quality_for(height: int) -> str:
    if height >= 2160:
        return "4K"
    if height >= 1080:
        return "FHD"
    if height >= 720:
        return "HD"
    return "SD"


def probe(ch: dict) -> tuple[str, str | None]:
    """Return (status, best "WxH" or None)."""
    headers = {"User-Agent": UA, **(ch.get("headers") or {})}
    req = urllib.request.Request(ch["url"], headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read(65536)
            ctype = r.headers.get("Content-Type", "").lower()
    except Exception:
        return "dead", None
    if not (b"#EXTM3U" in body or "mpegurl" in ctype or "video" in ctype):
        return "dead", None
    sizes = [(int(w), int(h)) for w, h in RES.findall(body)]
    if not sizes:
        return "ok", None
    w, h = max(sizes, key=lambda s: s[1])
    return "ok", f"{w}x{h}"


def token_expired(ch: dict) -> bool:
    """True when the url carries a signed token that has already lapsed.
    Expired tokens 403 regardless of stream health — marking the channel
    dead on that alone would be wrong. The curator refreshes tokens daily;
    a stale token just means 'unknown, needs refresh'."""
    m = re.search(r"[?&]expires=(\d+)", ch.get("url") or "")
    if not m:
        return False
    return int(m.group(1)) < datetime.now(timezone.utc).timestamp()


def main() -> None:
    doc = json.loads(PATH.read_text())
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for ch in doc["channels"]:
        if ch.get("status") == "todo" or not ch.get("url"):
            continue
        if token_expired(ch):
            # Stale token: leave the last known status untouched.
            continue
        status, res = probe(ch)
        ch["status"] = status
        ch["last_checked"] = now
        if res:
            ch["resolution"] = res
            ch["quality"] = quality_for(int(res.split("x")[1]))
        print(f'{status:4} {res or "-":>10} {ch["name"]}')
    doc["updated"] = now
    PATH.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
