# FloodLens

FloodLens is a spatial flood-risk intelligence project for a specific
flood-prone region of Bihar, India. It aims to turn public satellite
observations into an actionable, geographically-explicit flood-risk map,
validated against a real historical flood event.

## Problem framing

- **Hazard:** Flood (single hazard, by design)
- **Region:** A specific flood-prone area of Bihar, India (exact AOI to be
  finalized by the AI/geospatial team)
- **Data:** Public satellite data, over a defined historical time window
- **Output:** A spatial flood-risk prediction — a risk map over the region,
  not a single classification score
- **Validation:** Against at least one real historical flood event in the
  region
- **Lag:** The system will document the explicit lag between a satellite
  pass and the resulting prediction

### Why spatial prediction, not a single score

Flood risk is not uniform across a region — river proximity, elevation, and
land cover mean risk varies block by block. A single "is there a flood"
score would hide exactly the information a responder or planner needs:
*where*. FloodLens is designed around producing a risk map (a grid/raster
of per-location risk), not a scalar prediction.

## Current phase: project foundation

This repository is currently in its **foundation phase**. The goal of this
phase is a clean, runnable skeleton that the rest of the project can build
on — not a working prediction system.

### What exists right now

- A running React + TypeScript + Vite frontend with a basic application
  shell, a dashboard placeholder, and a map placeholder (base map only, no
  risk overlay).
- A running FastAPI backend exposing a single health-check endpoint.
- Organizational scaffolding for the future AI/geospatial workspace.
- Documentation of the intended architecture and the proposed AI↔backend
  data contract (not yet implemented).

### What is intentionally NOT implemented yet

- No satellite data has been downloaded or connected.
- No connection to Google Earth Engine, Sentinel Hub, or any other
  satellite data provider.
- No flood prediction model exists.
- No real or fabricated risk data is displayed anywhere in the app.
- No validation against historical flood events has been performed.
- No alerting/threshold logic exists.
- No authentication.
- Nothing is deployed.

Anywhere the UI shows a "map" or "risk" placeholder, it is explicitly
labeled as a placeholder — FloodLens will never present fabricated data as
if it were a real prediction.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the intended
end-to-end pipeline (satellite data → preprocessing → AI model → spatial
risk output → backend API → frontend map) and which stages currently exist.

See [docs/AI_INTEGRATION.md](docs/AI_INTEGRATION.md) for the proposed
contract between the future AI pipeline and the backend/frontend.

## Repository structure

```
floodlens/
├── frontend/   # React + TypeScript + Vite dashboard
├── backend/    # FastAPI service
├── ai/         # Future AI/geospatial workspace (structure only)
├── data/       # Local data staging (git-ignored contents)
├── docs/       # Architecture & integration documentation
├── scripts/    # Future automation/utility scripts
├── .gitignore
└── README.md
```

## Running the project

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`. Copy `.env.example` to `.env` to point it
at a non-default backend URL.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Runs at `http://localhost:8000`. Verify with:

```bash
curl http://localhost:8000/api/health
```

## Team

- AI/geospatial research and model development: Hariom
- Product, full-stack, and integration: project lead
