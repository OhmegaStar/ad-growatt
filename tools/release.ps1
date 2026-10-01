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

    $changedFiles = @(Invoke-Git -Arguments @('diff', '--name-only', $commitRange))
    $nonReleaseFiles = @($changedFiles | Where-Object {
        $_ -and $_ -notmatch '^(appdaemon/|packages/)' }
    )
    if ($nonReleaseFiles.Count -gt 0) {
        throw "Release scope is limited to appdaemon/ and packages/. Remove or move these files before releasing: $($nonReleaseFiles -join ', ')"
    }

    $distPath = Join-Path (Get-Location) 'dist'
    New-Item -ItemType Directory -Path $distPath -Force | Out-Null
    $archivePath = Join-Path $distPath "ad-growatt-$Version.zip"
    if (Test-Path $archivePath) {
        Remove-Item $archivePath -Force
    }

    Compress-Archive -Path @(
        (Join-Path (Get-Location) 'appdaemon'),
        (Join-Path (Get-Location) 'packages')
    ) -DestinationPath $archivePath -Force

    Write-Host "Prepared release payload: $archivePath"

    Invoke-Git -Arguments @('commit', '--allow-empty', '-m', "Release $tag") | Out-Null
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
