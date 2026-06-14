from __future__ import annotations

import csv
import io
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.exporters import export_csv
from app.jobs import JobManager
from app.main import app
from app.params import validate_params
from app.storage import SQLiteStore
from parser_core import Company, Progress


class SlowCore:
    started = threading.Event()

    def run(self, query, area, params, on_progress, on_item, stop_flag):
        self.started.set()
        while not stop_flag.wait(0.01):
            on_progress(Progress(10, 0, 0, "working"))
        return []


def _configure(tmp_path: Path, core_factory=SlowCore) -> tuple[TestClient, SQLiteStore]:
    import app.main as main

    store = SQLiteStore(tmp_path / "test.db")
    store.initialize()
    main.store = store
    main.manager = JobManager(store, core_factory=core_factory)
    return TestClient(app), store


def _request() -> dict:
    return {
        "query": "кофейни",
        "area": {"type": "bbox", "coordinates": [39.6, 47.1, 39.9, 47.4]},
        "params": {"target_businesses_count": 1},
    }


def _wait(client: TestClient, job_id: str, statuses: set[str]) -> dict:
    for _ in range(100):
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in statuses:
            return job
        time.sleep(0.01)
    raise AssertionError(f"job did not reach {statuses}")


class TestCleanupOldJobs:
    def test_deletes_old_completed_jobs(self, tmp_path: Path) -> None:
        store = SQLiteStore(tmp_path / "cleanup.db")
        store.initialize()
        old_time = (datetime.now(UTC) - timedelta(days=60)).isoformat()
        recent_time = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        store.create_job({
            "id": "old", "status": "completed", "message": "done", "finished_at": old_time,
        })
        store.create_job({
            "id": "recent", "status": "completed", "message": "done", "finished_at": recent_time,
        })
        store.create_job({
            "id": "running", "status": "running", "message": "working",
        })
        store.add_result("old", {"name": "old result", "yandex_id": "1"})
        store.add_result("recent", {"name": "recent result", "yandex_id": "2"})

        deleted = store.cleanup_old_jobs(max_age_days=30)

        assert deleted == 1
        assert store.get_job("old") is None
        assert store.get_job("recent") is not None
        assert store.get_job("running") is not None
        assert store.list_results("recent", 0, 10)["total"] == 1
        assert store.list_results("old", 0, 10)["total"] == 0

    def test_does_not_delete_when_max_age_is_zero(self, tmp_path: Path) -> None:
        store = SQLiteStore(tmp_path / "no_delete.db")
        store.initialize()
        store.create_job({
            "id": "j1", "status": "completed", "message": "done",
            "finished_at": (datetime.now(UTC) - timedelta(days=999)).isoformat(),
        })
        deleted = store.cleanup_old_jobs(max_age_days=0)
        assert deleted == 0
        assert store.get_job("j1") is not None

    def test_skips_jobs_without_finished_at(self, tmp_path: Path) -> None:
        store = SQLiteStore(tmp_path / "no_finish.db")
        store.initialize()
        store.create_job({"id": "j1", "status": "running", "message": "working"})
        deleted = store.cleanup_old_jobs(max_age_days=0)
        assert deleted == 0
        assert store.get_job("j1") is not None


class TestConcurrentJobLimit:
    def test_rejects_when_limit_reached(self, tmp_path: Path) -> None:
        client, _ = _configure(tmp_path)
        SlowCore.started.clear()
        job1_id = client.post("/api/jobs", json=_request()).json()["id"]
        assert SlowCore.started.wait(1)

        original_max = __import__("app.jobs", fromlist=["MAX_CONCURRENT_JOBS"]).MAX_CONCURRENT_JOBS
        import app.jobs as jobs_mod
        jobs_mod.MAX_CONCURRENT_JOBS = 1
        try:
            response = client.post("/api/jobs", json=_request())
            assert response.status_code == 422
            assert "лимит" in response.json()["detail"]
        finally:
            jobs_mod.MAX_CONCURRENT_JOBS = original_max

        client.post(f"/api/jobs/{job1_id}/stop")
        _wait(client, job1_id, {"stopped"})

    def test_allows_new_job_after_one_completes(self, tmp_path: Path) -> None:
        from app.demo import DemoParserCore

        import app.main as main

        store = SQLiteStore(tmp_path / "limit.db")
        store.initialize()
        main.store = store
        original_max = __import__("app.jobs", fromlist=["MAX_CONCURRENT_JOBS"]).MAX_CONCURRENT_JOBS
        import app.jobs as jobs_mod
        jobs_mod.MAX_CONCURRENT_JOBS = 1
        try:
            main.manager = JobManager(store, core_factory=lambda: DemoParserCore(0.001))
            client = TestClient(app)
            job1 = client.post("/api/jobs", json=_request()).json()
            _wait(client, job1["id"], {"completed"})
            time.sleep(0.1)

            response = client.post("/api/jobs", json=_request())
            assert response.status_code == 202
        finally:
            jobs_mod.MAX_CONCURRENT_JOBS = original_max


