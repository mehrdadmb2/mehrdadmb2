# Setup — profile refresh v2

The README is generated from local SVG assets and public JSON feeds. The live-data workflows do not require a server, a Cloudflare Worker, a GitHub PAT, or secrets from the source projects.

## 1. GitHub Actions permissions

Open **Settings → Actions → General → Workflow permissions** and allow workflows to read and write repository contents. The repository-level setting must not block the `contents: write` permissions declared by the two refresh workflows.

The live-data and movie-poster workflows use the repository's automatic `GITHUB_TOKEN`. They only write to this profile repository:

- `Live Profile Data` updates `assets/live-dashboard.svg` every 10 minutes.
- `Featured Movie Posters` refreshes the movie shelf and local poster cache every 12 hours.

Neither workflow writes to ArzPulse, PySmartHome-PC or IMDb Showcase.

## 2. Optional Metrics token

The `lowlighter/metrics` and contribution-snake workflows still use `METRICS_TOKEN`.

1. Create a fine-scoped/classic token that can read public repositories and user profile data (`public_repo` + `read:user` for a public-only profile; use `repo` only when private-repository metrics are genuinely required).
2. Add it under **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the secret exactly `METRICS_TOKEN`.

The live market, IoT and poster workflows do **not** use this token.

## 3. First run

After uploading the refreshed files, open **Actions** and run these workflows manually once:

1. **Live Profile Data** — fetches the published ArzPulse and PySmartHome JSON snapshots and generates the live SVG.
2. **Featured Movie Posters** — downloads up to four locally cached posters from IMDb Showcase and writes the movie shelf into README.
3. **Profile Metrics** — regenerates the Metrics panels (requires `METRICS_TOKEN`).
4. **Contribution Snake** — generates the light/dark contribution snake.
5. **Blog Posts** — refreshes the activity feed between the markers in README.

`Profile Health Check` also runs on relevant pushes and pull requests. It verifies local README references, required assets, SVG syntax and generator tests.

## 4. Data sources and freshness

| Display | Public source | What is shown |
|---|---|---|
| Gold | `ArzPulse/docs/data/latest.json` | 18K price per gram, converted from rial to toman |
| USDT | `ArzPulse/docs/data/latest.json` | Latest USDT/IRR value, converted from rial to toman |
| Room 1 / Hub | `PySmartHome-PC/data/status.json` | Temperature, humidity, online state, latency and sample count |
| Room 2 / Sensor S3 | `PySmartHome-PC/data/status.json` | Temperature, humidity, online state, latency and sample count |
| Movie shelf | `imdb-showcase/docs/movies.json` and `docs/posters/` | Up to four highest personal-rated titles with cached posters |

All source links are public raw repository data. The generator labels market snapshots older than 20 minutes as stale and IoT readings older than 15 minutes as stale. Missing or unreachable feeds are displayed as unavailable; the previous successful movie shelf is kept when poster downloads fail.

GitHub Actions schedules are best-effort and may start late. A 10-minute refresh interval is not a guarantee of real-time delivery. The profile always displays source timestamps, so the viewer can judge the age of the information.

## 5. Local validation

Requirements: Python 3.10+ (the workflows use Python 3.12). No third-party Python packages are needed.

```bash
python scripts/check_profile.py
python -m unittest discover -s tests -v
```

To refresh both data panels and posters manually from a machine with internet access:

```bash
python scripts/generate_live_profile.py
```

Or refresh each part separately:

```bash
python scripts/generate_live_profile.py --live-only
python scripts/generate_live_profile.py --movies-only
```

## 6. Existing automation

| Workflow | Output | Schedule | Secret |
|---|---|---|---|
| `metrics.yml` | `metrics*.svg` analytics panels | Daily | `METRICS_TOKEN` |
| `snake.yml` | `assets/snake.svg`, `assets/snake-dark.svg` | Daily | `METRICS_TOKEN` |
| `blog-posts.yml` | Activity-feed text in README | Daily | `GITHUB_TOKEN` |
| `live-profile-data.yml` | `assets/live-dashboard.svg` | Every 10 minutes | None |
| `featured-movies.yml` | README movie shelf and `assets/posters/` | Every 12 hours | None |
| `profile-health.yml` | Validation only | Push / pull request / manual | None |

The blog workflow depends on these exact README markers; do not delete or rename them:

```html
<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->
```

The featured poster workflow also needs its markers:

```html
<!-- FEATURED-MOVIES:START -->
<!-- FEATURED-MOVIES:END -->
```

## 7. Troubleshooting

- **Live panel says unavailable:** open the two source JSON links from the README. If they are unavailable or malformed, the profile intentionally reports that state instead of fabricating a value.
- **A market value says stale:** inspect `timestamp`, `lastGoodTimestamp`, `derivedStale` and the relevant asset's `stale` flag in ArzPulse.
- **A sensor says stale/offline:** inspect `generated_at`, `last_seen` and `online` in PySmartHome-PC's `data/status.json`.
- **Movie posters do not appear:** run `Featured Movie Posters` manually and inspect its log. The source collection must contain a usable `imdb_id` and poster cache entry/URL.
- **Workflow cannot push:** check that Actions are enabled and repository workflow permissions allow `contents: write`.
- **Metrics images are blank:** check `METRICS_TOKEN`, its scopes and the `Profile Metrics` job logs. This token is unrelated to the live-data panel.
