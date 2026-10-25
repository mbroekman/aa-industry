"""Buyback item rules & pricing options (TASK-274)."""

# Standard Library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Third Party
import pytest
from eveuniverse.models import (
    EveCategory,
    EveGroup,
    EveMarketGroup,
    EveMarketPrice,
    EveType,
)

# Django
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.http import Http404
from django.test import RequestFactory

# Alliance Auth
from allianceauth.authentication.models import CharacterOwnership

# AA Industry App
from industry_reforged.forms import (
    BuybackItemRuleForm,
    BuybackStaticPriceForm,
    BuybackWatchlistItemForm,
)
from industry_reforged.models import (
    BuybackContract,
    BuybackItemRule,
    BuybackStaticPrice,
    BuybackWatchlistItem,
)
from industry_reforged.utils import buyback_data
from industry_reforged.utils.inventory_parser import (
    parse_inventory_paste_with_unpacked,
)
from industry_reforged.utils.pricing_engine import calculate_buyback_quote
from industry_reforged.views.buyback.director import (
    director_config_buyback_rule_edit,
)
from industry_reforged.views.buyback.member import buyback_calculator

from .factories import (
    BuybackProgramFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
    EveGroupFactory,
    EveTypeFactory,
    UserFactory,
)

PRICE = "industry_reforged.utils.pricing_engine._market_unit_prices"
REAL_ENSURE_SECTIONS = buyback_data.ensure_sections


def _prices(table, default=0.0):
    """_market_unit_prices replacement: {type_id: price}."""
    return lambda ids, order_type="sell": {tid: table.get(tid, default) for tid in ids}


def _category(category_id, name):
    return EveCategory.objects.get_or_create(
        id=category_id, defaults={"name": name, "published": True}
    )[0]


def _type_in_category(category_id, category_name="Category", **kwargs):
    group = EveGroupFactory(eve_category=_category(category_id, category_name))
    return EveTypeFactory(eve_group=group, **kwargs)


def _market_group(group_id, name, parent=None):
    return EveMarketGroup.objects.create(
        id=group_id, name=name, description="", parent_market_group=parent
    )


@pytest.fixture(autouse=True)
def _no_esi_section_loading():
    """Unit tests never fetch EVE data; the types are built complete."""
    with patch(
        "industry_reforged.utils.buyback_data.ensure_sections",
        side_effect=lambda types, section: {t.id: t for t in types},
    ):
        yield


@pytest.mark.django_db
class TestAcceptance:
    def test_blueprints_are_never_accepted(self):
        program = BuybackProgramFactory()
        blueprint = _type_in_category(9, "Blueprint")
        with patch(PRICE, side_effect=_prices({blueprint.id: 1000.0})):
            total, details = calculate_buyback_quote({blueprint: 1}, program)
        assert details[0]["blocked"] is True
        assert "Blueprint" in details[0]["blocked_reason"]
        assert total == Decimal("0.00")

    def test_assembled_items_need_the_option(self):
        ship = EveTypeFactory()
        with patch(PRICE, side_effect=_prices({ship.id: 100.0})):
            _, refused = calculate_buyback_quote(
                {ship: 1}, BuybackProgramFactory(), unpacked_type_ids={ship.id}
            )
            _, allowed = calculate_buyback_quote(
                {ship: 1},
                BuybackProgramFactory(allow_unpacked_items=True),
                unpacked_type_ids={ship.id},
            )
        assert refused[0]["blocked"] is True
        assert allowed[0]["blocked"] is False

    def test_group_watchlist_blocks_every_item_in_the_group(self):
        program = BuybackProgramFactory()
        item = EveTypeFactory()
        BuybackWatchlistItem.objects.create(
            program=program, eve_group=item.eve_group, blocks_submission=True
        )
        with patch(PRICE, side_effect=_prices({item.id: 100.0})):
            _, details = calculate_buyback_quote({item: 1}, program)
        assert details[0]["blocked"] is True

    def test_disallow_rule_blocks(self):
        program = BuybackProgramFactory()
        item = EveTypeFactory()
        BuybackItemRule.objects.create(program=program, eve_type=item, disallow=True)
        with patch(PRICE, side_effect=_prices({item.id: 100.0})):
            _, details = calculate_buyback_quote({item: 1}, program)
        assert details[0]["blocked"] is True

    def test_allowlist_mode_only_accepts_items_with_a_rule(self):
        program = BuybackProgramFactory(allow_all_items=False)
        listed, unlisted = EveTypeFactory(), EveTypeFactory()
        BuybackItemRule.objects.create(program=program, eve_type=listed)
        with patch(PRICE, side_effect=_prices({}, default=100.0)):
            total, details = calculate_buyback_quote({listed: 1, unlisted: 1}, program)
        by_type = {d["eve_type"].id: d for d in details}
        assert by_type[listed.id]["blocked"] is False
        assert by_type[unlisted.id]["blocked"] is True
        assert total == Decimal("100.00")


