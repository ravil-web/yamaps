from __future__ import annotations

import threading
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.jobs import JobManager
from app.main import app
from app.storage import SQLiteStore
from parser_core import Company, Progress


class FakeCore:
    def run(self, query, area, params, on_progress, on_item, stop_flag):
        results = []
        for index in range(3):
            if stop_flag.is_set():
                break
            company = Company(
                {
                    "name": f"{query} {index}",
                    "yandex_id": str(index),
                    "longitude": 39.7 + index / 100,
                    "latitude": 47.2 + index / 100,
                }
            )
            results.append(company)
            on_item(company)
            on_progress(Progress((index + 1) * 30, index + 1, index + 1, "working"))
        return results


class BlockingCore:
    started = threading.Event()

    def run(self, query, area, params, on_progress, on_item, stop_flag):
        self.started.set()
        while not stop_flag.wait(0.01):
            on_progress(Progress(10, 0, 0, "waiting"))
        return []


def _configure(tmp_path: Path, core_factory=FakeCore) -> TestClient:
    import app.main as main

    store = SQLiteStore(tmp_path / "test.db")
    store.initialize()
    main.store = store
    main.manager = JobManager(store, core_factory=core_factory)
    return TestClient(app)


def _request() -> dict:
    return {
        "query": "кофейни",
        "area": {"type": "bbox", "coordinates": [39.6, 47.1, 39.9, 47.4]},
        "params": {"target_businesses_count": 3},
    }


def _wait(client: TestClient, job_id: str, statuses: set[str]) -> dict:
    for _ in range(100):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in statuses:
            return job
        time.sleep(0.01)
    raise AssertionError(f"job did not reach {statuses}")


def test_api_job_lifecycle_results_and_exports(tmp_path: Path) -> None:
    client = _configure(tmp_path)
    response = client.post("/api/jobs", json=_request())
    assert response.status_code == 202
    job = _wait(client, response.json()["id"], {"completed"})
    assert job["progress"] == 100
    assert job["found"] == 3

    page = client.get(f"/api/jobs/{job['id']}/results").json()
    assert page["total"] == 3
    assert len(page["items"]) == 3
    for format_name in ("json", "csv", "xlsx"):
        exported = client.get(f"/api/jobs/{job['id']}/export?format={format_name}")
        assert exported.status_code == 200
        assert exported.content


def test_api_stop_and_partial_export(tmp_path: Path) -> None:
    BlockingCore.started.clear()
    client = _configure(tmp_path, BlockingCore)
    job_id = client.post("/api/jobs", json=_request()).json()["id"]
    assert BlockingCore.started.wait(1)
    stopped = client.post(f"/api/jobs/{job_id}/stop")
    assert stopped.status_code == 200
    job = _wait(client, job_id, {"stopped"})
    assert job["status"] == "stopped"
    assert client.get(f"/api/jobs/{job_id}/export?format=json").status_code == 200


def test_api_validation_config_and_not_found(tmp_path: Path, monkeypatch) -> None:
    client = _configure(tmp_path)
    monkeypatch.delenv("YANDEX_MAPS_API_KEY", raising=False)
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/config").json()["map_enabled"] is False
    assert client.get("/api/params/schema").json()["parameters"]
    assert "Парсер Яндекс Карт" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/api/jobs/missing").status_code == 404
    invalid = _request()
    invalid["params"] = {"unknown": True}
    assert client.post("/api/jobs", json=invalid).status_code == 422
