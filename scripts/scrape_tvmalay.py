#!/usr/bin/env python3
"""Discovery helper for tvmalay.my.

Fetches the homepage, collects channel page links, then looks for .m3u8
URLs in each page's HTML/inline JS. Writes candidates to
data/candidates.json for the agent to review. It never edits
channels.json directly: the agent verifies and merges.

Streams loaded by heavy JS may not appear in raw HTML. In that case the
agent should inspect the page's network requests (headless browser) and
record any required Referer/User-Agent headers.
"""
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

BASE = "https://tvmalay.my/"
UA = "Mozilla/5.0 (X11; Linux x86_64) MasLiveTV-discovery/1.0"
OUT = Path(__file__).resolve().parent.parent / "data" / "candidates.json"
M3U8 = re.compile(r"https?://[^\s'\"<>]+?\.m3u8[^\s'\"<>]*")
HREF = re.compile(r'href=["\']([^"\']+)["\']')


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": BASE})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def main() -> None:
    home = get(BASE)
    pages = set()
    for href in HREF.findall(home):
        url = urljoin(BASE, href)
        if urlparse(url).netloc.endswith("tvmalay.my") and url.rstrip("/") != BASE.rstrip("/"):
            pages.add(url.split("#")[0])
    found = []
    for page in sorted(pages):
        try:
            html = get(page)
        except Exception as exc:
            found.append({"page": page, "error": str(exc)})
            continue
        for stream in sorted(set(M3U8.findall(html))):
            found.append({"page": page, "url": stream, "referer": page})
    OUT.write_text(json.dumps(found, indent=2) + "\n")
    print(f"{len(pages)} pages scanned, {sum('url' in f for f in found)} stream candidates")


if __name__ == "__main__":
    main()
