"""AI Market Manager Tasks"""

# Standard Library
import logging

# Third Party
from celery import shared_task

# Django
from django.utils import timezone

from .utils import log_task_execution

logger = logging.getLogger(__name__)


@shared_task(name="industry_reforged.tasks.evaluate_baskets")
@log_task_execution("AI Market Manager: Evaluate Baskets")
def evaluate_baskets(basket_id=None):
    """Iterate through active BasketItems, apply decision matrix, and generate ProductionTasks."""
    # Django

    from ..models.ai_manager import AIMarketLog, Basket, BasketItem
    from ..models.config import CorporationWebhookConfig
    from ..models.orders import ProductionTask
    from ..utils.ai_engine import (
        calculate_profitability,
        check_availability,
    )
    from ..utils.discord import send_discord_webhook

    try:
        if basket_id:
            active_items = BasketItem.objects.filter(
                basket_id=basket_id, basket__is_active=True
            )
            basket = Basket.objects.filter(pk=basket_id).first()
            if basket:
                basket.is_running = True
                basket.save(update_fields=["is_running"])
        else:
            active_items = BasketItem.objects.filter(basket__is_active=True)

        active_items = active_items.select_related(
            "eve_type", "basket", "basket__corporation"
        )
        new_jobs_by_corp = {}

        logger.info(
            f"AI Market Manager starting evaluation for {active_items.count()} basket items."
        )

        for b_item in active_items:
            eve_type = b_item.eve_type

            target_market = (
                b_item.basket.target_hub.facility_id
                if b_item.basket.target_hub
                else None
            )
            min_margin = b_item.basket.min_profit_margin

            # 1. Availability Check
            current_stock, in_flight = check_availability(
                eve_type,
                target_market=target_market,
                corporation_id=b_item.basket.corporation.corporation_id,
            )
            effective_stock = current_stock + in_flight

            if effective_stock >= b_item.target_stock_level:
                AIMarketLog.objects.create(
                    basket_item=b_item,
                    action_taken="Skipped",
                    stock_level=current_stock,
                    reason=f"Corp stock ({current_stock}) + in-flight ({in_flight}) is above target ({b_item.target_stock_level}).",
                )
                continue

            # 2. Profitability Check
            margin, sell_price, build_cost = calculate_profitability(
                eve_type, target_market=target_market
            )
            if margin < min_margin:
                AIMarketLog.objects.create(
                    basket_item=b_item,
                    action_taken="Skipped",
                    margin=margin,
                    stock_level=current_stock,
                    reason=f"Margin ({margin:.1f}%) is below minimum ({min_margin:.1f}%). (Sell: {sell_price:,.2f}, Build: {build_cost:,.2f})",
                )
                continue

            # 3. Action: Create Production Task
            # Calculate shortage and round up to next batch size if needed
            shortage = b_item.target_stock_level - effective_stock
            batches = (shortage + b_item.batch_size - 1) // b_item.batch_size
            order_qty = max(shortage, batches * b_item.batch_size)
            if order_qty > 0:
                ProductionTask.objects.create(
                    item_type=eve_type, quantity=order_qty, status="UNCLAIMED"
                )

                AIMarketLog.objects.create(
                    basket_item=b_item,
                    action_taken="Ordered",
                    margin=margin,
                    stock_level=current_stock,
                    reason=f"Corp stock ({current_stock}) + in-flight ({in_flight}). Margin OK ({margin:.1f}%). Ordered {order_qty}. (Sell: {sell_price:,.2f}, Build: {build_cost:,.2f})",
                )

            # Send Notification (Mocking a print/log for now as exact webhook setup isn't known)
            msg = f"AI Market Manager: Authorized {order_qty}x {eve_type.name} builds. Expected Margin: {margin:.1f}% (Sell: {sell_price:,.2f}, Build: {build_cost:,.2f})."
            logger.info(msg)

            corp_id = b_item.basket.corporation.corporation_id
            if corp_id not in new_jobs_by_corp:
                new_jobs_by_corp[corp_id] = []
            new_jobs_by_corp[corp_id].append(
                {
                    "name": eve_type.name,
                    "qty": order_qty,
                    "margin": margin,
                }
            )

        # Send Webhooks
        for corp_id, jobs in new_jobs_by_corp.items():
            if not jobs:
                continue
            try:
                webhook_config = CorporationWebhookConfig.objects.filter(
                    corporation__corporation_id=corp_id
                ).first()
                if webhook_config and webhook_config.ai_jobs_webhook:
                    embed = {
                        "title": "🏭 New AI-Generated Production Tasks",
                        "description": "The AI Market Manager has generated the following new tasks based on current market conditions:",
                        "color": 3447003,
                        "fields": [],
                    }
                    for job in jobs:
                        embed["fields"].append(
                            {
                                "name": job["name"],
                                "value": f"Quantity: {job['qty']}\nExpected Margin: {job['margin']:.1f}%",
                                "inline": False,
                            }
                        )
                    send_discord_webhook(webhook_config.ai_jobs_webhook, embed)
            except Exception as e:
                logger.error(f"Error sending AI jobs webhook for corp {corp_id}: {e}")

        return f"Evaluated {active_items.count()} items."
    finally:
        if basket_id:
            # Django

            from ..models.ai_manager import Basket

            Basket.objects.filter(pk=basket_id).update(
                is_running=False, last_run=timezone.now()
            )


