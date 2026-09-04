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
    """
    prices = get_market_prices(type_ids)

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
    """
    prices = get_market_prices(type_ids)
    detailed = {}
    for tid in type_ids:
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


def calculate_quote(parsed_items, corporation=None):
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
        if config:
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
        from ..models import CorpPricingConfig

        config = CorpPricingConfig.objects.filter(corporation=corporation).first()
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
