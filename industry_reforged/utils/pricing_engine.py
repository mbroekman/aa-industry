# Standard Library
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

# Third Party
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

ESI_MARKET_ORDERS_URL = "https://esi.evetech.net/latest/markets/{region_id}/orders/"
DEFAULT_REGION_ID = 10000002  # The Forge (Jita)
DEFAULT_STATION_ID = 60003760  # Jita IV - Moon 4 - Caldari Navy Assembly Plant
JITA_STATION_ID = DEFAULT_STATION_ID


def calculate_percentile_price(
    orders, percentile=0.05, station_id=DEFAULT_STATION_ID, order_type="sell"
):
    """
    Calculate the volume-weighted percentile sell price from ESI market orders.
    Matches standard Jita 5% Sell logic.

    Args:
        orders (list[dict]): List of market order dicts from ESI.
        percentile (float): Percentile threshold (default 0.05 for 5%).
        station_id (int): Primary station ID (default 60003760 for Jita 4-4).

    Returns:
        float: Calculated percentile price, or lowest sell price, or 0.0 if empty.
    """
    if not orders:
        return 0.0

    is_buy = order_type == "buy"
    filtered_orders = [o for o in orders if o.get("is_buy_order", False) == is_buy]
    if not filtered_orders:
        return 0.0

    # Prefer station orders (e.g. Jita 4-4)
    station_orders = [o for o in filtered_orders if o.get("location_id") == station_id]
    target_orders = station_orders if station_orders else filtered_orders

    # Sort ascending by price for sell orders (lowest first)
    # Sort descending by price for buy orders (highest first)
    sorted_orders = sorted(
        target_orders, key=lambda x: float(x.get("price", 0.0)), reverse=is_buy
    )
    if not sorted_orders:
        return 0.0

    total_volume = sum(int(o.get("volume_remain", 0)) for o in sorted_orders)
    if total_volume <= 0:
        return float(sorted_orders[0].get("price", 0.0))

    threshold_volume = total_volume * percentile
    accumulated_volume = 0

    for order in sorted_orders:
        accumulated_volume += int(order.get("volume_remain", 0))
        if accumulated_volume >= threshold_volume:
            return float(order.get("price", 0.0))

    return float(sorted_orders[-1].get("price", 0.0))


def fetch_single_market_price(
    type_id,
    region_id=DEFAULT_REGION_ID,
    station_id=DEFAULT_STATION_ID,
    session=None,
    order_type="sell",
):
    """
    Fetch market orders for a single type_id from ESI and return the 5% percentile sell price.
    Falls back to EveType average/adjusted price if ESI is unavailable or empty.
    """
    req_session = session if session is not None else requests.Session()
    url = ESI_MARKET_ORDERS_URL.format(region_id=region_id)
    params = {
        "datasource": "tranquility",
        "order_type": "all",
        "type_id": type_id,
    }
    headers = {
        "User-Agent": "aa-industry-reforged / Direct ESI Market Client",
        "Accept": "application/json",
    }

    try:
        res = req_session.get(url, params=params, headers=headers, timeout=5)
        if res.status_code == 200:
            orders = res.json()
            price = calculate_percentile_price(
                orders, percentile=0.05, station_id=station_id, order_type=order_type
            )
            if price > 0.0:
                return float(price)
    except Exception as e:
        logger.warning(f"ESI market order fetch failed for type_id {type_id}: {e}")

    # Fallback to EveMarketPrice from django-eveuniverse if available
    try:
        # Third Party
        from eveuniverse.models import EveMarketPrice

        market_price = EveMarketPrice.objects.filter(eve_type_id=type_id).first()
        if market_price:
            for attr in ("average_price", "adjusted_price"):
                val = getattr(market_price, attr, None)
                if val is not None and float(val) > 0.0:
                    return float(val)
    except Exception:
        pass

    # Final fallback to fuzzwork if price is 0.0 (especially for items like PLEX missing from ESI)
    try:
        fuzz_url = f"https://market.fuzzwork.co.uk/aggregates/?station={station_id}&types={type_id}"
        fuzz_res = req_session.get(fuzz_url, timeout=5)
        if fuzz_res.status_code == 200:
            fuzz_data = fuzz_res.json()
            if str(type_id) in fuzz_data:
                fuzz_price = fuzz_data[str(type_id)].get(order_type, {}).get("percentile")
                if fuzz_price and float(fuzz_price) > 0.0:
                    return float(fuzz_price)
    except Exception as e:
        logger.warning(f"Fuzzwork fallback failed for type_id {type_id}: {e}")

    return 0.0


