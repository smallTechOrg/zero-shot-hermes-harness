# Deploy

Quickest path: **Render** `Web Service` (Docker).

## Render setup
1. New Web Service → connect `rahul123877/data-agent` on `feature/phase3-prod-hardening-20260801-1040-v0.1`.
2. Runtime: `Docker`, Dockerfile: `./Dockerfile`.
3. Health Check Path: `/health`.
4. Env vars:
   - `AGENT_DATABASE_URL=sqlite:///./data/app.db`
   - `AGENT_LLM_PROVIDER=openrouter`
   - `AGENT_LLM_MODEL=tencent/hy3`
   - `AGENT_LOG_LEVEL=INFO`
   - `PORT=8001`
5. Deploy. Public URL appears after build.

## Other options
- `railway.toml` is included for Railway if you prefer that flow.
- Fly.io needs `flyctl` + a generated `fly.toml` (`flyctl launch --no-deploy`).
