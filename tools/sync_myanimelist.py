#!/usr/bin/env python3
"""Build the public anime dashboard data from the official MyAnimeList API.

Only the public client ID and username are used locally. They are never written
to generated HTML; the output contains watch-list data and a profile link only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "static" / "data" / "anime.json"
LOCAL_ENV = ROOT / ".env.local"
API = "https://api.myanimelist.net/v2/users/{username}/animelist"
MAX_PAGES = 100
MAX_RESPONSE_BYTES = 8 * 1024 * 1024


def validate_api_url(url: str) -> str:
    if not isinstance(url, str) or any(ord(c) < 33 for c in url):
        raise ValueError('Invalid MyAnimeList page URL')
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname != 'api.myanimelist.net'
            or parsed.port not in (None, 443) or parsed.username or parsed.password
            or parsed.fragment or not parsed.path.startswith('/v2/users/')
            or not parsed.path.endswith('/animelist')):
        raise ValueError('MyAnimeList pages must stay on the official HTTPS list API')
    username = urllib.parse.unquote(parsed.path[len('/v2/users/'):-len('/animelist')])
    if not username or '/' in username or '\\' in username or username in ('.', '..'):
        raise ValueError('Invalid MyAnimeList user path')
    return url


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('MyAnimeList API redirects are refused')


def load_local_env() -> None:
    if not LOCAL_ENV.exists(): return
    for raw in LOCAL_ENV.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"'))


def request_json(url: str, client_id: str) -> dict:
    validate_api_url(url)
    request = urllib.request.Request(url, headers={"X-MAL-CLIENT-ID": client_id, "Accept": "application/json", "User-Agent": "Kaz-Website-V5/5.0"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError('MyAnimeList response is too large')
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError('MyAnimeList response must be an object')
            return payload
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        if exc.code in (401, 403):
            raise SystemExit("MyAnimeList rejected the request. Check the client ID and ensure the list is public.") from exc
        raise SystemExit(f"MyAnimeList API returned HTTP {exc.code}: {message[:300]}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach MyAnimeList: {exc.reason}") from exc


def fetch_list(username: str, client_id: str) -> list[dict]:
    params = urllib.parse.urlencode({
        "fields": "list_status,num_episodes,media_type,main_picture,status,mean",
        "limit": 1000,
        "sort": "list_updated_at",
    })
    url = API.format(username=urllib.parse.quote(username, safe="")) + "?" + params
    results: list[dict] = []
    expected_path = urllib.parse.urlsplit(url).path
    visited = set()
    while url:
        validate_api_url(url)
        if urllib.parse.urlsplit(url).path != expected_path or url in visited or len(visited) >= MAX_PAGES:
            raise ValueError('MyAnimeList pagination changed user, repeated a page or exceeded its limit')
        visited.add(url)
        payload = request_json(url, client_id)
        results.extend(payload.get("data", []))
        url = payload.get("paging", {}).get("next", "")
    return results


def transform(entry: dict) -> dict:
    node = entry.get("node", {})
    status = entry.get("list_status", {})
    anime_id = node.get("id")
    pictures = node.get("main_picture") or {}
    return {
        "id": anime_id,
        "title": node.get("title", "Untitled"),
        "url": f"https://myanimelist.net/anime/{anime_id}" if anime_id else "https://myanimelist.net/",
        "image": pictures.get("large") or pictures.get("medium") or "",
        "status": status.get("status", "plan_to_watch"),
        "format": node.get("media_type", "unknown"),
        "episodesWatched": status.get("num_episodes_watched", 0),
        "episodesTotal": node.get("num_episodes", 0),
        "score": status.get("score", 0),
        "updatedAt": status.get("updated_at", ""),
        "seriesStatus": node.get("status", ""),
        "communityScore": node.get("mean", 0),
    }


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Synchronise the anime dashboard from MyAnimeList")
    command.add_argument("--username", help="MyAnimeList username (or MAL_USERNAME)")
    command.add_argument("--client-id", help="Official MyAnimeList API client ID (or MAL_CLIENT_ID)")
    command.add_argument("--output", type=Path, default=OUTPUT)
    return command


def main() -> None:
    load_local_env()
    args = parser().parse_args()
    username = args.username or os.environ.get("MAL_USERNAME", "")
    client_id = args.client_id or os.environ.get("MAL_CLIENT_ID", "")
    if not username and sys.stdin.isatty(): username = input("MyAnimeList username: ").strip()
    if not client_id and sys.stdin.isatty(): client_id = input("MyAnimeList API client ID: ").strip()
    if not username or not client_id:
        raise SystemExit("Set MAL_USERNAME and MAL_CLIENT_ID in .env.local, or pass --username and --client-id.")

    print(f"Synchronising the public anime list for {username}…")
    items = [transform(entry) for entry in fetch_list(username, client_id)]
    payload = {
        "source": "MyAnimeList",
        "username": username,
        "profileUrl": "https://myanimelist.net/profile/" + urllib.parse.quote(username, safe=""),
        "syncedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": items,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(f"Synced {len(items)} anime entries to {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
