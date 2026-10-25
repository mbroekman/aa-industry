"""Buyback monthly statistics (TASK-277): leaderboard, performance, CSV, wallet."""

# Standard Library
import csv
import io
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

# Third Party
import pytest

# Django
from django.contrib.auth.models import Group, Permission
from django.http import Http404
from django.test import RequestFactory
from django.utils import timezone

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership

# AA Industry App
from industry_reforged.models import LedgerTransaction
from industry_reforged.utils.buyback_stats import (
    available_months,
    export_rows,
    monthly_leaderboard,
    monthly_performance,
    top_item_groups,
)
from industry_reforged.views.buyback.stats import (
    buyback_export_csv,
    buyback_leaderboard,
    buyback_performance,
    buyback_stats,
)

from .factories import (
    BuybackContractFactory,
    BuybackContractItemFactory,
    BuybackProgramFactory,
    CorpWalletDivisionFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveGroupFactory,
    EveTypeFactory,
    UserFactory,
)


@pytest.fixture(autouse=True)
def mock_static(monkeypatch):
    # Django
    from django.contrib.staticfiles.storage import staticfiles_storage

    monkeypatch.setattr(staticfiles_storage, "url", lambda name: f"/static/{name}")
    try:
        # Third Party
        from sri.templatetags import sri

        monkeypatch.setattr(
            sri,
            "sri_integrity_static",
            lambda path, algorithm_type=None: "sha256-dummy",
        )
    except ImportError:
        pass


def _aware(year, month, day=15):
    return timezone.make_aware(datetime(year, month, day, 12, 0))


def _paid(program, character, amount, when, donation="0", items=()):
    contract = BuybackContractFactory(
        program=program,
        character=character,
        status="PAID",
        quoted_price=Decimal(amount),
        donation_amount=Decimal(donation),
    )
    for eve_type, quantity, unit_price in items:
        BuybackContractItemFactory(
            contract=contract,
            eve_type=eve_type,
            quantity=quantity,
            unit_price=Decimal(unit_price),
        )
    payout = LedgerTransaction.objects.create(
        transaction_type="BUYBACK_PAYOUT",
        amount=Decimal(amount),
        character=character,
        reference=contract.tracking_number,
        buyback_contract=contract,
    )
    LedgerTransaction.objects.filter(pk=payout.pk).update(date=when)
    return contract


def _user(corporation=None, perms=("basic_access",)):
    user = UserFactory()
    corporation = corporation or EveCorporationInfoFactory()
    character = EveCharacterFactory(
        corporation_id=corporation.corporation_id,
        corporation_name=corporation.corporation_name,
    )
    user.profile.main_character = character
    user.profile.save()
    CharacterOwnership.objects.create(
        user=user, character=character, owner_hash=f"s-{character.character_id}"
    )
    for codename in perms:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    return user.__class__.objects.get(pk=user.pk)


def _request(user, data=None):
    request = RequestFactory().get("/", data or {})
    request.user = user
    request.session = MagicMock()
    return request


@pytest.mark.django_db
class TestMonthlyLeaderboard:
    def test_ranks_sellers_by_isk_paid_in_that_month(self):
        program = BuybackProgramFactory()
        alice, bob = EveCharacterFactory(), EveCharacterFactory()
        _paid(program, alice, "100", _aware(2026, 3))
        _paid(program, bob, "300", _aware(2026, 3), donation="20")
        _paid(program, alice, "150", _aware(2026, 3))
        _paid(program, alice, "9999", _aware(2026, 4))  # other month

        rows = monthly_leaderboard(program, 2026, 3)

        assert [(r.rank, r.character_name) for r in rows] == [
            (1, bob.character_name),
            (2, alice.character_name),
        ]
        assert rows[0].isk_paid == Decimal("300") and rows[0].donated == Decimal("20")
        assert rows[1].isk_paid == Decimal("250") and rows[1].contract_count == 2

    def test_other_programs_are_ignored(self):
        program = BuybackProgramFactory()
        _paid(BuybackProgramFactory(), EveCharacterFactory(), "500", _aware(2026, 3))
        assert monthly_leaderboard(program, 2026, 3) == []

    def test_available_months_newest_first(self):
        program = BuybackProgramFactory()
        character = EveCharacterFactory()
        _paid(program, character, "1", _aware(2026, 1))
        _paid(program, character, "1", _aware(2026, 3))
        _paid(program, character, "1", _aware(2026, 3, 20))
        assert available_months(program) == [date(2026, 3, 1), date(2026, 1, 1)]


