# FloodLens Architecture

This document describes the **intended** end-to-end pipeline for FloodLens
and which parts of it currently exist. It will be revised as the AI/data
research progresses.

## Intended pipeline

```
Satellite data
    ↓
Preprocessing
    ↓
AI model
    ↓
Spatial risk output
    ↓
Backend / API
    ↓
Frontend
    ↓
Interactive risk map
```

| Stage | Description | Status |
|---|---|---|
| Satellite data | Public satellite imagery/derived products over a defined historical window, for the selected Bihar AOI | **Not implemented.** No data source is connected. |
| Preprocessing | Cleaning, reprojecting, and tiling raw satellite data into model-ready inputs | **Not implemented.** |
| AI model | Model producing spatial flood-risk predictions from preprocessed inputs | **Not implemented.** Owned by the AI/geospatial team member. |
| Spatial risk output | A georeferenced grid/raster of per-location risk, with metadata (see [AI_INTEGRATION.md](AI_INTEGRATION.md)) | **Not implemented.** |
| Backend / API | FastAPI service exposing prediction/risk data to the frontend | **Foundation only.** A health-check endpoint exists (`GET /api/health`). No prediction endpoints exist yet. |
| Frontend | React dashboard consuming the API | **Foundation only.** Basic app shell and dashboard layout exist; no data is fetched from AI/prediction endpoints because none exist. |
| Interactive risk map | Leaflet-based map rendering the risk output over the region | **Placeholder only.** A base map centered on the target region renders via `react-leaflet`, clearly labeled as having no risk overlay. |

## Current phase

The project is in the **foundation phase**: repository structure, a
runnable frontend shell, and a runnable backend health check. No stage of
the actual pipeline (satellite → preprocessing → model → risk output) has
been built.

## Design intent (for future phases)

- **Validation:** The model's output will be checked against at least one
  real historical flood event in the target region before being treated as
  trustworthy.
- **Lag:** The gap between a satellite pass (observation time) and the
  resulting prediction being available will be explicit and surfaced, not
  hidden — see the `sourcePassTimestamp` / `predictionTimestamp` fields in
  [AI_INTEGRATION.md](AI_INTEGRATION.md).
- **Secondary data source & alerts:** Optional; only added after the core
  single-source pipeline is validated.