def get_market_prices(
    type_ids,
    region_id=DEFAULT_REGION_ID,
    station_id=DEFAULT_STATION_ID,
    order_type="sell",
):
    """
    Fetch market prices (Jita 5% Sell) for a list of type IDs using direct CCP ESI API
    with concurrent batching and caching.
    Returns a dict mapping type_id (int) -> float.
    """
    if not type_ids:
        return {}

    # Django
    from django.core.cache import cache

    prices = {}
    missing_ids = []

    # Check cache first
    for tid in type_ids:
        int_tid = int(tid)
        cache_key = f"esi_market_price_{order_type}_{region_id}_{int_tid}"
        cached_price = cache.get(cache_key)
        if cached_price is not None:
            prices[int_tid] = cached_price
        else:
            missing_ids.append(int_tid)

    if not missing_ids:
        return prices

    # Use ThreadPoolExecutor to fetch missing IDs concurrently with persistent session
    session = requests.Session()
    retries = Retry(total=2, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=15, pool_maxsize=30, max_retries=retries)
    session.mount("https://", adapter)

    max_workers = min(15, len(missing_ids))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_tid = {
            executor.submit(
                fetch_single_market_price,
                tid,
                region_id=region_id,
                station_id=station_id,
                session=session,
                order_type=order_type,
            ): tid
            for tid in missing_ids
        }
        for future in as_completed(future_to_tid):
            tid = future_to_tid[future]
            try:
                price = future.result()
            except Exception as e:
                logger.error(f"Error fetching price for type_id {tid}: {e}")
                price = 0.0

            prices[tid] = price
            cache_key = f"esi_market_price_{order_type}_{region_id}_{tid}"
            ttl = 3600 if price > 0.0 else 60
            cache.set(cache_key, price, ttl)

    return prices


def get_fuzzwork_prices(type_ids):
    """
    Deprecated alias for get_market_prices(). Maintained for backwards compatibility.
    """
    return get_market_prices(type_ids)


def get_prices_with_overrides(type_ids, corporation=None):
    """
    Fetch Jita prices for a list of type IDs, but apply any manual price
    overrides defined in CorpItemConfig for the given corporation.
    Blueprints (category_id 9) are ignored from ESI and default to 0 unless overridden.
    """
    from eveuniverse.models import EveType

    blueprints = set(
        EveType.objects.filter(
            id__in=type_ids, eve_group__eve_category_id=9
        ).values_list("id", flat=True)
    )
    non_bp_type_ids = [t for t in type_ids if t not in blueprints]

    prices = get_market_prices(non_bp_type_ids)
    
    for bp_id in blueprints:
        prices[bp_id] = 0.0

    if corporation:
        from ..models import CorpItemConfig

        configs = CorpItemConfig.objects.filter(
            corporation=corporation,
            item_type_id__in=type_ids,
            manual_price__isnull=False,
        )
        for config in configs:
            prices[config.item_type_id] = float(config.manual_price)

    return prices


