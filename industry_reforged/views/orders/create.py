"""App Views"""

# Django
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from ..models import (
    CorpItemConfig,
    CorporationWebhookConfig,
    MemberOrder,
    OrderFit,
    OrderItem,
)
from ..utils.discord import send_discord_webhook
from ..utils.fit_parser import parse_fit_text
from ..utils.pricing_engine import (
    calculate_quote,
)


def create_order(request: WSGIRequest) -> HttpResponse:
    """Create a new order from EFT fit or single items"""
    if request.method == "POST":
        fit_text = request.POST.get("fit_text", "").strip()

        if not fit_text:
            messages.error(request, _("Please provide an EFT fit."))
            return redirect("industry_reforged:create_order")

        character = request.user.profile.main_character
        if not character:
            messages.error(
                request, _("You must have a main character set to create orders.")
            )
            return redirect("industry_reforged:create_order")

        parsed_items, unrecognized = parse_fit_text(fit_text)

        if unrecognized:
            messages.warning(
                request,
                f"Could not recognize the following items: {', '.join(unrecognized)}",
            )

        # Optional: Apply corp discount if user's main character is in a corp with config
        main_char = request.user.profile.main_character
        corporation = main_char.corporation if main_char else None

        # Filter out excluded items
        if corporation and parsed_items:
            excluded_configs = CorpItemConfig.objects.filter(
                corporation=corporation,
                exclude_from_orders=True,
                item_type_id__in=parsed_items.keys(),
            ).select_related("item_type")

            for config in excluded_configs:
                # Remove from the parsed dictionary
                if config.item_type in parsed_items:
                    del parsed_items[config.item_type]

                # Show warning message to the user
                msg = _(
                    "Item '%(item)s' was automatically removed from your order."
                ) % {"item": config.item_type.name}
                if config.exclude_warning_message:
                    msg += f" {config.exclude_warning_message}"
                messages.warning(request, msg)

        if not parsed_items:
            messages.error(
                request, _("No valid items remaining in the fit after filtering.")
            )
            return redirect("industry_reforged:create_order")

        total_price, item_details = calculate_quote(parsed_items, corporation)

        # Django
        from django.utils.crypto import get_random_string

        ref = "ORD-" + get_random_string(4).upper() + "-" + get_random_string(4).upper()

        from ..models import IndustryFacility

        default_facility = IndustryFacility.objects.filter(is_default=True).first()

        order = MemberOrder.objects.create(
            character=character,
            status="REQUESTED",
            total_price=total_price,
            payment_reference=ref,
            target_facility=default_facility,
        )

        OrderFit.objects.create(order=order, raw_fit_text=fit_text)

        order_items = []
        for detail in item_details:
            order_items.append(
                OrderItem(
                    order=order,
                    item_type=detail["eve_type"],
                    quantity=detail["quantity"],
                    price_per_unit=detail["final_price_per_unit"],
                    discount_applied=detail["discount_percent"],
                )
            )
        OrderItem.objects.bulk_create(order_items)

        # Send to all configured webhooks in the system, since orders are global
        webhook_configs = CorporationWebhookConfig.objects.all()
        for config in webhook_configs:
            embed = {
                "title": f"New Quote Requested: Order #{order.id}",
                "description": f"**{character.character_name}** has requested a quote.",
                "color": 3447003,  # Blue
                "fields": [
                    {
                        "name": "Total Estimated Price",
                        "value": f"{total_price:,.2f} ISK",
                        "inline": False,
                    }
                ],
            }
            if config.orders_webhook:
                send_discord_webhook(config.orders_webhook, embed)
            elif config.directors_webhook:
                send_discord_webhook(config.directors_webhook, embed)

        messages.success(request, _("Order parsed and quoted successfully!"))
        return redirect("industry_reforged:view_quote", order_id=order.id)

    characters = request.user.character_ownerships.all().select_related("character")
    context = {"title": "Create Order", "characters": [c.character for c in characters]}
    return render(request, "industry_reforged/create_order.html", context)
