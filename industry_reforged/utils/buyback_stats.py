"""
Per-program statistics for the Buyback feature.

Goes beyond the source third-party project's plain "stats/leaderboards"
(doc-18 SS2) with operational-health insights it didn't have: flag/rejection/
expiry rates and average turnaround time, alongside the expected ISK/item
leaderboards and a daily activity trend.
"""

# Standard Library
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

# Django
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

TERMINAL_STATUSES = ("PAID", "REJECTED", "EXPIRED", "CANCELLED")
RESOLVED_STATUSES = (
    "MATCHED",
    "FLAGGED",
    "PAID",
    "REJECTED",
    "EXPIRED",
    "CANCELLED",
)


@dataclass
class ItemStat:
    eve_type_id: int
    eve_type_name: str
    total_quantity: int
    total_value: Decimal


@dataclass
class SellerStat:
    character_id: int
    character_name: str
    total_paid: Decimal
    contract_count: int


@dataclass
class DonorStat:
    character_id: int
    character_name: str
    total_donated: Decimal
    contract_count: int


@dataclass
class DailyStat:
    date: str
    submitted_count: int
    paid_isk: Decimal


@dataclass
class ProgramStats:
    program_id: int
    program_name: str
    total_contracts: int
    contracts_by_status: dict = field(default_factory=dict)
    total_isk_paid: Decimal = Decimal("0.00")
    total_items_sold: int = 0
    avg_contract_value: Decimal = Decimal("0.00")
    total_donated: Decimal = Decimal("0.00")
    flag_rate: float = 0.0
    rejection_rate: float = 0.0
    expiry_rate: float = 0.0
    avg_turnaround_hours: float | None = None
    top_items: list = field(default_factory=list)
    top_sellers: list = field(default_factory=list)
    top_donors: list = field(default_factory=list)
    daily_trend: list = field(default_factory=list)


def get_program_stats(program, days: int = 30, top_n: int = 10) -> ProgramStats:
    """Compute aggregate statistics for a single BuybackProgram."""
    # Local import avoids a circular import (models/buyback.py doesn't import this module).
    from ..models import BuybackContract, BuybackContractItem, LedgerTransaction

    contracts = BuybackContract.objects.filter(program=program)
    total_contracts = contracts.count()

    contracts_by_status = {
        row["status"]: row["count"]
        for row in contracts.values("status").annotate(count=Count("id"))
    }

    paid_contracts_qs = contracts.filter(status="PAID")
    payout_qs = LedgerTransaction.objects.filter(
        buyback_contract__program=program, transaction_type="BUYBACK_PAYOUT"
    )
    total_isk_paid = payout_qs.aggregate(total=Sum("amount"))["total"] or Decimal(
        "0.00"
    )
    paid_count = paid_contracts_qs.count()
    avg_contract_value = (
        (total_isk_paid / paid_count) if paid_count else Decimal("0.00")
    )

    total_items_sold = (
        BuybackContractItem.objects.filter(contract__in=paid_contracts_qs).aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )

    total_donated = paid_contracts_qs.aggregate(total=Sum("donation_amount"))[
        "total"
    ] or Decimal("0.00")

    resolved_qs = contracts.filter(status__in=RESOLVED_STATUSES)
    resolved_count = resolved_qs.count()
    flagged_count = resolved_qs.filter(
        Q(flag_item_mismatch=True)
        | Q(flag_price_mismatch=True)
        | Q(flag_structure_mismatch=True)
        | Q(flag_receiver_mismatch=True)
        | Q(flag_title_tampered=True)
        | Q(flag_no_tracking=True)
    ).count()
    rejected_count = contracts.filter(status="REJECTED").count()
    expired_count = contracts.filter(status="EXPIRED").count()

    flag_rate = (flagged_count / resolved_count * 100) if resolved_count else 0.0
    rejection_rate = (rejected_count / resolved_count * 100) if resolved_count else 0.0
    expiry_rate = (expired_count / resolved_count * 100) if resolved_count else 0.0

    # Computed in Python rather than via a DB-side Avg(DurationField) aggregate,
    # which isn't portable across SQLite/PostgreSQL/MySQL - buyback contract
    # volume per program is modest, so this is cheap enough.
    terminal_timestamps = contracts.filter(status__in=TERMINAL_STATUSES).values_list(
        "created_at", "updated_at"
    )
    durations_hours = [
        (updated - created).total_seconds() / 3600.0
        for created, updated in terminal_timestamps
        if updated and created
    ]
    avg_turnaround_hours = (
        (sum(durations_hours) / len(durations_hours)) if durations_hours else None
    )

    top_items = [
        ItemStat(
            eve_type_id=row["eve_type_id"],
            eve_type_name=row["eve_type__name"],
            total_quantity=row["total_qty"],
            total_value=row["total_value"] or Decimal("0.00"),
        )
        for row in (
            BuybackContractItem.objects.filter(contract__in=paid_contracts_qs)
            .values("eve_type_id", "eve_type__name")
            .annotate(
                total_qty=Sum("quantity"),
                total_value=Sum(F("quantity") * F("unit_price")),
            )
            .order_by("-total_value")[:top_n]
        )
    ]

    top_sellers = [
        SellerStat(
            character_id=row["character_id"],
            character_name=row["character__character_name"] or "Unknown",
            total_paid=row["total_paid"] or Decimal("0.00"),
            contract_count=row["contract_count"],
        )
        for row in (
            payout_qs.values("character_id", "character__character_name")
            .annotate(total_paid=Sum("amount"), contract_count=Count("id"))
            .order_by("-total_paid")[:top_n]
        )
    ]

    top_donors = [
        DonorStat(
            character_id=row["character_id"],
            character_name=row["character__character_name"] or "Unknown",
            total_donated=row["total_donated"],
            contract_count=row["contract_count"],
        )
        for row in (
            paid_contracts_qs.filter(donation_amount__gt=0)
            .values("character_id", "character__character_name")
            .annotate(total_donated=Sum("donation_amount"), contract_count=Count("id"))
            .order_by("-total_donated")[:top_n]
        )
    ]

    daily_trend = _build_daily_trend(contracts, payout_qs, days)

    return ProgramStats(
        program_id=program.id,
        program_name=program.name,
        total_contracts=total_contracts,
        contracts_by_status=contracts_by_status,
        total_isk_paid=total_isk_paid,
        total_items_sold=total_items_sold,
        avg_contract_value=avg_contract_value,
        total_donated=total_donated,
        flag_rate=flag_rate,
        rejection_rate=rejection_rate,
        expiry_rate=expiry_rate,
        avg_turnaround_hours=avg_turnaround_hours,
        top_items=top_items,
        top_sellers=top_sellers,
        top_donors=top_donors,
        daily_trend=daily_trend,
    )


