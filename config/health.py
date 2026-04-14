"""
Enterprise health-check server (FastAPI).

Exposes two standard endpoints used by Kubernetes / Cloud Run probes:
  GET /health         → liveness  (is the process alive?)
  GET /health/ready   → readiness (are all dependencies available?)

Run standalone:
    uvicorn config.health:app --host 0.0.0.0 --port 8080

Or import `app` and mount it inside an existing FastAPI application.
"""

import os
import time
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="ADK Health API", docs_url=None, redoc_url=None)

_START_TIME = time.time()


# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------

def _check_gcp_credentials() -> dict[str, Any]:
    """Verify that Application Default Credentials (ADC) are available."""
    try:
        import google.auth

        _, project = google.auth.default()
        return {"status": "ok", "project": project}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _check_bigquery() -> dict[str, Any]:
    """
    Perform a lightweight BigQuery round-trip.
    We only list datasets (no bytes scanned) to keep it cheap.
    """
    try:
        from google.cloud import bigquery

        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        client = bigquery.Client(project=project)
        # list_datasets is an iterator; peek at the first page only
        next(iter(client.list_datasets(max_results=1)), None)
        return {"status": "ok", "project": project}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["health"])
def liveness() -> JSONResponse:
    """
    Liveness probe — returns 200 as long as the Python process is running.
    Kubernetes restarts the pod if this endpoint stops responding.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "alive",
            "uptime_seconds": round(time.time() - _START_TIME),
        },
    )


@app.get("/health/ready", tags=["health"])
def readiness() -> JSONResponse:
    """
    Readiness probe — returns 200 only when all external dependencies are
    reachable.  Returns 503 if any check fails so the load balancer stops
    routing traffic until the issue resolves.
    """
    checks: dict[str, dict[str, Any]] = {
        "gcp_credentials": _check_gcp_credentials(),
        "bigquery": _check_bigquery(),
    }
    all_ok = all(v["status"] == "ok" for v in checks.values())

    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={
            "status": "ready" if all_ok else "degraded",
            "uptime_seconds": round(time.time() - _START_TIME),
            "checks": checks,
        },
    )
