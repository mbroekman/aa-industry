"""App Views"""

# Standard Library
import csv
from datetime import date

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext as _

from ...models import BuybackContract, BuybackProgram
from ...utils.buyback_stats import (
    CSV_HEADER,
    available_months,
    export_rows,
    get_program_stats,
    monthly_leaderboard,
    monthly_performance,
    top_item_groups,
    top_items,
)
from .member import _is_program_director


@login_required
@permission_required("industry_reforged.basic_access")
def buyback_stats(request: WSGIRequest) -> HttpResponse:
    """Per-program statistics: ISK/item leaderboards, a daily activity trend,
    and operational-health rates (flagged/rejected/expired, avg turnaround)."""
    try:
        days = int(request.GET.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    days = max(1, min(days, 365))

    programs = BuybackProgram.objects.visible_to(request.user).select_related(
        "corporation"
    )
    program_stats = [get_program_stats(program, days=days) for program in programs]
    director_program_ids = {
        program.id
        for program in programs
        if _is_program_director(request.user, program)
    }

    chart_data = {
        str(stats.program_id): {
            "labels": [point.date for point in stats.daily_trend],
            "submitted": [point.submitted_count for point in stats.daily_trend],
            "paidIsk": [float(point.paid_isk) for point in stats.daily_trend],
        }
        for stats in program_stats
    }

    context = {
        "title": _("Buyback Statistics"),
        "program_stats": program_stats,
        "director_program_ids": director_program_ids,
        "chart_data": chart_data,
        "days": days,
    }
    return render(request, "industry_reforged/buyback/stats.html", context)


def _parse_month(value: str | None) -> date | None:
    try:
        year, month = (int(part) for part in (value or "").split("-", 1))
        return date(year, month, 1)
    except (TypeError, ValueError):
        return None


@login_required
@permission_required("industry_reforged.basic_access")
def buyback_leaderboard(request: WSGIRequest) -> HttpResponse:
    """Monthly ranking of sellers by ISK paid out, per visible program."""
    programs = list(
        BuybackProgram.objects.visible_to(request.user)
        .select_related("corporation")
        .order_by("name")
    )
    program = programs[0] if programs else None
    if request.GET.get("program"):
        try:
            wanted = int(request.GET["program"])
        except ValueError as exc:
            raise Http404 from exc
        program = next((p for p in programs if p.id == wanted), None)
        if program is None:
            raise Http404

    months = available_months(program) if program else []
    month = _parse_month(request.GET.get("month"))
    if month is None:
        today = timezone.localdate()
        month = months[0] if months else date(today.year, today.month, 1)
    if month not in months:
        months = sorted([*months, month], reverse=True)

    rows = monthly_leaderboard(program, month.year, month.month) if program else []
    context = {
        "title": _("Buyback Leaderboard"),
        "programs": programs,
        "program": program,
        "months": months,
        "month": month,
        "rows": rows,
        "total_isk": sum((row.isk_paid for row in rows), 0),
        "total_donated": sum((row.donated for row in rows), 0),
    }
    return render(request, "industry_reforged/buyback/leaderboard.html", context)


def _director_program_or_404(request, program_id: int) -> BuybackProgram:
    program = get_object_or_404(
        BuybackProgram.objects.select_related("corporation", "wallet_division"),
        id=program_id,
    )
    if not _is_program_director(request.user, program):
        raise Http404
    return program


@login_required
@permission_required("industry_reforged.corp_access")
def buyback_performance(request: WSGIRequest, program_id: int) -> HttpResponse:
    """Director view of one program: 12 months of activity and payouts, the
    item groups and items it buys most, and the funding wallet's balance."""
    program = _director_program_or_404(request, program_id)
    performance = monthly_performance(program, months=12)
    statuses = [code for code, _label in BuybackContract.STATUS_CHOICES]

    chart_data = {
        "labels": [row.month.strftime("%Y-%m") for row in performance],
        "submitted": [row.submitted for row in performance],
        "paidIsk": [float(row.isk_paid) for row in performance],
        "donated": [float(row.donated) for row in performance],
    }
    context = {
        "title": _("%(name)s - performance") % {"name": program.name},
        "program": program,
        "wallet": program.wallet_division,
        "statuses": statuses,
        "performance": [
            (row, [row.by_status.get(status, 0) for status in statuses])
            for row in reversed(performance)
        ],
        "top_groups": top_item_groups(program, months=3),
        "top_items": top_items(program, months=3),
        "chart_data": chart_data,
    }
    return render(request, "industry_reforged/buyback/performance.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def buyback_export_csv(request: WSGIRequest, program_id: int) -> HttpResponse:
    """All paid contract lines of a program as CSV, for the program's directors."""
    program = _director_program_or_404(request, program_id)
    filename = f"buyback-{slugify(program.name) or program.id}-{timezone.localdate():%Y%m%d}.csv"

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(CSV_HEADER)
    for row in export_rows(program):
        writer.writerow(row)
    return response
