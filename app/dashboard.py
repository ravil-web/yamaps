from __future__ import annotations

import io
from collections import Counter
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "DashboardTitle", parent=styles["Title"],
        fontSize=22, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"),
    ))
    styles.add(ParagraphStyle(
        "DashboardSubtitle", parent=styles["Normal"],
        fontSize=11, textColor=colors.HexColor("#666666"), spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        "SectionHead", parent=styles["Heading2"],
        fontSize=14, textColor=colors.HexColor("#2563eb"), spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        "KpiValue", parent=styles["Normal"],
        fontSize=28, alignment=TA_CENTER, textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        "KpiLabel", parent=styles["Normal"],
        fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#888888"),
    ))
    styles.add(ParagraphStyle(
        "TableCell", parent=styles["Normal"], fontSize=8, leading=10,
    ))
    styles.add(ParagraphStyle(
        "TableHeader", parent=styles["Normal"], fontSize=8, leading=10,
        fontName="Helvetica-Bold", textColor=colors.white,
    ))
    return styles


def _kpi_block(value: str, label: str, styles) -> Paragraph:
    return Paragraph(
        f'<font size="28" color="#1a1a2e"><b>{value}</b></font>'
        f'<br/><font size="9" color="#888888">{label}</font>',
        styles["Normal"],
    )


def _bar_row(label: str, count: int, max_count: int, styles) -> list:
    bar_width = int(180 * count / max(max_count, 1))
    bar = f'<font color="#2563eb">{"█" * bar_width}</font>'
    return [Paragraph(label, styles["TableCell"]),
            Paragraph(f"{bar} {count}", styles["TableCell"])]


def generate_dashboard_pdf(
    job: dict[str, Any],
    results: list[dict[str, Any]],
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )
    styles = _build_styles()
    elements: list = []

    query = job.get("query", "—")
    status = job.get("status", "—")
    found = job.get("found", 0)
    created = job.get("created_at", "")[:19].replace("T", " ")

    elements.append(Paragraph("Отчёт парсинга Яндекс Карт", styles["DashboardTitle"]))
    elements.append(Paragraph(
        f"Запрос: <b>{query}</b> &nbsp;|&nbsp; Статус: <b>{status}</b> &nbsp;|&nbsp; Дата: {created}",
        styles["DashboardSubtitle"],
    ))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#e5e7eb"), thickness=1))
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph("Сводка", styles["SectionHead"]))

    ratings = [float(r.get("rating", "0").replace(",", ".")) or 0 for r in results if r.get("rating")]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0
    total_phones = sum(len(r.get("phones", [])) for r in results)
    total_products = sum(len(r.get("products_and_services", [])) for r in results)
    websites = sum(1 for r in results if r.get("website"))

    all_cats: list[str] = []
    for r in results:
        cats = r.get("categories", [])
        if isinstance(cats, list):
            all_cats.extend(cats)
    cat_counts = Counter(all_cats)

    kpi_data = [[
        _kpi_block(str(found), "Найдено", styles),
        _kpi_block(f"{avg_rating:.1f}" if ratings else "—", "Ср. рейтинг", styles),
        _kpi_block(str(total_phones), "Телефонов", styles),
        _kpi_block(str(total_products), "Товаров", styles),
        _kpi_block(str(websites), "Сайтов", styles),
    ]]
    kpi_table = Table(kpi_data, colWidths=[doc.width / 5] * 5, rowHeights=[52])
    kpi_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 6 * mm))

    if cat_counts:
        elements.append(Paragraph("Категории", styles["SectionHead"]))
        top_cats = cat_counts.most_common(12)
        max_c = top_cats[0][1] if top_cats else 1
        cat_rows = [[
            Paragraph("Категория", styles["TableHeader"]),
            Paragraph("Кол-во", styles["TableHeader"]),
        ]]
        for cat, cnt in top_cats:
            cat_rows.append(_bar_row(cat, cnt, max_c, styles))
        cat_table = Table(cat_rows, colWidths=[doc.width * 0.55, doc.width * 0.45])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph("Найденные организации", styles["SectionHead"]))

    header = [
        Paragraph("#", styles["TableHeader"]),
        Paragraph("Название", styles["TableHeader"]),
        Paragraph("Адрес", styles["TableHeader"]),
        Paragraph("Телефон", styles["TableHeader"]),
        Paragraph("Рейтинг", styles["TableHeader"]),
        Paragraph("Товаров", styles["TableHeader"]),
    ]
    table_data = [header]
    for i, r in enumerate(results, 1):
        phones = r.get("phones", [])
        phone_str = phones[0] if phones else "—"
        if len(phone_str) > 20:
            phone_str = phone_str[:18] + "…"
        name = r.get("name", "—")
        if len(name) > 30:
            name = name[:28] + "…"
        addr = r.get("address", "—")
        if len(addr) > 40:
            addr = addr[:38] + "…"
        table_data.append([
            Paragraph(str(i), styles["TableCell"]),
            Paragraph(name, styles["TableCell"]),
            Paragraph(addr, styles["TableCell"]),
            Paragraph(phone_str, styles["TableCell"]),
            Paragraph(str(r.get("rating", "—")), styles["TableCell"]),
            Paragraph(str(len(r.get("products_and_services", []))), styles["TableCell"]),
        ])

    col_widths = [22, doc.width * 0.22, doc.width * 0.30, doc.width * 0.18, 40, 40]
    org_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    org_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(org_table)

    elements.append(Spacer(1, 10 * mm))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#e5e7eb"), thickness=0.5))
    elements.append(Paragraph(
        f"Парсер Яндекс Карт — {found} организаций — {created}",
        styles["DashboardSubtitle"],
    ))

    doc.build(elements)
    return buf.getvalue()
