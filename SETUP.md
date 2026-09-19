# Setup — read this once after uploading

Everything the README references now actually exists in this repo. This file is
the one-time checklist to make it render fully on GitHub.

## 1. Create the METRICS_TOKEN secret

Both `metrics.yml` and `snake.yml` need one classic Personal Access Token.

1. Go to <https://github.com/settings/tokens/new>.
2. Scopes: **`repo`** and **`read:user`**. (Public-only profile → `public_repo` instead of full `repo` also works.)
3. Copy the token.
4. In this repository: `Settings → Secrets and variables → Actions → New repository secret`.
5. Name: `METRICS_TOKEN`. Value: the token. Save.

Nothing else needs a secret — `blog-posts.yml` and the commit step in `snake.yml`
use the automatic `GITHUB_TOKEN` that every workflow already has.

## 2. First run

`Actions` tab → run each of these once manually (▸ *Run workflow*), in order:

1. **Profile Metrics** — takes ~1–2 minutes, writes all 10 `metrics.*.svg` files.
2. **Contribution Snake** — writes `assets/snake.svg` / `assets/snake-dark.svg`.
3. **Blog Posts** — fills in the section between the `BLOG-POST-LIST` markers.

Then open the profile README and confirm every image loads. After this, all
three run on their own schedule (see each workflow's `cron:` line) and again on
every push to `main`.

## 3. What each workflow owns

| File | Generates | Schedule | Token |
|---|---|---|---|
| `.github/workflows/metrics.yml` | `metrics.svg` + 9 more `metrics.*.svg` | daily 03:00 UTC | `METRICS_TOKEN` |
| `.github/workflows/snake.yml` | `assets/snake.svg`, `assets/snake-dark.svg` | daily 04:00 UTC | `METRICS_TOKEN` (read) + `GITHUB_TOKEN` (commit) |
| `.github/workflows/blog-posts.yml` | text between the `BLOG-POST-LIST` markers | daily 05:00 UTC | `GITHUB_TOKEN` |

`metrics.yml` runs each `metrics.*.svg` as its own step with
`if: success() || failure()`, so one plugin failing (rate limit, transient API
error) can't take the other nine images down with it — that's exactly what left
9 of 10 metrics images permanently broken before this setup existed.

## 4. Versioning

- `lowlighter/metrics` is pinned to **`@v3.34`** — an exact version, not
  `@latest`, so a future upstream release can't silently change the images.
  v3.34 also fixes a real bug where the achievements plugin could crash after
  GitHub sunset "Projects (classic)". Upgrade deliberately: change `@v3.34` in
  one commit, then check the rendered SVGs before merging.
- `gautamkrishnar/blog-post-workflow` is pinned to **`@v1`** (floating major
  version, not an exact patch) — its output is just text, so tracking the
  latest 1.x bugfixes automatically is lower-risk than for the Metrics images.

## 5. Timezone

`config_timezone: Asia/Baku` in `metrics.yml` controls how day boundaries are
computed for the habits/activity plugins. Change both occurrences if a
different display timezone is wanted.

## 6. Blog feed

`blog-posts.yml` defaults `feed_list` to this profile's own GitHub Atom feed
(`https://github.com/mehrdadmb2.atom`), so the `~/blog $ tail -n 6 latest.log`
section reads like a real activity log immediately, with no setup. The moment
there's an actual blog, newsletter, or Dev.to/Medium profile, replace that URL
with its RSS/Atom feed — comma-separate multiple feeds if there's more than
one. Keep the `<!-- BLOG-POST-LIST:START -->` / `<!-- BLOG-POST-LIST:END -->`
markers in `README.md` exactly as they are; the workflow writes between them.

## 7. Donation QR codes

QR images live in `assets/qr/` and are generated locally by
`scripts/generate_qr.py` from the addresses hard-coded in that file — no QR
rendering API is called when someone views the README. To regenerate after
changing an address:

```bash
python -m pip install "qrcode[pil]"
python scripts/generate_visual_assets.py
```

Then commit the changed SVGs under `assets/qr/`.

## 8. Contact form

The "Open Contact / Collaboration Form" link in the README points at
`.github/ISSUE_TEMPLATE/contact.yml`, a GitHub Issue Form. `config.yml` in the
same folder disables blank issues and adds quick links (email, Telegram,
LinkedIn) next to the form. Both need to be on the repo's default branch to
take effect — they will be, once this package is uploaded.

## 9. One-time repo cleanup

`scripts/__pycache__/` was previously committed by accident. `.gitignore` now
excludes it, but that only stops *new* commits from adding it back — it won't
remove what's already tracked. Run this once after uploading:

```bash
git rm -r --cached scripts/__pycache__
git commit -m "chore: stop tracking compiled Python cache"
git push
```

## 10. If an image stays blank

Check the failing step's log under the `Actions` tab first. Common causes:

- `METRICS_TOKEN` missing, expired, or missing the `read:user` scope
- repository setting `Settings → Actions → General → Workflow permissions` set
  to "Read repository contents" instead of allowing `contents: write` (the
  workflows already declare `permissions: contents: write`, but an
  organization/repo-level lockdown can still override it)
- a feed in `feed_list` that doesn't actually expose RSS/Atom XML

## Architecture

```text
                       GitHub profile repository
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
      lowlighter/metrics   generate_snake.py   local assets
      (GitHub data → SVG)  (GitHub data → SVG)  (SVG + QR, static)
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                            README.md
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
          analytics         identity           contact
          panels            visuals           Issue Form
```