@shared_task(name="industry_reforged.tasks.scan_market_opportunities")
@log_task_execution("AI Market Manager: Scan Market Opportunities")
def scan_market_opportunities(
    corporation_id, region_id, categories, target_hub_id=None, scanner_id=None
):
    """
    Scans the market in `region_id` (and optionally `target_hub_id`) for items in `categories`
    that the corporation can build, and updates the MarketOpportunity model.
    """
    # Third Party
    from eveuniverse.models import EveIndustryActivityProduct

    from ..models import CorpBlueprint
    from ..models.ai_manager import BasketItem, MarketOpportunity
    from ..utils.ai_engine import calculate_profitability, get_market_velocity

    logger.info(
        f"Scanning opportunities for corp {corporation_id}, region {region_id}, categories {categories}"
    )

    # Convert categories to integers if they are strings
    categories = [int(c) for c in categories]

    try:
        # 1. Get all product types the corporation can build
        # First, get type IDs of all blueprints the corp owns
        corp_blueprints = CorpBlueprint.objects.filter(
            corporation_id=corporation_id
        ).values_list("eve_type_id", flat=True)

        # Then get the product type IDs for these blueprints (Activity 1 = Manufacturing, 11 = Reactions output)
        products = EveIndustryActivityProduct.objects.filter(
            eve_type_id__in=corp_blueprints, activity_id__in=[1, 11]
        ).select_related("product_eve_type", "product_eve_type__eve_group")

        # Extract unique EveTypes that match the selected categories
        candidate_types = set()
        for prod in products:
            eve_type = prod.product_eve_type
            if (
                eve_type
                and eve_type.eve_group
                and eve_type.eve_group.eve_category_id in categories
            ):
                candidate_types.add(eve_type)

        # 2. Exclude items already in a Basket
        existing_basket_items = set(
            BasketItem.objects.filter(
                basket__corporation_id=corporation_id
            ).values_list("eve_type_id", flat=True)
        )
        candidates = [
            ct for ct in candidate_types if ct.id not in existing_basket_items
        ]

        # Fetch the scanner if one is provided
        scanner = None
        if scanner_id:
            from ..models.ai_manager import OpportunityScanner

            scanner = OpportunityScanner.objects.filter(pk=scanner_id).first()

        missing_types = set()
        if scanner and scanner.scan_missing_blueprints:
            all_products = EveIndustryActivityProduct.objects.filter(
                activity_id__in=[1, 11],
                product_eve_type__eve_group__eve_category_id__in=categories,
            ).select_related("product_eve_type")

            for prod in all_products:
                if prod.product_eve_type not in candidate_types:
                    missing_types.add(prod.product_eve_type)

        missing = list(missing_types)

        logger.info(
            f"Found {len(candidates)} candidate items to scan, and {len(missing)} missing blueprints to evaluate."
        )

        # Determine thresholds
        min_profit_margin = scanner.min_profit_margin if scanner else 15.0
        min_velocity = scanner.min_velocity if scanner else 1.0

        # 3. Evaluate each candidate
        opportunities = []
        auto_added_count = 0
        from ..models.ai_manager import AIMarketLog

        for eve_type in candidates:
            velocity = get_market_velocity(eve_type.id, region_id=region_id, days=30)
            margin, sell_price, build_cost = calculate_profitability(eve_type)

            # We only care about positive velocity and positive margin based on thresholds
            if velocity >= min_velocity and margin >= min_profit_margin:
                opportunities.append(
                    MarketOpportunity(
                        corporation_id=corporation_id,
                        eve_type=eve_type,
                        region_id=region_id,
                        target_hub_id=target_hub_id,
                        velocity=velocity,
                        margin=margin,
                    )
                )

                # 3b. AI Auto-add Action
                if scanner and scanner.auto_add_basket:
                    target_stock = max(1, int(velocity * scanner.target_stock_days))
                    batch_size = max(
                        1, int(velocity * (scanner.target_stock_days / 2.0))
                    )

                    # Check if it already exists (just to be absolutely safe)
                    if not BasketItem.objects.filter(
                        basket=scanner.auto_add_basket, eve_type=eve_type
                    ).exists():
                        b_item = BasketItem.objects.create(
                            basket=scanner.auto_add_basket,
                            eve_type=eve_type,
                            target_stock_level=target_stock,
                            batch_size=batch_size,
                        )
                        from ..utils.ai_engine import check_availability

                        current_stock, in_flight = check_availability(
                            eve_type,
                            target_market=target_hub_id,
                            corporation_id=corporation_id,
                        )

                        AIMarketLog.objects.create(
                            basket_item=b_item,
                            action_taken="Auto-Added by Scanner",
                            margin=margin,
                            stock_level=current_stock,
                            reason=f"Scanner '{scanner.name}' found opportunity with margin {margin:.1f}% (Sell: {sell_price:,.2f}, Build: {build_cost:,.2f}). Current corp stock: {current_stock}, in-flight: {in_flight}.",
                        )
                        auto_added_count += 1

        # 4. Evaluate missing BPOs if requested
        missing_bpo_count = 0
        if scanner and scanner.scan_missing_blueprints:
            from ..models.ai_manager import MissingBlueprintOpportunity

            # Clear old missing BPOs for this scanner
            MissingBlueprintOpportunity.objects.filter(scanner=scanner).delete()

            for eve_type in missing:
                velocity = get_market_velocity(
                    eve_type.id, region_id=region_id, days=30
                )
                margin, sell_price, build_cost = calculate_profitability(eve_type)

                if velocity >= min_velocity and margin >= min_profit_margin:
                    MissingBlueprintOpportunity.objects.create(
                        scanner=scanner,
                        eve_type=eve_type,
                        velocity=velocity,
                        margin=margin,
                    )
                    missing_bpo_count += 1

        # 4. Save results
        if opportunities:
            # Delete old records for these specific types in this region/hub so we can recreate them
            type_ids = [opp.eve_type_id for opp in opportunities]
            qs = MarketOpportunity.objects.filter(
                corporation_id=corporation_id,
                region_id=region_id,
                eve_type_id__in=type_ids,
            )
            if target_hub_id:
                qs = qs.filter(target_hub_id=target_hub_id)
            else:
                qs = qs.filter(target_hub_id__isnull=True)
            qs.delete()

            MarketOpportunity.objects.bulk_create(opportunities)

        result_msg = f"Scanned {len(candidates)} items. Found {len(opportunities)} profitable opportunities."
        if auto_added_count > 0:
            result_msg += f" Auto-added {auto_added_count} items to basket."
        if missing_bpo_count > 0:
            result_msg += f" Found {missing_bpo_count} missing BPO opportunities."

        if scanner:
            # Django

            from ..models.ai_manager import OpportunityScannerLog

            scanner.last_run = timezone.now()
            scanner.save(update_fields=["last_run"])

            OpportunityScannerLog.objects.create(
                scanner=scanner,
                items_scanned=len(candidates),
                opportunities_found=len(opportunities),
                items_auto_added=auto_added_count,
                details=result_msg,
            )

        return result_msg
    finally:
        if scanner_id:
            from ..models.ai_manager import OpportunityScanner

            OpportunityScanner.objects.filter(pk=scanner_id).update(is_running=False)


