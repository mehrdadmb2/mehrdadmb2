[CmdletBinding()]
param(
    [Parameter()][string]$RepoPath = (Get-Location).Path,
    [Parameter()][switch]$NoBackup
)

$ErrorActionPreference = 'Stop'
$packageRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$targetRoot = (Resolve-Path -LiteralPath $RepoPath).Path
$requiredPackageFiles = @(
    'README.md', 'SETUP.md', 'UPLOAD-GUIDE.fa.md', 'CHANGELOG.md', 'PACK-NOTES.md', 'README-MIGRATION.md', 'APPLY-REFRESH.ps1', '.gitignore',
    '.github/workflows/profile-health.yml',
    '.github/workflows/live-profile-data.yml',
    '.github/workflows/featured-movies.yml',
    'assets/banner.svg', 'assets/footer.svg', 'assets/logo.svg',
    'assets/live-dashboard.svg', 'assets/project-arzpulse.svg',
    'assets/project-smarthome.svg', 'assets/project-cinema.svg', 'assets/posters/.gitkeep',
    'assets/stack.svg', 'assets/status.svg',
    'scripts/check_profile.py', 'scripts/generate_live_profile.py',
    'tests/test_profile_generator.py'
)

foreach ($relative in $requiredPackageFiles) {
    $source = Join-Path $packageRoot $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Package file missing: $relative. No files were copied."
    }
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupRoot = Join-Path $targetRoot (Join-Path '.profile-refresh-backup' $stamp)
$copied = 0

foreach ($relative in $requiredPackageFiles) {
    $source = Join-Path $packageRoot $relative
    $destination = Join-Path $targetRoot $relative
    $destinationDirectory = Split-Path -Parent $destination
    if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
        New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
    }

    if ((Test-Path -LiteralPath $destination -PathType Leaf) -and -not $NoBackup) {
        $backup = Join-Path $backupRoot $relative
        $backupDirectory = Split-Path -Parent $backup
        if (-not (Test-Path -LiteralPath $backupDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
        }
        Copy-Item -LiteralPath $destination -Destination $backup -Force
    }

    if ($relative -eq '.gitignore' -and (Test-Path -LiteralPath $destination -PathType Leaf)) {
        $currentRules = @([System.IO.File]::ReadAllLines($destination))
        $incomingRules = @([System.IO.File]::ReadAllLines($source))
        $missingRules = @($incomingRules | Where-Object { $_.Trim() -and ($currentRules -notcontains $_) })
        if ($missingRules.Count -gt 0) {
            $appendText = [Environment]::NewLine + ($missingRules -join [Environment]::NewLine) + [Environment]::NewLine
            [System.IO.File]::AppendAllText($destination, $appendText, (New-Object System.Text.UTF8Encoding($false)))
        }
    }
    else {
        Copy-Item -LiteralPath $source -Destination $destination -Force
    }
    Write-Host "Updated $relative" -ForegroundColor Cyan
    $copied++
}

Write-Host "`nCopied $copied files into: $targetRoot" -ForegroundColor Green
if (-not $NoBackup) {
    Write-Host "Previous versions (where present) were backed up to: $backupRoot" -ForegroundColor DarkCyan
}

$oldCache = Join-Path $targetRoot 'scripts/__pycache__'
if (Test-Path -LiteralPath $oldCache -PathType Container) {
    Remove-Item -LiteralPath $oldCache -Recurse -Force
    Write-Host 'Removed generated Python bytecode cache.' -ForegroundColor DarkCyan
}

$validator = Join-Path $targetRoot 'scripts/check_profile.py'
if (Get-Command python -ErrorAction SilentlyContinue) {
    Push-Location $targetRoot
    try {
        Write-Host "`nRunning profile validation..." -ForegroundColor Yellow
        & python $validator
        if ($LASTEXITCODE -ne 0) {
            throw 'Profile validation failed. Review the errors before committing.'
        }
        Write-Host "`nRunning unit tests..." -ForegroundColor Yellow
        & python -m unittest discover -s tests -v
        if ($LASTEXITCODE -ne 0) {
            throw 'Profile generator tests failed. Review the errors before committing.'
        }
    }
    finally {
        Pop-Location
    }
}
else {
    Write-Warning 'Python was not found. Run the validation commands from UPLOAD-GUIDE.fa.md before committing.'
}

Write-Host "`nNext: review git diff, then commit and push the refreshed profile files." -ForegroundColor Green
