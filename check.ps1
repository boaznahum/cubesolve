pyright src/cube
if ($LASTEXITCODE -ne 0) { Write-Host "pyright failed, aborting"; exit $LASTEXITCODE }

mypy -p cube
if ($LASTEXITCODE -ne 0) { Write-Host "mypy failed, aborting"; exit $LASTEXITCODE }

ruff check src/cube
if ($LASTEXITCODE -ne 0) { Write-Host "ruff failed, aborting"; exit $LASTEXITCODE }
