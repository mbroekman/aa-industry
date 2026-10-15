# Standard Library
from unittest.mock import patch

# Third Party
import pytest

# Django
from django.contrib.auth.models import Permission
from django.test import RequestFactory

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership

# AA Industry App
from industry_reforged.models import BuybackContract, BuybackContractItem
from industry_reforged.views.buyback.member import (
    buyback_calculator,
    buyback_contract_cancel,
    buyback_contract_detail,
    buyback_dashboard,
)

from .factories import (
    BuybackContractFactory,
    BuybackProgramFactory,
    EveCharacterFactory,
    EveTypeFactory,
    UserFactory,
)


@pytest.fixture
def rf():
    return RequestFactory()


def _member_user(character=None):
    user = UserFactory()
    character = character or EveCharacterFactory()
    user.profile.main_character = character
    user.profile.save()
    CharacterOwnership.objects.create(user=user, character=character, owner_hash=f"hash-{character.id}")
    perm = Permission.objects.get(codename="basic_access")
    user.user_permissions.add(perm)
    user = user.__class__.objects.get(pk=user.pk)
    return user, character


@pytest.mark.django_db
class TestBuybackMemberViews:
    @patch("industry_reforged.views.buyback.member.render")
    def test_dashboard_requires_permission(self, mock_render, rf):
        request = rf.get("/")
        request.user = UserFactory()  # no basic_access permission
        response = buyback_dashboard(request)
        assert response.status_code == 302
        mock_render.assert_not_called()

    @patch("industry_reforged.views.buyback.member.render")
    def test_dashboard_renders_with_permission(self, mock_render, rf):
        user, _ = _member_user()
        request = rf.get("/")
        request.user = user
        buyback_dashboard(request)
        mock_render.assert_called()

    @patch("industry_reforged.views.buyback.member.render")
    def test_calculator_preview_does_not_persist(self, mock_render, rf):
        user, character = _member_user()
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory(name="Tritanium")

        request = rf.post(
            "/",
            {"program_id": program.id, "inventory_text": "Tritanium\t100"},
        )
        request.user = user

        with patch(
            "industry_reforged.views.buyback.member.calculate_buyback_quote",
            return_value=(100, [{"eve_type": eve_type, "quantity": 100, "unit_price": 1, "line_total": 100, "blocked": False, "flagged": False, "value_source": "market", "watchlist_reason": ""}]),
        ):
            buyback_calculator(request)

        mock_render.assert_called()
        assert BuybackContract.objects.count() == 0

    def test_calculator_confirm_creates_exactly_one_contract(self, rf):
        user, character = _member_user()
        program = BuybackProgramFactory()
        eve_type = EveTypeFactory(name="Tritanium")

        request = rf.post(
            "/",
            {
                "program_id": program.id,
                "inventory_text": "Tritanium\t100",
                "confirm": "1",
            },
        )
        request.user = user

        detail = {
            "eve_type": eve_type,
            "quantity": 100,
            "unit_price": 1,
            "line_total": 100,
            "blocked": False,
            "flagged": False,
            "value_source": "market",
            "watchlist_reason": "",
        }
        with patch(
            "industry_reforged.views.buyback.member.calculate_buyback_quote",
            return_value=(100, [detail]),
        ):
            with patch("industry_reforged.views.buyback.member.messages"):
                response = buyback_calculator(request)

        assert response.status_code == 302
        assert BuybackContract.objects.count() == 1
        contract = BuybackContract.objects.first()
        assert contract.character_id == character.id
        assert contract.tracking_number.startswith("BB-")
        assert BuybackContractItem.objects.filter(contract=contract).count() == 1

    @patch("industry_reforged.views.buyback.member.render")
    def test_contract_detail_denies_non_owner(self, mock_render, rf):
        user, _ = _member_user()
        other_character = EveCharacterFactory()
        contract = BuybackContractFactory(character=other_character)

        request = rf.get("/")
        request.user = user

        with patch("industry_reforged.views.buyback.member.messages"):
            buyback_contract_detail(request, contract.tracking_number)

        mock_render.assert_not_called()

    @patch("industry_reforged.views.buyback.member.render")
    def test_contract_detail_allows_owner(self, mock_render, rf):
        user, character = _member_user()
        contract = BuybackContractFactory(character=character)

        request = rf.get("/")
        request.user = user
        buyback_contract_detail(request, contract.tracking_number)
        mock_render.assert_called()

    def test_cancel_only_works_while_pending(self, rf):
        user, character = _member_user()
        contract = BuybackContractFactory(character=character, status="MATCHED")

        request = rf.post("/")
        request.user = user

        with patch("industry_reforged.views.buyback.member.messages"):
            buyback_contract_cancel(request, contract.tracking_number)

        contract.refresh_from_db()
        assert contract.status == "MATCHED"

    def test_cancel_succeeds_while_pending(self, rf):
        user, character = _member_user()
        contract = BuybackContractFactory(character=character, status="PENDING")

        request = rf.post("/")
        request.user = user

        with patch("industry_reforged.views.buyback.member.messages"):
            buyback_contract_cancel(request, contract.tracking_number)

        contract.refresh_from_db()
        assert contract.status == "CANCELLED"