def _build_daily_trend(contracts_qs, payout_qs, days: int) -> list:
    """Zero-filled daily series for the last `days` days: how many contracts
    were submitted, and how much ISK was paid out, each day."""
    cutoff = timezone.now() - timedelta(days=days)

    submitted_by_day = {
        row["day"]: row["count"]
        for row in (
            contracts_qs.filter(created_at__gte=cutoff)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
        )
    }
    paid_by_day = {
        row["day"]: row["total"]
        for row in (
            payout_qs.filter(date__gte=cutoff)
            .annotate(day=TruncDate("date"))
            .values("day")
            .annotate(total=Sum("amount"))
        )
    }

    today = timezone.now().date()
    trend = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        trend.append(
            DailyStat(
                date=day.isoformat(),
                submitted_count=submitted_by_day.get(day, 0),
                paid_isk=paid_by_day.get(day, Decimal("0.00")),
            )
        )
    return trend


# --- Monthly leaderboard, performance and export (TASK-277) -----------------
#
# Payouts are dated by their ledger entry (when the contract was paid), so a
# contract submitted in March and paid in April counts for April.


@dataclass
class LeaderboardRow:
    rank: int
    character_id: int | None
    character_name: str
    isk_paid: Decimal
    donated: Decimal
    contract_count: int


def _payouts(program):
    from ..models import LedgerTransaction

    return LedgerTransaction.objects.filter(
        transaction_type="BUYBACK_PAYOUT", buyback_contract__program=program
    )


def available_months(program) -> list[date]:
    """First day of every month with at least one payout, newest first."""
    months = (
        _payouts(program)
        .annotate(month=TruncMonth("date"))
        .values_list("month", flat=True)
        .distinct()
    )
    return sorted({_as_date(m) for m in months if m}, reverse=True)


def _as_date(value) -> date:
    return value.date() if isinstance(value, datetime) else value


def monthly_leaderboard(program, year: int, month: int) -> list[LeaderboardRow]:
    rows = (
        _payouts(program)
        .filter(date__year=year, date__month=month)
        .values(
            "buyback_contract__character_id",
            "buyback_contract__character__character_name",
        )
        .annotate(
            isk_paid=Sum("amount"),
            donated=Sum("buyback_contract__donation_amount"),
            contract_count=Count("id"),
        )
        .order_by("-isk_paid")
    )
    return [
        LeaderboardRow(
            rank=index,
            character_id=row["buyback_contract__character_id"],
            character_name=row["buyback_contract__character__character_name"]
            or "-",
            isk_paid=row["isk_paid"] or Decimal("0.00"),
            donated=row["donated"] or Decimal("0.00"),
            contract_count=row["contract_count"],
        )
        for index, row in enumerate(rows, start=1)
    ]


