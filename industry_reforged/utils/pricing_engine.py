# Standard Library
import logging
import math
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

    # For buy orders, filter out extreme lowball / troll bids (< 25% of highest bid)
    if is_buy:
        top_buy_price = float(sorted_orders[0].get("price", 0.0))
        if top_buy_price <= 0.05:
            return 0.0
        valid_buy_orders = [
            o
            for o in sorted_orders
            if float(o.get("price", 0.0)) >= 0.25 * top_buy_price
        ]
        if valid_buy_orders:
            sorted_orders = valid_buy_orders

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
            if price > 0.05:
                # For buy orders, verify against sell market to prevent illiquid/manipulated book distortion
                if order_type == "buy":
                    sell_price = calculate_percentile_price(
                        orders,
                        percentile=0.05,
                        station_id=station_id,
                        order_type="sell",
                    )
                    # If an active sell market exists and buy price is < 20% of sell price,
                    # the buy book is illiquid or manipulated; invalidate to trigger fallback
                    if sell_price > 0.0 and price < 0.20 * sell_price:
                        price = 0.0
                if price > 0.05:
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
                if val is not None and float(val) > 0.05:
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
                fuzz_price = (
                    fuzz_data[str(type_id)].get(order_type, {}).get("percentile")
                )
                if fuzz_price and float(fuzz_price) > 0.05:
                    return float(fuzz_price)
    except Exception as e:
        logger.warning(f"Fuzzwork fallback failed for type_id {type_id}: {e}")

    # If buy price was requested but no valid buy price exists, fallback to sell price
    if order_type == "buy":
        try:
            sell_fallback = fetch_single_market_price(
                type_id,
                region_id=region_id,
                station_id=station_id,
                session=req_session,
                order_type="sell",
            )
            if sell_fallback > 0.05:
                return sell_fallback
        except Exception as e:
            logger.debug(f"Sell fallback failed for type_id {type_id}: {e}")

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
        if cached_price is not None and (order_type != "buy" or cached_price > 0.05):
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
    # Third Party
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
    # Third Party
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


def calculate_quote(
    parsed_items, corporation=None, ignore_discounts=False, target_facility=None
):
    """
    Takes a dict of {EveType: quantity} and an optional EveCorporationInfo.
    Returns:
    - total_price: Decimal
    - item_details: List of dicts with price breakdown
    """
    type_ids = [t.id for t in parsed_items]
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
            true_cost_per_unit = calculate_bom_cost(
                {eve_type: 1}, corporation, target_facility=target_facility
            )

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


def fetch_system_cost_indices(solar_system_id=None):
    """
    Fetch system cost indices from ESI with Django cache caching.
    Returns:
        dict: If solar_system_id is provided, returns {activity_name: float_cost_index}.
            If None, returns {solar_system_id: {activity_name: float_cost_index}}.
    """
    # Django
    from django.core.cache import cache

    cache_key = "aa_industry_system_cost_indices"
    sys_indices = cache.get(cache_key)

    if sys_indices is None:
        sys_indices = {}
        try:
            res = requests.get(
                "https://esi.evetech.net/latest/industry/systems/", timeout=5
            )
            if res.status_code == 200:
                for entry in res.json():
                    sid = entry.get("solar_system_id")
                    if sid:
                        sys_indices[sid] = {
                            ci["activity"]: float(ci["cost_index"])
                            for ci in entry.get("cost_indices", [])
                            if "activity" in ci and "cost_index" in ci
                        }
                if sys_indices:
                    cache.set(cache_key, sys_indices, timeout=3600)
        except Exception as e:
            logger.warning(f"Failed to fetch ESI system cost indices: {e}")

    default_indices = {
        "manufacturing": 0.02,
        "reaction": 0.01,
        "copying": 0.01,
        "invention": 0.02,
    }

    if solar_system_id is not None:
        return sys_indices.get(solar_system_id, default_indices)
    return sys_indices


