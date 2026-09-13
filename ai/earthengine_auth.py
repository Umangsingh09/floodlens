"""Earth Engine authentication for both local development and a server deployment.

Locally, `earthengine authenticate` stores interactive user OAuth credentials on disk, and
plain `ee.Initialize(project=...)` picks those up automatically. A deployed server (Render,
etc.) can't run that interactive browser flow, so it authenticates instead with a Google Cloud
service account key — the standard non-interactive credential for server-to-server access.

Nothing here fabricates access: if neither credential source is available, `ee.Initialize`
raises the same error it always would.
"""

from __future__ import annotations

import json
import os
from typing import Any


def initialize_earth_engine(*, project: str | None = None) -> None:
    import ee  # type: ignore

    key_data = _load_service_account_key()
    if key_data is not None:
        email = key_data.get("client_email")
        if not email:
            raise RuntimeError("Service account key is missing 'client_email'.")
        credentials = ee.ServiceAccountCredentials(email, key_data=json.dumps(key_data))
        ee.Initialize(credentials, project=project or key_data.get("project_id"))
        return

    # Local development: relies on `earthengine authenticate` having stored user credentials.
    ee.Initialize(project=project)


def _load_service_account_key() -> dict[str, Any] | None:
    """Return the service-account key as a dict, from either supported source, or None."""
    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path and os.path.isfile(key_path):
        with open(key_path, encoding="utf-8") as f:
            return json.load(f)

    inline_key = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if inline_key:
        return json.loads(inline_key)

    return None


__all__ = ["initialize_earth_engine"]
