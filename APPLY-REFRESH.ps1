[CmdletBinding()]
param(
    [string]$RepoPath = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath $RepoPath).Path
$readmePath = Join-Path $repoRoot 'README.md'
if (-not (Test-Path -LiteralPath $readmePath -PathType Leaf)) {
    throw "README.md was not found in '$repoRoot'. Pass -RepoPath pointing to your local clone of mehrdadmb2/mehrdadmb2."
}

# Preflight the current source layout before copying or rewriting any files.
$readmeSource = [System.IO.File]::ReadAllText($readmePath)
$projectAnchorCheck = @'
---

<a id="github-command-center"></a>
'@
$requiredReadmeSnippets = @(
    '<img src="assets/status.svg" alt="System status: online, build mode" width="92%">',
    '## `~/blog $ tail -n 6 latest.log`',
    'The blog section is refreshed automatically by GitHub Actions from the feeds configured in `.github/workflows/blog-posts.yml`.',
    $projectAnchorCheck
)
$missingReadmeSnippets = @($requiredReadmeSnippets | Where-Object { -not $readmeSource.Contains($_) })
if ($missingReadmeSnippets.Count -gt 0) {
    throw "Preflight failed: expected README sections were not found. No files were copied or changed. Missing: $($missingReadmeSnippets -join ' | ')"
}
$setupSourcePath = Join-Path $repoRoot 'SETUP.md'
if (Test-Path -LiteralPath $setupSourcePath -PathType Leaf) {
    $setupSource = [System.IO.File]::ReadAllText($setupSourcePath)
    if (-not $setupSource.Contains('config_timezone: Asia/Baku') -or -not $setupSource.Contains('## Architecture')) {
        throw 'Preflight failed: SETUP.md does not match the expected source layout. No files were copied or changed.'
    }
}
$changeSourcePath = Join-Path $repoRoot 'CHANGELOG.md'
if (Test-Path -LiteralPath $changeSourcePath -PathType Leaf) {
    $changeSource = [System.IO.File]::ReadAllText($changeSourcePath)
    if (-not $changeSource.Contains('# Changelog')) {
        throw 'Preflight failed: CHANGELOG.md does not contain the expected heading. No files were copied or changed.'
    }
}

# Copy the package payload into the target clone. The helper and package notes stay outside it.
$overlayFiles = @(
    '.gitignore',
    '.github/dependabot.yml',
    '.github/workflows/blog-posts.yml',
    '.github/workflows/metrics.yml',
    '.github/workflows/profile-health.yml',
    '.github/workflows/snake.yml',
    'assets/banner.svg',
    'assets/footer.svg',
    'assets/stack.svg',
    'assets/status.svg',
    'scripts/check_profile.py'
)
foreach ($relative in $overlayFiles) {
    $source = Join-Path $PSScriptRoot $relative
    $destination = Join-Path $repoRoot $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Package file missing: $relative"
    }
    $destinationDirectory = Split-Path -Parent $destination
    if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
        New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    }
    Copy-Item -LiteralPath $source -Destination $destination -Force
    Write-Host "Copied $relative" -ForegroundColor DarkCyan
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
function Replace-RequiredText {
    param(
        [Parameter(Mandatory=$true)][string]$RelativePath,
        [Parameter(Mandatory=$true)][string]$OldText,
        [Parameter(Mandatory=$true)][string]$NewText,
        [Parameter(Mandatory=$true)][string]$Description
    )
    $fullPath = Join-Path $repoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) { throw "Required file missing: $RelativePath" }
    $text = [System.IO.File]::ReadAllText($fullPath)
    if (-not $text.Contains($OldText)) { throw "Could not find expected source text for: $Description ($RelativePath). No replacement was made for this item." }
    $text = $text.Replace($OldText, $NewText)
    [System.IO.File]::WriteAllText($fullPath, $text, $utf8NoBom)
    Write-Host "Updated $RelativePath — $Description" -ForegroundColor Cyan
}

$statusOld = @'
<img src="assets/status.svg" alt="System status: online, build mode" width="92%">

