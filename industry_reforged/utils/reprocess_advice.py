"""What to do with the items a buyback contract brings in.

Every item lands in one of four groups:

- SELL: worth more as-is.
- REPROCESS: worth more as the materials it reprocesses into.
- BUILD: on the corporation's build-material list; kept, never sold.
- SORT ("to be sorted"): a director decides. No price is known, selling and
    reprocessing are within the configured margin, or the advice would be to
    sell but the quantity is more than a few days of Jita trade volume.

Values: sold straight to Jita buy orders ("instant") or through a Jita sell
order minus broker fee and sales tax ("listed"), as the item itself or as its
reprocessed materials (whole batches only, after reprocessing tax). The
corporation's reprocessing config picks the route the advice is based on.

Reprocessed materials that are build materials, or that fill a low-stock
shortage, count as used in-house: valued at what buying them at Jita sell
would cost. A shortage is shared out over the contract's items in order, so
it is never counted twice.
"""

# Standard Library
import math
from dataclasses import dataclass, field
from decimal import Decimal

# Third Party
from eveuniverse.models import EveType

# Django
from django.core.cache import cache

from . import buyback_data
from .pricing_engine import _market_unit_prices

SELL = "SELL"
REPROCESS = "REPROCESS"
BUILD = "BUILD"
SORT = "SORT"
CATEGORIES = (SELL, REPROCESS, BUILD, SORT)

SORT_NO_PRICE = "no_price"
SORT_CLOSE = "close"
SORT_SLOW = "slow"

SLOW_SALE_DAYS = 5
_VELOCITY_CACHE_TTL = 24 * 3600

ZERO = Decimal("0.00")


@dataclass
class MaterialYield:
    eve_type: EveType
    quantity: int
    in_house: int = 0  # units kept: build material or filling a shortage
    build_material: bool = False


@dataclass
class ItemAdvice:
    eve_type: EveType
    quantity: int
    reprocessable: bool
    sell_instant: Decimal = ZERO
    sell_listed: Decimal = ZERO
    reprocess_instant: Decimal = ZERO
    reprocess_listed: Decimal = ZERO
    in_house_bonus: Decimal = ZERO  # extra value of the materials kept in-house
    replacement_value: Decimal = ZERO  # what buying the item at Jita sell costs
    leftover: int = 0  # units below one reprocessing batch
    materials: list = field(default_factory=list)
    advice: str = SELL
    sort_reason: str = ""
    difference: Decimal = ZERO  # reprocess minus sell on the chosen route
    value: Decimal = ZERO  # the item's value in its group
    slow_sale: bool = False

    @property
    def advantage(self) -> Decimal:
        """How much better the advised option is than the other one."""
        return abs(self.difference)

    @property
    def fills_shortage(self) -> list[str]:
        return [m.eve_type.name for m in self.materials if m.in_house]


@dataclass
class CategoryTotal:
    count: int = 0
    value: Decimal = ZERO


@dataclass
class ContractAdvice:
    route: str
    items: list
    sell_all: Decimal = ZERO  # everything sold as-is on the chosen route
    totals: dict = field(
        default_factory=lambda: {key: CategoryTotal() for key in CATEGORIES}
    )
    build_materials: list = field(default_factory=list)  # kept for building
    sell_materials: list = field(default_factory=list)  # reprocessed, to sell

    @property
    def gain(self) -> Decimal:
        """What reprocessing the REPROCESS items adds over selling them."""
        return sum((i.difference for i in self.items if i.advice == REPROCESS), ZERO)

    def by_category(self, category) -> list:
        return [i for i in self.items if i.advice == category]

    @property
    def ordered_items(self) -> list:
        """Items grouped as Sell, Reprocess, Build material, To be sorted."""
        return sorted(self.items, key=lambda i: CATEGORIES.index(i.advice))

    # Template helpers: Django templates can't index a dict with a constant.
    @property
    def sell(self):
        return self.totals[SELL]

    @property
    def reprocess(self):
        return self.totals[REPROCESS]

    @property
    def build(self):
        return self.totals[BUILD]

    @property
    def sort(self):
        return self.totals[SORT]


def _d(value) -> Decimal:
    return Decimal(str(value or 0.0))


