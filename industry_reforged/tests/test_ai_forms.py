# Third Party
import pytest

# Alliance Auth
from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo

# AA Industry App
from industry_reforged.forms import (
    BasketForm,
    OpportunityScannerForm,
    get_target_hub_choices,
)
from industry_reforged.models.facilities import IndustryFacility, KnownLocation


@pytest.mark.django_db
class TestAITargetHubChoices:
    def test_get_target_hub_choices_includes_industry_facilities(self):
        # Create an alliance and corporations
        alliance = EveAllianceInfo.objects.create(
            alliance_id=3001,
            alliance_name="Test Alliance",
            executor_corp_id=2001,
        )
        corp1 = EveCorporationInfo.objects.create(
            corporation_id=2001,
            corporation_name="Corp One",
            alliance=alliance,
            member_count=10,
        )
        corp2 = EveCorporationInfo.objects.create(
            corporation_id=2002,
            corporation_name="Corp Two",
            alliance=alliance,
            member_count=5,
        )
        other_corp = EveCorporationInfo.objects.create(
            corporation_id=9999,
            corporation_name="Other Corp",
            member_count=1,
        )

        # Create facilities
        fac1 = IndustryFacility.objects.create(
            facility_id=101,
            name="Corp1 Hub",
            owner_id=corp1.corporation_id,
        )
        fac2 = IndustryFacility.objects.create(
            facility_id=102,
            name="Alliance Hub",
            owner_id=corp2.corporation_id,
        )
        npc_fac = IndustryFacility.objects.create(
            facility_id=600001,
            name="Jita IV - 4",
            owner_id=1000002,  # NPC
        )
        unowned_prod_fac = IndustryFacility.objects.create(
            facility_id=103,
            name="Public Production Plant",
            owner_id=None,
            is_production_facility=True,
        )

        # Create a KnownLocation
        loc = KnownLocation.objects.create(
            location_id=104,
            name="Asset Outpost",
        )
        loc.corporations.add(corp1)

        user_corps = EveCorporationInfo.objects.filter(pk=corp1.pk)
        choices = get_target_hub_choices(user_corps=user_corps)

        choice_ids = [c[0] for c in choices if c[0] != ""]
        assert 101 in choice_ids
        assert 102 in choice_ids
        assert 600001 in choice_ids
        assert 103 in choice_ids
        assert 104 in choice_ids

        # Test BasketForm integration
        b_form = BasketForm(user_corps=user_corps)
        b_choice_ids = [c[0] for c in b_form.fields["target_hub_id"].choices if c[0] != ""]
        assert 101 in b_choice_ids
        assert 102 in b_choice_ids
        assert 600001 in b_choice_ids

        # Test OpportunityScannerForm integration
        s_form = OpportunityScannerForm(user_corps=user_corps)
        s_choice_ids = [c[0] for c in s_form.fields["target_hub_id"].choices if c[0] != ""]
        assert 101 in s_choice_ids
        assert 102 in s_choice_ids

    def test_target_hub_choices_no_duplicates(self):
        # When an ID is both in IndustryFacility and KnownLocation
        fac = IndustryFacility.objects.create(
            facility_id=201,
            name="Shared Facility",
            owner_id=None,
        )
        KnownLocation.objects.create(
            location_id=201,
            name="Shared Facility Known",
        )

        choices = get_target_hub_choices()
        choice_ids = [c[0] for c in choices if c[0] != ""]
        assert choice_ids.count(201) == 1
