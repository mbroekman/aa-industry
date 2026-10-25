"""Sell or reprocess? Advice for the items a buyback contract brings in.

Every item gets four values: sold straight to Jita buy orders ("instant") or
through a Jita sell order minus broker fee and sales tax ("listed"), either as
the item itself or as the materials it reprocesses into. The corporation's
reprocessing config picks the route the advice is based on and sets the yields.

Materials the corporation is short of (low-stock targets) can count as used
in-house, valued at what buying them at Jita sell would cost. A shortage is
shared out over the contract's items in order, so it is never counted twice.
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
EITHER = "EITHER"

SLOW_SALE_DAYS = 5
_VELOCITY_CACHE_TTL = 24 * 3600

ZERO = Decimal("0.00")


@dataclass
class MaterialYield:
    eve_type: EveType
    quantity: int
    in_house: int = 0  # units that fill a corporation shortage


@dataclass
class ItemAdvice:
    eve_type: EveType
    quantity: int
    reprocessable: bool
    sell_instant: Decimal = ZERO
    sell_listed: Decimal = ZERO
    reprocess_instant: Decimal = ZERO
    reprocess_listed: Decimal = ZERO
    in_house_bonus: Decimal = ZERO  # extra value of the materials used in-house
    leftover: int = 0  # units below one reprocessing portion
    materials: list = field(default_factory=list)
    advice: str = SELL
    difference: Decimal = ZERO  # reprocess minus sell on the chosen route
    slow_sale: bool = False

    @property
    def advantage(self) -> Decimal:
        """How much better the advised option is than the other one."""
        return abs(self.difference)

    @property
    def fills_shortage(self) -> list[str]:
        return [m.eve_type.name for m in self.materials if m.in_house]


@dataclass
class ContractAdvice:
    route: str
    items: list
    sell_all: Decimal = ZERO
    reprocess_all: Decimal = ZERO
    best_mix: Decimal = ZERO
    materials: list = field(default_factory=list)  # from items advised REPROCESS

    @property
    def gain(self) -> Decimal:
        """What following the advice adds over selling everything as-is."""
        return self.best_mix - self.sell_all


def _d(value) -> Decimal:
    return Decimal(str(value or 0.0))


def _cents(value: Decimal) -> Decimal:
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


def _yields(eve_type, quantity: int, config) -> tuple[list[MaterialYield], int]:
    """Materials from reprocessing `quantity` units, and the units left over.
    Only whole portions reprocess, and EVE rounds each output down."""
    materials = list(eve_type.materials.all())
    if not materials or buyback_data.is_blueprint(eve_type):
        return [], quantity
    portion = max(int(eve_type.portion_size or 1), 1)
    portions = quantity // portion
    leftover = quantity - portions * portion
    percent = (
        config.ore_yield_percent
        if buyback_data.is_ore(eve_type)
        else config.scrap_yield_percent
    )
    rate = float(percent or 0.0) / 100.0
    out = []
    for mat in materials:
        amount = math.floor(portions * mat.quantity * rate)
        if amount > 0:
            out.append(MaterialYield(eve_type=mat.material_eve_type, quantity=amount))
    return out, leftover


def advise(items, corporation, config=None, deficits=None) -> ContractAdvice:
    """`items` is a list of (EveType, quantity). `config` defaults to the
    corporation's CorpReprocessingConfig; `deficits` ({type_id: units}) to its
    low-stock shortages when the config asks for them."""
    from ..models import CorpReprocessingConfig, TaxConfig

    config = config or CorpReprocessingConfig.for_corporation(corporation)
    if deficits is None:
        deficits = {}
        if config.use_stock_needs:
            from .stock_needs import stock_deficits

            deficits = stock_deficits(corporation)
    remaining_need = dict(deficits)

    tax = TaxConfig.objects.filter(corporation=corporation).first()
    broker = _d(tax.broker_fee_rate if tax else 0.0)
    listed_factor = 1 - (broker + _d(config.sales_tax_percent)) / 100
    reprocess_tax = 1 - _d(config.reprocessing_tax_percent) / 100
    margin = _d(config.margin_percent) / 100
    listed_route = config.sell_route == CorpReprocessingConfig.ROUTE_LISTED

    types = buyback_data.ensure_sections(
        [eve_type for eve_type, _qty in items], EveType.Section.TYPE_MATERIALS
    )
    yields = {}
    for eve_type, quantity in items:
        eve_type = types.get(eve_type.id, eve_type)
        yields[eve_type.id] = (eve_type, *_yields(eve_type, quantity, config))

    price_ids = {eve_type.id for eve_type, _qty in items}
    for _type, mats, _left in yields.values():
        price_ids.update(m.eve_type.id for m in mats)
    buy = _market_unit_prices(list(price_ids), order_type="buy")
    sell = _market_unit_prices(list(price_ids), order_type="sell")

    result = ContractAdvice(route=config.sell_route, items=[])
    combined = {}

    for original, quantity in items:
        eve_type, materials, leftover = yields[original.id]
        item = ItemAdvice(
            eve_type=eve_type,
            quantity=quantity,
            reprocessable=bool(materials),
            materials=materials,
            leftover=leftover if materials else 0,
        )
        item.sell_instant = _d(buy.get(eve_type.id)) * quantity
        item.sell_listed = _d(sell.get(eve_type.id)) * quantity * listed_factor

        if materials:
            left_instant = _d(buy.get(eve_type.id)) * leftover
            left_listed = _d(sell.get(eve_type.id)) * leftover * listed_factor
            mats_instant = sum(
                (_d(buy.get(m.eve_type.id)) * m.quantity for m in materials), ZERO
            )
            mats_listed = sum(
                (_d(sell.get(m.eve_type.id)) * m.quantity for m in materials), ZERO
            )
            item.reprocess_instant = mats_instant * reprocess_tax + left_instant
            item.reprocess_listed = (
                mats_listed * listed_factor * reprocess_tax + left_listed
            )

            # In-house use: the units the corp is short of are worth their Jita
            # sell price (no fees) instead of what selling them would bring.
            for mat in materials:
                need = remaining_need.get(mat.eve_type.id, 0)
                if need <= 0:
                    continue
                mat.in_house = min(need, mat.quantity)
                sale_price = (
                    _d(sell.get(mat.eve_type.id)) * listed_factor
                    if listed_route
                    else _d(buy.get(mat.eve_type.id))
                )
                item.in_house_bonus += (
                    (_d(sell.get(mat.eve_type.id)) - sale_price)
                    * mat.in_house
                    * reprocess_tax
                )

        sell_value = item.sell_listed if listed_route else item.sell_instant
        reprocess_value = (
            item.reprocess_listed if listed_route else item.reprocess_instant
        ) + item.in_house_bonus

        if not materials:
            item.advice = SELL
        else:
            item.difference = reprocess_value - sell_value
            base = max(sell_value, reprocess_value)
            if base > 0 and abs(item.difference) < base * margin:
                item.advice = EITHER
            elif item.difference > 0:
                item.advice = REPROCESS
            else:
                item.advice = SELL

        # Only reserve the shortage for items we'll actually reprocess.
        if item.advice == REPROCESS:
            for mat in materials:
                if mat.in_house:
                    remaining_need[mat.eve_type.id] -= mat.in_house
                total = combined.setdefault(
                    mat.eve_type.id, MaterialYield(eve_type=mat.eve_type, quantity=0)
                )
                total.quantity += mat.quantity
                total.in_house += mat.in_house
        else:
            for mat in materials:
                mat.in_house = 0
            item.in_house_bonus = ZERO
            if materials:
                reprocess_value = (
                    item.reprocess_listed if listed_route else item.reprocess_instant
                )
                item.difference = reprocess_value - sell_value

        if listed_route:
            velocity = _velocity(eve_type.id)
            item.slow_sale = (
                item.advice != REPROCESS
                and velocity > 0
                and quantity > velocity * SLOW_SALE_DAYS
            )

        for name in (
            "sell_instant",
            "sell_listed",
            "reprocess_instant",
            "reprocess_listed",
            "in_house_bonus",
            "difference",
        ):
            setattr(item, name, _cents(getattr(item, name)))
        sell_value, reprocess_value = _cents(sell_value), _cents(reprocess_value)

        result.items.append(item)
        result.sell_all += sell_value
        result.reprocess_all += reprocess_value if materials else sell_value
        result.best_mix += reprocess_value if item.advice == REPROCESS else sell_value

    result.materials = sorted(combined.values(), key=lambda m: m.eve_type.name.lower())
    return result


def advise_contract(contract, deficits=None) -> ContractAdvice | None:
    """Advice for a buyback contract's appraised items, or None if it has none."""
    totals = {}
    for line in contract.items.select_related("eve_type__eve_group"):
        eve_type, quantity = totals.get(line.eve_type_id, (line.eve_type, 0))
        totals[line.eve_type_id] = (eve_type, quantity + line.quantity)
    if not totals:
        return None
    return advise(
        list(totals.values()), contract.program.corporation, deficits=deficits
    )