def get_detailed_prices(type_ids, corporation=None):
    """
    Fetch Jita prices and return detailed breakdown with both original and final prices.
    Blueprints (category_id 9) are ignored from ESI and default to 0 unless overridden.
    """
    from eveuniverse.models import EveType

    blueprints = set(
        EveType.objects.filter(
            id__in=type_ids, eve_group__eve_category_id=9
        ).values_list("id", flat=True)
    )
    non_bp_type_ids = [t for t in type_ids if t not in blueprints]

    prices = get_market_prices(non_bp_type_ids)
    detailed = {}
    
    for tid in type_ids:
        if tid in blueprints:
            detailed[tid] = {"original_jita_price": 0.0, "final_price": 0.0}
        else:
            val = prices.get(tid, 0.0)
            detailed[tid] = {"original_jita_price": val, "final_price": val}

    if corporation:
        from ..models import CorpItemConfig

        configs = CorpItemConfig.objects.filter(
            corporation=corporation,
            item_type_id__in=type_ids,
            manual_price__isnull=False,
        )
        for config in configs:
            detailed[config.item_type_id]["final_price"] = float(config.manual_price)

    return detailed


def calculate_quote(parsed_items, corporation=None, ignore_discounts=False):
    """
    Takes a dict of {EveType: quantity} and an optional EveCorporationInfo.
    Returns:
    - total_price: Decimal
    - item_details: List of dicts with price breakdown
    """
    type_ids = [t.id for t in parsed_items.keys()]
    market_prices = get_prices_with_overrides(type_ids, corporation)

    config = None
    corp_pricing = None
    if corporation:
        from ..models import CorpPricingConfig

        config = CorpPricingConfig.objects.filter(corporation=corporation).first()
        from ..models.config import CorporationPricingConfig

        corp_pricing = CorporationPricingConfig.objects.filter(
            corporation=corporation
        ).first()

    total_price = Decimal("0.00")
    item_details = []

    for eve_type, quantity in parsed_items.items():
        base_price = market_prices.get(eve_type.id, 0.0)

        discount_percent = 0.0
        if config and not ignore_discounts:
            # Check specific type discount first
            from ..models import CorpTypeDiscount

            type_discount = CorpTypeDiscount.objects.filter(
                config=config, eve_type=eve_type
            ).first()
            if type_discount:
                discount_percent = type_discount.discount_percent
            else:
                discount_percent = config.default_discount_percent

        discount_multiplier = (100.0 - discount_percent) / 100.0
        final_price_per_unit = Decimal(str(base_price * discount_multiplier)).quantize(
            Decimal("0.01")
        )

        # True Material Cost and Minimum Margin Logic
        true_cost_per_unit = Decimal("0.00")
        if corporation:
            true_cost_per_unit = calculate_bom_cost({eve_type: 1}, corporation)

        minimum_margin_floor = Decimal("0.00")
        if corp_pricing:
            minimum_margin_floor = corp_pricing.minimum_margin_floor

        if true_cost_per_unit > 0:
            margin_multiplier = Decimal("1.00") + (
                minimum_margin_floor / Decimal("100.00")
            )
            minimum_price_per_unit = (true_cost_per_unit * margin_multiplier).quantize(
                Decimal("0.01")
            )

            # Final quote is the MAX of the discounted market price and the minimum margin price
            if minimum_price_per_unit > final_price_per_unit:
                final_price_per_unit = minimum_price_per_unit
                if base_price > 0:
                    effective_discount = Decimal("100.0") - (
                        final_price_per_unit / Decimal(str(base_price))
                    ) * Decimal("100.0")
                    discount_percent = float(
                        effective_discount.quantize(Decimal("0.01"))
                    )
                else:
                    discount_percent = 0.0

        line_total = final_price_per_unit * quantity
        total_price += line_total

        item_details.append(
            {
                "eve_type": eve_type,
                "quantity": quantity,
                "base_price_per_unit": Decimal(str(base_price)).quantize(
                    Decimal("0.01")
                ),
                "discount_percent": discount_percent,
                "final_price_per_unit": final_price_per_unit,
                "line_total": line_total,
                "true_cost_per_unit": true_cost_per_unit,
            }
        )

    return total_price, item_details


