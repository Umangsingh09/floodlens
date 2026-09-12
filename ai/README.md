# FloodLens AI Workspace

This directory is organizational scaffolding for the future AI/geospatial
pipeline. **No model, preprocessing logic, or training code exists yet.**
This work is owned by the AI/geospatial team member and will be built in a
later phase.

## Structure

```
ai/
├── data/           # Local staging for downloaded/derived datasets (not committed)
├── preprocessing/  # Satellite data ingestion & preprocessing (future)
├── models/         # Model architecture definitions (future)
├── training/       # Training scripts & experiment configs (future)
├── inference/       # Inference/prediction pipeline (future)
└── evaluation/      # Validation against historical flood events (future)
```

## Status

Not started. See [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) and
[docs/AI_INTEGRATION.md](../docs/AI_INTEGRATION.md) for the intended pipeline
and the proposed output contract with the backend.
