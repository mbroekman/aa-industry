"""Root-location resolution for corp assets and spare stock on claimed jobs."""

# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# AA Industry App
from industry_reforged.models import (
    CorporationIndustryJob,
    CorpInventory,
    IndustryFacility,
    MemberOrder,
    TaskJobLink,
)
from industry_reforged.tests.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveTypeFactory,
    ProductionTaskFactory,
)
from industry_reforged.utils.locations import resolve_root_location
from industry_reforged.utils.spare_stock import annotate_spare_stock

SYSTEM = 30004582
FOUNDRY = 1043380432539
CONTAINER = 1050000000001
NESTED = 1050000000002


class TestResolveRootLocation:
    def test_container_in_owned_structure_resolves_to_structure(self):
        # The corp owns the structure, so it is itself an asset in the system.
        item_locations = {FOUNDRY: SYSTEM, CONTAINER: FOUNDRY, NESTED: CONTAINER}
        assert resolve_root_location(NESTED, item_locations) == FOUNDRY
        assert resolve_root_location(CONTAINER, item_locations) == FOUNDRY
        assert resolve_root_location(FOUNDRY, item_locations) == FOUNDRY

    def test_hangar_of_foreign_structure_stays_put(self):
        assert resolve_root_location(FOUNDRY, {CONTAINER: FOUNDRY}) == FOUNDRY

    def test_circular_reference_terminates(self):
        assert resolve_root_location(CONTAINER, {CONTAINER: NESTED, NESTED: CONTAINER}) in (
            CONTAINER,
            NESTED,
        )


@pytest.mark.django_db
@patch(
    "industry_reforged.utils.pricing_engine.get_item_production_details",
    return_value=(None, 1),
)
class TestAnnotateSpareStock:
    def _setup(self, stock):
        corp = EveCorporationInfoFactory(corporation_id=98000001)
        char = EveCharacterFactory(corporation_id=corp.corporation_id)
        facility = IndustryFacility.objects.create(
            facility_id=FOUNDRY, name="Foundry", owner_id=corp.corporation_id
        )
        order = MemberOrder.objects.create(
            character=char, status="ACCEPTED", target_facility=facility
        )
        bay = EveTypeFactory(id=24558, name="Capital Ship Maintenance Bay")
        CorpInventory.objects.create(
            corporation=corp, item_type=bay, location_id=FOUNDRY, quantity=stock
        )
        return corp, order, bay

    def _deliver(self, task, corp, runs, job_id):
        job = CorporationIndustryJob.objects.create(
            corporation=corp,
            job_id=job_id,
            activity_id=1,
            status="delivered",
            runs=runs,
        )
        TaskJobLink.objects.create(task=task, corporation_job=job, linked_runs=runs)

    def test_own_delivered_output_is_not_spare(self, _details):
        corp, order, bay = self._setup(stock=334)
        task = ProductionTaskFactory(
            item_type=bay, quantity=432, status="IN_PRODUCTION", created_from_order=order
        )
        self._deliver(task, corp, runs=261, job_id=1)

        annotate_spare_stock([task])

        assert task.spare_stock_qty == 73

    def test_unconsumed_completed_task_output_is_reserved(self, _details):
        corp, order, bay = self._setup(stock=500)
        parent = ProductionTaskFactory(status="UNCLAIMED", created_from_order=order)
        ProductionTaskFactory(
            item_type=bay,
            quantity=432,
            status="COMPLETED",
            created_from_order=order,
            bom_parent=parent,
        )
        task = ProductionTaskFactory(
            item_type=bay, quantity=100, status="CLAIMED", created_from_order=order
        )

        annotate_spare_stock([task])

        assert task.spare_stock_qty == 68

    def test_stock_elsewhere_or_no_facility_gives_zero(self, _details):
        corp, order, bay = self._setup(stock=0)
        CorpInventory.objects.create(
            corporation=corp, item_type=bay, location_id=SYSTEM, quantity=334
        )
        at_facility = ProductionTaskFactory(
            item_type=bay, quantity=10, status="CLAIMED", created_from_order=order
        )
        no_order = ProductionTaskFactory(item_type=bay, quantity=10, status="CLAIMED")

        annotate_spare_stock([at_facility, no_order])

        assert at_facility.spare_stock_qty == 0
        assert no_order.spare_stock_qty == 0
