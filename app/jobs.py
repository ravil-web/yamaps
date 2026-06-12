from __future__ import annotations

import threading
import time
import traceback
import uuid
from datetime import UTC, datetime
from typing import Any, Callable

from parser_core import ParserCore, ParserParams, Progress

from .storage import SQLiteStore


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class JobManager:
    def __init__(
        self,
        store: SQLiteStore,
        core_factory: Callable[[], ParserCore] = ParserCore,
    ) -> None:
        self.store = store
        self.core_factory = core_factory
        self._stops: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def create(self, query: str, area: Any, params: dict[str, Any]) -> dict[str, Any]:
        job_id = str(uuid.uuid4())
        job = {
            "id": job_id,
            "query": query,
            "area": area.model_dump() if hasattr(area, "model_dump") else area,
            "params": params,
            "status": "queued",
            "progress": 0,
            "processed": 0,
            "found": 0,
            "message": "Задача поставлена в очередь",
            "error": None,
            "created_at": utc_now(),
            "started_at": None,
            "finished_at": None,
        }
        self.store.create_job(job)
        stop = threading.Event()
        with self._lock:
            self._stops[job_id] = stop
        thread = threading.Thread(
            target=self._run,
            args=(job_id, query, area.to_core(), params, stop),
            daemon=True,
            name=f"parser-job-{job_id[:8]}",
        )
        thread.start()
        return self.store.get_job(job_id)

    def stop(self, job_id: str) -> dict[str, Any] | None:
        job = self.store.get_job(job_id)
        if not job:
            return None
        if job["status"] not in {"queued", "running"}:
            return job
        self.store.update_job(job_id, status="stopping", message="Остановка задачи")
        with self._lock:
            stop = self._stops.get(job_id)
        if stop:
            stop.set()
        return self.store.get_job(job_id)

    def _run(self, job_id: str, query: str, area: Any, params: dict[str, Any], stop: threading.Event) -> None:
        started = time.monotonic()
        heartbeat_done = threading.Event()
        self.store.update_job(job_id, status="running", started_at=utc_now(), message="Запуск фонового браузера")

        def heartbeat() -> None:
            while not heartbeat_done.wait(5):
                job = self.store.get_job(job_id)
                if not job or job["status"] != "running" or job["progress"] != 0:
                    continue
                elapsed = int(time.monotonic() - started)
                self.store.update_job(
                    job_id,
                    message=f"Поиск организаций на Яндекс Картах, прошло {elapsed} сек.",
                )

        threading.Thread(target=heartbeat, daemon=True, name=f"parser-heartbeat-{job_id[:8]}").start()

        def on_progress(progress: Progress) -> None:
            self.store.update_job(
                job_id,
                progress=progress.progress,
                processed=progress.processed,
                found=progress.found,
                message=progress.message,
            )

        def on_item(company: Any) -> None:
            self.store.add_result(job_id, company.data)

        try:
            results = self.core_factory().run(
                query=query,
                area=area,
                params=ParserParams(params),
                on_progress=on_progress,
                on_item=on_item,
                stop_flag=stop,
            )
            status = "stopped" if stop.is_set() else "completed"
            self.store.update_job(
                job_id,
                status=status,
                progress=100 if status == "completed" else self.store.get_job(job_id)["progress"],
                found=len(results),
                message="Задача остановлена" if status == "stopped" else "Парсинг завершён",
                finished_at=utc_now(),
            )
        except Exception as exc:
            self.store.update_job(
                job_id,
                status="failed",
                message="Парсинг завершился с ошибкой",
                error=f"{type(exc).__name__}: {exc}",
                finished_at=utc_now(),
            )
            traceback.print_exc()
        finally:
            heartbeat_done.set()
            with self._lock:
                self._stops.pop(job_id, None)
