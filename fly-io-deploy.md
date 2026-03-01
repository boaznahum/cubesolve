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
fly apps create cubesolve             # → cubesolve.fly.dev (web backend)
fly apps create cubesolve-dev         # → cubesolve-dev.fly.dev
fly apps create cubesolve-webgl       # → cubesolve-webgl.fly.dev (webgl backend)
```

**Important — scale to 1 machine after first deploy:**

Fly.io defaults to 2 machines for redundancy. This app uses WebSocket
connections which are pinned to a single machine, so multiple machines
cause wrong session counts and lost state on reconnect. After the first
`fly deploy`, scale down once (this persists across future deploys):

```bash
fly scale count 1 --app cubesolve
fly scale count 1 --app cubesolve-dev
fly scale count 1 --app cubesolve-webgl
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
# Web backend (server-side rendering, Dockerfile + fly.toml)
fly deploy --app cubesolve        # deploy to stable
fly deploy --app cubesolve-dev    # deploy to dev

# WebGL backend (client-side rendering, Dockerfile + fly-webgl.toml)
fly deploy --config fly-webgl.toml --app cubesolve-webgl
```

**Note:** `fly deploy` without `--app` uses the `app` name from `fly.toml`.

| Backend | Dockerfile | fly config | Default port | App name |
|---------|-----------|------------|-------------|----------|
| web | `Dockerfile` | `fly.toml` | 8765 | cubesolve |
| webgl | `Dockerfile.webgl` | `fly-webgl.toml` | 8766 | cubesolve-webgl |

**Automatic deploys:** See [GitHub Actions Auto-Deploy](#github-actions-auto-deploy) below.

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

- `fly.toml` — Web backend config (port 8765, `Dockerfile`)
- `fly-webgl.toml` — WebGL backend config (port 8766, `Dockerfile.webgl`)
- `Dockerfile` — Web backend container (runs `cube.main_web`)
- `Dockerfile.webgl` — WebGL backend container (runs `cube.main_webgl`)
- The apps auto-stop after inactivity and auto-start on request (~2-5s cold start)
- Region is set to `cdg` (Paris) — change `primary_region` in the toml files if needed

### Costs
- Free tier: 3 shared-cpu-1x VMs with 256MB RAM
- Auto-stop means you only use resources when someone is connected


## GitHub Actions Auto-Deploy

Configured in `.github/workflows/fly-deploy.yml`.

### Branch → App Mapping

| Branch | App | Secret |
|--------|-----|--------|
| `main` | `cubesolve` (prod) | `FLY_API_TOKEN` |
| `webgl-4` | `cubesolve-dev` | `FLY_API_TOKEN_DEV` |
| `staging` | `cubesolve-staging` | (needs token) |

Push to a branch → GitHub Actions auto-deploys to the corresponding app.

### Monitoring Deploys

```bash
# List recent workflow runs
gh run list --limit 5

# View logs of a failed run
gh run view <RUN_ID> --log-failed

# Re-run a failed deploy
gh run rerun <RUN_ID>

# Watch a running deploy
gh run watch <RUN_ID>
```


## Token Management

### List tokens for an app

```bash
fly tokens list -a cubesolve-dev
fly tokens list -a cubesolve
```

**Important:** Token values are shown only once at creation. You cannot retrieve them later.

### Create a deploy token (per-app, recommended)

```bash
# For dev
fly tokens create deploy -a cubesolve-dev

# For prod
fly tokens create deploy -a cubesolve

# For staging
fly tokens create deploy -a cubesolve-staging
```

Save the output immediately — copy it before doing anything else.

### Create an org-level token (all apps)

```bash
fly tokens create org
```

Works for all apps. Simpler (one token for everything) but less secure.

### Revoke a token

```bash
# Get the TOKEN_ID from the list
fly tokens list -a cubesolve-dev

# Revoke it
fly tokens revoke -a cubesolve-dev <TOKEN_ID>
```


## GitHub Secrets Management

### From CLI (`gh`)

```bash
# List all secrets
gh secret list

# Set a secret (pipe the token value)
echo "FlyV1 fm2_..." | gh secret set FLY_API_TOKEN_DEV

# Set a secret interactively (prompts for value, safer)
gh secret set FLY_API_TOKEN_DEV

# Delete a secret
gh secret delete FLY_API_TOKEN_DEV
```

### From GitHub UI

1. Go to: https://github.com/boaznahum/cubesolve/settings/secrets/actions
2. Click **New repository secret**
3. Enter name (e.g., `FLY_API_TOKEN_DEV`) and paste the token value
4. Click **Add secret**

### Full Setup for a New App

```bash
# 1. Create the app
fly apps create cubesolve-staging

# 2. Scale to 1 machine (WebSocket needs single machine)
# (do this after first deploy)
fly scale count 1 --app cubesolve-staging

# 3. Create a deploy token — SAVE THE OUTPUT!
fly tokens create deploy -a cubesolve-staging

# 4. Add token to GitHub secrets
echo "<paste-token-here>" | gh secret set FLY_API_TOKEN_STAGING

# 5. Update .github/workflows/fly-deploy.yml:
#    - Add branch to trigger list
#    - Add job with the new secret name
#    - Commit and push
```
