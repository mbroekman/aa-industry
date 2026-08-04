# Standard Library
from decimal import Decimal

# Third Party
import pytest

# Django
from django.utils import timezone

from .factories import (
    CharacterIndustryJobFactory,
    CorporationIndustryJobFactory,
    IndustryFacilityFactory,
    MemberOrderFactory,
    OrderItemFactory,
)


@pytest.mark.django_db
class TestIndustryFacilityModel:
    def test_create_facility(self):
        facility = IndustryFacilityFactory(name="Test Facility")
        assert facility.name == "Test Facility"
        assert facility.facility_id is not None


@pytest.mark.django_db
class TestCharacterIndustryJob:
    def test_str(self):
        job = CharacterIndustryJobFactory(job_id=123, character__character_name="Bob")
        assert str(job) == "Bob - Job 123"

    def test_activity_name(self):
        job = CharacterIndustryJobFactory(activity_id=1)
        assert job.activity_name == "Manufacturing"
        job.activity_id = 999
        assert job.activity_name == "Activity 999"

    def test_is_ready(self):
        # Test ready status
        job = CharacterIndustryJobFactory(status="ready")
        assert job.is_ready is True

        # Test active status with end date in the past
        job = CharacterIndustryJobFactory(
            status="active", end_date=timezone.now() - timezone.timedelta(days=1)
        )
        assert job.is_ready is True

        # Test active status with end date in the future
        job = CharacterIndustryJobFactory(
            status="active", end_date=timezone.now() + timezone.timedelta(days=1)
        )
        assert job.is_ready is False


@pytest.mark.django_db
class TestCorporationIndustryJob:
    def test_str(self):
        job = CorporationIndustryJobFactory(
            job_id=456, corporation__corporation_name="My Corp"
        )
        assert str(job) == "My Corp - Job 456"

    def test_activity_name(self):
        job = CorporationIndustryJobFactory(activity_id=8)
        assert job.activity_name == "Invention"

    def test_is_ready(self):
        job = CorporationIndustryJobFactory(status="active", end_date=None)
        assert job.is_ready is False


@pytest.mark.django_db
class TestMemberOrder:
    def test_str(self):
        order = MemberOrderFactory(
            character__character_name="Alice", status="REQUESTED"
        )
        assert "Order #" in str(order)
        assert "Alice" in str(order)
        assert "REQUESTED" in str(order)

    def test_remaining_balance(self):
        order = MemberOrderFactory(
            total_price=Decimal("1000.0"), amount_paid=Decimal("250.0")
        )
        assert order.remaining_balance == Decimal("750.0")

    def test_grand_total(self):
        parent = MemberOrderFactory(total_price=Decimal("500.0"))
        MemberOrderFactory(parent_order=parent, total_price=Decimal("300.0"))
        MemberOrderFactory(parent_order=parent, total_price=Decimal("200.0"))
        assert parent.grand_total == Decimal("1000.0")

    def test_save_propagates_status(self):
        parent = MemberOrderFactory(status="REQUESTED")
        child1 = MemberOrderFactory(parent_order=parent, status="REQUESTED")

        parent.status = "ACCEPTED"
        parent.save()

        child1.refresh_from_db()
        assert child1.status == "ACCEPTED"


@pytest.mark.django_db
class TestOrderItem:
    def test_line_total(self):
        item = OrderItemFactory(quantity=5, price_per_unit=Decimal("100.0"))
        assert item.line_total == Decimal("500.0")

    def test_original_price_per_unit(self):
        # 10% discount means original price was 100 / 0.9 = 111.11...
        item = OrderItemFactory(
            price_per_unit=Decimal("90.0"), discount_applied=Decimal("10.0")
        )
        assert round(item.original_price_per_unit, 2) == Decimal("100.00")
