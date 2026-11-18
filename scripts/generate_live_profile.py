#!/usr/bin/env python3
"""Generate the profile's cross-repository SVG snapshot and featured movie shelf.

The profile repository reads only public, already-published JSON from the linked
projects. It never needs their private tokens and never writes to those projects.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import mimetypes
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TEHRAN = ZoneInfo("Asia/Tehran")
MARKET_URL = os.environ.get(
    "ARZPULSE_LATEST_URL",
    "https://raw.githubusercontent.com/mehrdadmb2/ArzPulse/main/docs/data/latest.json",
)
IOT_URL = os.environ.get(
    "PYSMARTHOME_STATUS_URL",
    "https://raw.githubusercontent.com/mehrdadmb2/PySmartHome-PC/main/data/status.json",
)
MOVIES_URL = os.environ.get(
    "IMDB_MOVIES_URL",
    "https://raw.githubusercontent.com/mehrdadmb2/imdb-showcase/main/docs/movies.json",
)
IMDB_RAW_ROOT = "https://raw.githubusercontent.com/mehrdadmb2/imdb-showcase/main/"
DASHBOARD_PATH = ROOT / "assets" / "live-dashboard.svg"
README_PATH = ROOT / "README.md"
MOVIE_START = "<!-- FEATURED-MOVIES:START -->"
MOVIE_END = "<!-- FEATURED-MOVIES:END -->"


def fetch_bytes(url: str, timeout: int = 25, max_bytes: int = 24 * 1024 * 1024) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "mehrdadmb2-profile-refresh/2.0 (+https://github.com/mehrdadmb2/mehrdadmb2)",
            "Accept": "application/json,image/*,*/*;q=0.8",
            "Cache-Control": "no-cache",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"Remote resource exceeds {max_bytes} bytes: {url}")
        return data


def fetch_json(url: str) -> dict[str, Any] | list[Any]:
    raw = fetch_bytes(url, timeout=30)
    parsed = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(parsed, (dict, list)):
        raise ValueError(f"Expected a JSON object or array from {url}")
    return parsed


def safe_json(url: str, label: str) -> dict[str, Any]:
    try:
        value = fetch_json(url)
        return value if isinstance(value, dict) else {"_error": f"{label} returned an array"}
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"WARN: {label} unavailable: {exc}", file=sys.stderr)
        return {"_error": str(exc)}


def parse_timestamp(value: Any) -> dt.datetime | None:
    if not value:
        return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(TEHRAN)
    except (TypeError, ValueError, OverflowError):
        return None


def fmt_number(value: Any, decimals: int = 1) -> str:
    try:
        number = float(value)
        if number != number or number in (float("inf"), float("-inf")):
            return "—"
        return f"{number:,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def fmt_toman(rial_value: Any) -> str:
    try:
        number = float(rial_value)
        if number <= 0 or number != number:
            return "—"
        toman = int(round(number / 10))
        return f"{toman:,}"
    except (TypeError, ValueError, OverflowError):
        return "—"


def age_minutes(timestamp: dt.datetime | None, now: dt.datetime | None = None) -> int | None:
    if not timestamp:
        return None
    now = now or dt.datetime.now(TEHRAN)
    return max(0, int((now - timestamp).total_seconds() // 60))


def age_label(minutes: int | None) -> str:
    if minutes is None:
        return "TIME UNKNOWN"
    if minutes < 1:
        return "JUST UPDATED"
    if minutes < 60:
        return f"{minutes} MIN AGO"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}H {minutes % 60}M AGO"
    return f"{minutes // 1440}D AGO"


def timestamp_label(timestamp: dt.datetime | None) -> str:
    if not timestamp:
        return "SOURCE TIMESTAMP UNAVAILABLE"
    return timestamp.strftime("%d %b %Y  ·  %H:%M:%S TEHRAN").upper()


def svg_text(x: int, y: int, value: Any, *, size: int = 18, fill: str = "#EAF2FC",
             weight: int = 500, family: str = "Inter,Segoe UI,Arial,sans-serif",
             anchor: str = "start", letter: float | None = None) -> str:
    spacing = f' letter-spacing="{letter}"' if letter is not None else ""
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}"{spacing}>'
        f'{html.escape(str(value))}</text>'
    )


def card_status(is_fresh: bool, unavailable: bool = False) -> tuple[str, str]:
    if unavailable:
        return "UNAVAILABLE", "#FF9B67"
    if is_fresh:
        return "FRESH", "#42E4C5"
    return "STALE", "#FFB36B"


def market_snapshot(market: dict[str, Any], now: dt.datetime | None = None) -> dict[str, Any]:
    now = now or dt.datetime.now(TEHRAN)
    prices = market.get("prices") if isinstance(market.get("prices"), dict) else {}
    derived = market.get("derivedStale") if isinstance(market.get("derivedStale"), dict) else {}
    xaut = prices.get("XAUT") if isinstance(prices.get("XAUT"), dict) else {}
    usdt = prices.get("USDT") if isinstance(prices.get("USDT"), dict) else {}
    source_time = (
        parse_timestamp(market.get("lastGoodTimestamp"))
        or parse_timestamp(market.get("timestamp"))
        or parse_timestamp(usdt.get("fetchedAt"))
    )
    minutes = age_minutes(source_time, now)
    time_fresh = minutes is not None and minutes <= 20
    usdt_value = market.get("usdtPrice") or market.get("dollarPrice") or usdt.get("lastPrice")
    gold_missing = not isinstance(market.get("gold18K"), (int, float)) or market.get("gold18K", 0) <= 0
    usdt_missing = not isinstance(usdt_value, (int, float)) or usdt_value <= 0
    gold_stale = bool(derived.get("gold18K", False)) or bool(xaut.get("stale", False)) or bool(usdt.get("stale", False))
    dollar_stale = bool(derived.get("dollar", False)) or bool(usdt.get("stale", False))
    gold_fresh = time_fresh and not gold_stale and not gold_missing
    dollar_fresh = time_fresh and not dollar_stale and not usdt_missing
    return {
        "gold": fmt_toman(market.get("gold18K")),
        "usdt": fmt_toman(usdt_value),
        "gold_fresh": gold_fresh,
        "dollar_fresh": dollar_fresh,
        "gold_missing": gold_missing,
        "usdt_missing": usdt_missing,
        "timestamp": source_time,
        "age": age_label(minutes),
        "source": str(usdt.get("source") or "ArzPulse / Nobitex"),
    }


def sensor_snapshot(status: dict[str, Any], node_key: str, now: dt.datetime | None = None) -> dict[str, Any]:
    now = now or dt.datetime.now(TEHRAN)
    nodes = status.get("nodes") if isinstance(status.get("nodes"), dict) else {}
    node = nodes.get(node_key) if isinstance(nodes.get(node_key), dict) else {}
    last_seen = parse_timestamp(node.get("last_seen"))
    minutes = age_minutes(last_seen, now)
    online_flag = node.get("online") is True
    fresh = online_flag and minutes is not None and minutes <= 15
    if not node:
        state, state_color = "NO DATA", "#FF9B67"
    elif not online_flag:
        state, state_color = "OFFLINE", "#FF7D85"
    elif not fresh:
        state, state_color = "STALE", "#FFB36B"
    else:
        state, state_color = "ONLINE", "#42E4C5"
    name = str(node.get("name") or ("Room 1 · Hub" if node_key == "esp32_1" else "Room 2 · Sensor S3"))
    return {
        "name": name,
        "state": state,
        "state_color": state_color,
        "temperature": fmt_number(node.get("temperature"), 1),
        "humidity": fmt_number(node.get("humidity"), 1),
        "latency": f'{fmt_number(node.get("latency_ms"), 0)} ms' if node.get("latency_ms") is not None else "—",
        "samples": str(node.get("samples", "—")),
        "last_seen": last_seen,
        "age": age_label(minutes),
        "fresh": fresh,
        "missing": not bool(node),
    }


def render_live_dashboard(market: dict[str, Any], telemetry: dict[str, Any], now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now(TEHRAN)
    m = market_snapshot(market, now)
    n1 = sensor_snapshot(telemetry, "esp32_1", now)
    n2 = sensor_snapshot(telemetry, "esp32_s3", now)
    telemetry_time = parse_timestamp(telemetry.get("generated_at")) or parse_timestamp(
        (telemetry.get("server") or {}).get("last_poll") if isinstance(telemetry.get("server"), dict) else None
    )
    if market.get("_error"):
        market_state, market_color = "SOURCE UNAVAILABLE", "#FF9B67"
    elif m["gold_missing"] and m["usdt_missing"]:
        market_state, market_color = "NO MARKET VALUES", "#FFB36B"
    elif m["gold_fresh"] or m["dollar_fresh"]:
        market_state, market_color = "MARKET FEED", "#42E4C5"
    else:
        market_state, market_color = "STALE SNAPSHOT", "#FFB36B"
    generated_label = timestamp_label(telemetry_time)
    market_label = timestamp_label(m["timestamp"])

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 585" role="img" aria-labelledby="title desc">',
        '<title id="title">Mehrdad cross-project live data dashboard</title>',
        '<desc id="desc">Gold and USDT market data from ArzPulse, plus temperature and humidity from two ESP32 nodes published by PySmartHome-PC. Source freshness is shown explicitly.</desc>',
        '<defs>',
        '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#080E1A"/><stop offset=".55" stop-color="#111D31"/><stop offset="1" stop-color="#080F1D"/></linearGradient>',
        '<linearGradient id="edge" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#38E2CC"/><stop offset=".52" stop-color="#858DFF"/><stop offset="1" stop-color="#FFA260"/></linearGradient>',
        '<linearGradient id="panel" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#1C2C43" stop-opacity=".95"/><stop offset="1" stop-color="#0B1424" stop-opacity=".98"/></linearGradient>',
        '<filter id="soft" x="-20%" y="-20%" width="140%" height="150%"><feGaussianBlur in="SourceAlpha" stdDeviation="6"/><feOffset dy="3"/><feComponentTransfer><feFuncA type="linear" slope=".26"/></feComponentTransfer><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '</defs>',
        '<rect width="1500" height="585" rx="28" fill="url(#bg)" stroke="#6D86A6" stroke-opacity=".34"/>',
        '<path d="M1 2H1499" stroke="url(#edge)" stroke-width="3"/>',
        '<g opacity=".20" stroke="#8BA3C1" fill="none"><path d="M18 70H1482M18 556H1482"/><path d="M750 95V535" stroke-dasharray="4 10"/></g>',
        svg_text(38, 43, "CROSS-PROJECT TELEMETRY", size=14, fill="#8DA8C7", weight=800, letter=2.2),
        svg_text(38, 76, "MARKET SNAPSHOT  /  HOME ENVIRONMENT", size=23, fill="#F4F8FF", weight=800, letter=0.6),
        f'<rect x="1190" y="27" width="272" height="38" rx="19" fill="#152A3A" stroke="{market_color}" stroke-opacity=".65"/>',
        f'<circle cx="1215" cy="46" r="5" fill="{market_color}"/>',
        svg_text(1231, 51, market_state, size=13, fill=market_color, weight=800, letter=1.1),
    ]

    # Market cards.
    market_cards = [
        (28, "18K GOLD  /  GRAM", m["gold"], "TOMAN", m["gold_fresh"], m["gold_missing"], "#F5B45F", "SOURCE  ·  XAUT / USDT + USDT / IRR"),
        (760, "USDT  /  IRR RATE", m["usdt"], "TOMAN", m["dollar_fresh"], m["usdt_missing"], "#49DCCB", "SOURCE  ·  NOBITEX USDT / IRR"),
    ]
    for x, label, value, unit, fresh, missing, accent, detail in market_cards:
        state, state_color = card_status(fresh, missing or bool(market.get("_error")))
        parts.extend([
            f'<g filter="url(#soft)"><rect x="{x}" y="101" width="712" height="157" rx="22" fill="url(#panel)" stroke="{accent}" stroke-opacity=".38"/></g>',
            f'<rect x="{x+24}" y="124" width="5" height="36" rx="2.5" fill="{accent}"/>',
            svg_text(x+46, 148, label, size=15, fill="#B7C9DE", weight=800, letter=1.8),
            svg_text(x+24, 205, value, size=38, fill="#F4F8FF", weight=800),
            svg_text(x+24, 232, unit, size=12, fill="#8198B5", weight=800, letter=1.5),
            f'<rect x="{x+551}" y="120" width="135" height="31" rx="15" fill="#142A37" stroke="{state_color}" stroke-opacity=".6"/>',
            f'<circle cx="{x+570}" cy="135" r="4" fill="{state_color}"/>',
            svg_text(x+585, 140, state, size=11, fill=state_color, weight=800, letter=.6),
            svg_text(x+24, 248, detail, size=10, fill="#607C9B", weight=700, letter=1),
        ])

    # Sensor cards.
    sensor_cards = [(28, "NODE 01", n1, "#9998FF"), (760, "NODE 02", n2, "#49DCCB")]
    for x, node_label, node, accent in sensor_cards:
        parts.extend([
            f'<g filter="url(#soft)"><rect x="{x}" y="278" width="712" height="204" rx="22" fill="url(#panel)" stroke="{accent}" stroke-opacity=".36"/></g>',
            f'<rect x="{x+24}" y="301" width="5" height="34" rx="2.5" fill="{accent}"/>',
            svg_text(x+46, 324, node_label + "  /  " + node["name"], size=14, fill="#C5D2E3", weight=800, letter=1),
            f'<rect x="{x+555}" y="297" width="130" height="30" rx="15" fill="#142A37" stroke="{node["state_color"]}" stroke-opacity=".58"/>',
            f'<circle cx="{x+574}" cy="312" r="4" fill="{node["state_color"]}"/>',
            svg_text(x+589, 317, node["state"], size=11, fill=node["state_color"], weight=800, letter=.7),
            svg_text(x+26, 385, node["temperature"], size=39, fill="#F5F8FF", weight=800),
            svg_text(x+153, 385, "°C", size=16, fill="#9BAEC6", weight=700),
            svg_text(x+26, 411, "TEMPERATURE", size=10, fill="#7790AD", weight=800, letter=1.6),
            svg_text(x+252, 385, node["humidity"], size=39, fill="#F5F8FF", weight=800),
            svg_text(x+377, 385, "%", size=16, fill="#9BAEC6", weight=700),
            svg_text(x+252, 411, "HUMIDITY", size=10, fill="#7790AD", weight=800, letter=1.6),
            f'<path d="M{x+472} 350V421" stroke="#66809F" stroke-opacity=".25"/>',
            svg_text(x+496, 369, "LATENCY", size=10, fill="#7790AD", weight=800, letter=1.3),
            svg_text(x+496, 395, node["latency"], size=16, fill="#E6EFF8", weight=800),
            svg_text(x+496, 424, f'SAMPLES  {node["samples"]}', size=10, fill="#7790AD", weight=700),
            svg_text(x+26, 458, "LAST SEEN  ·  " + timestamp_label(node["last_seen"]), size=10, fill="#7089A7", weight=700, letter=.25),
        ])

    # Source timestamps and trust/freshness note.
    parts.extend([
        '<rect x="28" y="500" width="1444" height="58" rx="16" fill="#0C1727" stroke="#6D86A6" stroke-opacity=".23"/>',
        svg_text(48, 523, "MARKET SOURCE", size=10, fill="#7C95B3", weight=800, letter=1.4),
        svg_text(48, 543, market_label, size=12, fill="#DAE6F4", weight=700),
        svg_text(770, 523, "IOT SOURCE  ·  " + generated_label, size=10, fill="#7C95B3", weight=800, letter=.5),
        svg_text(770, 543, "FRESHNESS IS BASED ON SOURCE TIMESTAMPS — NOT THE PROFILE WORKFLOW START TIME", size=10, fill="#8EA5C0", weight=700, letter=.4),
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def write_live_dashboard() -> bool:
    market = safe_json(MARKET_URL, "ArzPulse market feed")
    telemetry = safe_json(IOT_URL, "PySmartHome telemetry")
    content = render_live_dashboard(market, telemetry)
    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    old = DASHBOARD_PATH.read_text(encoding="utf-8") if DASHBOARD_PATH.exists() else ""
    if content == old:
        print("Live dashboard unchanged.")
        return False
    DASHBOARD_PATH.write_text(content, encoding="utf-8", newline="\n")
    print(f"Updated {DASHBOARD_PATH.relative_to(ROOT)}")
    return True


def movie_rating(movie: dict[str, Any]) -> float:
    for key in ("user_rating", "personal_rating"):
        try:
            value = float(str(movie.get(key, "")).replace(",", "").strip())
            if 0 < value <= 10:
                return value
        except (TypeError, ValueError):
            pass
    return 0.0


def movie_candidates(movie: dict[str, Any]) -> list[str]:
    imdb_id = str(movie.get("imdb_id") or "").strip()
    local = str(movie.get("poster_local") or "").strip()
    candidates: list[str] = []
    if local:
        if local.startswith(("https://", "http://")):
            candidates.append(local)
        else:
            path = local.replace("\\", "/").lstrip("./")
            if path.startswith("docs/"):
                candidates.append(IMDB_RAW_ROOT + path)
            elif path.startswith("posters/"):
                candidates.append(IMDB_RAW_ROOT + "docs/" + path)
            elif path:
                candidates.append(IMDB_RAW_ROOT + "docs/posters/" + Path(path).name)
    if imdb_id and re.fullmatch(r"tt\d+", imdb_id):
        candidates.append(IMDB_RAW_ROOT + f"docs/posters/{imdb_id}.webp")
    for field in ("poster_url", "poster", "image_url"):
        value = movie.get(field)
        if isinstance(value, str) and value.startswith(("https://", "http://")) and value.lower() != "n/a":
            candidates.append(value)
    raw_omdb = movie.get("raw_omdb")
    if isinstance(raw_omdb, dict):
        value = raw_omdb.get("Poster")
        if isinstance(value, str) and value.startswith(("https://", "http://")) and value.lower() != "n/a":
            candidates.append(value)
    # Keep order but remove duplicates.
    return list(dict.fromkeys(candidates))


def image_extension(data: bytes, content_type: str | None = None) -> str | None:
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    guess = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
    return guess if guess in (".webp", ".jpg", ".jpeg", ".png", ".gif") else None


def download_movie_poster(movie: dict[str, Any], slot: int) -> Path | None:
    poster_dir = ROOT / "assets" / "posters"
    poster_dir.mkdir(parents=True, exist_ok=True)
    imdb_id = str(movie.get("imdb_id") or "").strip()
    safe_id = imdb_id if re.fullmatch(r"tt\d+", imdb_id) else f"item-{slot}"
    for url in movie_candidates(movie):
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; mehrdadmb2-profile/2.0)"})
            with urlopen(request, timeout=20) as response:
                data = response.read(4 * 1024 * 1024 + 1)
                content_type = response.headers.get("Content-Type", "")
            if len(data) > 4 * 1024 * 1024:
                continue
            extension = image_extension(data, content_type)
            if not extension:
                continue
            target = poster_dir / f"featured-{safe_id}{extension}"
            for old in poster_dir.glob(f"featured-{safe_id}.*"):
                if old != target:
                    old.unlink(missing_ok=True)
            target.write_bytes(data)
            return target
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            print(f"WARN: poster candidate failed ({url}): {exc}", file=sys.stderr)
    # Reuse a last-known-good poster if a temporary upstream failure occurs.
    existing = sorted(p for p in poster_dir.glob(f"featured-{safe_id}.*") if p.is_file())
    return existing[0] if existing else None


def safe_movie_title(movie: dict[str, Any]) -> str:
    value = movie.get("title") or movie.get("original_title") or "Untitled"
    return str(value).strip()[:120] or "Untitled"


def replace_movie_section(movies: list[dict[str, Any]]) -> bool:
    readme = README_PATH.read_text(encoding="utf-8")
    if readme.count(MOVIE_START) != 1 or readme.count(MOVIE_END) != 1:
        raise ValueError("README must contain exactly one FEATURED-MOVIES start and end marker.")
    start = readme.index(MOVIE_START) + len(MOVIE_START)
    end = readme.index(MOVIE_END)
    if start >= end:
        raise ValueError("Featured movie markers are out of order.")

    items: list[tuple[dict[str, Any], Path]] = []
    for movie in movies:
        if not isinstance(movie, dict):
            continue
        poster_path = download_movie_poster(movie, len(items) + 1)
        if poster_path:
            items.append((movie, poster_path))
        if len(items) >= 4:
            break
    if not items:
        print("No poster images could be downloaded; keeping the existing movie shelf.", file=sys.stderr)
        return False

    cells = []
    for movie, poster_path in items:
        title = html.escape(safe_movie_title(movie))
        imdb_id = str(movie.get("imdb_id") or "").strip()
        imdb_url = f"https://www.imdb.com/title/{imdb_id}/" if re.fullmatch(r"tt\d+", imdb_id) else "https://mehrdadmb2.github.io/imdb-showcase/"
        year = str(movie.get("year") or movie.get("release_date") or "").strip()
        match = re.search(r"(?:18|19|20)\d{2}", year)
        year_text = match.group(0) if match else ""
        rating = movie_rating(movie)
        meta = " · ".join(part for part in (year_text, f"Personal ★ {rating:.1f}/10" if rating else "In my collection") if part)
        relative = poster_path.relative_to(ROOT).as_posix()
        cells.append(
            '<td align="center" width="25%">'
            f'<a href="{html.escape(imdb_url, quote=True)}"><img src="{html.escape(relative, quote=True)}" width="126" alt="{title} poster"></a><br>'
            f'<b><a href="{html.escape(imdb_url, quote=True)}">{title}</a></b><br>'
            f'<sub>{html.escape(meta)}</sub></td>'
        )
    table = (
        '\n<div align="center">\n<table>\n<tr>\n'
        + "\n".join(cells)
        + '\n</tr>\n</table>\n'
        + '<sub>Selected from the latest published IMDb Showcase dataset · <a href="https://mehrdadmb2.github.io/imdb-showcase/">Open the full library ↗</a></sub>\n'
        + '</div>\n'
    )
    new_readme = readme[:start] + "\n" + table + readme[end:]
    if new_readme == readme:
        print("Featured movie shelf unchanged.")
        return False
    README_PATH.write_text(new_readme, encoding="utf-8", newline="\n")
    print(f"Updated README movie shelf with {len(items)} poster(s).")
    return True


def write_movie_shelf() -> bool:
    raw = fetch_json(MOVIES_URL)
    if isinstance(raw, dict):
        movies = raw.get("movies")
    else:
        movies = raw
    if not isinstance(movies, list):
        raise ValueError("IMDb Showcase dataset does not contain a 'movies' array.")
    valid = [m for m in movies if isinstance(m, dict) and safe_movie_title(m)]
    # Prefer items carrying a personal rating; if none exist, retain a useful poster preview.
    personal = [m for m in valid if movie_rating(m) > 0]
    selected = personal or valid
    selected.sort(
        key=lambda m: (
            movie_rating(m),
            parse_timestamp(m.get("date_rated")) or dt.datetime.min.replace(tzinfo=TEHRAN),
            float(re.sub(r"[^0-9.]", "", str(m.get("imdb_rating") or "0")) or 0),
        ),
        reverse=True,
    )
    return replace_movie_section(selected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--live-only", action="store_true", help="Refresh only the cross-project SVG dashboard.")
    group.add_argument("--movies-only", action="store_true", help="Refresh only poster previews and the README movie shelf.")
    args = parser.parse_args()

    try:
        if args.live_only:
            write_live_dashboard()
        elif args.movies_only:
            write_movie_shelf()
        else:
            write_live_dashboard()
            write_movie_shelf()
        return 0
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: profile refresh failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
