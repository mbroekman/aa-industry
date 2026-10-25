# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.http import Http404
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
    """A corp_access user whose main character is in a fresh corporation."""
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
    return user, corp


def _own_contract(corp, **kwargs):
    return BuybackContractFactory(
        program=BuybackProgramFactory(corporation=corp), **kwargs
    )


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
        user, corp = _director_user()
        facility = IndustryFacilityFactory()

        request = rf.post(
            "/",
            {
                "corporation": corp.id,
                "name": "Main Buyback",
                "is_active": "on",
                "facilities": [facility.facility_id],
                "recipient_type": "CORPORATION",
                "tracking_prefix": "corp1",
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
        program = BuybackProgram.objects.get(name="Main Buyback", corporation=corp)
        assert program.tracking_prefix == "CORP1"
        assert list(program.facilities.all()) == [facility]

    def test_character_recipient_requires_a_character(self, rf):
        user, corp = _director_user()
        facility = IndustryFacilityFactory()

        request = rf.post(
            "/",
            {
                "corporation": corp.id,
                "name": "To A Character",
                "facilities": [facility.facility_id],
                "recipient_type": "CHARACTER",
                "tracking_prefix": "BB",
                "price_modifier_percent": "0",
                "price_density_threshold": "0",
                "price_density_tax_percent": "0",
                "contract_expiry_days": "7",
                "price_type": "SELL",
                "refining_rate": "90.0",
            },
        )
        request.user = user

        with patch("industry_reforged.views.buyback.director.render") as mock_render:
            director_config_buyback_program_edit(request)

        form = mock_render.call_args[0][2]["form"]
        assert "recipient_character" in form.errors
        assert not BuybackProgram.objects.filter(name="To A Character").exists()

    def test_program_cannot_be_created_for_another_corporation(self, rf):
        user, _ = _director_user()
        other_corp = EveCorporationInfoFactory()
        facility = IndustryFacilityFactory()

        request = rf.post(
            "/",
            {
                "corporation": other_corp.id,
                "name": "Foreign Buyback",
                "facilities": [facility.facility_id],
                "price_modifier_percent": "0",
                "price_density_threshold": "0",
                "price_density_tax_percent": "0",
                "contract_expiry_days": "7",
                "price_type": "SELL",
                "refining_rate": "90.0",
            },
        )
        request.user = user

        with patch("industry_reforged.views.buyback.director.render"):
            director_config_buyback_program_edit(request)

        assert not BuybackProgram.objects.filter(name="Foreign Buyback").exists()

    def test_program_requires_facility_or_known_location(self, rf):
        user, corp = _director_user()

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

    def test_program_of_another_corporation_cannot_be_edited(self, rf):
        user, _ = _director_user()
        foreign = BuybackProgramFactory()

        request = rf.get("/")
        request.user = user

        with pytest.raises(Http404):
            director_config_buyback_program_edit(request, foreign.id)

    def test_program_delete(self, rf):
        user, corp = _director_user()
        program = BuybackProgramFactory(corporation=corp)

        request = rf.post("/")
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            director_config_buyback_program_delete(request, program.id)

        assert not BuybackProgram.objects.filter(pk=program.pk).exists()

    def test_program_delete_rejects_get(self, rf):
        user, corp = _director_user()
        program = BuybackProgramFactory(corporation=corp)

        request = rf.get("/")
        request.user = user
        response = director_config_buyback_program_delete(request, program.id)

        assert response.status_code == 405
        assert BuybackProgram.objects.filter(pk=program.pk).exists()

    def test_program_with_contracts_is_not_deleted(self, rf):
        user, corp = _director_user()
        contract = _own_contract(corp)

        request = rf.post("/")
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages") as msgs:
            director_config_buyback_program_delete(request, contract.program_id)

        assert BuybackProgram.objects.filter(pk=contract.program_id).exists()
        msgs.error.assert_called_once()

    def test_program_of_another_corporation_cannot_be_deleted(self, rf):
        user, _ = _director_user()
        foreign = BuybackProgramFactory()

        request = rf.post("/")
        request.user = user

        with pytest.raises(Http404):
            director_config_buyback_program_delete(request, foreign.id)
        assert BuybackProgram.objects.filter(pk=foreign.pk).exists()

    def test_watchlist_add(self, rf):
        user, corp = _director_user()
        program = BuybackProgramFactory(corporation=corp)
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

    def test_watchlist_cannot_target_another_corporations_program(self, rf):
        user, _ = _director_user()
        foreign = BuybackProgramFactory()
        EveTypeFactory(name="PLEX")

        request = rf.post(
            "/", {"program": foreign.id, "item_name": "PLEX", "reason": "x"}
        )
        request.user = user

        with patch("industry_reforged.views.buyback.director.render"):
            director_config_buyback_watchlist_edit(request)

        assert not BuybackWatchlistItem.objects.filter(program=foreign).exists()

    def test_watchlist_delete(self, rf):
        user, corp = _director_user()
        item = BuybackWatchlistItemFactory(
            program=BuybackProgramFactory(corporation=corp)
        )

        request = rf.post("/")
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            director_config_buyback_watchlist_delete(request, item.id)

        assert not BuybackWatchlistItem.objects.filter(pk=item.pk).exists()

    @patch("industry_reforged.views.buyback.director.render")
    def test_review_queue_only_lists_own_flagged_and_matched(self, mock_render, rf):
        user, corp = _director_user()
        _own_contract(corp, status="FLAGGED")
        _own_contract(corp, status="MATCHED")
        _own_contract(corp, status="PAID")
        _own_contract(corp, status="PENDING")
        BuybackContractFactory(status="FLAGGED")  # another corporation's

        request = rf.get("/")
        request.user = user
        director_buyback_review(request)

        contracts = list(mock_render.call_args[0][2]["contracts"])
        assert {c.status for c in contracts} == {"FLAGGED", "MATCHED"}
        assert all(c.program.corporation_id == corp.id for c in contracts)

    @patch("industry_reforged.views.buyback.director.notify_discord_user")
    def test_accept_and_pay_creates_ledger_transaction_and_pays(self, mock_notify, rf):
        user, corp = _director_user()
        contract = _own_contract(corp, status="MATCHED", quoted_price=5000)

        request = rf.post("/", {"action": "accept_and_pay"})
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            director_buyback_contract_resolve(request, contract.tracking_number)

        contract.refresh_from_db()
        assert contract.status == "PAID"
        payouts = LedgerTransaction.objects.filter(
            buyback_contract=contract, transaction_type="BUYBACK_PAYOUT"
        )
        assert payouts.count() == 1
        assert payouts.first().director == user
        mock_notify.assert_called_once()

    def test_reject_flips_status_without_ledger_row(self, rf):
        user, corp = _director_user()
        contract = _own_contract(corp, status="FLAGGED")

        request = rf.post("/", {"action": "reject", "reason": "scam"})
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            with patch("industry_reforged.views.buyback.director.notify_discord_user"):
                director_buyback_contract_resolve(request, contract.tracking_number)

        contract.refresh_from_db()
        assert contract.status == "REJECTED"
        assert LedgerTransaction.objects.filter(buyback_contract=contract).count() == 0

    def test_resolving_already_paid_contract_is_a_noop(self, rf):
        user, corp = _director_user()
        contract = _own_contract(corp, status="PAID")

        request = rf.post("/", {"action": "accept_and_pay"})
        request.user = user

        with patch("industry_reforged.views.buyback.director.messages"):
            director_buyback_contract_resolve(request, contract.tracking_number)

        assert LedgerTransaction.objects.filter(buyback_contract=contract).count() == 0

    def test_another_corporations_contract_cannot_be_resolved(self, rf):
        user, _ = _director_user()
        foreign = BuybackContractFactory(status="MATCHED")

        request = rf.post("/", {"action": "accept_and_pay"})
        request.user = user

        with pytest.raises(Http404):
            director_buyback_contract_resolve(request, foreign.tracking_number)
        foreign.refresh_from_db()
        assert foreign.status == "MATCHED"
