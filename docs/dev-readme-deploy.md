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

### First-time Deploy
```bash
# From the project root (where fly.toml and Dockerfile are)

# Create the app on Fly.io
fly launch --no-deploy

# Deploy
fly deploy
```

Fly.io will build the Docker image and deploy it. You'll get a URL like:
```
https://cubesolve.fly.dev
```

### Subsequent Deploys
```bash
# After code changes, just:
fly deploy
```

### Useful Commands
```bash
# Check status
fly status

# View logs
fly logs

# Open in browser
fly open

# SSH into the running machine
fly ssh console

# Stop the app (save free tier hours)
fly scale count 0

# Restart the app
fly scale count 1
```

### Configuration

- `fly.toml` — Fly.io config (region, ports, auto-stop)
- `Dockerfile` — Container build instructions
- The app auto-stops after inactivity and auto-starts on request (~2-5s cold start)
- Region is set to `cdg` (Paris) — change in `fly.toml` if needed

### Costs
- Free tier: 3 shared-cpu-1x VMs with 256MB RAM
- The app uses `shared` CPU with 512MB RAM
- Auto-stop means you only use resources when someone is connected
