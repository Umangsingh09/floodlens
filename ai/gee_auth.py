"""Shared Earth Engine authentication for both local development and deployed hosts.

Locally, `earthengine authenticate` caches a user OAuth credential on disk and plain
`ee.Initialize(project=...)` picks it up automatically. A deployed server has no such cache and
cannot run an interactive OAuth flow, so it authenticates as a Google Cloud service account
instead, via a JSON key provided through an environment variable.

This module is the single place that decides which of the two to use, so every real Earth Engine
call site (training, live inference) authenticates the same way without duplicating the logic.
"""

from __future__ import annotations

import json
import os


def initialize_earth_engine(*, project: str | None = None) -> None:
    import ee  # type: ignore

    service_account_json = os.environ.get("GEE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        key_data = json.loads(service_account_json)
        credentials = ee.ServiceAccountCredentials(key_data["client_email"], key_data=service_account_json)
        ee.Initialize(credentials, project=project or key_data.get("project_id"))
        return

    # Local development: use the credential cached by `earthengine authenticate`.
    ee.Initialize(project=project)


__all__ = ["initialize_earth_engine"]