def calculate_structure_job_costs(
    parsed_items_or_trees, target_facility=None, corporation=None
):
    """
    Calculates the industry job installation fees for all manufacturing and reaction steps
    in the recursive BOM trees based on system cost indices and facility tax rate.
    """
    if not parsed_items_or_trees:
        return Decimal("0.00")

    # If dict of {EveType: quantity} is passed, build the recursive BOM trees
    if isinstance(parsed_items_or_trees, dict):
        from .bom_engine import get_recursive_bom_tree

        trees = []
        for eve_type, quantity in parsed_items_or_trees.items():
            t = get_recursive_bom_tree(
                type_id=eve_type.id,
                name=eve_type.name,
                quantity=quantity,
                config_dict={},
                corp_info=corporation,
                target_facility=target_facility,
            )
            trees.append(t)
    elif isinstance(parsed_items_or_trees, list):
        trees = parsed_items_or_trees
    else:
        trees = [parsed_items_or_trees]

    from ..models import IndustryFacility

    if target_facility is None and corporation:
        target_facility = (
            IndustryFacility.objects.filter(
                owner_id=corporation.corporation_id, is_default=True
            ).first()
            or IndustryFacility.objects.filter(is_default=True).first()
        )

    if not target_facility or not target_facility.solar_system_id:
        return Decimal("0.00")

    indices = fetch_system_cost_indices(target_facility.solar_system_id)
    mfg_index = indices.get("manufacturing", 0.02)
    rxn_index = indices.get("reaction", 0.01)

    tax_rate = 0.0
    if corporation:
        from ..models import TaxConfig

        tax_config = TaxConfig.objects.filter(corporation=corporation).first()
        if tax_config and tax_config.industry_tax_rate:
            tax_rate = tax_config.industry_tax_rate / 100.0

    total_job_cost = Decimal("0.00")

    # Third Party
    from eveuniverse.models import EveMarketPrice

    def _calc_jobs(nodes):
        nonlocal total_job_cost
        for node in nodes:
            sub = node.get("sub_materials")
            if sub:
                act = node.get("activity_id")
                tid = node.get("type_id")
                qty = node.get("quantity", 1)

                is_reaction = act == 11 or node.get("is_reaction", False)
                cost_index = rxn_index if is_reaction else mfg_index

                # Estimated Item Value (EIV) from EveMarketPrice adjusted_price
                emp = EveMarketPrice.objects.filter(eve_type_id=tid).first()
                adj_price = (
                    float(emp.adjusted_price) if (emp and emp.adjusted_price) else 0.0
                )
                if adj_price <= 0.05 and emp and emp.average_price:
                    adj_price = float(emp.average_price)
                if adj_price <= 0.05:
                    adj_price = get_market_prices([tid]).get(tid, 0.0)

                if adj_price > 0.0:
                    fee = (
                        Decimal(str(adj_price))
                        * Decimal(str(qty))
                        * Decimal(str(cost_index))
                        * Decimal(str(1.0 + tax_rate))
                    )
                    total_job_cost += fee

                _calc_jobs(sub)

    _calc_jobs(trees)
    return total_job_cost.quantize(Decimal("0.01"))


def calculate_bom_cost(parsed_items, corporation=None, target_facility=None):
    """
    Calculate the True Material Cost of the parsed_items based on a flattened BOM,
    including unowned blueprint acquisition costs and structure job installation fees.
    """
    from ..models import IndustryFacility
    from .bom_engine import get_recursive_bom_tree

    if target_facility is None and corporation:
        target_facility = (
            IndustryFacility.objects.filter(
                owner_id=corporation.corporation_id, is_default=True
            ).first()
            or IndustryFacility.objects.filter(is_default=True).first()
        )

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
    trees = []

    for eve_type, quantity in parsed_items.items():
        tree = get_recursive_bom_tree(
            type_id=eve_type.id,
            name=eve_type.name,
            quantity=quantity,
            config_dict=config_dict,
            target_facility=target_facility,
            corp_info=corporation,
        )
        trees.append(tree)

        def _flatten(node):
            # Science job / Blueprint copying or Reaction Formula
            if node.get("activity_id") == 5 or (
                node.get("activity_id") == 11 and not node.get("sub_materials")
            ):
                bp_id = node.get("type_id")
                if corporation:
                    from ..models import CorpBlueprint

                    # Any blueprint the corp owns as BPO or BPC is NOT counted as cost
                    if CorpBlueprint.objects.filter(
                        corporation=corporation, eve_type_id=bp_id
                    ).exists():
                        return
                # Unowned blueprint: acquisition cost of 1 blueprint
                raw_materials_qty[bp_id] = raw_materials_qty.get(bp_id, 0) + 1
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
        # Sanity check against troll buy orders (e.g. 0.01 or 1.10 ISK) and illiquid books
        sell_prices = get_market_prices(type_ids, order_type="sell")
        for tid in type_ids:
            bp = base_prices.get(tid, 0.0)
            sp = sell_prices.get(tid, 0.0)
            if bp <= 0.05 or (sp > 0.0 and bp < 0.25 * sp):
                base_prices[tid] = sp
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

    # 5. Calculate Total Material Cost
    total_bom_cost = Decimal("0.00")
    for tid, qty in raw_materials_qty.items():
        price = Decimal(str(base_prices.get(tid, 0.0)))
        total_bom_cost += price * qty

    # 6. Add Structure Job Installation Fees
    structure_fees = calculate_structure_job_costs(
        trees, target_facility=target_facility, corporation=corporation
    )
    total_bom_cost += structure_fees

    return total_bom_cost


