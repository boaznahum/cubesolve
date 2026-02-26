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

### Apps

There are two Fly.io apps deployed from the same branch (`web1`):

| | Stable | Dev |
|---|---|---|
| **App name** | `cubesolve-boaz` | `cubesolve-boaz-dev` |
| **URL** | `cubesolve-boaz.fly.dev` | `cubesolve-boaz-dev.fly.dev` |
| **When to deploy** | Manually, when ready | Anytime (auto on push) |

Both use the same `fly.toml` config. The `--app` flag selects which app to deploy to.

### Creating Apps on Fly.io

Before deploying, you must create the app on Fly.io. Each app name becomes
its URL (`<app-name>.fly.dev`), so pick any name you want:

```bash
# Create an app (run once per app name)
fly apps create <app-name>

# Examples:
fly apps create cubesolve-boaz        # → cubesolve-boaz.fly.dev
fly apps create cubesolve-boaz-dev    # → cubesolve-boaz-dev.fly.dev
fly apps create cubesolve             # → cubesolve.fly.dev
fly apps create my-cube-demo          # → my-cube-demo.fly.dev
```

You can create as many apps as you want. To list your existing apps:
```bash
fly apps list
```

To delete an app you no longer need:
```bash
fly apps destroy <app-name>
```

### First-time Deploy

```bash
# From the project root (where fly.toml and Dockerfile are)

# Deploy to a specific app (must be created first!)
fly deploy --app cubesolve-boaz
fly deploy --app cubesolve-boaz-dev
```

### Deploying After Code Changes

```bash
# Deploy to DEV (for testing)
fly deploy --app cubesolve-boaz-dev

# Deploy to STABLE (when you're happy with dev)
fly deploy --app cubesolve-boaz
```

**Automatic deploys:** Pushing to `web1` on GitHub auto-deploys to the
**dev** app via GitHub Actions (`.github/workflows/fly-deploy.yml`).
Stable is always manual.

### Useful Commands

```bash
# Check status (add --app to target specific app)
fly status --app cubesolve-boaz
fly status --app cubesolve-boaz-dev

# View logs
fly logs --app cubesolve-boaz-dev

# Open in browser
fly open --app cubesolve-boaz

# SSH into the running machine
fly ssh console --app cubesolve-boaz-dev

# Stop an app (save free tier hours)
fly scale count 0 --app cubesolve-boaz

# Restart an app
fly scale count 1 --app cubesolve-boaz
```

### Configuration

- `fly.toml` — Shared config (region, ports, auto-stop). The `--app` flag overrides the app name.
- `Dockerfile` — Container build instructions
- The apps auto-stop after inactivity and auto-start on request (~2-5s cold start)
- Region is set to `waw` (Warsaw)

### Costs
- Free tier: 3 shared-cpu-1x VMs with 256MB RAM
- Each app uses shared CPU with 1024MB RAM
- Auto-stop means you only use resources when someone is connected
- Both apps with auto-stop fit easily in the free tier
