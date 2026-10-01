param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[0-9]+\.[0-9]+\.[0-9]+$')]
    [string]$Version,

    [switch]$Push
)

$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')

function Invoke-Git {
    param([string[]]$Arguments)

    $output = & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed."
    }
    return $output
}

try {
    if (@(Invoke-Git -Arguments @('status', '--porcelain')).Count -gt 0) {
        throw 'Working tree is not clean. Commit all intended changes before creating a release.'
    }

    $branch = (Invoke-Git -Arguments @('branch', '--show-current') | Select-Object -First 1)
    if (-not $branch) {
        throw 'Release from a named branch, not a detached HEAD.'
    }

    $tag = "v$Version"
    $existingTag = Invoke-Git -Arguments @('tag', '--list', $tag)
    if ($existingTag) {
        throw "Tag $tag already exists. Choose a new version."
    }

    $releaseTags = @(Invoke-Git -Arguments @('tag', '--list', 'v*', '--sort=-version:refname') |
        Where-Object { $_ -match '^v[0-9]+\.[0-9]+\.[0-9]+$' })
    if ($releaseTags.Count -gt 0) {
        $commitRange = "$($releaseTags[0])..HEAD"
    } else {
        $commitRange = 'HEAD'
    }

    $commitMessages = @(Invoke-Git -Arguments @('log', $commitRange, '--format=- %s (%h)'))
    if ($commitMessages.Count -eq 0) {
        throw 'No commits found since the previous release.'
    }

    $readmePath = Join-Path (Get-Location) 'README.md'
    $changelogPath = Join-Path (Get-Location) 'CHANGELOG.md'

    $readme = [System.IO.File]::ReadAllText($readmePath)
    $changelog = [System.IO.File]::ReadAllText($changelogPath)
    $marker = '(?m)^Latest release:.*$'
    if ([regex]::Matches($readme, $marker).Count -ne 1) {
        throw 'README.md must contain exactly one "Latest release:" line.'
    }

    $versionHeading = [regex]::Match($changelog, '(?m)^## \[[0-9]+\.[0-9]+\.[0-9]+\] - ')
    if (-not $versionHeading.Success) {
        throw 'CHANGELOG.md must contain at least one dated version section.'
    }

    $date = Get-Date -Format 'yyyy-MM-dd'
    $updatedReadme = ([regex]::new($marker)).Replace(
        $readme,
        "Latest release: **$tag** (released $date)",
        1
    )

    $newline = if ($changelog.Contains("`r`n")) { "`r`n" } else { "`n" }
    $entryLines = @(
        "## [$Version] - $date",
        '',
        '### Added',
        '### Changed',
        '### Fixed',
        ''
    ) + $commitMessages + @('')
    $changelogEntry = [string]::Join($newline, [string[]]$entryLines)
    $updatedChangelog = $changelog.Insert($versionHeading.Index, $changelogEntry)

    [System.IO.File]::WriteAllText(
        $readmePath,
        $updatedReadme,
        [System.Text.UTF8Encoding]::new($false)
    )
    [System.IO.File]::WriteAllText(
        $changelogPath,
        $updatedChangelog,
        [System.Text.UTF8Encoding]::new($false)
    )

    Invoke-Git -Arguments @('diff', '--check') | Out-Null
    Invoke-Git -Arguments @('add', '--', 'README.md', 'CHANGELOG.md') | Out-Null
    Invoke-Git -Arguments @('commit', '-m', "Release $tag") | Out-Null
    Invoke-Git -Arguments @('tag', $tag) | Out-Null

    if ($Push) {
        Invoke-Git -Arguments @('push', 'origin', 'HEAD') | Out-Null
        Invoke-Git -Arguments @('push', 'origin', $tag) | Out-Null
        Write-Host "Pushed $tag. GitHub Actions will publish the release."
    } else {
        Write-Host "Created commit and tag $tag. Review them, then push with: git push origin HEAD; git push origin $tag"
    }
} finally {
    Pop-Location
}
