from __future__ import annotations

import html
from typing import Any


def generate_business_html(
    job: dict[str, Any],
    business: dict[str, Any],
    index: int,
    total: int,
) -> str:
    name = html.escape(str(business.get("name", "—")))
    addr = html.escape(str(business.get("address", "—")))
    rating = html.escape(str(business.get("rating", "—")))
    phones = business.get("phones", [])
    website = business.get("website", "")
    categories = business.get("categories", [])
    url = business.get("url", "")
    yandex_id = business.get("yandex_id", "")
    products = business.get("products_and_services", [])
    query = html.escape(str(job.get("query", "")))
    job_id = html.escape(str(job.get("id", "")))

    phones_html = "".join(f'<a href="tel:{html.escape(p)}" style="color:#2563eb;text-decoration:none">{html.escape(p)}</a>' for p in phones) if phones else "—"
    cats_html = " &middot; ".join(html.escape(c) for c in categories) if categories else "—"
    website_html = f'<a href="{html.escape(website)}" target="_blank" style="color:#2563eb">{html.escape(website)}</a>' if website else "—"
    url_html = f'<a href="{html.escape(url)}" target="_blank" style="color:#2563eb;font-size:13px">{html.escape(url[:80])}</a>' if url else ""

    products_html = ""
    if products:
        products_html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin-top:16px">'
        for p in products:
            t = html.escape(str(p.get("title", "—")))
            pr = html.escape(str(p.get("price", "")))
            desc = html.escape(str(p.get("description", "")))
            products_html += f"""
            <div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px">
              <div style="font-size:14px;font-weight:600;color:#1a1a2e;margin-bottom:4px">{t}</div>
              {'<div style="font-size:15px;color:#2563eb;font-weight:700;margin-bottom:4px">' + pr + '</div>' if pr else ''}
              {'<div style="font-size:12px;color:#888">' + desc + '</div>' if desc else ''}
            </div>"""
        products_html += "</div>"

    rating_html = f'<span style="background:#fef3c7;color:#92400e;padding:4px 14px;border-radius:20px;font-size:16px;font-weight:600">⭐ {rating}</span>' if rating != "—" else '<span style="color:#999">Нет данных</span>'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{name}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#1a1a2e;line-height:1.6}}
  .container{{max-width:900px;margin:0 auto;padding:24px}}
  .card{{background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.06);padding:28px;margin-bottom:20px}}
  .back{{display:inline-flex;align-items:center;gap:6px;color:#666;text-decoration:none;font-size:14px;margin-bottom:16px;transition:color .15s}}
  .back:hover{{color:#2563eb}}
  h1{{font-size:24px;font-weight:700;margin-bottom:4px}}
  .meta{{color:#888;font-size:13px;margin-bottom:16px}}
  .badge{{display:inline-block;padding:4px 12px;border-radius:20px;font-size:13px;background:#eff6ff;color:#2563eb;margin:2px 4px 2px 0}}
  .info-grid{{display:grid;grid-template-columns:140px 1fr;gap:8px 16px;font-size:14px;margin-top:16px}}
  .info-label{{color:#888;font-weight:500}}
  .info-value{{color:#1a1a2e}}
  .section-title{{font-size:16px;font-weight:600;color:#2563eb;margin:24px 0 4px}}
  hr{{border:0;border-top:1px solid #e5e7eb;margin:20px 0}}
</style>
</head>
<body>
<div class="container">
  <a class="back" href="/api/jobs/{job_id}/results?limit=1000" onclick="history.back();return false">← Назад к результатам</a>

  <div class="card">
    <h1>{name}</h1>
    <div class="meta">{query} &middot; {index + 1} из {total}</div>
    {rating_html}
    {url_html}

    <hr>
    <div class="info-grid">
      <div class="info-label">Адрес</div><div class="info-value">{addr}</div>
      <div class="info-label">Телефон</div><div class="info-value">{phones_html}</div>
      <div class="info-label">Сайт</div><div class="info-value">{website_html}</div>
      <div class="info-label">Категории</div><div class="info-value">{cats_html}</div>
      <div class="info-label">Yandex ID</div><div class="info-value">{html.escape(yandex_id) if yandex_id else '—'}</div>
    </div>
  </div>

  {"<div class='card'><div class='section-title'>Товары и услуги (" + str(len(products)) + ")</div>" + products_html + "</div>" if products else '<div class="card"><div class="section-title">Товары и услуги</div><p style="color:#999;margin-top:8px">Нет данных о товарах/услугах</p></div>'}
</div>
</body>
</html>"""
