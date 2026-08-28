# Mehrdad profile README v2 — setup

## 1. Replace the profile README

The current repository contains `Readme.md`. GitHub profile repositories should use the conventional `README.md` filename.

1. Keep the new `README.md` from this package.
2. Delete the old `Readme.md` after confirming the new file is present.
3. Do not keep both files with only a casing difference.

## 2. Add the new folders/files

```text
.
├── README.md
├── metrics.svg
├── assets/
│   ├── banner.svg
│   ├── donations.svg
│   ├── footer.svg
│   ├── logo.svg              # keep your existing file
│   ├── snake.svg
│   └── stack.svg
├── profile-3d-contrib/
│   └── profile-night-rainbow.svg
├── scripts/
│   └── generate_profile_assets.py
└── .github/
    ├── ISSUE_TEMPLATE/
    │   └── contact.yml
    └── workflows/
        ├── blog-posts.yml
        └── profile-assets.yml
```

## 3. Remove the old external-renderer workflows

Delete these three files:

```text
.github/workflows/metrics.yml
.github/workflows/profile-3d-contrib.yml
.github/workflows/snake.yml
```

They are replaced by the single repository-local workflow:

```text
.github/workflows/profile-assets.yml
```

This keeps the visible capabilities but moves their generated output into your own repository.

## 4. Workflow permissions

The new profile generator requires only:

```yaml
permissions:
  contents: write
```

GitHub automatically creates a `GITHUB_TOKEN` for workflow jobs; the workflow passes that token to the Python generator. Do not put a personal GitHub token in the repository.

## 5. First run

After pushing the files:

1. Open **Actions**.
2. Open **Generate local profile visuals**.
3. Click **Run workflow**.
4. After it finishes, refresh the profile.

The first run changes the three preview SVGs into live data:

```text
metrics.svg
profile-3d-contrib/profile-night-rainbow.svg
assets/snake.svg
```

## 6. Local testing

The generator uses only the Python standard library.

Windows PowerShell:

```powershell
$env:GITHUB_TOKEN="YOUR_TOKEN"
python .\scripts\generate_profile_assets.py
```

Linux/macOS:

```bash
export GITHUB_TOKEN="YOUR_TOKEN"
python3 scripts/generate_profile_assets.py
```

A local token is optional; it is only needed when you want to run the generator outside GitHub Actions. Never commit that token.

## 7. Contact form

The external Formspree form is replaced with a GitHub Issue Form at:

```text
.github/ISSUE_TEMPLATE/contact.yml
```

This is deliberately public because the profile repository is public. The form explicitly warns users not to send secrets.

## 8. Blog workflow

The existing blog automation is retained so the original feature is not lost. It is updated to `actions/checkout@v7` and writes into the new:

```md
<!-- BLOG-POST-LIST:START -->
<!-- BLOG-POST-LIST:END -->
```

section.

## 9. What remains external

Only features that are impractical to reproduce cleanly from GitHub-native data remain third-party rendered assets:

- GitHub profile trophy image
- Profile view counter
- GitHub Sponsors / Buy Me a Coffee buttons

Everything else visual is stored in this repository as SVG.