# --- Buyback appraisal ---------------------------------------------------
#
# Appended here rather than in a separate module: the buyback appraisal is
# the same "value an item" concept get_market_prices/get_prices_with_overrides
# already own, and keeping it in one file means there is only ever one cache
# format and one place to fix a pricing bug.


def _market_unit_prices(type_ids, order_type="sell") -> dict:
    """Jita unit prices for `order_type` "buy", "sell" or "split" (average of both)."""
    if order_type == "split":
        buy = get_market_prices(type_ids, order_type="buy")
        sell = get_market_prices(type_ids, order_type="sell")
        return {tid: (buy.get(tid, 0.0) + sell.get(tid, 0.0)) / 2.0 for tid in type_ids}
    return get_market_prices(type_ids, order_type=order_type)


def get_reprocessing_value(
    eve_type, quantity, efficiency=1.0, order_type="sell"
) -> Decimal | None:
    """
    Reprocessing valuation via eveuniverse's EveType.materials (SDE reprocessing
    yield), with the materials valued at the same price basis (buy/sell/split)
    as the item itself. Returns None (never False/0) when the item has no
    reprocessing output at all, so callers never hit a "0 vs. unset" ambiguity.
    """
    materials = list(eve_type.materials.all())
    if not materials:
        return None

    material_ids = [m.material_eve_type_id for m in materials]
    prices = _market_unit_prices(material_ids, order_type=order_type)

    total = Decimal("0.00")
    for mat in materials:
        unit_price = Decimal(str(prices.get(mat.material_eve_type_id, 0.0)))
        yielded_per_unit = Decimal(str(mat.quantity)) * Decimal(str(efficiency))
        total += unit_price * yielded_per_unit

    return total * quantity


def get_item_value_variants(
    eve_type, quantity, order_type="sell", refining_efficiency=1.0
) -> dict:
    """
    Single parameterized replacement for the "raw/compressed/refined/NPC
    best-of" concept: returns only the valuation keys that actually apply to
    this item, using explicit `is not None` checks rather than a `False`-as-
    sentinel pattern. Compressed/raw ore items are themselves distinct
    EveTypes with their own market price, so "best of market vs. reprocessed"
    already covers raw ore without any ore-specific special-casing.

    `order_type` is "buy", "sell", or "split" (average of both) - the pricing
    basis for the direct market valuation. `refining_efficiency` (0.0-1.0)
    scales the reprocessed valuation to a realistic refining rate.
    """
    variants = {}

    market_price = _market_unit_prices([eve_type.id], order_type=order_type).get(
        eve_type.id, 0.0
    )
    if market_price and market_price > 0.0:
        variants["market"] = Decimal(str(market_price)) * quantity

    reprocessed = get_reprocessing_value(
        eve_type, quantity, efficiency=refining_efficiency, order_type=order_type
    )
    if reprocessed is not None and reprocessed > 0:
        variants["reprocessed"] = reprocessed

    return variants


