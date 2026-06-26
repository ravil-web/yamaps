#!/usr/bin/env python3
from __future__ import annotations

import base64
import csv
import gzip
import html
import io
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": UA,
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
})

BAD_DOMAINS = {
    "bing.net", "bing.com", "google.com", "gstatic.com", "yandex.net",
    "pinimg.com", "pinterest.com", "lookaside.fbsbx.com",
}
PREFERRED_HINTS = (
    "crocs", "shopify", "cloudfront", "walmartimages", "ebayimg",
    "tradeinn", "scene7", "fcdn", "cdn", "media", "images",
)
STOP = {
    "crocs","jibbitz","charm","charms","shoe","shoes","adult","adults",
    "for","the","and","card","style","bag","silicone","togo","momentwear",
    "для","взрослых","обувь","цвет","размер","модель","момент",
}

def load_records() -> list[dict[str, Any]]:
    packed = (ROOT / "products.json.gz.b64").read_text(encoding="utf-8").strip()
    raw = gzip.decompress(base64.b64decode(packed))
    return json.loads(raw.decode("utf-8"))

def fold(text: str | None) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9а-яё]+", " ", text.lower()).strip()

def terms(text: str | None) -> list[str]:
    return [x for x in fold(text).split() if len(x) >= 3 and x not in STOP]

def query_variants(rec: dict[str, Any]) -> list[str]:
    key = rec["key"]
    sku = rec.get("sku") or ""
    name = rec["name"]
    cat = rec["category"]
    clean_sku = key.replace("NAME:", "")
    if cat == "Джиббитсы":
        return [
            f'"{sku or clean_sku}" "{name}" Crocs Jibbitz',
            f'"{name}" Crocs Jibbitz charm',
            f'{name} Jibbitz Crocs',
        ]
    if cat == "Обувь Crocs / другая":
        return [
            f'"{clean_sku}" "{name}" Crocs',
            f'Crocs {clean_sku} {name}',
            f'"{name}" Crocs',
        ]
    if cat == "Сумки и аксессуары ToGo":
        return [
            f'"{sku}" "{name}"',
            f'"{name}" ToGo Uniqbrand',
            f'{name} silicone bag',
        ]
    return [
        f'"{sku}" "{name}"',
        f'"{name}" Momentwear',
        f'Momentwear {name}',
    ]