@shared_task(name="industry_reforged.tasks.run_all_active_scanners")
@log_task_execution("AI Market Manager: Run Active Scanners")
def run_all_active_scanners():
    """Periodic task to trigger all active Opportunity Scanners based on their interval."""
    # Standard Library
    from datetime import timedelta

    from ..models.ai_manager import OpportunityScanner

    scanners = OpportunityScanner.objects.filter(is_active=True)
    count = 0
    now = timezone.now()

    for scanner in scanners:
        # Check if it's time to run based on last_run and run_interval_hours
        should_run = False
        if not scanner.last_run:
            should_run = True
        else:
            time_since_last = now - scanner.last_run
            if time_since_last >= timedelta(hours=scanner.run_interval_hours):
                should_run = True

        if should_run:
            target_hub_id = (
                scanner.target_hub.facility_id if scanner.target_hub else None
            )
            scan_market_opportunities.delay(
                scanner.corporation_id,
                scanner.target_region_id,
                scanner.categories,
                target_hub_id=target_hub_id,
                scanner_id=scanner.id,
            )
            count += 1

    return f"Queued {count} active Opportunity Scanners."


@shared_task(name="industry_reforged.tasks.run_all_active_baskets")
def run_all_active_baskets():
    """Finds baskets that are due to run and evaluates them."""
    # Standard Library
    from datetime import timedelta

    from ..models.ai_manager import Basket

    active_baskets = Basket.objects.filter(is_active=True)
    now = timezone.now()
    count = 0
    for basket in active_baskets:
        if not basket.last_run or now - basket.last_run >= timedelta(
            hours=basket.run_interval_hours
        ):
            if not basket.is_running:
                evaluate_baskets.delay(basket.id)
                count += 1

    return f"Triggered {count} baskets for evaluation."