</div>
'@
$statusNew = @'
<img src="assets/status.svg" alt="Profile focus: software, IoT, systems and 3D" width="100%">

<p><strong>Computer Engineering · Software | Practical systems, thoughtful automation and visual engineering</strong></p>
<p>
  <a href="https://github.com/mehrdadmb2/mehrdadmb2/actions/workflows/metrics.yml"><img src="https://github.com/mehrdadmb2/mehrdadmb2/actions/workflows/metrics.yml/badge.svg?branch=main" alt="Profile Metrics workflow"></a>
  <a href="https://github.com/mehrdadmb2/mehrdadmb2/actions/workflows/snake.yml"><img src="https://github.com/mehrdadmb2/mehrdadmb2/actions/workflows/snake.yml/badge.svg?branch=main" alt="Contribution Snake workflow"></a>
  <a href="https://github.com/mehrdadmb2/mehrdadmb2/actions/workflows/profile-health.yml"><img src="https://github.com/mehrdadmb2/mehrdadmb2/actions/workflows/profile-health.yml/badge.svg?branch=main" alt="Profile Health Check workflow"></a>
</p>

</div>
'@
Replace-RequiredText -RelativePath 'README.md' -OldText $statusOld -NewText $statusNew -Description 'modern profile intro and workflow health badges'

$activityHeadingOld = '## `~/blog $ tail -n 6 latest.log`'
$activityHeadingNew = '## `~/activity $ tail -n 6 latest.log`'
Replace-RequiredText -RelativePath 'README.md' -OldText $activityHeadingOld -NewText $activityHeadingNew -Description 'rename activity feed accurately'

$activityNoteOld = 'The blog section is refreshed automatically by GitHub Actions from the feeds configured in `.github/workflows/blog-posts.yml`.'
$activityNoteNew = 'This is a live GitHub activity feed, not a personal blog list. GitHub Actions refreshes it from the public Atom feed configured in `.github/workflows/blog-posts.yml`. When a real blog or newsletter is available, add its RSS/Atom feed there.'
Replace-RequiredText -RelativePath 'README.md' -OldText $activityNoteOld -NewText $activityNoteNew -Description 'clarify source of activity feed'

$projectAnchorOld = @'
---

<a id="github-command-center"></a>
'@
$projectSection = @'
### 🧭 More builds & tools

