"""Sell or reprocess advice for buyback contracts (TASK-279)."""

# Standard Library
from decimal import Decimal
from unittest.mock import patch

# Third Party
import pytest
from eveuniverse.models import EveCategory, EveTypeMaterial

# AA Industry App
from industry_reforged.models import (
    CorpBuildMaterial,
    CorpItemConfig,
    CorpReprocessingConfig,
    TaxConfig,
)
from industry_reforged.utils import reprocess_advice
from industry_reforged.utils.reprocess_advice import (
    BUILD,
    REPROCESS,
    SELL,
    SORT,
    SORT_CLOSE,
    SORT_NO_PRICE,
    SORT_SLOW,
    advise,
)
from industry_reforged.utils.stock_needs import stock_deficits

from .factories import EveCorporationInfoFactory, EveGroupFactory, EveTypeFactory

PRICES = "industry_reforged.utils.reprocess_advice._market_unit_prices"


@pytest.fixture(autouse=True)
def _no_esi():
    with (
        patch(
            "industry_reforged.utils.buyback_data.ensure_sections",
            side_effect=lambda types, section: {t.id: t for t in types},
        ),
        patch.object(reprocess_advice, "_velocity", return_value=0.0),
    ):
        yield


def _prices(buy, sell):
    """_market_unit_prices replacement from {type_id: price} tables."""
    tables = {"buy": buy, "sell": sell}
    return lambda ids, order_type="sell": {
        tid: tables[order_type].get(tid, 0.0) for tid in ids
    }


def _ore(**kwargs):
    asteroid, _ = EveCategory.objects.get_or_create(
        id=25, defaults={"name": "Asteroid", "published": True}
    )
    return EveTypeFactory(eve_group=EveGroupFactory(eve_category=asteroid), **kwargs)


def _config(corp, **kwargs):
    defaults = {
        "ore_yield_percent": 100.0,
        "scrap_yield_percent": 50.0,
        "reprocessing_tax_percent": 0.0,
        "sales_tax_percent": 0.0,
        "margin_percent": 0.0,
        "use_stock_needs": False,
    }
    defaults.update(kwargs)
    return CorpReprocessingConfig(corporation=corp, **defaults)


@pytest.mark.django_db
class TestYields:
    def test_only_whole_portions_reprocess_and_outputs_round_down(self):
        corp = EveCorporationInfoFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        ore = _ore(name="Veldspar", portion_size=100)
        EveTypeMaterial.objects.create(
            eve_type=ore, material_eve_type=tritanium, quantity=400
        )

        with patch(PRICES, side_effect=_prices({ore.id: 1.0}, {})):
            item = advise(
                [(ore, 250)], corp, config=_config(corp, ore_yield_percent=90.6)
            ).items[0]

        # 2 portions x 400 x 0.906 = 724.8 -> 724; 50 units left over
        assert [(m.eve_type.name, m.quantity) for m in item.materials] == [
            ("Tritanium", 724)
        ]
        assert item.leftover == 50

    def test_ore_and_scrap_use_their_own_yield(self):
        corp = EveCorporationInfoFactory()
        tritanium = EveTypeFactory()
        ore = _ore(portion_size=1)
        module = EveTypeFactory(portion_size=1)
        for eve_type in (ore, module):
            EveTypeMaterial.objects.create(
                eve_type=eve_type, material_eve_type=tritanium, quantity=100
            )

        with patch(PRICES, side_effect=_prices({}, {})):
            result = advise(
                [(ore, 1), (module, 1)],
                corp,
                config=_config(corp, ore_yield_percent=80, scrap_yield_percent=50),
            )

        assert [i.materials[0].quantity for i in result.items] == [80, 50]