@pytest.mark.django_db
class TestRulePricing:
    def test_item_rule_adds_to_the_program_modifier(self):
        program = BuybackProgramFactory(price_modifier_percent=-10.0)
        item = EveTypeFactory()
        BuybackItemRule.objects.create(
            program=program, eve_type=item, price_modifier_percent=5.0
        )
        with patch(PRICE, side_effect=_prices({item.id: 100.0})):
            total, details = calculate_buyback_quote({item: 1}, program)
        assert details[0]["unit_price"] == Decimal("95.00")
        assert any("item rule" in note for note in details[0]["notes"])

    def test_market_group_rule_covers_subgroups_and_item_rule_wins(self):
        program = BuybackProgramFactory()
        ore_root = _market_group(900001, "Ore")
        veldspar_group = _market_group(900002, "Veldspar", parent=ore_root)
        covered = EveTypeFactory(eve_market_group=veldspar_group)
        overridden = EveTypeFactory(eve_market_group=veldspar_group)
        BuybackItemRule.objects.create(
            program=program, eve_market_group=ore_root, price_modifier_percent=-20.0
        )
        BuybackItemRule.objects.create(
            program=program, eve_type=overridden, price_modifier_percent=10.0
        )
        with patch(PRICE, side_effect=_prices({}, default=100.0)):
            _, details = calculate_buyback_quote({covered: 1, overridden: 1}, program)
        by_type = {d["eve_type"].id: d for d in details}
        assert by_type[covered.id]["unit_price"] == Decimal("80.00")
        assert by_type[overridden.id]["unit_price"] == Decimal("110.00")

    def test_static_price_ignores_modifiers_and_density_tax(self):
        program = BuybackProgramFactory(
            price_modifier_percent=-50.0,
            price_density_threshold=1_000_000.0,
            price_density_tax_percent=50.0,
        )
        item = EveTypeFactory(packaged_volume=10.0)
        BuybackStaticPrice.objects.create(
            program=program, eve_type=item, price=Decimal("1234.56")
        )
        with patch(PRICE, side_effect=_prices({item.id: 1.0})):
            total, details = calculate_buyback_quote({item: 2}, program)
        assert details[0]["value_source"] == "static"
        assert details[0]["unit_price"] == Decimal("1234.56")
        assert total == Decimal("2469.12")

    def test_npc_price_for_overseers_personal_effects(self):
        ope_group = EveGroup.objects.create(
            id=493,
            name="Overseer Personal Effects",
            eve_category=_category(100500, "Commodity"),
            published=True,
        )
        effects = EveTypeFactory(eve_group=ope_group)
        EveMarketPrice.objects.create(
            eve_type=effects, average_price=500000.0, adjusted_price=1.0
        )
        with patch(PRICE, side_effect=_prices({effects.id: 10.0})):
            _, off = calculate_buyback_quote({effects: 1}, BuybackProgramFactory())
            _, on = calculate_buyback_quote(
                {effects: 1}, BuybackProgramFactory(npc_price_ope=True)
            )
        assert off[0]["unit_price"] == Decimal("10.00")
        assert on[0]["value_source"] == "npc"
        assert on[0]["unit_price"] == Decimal("500000.00")

    def test_bonds_toggle_is_independent_of_ope_toggle(self):
        """The original plugin's bonds option read the OPE flag by mistake."""
        bonds_group = EveGroup.objects.create(
            id=1248,
            name="SCC Encrypted Bonds",
            eve_category=_category(100501, "Commodity 2"),
            published=True,
        )
        bond = EveTypeFactory(eve_group=bonds_group)
        program = BuybackProgramFactory(npc_price_ope=True, npc_price_bonds=False)
        assert buyback_data.npc_price_applies(program, bond) is False