@pytest.mark.django_db
class TestMonthlyPerformance:
    def test_counts_submissions_and_payouts_per_month(self):
        program = BuybackProgramFactory()
        now = timezone.now()
        this_month = date(now.year, now.month, 1)
        _paid(program, EveCharacterFactory(), "400", now, donation="40")
        BuybackContractFactory(program=program, status="REJECTED")

        performance = monthly_performance(program, months=12)

        assert len(performance) == 12
        current = performance[-1]
        assert current.month == this_month
        assert current.submitted == 2
        assert current.by_status == {"PAID": 1, "REJECTED": 1}
        assert current.isk_paid == Decimal("400")
        assert current.donated == Decimal("40")
        assert current.paid_count == 1
        assert all(row.submitted == 0 for row in performance[:-1])

    def test_top_item_groups_by_isk(self):
        program = BuybackProgramFactory()
        ore = EveGroupFactory(name="Veldspar")
        loot = EveGroupFactory(name="Salvage")
        items = [
            (EveTypeFactory(eve_group=ore), 1000, "10"),  # 10,000
            (EveTypeFactory(eve_group=loot), 5, "100"),  # 500
            (EveTypeFactory(eve_group=ore), 100, "10"),  # 1,000
        ]
        _paid(program, EveCharacterFactory(), "11500", timezone.now(), items=items)

        groups = top_item_groups(program, months=3)

        assert [(g.name, g.isk, g.quantity) for g in groups] == [
            ("Veldspar", Decimal("11000"), 1100),
            ("Salvage", Decimal("500"), 5),
        ]


@pytest.mark.django_db
class TestExport:
    def test_one_row_per_paid_item(self):
        program = BuybackProgramFactory()
        seller = EveCharacterFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        contract = _paid(
            program,
            seller,
            "500",
            _aware(2026, 2),
            items=[(tritanium, 100, "5")],
        )
        BuybackContractItemFactory(
            contract=BuybackContractFactory(program=program, status="PENDING")
        )

        rows = list(export_rows(program))

        assert len(rows) == 1
        row = rows[0]
        assert row[0] == contract.tracking_number
        assert row[3] == seller.character_name
        assert row[4] == "Tritanium"
        assert row[6:] == [100, "5.00", "500.00"]

    def test_csv_view_only_for_the_programs_directors(self):
        corp = EveCorporationInfoFactory()
        program = BuybackProgramFactory(corporation=corp)
        _paid(
            program,
            EveCharacterFactory(),
            "50",
            _aware(2026, 2),
            items=[(EveTypeFactory(), 10, "5")],
        )

        director = _user(corporation=corp, perms=("basic_access", "corp_access"))
        response = buyback_export_csv(_request(director), program.id)
        lines = list(csv.reader(io.StringIO(response.content.decode())))
        assert response["Content-Type"].startswith("text/csv")
        assert lines[0][0] == "tracking_number" and len(lines) == 2

        other_director = _user(perms=("basic_access", "corp_access"))
        with pytest.raises(Http404):
            buyback_export_csv(_request(other_director), program.id)


@pytest.mark.django_db
class TestViews:
    def test_leaderboard_page_lists_sellers(self):
        program = BuybackProgramFactory(name="Ore Buyback")
        seller = EveCharacterFactory(character_name="Top Miner")
        _paid(program, seller, "1000", _aware(2026, 5))

        html = buyback_leaderboard(
            _request(_user(), {"program": program.id, "month": "2026-05"})
        ).content.decode()

        assert "Top Miner" in html and "May 2026" in html

    def test_leaderboard_hides_restricted_program(self):
        program = BuybackProgramFactory()
        program.restricted_to_groups.add(Group.objects.create(name="Closed"))
        with pytest.raises(Http404):
            buyback_leaderboard(_request(_user(), {"program": program.id}))

    def test_performance_shows_wallet_balance(self):
        corp = EveCorporationInfoFactory()
        wallet = CorpWalletDivisionFactory(
            corporation=corp, name="Buyback Fund", balance=Decimal("123456789")
        )
        program = BuybackProgramFactory(corporation=corp, wallet_division=wallet)
        director = _user(corporation=corp, perms=("basic_access", "corp_access"))

        html = buyback_performance(_request(director), program.id).content.decode()

        assert "Buyback Fund" in html
        assert "123,456,789" in html

    def test_performance_denied_to_other_corporations(self):
        program = BuybackProgramFactory()
        with pytest.raises(Http404):
            buyback_performance(
                _request(_user(perms=("basic_access", "corp_access"))), program.id
            )

    def test_stats_page_links_performance_for_directors_only(self):
        corp = EveCorporationInfoFactory()
        program = BuybackProgramFactory(corporation=corp)
        url = f"/program/{program.id}/performance/"

        member_html = buyback_stats(_request(_user())).content.decode()
        director = _user(corporation=corp, perms=("basic_access", "corp_access"))
        director_html = buyback_stats(_request(director)).content.decode()

        assert url not in member_html
        assert url in director_html
