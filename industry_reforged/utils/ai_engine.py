# Standard Library
import datetime
import logging

# Third Party
import requests

# Django
from django.utils import timezone

# AA Industry App
from industry_reforged.models import CorpInventory, ProductionTask
from industry_reforged.utils.pricing_engine import get_detailed_prices

logger = logging.getLogger(__name__)
ESI_MARKET_HISTORY_URL = "https://esi.evetech.net/latest/markets/{region_id}/history/"


def get_market_velocity(type_id, region_id=None, location_id=None, days=30):
    """
    Fetches the market history for the given type_id and calculates the Average Daily Volume (ADV).
    If a region_id is provided, it pulls for that region.
    If a location_id is provided, it tries to infer the region (or defaults to The Forge 10000002 for now).
    """
    # For now, default to The Forge (Jita) if region_id is missing
    if not region_id:
        region_id = 10000002

    url = ESI_MARKET_HISTORY_URL.format(region_id=region_id)
    params = {"type_id": type_id}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        history = response.json()

        if not history:
            return 0.0

        # Parse dates and filter to last `days` days
        cutoff_date = timezone.now().date() - datetime.timedelta(days=days)
        recent_history = [
            day
            for day in history
            if datetime.datetime.strptime(day["date"], "%Y-%m-%d").date() >= cutoff_date
        ]

        if not recent_history:
            return 0.0

        total_volume = sum(day.get("volume", 0) for day in recent_history)
        adv = total_volume / float(days)
        return adv

    except requests.exceptions.RequestException as e:
        logger.error(f"ESI API error fetching market history for type {type_id}: {e}")
        # In case of API failure, return 0 velocity safely
        return 0.0


def calculate_profitability(eve_type, target_market=None):
    """
    Checks the current sell price of the item and subtracts the estimated BOM cost.
    Returns the estimated margin percentage.
    """
    # In a fully fleshed out engine, we'd use `calculate_bom_cost(parsed_items)`
    # For the AI Engine, we just grab the Jita sell price and compare it to an assumed build cost.

    try:
        # get_detailed_prices returns a dict mapped by type_id
        prices = get_detailed_prices([eve_type.id])
        if eve_type.id not in prices:
            return 0.0, 0.0, 0.0

        item_price_data = prices[eve_type.id]
        sell_price = item_price_data.get("final_price", 0.0)

        # NOTE: Full BOM cost calculation requires the blueprint materials tree.
        # As a placeholder for the MVP AI Engine, we mock the BOM cost using the adjusted price
        # Fallback to 80% of sell price if adjusted_price is missing or 0
        adjusted_price = 0.0
        try:
            # Third Party
            from eveuniverse.models import EveMarketPrice

            market_price = EveMarketPrice.objects.filter(
                eve_type_id=eve_type.id
            ).first()
            if market_price and market_price.adjusted_price:
                adjusted_price = float(market_price.adjusted_price)
        except Exception:
            pass

        build_cost = adjusted_price if adjusted_price > 0 else (sell_price * 0.8)

        if build_cost <= 0:
            return 0.0, sell_price, build_cost

        profit = sell_price - build_cost
        margin_percent = (profit / build_cost) * 100.0
        return margin_percent, sell_price, build_cost

    except Exception as e:
        logger.error(f"Error calculating profitability for {eve_type.id}: {e}")
        return 0.0, 0.0, 0.0


def check_availability(eve_type, target_market=None):
    """
    Calculates how many units of this item we already have in inventory or in-flight (ProductionTask).
    If target_market is passed, only filters for that specific location.
    """
    # Check corp inventory
    inventory_qs = CorpInventory.objects.filter(item_type=eve_type)
    if target_market:
        inventory_qs = inventory_qs.filter(location_id=target_market)

    total_inventory = sum(inv.quantity for inv in inventory_qs)

    # Check in-flight production tasks
    tasks_qs = ProductionTask.objects.filter(
        item_type=eve_type, status__in=["UNCLAIMED", "IN_PRODUCTION"]
    )
    in_flight = sum(task.quantity for task in tasks_qs)

    return total_inventory + in_flight
