#!/usr/bin/env python3
"""Build playlists/*.m3u from data/channels.json + data/categories.json.

Only channels with status "ok" are written. Stdlib only.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "playlists"


def esc(value: str) -> str:
    return str(value or "").replace('"', "'")


def entry(ch: dict) -> str:
    attrs = [
        f'tvg-id="{esc(ch.get("tvg_id"))}"',
        f'tvg-name="{esc(ch["name"])}"',
        f'tvg-logo="{esc(ch.get("logo"))}"',
        f'group-title="{esc(ch["category"])}"',
    ]
    lines = [f'#EXTINF:-1 {" ".join(attrs)},{ch["name"]}']
    headers = ch.get("headers") or {}
    if headers.get("Referer"):
        lines.append(f'#EXTVLCOPT:http-referrer={headers["Referer"]}')
    if headers.get("User-Agent"):
        lines.append(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}')
    lines.append(ch["url"])
    return "\n".join(lines)


def main() -> None:
    cats = json.loads((DATA / "categories.json").read_text())
    chans = json.loads((DATA / "channels.json").read_text())["channels"]
    order = {c: i for i, c in enumerate(cats["order"])}
    unknown = sorted({c["category"] for c in chans} - set(order))
    if unknown:
        raise SystemExit(f"Unknown categories in channels.json: {unknown}")
    live = [c for c in chans if c.get("status") == "ok" and c.get("url")]
    live.sort(key=lambda c: (order[c["category"]], c["name"].lower()))
    OUT.mkdir(exist_ok=True)
    for name, groups in cats["playlists"].items():
        picked = live if groups == "*" else [c for c in live if c["category"] in groups]
        body = "\n".join(["#EXTM3U"] + [entry(c) for c in picked]) + "\n"
        (OUT / name).write_text(body)
        print(f"{name}: {len(picked)} channels")


if __name__ == "__main__":
    main()
