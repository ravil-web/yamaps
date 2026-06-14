from __future__ import annotations

import html
import json
from collections import Counter
from typing import Any


def generate_dashboard_html(
    job: dict[str, Any],
    results: list[dict[str, Any]],
) -> str:
    query = html.escape(str(job.get("query", "—")))
    status = html.escape(str(job.get("status", "—")))
    found = job.get("found", 0)
    created = str(job.get("created_at", ""))[:19].replace("T", " ")
    job_id = html.escape(str(job.get("id", "")))

    ratings = [float(str(r.get("rating", "0")).replace(",", ".")) or 0 for r in results if r.get("rating")]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    total_phones = sum(len(r.get("phones", [])) for r in results)
    total_products = sum(len(r.get("products_and_services", [])) for r in results)
    websites = sum(1 for r in results if r.get("website"))

    all_cats: list[str] = []
    for r in results:
        cats = r.get("categories", [])
        if isinstance(cats, list):
            all_cats.extend(cats)
    cat_counts = Counter(all_cats).most_common(15)
    max_cat = cat_counts[0][1] if cat_counts else 1

    status_colors = {
        "completed": "#22c55e", "running": "#f59e0b", "failed": "#ef4444",
        "stopped": "#f97316", "queued": "#6b7280",
    }
    status_color = status_colors.get(status, "#6b7280")

    rows_html = ""
    for i, r in enumerate(results, 1):
        name = html.escape(str(r.get("name", "—")))
        addr = html.escape(str(r.get("address", "—")))
        phones = r.get("phones", [])
        phone = html.escape(phones[0]) if phones else "—"
        rating = html.escape(str(r.get("rating", "—")))
        cats = r.get("categories", [])
        cat_str = html.escape(", ".join(cats)) if cats else "—"
        products = len(r.get("products_and_services", []))
        website = r.get("website", "")
        bg = "#f8fafc" if i % 2 == 0 else "#ffffff"
        rows_html += f"""
        <tr style="background:{bg}">
          <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;text-align:center;color:#6b7280">{i}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb"><b>{name}</b>{f'<br><a href="{html.escape(website)}" target="_blank" style="color:#2563eb;font-size:12px;text-decoration:none">{html.escape(website[:40])}</a>' if website else ''}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;font-size:13px;color:#555">{addr}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;font-size:13px">{phone}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;text-align:center">{f'<span style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:10px;font-size:13px">⭐ {rating}</span>' if rating != '—' else '—'}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;font-size:12px;color:#888">{cat_str}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #e5e7eb;text-align:center">{products}</td>
        </tr>"""

    cat_bars = ""
    for cat, cnt in cat_counts:
        pct = int(100 * cnt / max_cat)
        cat_bars += f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
          <span style="width:180px;font-size:13px;text-align:right;color:#444;flex-shrink:0">{html.escape(cat)}</span>
          <div style="flex:1;background:#e5e7eb;border-radius:6px;height:22px;overflow:hidden">
            <div style="width:{pct}%;background:linear-gradient(90deg,#2563eb,#60a5fa);height:100%;border-radius:6px"></div>
          </div>
          <span style="width:30px;font-size:13px;color:#666">{cnt}</span>
        </div>"""

    cards_html = ""
    for i, r in enumerate(results):
        name = html.escape(str(r.get("name", "—")))
        addr = html.escape(str(r.get("address", "—")))
        phones = r.get("phones", [])
        phone_str = html.escape(phones[0]) if phones else "—"
        rating = html.escape(str(r.get("rating", "—")))
        cats = r.get("categories", [])
        cat_str = html.escape(", ".join(cats)) if cats else ""
        website = r.get("website", "")
        url = r.get("url", "")
        prods = r.get("products_and_services", [])
        rating_badge = f'<span style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:10px;font-size:12px">⭐ {rating}</span>' if rating != "—" else ""
        website_link = f'<a href="{html.escape(website)}" target="_blank" style="color:#2563eb;font-size:12px;text-decoration:none">{html.escape(website[:40])}</a>' if website else ""
        detail_link = f'/business/{job_id}/{i}'
        prods_html = ""
        if prods:
            prods_html = '<div style="margin-top:10px;display:flex;flex-wrap:wrap;gap:4px">'
            for p in prods[:8]:
                t = html.escape(str(p.get("title", "")))
                pr = html.escape(str(p.get("price", "")))
                if t:
                    prods_html += f'<span style="background:#eff6ff;color:#1e40af;padding:2px 8px;border-radius:8px;font-size:11px">{t}'
                    if pr:
                        prods_html += f' <b>{pr}</b>'
                    prods_html += '</span>'
            if len(prods) > 8:
                prods_html += f'<span style="color:#888;font-size:11px;padding:2px 4px">+{len(prods) - 8} ещё</span>'
            prods_html += '</div>'
        cards_html += f"""
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:14px;padding:18px 20px;transition:box-shadow .15s;cursor:pointer" onmouseover="this.style.boxShadow='0 4px 20px rgba(0,0,0,.08)'" onmouseout="this.style.boxShadow='none'" onclick="window.location.href='{detail_link}'">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:6px">
            <div style="font-size:16px;font-weight:600;color:#1a1a2e">{name}</div>
            {rating_badge}
          </div>
          <div style="font-size:13px;color:#555;margin-bottom:4px">📍 {addr}</div>
          <div style="font-size:13px;color:#555;margin-bottom:4px">📞 {phone_str}</div>
          {'<div style="font-size:12px;color:#888;margin-bottom:4px">🏷️ ' + cat_str + '</div>' if cat_str else ''}
          {website_link}
          {prods_html}
        </div>"""

    products_html = ""
    for r in results:
        prods = r.get("products_and_services", [])
        if not prods:
            continue
        rname = html.escape(str(r.get("name", "")))
        products_html += f'<h3 style="margin:18px 0 8px;color:#333;font-size:14px">{rname}</h3>'
        products_html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px">'
        for p in prods[:20]:
            t = html.escape(str(p.get("title", "—")))
            pr = html.escape(str(p.get("price", "")))
            products_html += f"""
            <div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px">
              <div style="font-size:13px;font-weight:600;color:#1a1a2e;margin-bottom:4px">{t}</div>
              {'<div style="font-size:12px;color:#2563eb;font-weight:600">' + pr + '</div>' if pr else ''}
            </div>"""
        products_html += '</div>'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Отчёт — {query}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#1a1a2e;line-height:1.5}}
  .container{{max-width:1100px;margin:0 auto;padding:24px}}
  .card{{background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,.06);padding:24px;margin-bottom:20px}}
  h1{{font-size:26px;font-weight:700;margin-bottom:4px}}
  .subtitle{{color:#666;font-size:14px;margin-bottom:20px}}
  .kpi-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}}
  .kpi{{text-align:center;padding:16px 8px;background:#f8fafc;border-radius:12px;border:1px solid #e5e7eb}}
  .kpi-value{{font-size:32px;font-weight:700;color:#1a1a2e}}
  .kpi-label{{font-size:12px;color:#888;margin-top:4px}}
  .section-title{{font-size:18px;font-weight:600;color:#2563eb;margin:20px 0 12px}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  th{{background:#2563eb;color:#fff;padding:10px 12px;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}
  .status{{display:inline-block;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600;color:#fff;background:{status_color}}}
  @media(max-width:768px){{.kpi-grid{{grid-template-columns:repeat(2,1fr)}}}}
</style>
</head>
<body>
<div class="container">
  <div class="card">
    <h1>Отчёт парсинга</h1>
    <div class="subtitle">
      Запрос: <b>{query}</b> &nbsp;·&nbsp;
      Статус: <span class="status">{status}</span> &nbsp;·&nbsp;
      Дата: {created}
    </div>
  </div>

  <div class="card">
    <div class="kpi-grid">
      <div class="kpi"><div class="kpi-value">{found}</div><div class="kpi-label">Найдено</div></div>
      <div class="kpi"><div class="kpi-value">{f'{avg_rating:.1f}' if ratings else '—'}</div><div class="kpi-label">Ср. рейтинг</div></div>
      <div class="kpi"><div class="kpi-value">{total_phones}</div><div class="kpi-label">Телефонов</div></div>
      <div class="kpi"><div class="kpi-value">{total_products}</div><div class="kpi-label">Товаров</div></div>
      <div class="kpi"><div class="kpi-value">{websites}</div><div class="kpi-label">Сайтов</div></div>
    </div>
  </div>

  {'<div class="card"><div class="section-title">Категории</div>' + cat_bars + '</div>' if cat_bars else ''}

  <div class="card">
    <div class="section-title">Найденные организации</div>
    <div style="overflow-x:auto">
    <table>
      <thead><tr>
        <th style="width:40px">#</th><th>Название</th><th>Адрес</th><th>Телефон</th><th style="width:70px">Рейтинг</th><th>Категории</th><th style="width:60px">Тов.</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
  </div>

  <div class="card">
    <div class="section-title">Предприятия</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;margin-top:12px">
      {cards_html}
    </div>
  </div>

  {'<div class="card"><div class="section-title">Товары и услуги</div>' + products_html + '</div>' if products_html else ''}

  <div class="card">
    <div class="section-title">Скачать данные</div>
    <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:12px">
      <a href="/api/jobs/{job_id}/export?format=csv" download style="display:inline-flex;align-items:center;gap:6px;padding:10px 20px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;color:#1a1a2e;text-decoration:none;font-size:14px;font-weight:500;transition:all .15s" onmouseover="this.style.background='#eef4ff';this.style.borderColor='#2563eb'" onmouseout="this.style.background='#f8fafc';this.style.borderColor='#e5e7eb'">📄 CSV</a>
      <a href="/api/jobs/{job_id}/export?format=json" download style="display:inline-flex;align-items:center;gap:6px;padding:10px 20px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;color:#1a1a2e;text-decoration:none;font-size:14px;font-weight:500;transition:all .15s" onmouseover="this.style.background='#eef4ff';this.style.borderColor='#2563eb'" onmouseout="this.style.background='#f8fafc';this.style.borderColor='#e5e7eb'">📋 JSON</a>
      <a href="/api/jobs/{job_id}/export?format=xlsx" download style="display:inline-flex;align-items:center;gap:6px;padding:10px 20px;background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;color:#1a1a2e;text-decoration:none;font-size:14px;font-weight:500;transition:all .15s" onmouseover="this.style.background='#eef4ff';this.style.borderColor='#2563eb'" onmouseout="this.style.background='#f8fafc';this.style.borderColor='#e5e7eb'">📊 XLSX</a>
      <a href="/api/jobs/{job_id}/dashboard" download style="display:inline-flex;align-items:center;gap:6px;padding:10px 20px;background:#2563eb;border:1px solid #2563eb;border-radius:10px;color:#fff;text-decoration:none;font-size:14px;font-weight:500;transition:all .15s" onmouseover="this.style.background='#1d4ed8'" onmouseout="this.style.background='#2563eb'">📑 PDF Отчёт</a>
    </div>
  </div>

  <div style="text-align:center;padding:16px;color:#999;font-size:12px">
    Парсер Яндекс Карт — {found} организаций — {created}
  </div>
</div>
</body>
</html>"""
