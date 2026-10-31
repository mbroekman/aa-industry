"""Per-structure stock and the pick-up list for the build facility."""

# Django
from django.test import TestCase

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# AA Industry App
from industry_reforged.models import CorpInventory, IndustryFacility, KnownLocation
from industry_reforged.tests.factories import EveTypeFactory, MemberOrderFactory
from industry_reforged.utils.stock_locations import (
    annotate_stock_locations,
    build_haul_list,
    single_facility,
)

FOUNDRY = 1_000_000_000_001
JITA = 60_003_760
STAGING = 1_000_000_000_002


class StockLocationsTest(TestCase):
    def setUp(self):
        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98000123, corporation_name="Stock Corp", corporation_ticker="SC"
        )
        IndustryFacility.objects.create(facility_id=FOUNDRY, name="Foundry")
        KnownLocation.objects.create(location_id=JITA, name="Jita IV - Moon 4")
        self.trit = EveTypeFactory(id=34, name="Tritanium")
        self.pye = EveTypeFactory(id=35, name="Pyerite")

    def _stock(self, item, location, qty):
        CorpInventory.objects.create(
            corporation=self.corp, item_type=item, location_id=location, quantity=qty
        )

    def test_split_between_facility_and_elsewhere(self):
        self._stock(self.trit, FOUNDRY, 400)
        self._stock(self.trit, JITA, 1000)
        self._stock(self.trit, STAGING, 300)
        mats = [{"type_id": 34, "name": "Tritanium", "quantity": 1000}]

        annotate_stock_locations(mats, self.corp, FOUNDRY)
        mat = mats[0]

        assert mat["stock_at_facility"] == 400
        assert mat["stock_elsewhere"] == 1300
        assert mat["to_haul"] == 600
        # Build structure first, then largest pile; unknown IDs still get a name.
        assert [loc["name"] for loc in mat["stock_locations"]] == [
            "Foundry",
            "Jita IV - Moon 4",
            f"Location {STAGING}",
        ]
        assert mat["stock_locations"][0]["is_facility"] is True

    def test_haul_list_takes_largest_piles_first(self):
        self._stock(self.trit, JITA, 1000)
        self._stock(self.trit, STAGING, 300)
        self._stock(self.pye, STAGING, 50)
        mats = [
            {"type_id": 34, "name": "Tritanium", "quantity": 1100},
            {"type_id": 35, "name": "Pyerite", "quantity": 80},
        ]
        annotate_stock_locations(mats, self.corp, FOUNDRY)

        haul = build_haul_list(mats)

        by_stop = {s["location_id"]: s for s in haul}
        assert {i["name"]: i["quantity"] for i in by_stop[JITA]["items"]} == {
            "Tritanium": 1000
        }
        # Only what is still short after Jita; Pyerite capped at what exists.
        assert {i["name"]: i["quantity"] for i in by_stop[STAGING]["items"]} == {
            "Pyerite": 50,
            "Tritanium": 100,
        }
        assert haul[0]["location_id"] == STAGING  # most items first

    def test_enough_at_facility_means_nothing_to_haul(self):
        self._stock(self.trit, FOUNDRY, 5000)
        self._stock(self.trit, JITA, 5000)
        mats = [{"type_id": 34, "name": "Tritanium", "quantity": 1000}]
        annotate_stock_locations(mats, self.corp, FOUNDRY)
        assert mats[0]["to_haul"] == 0
        assert build_haul_list(mats) == []

    def test_without_facility_only_locations(self):
        self._stock(self.trit, JITA, 10)
        mats = [{"type_id": 34, "name": "Tritanium", "quantity": 100}]
        annotate_stock_locations(mats, self.corp, None)
        assert mats[0]["stock_at_facility"] is None
        assert mats[0]["to_haul"] == 0
        assert mats[0]["stock_locations"][0]["name"] == "Jita IV - Moon 4"

    def test_other_corps_stock_is_ignored(self):
        other = EveCorporationInfo.objects.create(
            corporation_id=98000124, corporation_name="Other", corporation_ticker="OT"
        )
        CorpInventory.objects.create(
            corporation=other, item_type=self.trit, location_id=JITA, quantity=999
        )
        mats = [{"type_id": 34, "name": "Tritanium", "quantity": 100}]
        annotate_stock_locations(mats, self.corp, FOUNDRY)
        assert mats[0]["stock_locations"] == []

    def test_single_facility(self):
        facility = IndustryFacility.objects.get(facility_id=FOUNDRY)
        a = MemberOrderFactory(target_facility=facility)
        b = MemberOrderFactory(target_facility=facility)
        c = MemberOrderFactory(target_facility=None)
        assert single_facility([a, b]) == facility
        assert single_facility([a, c]) is None
        assert single_facility([]) is None