@dataclass
class MonthPerformance:
    month: date
    submitted: int = 0
    by_status: dict = field(default_factory=dict)
    paid_count: int = 0
    isk_paid: Decimal = Decimal("0.00")
    donated: Decimal = Decimal("0.00")


def _month_starts(months: int) -> list[date]:
    """First day of the last `months` months, oldest first, ending this month."""
    today = timezone.localdate()
    year, month = today.year, today.month
    starts = []
    for _ in range(months):
        starts.append(date(year, month, 1))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(starts))


def monthly_performance(program, months: int = 12) -> list[MonthPerformance]:
    """Per month: contracts submitted (by status) and ISK/donations paid out."""
    from ..models import BuybackContract

    starts = _month_starts(months)
    rows = {start: MonthPerformance(month=start) for start in starts}
    since = starts[0]

    for row in (
        BuybackContract.objects.filter(program=program, created_at__date__gte=since)
        .annotate(month=TruncMonth("created_at"))
        .values("month", "status")
        .annotate(count=Count("id"))
    ):
        perf = rows.get(_as_date(row["month"]))
        if perf:
            perf.submitted += row["count"]
            perf.by_status[row["status"]] = row["count"]

    for row in (
        _payouts(program)
        .filter(date__date__gte=since)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(
            isk=Sum("amount"),
            donated=Sum("buyback_contract__donation_amount"),
            count=Count("id"),
        )
    ):
        perf = rows.get(_as_date(row["month"]))
        if perf:
            perf.isk_paid = row["isk"] or Decimal("0.00")
            perf.donated = row["donated"] or Decimal("0.00")
            perf.paid_count = row["count"]

    return [rows[start] for start in starts]


@dataclass
class ValueRow:
    name: str
    isk: Decimal
    quantity: int


def _paid_items(program, months: int):
    from ..models import BuybackContractItem

    since = _month_starts(months)[0]
    return BuybackContractItem.objects.filter(
        contract__program=program,
        contract__status="PAID",
        contract__ledger_transactions__transaction_type="BUYBACK_PAYOUT",
        contract__ledger_transactions__date__date__gte=since,
    )


def top_item_groups(program, months: int = 3, limit: int = 10) -> list[ValueRow]:
    """Item groups paid out most, by ISK, over the last `months` months."""
    return _top_by(program, "eve_type__eve_group__name", months, limit)


def top_items(program, months: int = 3, limit: int = 10) -> list[ValueRow]:
    return _top_by(program, "eve_type__name", months, limit)


def _top_by(program, name_field: str, months: int, limit: int) -> list[ValueRow]:
    rows = (
        _paid_items(program, months)
        .values(name_field)
        .annotate(isk=Sum(F("unit_price") * F("quantity")), quantity=Sum("quantity"))
        .order_by("-isk")[:limit]
    )
    return [
        ValueRow(
            name=row[name_field] or "-",
            isk=row["isk"] or Decimal("0.00"),
            quantity=row["quantity"] or 0,
        )
        for row in rows
    ]


CSV_HEADER = [
    "tracking_number",
    "submitted",
    "paid",
    "seller",
    "item",
    "item_group",
    "quantity",
    "unit_price",
    "line_isk",
]


def export_rows(program):
    """One row per item of every paid contract, oldest payout first."""
    from ..models import BuybackContractItem

    items = (
        BuybackContractItem.objects.filter(
            contract__program=program,
            contract__status="PAID",
            contract__ledger_transactions__transaction_type="BUYBACK_PAYOUT",
        )
        .select_related("contract__character", "eve_type__eve_group")
        .annotate(paid=F("contract__ledger_transactions__date"))
        .order_by("paid", "contract_id", "id")
    )
    for item in items:
        contract = item.contract
        yield [
            contract.tracking_number,
            timezone.localtime(contract.created_at).strftime("%Y-%m-%d %H:%M"),
            timezone.localtime(item.paid).strftime("%Y-%m-%d %H:%M"),
            contract.character.character_name if contract.character else "",
            item.eve_type.name,
            item.eve_type.eve_group.name if item.eve_type.eve_group_id else "",
            item.quantity,
            f"{item.unit_price:.2f}",
            f"{item.unit_price * item.quantity:.2f}",
        ]
