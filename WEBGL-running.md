# WebGL Backend — Running Instructions

## Start the Server

```bash
python -m cube.main_webgl
```

This starts an HTTP + WebSocket server on `http://localhost:8766`. Open that URL manually in your browser.

To auto-open the browser on startup:

```bash
python -m cube.main_webgl --open-browser
```

### Options

```bash
python -m cube.main_webgl --open-browser    # auto-open browser
python -m cube.main_webgl --debug-all       # verbose logging
python -m cube.main_webgl --quiet           # minimal output
python -m cube.main_webgl --cube-size 5     # 5×5 cube
```

### Windows (PowerShell) — UTF-8 fix

```powershell
$env:PYTHONIOENCODING="utf-8"; python -m cube.main_webgl --open-browser
```