@pytest.mark.django_db
class TestHauling:
    def test_hauling_is_deducted_per_m3(self):
        program = BuybackProgramFactory(hauling_fuel_cost=100.0)
        item = EveTypeFactory(packaged_volume=10.0)
        with patch(PRICE, side_effect=_prices({item.id: 5000.0})):
            total, details = calculate_buyback_quote({item: 3}, program)
        # 3 x 10 m3 x 100 ISK/m3 = 3,000 hauling from 15,000
        assert details[0]["hauling_cost"] == Decimal("3000.00")
        assert total == Decimal("12000.00")

    def test_compression_modifier_uses_compressed_volume(self):
        program = BuybackProgramFactory(
            hauling_fuel_cost=100.0, compression_density_modifier=True
        )
        ore = _type_in_category(25, "Asteroid", name="Veldspar", packaged_volume=0.1)
        _type_in_category(
            25, "Asteroid", name="Compressed Veldspar", packaged_volume=0.001
        )
        with patch(PRICE, side_effect=_prices({ore.id: 20.0})):
            _, details = calculate_buyback_quote({ore: 1000}, program)
        # 1000 x 0.001 m3 x 100 = 100 ISK instead of 10,000 at raw volume
        assert details[0]["hauling_cost"] == Decimal("100.00")


def _member():
    user = UserFactory()
    corp = EveCorporationInfoFactory()
    character = EveCharacterFactory(
        corporation_id=corp.corporation_id, corporation_name=corp.corporation_name
    )
    user.profile.main_character = character
    user.profile.save()
    CharacterOwnership.objects.create(
        user=user, character=character, owner_hash=f"h-{character.character_id}"
    )
    user.user_permissions.add(Permission.objects.get(codename="basic_access"))
    return user.__class__.objects.get(pk=user.pk), corp


def _post(user, data):
    request = RequestFactory().post("/", data)
    request.user = user
    request.session = MagicMock()
    request._messages = FallbackStorage(request)
    return request


@pytest.mark.django_db
class TestCalculatorWithOptions:
    @patch("industry_reforged.views.buyback.member.render")
    def test_whole_appraisal_refused_when_any_item_is_not_accepted(self, _render):
        user, _ = _member()
        program = BuybackProgramFactory(reject_appraisal_on_disallowed=True)
        EveTypeFactory(name="Tritanium")
        _type_in_category(9, "Blueprint", name="Rifter Blueprint")

        with patch(PRICE, side_effect=_prices({}, default=5.0)):
            buyback_calculator(
                _post(
                    user,
                    {
                        "program_id": program.id,
                        "inventory_text": "Tritanium\t100\nRifter Blueprint\t1",
                        "confirm": "1",
                    },
                )
            )
        assert not BuybackContract.objects.exists()

    def test_hauling_is_stored_on_the_contract(self):
        user, _ = _member()
        program = BuybackProgramFactory(hauling_fuel_cost=10.0)
        EveTypeFactory(name="Tritanium", packaged_volume=0.01)

        with patch(PRICE, side_effect=_prices({}, default=5.0)):
            buyback_calculator(
                _post(
                    user,
                    {
                        "program_id": program.id,
                        "inventory_text": "Tritanium\t1000",
                        "confirm": "1",
                    },
                )
            )
        contract = BuybackContract.objects.get()
        # 1000 x 5 ISK = 5,000; hauling 1000 x 0.01 m3 x 10 = 100
        assert contract.hauling_cost == Decimal("100.00")
        assert contract.quoted_price == Decimal("4900.00")
        assert contract.modifier_impact == Decimal("0.00")


@pytest.mark.django_db
class TestEnsureSections:
    """The real ensure_sections, not the autouse stub."""

    def setup_method(self):
        cache.clear()

    def test_fetches_a_missing_section_once_and_remembers_failures(self):
        item = EveTypeFactory()
        with patch.object(
            EveType.objects, "update_or_create_esi", side_effect=Exception("down")
        ) as fetch:
            REAL_ENSURE_SECTIONS([item], EveType.Section.DOGMAS)
            REAL_ENSURE_SECTIONS([item], EveType.Section.DOGMAS)
        assert fetch.call_count == 1

    def test_skips_types_that_already_have_the_section(self):
        item = EveTypeFactory()
        item.enabled_sections.dogmas = True
        item.save()
        with patch.object(EveType.objects, "update_or_create_esi") as fetch:
            REAL_ENSURE_SECTIONS(
                [EveType.objects.get(pk=item.pk)], EveType.Section.DOGMAS
            )
        fetch.assert_not_called()


