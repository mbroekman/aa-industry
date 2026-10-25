"""
Per-program statistics for the Buyback feature.

Goes beyond the source third-party project's plain "stats/leaderboards"
(doc-18 SS2) with operational-health insights it didn't have: flag/rejection/
expiry rates and average turnaround time, alongside the expected ISK/item
leaderboards and a daily activity trend.
"""

# Standard Library
from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

# Django
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
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