| Project | What it does | Focus |
|---|---|---|
| [**Peugeot 206 Garage**](https://github.com/mehrdadmb2/peugeot-206-garage) | A maintenance logbook for odometer readings, service intervals and car-care history, with a Telegram-first workflow and web dashboard. | Telegram · Cloudflare Workers · GitHub Pages |
| [**DevPulse · Infra Radar**](https://github.com/mehrdadmb2/devpulse-infra-bot) | A lightweight infrastructure-monitoring bot project for surfacing availability and operational signals. | Telegram · Workers · Automation |
| [**Dual Ping Monitor**](https://github.com/mehrdadmb2/dual-ping-monitor) | Network availability monitoring across multiple endpoints with a dashboard-oriented workflow. | Networking · DNS · GitHub Actions |
| [**ArzPulse**](https://github.com/mehrdadmb2/ArzPulse) | A market-monitoring bot project focused on crypto and gold price signals. | Telegram · Market data · Alerts |
| [**Mehrdad Dev**](https://github.com/mehrdadmb2/mehrdad-dev) | Personal developer portfolio and project showcase. | GitHub Pages · UI engineering |

---

<a id="github-command-center"></a>
'@
Replace-RequiredText -RelativePath 'README.md' -OldText $projectAnchorOld -NewText $projectSection -Description 'feature more current projects'

$setupPath = Join-Path $repoRoot 'SETUP.md'
if (Test-Path -LiteralPath $setupPath -PathType Leaf) {
    $setup = [System.IO.File]::ReadAllText($setupPath)
    $setup = $setup.Replace('`config_timezone: Asia/Baku`', '`config_timezone: Asia/Tehran`')
    $setup = $setup.Replace('Change both occurrences if a', 'Change every `config_timezone` occurrence in `.github/workflows/metrics.yml` if a')
    $blogRow = '| `.github/workflows/blog-posts.yml` | text between the `BLOG-POST-LIST` markers | daily 05:00 UTC | `GITHUB_TOKEN` |'
    $healthRow = '| `.github/workflows/profile-health.yml` | validate README-local references and SVG XML | push / pull request / manual | none |'
    if ($setup.Contains($blogRow) -and -not $setup.Contains($healthRow)) { $setup = $setup.Replace($blogRow, $blogRow + "`n" + $healthRow) }
    $setupAddition = @'

## 11. Profile integrity and update policy

- `scripts/check_profile.py` checks README-local image/file references, the activity-feed markers and SVG XML validity.
- `.github/workflows/profile-health.yml` runs that check on relevant pushes and pull requests.
- `.github/dependabot.yml` checks pinned GitHub Actions weekly and can open update PRs when upstream releases change.
- Workflow actions are pinned to verified immutable commit SHAs. The Metrics action remains at upstream `v3.34`, which is the latest release verified for this refresh; Dependabot will help surface future releases.
'@
    if (-not $setup.Contains('## 11. Profile integrity and update policy')) {
        $architectureAnchor = '## Architecture'
        if ($setup.Contains($architectureAnchor)) {
            $setup = $setup.Replace($architectureAnchor, $setupAddition + "`n`n" + $architectureAnchor)
        } else {
            $setup += $setupAddition
        }
    }
    [System.IO.File]::WriteAllText($setupPath, $setup, $utf8NoBom)
    Write-Host 'Updated SETUP.md — integrity check and dependency policy' -ForegroundColor Cyan
}

$changePath = Join-Path $repoRoot 'CHANGELOG.md'
if (Test-Path -LiteralPath $changePath -PathType Leaf) {
    $change = [System.IO.File]::ReadAllText($changePath)
    $entry = @'

## 2026-10-23 — visual refresh and workflow hardening

**Updated**
- Redesigned the profile hero, status strip, technology-stack panel and footer using repository-local SVG assets.
- Added current project highlights, workflow badges and clarified that the automatically populated activity list is a GitHub Atom feed rather than a personal blog.
- Pinned GitHub Actions to verified release commit SHAs, aligned Metrics timezone with Asia/Tehran, and added a delay/retry safeguard for the Lines plugin.
- Added a profile-integrity workflow, a local README/SVG validator, weekly Dependabot checks and a `.gitignore` for generated/local files.
- Removed accidentally tracked Python bytecode caches.
'@
    if (-not $change.Contains('## 2026-10-23 — visual refresh and workflow hardening')) {
        $change = $change.Replace('# Changelog', '# Changelog' + $entry)
        [System.IO.File]::WriteAllText($changePath, $change, $utf8NoBom)
        Write-Host 'Updated CHANGELOG.md' -ForegroundColor Cyan
    }
}

# Remove generated bytecode that was accidentally committed in earlier revisions.
$cacheFiles = @(
    'scripts/__pycache__/generate_qr.cpython-313.pyc',
    'scripts/__pycache__/generate_snake.cpython-313.pyc',
    'scripts/__pycache__/generate_visual_assets.cpython-313.pyc'
)
foreach ($relative in $cacheFiles) {
    $path = Join-Path $repoRoot $relative
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        Remove-Item -LiteralPath $path -Force
        Write-Host "Removed generated cache: $relative" -ForegroundColor DarkYellow
    }
}
$cacheDir = Join-Path $repoRoot 'scripts/__pycache__'
if ((Test-Path -LiteralPath $cacheDir -PathType Container) -and -not (Get-ChildItem -LiteralPath $cacheDir -Force | Select-Object -First 1)) {
    Remove-Item -LiteralPath $cacheDir -Force
}

Write-Host ''
Write-Host 'Profile refresh files copied and text updates applied.' -ForegroundColor Green
Write-Host 'Next: run `python scripts/check_profile.py`, review `git diff`, then commit and push.' -ForegroundColor Green