@pytest.mark.django_db
class TestForms:
    def test_rule_needs_exactly_one_target(self):
        program = BuybackProgramFactory()
        form = BuybackItemRuleForm(
            {"program": program.id, "price_modifier_percent": "5"},
            corporation=program.corporation,
        )
        assert not form.is_valid()

    def test_rule_for_an_item(self):
        program = BuybackProgramFactory()
        item = EveTypeFactory(name="Zydrine")
        form = BuybackItemRuleForm(
            {
                "program": program.id,
                "item_name": "zydrine",
                "price_modifier_percent": "5",
            },
            corporation=program.corporation,
        )
        assert form.is_valid(), form.errors
        rule = form.save()
        assert rule.eve_type == item and rule.eve_market_group is None

    def test_rule_for_a_market_group(self):
        program = BuybackProgramFactory()
        group = _market_group(900010, "Minerals")
        form = BuybackItemRuleForm(
            {
                "program": program.id,
                "eve_market_group": group.id,
                "disallow": "on",
                "price_modifier_percent": "0",
            },
            corporation=program.corporation,
        )
        assert form.is_valid(), form.errors
        assert form.save().eve_market_group == group

    def test_watchlist_by_group_name(self):
        program = BuybackProgramFactory()
        item = EveTypeFactory()
        form = BuybackWatchlistItemForm(
            {"program": program.id, "group_name": item.eve_group.name},
            corporation=program.corporation,
        )
        assert form.is_valid(), form.errors
        entry = form.save()
        assert entry.eve_group == item.eve_group and entry.eve_type is None

    def test_static_price_is_unique_per_item(self):
        program = BuybackProgramFactory()
        item = EveTypeFactory(name="PLEX")
        BuybackStaticPrice.objects.create(program=program, eve_type=item, price=1)
        form = BuybackStaticPriceForm(
            {"program": program.id, "item_name": "PLEX", "price": "5"},
            corporation=program.corporation,
        )
        assert not form.is_valid()


@pytest.mark.django_db
class TestRuleViewScoping:
    def test_rule_of_another_corporation_cannot_be_edited(self):
        user = UserFactory()
        corp = EveCorporationInfoFactory()
        user.profile.main_character = EveCharacterFactory(
            corporation_id=corp.corporation_id
        )
        user.profile.save()
        user.user_permissions.add(Permission.objects.get(codename="corp_access"))
        user = user.__class__.objects.get(pk=user.pk)
        foreign = BuybackItemRule.objects.create(
            program=BuybackProgramFactory(), eve_type=EveTypeFactory()
        )
        request = RequestFactory().get("/")
        request.user = user
        with pytest.raises(Http404):
            director_config_buyback_rule_edit(request, foreign.id)


@pytest.mark.django_db
class TestParserUnpacked:
    def test_lines_without_quantity_are_reported_as_unpacked(self):
        rifter = EveTypeFactory(name="Rifter")
        trit = EveTypeFactory(name="Tritanium")
        parsed, _, unpacked = parse_inventory_paste_with_unpacked(
            "Rifter\tFrigate\nTritanium\t100"
        )
        assert parsed == {rifter: 1, trit: 100}
        assert unpacked == {rifter.id}


@pytest.mark.django_db
class TestUniqueRulesAndWatchlist:
    """The unique constraints have no condition (MariaDB can't create those);
    they rely on NULLs being distinct, so the empty side never collides."""

    def test_many_group_rules_and_one_rule_per_item(self):
        # Django
        from django.db import IntegrityError, transaction

        program = BuybackProgramFactory()
        BuybackItemRule.objects.create(
            program=program, eve_market_group=_market_group(910001, "Ore")
        )
        BuybackItemRule.objects.create(
            program=program, eve_market_group=_market_group(910002, "Ice")
        )
        item = EveTypeFactory()
        BuybackItemRule.objects.create(program=program, eve_type=item)

        with pytest.raises(IntegrityError), transaction.atomic():
            BuybackItemRule.objects.create(program=program, eve_type=item)
        assert BuybackItemRule.objects.filter(program=program).count() == 3

    def test_many_item_entries_and_one_entry_per_group(self):
        # Django
        from django.db import IntegrityError, transaction

        program = BuybackProgramFactory()
        group = EveGroupFactory()
        BuybackWatchlistItem.objects.create(program=program, eve_type=EveTypeFactory())
        BuybackWatchlistItem.objects.create(program=program, eve_type=EveTypeFactory())
        BuybackWatchlistItem.objects.create(program=program, eve_group=group)

        with pytest.raises(IntegrityError), transaction.atomic():
            BuybackWatchlistItem.objects.create(program=program, eve_group=group)
