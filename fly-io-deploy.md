# Deploying the Web Backend

## Option 1: ngrok (tunnel from your PC)

Quickest way — your PC runs the server, ngrok makes it publicly accessible.

### Setup
1. Install ngrok: https://ngrok.com (free account required)
2. Authenticate: `ngrok config add-authtoken YOUR_TOKEN`

### Run
```bash
# Terminal 1: Start the web backend
python -m cube.main_web

# Terminal 2: Start ngrok tunnel
ngrok http 8765
```

ngrok gives you a URL like `https://xyz.ngrok-free.dev` — share it with anyone.

### Notes
- Your PC must be running for it to work
- Free tier shows an interstitial page on first visit
- URL changes each time you restart ngrok (paid plan gets fixed subdomain)


## Option 2: Fly.io (cloud deployment)

Always-on deployment with a free tier (3 shared VMs).

### Prerequisites
1. Install flyctl: https://fly.io/docs/flyctl/install/
2. Sign up: `fly auth signup` (requires credit card but free tier exists)
3. Login: `fly auth login`


### Regions

fly platform regions

### Creating Apps on Fly.io

Before deploying, you must create the app on Fly.io. Each app name becomes
its URL (`<app-name>.fly.dev`), so pick any name you want:

```bash
# Create an app (run once per app name)
fly apps create <app-name>

# Examples:
fly apps create cubesolve             # → cubesolve.fly.dev
fly apps create cubesolve-dev         # → cubesolve-dev.fly.dev
```

**Important — scale to 1 machine after first deploy:**

Fly.io defaults to 2 machines for redundancy. This app uses WebSocket
connections which are pinned to a single machine, so multiple machines
cause wrong session counts and lost state on reconnect. After the first
`fly deploy`, scale down once (this persists across future deploys):

```bash
fly scale count 1 --app cubesolve
fly scale count 1 --app cubesolve-dev
```

List your existing apps:
```bash
fly apps list
```

Delete an app you no longer need:
```bash
fly apps destroy <app-name>
```

### Deploying

Use `--app` to choose which app to deploy to:

```bash
fly deploy --app cubesolve        # deploy to stable
fly deploy --app cubesolve-dev    # deploy to dev
```

**Note:** `fly deploy` without `--app` uses the `app` name from `fly.toml`.

**Automatic deploys:** Pushing to `web1` on GitHub auto-deploys to the
**dev** app via GitHub Actions (`.github/workflows/fly-deploy.yml`).

### Useful Commands

All commands use `--app` to target a specific app (see [known bug](#known-bug---app-ignored-when-flytoml-is-present) below):

```bash
# Check status
fly status --app cubesolve-dev

# View logs
fly logs --app cubesolve-dev

# Open in browser
fly open --app cubesolve-dev

# SSH into the running machine
fly ssh console --app cubesolve-dev

# Stop an app (save free tier hours)
fly scale count 0 --app cubesolve

# Restart an app
fly scale count 1 --app cubesolve
```

### Known Bug: `--app` ignored when `fly.toml` is present

Some `fly` commands ignore `--app` when run from a directory containing `fly.toml` —
they use the `app` name from the file instead. If this happens, just `cd` to a
different directory first:

```bash
cd ~ && fly open --app cubesolve-dev && cd -
```

### Configuration

- `fly.toml` — Shared config (region, ports, auto-stop). Use `--app` to target any app.
- `Dockerfile` — Container build instructions
- The apps auto-stop after inactivity and auto-start on request (~2-5s cold start)
- Region is set to `cdg` (Paris) — change `primary_region` in `fly.toml` if needed

### Costs
- Free tier: 3 shared-cpu-1x VMs with 256MB RAM
- Auto-stop means you only use resources when someone is connected