def calculate_price_density_tax(
    unit_price: Decimal, packaged_volume, program
) -> Decimal:
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
    if (
        threshold <= 0
        or tax_percent <= 0
        or not packaged_volume
        or packaged_volume <= 0
    ):
        return Decimal("0.00")

    density = unit_price / Decimal(str(packaged_volume))
    if density >= Decimal(str(threshold)):
        return Decimal("0.00")

    return (unit_price * Decimal(str(tax_percent)) / Decimal("100.00")).quantize(
        Decimal("0.01")
    )


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

    accepted_category_ids = (
        set(program.accepted_categories.values_list("id", flat=True))
        if program.pk
        else set()
    )

    total_price = Decimal("0.00")
    item_details = []
    order_type = (program.price_type or "SELL").lower()
    refining_efficiency = float(program.refining_rate or 0.0) / 100.0

    def blocked_line(eve_type, quantity, reason, watchlist_reason=""):
        return {
            "eve_type": eve_type,
            "quantity": quantity,
            "unit_price": Decimal("0.00"),
            "line_total": Decimal("0.00"),
            "base_unit_price": Decimal("0.00"),
            "base_line_total": Decimal("0.00"),
            "value_source": None,
            "blocked": True,
            "blocked_reason": reason,
            "flagged": False,
            "watchlist_reason": watchlist_reason,
        }

    for eve_type, quantity in parsed_items.items():
        watchlist_entry = watchlist.get(eve_type.id)
        if watchlist_entry and watchlist_entry.blocks_submission:
            item_details.append(
                blocked_line(
                    eve_type,
                    quantity,
                    watchlist_entry.reason or "Not accepted by this program.",
                    watchlist_entry.reason,
                )
            )
            continue

        category_id = (
            eve_type.eve_group.eve_category_id if eve_type.eve_group_id else None
        )
        if accepted_category_ids and category_id not in accepted_category_ids:
            item_details.append(
                blocked_line(
                    eve_type,
                    quantity,
                    "This item's category isn't accepted by this program.",
                )
            )
            continue

        variants = get_item_value_variants(
            eve_type,
            quantity,
            order_type=order_type,
            refining_efficiency=refining_efficiency,
        )
        if not variants:
            logger.warning(
                f"No valuation method applies to {eve_type.name} ({eve_type.id}) - valuing at 0."
            )
            line_total = Decimal("0.00")
            value_source = None
        else:
            value_source, line_total = max(variants.items(), key=lambda kv: kv[1])

        base_unit_price = (
            (line_total / quantity).quantize(Decimal("0.01"))
            if quantity
            else Decimal("0.00")
        )

        modifier = Decimal(str(program.price_modifier_percent or 0.0)) / Decimal(
            "100.00"
        )
        unit_price = (base_unit_price * (Decimal("1.00") + modifier)).quantize(
            Decimal("0.01")
        )

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
                "blocked_reason": "",
                "flagged": bool(watchlist_entry),
                "watchlist_reason": watchlist_entry.reason if watchlist_entry else "",
            }
        )

    return total_price, item_details


def get_item_production_details(type_id: int, activity_id: int = 1) -> tuple[int, int]:
    """
    Returns (base_duration_seconds, portion_size) for 1 run of an item.
    Uses django-eveuniverse EveIndustryActivityProduct and EveIndustryActivityDuration.
    Cached for fast repeated lookups.
    """
    # Django
    from django.core.cache import cache

    cache_key = f"aa_industry_prod_details_{type_id}_{activity_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Third Party
    from eveuniverse.models import (
        EveIndustryActivityDuration,
        EveIndustryActivityProduct,
    )

    try:
        bp_prod = EveIndustryActivityProduct.objects.filter(
            product_eve_type_id=type_id,
            activity_id=activity_id,
            eve_type__published=True,
        ).first()

        if bp_prod:
            portion_size = bp_prod.quantity or 1
            duration_obj = EveIndustryActivityDuration.objects.filter(
                eve_type_id=bp_prod.eve_type_id,
                activity_id=activity_id,
            ).first()
            dur_sec = duration_obj.time if duration_obj and duration_obj.time else 0
            res = (dur_sec, portion_size)
            cache.set(cache_key, res, timeout=86400)
            return res
    except Exception as exc:
        logger.warning(
            "Error fetching production details for type %s (act %s): %s",
            type_id,
            activity_id,
            exc,
        )

    fallback = (0, 1)
    cache.set(cache_key, fallback, timeout=86400)
    return fallback


