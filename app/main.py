from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from parser_core import ParserCore
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

from .exporters import export_csv, export_json, export_xlsx
from .dashboard import generate_dashboard_pdf
from .dashboard_html import generate_dashboard_html
from .demo import DemoParserCore
from .jobs import JobManager
from .geocode import geocode_address, suggest_addresses
from .params import load_schema, validate_params
from .schemas import JobCreate, ResultPage
from .storage import SQLiteStore

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)
DATA_DIR = Path(os.getenv("APP_DATA_DIR", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

store = SQLiteStore(DATA_DIR / "app.db")
store.initialize()
store.recover_interrupted_jobs()
manager = JobManager(store, core_factory=DemoParserCore if os.getenv("PARSER_DEMO_MODE") == "1" else ParserCore)

app = FastAPI(title="Yandex Maps Parser", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(ROOT / "app" / "static" / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def config() -> JSONResponse:
    key = os.getenv("YANDEX_MAPS_API_KEY", "")
    return JSONResponse(
        {"yandex_maps_api_key": key, "map_enabled": bool(key)},
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/api/params/schema")
def params_schema() -> dict:
    return load_schema()


@app.get("/api/geocode")
def geocode(address: str = Query(min_length=1, max_length=500)) -> dict:
    try:
        result = geocode_address(address.strip())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"geocoding service unavailable: {exc}") from exc
    if not result:
        raise HTTPException(status_code=404, detail="address not found")
    return result


@app.get("/api/geocode/suggest")
def geocode_suggest(address: str = Query(min_length=3, max_length=500)) -> list[dict]:
    try:
        return suggest_addresses(address.strip(), limit=5)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"geocoding service unavailable: {exc}") from exc


@app.post("/api/jobs", status_code=202)
def create_job(request: JobCreate) -> dict:
    try:
        params = validate_params(request.params)
        request.area.to_core()
        return manager.create(request.query, request.area, params)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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


@app.get("/api/jobs/{job_id}/dashboard")
def dashboard_pdf(job_id: str) -> Response:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    results = store.all_results(job_id)
    return Response(generate_dashboard_pdf(job, results), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="dashboard_{job_id}.pdf"'})


@app.get("/api/jobs/{job_id}/dashboard.html")
def dashboard_html(job_id: str) -> Response:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    results = store.all_results(job_id)
    return Response(generate_dashboard_html(job, results).encode("utf-8"), media_type="text/html; charset=utf-8")


@app.get("/api/dashboards")
def list_dashboards() -> list[dict[str, str]]:
    from .jobs import DASHBOARDS_DIR
    DASHBOARDS_DIR.mkdir(parents=True, exist_ok=True)
    dashboards = []
    for f in sorted(DASHBOARDS_DIR.glob("*.html"), reverse=True):
        name = f.stem
        parts = name.rsplit("_", 2)
        query = parts[0].replace("_", " ") if len(parts) >= 3 else name
        ts = f"{parts[-2]}_{parts[-1]}" if len(parts) >= 3 else ""
        dashboards.append({"name": name, "query": query, "created": ts,
                           "html": f"/api/dashboards/{f.name}", "pdf": f"/api/dashboards/{f.stem}.pdf"})
    return dashboards


@app.get("/api/dashboards/{filename}")
def serve_dashboard(filename: str) -> Response:
    from .jobs import DASHBOARDS_DIR
    safe = re.sub(r'[^a-zA-Z0-9_\-]', '', filename)
    for ext, ct in [(".html", "text/html; charset=utf-8"), (".pdf", "application/pdf")]:
        path = DASHBOARDS_DIR / f"{safe}{ext}"
        if path.exists():
            return Response(path.read_bytes(), media_type=ct)
    raise HTTPException(status_code=404, detail="dashboard not found")


@app.get("/api/jobs/{job_id}/business/{index}")
def get_business(job_id: str, index: int) -> dict:
    if not store.get_job(job_id):
        raise HTTPException(status_code=404, detail="job not found")
    results = store.all_results(job_id)
    if index < 0 or index >= len(results):
        raise HTTPException(status_code=404, detail="business not found")
    return results[index]


@app.get("/business/{job_id}/{index}")
def business_page(job_id: str, index: int) -> Response:
    from .business_page import generate_business_html
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    results = store.all_results(job_id)
    if index < 0 or index >= len(results):
        raise HTTPException(status_code=404, detail="business not found")
    return Response(generate_business_html(job, results[index], index, len(results)).encode("utf-8"),
                    media_type="text/html; charset=utf-8")
