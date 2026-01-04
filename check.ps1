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
ruff check src/cube
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