@pytest.mark.django_db
class TestAdvice:
    def _scrap_item(self, sell_price_each, mineral_price):
        tritanium = EveTypeFactory(name="Tritanium")
        module = EveTypeFactory(name="Module", portion_size=1)
        EveTypeMaterial.objects.create(
            eve_type=module, material_eve_type=tritanium, quantity=100
        )
        prices = _prices(
            {module.id: sell_price_each, tritanium.id: mineral_price},
            {module.id: sell_price_each * 1.1, tritanium.id: mineral_price * 1.1},
        )
        return module, tritanium, prices

    def test_reprocess_when_minerals_are_worth_more(self):
        corp = EveCorporationInfoFactory()
        module, _, prices = self._scrap_item(sell_price_each=100, mineral_price=5)
        with patch(PRICES, side_effect=prices):
            result = advise([(module, 10)], corp, config=_config(corp))

        item = result.items[0]
        # sell 10 x 100 = 1,000; reprocess 10 x 50 trit x 5 = 2,500
        assert item.advice == REPROCESS
        assert item.difference == Decimal("1500")
        assert result.sell_all == Decimal("1000")
        assert result.reprocess.count == 1
        assert result.reprocess.value == Decimal("2500")
        assert result.gain == Decimal("1500")
        assert result.sell_materials[0].quantity == 500
        assert result.build_materials == []

    def test_sell_when_the_item_is_worth_more(self):
        corp = EveCorporationInfoFactory()
        module, _, prices = self._scrap_item(sell_price_each=1000, mineral_price=5)
        with patch(PRICES, side_effect=prices):
            result = advise([(module, 1)], corp, config=_config(corp))
        assert result.items[0].advice == SELL
        assert result.sell.value == Decimal("1000")
        assert result.sell_materials == []

    def test_small_difference_is_to_be_sorted(self):
        corp = EveCorporationInfoFactory()
        module, _, prices = self._scrap_item(sell_price_each=250, mineral_price=5.1)
        with patch(PRICES, side_effect=prices):
            item = advise(
                [(module, 1)], corp, config=_config(corp, margin_percent=5)
            ).items[0]
        assert (item.advice, item.sort_reason) == (SORT, SORT_CLOSE)  # 250 vs 255

    def test_reprocessing_tax_lowers_the_material_value(self):
        corp = EveCorporationInfoFactory()
        module, _, prices = self._scrap_item(sell_price_each=100, mineral_price=5)
        with patch(PRICES, side_effect=prices):
            item = advise(
                [(module, 1)], corp, config=_config(corp, reprocessing_tax_percent=10)
            ).items[0]
        assert item.reprocess_instant == Decimal("225")  # 250 - 10%

    def test_listed_route_deducts_broker_fee_and_sales_tax(self):
        corp = EveCorporationInfoFactory()
        TaxConfig.objects.create(corporation=corp, broker_fee_rate=1.5)
        module, _, prices = self._scrap_item(sell_price_each=100, mineral_price=5)
        config = _config(
            corp,
            sell_route=CorpReprocessingConfig.ROUTE_LISTED,
            sales_tax_percent=3.5,
        )
        with patch(PRICES, side_effect=prices):
            result = advise([(module, 1)], corp, config=config)
        item = result.items[0]
        # sell order at 110 - 5% fees = 104.5
        assert item.sell_listed == Decimal("104.50")
        assert result.route == CorpReprocessingConfig.ROUTE_LISTED

    def test_unpriced_items_are_to_be_sorted(self):
        corp = EveCorporationInfoFactory()
        fuel = EveTypeFactory(name="Oxygen Fuel Block")
        blueprint_category, _ = EveCategory.objects.get_or_create(
            id=9, defaults={"name": "Blueprint", "published": True}
        )
        blueprint = EveTypeFactory(
            eve_group=EveGroupFactory(eve_category=blueprint_category)
        )
        EveTypeMaterial.objects.create(
            eve_type=blueprint, material_eve_type=EveTypeFactory(), quantity=10
        )
        with patch(PRICES, side_effect=_prices({fuel.id: 10}, {})):
            result = advise([(fuel, 5), (blueprint, 1)], corp, config=_config(corp))
        assert [(i.reprocessable, i.advice, i.sort_reason) for i in result.items] == [
            (False, SELL, ""),
            (False, SORT, SORT_NO_PRICE),  # blueprint: no market price
        ]


