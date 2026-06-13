"""Synchronous (in-request) report generation with WeasyPrint.

Pulls from the reporting SQL views for the report's period and renders an HTML
template → PDF. Kept import-light: WeasyPrint is imported lazily so the rest of the
backend runs without its system libraries installed (e.g. during tests).
"""
from django.core.files.base import ContentFile
from django.db import connection
from django.template.loader import render_to_string


def _dictfetch(sql, params):
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [c[0] for c in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception:
        # Views may not exist (e.g. SQLite dev DB); degrade gracefully.
        return []


def gather_report_context(report):
    project = report.project
    pid = project.id
    physical = _dictfetch(
        "SELECT * FROM v_indicator_progress WHERE project_id = %s AND period_year = %s",
        [pid, report.period_year],
    )
    finance_cat = _dictfetch(
        "SELECT * FROM v_financial_by_category WHERE project_id = %s AND fiscal_year = %s",
        [pid, report.period_year],
    )
    finance_comp = _dictfetch(
        "SELECT * FROM v_financial_by_component WHERE project_id = %s AND fiscal_year = %s",
        [pid, report.period_year],
    )
    procurement = _dictfetch(
        "SELECT * FROM v_procurement_status WHERE project_id = %s", [pid]
    )
    return {
        "report": report,
        "project": project,
        "physical": physical,
        "finance_category": finance_cat,
        "finance_component": finance_comp,
        "procurement": procurement,
    }


def generate_report_pdf(report):
    context = gather_report_context(report)
    html = render_to_string("reporting/quarterly_report.html", context)
    try:
        from weasyprint import HTML

        pdf_bytes = HTML(string=html).write_pdf()
    except Exception:
        # WeasyPrint unavailable: fall back to storing the HTML so the flow still works.
        pdf_bytes = html.encode("utf-8")
        report.file.save(f"report_{report.id}.html", ContentFile(pdf_bytes), save=True)
        return report
    report.file.save(f"report_{report.id}.pdf", ContentFile(pdf_bytes), save=True)
    return report
