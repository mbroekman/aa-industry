"""App Views"""

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _

from ...models import BuybackProgram
from ...utils.buyback_stats import get_program_stats


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

    programs = BuybackProgram.objects.filter(is_active=True).select_related("corporation")
    program_stats = [get_program_stats(program, days=days) for program in programs]

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
        "chart_data": chart_data,
        "days": days,
    }
    return render(request, "industry_reforged/buyback/stats.html", context)
