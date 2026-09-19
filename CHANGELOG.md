# Changelog

## Unreleased — completeness & bug-fix pass

**Fixed**
- Removed leaked AI-tool citation artifacts (`citeturn...search...`, plus
  invisible Private-Use-Area characters) from two paragraphs in `README.md` —
  previously visible as garbled text on the live profile page.
- Added the entire missing `.github/` folder. `SETUP.md` and the old
  `README-MIGRATION.md` both documented workflows and issue templates that were
  never actually uploaded, so 9 of the 10 `metrics.*.svg` images in the README
  were permanently broken links, the blog section could never populate, and the
  "Open Contact Form" link pointed at a template that didn't exist.
- Added `.gitignore` — `scripts/__pycache__/*.pyc` was being committed.

**Added**
- `.github/workflows/metrics.yml` — generates all 10 `metrics.*.svg` files via
  `lowlighter/metrics@v3.34`, one independent step per file.
- `.github/workflows/snake.yml` — runs the repo's own
  `scripts/generate_snake.py` on a schedule so `assets/snake*.svg` actually
  refreshes, instead of being a permanently static file.
- `.github/workflows/blog-posts.yml` — populates the `BLOG-POST-LIST` markers,
  defaulting to this profile's own GitHub activity feed.
- `.github/ISSUE_TEMPLATE/contact.yml` + `config.yml` — the contact form the
  README already linked to.
- `.github/FUNDING.yml` — enables GitHub's native "Sponsor" button using the
  Sponsors/Buy Me a Coffee links already in the README.
- `LICENSE` (MIT).
- Real, linked projects in the "Featured Builds" section
  (`SmartHome-Hybrid-IoT`, `javaz-renewal-calculator`, and related repos)
  alongside the existing utility/portfolio categories.

**Removed**
- `README-MIGRATION.md` — its checklist was for removing pre-existing
  conflicting workflows, but no `.github/` folder existed to conflict with.
  Superseded by this changelog and `SETUP.md`.

See `SETUP.md` for the one-time setup steps (mainly: add the `METRICS_TOKEN`
secret, then run each workflow once manually).
