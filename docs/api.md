# API Contract

Base path: `/api`. JSON uses UTF-8. Timestamps use UTC ISO-8601.

## Data Contracts

### Area

Rectangle:

```json
{"type":"bbox","coordinates":[39.65,47.20,39.75,47.30]}
```

Polygon:

```json
{"type":"polygon","coordinates":[[39.65,47.20],[39.75,47.20],[39.72,47.30],[39.65,47.20]]}
```

Coordinates use `[longitude, latitude]`. Polygon rings must be closed and
contain at least four points including the repeated final point.

### Job Create

```json
{
  "query": "кофейни",
  "area": {"type":"bbox","coordinates":[39.65,47.20,39.75,47.30]},
  "params": {"target_businesses_count": 20, "delays.scroll": 1}
}
```

Only names from `params_schema.json.parameters` are accepted. Omitted
parameters use the original parser defaults.

### Job

```json
{
  "id": "uuid",
  "query": "кофейни",
  "status": "queued|running|completed|stopping|stopped|failed",
  "progress": 45,
  "processed": 9,
  "found": 12,
  "message": "Обработка 9/20",
  "error": null,
  "created_at": "2026-06-12T10:00:00Z",
  "started_at": null,
  "finished_at": null
}
```

### Company

The normalized result retains source fields and guarantees:

```json
{
  "name": "Example",
  "address": "Address",
  "phones": ["+7..."],
  "rating": "4.8",
  "url": "https://yandex.ru/maps/org/.../123/",
  "yandex_id": "123",
  "latitude": 47.25,
  "longitude": 39.70
}
```

## Endpoints

### `POST /api/jobs`

Creates and queues a parsing job. Returns `202` and Job. Returns `422` for
invalid area or parser parameters.

### `GET /api/jobs/{id}`

Returns current Job. Returns `404` for unknown ID.

### `GET /api/jobs/{id}/results?offset=0&limit=100`

Returns:

```json
{"items":[],"total":0,"offset":0,"limit":100}
```

Results remain available for stopped and failed jobs.

### `GET /api/jobs/{id}/export?format=csv|xlsx|json`

Returns an attachment generated from all currently persisted results. Partial
exports are supported. Returns `400` for unsupported formats.

### `POST /api/jobs/{id}/stop`

Sets the job stop event and returns the current Job. Completed/failed/stopped
jobs are returned unchanged.

### `GET /api/params/schema`

Returns the frontend-consumable contents of `params_schema.json`.

### `GET /api/config`

Returns public frontend configuration:

```json
{"yandex_maps_api_key":"","map_enabled":false}
```

No other environment values or secrets are exposed.

### `GET /api/health`

Returns `{"status":"ok"}` when the application and SQLite storage are
available.

## Area Translation

1. Compute the bbox of the rectangle or polygon.
2. Split it into a configurable grid (`area.tile_rows`, `area.tile_columns`;
   default `1x1`) to avoid changing the baseline parser's traversal behavior.
3. Build a Yandex Maps search URL for each tile with escaped query, `ll`
   (center), `spn`/`sspn` (longitude/latitude span), and compatible zoom.
4. Invoke the frozen legacy URL-collection and card-extraction logic for each
   tile.
5. Normalize coordinates, filter polygon results using point-in-polygon, and
   deduplicate by Yandex ID, then normalized URL, then rounded coordinates.