@pytest.mark.django_db
class TestStockNeeds:
    def test_shortage_tips_the_advice_and_is_counted_once(self):
        corp = EveCorporationInfoFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        first = EveTypeFactory(name="Module A", portion_size=1)
        second = EveTypeFactory(name="Module B", portion_size=1)
        for module in (first, second):
            EveTypeMaterial.objects.create(
                eve_type=module, material_eve_type=tritanium, quantity=100
            )
        # Selling a module brings 51; its 50 tritanium only sell for 50 (buy
        # 1.0) but would cost 2.0 each to buy in, and the corp is short of 50.
        prices = _prices(
            {first.id: 51, second.id: 51, tritanium.id: 1.0},
            {first.id: 60, second.id: 60, tritanium.id: 2.0},
        )
        with patch(PRICES, side_effect=prices):
            result = advise(
                [(first, 1), (second, 1)],
                corp,
                config=_config(corp, use_stock_needs=True),
                deficits={tritanium.id: 50},
            )

        a, b = result.items
        assert a.advice == REPROCESS and a.fills_shortage == ["Tritanium"]
        assert a.in_house_bonus == Decimal("50")  # 50 x (2.0 - 1.0)
        assert b.advice == SELL and b.fills_shortage == []
        assert [(m.eve_type.name, m.quantity) for m in result.build_materials] == [
            ("Tritanium", 50)
        ]

    def test_stock_deficits_from_low_stock_targets(self):
        corp = EveCorporationInfoFactory()
        tritanium = EveTypeFactory()
        CorpItemConfig.objects.create(
            corporation=corp, item_type=tritanium, target_threshold=1000
        )
        assert stock_deficits(corp) == {tritanium.id: 1000}

    def test_config_defaults_without_a_saved_row(self):
        corp = EveCorporationInfoFactory()
        config = CorpReprocessingConfig.for_corporation(corp)
        assert config.pk is None and config.ore_yield_percent == 90.6


@pytest.mark.django_db
class TestBuildMaterials:
    def test_item_on_the_list_is_kept_for_building(self):
        corp = EveCorporationInfoFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        CorpBuildMaterial.objects.create(corporation=corp, eve_type=tritanium)

        with patch(PRICES, side_effect=_prices({tritanium.id: 4.0}, {tritanium.id: 5.0})):
            result = advise([(tritanium, 1000)], corp, config=_config(corp))

        item = result.items[0]
        assert item.advice == BUILD
        assert item.value == Decimal("5000")  # what buying it in would cost
        assert result.build.count == 1
        assert [(m.eve_type.name, m.quantity) for m in result.build_materials] == [
            ("Tritanium", 1000)
        ]

    def test_market_group_covers_the_groups_below_it(self):
        # Third Party
        from eveuniverse.models import EveMarketGroup

        corp = EveCorporationInfoFactory()
        materials = EveMarketGroup.objects.create(
            id=920001, name="Manufacture & Research", description=""
        )
        minerals = EveMarketGroup.objects.create(
            id=920002, name="Minerals", description="", parent_market_group=materials
        )
        pyerite = EveTypeFactory(name="Pyerite", eve_market_group=minerals)
        CorpBuildMaterial.objects.create(corporation=corp, eve_market_group=materials)

        with patch(PRICES, side_effect=_prices({pyerite.id: 10}, {pyerite.id: 11})):
            item = advise([(pyerite, 10)], corp, config=_config(corp)).items[0]

        assert item.advice == BUILD

    def test_reprocessed_build_materials_are_kept_and_valued_at_replacement(self):
        corp = EveCorporationInfoFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        module = EveTypeFactory(name="Module", portion_size=1)
        EveTypeMaterial.objects.create(
            eve_type=module, material_eve_type=tritanium, quantity=100
        )
        CorpBuildMaterial.objects.create(corporation=corp, eve_type=tritanium)
        # Sold: 60. Reprocessed and sold: 50 x 1.0 = 50. Kept: 50 x 2.0 = 100.
        prices = _prices({module.id: 60, tritanium.id: 1.0}, {tritanium.id: 2.0})

        with patch(PRICES, side_effect=prices):
            result = advise([(module, 1)], corp, config=_config(corp))

        item = result.items[0]
        assert item.advice == REPROCESS
        assert item.in_house_bonus == Decimal("50")
        assert result.sell_materials == []
        assert [(m.eve_type.name, m.quantity) for m in result.build_materials] == [
            ("Tritanium", 50)
        ]

    def test_slow_selling_item_is_to_be_sorted(self):
        corp = EveCorporationInfoFactory()
        fuel = EveTypeFactory(name="Fuel")
        with patch(PRICES, side_effect=_prices({fuel.id: 10}, {})), patch.object(
            reprocess_advice, "_velocity", return_value=100.0
        ):
            item = advise([(fuel, 1000)], corp, config=_config(corp)).items[0]
        assert (item.advice, item.sort_reason) == (SORT, SORT_SLOW)
        assert item.slow_sale


