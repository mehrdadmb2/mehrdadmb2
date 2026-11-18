#!/usr/bin/env python3
"""Validate README local references, generated assets and repository SVG files."""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
HTML_REF = re.compile(r"\b(?:src|srcset|href)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
MARKDOWN_REF = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
BLOG_START = "<!-- BLOG-POST-LIST:START -->"
BLOG_END = "<!-- BLOG-POST-LIST:END -->"
MOVIE_START = "<!-- FEATURED-MOVIES:START -->"
MOVIE_END = "<!-- FEATURED-MOVIES:END -->"


def validate_marker_pair(text: str, start: str, end: str, label: str, errors: list[str]) -> None:
    if text.count(start) != 1 or text.count(end) != 1:
        errors.append(f"README must contain exactly one start and end marker for {label}.")
    elif text.index(start) >= text.index(end):
        errors.append(f"README {label} markers are out of order.")


def check_reference(reference: str, errors: list[str]) -> None:
    value = reference.strip().split()[0].strip("<>")
    if not value or value.startswith(("#", "https://", "http://", "mailto:", "tel:", "data:", "//")):
        return
    parsed = urlsplit(value)
    if parsed.scheme or not parsed.path:
        return
    local_path = unquote(parsed.path)
    candidate = (ROOT / local_path.lstrip("/")).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(f"Reference escapes repository root: {reference}")
        return
    if not candidate.is_file():
        errors.append(f"Missing local README asset: {reference}")


def main() -> int:
    errors: list[str] = []
    if not README.is_file():
        print("FAIL: README.md is missing")
        return 1

    readme = README.read_text(encoding="utf-8")
    validate_marker_pair(readme, BLOG_START, BLOG_END, "activity feed", errors)
    validate_marker_pair(readme, MOVIE_START, MOVIE_END, "featured movie shelf", errors)

    references = HTML_REF.findall(readme) + MARKDOWN_REF.findall(readme)
    for reference in references:
        check_reference(reference, errors)

    svg_files = sorted(
        path for path in ROOT.rglob("*.svg")
        if not any(part.startswith(".") for part in path.relative_to(ROOT).parts)
    )
    for svg_path in svg_files:
        try:
            tree = ET.parse(svg_path)
            root = tree.getroot()
            if root.tag.split("}")[-1] != "svg":
                errors.append(f"SVG root element is not <svg>: {svg_path.relative_to(ROOT)}")
        except (ET.ParseError, OSError) as exc:
            errors.append(f"Invalid SVG {svg_path.relative_to(ROOT)}: {exc}")

    required = (
        "assets/banner.svg", "assets/status.svg", "assets/stack.svg", "assets/footer.svg",
        "assets/logo.svg", "assets/live-dashboard.svg", "assets/project-arzpulse.svg",
        "assets/project-smarthome.svg", "assets/project-cinema.svg", "assets/snake.svg",
        "assets/snake-dark.svg", "scripts/generate_live_profile.py",
        ".github/workflows/live-profile-data.yml", ".github/workflows/featured-movies.yml",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            errors.append(f"Required profile file is missing: {relative}")

    if errors:
        print("PROFILE HEALTH CHECK FAILED")
        for error in errors:
            print(f" - {error}")
        return 1

    print(f"PROFILE HEALTH CHECK PASSED — {len(svg_files)} SVG files parsed; {len(references)} README references inspected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
