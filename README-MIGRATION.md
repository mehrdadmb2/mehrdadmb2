# Migration checklist — profile refresh v2

This update replaces the previous profile README and visual assets while preserving the existing Metrics, Snake, Blog Posts and issue-template automation.

## Apply the update

Use the included PowerShell helper from the extracted package folder:

```powershell
.\APPLY-REFRESH.ps1 -RepoPath "C:\path\to\mehrdadmb2"
```

The helper backs up replaced files, copies the v2 payload and runs the Python validator/tests when Python is installed. It never commits or pushes.

## Workflows to keep

Keep one active copy of each workflow below. Replace the existing `profile-health.yml` with the supplied version; add the two new workflows rather than creating duplicate schedules.

```text
.github/workflows/
├── blog-posts.yml
├── featured-movies.yml
├── live-profile-data.yml
├── metrics.yml
├── profile-health.yml
└── snake.yml
```

## Canonical generated assets

```text
assets/
├── banner.svg
├── footer.svg
├── live-dashboard.svg
├── logo.svg
├── project-arzpulse.svg
├── project-cinema.svg
├── project-smarthome.svg
├── stack.svg
├── status.svg
├── snake.svg
├── snake-dark.svg
├── posters/             # Downloaded by Featured Movie Posters
└── qr/                  # Existing local donation QR images
```

`metrics*.svg` files remain at the repository root as before.

## README markers — do not remove

```html
<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->

<!-- FEATURED-MOVIES:START -->
<!-- FEATURED-MOVIES:END -->
```

The blog workflow updates the first pair. The movie workflow rewrites only the content between the second pair.

## Permissions and secrets

- Set GitHub Actions workflow permissions to allow repository contents write.
- Keep `METRICS_TOKEN` for Metrics and contribution snake.
- No token is needed for the public ArzPulse, PySmartHome-PC or IMDb Showcase datasets.

See `SETUP.md` for workflow schedules, freshness rules and troubleshooting.
