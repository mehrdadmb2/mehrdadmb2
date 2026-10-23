#!/usr/bin/env python3
"""Validate the profile README's local references and all committed SVG assets."""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
HTML_REF = re.compile(r"\b(?:src|href)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
BLOG_START = "<!-- BLOG-POST-LIST:START -->"
BLOG_END = "<!-- BLOG-POST-LIST:END -->"


def main() -> int:
    errors: list[str] = []
    if not README.is_file():
        print("FAIL: README.md is missing")
        return 1

    readme = README.read_text(encoding="utf-8")
    if readme.count(BLOG_START) != 1 or readme.count(BLOG_END) != 1:
        errors.append("README must contain exactly one start and end marker for the activity feed.")
    elif readme.index(BLOG_START) >= readme.index(BLOG_END):
        errors.append("Activity-feed markers are out of order.")

    for reference in HTML_REF.findall(readme):
        if reference.startswith(("#", "https://", "http://", "mailto:", "tel:", "data:")):
            continue
        local_path = urlsplit(reference).path
        if not local_path:
            continue
        candidate = (ROOT / local_path.lstrip("/")).resolve()
        try:
            candidate.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"Reference escapes repository root: {reference}")
            continue
        if not candidate.is_file():
            errors.append(f"Missing local README asset: {reference}")

    svg_files = sorted(path for path in ROOT.rglob("*.svg") if not any(part.startswith(".") for part in path.relative_to(ROOT).parts))
    for svg_path in svg_files:
        try:
            ET.parse(svg_path)
        except (ET.ParseError, OSError) as exc:
            errors.append(f"Invalid SVG {svg_path.relative_to(ROOT)}: {exc}")

    required = (
        "assets/banner.svg", "assets/status.svg", "assets/stack.svg", "assets/footer.svg",
        "assets/snake.svg", "assets/snake-dark.svg",
    )
    for relative in required:
        if not (ROOT / relative).is_file():
            errors.append(f"Required profile asset is missing: {relative}")

    if errors:
        print("PROFILE HEALTH CHECK FAILED")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"PROFILE HEALTH CHECK PASSED — {len(svg_files)} SVG files parsed; README local assets verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