def calculate_bom_cost(parsed_items, corporation=None):
    """
    Calculate the True Material Cost of the parsed_items based on a flattened BOM.
    """
    from .bom_engine import get_recursive_bom_tree

    # 1. Determine material valuation method
    valuation_method = "JITA_SELL"
    if corporation:
        from ..models import CorporationPricingConfig

        config = CorporationPricingConfig.objects.filter(
            corporation=corporation
        ).first()
        if config:
            valuation_method = config.material_valuation_method

    # 2. Extract CorpItemConfig rules
    config_dict = {}
    if corporation:
        from ..models import CorpItemConfig

        configs = CorpItemConfig.objects.filter(corporation=corporation)
        for c in configs:
            config_dict[c.item_type_id] = {
                "exclude_from_orders": getattr(c, "exclude_from_orders", False),
                "build_or_buy": getattr(c, "build_or_buy", "BUILD"),
            }

    # 3. Calculate flattened BOM
    raw_materials_qty = {}

    for eve_type, quantity in parsed_items.items():
        tree = get_recursive_bom_tree(
            type_id=eve_type.id,
            name=eve_type.name,
            quantity=quantity,
            config_dict=config_dict,
            corp_info=corporation,
        )

        def _flatten(node):
            if node.get("activity_id") == 5:
                # Do not include Blueprint copies (BPOs) as a raw material cost
                return
            if not node.get("sub_materials"):
                tid = node["type_id"]
                qty = node["quantity"]
                raw_materials_qty[tid] = raw_materials_qty.get(tid, 0) + qty
            else:
                for mat in node["sub_materials"]:
                    _flatten(mat)

        _flatten(tree)

    # 4. Fetch unit prices for raw materials based on valuation_method
    type_ids = list(raw_materials_qty.keys())

    if valuation_method == "JITA_BUY":
        base_prices = get_market_prices(type_ids, order_type="buy")
    else:
        base_prices = get_market_prices(type_ids, order_type="sell")

    # Apply manual overrides regardless of the valuation method
    if corporation:
        from ..models import CorpItemConfig

        configs = CorpItemConfig.objects.filter(
            corporation=corporation,
            item_type_id__in=type_ids,
            manual_price__isnull=False,
        )
        for config in configs:
            base_prices[config.item_type_id] = float(config.manual_price)

    # 5. Calculate Total Cost
    total_bom_cost = Decimal("0.00")
    for tid, qty in raw_materials_qty.items():
        price = Decimal(str(base_prices.get(tid, 0.0)))
        total_bom_cost += price * qty

    return total_bom_cost


# --- Buyback appraisal ---------------------------------------------------
#
# Appended here rather than in a separate module: the buyback appraisal is
# the same "value an item" concept get_market_prices/get_prices_with_overrides
# already own, and keeping it in one file means there is only ever one cache
# format and one place to fix a pricing bug.


def get_reprocessing_value(eve_type, quantity, efficiency=1.0) -> Decimal | None:
    """
    Reprocessing valuation via eveuniverse's EveType.materials (SDE reprocessing
    yield), valued at the refined materials' market sell price. Returns None
    (never False/0) when the item has no reprocessing output at all, so callers
    never hit a "0 vs. unset" ambiguity.
    """
    materials = list(eve_type.materials.all())
    if not materials:
        return None

    material_ids = [m.material_eve_type_id for m in materials]
    prices = get_market_prices(material_ids)

    total = Decimal("0.00")
    for mat in materials:
        unit_price = Decimal(str(prices.get(mat.material_eve_type_id, 0.0)))
        yielded_per_unit = Decimal(str(mat.quantity)) * Decimal(str(efficiency))
        total += unit_price * yielded_per_unit

    return total * quantity


def get_item_value_variants(eve_type, quantity) -> dict:
    """
    Single parameterized replacement for the "raw/compressed/refined/NPC
    best-of" concept: returns only the valuation keys that actually apply to
    this item, using explicit `is not None` checks rather than a `False`-as-
    sentinel pattern. Compressed/raw ore items are themselves distinct
    EveTypes with their own market price, so "best of market vs. reprocessed"
    already covers raw ore without any ore-specific special-casing.
    """
    variants = {}

    market_price = get_market_prices([eve_type.id]).get(eve_type.id, 0.0)
    if market_price and market_price > 0.0:
        variants["market"] = Decimal(str(market_price)) * quantity

    reprocessed = get_reprocessing_value(eve_type, quantity)
    if reprocessed is not None and reprocessed > 0:
        variants["reprocessed"] = reprocessed

    return variants


