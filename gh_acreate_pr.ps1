$ErrorActionPreference = "Stop"

$branch = "webgl-dev"
$pollInterval = 5
$maxRetries = 12

try {
    $version = Get-Content src/cube/resources/version.txt
    Write-Host "Deploying version: $version" -ForegroundColor Cyan

    # Get the latest run ID BEFORE the push
    $beforeId = (gh run list --branch $branch -L 1 --json databaseId |
        ConvertFrom-Json)[0].databaseId

    # Push current branch to origin
    git push -u origin HEAD
    if ($LASTEXITCODE -ne 0) { throw "Failed to push branch" }

    # Pull webgl-dev into current branch (no-op if already up to date), then push
    git pull origin $branch --no-edit
    if ($LASTEXITCODE -ne 0) { throw "Failed to pull origin/$branch" }

    git push origin HEAD:$branch
    if ($LASTEXITCODE -ne 0) { throw "Push to $branch failed" }

    Write-Host "Pushed to $branch (fast-forward)" -ForegroundColor Green

    # Poll until a NEW run appears
    Write-Host "Waiting for new run to start..." -ForegroundColor Yellow
    $runId = $null
    for ($i = 0; $i -lt $maxRetries; $i++) {
        Start-Sleep $pollInterval
        $runId = (gh run list --branch $branch -L 1 --json databaseId |
            ConvertFrom-Json)[0].databaseId
        if ($runId -and $runId -ne $beforeId) {
            Write-Host "Found new run: $runId" -ForegroundColor Green
            break
        }
        Write-Host "  Polling... ($($i + 1)/$maxRetries)"
        $runId = $null
    }

    if (-not $runId) {
        throw "Timed out waiting for new run after $($pollInterval * $maxRetries) seconds"
    }

    # Watch the run
    gh run watch $runId --exit-status
    if ($LASTEXITCODE -ne 0) { throw "Run $runId failed" }

    Write-Host "Done! Version $version deployed." -ForegroundColor Green

} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
