# Deployment guide

This repo contains a deploy-ready Docker image for the UP Police Data Analyst backend.

## Public hosting options

### Render
1. Sign in at https://render.com and create a new **Web Service**.
2. Connect the `rahul123877/data-agent` repo.
3. Set branch `feature/phase3-prod-hardening-20260801-1040-v0.1`.
4. Set **Runtime** to `Docker` and **Dockerfile Path** to `./Dockerfile`.
5. Add env vars: `AGENT_DATABASE_URL`, `AGENT_LLM_PROVIDER`, `AGENT_LLM_MODEL`, `AGENT_LOG_LEVEL`, `PORT=8001`.
6. Set Health Check Path to `/health`.
7. Deploy. Render provides a public URL after the build succeeds.

### Railway
1. Sign in at https://railway.app and create a new project from GitHub.
2. Connect `rahul123877/data-agent`, branch `feature/phase3-prod-hardening-20260801-1040-v0.1`.
3. Use the included `railway.toml`.
4. Set env vars as above.
5. Railway auto-builds the Docker image and assigns a public domain.

### Fly.io
If `fly` is available:
```bash
cd /path/to/data-agent
flyctl launch --no-deploy
flyctl secrets set AGENT_OPENROUTER_API_KEY="sk-..."
flyctl deploy
```
Generate a `fly.toml` if needed:
```bash
flyctl launch --name data-agent --port 8001 --no-deploy
```

## Frontend
The frontend is served by the FastAPI app at `/app`. After backend deploy:
- Health: `https://<host>/health`
- API docs: `https://<host>/docs`
- Frontend: `https://<host>/app`
- GitHub Pages: `https://rahul123877.github.io/data-agent/` (static)
