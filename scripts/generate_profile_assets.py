#!/usr/bin/env python3
"""Generate local GitHub profile SVGs without third-party rendering services.

Outputs:
  - metrics.svg
  - profile-3d-contrib/profile-night-rainbow.svg
  - assets/snake.svg

Uses only Python's standard library and GitHub's GraphQL API.
For GitHub Actions, the automatically provided GITHUB_TOKEN is used.
For local execution, export GITHUB_TOKEN=<token> before running.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import math
import os
import pathlib
import ssl
import urllib.request
from collections import defaultdict

OWNER = "mehrdadmb2"
ROOT = pathlib.Path(__file__).resolve().parents[1]
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
API = "https://api.github.com/graphql"
PURPLE = ["#160b22", "#2a1040", "#4c1d68", "#7a2fa3", "#b44fe8", "#e0aaff"]
BG = "#09070f"
TEXT = "#f5efff"
MUTED = "#bca9ca"

QUERY = r"""
query($login:String!) {
  user(login:$login) {
    login
    name
    followers { totalCount }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false) {
      totalCount
      nodes {
        name
        stargazerCount
        languages(first:10) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""


def gql(query: str, variables: dict) -> dict:
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required. GitHub Actions supplies it automatically.")
    payload = json.dumps({"query": query, "variables": variables}).encode()
    request = urllib.request.Request(
        API,
        data=payload,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "mehrdadmb2-profile-assets",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, context=ssl.create_default_context(), timeout=30) as response:
        data = json.load(response)
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"]))
    return data["data"]["user"]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def level(count: int, max_count: int) -> int:
    if count <= 0 or max_count <= 0:
        return 0
    return min(5, max(1, math.ceil((count / max_count) * 5)))


def calendar_days(user: dict) -> list[dict]:
    days: list[dict] = []
    for week in user["contributionsCollection"]["contributionCalendar"]["weeks"]:
        days.extend(week["contributionDays"])
    return sorted(days, key=lambda item: item["date"])


def streaks(days: list[dict]) -> tuple[int, int]:
    counts = {dt.date.fromisoformat(d["date"]): d["contributionCount"] for d in days}
    best = current_run = 0
    previous_active = None
    for day in sorted(counts):
        if counts[day] > 0 and previous_active is not None and day == previous_active + dt.timedelta(days=1):
            current_run += 1
        elif counts[day] > 0:
            current_run = 1
        else:
            current_run = 0
        best = max(best, current_run)
        previous_active = day if counts[day] > 0 else None

    current = 0
    cursor = min(dt.date.today(), max(counts) if counts else dt.date.today())
    while counts.get(cursor, 0) > 0:
        current += 1
        cursor -= dt.timedelta(days=1)
    return current, best


def svg_doc(width: int, height: int, body: str, title: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
  <title>{esc(title)}</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#09070f"/><stop offset="1" stop-color="#160b22"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#b44fe8"/><stop offset="1" stop-color="#e0aaff"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect width="100%" height="100%" rx="24" fill="url(#bg)"/>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="23" fill="none" stroke="#4b2a58"/>
  {body}
</svg>'''


def make_metrics(user: dict, days: list[dict]) -> str:
    repos = user["repositories"]["totalCount"]
    followers = user["followers"]["totalCount"]
    stars = sum(repo["stargazerCount"] for repo in user["repositories"]["nodes"])
    cc = user["contributionsCollection"]
    contributions = cc["contributionCalendar"]["totalContributions"]
    commits = cc["totalCommitContributions"]
    prs = cc["totalPullRequestContributions"]
    issues = cc["totalIssueContributions"]
    current, best = streaks(days)

    language_sizes: dict[str, int] = defaultdict(int)
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            language_sizes[edge["node"]["name"]] += edge["size"]
    total_lang = sum(language_sizes.values()) or 1
    languages = sorted(language_sizes.items(), key=lambda pair: pair[1], reverse=True)[:6]

    cards = [
        ("REPOSITORIES", repos),
        ("FOLLOWERS", followers),
        ("TOTAL STARS", stars),
        ("CONTRIBUTIONS", contributions),
        ("COMMITS", commits),
        ("PULL REQUESTS", prs),
    ]
    body: list[str] = [
        '<g font-family="Segoe UI,Arial,sans-serif">',
        '<text x="42" y="48" fill="url(#accent)" font-size="25" font-weight="800">MEHRDAD // PROFILE TELEMETRY</text>',
        f'<text x="42" y="73" fill="{MUTED}" font-size="12">Generated locally from GitHub API • updated {dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")}</text>',
    ]
    for i, (label, value) in enumerate(cards):
        x = 42 + (i % 3) * 247
        y = 96 + (i // 3) * 73
        body += [
            f'<rect x="{x}" y="{y}" width="225" height="58" rx="15" fill="#120c19" stroke="#33203d"/>',
            f'<text x="{x+16}" y="{y+22}" fill="{MUTED}" font-size="10" font-weight="700">{label}</text>',
            f'<text x="{x+16}" y="{y+45}" fill="{TEXT}" font-size="22" font-weight="800">{esc(f"{value:,}")}</text>',
        ]
    body += [
        '<text x="783" y="110" fill="#bca9ca" font-size="11" font-weight="700">STREAK ENGINE</text>',
        f'<text x="783" y="140" fill="{TEXT}" font-size="24" font-weight="800">{current}d <tspan fill="{MUTED}" font-size="13">current</tspan></text>',
        f'<text x="783" y="164" fill="#d5b7e8" font-size="13">best: {best}d • issues: {issues}</text>',
        f'<text x="42" y="247" fill="{MUTED}" font-size="12" font-weight="700">CONTRIBUTION MATRIX • LAST 52 WEEKS</text>',
    ]

    weeks = [days[i:i + 7] for i in range(0, len(days), 7)][-52:]
    max_count = max((d["contributionCount"] for d in days), default=1)
    gx, gy, cell, gap = 42, 260, 13, 3
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            xx = gx + wi * (cell + gap)
            yy = gy + di * (cell + gap)
            color = PURPLE[level(day["contributionCount"], max_count)]
            body.append(
                f'<rect x="{xx}" y="{yy}" width="{cell}" height="{cell}" rx="3" fill="{color}">'
                f'<title>{esc(day["date"])} • {day["contributionCount"]} contribution(s)</title></rect>'
            )

    body.append(f'<text x="42" y="383" fill="{MUTED}" font-size="12" font-weight="700">LANGUAGE PROFILE</text>')
    for i, (name, size) in enumerate(languages):
        x = 140 + i * 155
        share = size * 100.0 / total_lang
        bar = max(24, min(140, share * 5.5))
        body += [
            f'<text x="{x}" y="383" fill="{TEXT}" font-size="11" font-weight="700" text-anchor="middle">{esc(name)}</text>',
            f'<rect x="{x-70}" y="394" width="140" height="8" rx="4" fill="#261a2e"/>',
            f'<rect x="{x-70}" y="394" width="{bar:.1f}" height="8" rx="4" fill="url(#accent)"/>',
            f'<text x="{x}" y="421" fill="{MUTED}" font-size="10" text-anchor="middle">{share:.1f}%</text>',
        ]
    body.append('</g>')
    return svg_doc(1000, 445, ''.join(body), 'Mehrdad GitHub profile telemetry')


def make_3d(days: list[dict]) -> str:
    max_count = max((d["contributionCount"] for d in days), default=1)
    selected = days[-364:]
    cells = []
    for idx, day in enumerate(selected):
        week, dow = divmod(idx, 7)
        count = day["contributionCount"]
        height = 8 + level(count, max_count) * 7
        base_x = 44 + week * 18 - dow * 4
        base_y = 335 - week * 1.6 + dow * 8
        top = f'{base_x},{base_y-height} {base_x+12},{base_y-4-height} {base_x+24},{base_y-height} {base_x+12},{base_y+4-height}'
        left = f'{base_x},{base_y-height} {base_x+12},{base_y+4-height} {base_x+12},{base_y+4} {base_x},{base_y}'
        right = f'{base_x+12},{base_y+4-height} {base_x+24},{base_y-height} {base_x+24},{base_y} {base_x+12},{base_y+4}'
        color = PURPLE[level(count, max_count)]
        cells.append(
            f'<polygon points="{top}" fill="{color}" stroke="#351f43" stroke-width="0.5">'
            f'<title>{esc(day["date"])} • {count} contribution(s)</title></polygon>'
            f'<polygon points="{left}" fill="#32173f" opacity="0.92"/>'
            f'<polygon points="{right}" fill="#5b2474" opacity="0.92"/>'
        )
    body = (
        '<g font-family="Segoe UI,Arial,sans-serif">'
        '<text x="40" y="42" fill="url(#accent)" font-size="25" font-weight="800">3D CONTRIBUTION TERRAIN</text>'
        '<text x="40" y="66" fill="#bca9ca" font-size="12">Repository-local isometric contribution field • no external renderer</text>'
        '<g opacity="0.42"><path d="M30 350 H1080 M70 300 H1120 M100 250 H1150" stroke="#37263e"/></g>'
        + ''.join(cells) +
        '<circle cx="1040" cy="70" r="3" fill="#e0aaff" filter="url(#glow)"><animate attributeName="opacity" values=".2;1;.2" dur="2.6s" repeatCount="indefinite"/></circle>'
        '</g>'
    )
    return svg_doc(1180, 430, body, 'Three dimensional contribution graph')


def make_snake(days: list[dict]) -> str:
    selected = days[-364:]
    max_count = max((d["contributionCount"] for d in selected), default=1)
    cols, rows = 52, 7
    x0, y0 = 70, 95
    grid = []
    for idx, day in enumerate(selected):
        week, dow = divmod(idx, rows)
        x, y = x0 + week * 19, y0 + dow * 19
        color = PURPLE[level(day["contributionCount"], max_count)]
        grid.append(
            f'<rect x="{x}" y="{y}" width="14" height="14" rx="3" fill="{color}">'
            f'<title>{esc(day["date"])} • {day["contributionCount"]}</title></rect>'
        )
    points = []
    for week in range(cols):
        rows_iter = range(rows) if week % 2 == 0 else range(rows - 1, -1, -1)
        points.extend((x0 + week * 19 + 7, y0 + row * 19 + 7) for row in rows_iter)
    path = 'M ' + ' L '.join(f'{x},{y}' for x, y in points)
    body = (
        '<g font-family="Segoe UI,Arial,sans-serif">'
        '<text x="42" y="38" fill="url(#accent)" font-size="24" font-weight="800">CONTRIBUTION SNAKE</text>'
        '<text x="42" y="61" fill="#bca9ca" font-size="12">Local SVG animation • generated from the same contribution calendar</text>'
        + ''.join(grid) +
        f'<path id="snake-path" d="{path}" fill="none" stroke="#f3dfff" stroke-opacity=".08" stroke-width="5"/>'
        f'<path d="{path}" fill="none" stroke="url(#accent)" stroke-width="4" stroke-linecap="round" stroke-dasharray="28 120">'
        '<animate attributeName="stroke-dashoffset" from="0" to="-148" dur="3s" repeatCount="indefinite"/></path>'
        '<circle r="6" fill="#ffffff" filter="url(#glow)"><animateMotion dur="14s" repeatCount="indefinite" rotate="auto"><mpath href="#snake-path"/></animateMotion></circle>'
        '</g>'
    )
    return svg_doc(1120, 270, body, 'Animated contribution snake')


def main() -> None:
    user = gql(QUERY, {"login": OWNER})
    days = calendar_days(user)
    outputs = {
        ROOT / 'metrics.svg': make_metrics(user, days),
        ROOT / 'profile-3d-contrib' / 'profile-night-rainbow.svg': make_3d(days),
        ROOT / 'assets' / 'snake.svg': make_snake(days),
    }
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        print(f'generated {path.relative_to(ROOT)} ({len(content):,} bytes)')


if __name__ == '__main__':
    main()
