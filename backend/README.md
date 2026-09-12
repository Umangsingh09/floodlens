# FloodLens Backend

Minimal FastAPI service for the FloodLens project foundation.

Currently exposes only a health check endpoint. Prediction, data ingestion,
and alerting endpoints will be added in later phases once the AI/data
pipeline exists.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Verify

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{ "status": "ok", "service": "FloodLens API" }
```

## Structure

```
app/
├── main.py       # FastAPI app instance, middleware, router wiring
├── api/          # Route definitions
├── services/     # Business logic (empty — future work)
├── schemas/      # Pydantic request/response models
└── core/         # Configuration
```