def calculate_task_builder_reward(
    eve_type,
    quantity: int,
    activity_id: int = 1,
    priority: str = "NORMAL",
    pricing_config=None,
    line_total_value: float | Decimal = 0.0,
) -> tuple[Decimal, int]:
    """
    Calculates the builder reward and estimated duration using Hybrid Model 2:
    Raw = Base Fee + (Slot Duration Hours * Hourly Rate) + (Output Market Value * Value %)
    Bounded = Clamp(Raw, Minimum Floor, Maximum Cap)
    Final = Bounded * Priority Multiplier

    Args:
        eve_type: EveType instance or object with .id, or integer type_id.
        quantity: Integer quantity to produce.
        activity_id: Industry activity ID (1=Manufacturing, 11=Reactions).
        priority: Priority string ('URGENT', 'HIGH', 'NORMAL', 'LOW').
        pricing_config: CorpPricingConfig instance or None.
        line_total_value: Market value of total output quantity.

    Returns:
        tuple[Decimal, int]: (final_builder_reward, estimated_duration_seconds)
    """
    # 1. Retrieve config parameters with defaults
    base_fee = (
        Decimal(str(pricing_config.builder_base_fee))
        if pricing_config and pricing_config.builder_base_fee is not None
        else Decimal("1000000.00")
    )
    hourly_rate = (
        Decimal(str(pricing_config.builder_hourly_rate))
        if pricing_config and pricing_config.builder_hourly_rate is not None
        else Decimal("750000.00")
    )
    reward_percent = (
        float(pricing_config.builder_reward_percent)
        if pricing_config and pricing_config.builder_reward_percent is not None
        else 0.5
    )
    min_reward = (
        Decimal(str(pricing_config.builder_min_reward))
        if pricing_config and pricing_config.builder_min_reward is not None
        else Decimal("2500000.00")
    )
    max_reward = (
        Decimal(str(pricing_config.builder_max_reward))
        if pricing_config and pricing_config.builder_max_reward is not None
        else Decimal("75000000.00")
    )
    urgent_mult = (
        float(pricing_config.builder_urgent_multiplier)
        if pricing_config and pricing_config.builder_urgent_multiplier is not None
        else 1.5
    )
    high_mult = (
        float(pricing_config.builder_high_multiplier)
        if pricing_config and pricing_config.builder_high_multiplier is not None
        else 1.25
    )
    low_mult = (
        float(pricing_config.builder_low_multiplier)
        if pricing_config and pricing_config.builder_low_multiplier is not None
        else 0.8
    )

    # 2. Duration calculation
    type_id = eve_type.id if hasattr(eve_type, "id") else int(eve_type)
    base_dur_sec, portion_size = get_item_production_details(type_id, activity_id)
    runs = max(math.ceil(quantity / max(portion_size, 1)), 1)
    # Apply standard TE 0.75 efficiency factor (rigs + skills)
    est_duration_sec = int(base_dur_sec * runs * 0.75) if base_dur_sec > 0 else 0
    duration_hours = Decimal(str(est_duration_sec)) / Decimal("3600.0")

    # 3. Raw reward components
    slot_cost = duration_hours * hourly_rate
    val_incentive = Decimal(str(line_total_value)) * (
        Decimal(str(reward_percent)) / Decimal("100.0")
    )
    raw_reward = base_fee + slot_cost + val_incentive

    # 4. Bounds Clamping
    bounded = raw_reward
    if max_reward > 0 and bounded > max_reward:
        bounded = max_reward
    if min_reward > 0 and bounded < min_reward:
        bounded = min_reward

    # 5. Priority Multiplier
    prio = (priority or "NORMAL").upper()
    if prio == "URGENT":
        mult = Decimal(str(urgent_mult))
    elif prio == "HIGH":
        mult = Decimal(str(high_mult))
    elif prio == "LOW":
        mult = Decimal(str(low_mult))
    else:
        mult = Decimal("1.0")

    final_reward = (bounded * mult).quantize(Decimal("0.01"))
    return final_reward, est_duration_sec
