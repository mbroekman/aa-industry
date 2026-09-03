# Standard Library
from decimal import Decimal

# Third Party
import pytest

# Django
from django.utils import timezone

from .factories import (
    CharacterIndustryJobFactory,
    CorporationIndustryJobFactory,
    EveCharacterFactory,
    EveTypeFactory,
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


@pytest.mark.django_db
class TestCharacterPlanetModel:
    def test_factory_depletion_time_with_resources(self):
        # AA Industry App
        from industry_reforged.models import (
            CharacterPlanet,
            PISchematic,
            PISchematicInput,
            PISchematicOutput,
            PlanetPin,
        )

        character = EveCharacterFactory()

        planet = CharacterPlanet.objects.create(
            character=character,
            planet_id=40000001,
            system_id=30000142,
            last_update=timezone.now(),
        )

        input_type = EveTypeFactory(name="Robotics Inputs")
        output_type = EveTypeFactory(name="Robotics")
        factory_type = EveTypeFactory(name="Advanced Industry Facility")
        storage_type = EveTypeFactory(name="Launchpad")

        schematic, _ = PISchematic.objects.get_or_create(
            schematic_id=101,
            defaults={
                "name": "Robotics Schematic",
                "cycle_time": 3600,
            },
        )
        PISchematicInput.objects.create(
            schematic=schematic, type=input_type, quantity=10
        )
        PISchematicOutput.objects.create(
            schematic=schematic, type=output_type, quantity=3
        )

        # Factory pin (even if last_cycle_start was in the past)
        PlanetPin.objects.create(
            planet=planet,
            pin_id=1,
            type=factory_type,
            schematic_id=101,
            last_cycle_start=timezone.now() - timezone.timedelta(days=2),
        )

        # Storage pin with 100 units of input material
        PlanetPin.objects.create(
            planet=planet,
            pin_id=2,
            type=storage_type,
            contents={
                input_type.name: {
                    "type_id": input_type.id,
                    "amount": 100,
                    "volume": 10.0,
                }
            },
        )

        # Consumption is 10 units/hour, available is 100 -> 10 hours remaining
        depletion_time = planet.factory_depletion_time
        assert depletion_time is not None
        diff_hours = (
            depletion_time - planet.factory_baseline_time
        ).total_seconds() / 3600
        assert round(diff_hours, 1) == 10.0

    def test_factory_depleted_status_and_categorized_contents(self):
        # AA Industry App
        from industry_reforged.models import (
            CharacterPlanet,
            PISchematic,
            PISchematicInput,
            PISchematicOutput,
            PlanetPin,
        )

        character = EveCharacterFactory()

        # Planet updated 5 hours ago
        planet = CharacterPlanet.objects.create(
            character=character,
            planet_id=40000002,
            system_id=30000142,
            last_update=timezone.now() - timezone.timedelta(hours=5),
        )

        input_type = EveTypeFactory(name="Synthetic Oil")
        output_type = EveTypeFactory(name="Cryoprotectant")
        factory_type = EveTypeFactory(name="Advanced Industry Facility")
        storage_type = EveTypeFactory(name="Launchpad")

        schematic, _ = PISchematic.objects.update_or_create(
            schematic_id=99999,
            defaults={
                "name": "Cryoprotectant Schematic",
                "cycle_time": 3600,
            },
        )
        schematic.inputs.all().delete()
        schematic.outputs.all().delete()
        PISchematicInput.objects.create(
            schematic=schematic, type=input_type, quantity=10
        )
        PISchematicOutput.objects.create(
            schematic=schematic, type=output_type, quantity=2
        )

        factory_pin = PlanetPin.objects.create(
            planet=planet,
            pin_id=10,
            type=factory_type,
            product_type=output_type,
            schematic_id=99999,
        )

        # 100 units of input -> 10 hours of runtime from 5 hours ago -> 5 hours left
        storage_pin = PlanetPin.objects.create(
            planet=planet,
            pin_id=20,
            type=storage_type,
            contents={
                input_type.name: {
                    "type_id": input_type.id,
                    "amount": 100,
                    "volume": 38.0,
                }
            },
        )

        # Planet updated 5 hours ago (use .update to bypass auto_now=True)
        CharacterPlanet.objects.filter(id=planet.id).update(
            last_update=timezone.now() - timezone.timedelta(hours=5)
        )
        planet.refresh_from_db()
        storage_pin.refresh_from_db()
        factory_pin.refresh_from_db()

        assert not planet.is_factory_depleted
        assert factory_pin.status_label == "Running"

        # Check categorized contents: 5 cycles ran (5 hours * 10 = 50 consumed, 5 * 2 = 10 produced)
        contents = storage_pin.categorized_contents
        assert len(contents["produced"]) == 1
        assert contents["produced"][0]["name"] == output_type.name
        assert contents["produced"][0]["amount"] == 10  # 5 cycles * 2

        assert len(contents["resources"]) == 1
        assert contents["resources"][0]["name"] == input_type.name
        assert contents["resources"][0]["amount"] == 50  # 100 - 50 consumed

        # Now test when planet has run out of resources (e.g. 15 hours elapsed)
        CharacterPlanet.objects.filter(id=planet.id).update(
            last_update=timezone.now() - timezone.timedelta(hours=15)
        )
        planet.refresh_from_db()
        storage_pin.refresh_from_db()
        factory_pin.refresh_from_db()

        assert planet.is_factory_depleted
        assert factory_pin.status_label == "Out of Resources"

        grouped = planet.grouped_factories
        assert len(grouped["advanced"]) == 1
        assert grouped["advanced"][0]["status_label"] == "Out of Resources"
        assert grouped["advanced"][0]["is_idle"] is True
