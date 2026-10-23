# Mehrdad Profile Refresh — package notes

This package overlays a carefully scoped refresh onto an existing local clone of `mehrdadmb2/mehrdadmb2`. It keeps the profile's terminal/engineering identity while modernizing the hero artwork, stack/status graphics and workflow maintenance.

## Included

- New hero/banner, status strip, technology stack panel and footer SVGs.
- Pinned and hardened Metrics, Snake and Activity-feed workflows.
- New Profile Health Check workflow and validator script.
- Weekly Dependabot checks for pinned GitHub Actions.
- `.gitignore` plus a PowerShell helper that copies the payload into your clone, updates README/SETUP/CHANGELOG text and removes previously tracked Python cache files.
- A preview of the new hero is supplied separately with the download links.

## Apply on Windows

1. Download and extract the ZIP anywhere (it does **not** need to be inside your git clone).
2. Open PowerShell in the extracted `mehrdadmb2-profile-refresh` folder.
3. Run the following, replacing the example path with your actual local clone path:

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\APPLY-REFRESH.ps1 -RepoPath "C:\path\to\mehrdadmb2"
   ```

4. Then open a terminal in your repository clone and validate/review the changes:

   ```powershell
   python scripts/check_profile.py
   git status --short
   git diff --check
   git diff -- README.md SETUP.md CHANGELOG.md
   ```

5. If the review looks correct, commit and push:

   ```powershell
   git add -A
   git commit -m "chore: modernize profile visuals and workflows"
   git push origin main
   ```

The helper preflights the expected README/SETUP/CHANGELOG layout before copying or rewriting files and stops if the source layout is different. It never commits or pushes automatically. Review generated workflow changes before pushing.

## Notes

- Existing `METRICS_TOKEN` secret remains required by Metrics and Contribution Snake. No new secret is introduced.
- `lowlighter/metrics` stays on `v3.34`, the latest upstream release verified for this refresh; its action reference is pinned to the corresponding commit SHA.
- The visual assets are repository-local SVGs, so rendering the hero does not depend on an external image host.
- `.github/workflows/profile-health.yml` validates README-local asset references and SVG parsing. YAML and SVG syntax were checked while preparing the package; run the Python profile checker after applying it.
- GitHub writes from this chat connection were rejected with `403 Resource not accessible by integration`; therefore this bundle is prepared for review and application locally, and has not been pushed to `main`.
