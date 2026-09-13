# Deploying FloodLens

FloodLens is two separate deployments:

- **Frontend** (`frontend/`) → Vercel. It's a plain static Vite build — Vercel's native use case.
- **Backend** (`backend/`) → Render (or any host that runs a persistent process). It cannot run on
  Vercel: it needs a long-lived scheduler, writes prediction results to local disk, and its
  refresh endpoint takes ~80s of real Earth Engine work — all incompatible with Vercel's
  serverless functions.

Do the backend first — the frontend needs its URL.

## 0. Prerequisites

- This repo pushed to GitHub (already done).
- A Google Cloud project with Earth Engine enabled (`floodlens-508506`, already set up locally).
- Free accounts on [render.com](https://render.com) and [vercel.com](https://vercel.com), signed
  in with GitHub.

## 1. Create a Earth Engine service account

Your machine authenticates to Earth Engine with a cached personal OAuth credential
(`earthengine authenticate`). A deployed server can't run that interactive flow, so it needs a
**service account** instead — a non-human Google identity with a downloadable JSON key.

1. Go to [console.cloud.google.com](https://console.cloud.google.com/), select the
   `floodlens-508506` project.
2. **IAM & Admin → Service Accounts → Create Service Account.** Name it e.g. `floodlens-backend`.
   No roles are required at this step — Earth Engine access is granted separately.
3. Open the new service account → **Keys → Add Key → Create new key → JSON**. This downloads a
   `.json` file — treat it like a password, never commit it.
4. Go to [code.earthengine.google.com/register](https://code.earthengine.google.com) (or
   [signup.earthengine.google.com](https://signup.earthengine.google.com)) and register that
   service account's email (looks like `floodlens-backend@floodlens-508506.iam.gserviceaccount.com`)
   for Earth Engine access, the same way your own account was registered.
5. Keep the downloaded JSON file handy — its entire content becomes the `GEE_SERVICE_ACCOUNT_JSON`
   environment variable in step 2.

The backend already supports this: `ai/gee_auth.py` uses the service account when
`GEE_SERVICE_ACCOUNT_JSON` is set, and falls back to your local OAuth cache otherwise (so nothing
changes for local development).

## 2. Deploy the backend to Render

1. On Render: **New → Blueprint**, connect your GitHub account, pick the `floodlens` repo. Render
   reads `render.yaml` at the repo root and proposes a `floodlens-backend` web service — accept it.
   (No Blueprint access? **New → Web Service** instead, root directory `backend`, build command
   `pip install -r requirements.txt`, start command
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health check path `/api/health`.)
2. Before the first deploy, set these environment variables on the service (Render prompts for the
   ones marked `sync: false` in `render.yaml`):
   - `EARTH_ENGINE_PROJECT` = `floodlens-508506`
   - `GEE_SERVICE_ACCOUNT_JSON` = paste the **entire contents** of the JSON key file from step 1,
     as one line.
   - `FLOODLENS_CORS_ALLOW_ORIGINS` — leave a placeholder like `["http://localhost:5173"]` for now;
     you'll update it in step 4 once the Vercel URL exists.

   (`OPENBLAS_NUM_THREADS`/`OMP_NUM_THREADS`/`MKL_NUM_THREADS` are already set to `1` in
   `render.yaml` — no action needed. They avoid a real OpenBLAS memory-allocation failure seen
   when scikit-learn tries to over-subscribe threads on a small instance.)
3. Deploy. First boot runs a bootstrap prediction automatically (the backend self-heals when
   `ai/outputs/` is empty — see the note on persistence below), so it can take ~1–2 minutes before
   `/api/risk/latest` returns data. Watch the logs for `"running a bootstrap prediction now"`.
4. Note the service URL, e.g. `https://floodlens-backend.onrender.com`.

## 3. Deploy the frontend to Vercel

1. On Vercel: **Add New → Project**, import the same GitHub repo.
2. **Root Directory**: `frontend`. Framework preset (Vite), build command, and output directory
   (`dist`) are auto-detected — leave them as-is.
3. Add an environment variable: `VITE_API_BASE_URL` = the Render URL from step 2 (no trailing
   slash), e.g. `https://floodlens-backend.onrender.com`.
4. Deploy. Note the resulting URL, e.g. `https://floodlens.vercel.app`.

## 4. Connect them

Vite bakes `VITE_API_BASE_URL` in at build time, and the backend's CORS check is an allowlist — so
each side needs to know the other's real URL:

1. Back on Render, update `FLOODLENS_CORS_ALLOW_ORIGINS` to
   `["https://floodlens.vercel.app"]` (your real Vercel URL) and redeploy.
2. If you changed anything on the Vercel side, redeploy there too.

## Verify

```bash
curl https://floodlens-backend.onrender.com/api/health
curl https://floodlens-backend.onrender.com/api/risk/latest
```

Then open the Vercel URL in a browser and confirm the dashboard loads real data (not stuck on the
loading skeleton) and the map renders colored cells.

## Known limitations of this free-tier setup

- **Render free web services sleep after 15 minutes idle.** The in-process scheduler only runs
  while the process is alive, so the "every 12h" auto-refresh won't fire reliably unless something
  keeps the service awake (a free uptime pinger like UptimeRobot or cron-job.org hitting
  `/api/health` every ~10 minutes works well). The bootstrap-on-startup behavior means it will
  still self-heal with a fresh prediction whenever it wakes up.
- **No guaranteed persistent disk on Render's free tier.** Prediction history
  (`GET /api/risk/history`) can reset on a cold start. The trained model artifact is committed to
  the repo specifically so at least *that* always survives; only generated predictions are
  ephemeral.
- **The refresh endpoint takes ~80s.** That's a real, live Earth Engine scan — not a bug. Both
  Render and Vercel handle long-running backend requests fine here since it's the backend (not a
  Vercel function) doing the work.
