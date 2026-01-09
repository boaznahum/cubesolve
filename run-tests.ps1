<#
.SYNOPSIS
    Run tests folder by folder with summary.

.DESCRIPTION
    Iterates over all folders under tests\ and runs pytest with:
    - CUBE_QUIET_ALL=1 environment variable
    - -n auto (parallel execution)
    - -v (verbose)

.PARAMETER IncludePerformance
    Also run tests\performance (skipped by default)

.PARAMETER IncludeGUI
    Also run tests\gui (skipped by default)

.EXAMPLE
    .\run-tests.ps1
    .\run-tests.ps1 -IncludePerformance
    .\run-tests.ps1 -p
    .\run-tests.ps1 -IncludeGUI -IncludePerformance
#>

param(
    [Alias("p")]
    [switch]$IncludePerformance,

    [Alias("g")]
    [switch]$IncludeGUI,

    [Alias("h", "?")]
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host ""
    Write-Host "run-tests.ps1 - Run tests folder by folder with summary" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "    .\run-tests.ps1 [flags]"
    Write-Host ""
    Write-Host "FLAGS:" -ForegroundColor Yellow
    Write-Host "    -p, -IncludePerformance    Include tests\performance (skipped by default)"
    Write-Host "    -g, -IncludeGUI            Include tests\gui (skipped by default)"
    Write-Host "    -h, -Help, -?              Show this help message"
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "    .\run-tests.ps1              Run all tests (except gui, performance)"
    Write-Host "    .\run-tests.ps1 -p           Include performance tests"
    Write-Host "    .\run-tests.ps1 -g           Include GUI tests"
    Write-Host "    .\run-tests.ps1 -p -g        Include both performance and GUI tests"
    Write-Host ""
    Write-Host "ENVIRONMENT:" -ForegroundColor Yellow
    Write-Host "    Sets CUBE_QUIET_ALL=1 to suppress debug output"
    Write-Host "    Uses pytest with: -n auto -v -m 'not slow'"
    Write-Host ""
    exit 0
}

# Set environment variable
$env:CUBE_QUIET_ALL = "1"

# Track results
$results = @{}
$totalPassed = 0
$totalFailed = 0

# Folders to skip by default
$skipFolders = @("__pycache__")
if (-not $IncludePerformance) {
    $skipFolders += "performance"
}
if (-not $IncludeGUI) {
    $skipFolders += "gui"
}

# Get all test folders
$testFolders = Get-ChildItem -Path "tests" -Directory | Where-Object { $_.Name -notin $skipFolders }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Running Tests by Folder" -ForegroundColor Cyan
Write-Host "  Skipping: $($skipFolders -join ', ')" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($folder in $testFolders) {
    $folderPath = "tests/$($folder.Name)"

    Write-Host ""
    Write-Host "----------------------------------------" -ForegroundColor Cyan
    Write-Host "  Testing: $folderPath" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor Cyan

    # Run pytest
    python -m pytest $folderPath -n auto -v -m "not slow"

    if ($LASTEXITCODE -eq 0) {
        $results[$folder.Name] = "PASSED"
        $totalPassed++
        Write-Host "$folderPath PASSED" -ForegroundColor Green
    } else {
        $results[$folder.Name] = "FAILED"
        $totalFailed++
        Write-Host "$folderPath FAILED" -ForegroundColor Red
    }
}

# Print summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

foreach ($folder in $results.Keys | Sort-Object) {
    $status = $results[$folder]
    $color = if ($status -eq "PASSED") { "Green" } else { "Red" }
    Write-Host ("  {0,-20} {1}" -f $folder, $status) -ForegroundColor $color
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host ("  Total: {0} passed, {1} failed" -f $totalPassed, $totalFailed) -ForegroundColor $(if ($totalFailed -eq 0) { "Green" } else { "Red" })
Write-Host "----------------------------------------" -ForegroundColor Cyan

# Exit with error if any failed
if ($totalFailed -gt 0) {
    exit 1
}