# --- Views ------------------------------------------------------------------


@pytest.fixture
def mock_static(monkeypatch):
    # Django
    from django.contrib.staticfiles.storage import staticfiles_storage

    monkeypatch.setattr(staticfiles_storage, "url", lambda name: f"/static/{name}")
    try:
        # Third Party
        from sri.templatetags import sri

        monkeypatch.setattr(
            sri, "sri_integrity_static", lambda path, algorithm_type=None: "x"
        )
    except ImportError:
        pass


def _user(corporation, perms=("basic_access",)):
    # Django
    from django.contrib.auth.models import Permission

    # Alliance Auth
    from allianceauth.authentication.models import CharacterOwnership

    from .factories import EveCharacterFactory, UserFactory

    user = UserFactory()
    character = EveCharacterFactory(
        corporation_id=corporation.corporation_id,
        corporation_name=corporation.corporation_name,
    )
    user.profile.main_character = character
    user.profile.save()
    CharacterOwnership.objects.create(
        user=user, character=character, owner_hash=f"r-{character.character_id}"
    )
    for codename in perms:
        user.user_permissions.add(Permission.objects.get(codename=codename))
    return user.__class__.objects.get(pk=user.pk), character


def _request(user, method="get", data=None):
    # Standard Library
    from unittest.mock import MagicMock

    # Django
    from django.contrib.messages.storage.fallback import FallbackStorage
    from django.test import RequestFactory

    request = getattr(RequestFactory(), method)("/", data or {})
    request.user = user
    request.session = MagicMock()
    request._messages = FallbackStorage(request)
    return request


def _contract_with_module(corp, seller=None):
    from .factories import (
        BuybackContractFactory,
        BuybackContractItemFactory,
        BuybackProgramFactory,
    )

    module = EveTypeFactory(name="Scrap Module", portion_size=1)
    EveTypeMaterial.objects.create(
        eve_type=module, material_eve_type=EveTypeFactory(name="Pyerite"), quantity=10
    )
    kwargs = {"character": seller} if seller else {}
    contract = BuybackContractFactory(
        program=BuybackProgramFactory(corporation=corp), status="MATCHED", **kwargs
    )
    BuybackContractItemFactory(contract=contract, eve_type=module, quantity=4)
    return contract


