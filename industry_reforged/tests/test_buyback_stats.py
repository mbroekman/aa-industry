# Standard Library
from datetime import timedelta
from decimal import Decimal

# Third Party
import pytest

# Django
from django.utils import timezone

# AA Industry App
from industry_reforged.models import BuybackContract, LedgerTransaction
from industry_reforged.utils.buyback_stats import get_program_stats

from .factories import (
    BuybackContractFactory,
    BuybackContractItemFactory,
    BuybackProgramFactory,
    EveCharacterFactory,
    EveTypeFactory,
)


def _set_timestamps(contract, created_at, updated_at):
    BuybackContract.objects.filter(pk=contract.pk).update(
        created_at=created_at, updated_at=updated_at
    )


def _pay(contract, amount):
    LedgerTransaction.objects.create(
        transaction_type="BUYBACK_PAYOUT",
        amount=amount,
        character=contract.character,
        reference=contract.tracking_number,
        buyback_contract=contract,
    )


@pytest.mark.django_db
class TestGetProgramStats:
    def test_empty_program_returns_zeros(self):
        program = BuybackProgramFactory()
        stats = get_program_stats(program)

        assert stats.total_contracts == 0
        assert stats.contracts_by_status == {}
        assert stats.total_isk_paid == Decimal("0.00")
        assert stats.total_items_sold == 0
        assert stats.avg_contract_value == Decimal("0.00")
        assert stats.flag_rate == 0.0
        assert stats.rejection_rate == 0.0
        assert stats.expiry_rate == 0.0
        assert stats.avg_turnaround_hours is None
        assert stats.top_items == []
        assert stats.top_sellers == []
        assert len(stats.daily_trend) == 30

    def test_contracts_by_status_counts(self):
        program = BuybackProgramFactory()
        BuybackContractFactory(program=program, status="PENDING")
        BuybackContractFactory(program=program, status="PENDING")
        BuybackContractFactory(program=program, status="PAID")

        stats = get_program_stats(program)
        assert stats.contracts_by_status == {"PENDING": 2, "PAID": 1}
        assert stats.total_contracts == 3

    def test_total_isk_paid_and_avg_contract_value(self):
        program = BuybackProgramFactory()
        c1 = BuybackContractFactory(program=program, status="PAID")
        c2 = BuybackContractFactory(program=program, status="PAID")
        _pay(c1, Decimal("1000.00"))
        _pay(c2, Decimal("3000.00"))

        stats = get_program_stats(program)
        assert stats.total_isk_paid == Decimal("4000.00")
        assert stats.avg_contract_value == Decimal("2000.00")

    def test_items_sold_only_counted_for_paid_contracts(self):
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory()
        paid = BuybackContractFactory(program=program, status="PAID")
        pending = BuybackContractFactory(program=program, status="PENDING")
        BuybackContractItemFactory(contract=paid, eve_type=eve_type, quantity=100)
        BuybackContractItemFactory(contract=pending, eve_type=eve_type, quantity=999)

        stats = get_program_stats(program)
        assert stats.total_items_sold == 100

    def test_flag_rate_excludes_pending(self):
        program = BuybackProgramFactory()
        BuybackContractFactory(program=program, status="PENDING", flag_price_mismatch=True)  # excluded
        BuybackContractFactory(program=program, status="MATCHED")  # not flagged
        BuybackContractFactory(program=program, status="FLAGGED", flag_item_mismatch=True)  # flagged

        stats = get_program_stats(program)
        # resolved = MATCHED + FLAGGED = 2, flagged = 1 -> 50%
        assert stats.flag_rate == 50.0

    def test_rejection_and_expiry_rate(self):
        program = BuybackProgramFactory()
        BuybackContractFactory(program=program, status="PAID")
        BuybackContractFactory(program=program, status="REJECTED")
        BuybackContractFactory(program=program, status="EXPIRED")

        stats = get_program_stats(program)
        # resolved = 3 total
        assert stats.rejection_rate == pytest.approx(33.333, rel=0.01)
        assert stats.expiry_rate == pytest.approx(33.333, rel=0.01)

    def test_avg_turnaround_hours(self):
        program = BuybackProgramFactory()
        c1 = BuybackContractFactory(program=program, status="PAID")
        c2 = BuybackContractFactory(program=program, status="PAID")
        now = timezone.now()
        _set_timestamps(c1, now - timedelta(hours=10), now)  # 10h
        _set_timestamps(c2, now - timedelta(hours=20), now)  # 20h

        stats = get_program_stats(program)
        assert stats.avg_turnaround_hours == pytest.approx(15.0, rel=0.01)

    def test_avg_turnaround_none_without_terminal_contracts(self):
        program = BuybackProgramFactory()
        BuybackContractFactory(program=program, status="PENDING")
        BuybackContractFactory(program=program, status="MATCHED")

        stats = get_program_stats(program)
        assert stats.avg_turnaround_hours is None

    def test_top_items_ordered_by_value_and_limited(self):
        program = BuybackProgramFactory()
        paid = BuybackContractFactory(program=program, status="PAID")
        cheap = EveTypeFactory(name="Cheap Item")
        expensive = EveTypeFactory(name="Expensive Item")
        BuybackContractItemFactory(contract=paid, eve_type=cheap, quantity=1000, unit_price=Decimal("1.00"))
        BuybackContractItemFactory(contract=paid, eve_type=expensive, quantity=1, unit_price=Decimal("5000.00"))

        stats = get_program_stats(program, top_n=1)
        assert len(stats.top_items) == 1
        assert stats.top_items[0].eve_type_name == "Expensive Item"
        assert stats.top_items[0].total_value == Decimal("5000.00")

    def test_top_sellers_ordered_by_total_paid(self):
        program = BuybackProgramFactory()
        alice = EveCharacterFactory(character_name="Alice")
        bob = EveCharacterFactory(character_name="Bob")
        c1 = BuybackContractFactory(program=program, status="PAID", character=alice)
        c2 = BuybackContractFactory(program=program, status="PAID", character=bob)
        _pay(c1, Decimal("500.00"))
        _pay(c2, Decimal("5000.00"))

        stats = get_program_stats(program)
        assert stats.top_sellers[0].character_name == "Bob"
        assert stats.top_sellers[0].total_paid == Decimal("5000.00")
        assert stats.top_sellers[1].character_name == "Alice"

    def test_daily_trend_zero_filled_and_windowed(self):
        program = BuybackProgramFactory()
        c1 = BuybackContractFactory(program=program, status="PAID")
        now = timezone.now()
        _set_timestamps(c1, now, now)
        _pay(c1, Decimal("100.00"))

        stats = get_program_stats(program, days=7)
        assert len(stats.daily_trend) == 7
        today_point = stats.daily_trend[-1]
        assert today_point.date == now.date().isoformat()
        assert today_point.submitted_count == 1
        assert today_point.paid_isk == Decimal("100.00")
        # Earlier days with no activity are zero-filled, not omitted.
        assert stats.daily_trend[0].submitted_count == 0
        assert stats.daily_trend[0].paid_isk == Decimal("0.00")

    def test_stats_scoped_to_own_program_only(self):
        program_a = BuybackProgramFactory()
        program_b = BuybackProgramFactory()
        BuybackContractFactory(program=program_a, status="PAID")
        BuybackContractFactory(program=program_b, status="PAID")
        BuybackContractFactory(program=program_b, status="PAID")

        stats_a = get_program_stats(program_a)
        assert stats_a.total_contracts == 1

    def test_total_donated_only_counts_paid_contracts(self):
        program = BuybackProgramFactory()
        BuybackContractFactory(program=program, status="PAID", donation_amount=Decimal("500.00"))
        BuybackContractFactory(program=program, status="PENDING", donation_amount=Decimal("999.00"))

        stats = get_program_stats(program)
        assert stats.total_donated == Decimal("500.00")

    def test_top_donors_excludes_zero_donations_and_orders_by_amount(self):
        program = BuybackProgramFactory()
        alice = EveCharacterFactory(character_name="Alice")
        bob = EveCharacterFactory(character_name="Bob")
        carol = EveCharacterFactory(character_name="Carol")
        BuybackContractFactory(program=program, status="PAID", character=alice, donation_amount=Decimal("100.00"))
        BuybackContractFactory(program=program, status="PAID", character=bob, donation_amount=Decimal("1000.00"))
        BuybackContractFactory(program=program, status="PAID", character=carol, donation_amount=Decimal("0.00"))

        stats = get_program_stats(program)
        donor_names = [d.character_name for d in stats.top_donors]
        assert donor_names == ["Bob", "Alice"]
        assert "Carol" not in donor_names
