# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.test import RequestFactory

# AA Industry App
from industry_reforged.models import (
    BuybackProgram,
    BuybackWatchlistItem,
    LedgerTransaction,
)
from industry_reforged.views.buyback.director import (
    director_buyback_contract_resolve,
    director_buyback_review,
    director_config_buyback_program_delete,
    director_config_buyback_program_edit,
    director_config_buyback_watchlist_delete,
    director_config_buyback_watchlist_edit,
)

from .factories import (
    BuybackContractFactory,
    BuybackProgramFactory,
    BuybackWatchlistItemFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveTypeFactory,
    IndustryFacilityFactory,
    UserFactory,
)


@pytest.fixture
def rf():
    return RequestFactory()


def _director_user():
    user = UserFactory()
    corp = EveCorporationInfoFactory()
    character = EveCharacterFactory(
        corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
    )
    user.profile.main_character = character
    user.profile.save()
    perm = Permission.objects.get(codename="corp_access")
    user.user_permissions.add(perm)
    user = user.__class__.objects.get(pk=user.pk)
    return user


@pytest.mark.django_db
class TestBuybackDirectorViews:
    @patch("industry_reforged.views.buyback.director.render")
    def test_program_edit_requires_corp_access(self, mock_render, rf):
        request = rf.get("/")
        request.user = UserFactory()  # no corp_access
        response = director_config_buyback_program_edit(request)
        assert response.status_code == 302
        mock_render.assert_not_called()

    def test_program_create_round_trip(self, rf):
        user = _director_user()
        corp = EveCorporationInfoFactory()
        facility = IndustryFacilityFactory()

        request = rf.post(
            "/",
            {
                "corporation": corp.id,
                "name": "Main Buyback",
                "is_active": "on",
                "facility": facility.facility_id,
                "price_modifier_percent": "-5.0",
                "price_density_threshold": "0",
                "price_density_tax_percent": "0",
                "contract_expiry_days": "7",
                "price_type": "SELL",
                "refining_rate": "90.0",
            },
        )
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            response = director_config_buyback_program_edit(request)

        assert response.status_code == 302
        assert BuybackProgram.objects.filter(name="Main Buyback").exists()

    def test_program_requires_facility_or_known_location(self, rf):
        user = _director_user()
        corp = EveCorporationInfoFactory()

        request = rf.post(
            "/",
            {
                "corporation": corp.id,
                "name": "No Dropoff",
                "price_modifier_percent": "0",
                "price_density_threshold": "0",
                "price_density_tax_percent": "0",
                "contract_expiry_days": "7",
            },
        )
        request.user = user

        with patch("industry_reforged.views.buyback.director.render") as mock_render:
            director_config_buyback_program_edit(request)
            # Form invalid -> falls through to re-render, not a redirect.
            mock_render.assert_called()
        assert not BuybackProgram.objects.filter(name="No Dropoff").exists()

    def test_program_delete(self, rf):
        user = _director_user()
        program = BuybackProgramFactory()

        request = rf.post("/")
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            director_config_buyback_program_delete(request, program.id)

        assert not BuybackProgram.objects.filter(pk=program.pk).exists()

    def test_watchlist_add(self, rf):
        user = _director_user()
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory(name="PLEX")

        request = rf.post(
            "/",
            {
                "program": program.id,
                "item_name": "PLEX",
                "reason": "manual review",
                "blocks_submission": "on",
            },
        )
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            director_config_buyback_watchlist_edit(request)

        assert BuybackWatchlistItem.objects.filter(
            program=program, eve_type=eve_type
        ).exists()

    def test_watchlist_delete(self, rf):
        user = _director_user()
        item = BuybackWatchlistItemFactory()

        request = rf.post("/")
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            director_config_buyback_watchlist_delete(request, item.id)

        assert not BuybackWatchlistItem.objects.filter(pk=item.pk).exists()

    @patch("industry_reforged.views.buyback.director.render")
    def test_review_queue_only_lists_flagged_and_matched(self, mock_render, rf):
        user = _director_user()
        BuybackContractFactory(status="FLAGGED")
        BuybackContractFactory(status="MATCHED")
        BuybackContractFactory(status="PAID")
        BuybackContractFactory(status="PENDING")

        request = rf.get("/")
        request.user = user
        director_buyback_review(request)

        context = mock_render.call_args[0][2]
        statuses = {c.status for c in context["contracts"]}
        assert statuses == {"FLAGGED", "MATCHED"}

    def test_accept_and_pay_creates_ledger_transaction_and_pays(self, rf):
        user = _director_user()
        contract = BuybackContractFactory(status="MATCHED", quoted_price=5000)

        request = rf.post("/", {"action": "accept_and_pay"})
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            director_buyback_contract_resolve(request, contract.tracking_number)

        contract.refresh_from_db()
        assert contract.status == "PAID"
        assert (
            LedgerTransaction.objects.filter(
                buyback_contract=contract, transaction_type="BUYBACK_PAYOUT"
            ).count()
            == 1
        )

    def test_reject_flips_status_without_ledger_row(self, rf):
        user = _director_user()
        contract = BuybackContractFactory(status="FLAGGED")

        request = rf.post("/", {"action": "reject", "reason": "scam"})
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            with patch("industry_reforged.views.buyback.director.notify_discord_user"):
                director_buyback_contract_resolve(request, contract.tracking_number)

        contract.refresh_from_db()
        assert contract.status == "REJECTED"
        assert LedgerTransaction.objects.filter(buyback_contract=contract).count() == 0

    def test_resolving_already_paid_contract_is_a_noop(self, rf):
        user = _director_user()
        contract = BuybackContractFactory(status="PAID")

        request = rf.post("/", {"action": "accept_and_pay"})
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            director_buyback_contract_resolve(request, contract.tracking_number)

        assert LedgerTransaction.objects.filter(buyback_contract=contract).count() == 0
