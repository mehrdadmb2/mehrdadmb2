# Mehrdad profile — setup

This package is designed to replace the current profile README and profile workflows while keeping the major sections and adding a cleaner Metrics-first architecture.

## 1. Files to replace

Use the files from this package as the new source of truth.

```text
README.md
.github/workflows/metrics.yml
.github/workflows/blog-posts.yml
.github/ISSUE_TEMPLATE/contact.yml
.github/ISSUE_TEMPLATE/config.yml
assets/banner.svg
assets/status.svg
assets/footer.svg
assets/stack.svg
assets/snake.svg
assets/snake-dark.svg
assets/qr/*.svg
scripts/generate_qr.py
scripts/generate_visual_assets.py
```

Remove conflicting old workflows that generate the same output files. In particular, do not keep multiple Metrics workflows writing `metrics*.svg` at the same time.

## 2. Metrics token

Create a repository secret named `METRICS_TOKEN`.

The token is used only by the official `lowlighter/metrics` Action and is not written into the repository. The Metrics documentation shows `METRICS_TOKEN` in its GitHub Actions setup examples and uses `contents: write` for workflows that commit rendered SVGs. 

Recommended approach:

1. Create a dedicated GitHub personal access token for this workflow.
2. Give it the minimum scopes required by the plugins you enable.
3. Add it under `Settings → Secrets and variables → Actions → New repository secret`.
4. Name it exactly `METRICS_TOKEN`.

If you do not need private repositories or private contribution data, keep the token scoped as narrowly as practical.

## 3. Why Metrics is split into multiple SVG files

One giant SVG becomes difficult to read and slower to diagnose. The profile therefore keeps a main dashboard plus focused renders:

```text
metrics.svg
metrics.isocalendar.svg
metrics.languages.svg
metrics.achievements.svg
metrics.habits.svg
metrics.notable.svg
metrics.activity.svg
metrics.repositories.svg
metrics.calendar.svg
metrics.lines.svg
```

The Metrics project explicitly supports these plugin families, including isocalendar, languages, achievements, habits, notable contributions, recent activity, repositories and commit calendar. 

## 4. Versioning

The workflow pins the Metrics Action to `v3.34` instead of `latest`. The Metrics project currently lists version 3.34 as its latest release in the public release history. 

This gives you reproducible runs. When you intentionally upgrade, change `@v3.34` in one controlled pull request, then review the generated SVGs.

## 5. Timezone

The profile uses `Asia/Baku` because that is the intended current timezone for this profile setup. Change the `config_timezone` values in `.github/workflows/metrics.yml` if your activity needs a different display timezone.

## 6. Blog workflow

The current feed workflow is retained so that the blog feature is not lost. It uses `gautamkrishnar/blog-post-workflow@1.9.6`, which is the latest Marketplace version currently listed. The README must keep these markers exactly as written:

```html
<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->
```

Edit `feed_list` when your real feeds differ.

## 7. Donation QR codes

QR images are stored locally in `assets/qr/` and are generated from the addresses in `scripts/generate_qr.py`.

No QR rendering API is called at README-view time.

To regenerate them locally:

```bash
python -m pip install qrcode[pil]==8.2
python scripts/generate_visual_assets.py
```

QR files are committed to the repository. The QR generator script is provided for maintenance when an address changes; it is not part of the profile-view dependency chain.

## 9. Contact

The contact flow is now GitHub-native through `.github/ISSUE_TEMPLATE/contact.yml`. GitHub issue forms support structured fields such as inputs, dropdowns, text areas and checkboxes. They are stored in the `.github/ISSUE_TEMPLATE` directory and are available from the repository's default branch. 

The form creates a public issue, so private details should be sent through email instead.

## 10. Important migration note

Do not keep both `Readme.md` and `README.md` as competing profile entry points. Make `README.md` the canonical file and remove the old conflicting version if it exists.

Likewise, do not keep the old Metrics / 3D / snake workflows running in parallel with the new workflow.

## 11. First run

After pushing the files:

1. Open the repository `Actions` tab.
2. Run `Profile Metrics` manually.
3. Run `Contribution Snake` once.
4. Run `Latest blog posts` once.
5. Return to the profile README and verify every generated SVG renders.

## 12. If an output is blank

Check the corresponding workflow run. The most common causes are:

- missing or insufficient `METRICS_TOKEN` permissions;
- a Metrics plugin requiring an additional scope;
- an invalid plugin option after a version upgrade;
- a feed URL that does not expose RSS/Atom content;
- repository Actions permissions not allowing `contents: write`.

## 13. Architecture

```text
                         GitHub profile repository
                                  │
                ┌─────────────────┴─────────────────┐
                │                                   │
        lowlighter/metrics                    Local assets
                │                                   │
       GitHub data → SVGs                    SVG + local QR
                │                                   │
                └─────────────────┬─────────────────┘
                                  │
                              README.md
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
             analytics         identity          contact
             panels            visuals          Issue Form
```

The goal is to make the profile visual layer repository-owned while still using the official Metrics engine for the difficult GitHub analytics work.