def calculate_price_density_tax(unit_price: Decimal, packaged_volume, program) -> Decimal:
    """
    Tax on bulky, low ISK/m3 items, consistently parameterized on
    packaged_volume (the source project's documented bug divided by the wrong
    volume field in one of its four copies of this logic - with a single
    copy, that bug class is structurally impossible).

    Returns the ISK amount to deduct from unit_price, or 0.00 if the program
    has no density threshold configured or the item doesn't qualify.
    """
    threshold = getattr(program, "price_density_threshold", 0.0) or 0.0
    tax_percent = getattr(program, "price_density_tax_percent", 0.0) or 0.0
    if threshold <= 0 or tax_percent <= 0 or not packaged_volume or packaged_volume <= 0:
        return Decimal("0.00")

    density = unit_price / Decimal(str(packaged_volume))
    if density >= Decimal(str(threshold)):
        return Decimal("0.00")

    return (unit_price * Decimal(str(tax_percent)) / Decimal("100.00")).quantize(Decimal("0.01"))


def calculate_buyback_quote(parsed_items, program) -> tuple[Decimal, list[dict]]:
    """
    The buyback calculator's entry point: takes {EveType: quantity} and a
    BuybackProgram, returns (total_price, item_details) in the same shape
    calculate_quote() already uses, so the calculator view can be built the
    same way views/orders/create.py already builds on calculate_quote().

    Never raises on an unrecognized valuation path (the source project's
    `raise f"Unknown pricing method: ..."` bug - raising a string isn't valid
    exception semantics) - logs a warning and returns a 0-value line instead.
    """
    from ..models.buyback import BuybackWatchlistItem

    watchlist = {
        w.eve_type_id: w
        for w in BuybackWatchlistItem.objects.filter(
            program=program, eve_type_id__in=[t.id for t in parsed_items.keys()]
        )
    }

    total_price = Decimal("0.00")
    item_details = []

    for eve_type, quantity in parsed_items.items():
        watchlist_entry = watchlist.get(eve_type.id)
        if watchlist_entry and watchlist_entry.blocks_submission:
            item_details.append(
                {
                    "eve_type": eve_type,
                    "quantity": quantity,
                    "unit_price": Decimal("0.00"),
                    "line_total": Decimal("0.00"),
                    "base_unit_price": Decimal("0.00"),
                    "base_line_total": Decimal("0.00"),
                    "value_source": None,
                    "blocked": True,
                    "flagged": False,
                    "watchlist_reason": watchlist_entry.reason,
                }
            )
            continue

        variants = get_item_value_variants(eve_type, quantity)
        if not variants:
            logger.warning(
                f"No valuation method applies to {eve_type.name} ({eve_type.id}) - valuing at 0."
            )
            line_total = Decimal("0.00")
            value_source = None
        else:
            value_source, line_total = max(variants.items(), key=lambda kv: kv[1])

        base_unit_price = (line_total / quantity).quantize(Decimal("0.01")) if quantity else Decimal("0.00")

        modifier = Decimal(str(program.price_modifier_percent or 0.0)) / Decimal("100.00")
        unit_price = (base_unit_price * (Decimal("1.00") + modifier)).quantize(Decimal("0.01"))

        packaged_volume = eve_type.packaged_volume or eve_type.volume
        density_tax = calculate_price_density_tax(unit_price, packaged_volume, program)
        unit_price = max(Decimal("0.00"), unit_price - density_tax)

        line_total = unit_price * quantity
        total_price += line_total

        item_details.append(
            {
                "eve_type": eve_type,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
                "base_unit_price": base_unit_price,
                "base_line_total": base_unit_price * quantity,
                "value_source": value_source,
                "blocked": False,
                "flagged": bool(watchlist_entry),
                "watchlist_reason": watchlist_entry.reason if watchlist_entry else "",
            }
        )

    return total_price, item_details
