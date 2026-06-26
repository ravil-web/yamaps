#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import search

ROOT = Path(__file__).resolve().parent


def load_records():
    parts = sorted(ROOT.glob("products.part*.txt"))
    if not parts:
        raise RuntimeError("Input chunks not found")
    packed = "".join(p.read_text(encoding="utf-8").strip() for p in parts)
    print(f"Loaded {len(parts)} chunks, {len(packed)} base64 characters", flush=True)
    raw = gzip.decompress(base64.b64decode(packed, validate=True))
    records = json.loads(raw.decode("utf-8"))
    print(f"Decoded {len(records)} product groups", flush=True)
    return records


search.load_records = load_records
search.main()