class TestTileParamValidation:
    def test_rejects_string_tile_values(self) -> None:
        with pytest.raises(ValueError, match="must be an integer"):
            validate_params({"area.tile_rows": "abc"})

    def test_rejects_non_numeric_tile_values(self) -> None:
        with pytest.raises(ValueError, match="must be an integer"):
            validate_params({"area.tile_columns": [1, 2]})

    def test_rejects_out_of_range_tile_values(self) -> None:
        with pytest.raises(ValueError, match="must be between 1 and 20"):
            validate_params({"area.tile_rows": 25})

    def test_rejects_zero_tile_values(self) -> None:
        with pytest.raises(ValueError, match="must be between 1 and 20"):
            validate_params({"area.tile_columns": 0})

    def test_accepts_valid_tile_values(self) -> None:
        result = validate_params({"area.tile_rows": 3, "area.tile_columns": 5})
        assert result["area.tile_rows"] == 3
        assert result["area.tile_columns"] == 5

    def test_defaults_tile_values_to_one(self) -> None:
        result = validate_params({})
        assert result["area.tile_rows"] == 1
        assert result["area.tile_columns"] == 1


class TestCsvBom:
    def test_csv_export_starts_with_bom(self) -> None:
        results = [{"name": "Тест", "address": "Москва"}]
        exported = export_csv(results)
        assert exported[:3] == b"\xef\xbb\xbf"

    def test_csv_empty_export_starts_with_bom(self) -> None:
        exported = export_csv([])
        assert exported[:3] == b"\xef\xbb\xbf"

    def test_csv_bom_then_utf8_content(self) -> None:
        results = [{"name": "Кофейня"}]
        exported = export_csv(results)
        text = exported[3:].decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert rows[0]["name"] == "Кофейня"


class TestGeocodeRetry:
    def test_retries_on_429(self) -> None:
        from app import geocode

        call_count = 0

        def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            if call_count <= 2:
                resp.status_code = 429
                resp.headers = {"Retry-After": "0.01"}
                resp.raise_for_status.side_effect = Exception("429")
            else:
                resp.status_code = 200
                resp.json.return_value = [{"lat": "55.75", "lon": "37.61", "display_name": "Москва"}]
                resp.raise_for_status = MagicMock()
            return resp

        with patch.object(geocode.httpx, "get", side_effect=mock_get):
            geocode._last_request_time = 0
            result = geocode.suggest_addresses("Москва")
            assert len(result) == 1
            assert call_count == 3

    def test_retries_on_timeout(self) -> None:
        from app import geocode

        call_count = 0

        def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise geocode.httpx.TimeoutException("timeout")
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = [{"lat": "55.75", "lon": "37.61", "display_name": "Москва"}]
            resp.raise_for_status = MagicMock()
            return resp

        with patch.object(geocode.httpx, "get", side_effect=mock_get):
            geocode._last_request_time = 0
            result = geocode.suggest_addresses("Москва")
            assert len(result) == 1
            assert call_count == 2

    def test_fails_after_max_retries(self) -> None:
        from app import geocode

        def mock_get(url, **kwargs):
            raise geocode.httpx.ConnectError("connection refused")

        with patch.object(geocode.httpx, "get", side_effect=mock_get):
            geocode._last_request_time = 0
            with pytest.raises(geocode.httpx.ConnectError):
                geocode.suggest_addresses("Москва")


class TestStopRaceCondition:
    def test_stop_during_run_preserves_stopping_status(self, tmp_path: Path) -> None:
        client, _ = _configure(tmp_path)
        SlowCore.started.clear()
        job_id = client.post("/api/jobs", json=_request()).json()["id"]
        assert SlowCore.started.wait(1)
        client.post(f"/api/jobs/{job_id}/stop")
        job = _wait(client, job_id, {"stopped"})
        assert job["status"] == "stopped"