def _cents(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def _velocity(type_id: int) -> float:
    """Average daily Jita volume over 30 days, cached for a day."""
    key = f"industry_reforged_market_velocity_{type_id}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    from .ai_engine import get_market_velocity

    try:
        velocity = float(get_market_velocity(type_id, days=30) or 0.0)
    except Exception:
        velocity = 0.0
    cache.set(key, velocity, _VELOCITY_CACHE_TTL)
    return velocity


class BuildMaterials:
    """The corporation's build-material list: items and market groups (a
    market group also covers every group below it)."""

    def __init__(self, corporation):
        from ..models import CorpBuildMaterial

        entries = CorpBuildMaterial.objects.filter(corporation=corporation)
        self.type_ids = set()
        self.market_group_ids = set()
        for entry in entries:
            if entry.eve_type_id:
                self.type_ids.add(entry.eve_type_id)
            else:
                self.market_group_ids.add(entry.eve_market_group_id)

    def __bool__(self):
        return bool(self.type_ids or self.market_group_ids)

    def covers(self, eve_type) -> bool:
        if eve_type.id in self.type_ids:
            return True
        if not self.market_group_ids:
            return False
        return bool(
            self.market_group_ids & set(buyback_data.market_group_ancestry(eve_type))
        )


def _yields(eve_type, quantity: int, config) -> tuple[list[MaterialYield], int]:
    """Materials from reprocessing `quantity` units, and the units left over.
    Only whole batches reprocess, and EVE rounds each output down."""
    materials = list(eve_type.materials.select_related("material_eve_type"))
    if not materials or buyback_data.is_blueprint(eve_type):
        return [], quantity
    batch = max(int(eve_type.portion_size or 1), 1)
    batches = quantity // batch
    leftover = quantity - batches * batch
    percent = (
        config.ore_yield_percent
        if buyback_data.is_ore(eve_type)
        else config.scrap_yield_percent
    )
    rate = float(percent or 0.0) / 100.0
    out = []
    for mat in materials:
        amount = math.floor(batches * mat.quantity * rate)
        if amount > 0:
            out.append(MaterialYield(eve_type=mat.material_eve_type, quantity=amount))
    return out, leftover


def _with_market_groups(eve_types, build: BuildMaterials) -> dict:
    """{type_id: EveType} with market groups loaded when the list needs them."""
    if not build.market_group_ids:
        return {t.id: t for t in eve_types}
    return buyback_data.ensure_sections(eve_types, EveType.Section.MARKET_GROUPS)


def _add_material(target: dict, mat: MaterialYield, quantity: int, build: bool):
    total = target.setdefault(
        mat.eve_type.id,
        MaterialYield(eve_type=mat.eve_type, quantity=0, build_material=build),
    )
    total.quantity += quantity


def advise(
    items, corporation, config=None, deficits=None, build=None
) -> ContractAdvice:
    """`items` is a list of (EveType, quantity). `config` defaults to the
    corporation's CorpReprocessingConfig, `deficits` ({type_id: units}) to its
    low-stock shortages when the config asks for them, and `build` to its
    build-material list."""
    from ..models import CorpReprocessingConfig, TaxConfig

    config = config or CorpReprocessingConfig.for_corporation(corporation)
    if deficits is None:
        deficits = {}
        if config.use_stock_needs:
            from .stock_needs import stock_deficits

            deficits = stock_deficits(corporation)
    remaining_need = dict(deficits)
    build = build if build is not None else BuildMaterials(corporation)

    tax = TaxConfig.objects.filter(corporation=corporation).first()
    broker = _d(tax.broker_fee_rate if tax else 0.0)
    listed_factor = 1 - (broker + _d(config.sales_tax_percent)) / 100
    reprocess_tax = 1 - _d(config.reprocessing_tax_percent) / 100
    margin = _d(config.margin_percent) / 100
    listed_route = config.sell_route == CorpReprocessingConfig.ROUTE_LISTED

    types = _with_market_groups([eve_type for eve_type, _qty in items], build)
    types.update(
        buyback_data.ensure_sections(
            [types[eve_type.id] for eve_type, _qty in items],
            EveType.Section.TYPE_MATERIALS,
        )
    )

    yields = {}
    material_types = {}
    for original, quantity in items:
        eve_type = types.get(original.id, original)
        if build.covers(eve_type):
            yields[original.id] = (eve_type, [], 0, True)
            continue
        materials, leftover = _yields(eve_type, quantity, config)
        yields[original.id] = (eve_type, materials, leftover, False)
        for mat in materials:
            material_types[mat.eve_type.id] = mat.eve_type
    material_types = _with_market_groups(list(material_types.values()), build)

    price_ids = {eve_type.id for eve_type, _qty in items} | set(material_types)
    buy = _market_unit_prices(list(price_ids), order_type="buy")
    sell = _market_unit_prices(list(price_ids), order_type="sell")

    def sale_price(type_id) -> Decimal:
        if listed_route:
            return _d(sell.get(type_id)) * listed_factor
        return _d(buy.get(type_id))

    result = ContractAdvice(route=config.sell_route, items=[])
    build_list, sell_list = {}, {}

    for original, quantity in items:
        eve_type, materials, leftover, is_build = yields[original.id]
        item = ItemAdvice(
            eve_type=eve_type,
            quantity=quantity,
            reprocessable=bool(materials),
            materials=materials,
            leftover=leftover if materials else 0,
        )
        item.sell_instant = _d(buy.get(eve_type.id)) * quantity
        item.sell_listed = _d(sell.get(eve_type.id)) * quantity * listed_factor
        item.replacement_value = _d(sell.get(eve_type.id)) * quantity
        sell_value = item.sell_listed if listed_route else item.sell_instant

        if is_build:
            item.advice = BUILD
            item.value = item.replacement_value
            build_list.setdefault(
                eve_type.id,
                MaterialYield(eve_type=eve_type, quantity=0, build_material=True),
            ).quantity += quantity
        else:
            reprocess_value = ZERO
            if materials:
                left_instant = _d(buy.get(eve_type.id)) * leftover
                left_listed = _d(sell.get(eve_type.id)) * leftover * listed_factor
                item.reprocess_instant = (
                    sum(
                        (_d(buy.get(m.eve_type.id)) * m.quantity for m in materials),
                        ZERO,
                    )
                    * reprocess_tax
                    + left_instant
                )
                item.reprocess_listed = (
                    sum(
                        (_d(sell.get(m.eve_type.id)) * m.quantity for m in materials),
                        ZERO,
                    )
                    * listed_factor
                    * reprocess_tax
                    + left_listed
                )
                # Kept materials are worth what buying them would cost.
                for mat in materials:
                    mat_type = material_types.get(mat.eve_type.id, mat.eve_type)
                    if build.covers(mat_type):
                        mat.build_material = True
                        mat.in_house = mat.quantity
                    else:
                        mat.in_house = min(
                            max(remaining_need.get(mat.eve_type.id, 0), 0),
                            mat.quantity,
                        )
                    if mat.in_house:
                        item.in_house_bonus += (
                            (
                                _d(sell.get(mat.eve_type.id))
                                - sale_price(mat.eve_type.id)
                            )
                            * mat.in_house
                            * reprocess_tax
                        )
                reprocess_value = (
                    item.reprocess_listed if listed_route else item.reprocess_instant
                ) + item.in_house_bonus
                item.difference = reprocess_value - sell_value

            if sell_value <= 0 and reprocess_value <= 0:
                item.advice, item.sort_reason = SORT, SORT_NO_PRICE
            elif not materials:
                item.advice = SELL
            else:
                base = max(sell_value, reprocess_value)
                if abs(item.difference) < base * margin:
                    item.advice, item.sort_reason = SORT, SORT_CLOSE
                elif item.difference > 0:
                    item.advice = REPROCESS
                else:
                    item.advice = SELL

            if item.advice == SELL:
                velocity = _velocity(eve_type.id)
                item.slow_sale = velocity > 0 and quantity > velocity * SLOW_SALE_DAYS
                if item.slow_sale:
                    item.advice, item.sort_reason = SORT, SORT_SLOW

            if item.advice == REPROCESS:
                item.value = reprocess_value
                for mat in materials:
                    if mat.in_house and not mat.build_material:
                        remaining_need[mat.eve_type.id] -= mat.in_house
                    if mat.in_house:
                        _add_material(build_list, mat, mat.in_house, True)
                    if mat.quantity > mat.in_house:
                        _add_material(
                            sell_list, mat, mat.quantity - mat.in_house, False
                        )
            else:
                # Nothing gets reprocessed, so nothing is kept from it.
                for mat in materials:
                    mat.in_house = 0
                if materials:
                    item.difference = (
                        item.reprocess_listed
                        if listed_route
                        else item.reprocess_instant
                    ) - sell_value
                item.in_house_bonus = ZERO
                item.value = sell_value

        for name in (
            "sell_instant",
            "sell_listed",
            "reprocess_instant",
            "reprocess_listed",
            "in_house_bonus",
            "replacement_value",
            "difference",
            "value",
        ):
            setattr(item, name, _cents(getattr(item, name)))

        result.items.append(item)
        result.sell_all += _cents(sell_value)
        total = result.totals[item.advice]
        total.count += 1
        total.value += item.value

    def ordered(materials):
        return sorted(materials.values(), key=lambda m: m.eve_type.name.lower())

    result.build_materials = ordered(build_list)
    result.sell_materials = ordered(sell_list)
    return result


def advise_contract(contract, deficits=None, build=None) -> ContractAdvice | None:
    """Advice for a buyback contract's appraised items, or None if it has none."""
    totals = {}
    for line in contract.items.select_related("eve_type__eve_group"):
        eve_type, quantity = totals.get(line.eve_type_id, (line.eve_type, 0))
        totals[line.eve_type_id] = (eve_type, quantity + line.quantity)
    if not totals:
        return None
    return advise(
        list(totals.values()),
        contract.program.corporation,
        deficits=deficits,
        build=build,
    )
