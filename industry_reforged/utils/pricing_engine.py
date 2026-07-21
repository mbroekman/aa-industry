# Standard Library
import logging
from decimal import Decimal

# Third Party
import requests

from ..models import CorpPricingConfig, CorpTypeDiscount

logger = logging.getLogger(__name__)

FUZZWORK_API_URL = "https://market.fuzzwork.co.uk/aggregates/"
JITA_STATION_ID = 60003760


def get_fuzzwork_prices(type_ids):
    """
    Fetch Jita prices for a list of type IDs from Fuzzwork API.
    Returns a dict mapping type_id (int) to a float (sell min).
    """
    if not type_ids:
        return {}

    # Django
    from django.core.cache import cache

    prices = {}
    missing_ids = []

    # Check cache first
    for tid in type_ids:
        cached_price = cache.get(f"fw_price_{tid}")
        if cached_price is not None:
            prices[int(tid)] = cached_price
        else:
            missing_ids.append(tid)

    if not missing_ids:
        return prices

    # Fetch missing from Fuzzwork
    chunk_size = 50
    for i in range(0, len(missing_ids), chunk_size):
        chunk = missing_ids[i : i + chunk_size]
        str_ids = ",".join(map(str, chunk))

        try:
            # Shorten timeout to 5 seconds so the UI doesn't hang forever
            res = requests.get(
                f"{FUZZWORK_API_URL}?station={JITA_STATION_ID}&types={str_ids}",
                timeout=5,
            )
            res.raise_for_status()
            data = res.json()

            for type_id_str, type_data in data.items():
                if "sell" in type_data and "min" in type_data["sell"]:
                    val = float(
                        type_data["sell"]["percentile"]
                    )  # 5% percentile sell is usually more stable than min
                    prices[int(type_id_str)] = val
                    # Cache for 1 hour
                    cache.set(f"fw_price_{type_id_str}", val, 3600)
        except Exception as e:
            logger.error(f"Failed to fetch Fuzzwork prices for {chunk}: {e}")
            # Cache failure for a short time to prevent spamming failing API
            for tid in chunk:
                cache.set(f"fw_price_{tid}", 0.0, 60)
                prices[int(tid)] = 0.0

    return prices


def get_prices_with_overrides(type_ids, corporation=None):
    """
    Fetch Jita prices for a list of type IDs, but apply any manual price
    overrides defined in CorpItemConfig for the given corporation.
    """
    prices = get_fuzzwork_prices(type_ids)

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
    prices = get_fuzzwork_prices(type_ids)
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
    if corporation:
        config = CorpPricingConfig.objects.filter(corporation=corporation).first()

    total_price = Decimal("0.00")
    item_details = []

    for eve_type, quantity in parsed_items.items():
        base_price = market_prices.get(eve_type.id, 0.0)

        discount_percent = 0.0
        if config:
            # Check specific type discount first
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
            }
        )

    return total_price, item_details
