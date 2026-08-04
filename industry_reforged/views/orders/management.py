"""App Views"""

# Django
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from ...models import (
    CorporationWebhookConfig,
    MemberOrder,
    ProductionTask,
)
from ...utils.discord import send_discord_webhook


def delete_order(request: WSGIRequest, order_id: int) -> HttpResponse:
    user_characters = request.user.character_ownerships.all().values_list(
        "character_id", flat=True
    )

    # Check if the user is a director or the owner
    is_director = request.user.has_perm("industry_reforged.corp_access")

    if is_director:
        order = MemberOrder.objects.filter(id=order_id).first()
    else:
        order = MemberOrder.objects.filter(
            id=order_id,
            character_id__in=user_characters,
            status__in=["REQUESTED", "QUOTED"],
        ).first()

    if order:
        parent = order.parent_order

        # Move OrderItems back to parent if this was a standard item split (not a component split)
        # We can guess it's a component split if the parent's BOM would normally contain the child's items.
        # But actually, it's safer to let component splits just be deleted (since the parent BOM recalculates them).
        # Wait, if we just delete the child, the BOM engine naturally absorbs the components back.
        # So we just need to recalculate the parent order's total price.

        # Delete related tasks explicitly since they have on_delete=models.SET_NULL
        ProductionTask.objects.filter(created_from_order=order).delete()

        # Discord Webhook Notification
        corporation = None
        if order.character and order.character.corporation:
            corporation = order.character.corporation
        if corporation:
            webhook_config = CorporationWebhookConfig.objects.filter(
                corporation=corporation
            ).first()
            if webhook_config and webhook_config.orders_webhook:
                main_char = request.user.profile.main_character
                deleted_by_name = (
                    main_char.character_name if main_char else request.user.username
                )
                embed = {
                    "title": f"Order Deleted: #{order.id}",
                    "description": f"**{order.character.character_name}**'s order was deleted by **{deleted_by_name}**.",
                    "color": 15158332,  # Red
                }
                send_discord_webhook(webhook_config.orders_webhook, embed)

        # If this is a child order created via Split Items, we should move the items back to the parent!
        # How to distinguish? Component splits have a specific note: "Sub-component ... split from Order"
        if parent and not order.notes.startswith("Sub-component"):
            order.items.update(order=parent)

        order.delete()

        # Recalculate parent if it exists
        if parent:
            # Alliance Auth
            from allianceauth.eveonline.models import EveCorporationInfo

            from ...utils.bom_engine import calculate_order_bom
            from ...utils.pricing_engine import get_prices_with_overrides

            try:
                corp_info = EveCorporationInfo.objects.get(
                    corporation_id=parent.character.corporation_id
                )
            except Exception:
                corp_info = None

            from ...models import CorpPricingConfig

            pricing_config = CorpPricingConfig.objects.filter(
                corporation__corporation_id=parent.character.corporation_id
            ).first()

            parent_bom = calculate_order_bom(parent)
            parent_bom_price = 0
            if parent_bom:
                mat_ids = list(parent_bom.keys())
                prices = get_prices_with_overrides(mat_ids, corp_info)
                for mat_id, data in parent_bom.items():
                    price = prices.get(mat_id, 0)
                    parent_bom_price += price * data["quantity"]

            parent_discount = (
                parent.items.first().discount_applied
                if parent.items.exists()
                else (
                    pricing_config.default_discount_percent if pricing_config else 0.0
                )
            )
            parent_discount_multiplier = (100.0 - parent_discount) / 100.0
            parent_discounted_price = parent_bom_price * parent_discount_multiplier

            tax = 0.0
            # Facility tax rate removed as it's not present on IndustryFacility
            parent_tax_amount = parent_discounted_price * tax

            corp_tax = 0.0
            parent_corp_tax_amount = parent_discounted_price * corp_tax

            parent_final = (
                parent_discounted_price + parent_tax_amount + parent_corp_tax_amount
            )
            parent.total_price = parent_final

            # If the parent was quoted, we might want to drop it back to requested since the scope changed,
            # but let's just update the price for now so the director can review it.
            if parent.status == "QUOTED":
                parent.status = "REQUESTED"

            parent.save(update_fields=["total_price", "status"])

            # Update line totals for parent if only 1 item
            if parent.items.count() == 1:
                i = parent.items.first()
                i.price_per_unit = (parent_final / i.quantity) if i.quantity > 0 else 0
                i.save(update_fields=["price_per_unit"])

        messages.success(request, _("Order successfully deleted."))
    else:
        messages.error(
            request,
            _("Order could not be found or you don't have permission to delete it."),
        )

    return redirect("industry_reforged:orders_dashboard")
