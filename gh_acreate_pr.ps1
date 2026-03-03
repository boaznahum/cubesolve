$ErrorActionPreference = "Stop"

$branch = "webgl-dev"
$pollInterval = 5
$maxRetries = 12

try {
    # Get the latest run ID BEFORE the merge
    $beforeId = (gh run list --branch $branch -L 1 --json databaseId |
        ConvertFrom-Json)[0].databaseId

    # Push current branch and create PR with auto-merge
    git push -u origin HEAD
    if ($LASTEXITCODE -ne 0) { throw "Failed to push branch" }

    gh pr create --base $branch --fill
    if ($LASTEXITCODE -ne 0) { throw "Failed to create PR" }

    gh pr merge --auto --merge
    if ($LASTEXITCODE -ne 0) { throw "Failed to set auto-merge" }

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

    Write-Host "Done!" -ForegroundColor Green

} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}