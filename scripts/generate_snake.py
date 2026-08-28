#!/usr/bin/env python3
"""Generate local light/dark contribution-snake SVGs from GitHub GraphQL."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
USER = os.environ.get("GITHUB_USER", "mehrdadmb2")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      contributionCalendar{
        totalContributions
        weeks{
          contributionDays{
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_calendar() -> dict:
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN is required")
    payload = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "mehrdadmb2-profile-snake",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.load(response)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def build_svg(calendar: dict, dark: bool) -> str:
    days = []
    for week in calendar["weeks"]:
        days.extend(week["contributionDays"])
    counts = [d["contributionCount"] for d in days]
    maximum = max(counts or [1])

    bg = "#07070D" if dark else "#FFFFFF"
    panel = "#0D0D16" if dark else "#F7F7FA"
    fg = "#F5F3FF" if dark else "#191622"
    muted = "#94A3B8" if dark else "#64748B"
    levels = ["#1B1630", "#33215B", "#5B2AA6", "#8B5CF6", "#67E8F9"] if dark else ["#EDE9FE", "#DDD6FE", "#C4B5FD", "#A78BFA", "#7C3AED"]
    neon = "#C084FC" if dark else "#7C3AED"

    # Layout: 53 columns × 7 rows, compact and responsive within the viewBox.
    cell = 14
    gap = 4
    left = 54
    top = 56
    width = 53 * (cell + gap) + left + 36
    height = 7 * (cell + gap) + top + 58

    rects = []
    idx = 0
    for x in range(53):
        for y in range(7):
            if idx >= len(days):
                break
            count = days[idx]["contributionCount"]
            if count == 0:
                level = 0
            else:
                ratio = count / maximum
                level = min(4, 1 + int(ratio * 3.99))
            px = left + x * (cell + gap)
            py = top + y * (cell + gap)
            rects.append((px, py, levels[level], count))
            idx += 1

    # Snake route: a smooth polyline that follows column centers in a boustrophedon path.
    centers = []
    for x in range(53):
        ys = range(7) if x % 2 == 0 else range(6, -1, -1)
        for y in ys:
            centers.append((left + x * (cell + gap) + cell / 2, top + y * (cell + gap) + cell / 2))
    path = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in centers)

    rect_svg = "".join(
        f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{fill}"/>'
        for x, y, fill, _ in rects
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Mehrdad GitHub contribution snake</title>
  <desc id="desc">A contribution calendar rendered locally from GitHub data with a snake path overlay.</desc>
  <defs>
    <linearGradient id="snake" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#7C3AED"/>
      <stop offset="0.5" stop-color="#C084FC"/>
      <stop offset="1" stop-color="#67E8F9"/>
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="{width}" height="{height}" rx="22" fill="{bg}"/>
  <rect x="1" y="1" width="{width-2}" height="{height-2}" rx="21" fill="{panel}" stroke="#8B5CF6" stroke-opacity=".28"/>
  <text x="28" y="30" fill="{fg}" font-family="JetBrains Mono,Consolas,monospace" font-size="15" font-weight="700">CONTRIBUTION SNAKE // LOCAL</text>
  <text x="28" y="48" fill="{muted}" font-family="JetBrains Mono,Consolas,monospace" font-size="11">Total contributions: {calendar['totalContributions']} · source: GitHub GraphQL</text>
  {rect_svg}
  <path d="{path}" fill="none" stroke="#67E8F9" stroke-opacity=".22" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="{path}" fill="none" stroke="url(#snake)" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow)"/>
  <circle r="6" fill="#F5F3FF" stroke="url(#snake)" stroke-width="4">
    <animateMotion dur="9s" repeatCount="indefinite" rotate="auto" path="{path}"/>
  </circle>
  <text x="28" y="{height-18}" fill="{muted}" font-family="JetBrains Mono,Consolas,monospace" font-size="10">DYNAMIC · REGENERATED BY GITHUB ACTIONS</text>
</svg>'''


def main() -> None:
    calendar = fetch_calendar()
    (OUT / "snake.svg").write_text(build_svg(calendar, dark=False), encoding="utf-8")
    (OUT / "snake-dark.svg").write_text(build_svg(calendar, dark=True), encoding="utf-8")
    print("Generated assets/snake.svg and assets/snake-dark.svg")


if __name__ == "__main__":
    main()
