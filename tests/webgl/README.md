# WebGL E2E Tests

## Run with visible browser (recommended)

```bash
CUBE_QUIET_ALL=1 python -m pytest tests/webgl/ -v -n0 --headed
```

```powershell
$env:CUBE_QUIET_ALL=1; python -m pytest tests/webgl/ -v -n0 --headed
```

## Run headless (CI mode)

```bash
CUBE_QUIET_ALL=1 python -m pytest tests/webgl/ -v -n0
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--headed` | off | Show the browser window |
| `--browser-type` | chromium | chromium, firefox, or webkit |
| `--webgl-timeout` | 60 | Timeout in seconds |

## Setup

```bash
pip install playwright
playwright install chromium
```
