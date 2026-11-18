# Mehrdad Profile Refresh v2 — package notes

This package rebuilds the profile README and its local visual/data pipeline. It is intended to be applied to the existing `mehrdadmb2/mehrdadmb2` repository; it does not modify the three source projects.

## Included

- A redesigned README with project cards, clearer navigation, cross-project live telemetry and a dynamically selected IMDb poster shelf.
- New local vector artwork: banner, MB2 monogram, status strip, technology panel, three project marks and footer.
- A Python generator that reads public ArzPulse and PySmartHome-PC JSON feeds and refreshes an SVG dashboard.
- A poster collector that selects up to four personally rated movies from IMDb Showcase and downloads their cached local posters.
- Two dedicated GitHub Actions workflows for live data and movie posters.
- Expanded profile health checks and unit tests.
- Updated setup and Persian upload instructions.
- A PowerShell overlay helper that backs up replaced files, validates the result and never commits or pushes automatically.

Existing Metrics, contribution snake, blog feed, issue templates, donation QR files and repository metadata are retained.

## Apply on Windows

1. Download and extract the ZIP to a separate folder.
2. Open PowerShell in the extracted `mehrdadmb2-profile-refresh-v2` folder.
3. Run:

   ```powershell
   .\APPLY-REFRESH.ps1 -RepoPath "C:\path\to\your\mehrdadmb2-clone"
   ```

4. The helper stores backups under `.profile-refresh-backup/<timestamp>/`, copies the new files, and runs the local validator and unit tests when Python is available.
5. Review `git status --short` and `git diff --check`, then commit and push manually.

The helper does not access GitHub credentials, alter the source projects, or publish changes on your behalf.

## Required setup

- Allow GitHub Actions to write repository contents (`contents: write`).
- Keep `METRICS_TOKEN` for the existing Metrics and contribution-snake workflows.
- No additional token or secret is required for the ArzPulse, PySmartHome-PC or IMDb Showcase feeds; all three source repositories are public.

Run `Live Profile Data` and `Featured Movie Posters` manually once after uploading. More detail is in `SETUP.md` and `UPLOAD-GUIDE.fa.md`.

## Refresh behaviour

- Market and IoT snapshot: every 10 minutes (best-effort GitHub Actions schedule).
- Movie poster shelf: every 12 hours.
- Market data older than 20 minutes and sensor readings older than 15 minutes are explicitly labelled stale.
- A missing source never becomes a fabricated live value. The latest known movie shelf is retained if poster retrieval fails.
