<#
.SYNOPSIS
    Run all code quality checks (pyright, mypy, ruff)

.DESCRIPTION
    Runs pyright, mypy, and ruff checks on the codebase.
    Exits with non-zero code if any check fails.

.PARAMETER fix
    Automatically fix ruff issues (passes --fix to ruff)

.EXAMPLE
    .\check.ps1
    Run all checks without fixing

.EXAMPLE
    .\check.ps1 -fix
    Run all checks and auto-fix ruff issues (NOTE: single dash!)
#>

param(
    [Parameter(HelpMessage="Auto-fix ruff issues (use -fix, not --fix)")]
    [switch]$fix
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Running: PYRIGHT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
pyright src/cube
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "PYRIGHT FAILED" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "PYRIGHT passed" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Running: MYPY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
mypy -p cube
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "MYPY FAILED" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "MYPY passed" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Running: RUFF" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Run ruff with optional --fix flag
if ($fix) {
    Write-Host "  (with --fix enabled)" -ForegroundColor Yellow
    ruff check src/cube --fix
} else {
    ruff check src/cube
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "RUFF FAILED" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "RUFF passed" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ALL CHECKS PASSED" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