@pytest.mark.django_db
@pytest.mark.usefixtures("mock_static")
class TestAdviceOnPages:
    def test_programs_directors_see_the_advice_card(self):
        # AA Industry App
        from industry_reforged.views.buyback.member import buyback_contract_detail

        corp = EveCorporationInfoFactory()
        contract = _contract_with_module(corp)
        director, _ = _user(corp, perms=("basic_access", "corp_access"))

        with patch(PRICES, side_effect=_prices({}, {})):
            html = buyback_contract_detail(
                _request(director), contract.tracking_number
            ).content.decode()

        assert "What to do with these items" in html and "Scrap Module" in html

    def test_seller_does_not_see_the_advice_card(self):
        # AA Industry App
        from industry_reforged.views.buyback.member import buyback_contract_detail

        corp = EveCorporationInfoFactory()
        seller, character = _user(corp)
        contract = _contract_with_module(corp, seller=character)

        html = buyback_contract_detail(
            _request(seller), contract.tracking_number
        ).content.decode()

        assert "What to do with these items" not in html

    def test_review_queue_shows_the_advice_column(self):
        # AA Industry App
        from industry_reforged.views.buyback.director import director_buyback_review

        corp = EveCorporationInfoFactory()
        contract = _contract_with_module(corp)
        director, _ = _user(corp, perms=("basic_access", "corp_access"))

        # Pyerite worth far more than the module: reprocessing gains.
        pyerite_id = EveTypeMaterial.objects.get().material_eve_type_id
        prices = _prices({contract.items.get().eve_type_id: 1.0, pyerite_id: 100.0}, {})
        with patch(PRICES, side_effect=prices):
            html = director_buyback_review(_request(director)).content.decode()

        assert "fa-recycle" in html and "#sell-or-reprocess" in html

    def test_settings_are_saved_for_the_directors_corporation(self):
        # AA Industry App
        from industry_reforged.views.buyback.director import (
            director_config_buyback_reprocessing,
        )

        corp = EveCorporationInfoFactory()
        director, _ = _user(corp, perms=("basic_access", "corp_access"))
        response = director_config_buyback_reprocessing(
            _request(
                director,
                "post",
                {
                    "sell_route": "LISTED",
                    "ore_yield_percent": "87.5",
                    "scrap_yield_percent": "55",
                    "reprocessing_tax_percent": "1",
                    "sales_tax_percent": "3.37",
                    "margin_percent": "2",
                    "use_stock_needs": "on",
                    "broker_fee_percent": "1.5",
                },
            )
        )

        assert response.status_code == 302
        config = CorpReprocessingConfig.objects.get(corporation=corp)
        assert config.sell_route == "LISTED" and config.ore_yield_percent == 87.5
        assert TaxConfig.objects.get(corporation=corp).broker_fee_rate == 1.5


@pytest.mark.django_db
@pytest.mark.usefixtures("mock_static")
class TestBuildMaterialManagement:
    def test_add_item_for_own_corporation(self):
        from industry_reforged.views.buyback.director import (
            director_config_build_material_edit,
        )

        corp = EveCorporationInfoFactory()
        EveTypeFactory(name="Tritanium")
        director, _ = _user(corp, perms=("basic_access", "corp_access"))

        response = director_config_build_material_edit(
            _request(director, "post", {"item_name": "Tritanium", "note": "hulls"})
        )

        assert response.status_code == 302
        entry = CorpBuildMaterial.objects.get()
        assert entry.corporation == corp and entry.eve_type.name == "Tritanium"

    def test_duplicate_item_is_refused(self):
        from industry_reforged.views.buyback.director import (
            director_config_build_material_edit,
        )

        corp = EveCorporationInfoFactory()
        tritanium = EveTypeFactory(name="Tritanium")
        CorpBuildMaterial.objects.create(corporation=corp, eve_type=tritanium)
        director, _ = _user(corp, perms=("basic_access", "corp_access"))

        response = director_config_build_material_edit(
            _request(director, "post", {"item_name": "Tritanium"})
        )

        assert response.status_code == 200  # form shown again with the error
        assert CorpBuildMaterial.objects.count() == 1

    def test_other_corporations_entry_cannot_be_deleted(self):
        # Django
        from django.http import Http404

        from industry_reforged.views.buyback.director import (
            director_config_build_material_delete,
        )

        foreign = CorpBuildMaterial.objects.create(
            corporation=EveCorporationInfoFactory(), eve_type=EveTypeFactory()
        )
        director, _ = _user(
            EveCorporationInfoFactory(), perms=("basic_access", "corp_access")
        )
        with pytest.raises(Http404):
            director_config_build_material_delete(
                _request(director, "post"), foreign.id
            )
        assert CorpBuildMaterial.objects.filter(pk=foreign.pk).exists()
