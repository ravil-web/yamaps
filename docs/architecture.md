# Architecture

## Stack

- Backend: Python, FastAPI, Pydantic
- Long-running work: one managed background thread per parsing job
- Persistence: SQLite through the standard library `sqlite3`
- Parser core: isolated `parser_core/` package wrapping frozen Selenium logic
- Frontend: dependency-free HTML/CSS/JavaScript SPA served by FastAPI
- Map: Yandex Maps JavaScript API 2.1

## Components

```text
Browser SPA
  -> FastAPI routes
     -> JobManager -> background ParserCore
     -> SQLiteStore
     -> ExportService
  -> Yandex Maps JS API (when key exists)

ParserCore
  -> area tiler / URL builder
  -> preserved MainParser URL collection
  -> preserved SingleBusinessParser extraction
  -> normalization / polygon filter / deduplication
```

## Parser Boundary

```python
class ParserCore:
    def run(
        self,
        query: str,
        area: Area,
        params: ParserParams,
        on_progress: Callable[[Progress], None],
        on_item: Callable[[Company], None],
        stop_flag: threading.Event,
    ) -> list[Company]: ...
```

The legacy selector, delay, wait, scrolling, extraction, and anti-detection
behavior is copied into `parser_core/legacy_adapter.py`. Runtime configuration
is injected before instantiation. New logic is limited to orchestration,
callbacks, stopping checks, area tiling, coordinate normalization, filtering,
and deduplication.

## Job Lifecycle

`queued -> running -> completed`

Alternative terminal paths:

- `running -> stopping -> stopped`
- `queued|running -> failed`

Progress callbacks update SQLite. Item callbacks persist each result
immediately, enabling live markers and partial export.

## Persistence

SQLite tables:

- `jobs`: request, status, counters, timestamps, message, error
- `results`: job ID, deduplication key, normalized JSON payload, coordinates

Writes use short transactions and a new SQLite connection per operation so
background threads do not share connections.

## Secrets And Configuration

- `YANDEX_MAPS_API_KEY` is read only from environment / `.env`.
- Missing key disables the map module and displays setup instructions; API and
  parser remain usable.
- Proxy secrets, if later supplied to supported parser options, remain
  environment-only and are never returned by `/api/config`.

## Failure Behavior

- Parser exceptions mark a job failed and retain partial results.
- Captcha/block signals are surfaced as a clear job message/error; the
  preserved browser and retry behavior remains in control.
- Stop is cooperative. It is checked between tiles, URL collection phases, and
  company cards; active Selenium waits may delay stopping.

## Testing

- Unit: area validation, tiling, URL generation, polygon filtering,
  normalization, deduplication, storage, exports.
- Integration: API lifecycle using an injected deterministic fake ParserCore.
- E2E: browser UI scenarios using deterministic demo mode; live Selenium smoke
  is separate because Yandex availability and captcha are external.

