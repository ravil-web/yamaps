from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .exporters import export_csv, export_json, export_xlsx
from .jobs import JobManager
from .params import load_schema, validate_params
from .schemas import JobCreate, ResultPage
from .storage import SQLiteStore

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("APP_DATA_DIR", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

store = SQLiteStore(DATA_DIR / "app.db")
store.initialize()
manager = JobManager(store)

app = FastAPI(title="Yandex Maps Parser", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(ROOT / "app" / "static" / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def config() -> dict[str, str | bool]:
    key = os.getenv("YANDEX_MAPS_API_KEY", "")
    return {"yandex_maps_api_key": key, "map_enabled": bool(key)}


@app.get("/api/params/schema")
def params_schema() -> dict:
    return load_schema()


@app.post("/api/jobs", status_code=202)
def create_job(request: JobCreate) -> dict:
    try:
        params = validate_params(request.params)
        request.area.to_core()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return manager.create(request.query, request.area, params)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/api/jobs/{job_id}/results", response_model=ResultPage)
def get_results(
    job_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    if not store.get_job(job_id):
        raise HTTPException(status_code=404, detail="job not found")
    return store.list_results(job_id, offset, limit)


@app.post("/api/jobs/{job_id}/stop")
def stop_job(job_id: str) -> dict:
    job = manager.stop(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.get("/api/jobs/{job_id}/export")
def export_job(job_id: str, format: Literal["csv", "xlsx", "json"]) -> Response:
    if not store.get_job(job_id):
        raise HTTPException(status_code=404, detail="job not found")
    results = store.all_results(job_id)
    exporters = {
        "json": (export_json, "application/json", "json"),
        "csv": (export_csv, "text/csv; charset=utf-8", "csv"),
        "xlsx": (
            export_xlsx,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xlsx",
        ),
    }
    exporter, media_type, suffix = exporters[format]
    return Response(
        exporter(results),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{job_id}.{suffix}"'},
    )