def bing_images(query: str) -> list[dict[str, Any]]:
    url = "https://www.bing.com/images/search?q=" + quote_plus(query) + "&form=HDRSC2&first=1"
    r = SESSION.get(url, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out: list[dict[str, Any]] = []
    for node in soup.select("a.iusc"):
        raw = node.get("m")
        if not raw:
            continue
        try:
            meta = json.loads(html.unescape(raw))
        except Exception:
            continue
        murl = meta.get("murl")
        if not murl or not murl.startswith(("http://", "https://")):
            continue
        out.append({
            "image_url": murl,
            "source_page": meta.get("purl", ""),
            "title": meta.get("t", ""),
            "thumb": meta.get("turl", ""),
        })
    return out

def relevance(rec: dict[str, Any], cand: dict[str, Any], rank: int) -> float:
    hay = fold(" ".join([
        cand.get("title", ""),
        cand.get("source_page", ""),
        cand.get("image_url", ""),
    ]))
    name_terms = terms(rec["name"])
    matched = sum(1 for t in name_terms if t in hay)
    ratio = matched / max(1, len(name_terms))
    score = 35 * ratio + max(0, 12 - rank * 0.6)
    key_tokens = [x for x in re.split(r"[-_\s]+", fold(rec["key"])) if len(x) >= 3]
    if any(x in hay for x in key_tokens):
        score += 30
    full_name = fold(rec["name"])
    if full_name and full_name in hay:
        score += 35
    host = urlparse(cand["image_url"]).netloc.lower()
    if any(h in host for h in PREFERRED_HINTS):
        score += 6
    if any(host == d or host.endswith("." + d) for d in BAD_DOMAINS):
        score -= 30
    return score

def validate_image(url: str, source_page: str = "") -> dict[str, Any] | None:
    headers = {"User-Agent": UA, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"}
    if source_page:
        headers["Referer"] = source_page
    try:
        with SESSION.get(url, headers=headers, timeout=22, stream=True, allow_redirects=True) as r:
            if r.status_code >= 400:
                return None
            ctype = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
            if not ctype.startswith("image/"):
                return None
            buf = bytearray()
            max_read = 7_000_000
            for chunk in r.iter_content(65536):
                if chunk:
                    buf.extend(chunk)
                if len(buf) >= max_read:
                    break
            if len(buf) < 2500:
                return None
            width = height = None
            fmt = ctype.split("/", 1)[-1]
            if ctype != "image/svg+xml":
                try:
                    im = Image.open(io.BytesIO(buf))
                    width, height = im.size
                    fmt = (im.format or fmt).lower()
                    if width < 180 or height < 180:
                        return None
                except Exception:
                    return None
            return {
                "final_url": r.url,
                "content_type": ctype,
                "bytes_checked": len(buf),
                "width": width,
                "height": height,
                "format": fmt,
            }
    except Exception:
        return None

def candidate_confidence(rec: dict[str, Any], cand: dict[str, Any], score: float) -> str:
    hay = fold(" ".join([cand.get("title",""), cand.get("source_page",""), cand.get("image_url","")]))
    nt = terms(rec["name"])
    ratio = sum(t in hay for t in nt) / max(1, len(nt))
    key_parts = [x for x in re.split(r"[-_\s]+", fold(rec["key"])) if len(x) >= 3]
    key_hit = any(x in hay for x in key_parts)
    if score >= 62 and (key_hit or ratio >= 0.65):
        return "high"
    if score >= 40 and ratio >= 0.4:
        return "medium"
    return "low"

def process(rec: dict[str, Any]) -> dict[str, Any]:
    base = {
        "key": rec["key"], "sku": rec.get("sku") or "", "name": rec["name"],
        "category": rec["category"], "image_url": "", "source_page": "",
        "content_type": "", "width": "", "height": "", "confidence": "",
        "search_query": "", "status": "", "candidate_2": "", "candidate_3": "",
    }
    override = rec.get("override")
    if override:
        valid = validate_image(override["image_url"], override.get("source_page", ""))
        if valid:
            base.update({
                "image_url": valid["final_url"],
                "source_page": override.get("source_page", ""),
                "content_type": valid["content_type"],
                "width": valid["width"] or "",
                "height": valid["height"] or "",
                "confidence": "high",
                "status": "verified_override",
            })
            return base

    all_candidates: dict[str, dict[str, Any]] = {}
    used_query = ""
    for qidx, q in enumerate(query_variants(rec)):
        try:
            found = bing_images(q)
        except Exception:
            found = []
        if found and not used_query:
            used_query = q
        for rank, cand in enumerate(found[:24]):
            url = cand["image_url"]
            score = relevance(rec, cand, rank) - qidx * 4
            old = all_candidates.get(url)
            if not old or score > old["score"]:
                cand = dict(cand)
                cand["score"] = score
                cand["query"] = q
                all_candidates[url] = cand
        if qidx == 0 and len(all_candidates) >= 10:
            break
        time.sleep(0.25)

    ranked = sorted(all_candidates.values(), key=lambda x: x["score"], reverse=True)
    verified: list[dict[str, Any]] = []
    for cand in ranked[:18]:
        conf = candidate_confidence(rec, cand, cand["score"])
        if conf == "low" and len(verified) == 0:
            continue
        valid = validate_image(cand["image_url"], cand.get("source_page", ""))
        if not valid:
            continue
        row = {**cand, **valid, "confidence": conf}
        verified.append(row)
        if len(verified) >= 3:
            break
        time.sleep(0.15)

    base["search_query"] = used_query
    if not verified:
        base["status"] = "not_found_or_unverified"
        return base
    best = verified[0]
    base.update({
        "image_url": best["final_url"],
        "source_page": best.get("source_page", ""),
        "content_type": best["content_type"],
        "width": best["width"] or "",
        "height": best["height"] or "",
        "confidence": best["confidence"],
        "search_query": best.get("query", used_query),
        "status": "verified_direct_image",
        "candidate_2": verified[1]["final_url"] if len(verified) > 1 else "",
        "candidate_3": verified[2]["final_url"] if len(verified) > 2 else "",
    })
    return base

def main() -> None:
    records = load_records()
    results: list[dict[str, Any]] = []
    for idx, rec in enumerate(records, 1):
        row = process(rec)
        results.append(row)
        print(f"[{idx}/{len(records)}] {rec['key']} -> {row['status']} {row['confidence']} {row['image_url'][:100]}", flush=True)
        time.sleep(0.35)
    fields = list(results[0].keys())
    with (OUT / "image_results.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
    (OUT / "image_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = {
        "total": len(results),
        "verified": sum(bool(r["image_url"]) for r in results),
        "high": sum(r["confidence"] == "high" for r in results),
        "medium": sum(r["confidence"] == "medium" for r in results),
        "not_found": sum(not r["image_url"] for r in results),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(summary)

if __name__ == "__main__":
    main()
