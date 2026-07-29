"""App Views"""

# Django
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from ..models import (
    MemberOrder,
)


def split_order(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Director splits specific items from an order into a new child order"""
    if request.method == "POST":
        order = MemberOrder.objects.filter(id=order_id, status="REQUESTED").first()
        if not order:
            messages.error(request, _("Order not found or is not in REQUESTED status."))
            return redirect("industry_reforged:director_dashboard")

        item_ids = request.POST.getlist("item_ids")
        if not item_ids:
            messages.error(request, _("No items selected for splitting."))
            return redirect("industry_reforged:view_quote", order_id=order.id)

        items_to_split = order.items.filter(id__in=item_ids)

        target_facility_id = request.POST.get("target_facility")
        from ..models import IndustryFacility

        facility = None
        if target_facility_id:
            facility = IndustryFacility.objects.filter(
                facility_id=target_facility_id
            ).first()

        # Parse requested quantities
        split_requests = []
        is_full_split = True
        for item in items_to_split:
            qty_str = request.POST.get(f"split_qty_{item.id}")
            try:
                split_qty = int(qty_str) if qty_str else item.quantity
            except ValueError:
                split_qty = item.quantity

            if split_qty <= 0 or split_qty > item.quantity:
                split_qty = item.quantity

            if split_qty < item.quantity:
                is_full_split = False

            split_requests.append((item, split_qty))

        if is_full_split and items_to_split.count() == order.items.count():
            messages.error(
                request,
                _(
                    "Cannot split all items completely from the order. Just change the facility instead."
                ),
            )
            return redirect("industry_reforged:view_quote", order_id=order.id)

        # Ensure parent has a payment reference
        # Django
        from django.utils.crypto import get_random_string

        if not order.payment_reference:
            order.payment_reference = (
                "ORD-"
                + get_random_string(4).upper()
                + "-"
                + get_random_string(4).upper()
            )
            order.save(update_fields=["payment_reference"])

        child_ref = (
            "ORD-" + get_random_string(4).upper() + "-" + get_random_string(4).upper()
        )

        # Create child order
        child_order = MemberOrder.objects.create(
            character=order.character,
            status="REQUESTED",
            target_facility=facility,
            parent_order=order,
            payment_reference=child_ref,
            notes=f"Split from Order #{order.id}",
        )

        # Process splits
        from ..models import OrderItem

        for item, split_qty in split_requests:
            if split_qty == item.quantity:
                # Full split: move item to child
                item.order = child_order
                item.save(update_fields=["order"])
            else:
                # Partial split
                # 1. Reduce parent item
                item.quantity -= split_qty
                item.save(update_fields=["quantity"])

                # 2. Create child item
                OrderItem.objects.create(
                    order=child_order,
                    item_type=item.item_type,
                    quantity=split_qty,
                    price_per_unit=item.price_per_unit,
                    discount_applied=item.discount_applied,
                )

        # Recalculate estimated total price for both parent and child based on line_totals
        parent_total = sum(item.line_total for item in order.items.all())
        order.total_price = parent_total
        order.save(update_fields=["total_price"])

        child_total = sum(item.line_total for item in child_order.items.all())
        child_order.total_price = child_total
        child_order.save(update_fields=["total_price"])

        messages.success(
            request,
            _("Order split successfully into Child Order #%(child_id)s.")
            % {"child_id": child_order.id},
        )

    return redirect("industry_reforged:view_quote", order_id=order.id)


def split_bom_component(request: WSGIRequest, order_id: int) -> HttpResponse:
    """Director splits a specific sub-component from the BOM into a new child order"""
    if request.method == "POST":
        order = MemberOrder.objects.filter(id=order_id, status="REQUESTED").first()
        if not order:
            messages.error(request, _("Order not found or is not in REQUESTED status."))
            return redirect("industry_reforged:director_dashboard")

        type_id = request.POST.get("type_id")
        quantity_str = request.POST.get("quantity")
        target_facility_id = request.POST.get("target_facility")

        if not type_id or not quantity_str:
            messages.error(request, _("Invalid component selection."))
            return redirect("industry_reforged:view_quote", order_id=order.id)

        try:
            quantity = int(quantity_str)
        except ValueError:
            messages.error(request, _("Invalid quantity."))
            return redirect("industry_reforged:view_quote", order_id=order.id)

        # Third Party
        from eveuniverse.models import EveType

        product_type = EveType.objects.filter(id=type_id).first()
        if not product_type:
            messages.error(request, _("Invalid EveType."))
            return redirect("industry_reforged:view_quote", order_id=order.id)

        from ..models import IndustryFacility

        facility = None
        if target_facility_id:
            facility = IndustryFacility.objects.filter(
                facility_id=target_facility_id
            ).first()

        # Ensure parent has a payment reference
        # Django
        from django.utils.crypto import get_random_string

        if not order.payment_reference:
            order.payment_reference = (
                "ORD-"
                + get_random_string(4).upper()
                + "-"
                + get_random_string(4).upper()
            )
            order.save(update_fields=["payment_reference"])

        child_ref = (
            "ORD-" + get_random_string(4).upper() + "-" + get_random_string(4).upper()
        )

        # Create child order
        child_order = MemberOrder.objects.create(
            character=order.character,
            status="REQUESTED",
            target_facility=facility,
            parent_order=order,
            payment_reference=child_ref,
            notes=f"Sub-component '{product_type.name}' split from Order #{order.id}",
        )

        from ..models import CorpPricingConfig, CorpTypeDiscount

        corp_id = order.character.corporation_id
        pricing_config = CorpPricingConfig.objects.filter(
            corporation__corporation_id=corp_id
        ).first()

        child_discount = (
            pricing_config.default_discount_percent if pricing_config else 0.0
        )
        if pricing_config:
            td = CorpTypeDiscount.objects.filter(
                config=pricing_config, eve_type=product_type
            ).first()
            if td:
                child_discount = td.discount_percent

        # Create OrderItem on the child order
        from ..models import OrderItem

        item = OrderItem.objects.create(
            order=child_order,
            item_type=product_type,
            quantity=quantity,
            discount_applied=child_discount,
            price_per_unit=0,  # Will be set below
        )

        # Recalculate estimated total price for both parent and child
        # This will now trigger the BOM engine which automatically deducts the child order's items
        # from the parent's BOM.
        # Alliance Auth
        from allianceauth.eveonline.models import EveCorporationInfo

        from ..utils.pricing_engine import calculate_quote

        corp_id = order.character.corporation_id
        try:
            corp_info = EveCorporationInfo.objects.get(corporation_id=corp_id)
        except Exception:
            corp_info = None

        # Child Total (using calculate_quote which looks at the top-level items, i.e., the subcomponent itself)
        child_parsed_items = {item.item_type: item.quantity}
        child_new_total, child_item_details = calculate_quote(
            child_parsed_items, corp_info
        )

        child_order.total_price = child_new_total
        child_order.save(update_fields=["total_price"])

        # Update the child item with the correct quoted price
        if child_item_details:
            detail = child_item_details[0]
            item.price_per_unit = detail["final_price_per_unit"]
            item.discount_applied = detail["discount_percent"]
            item.save(update_fields=["price_per_unit", "discount_applied"])

        # Parent Total (Recalculate parent order total just in case, though view_quote will handle it anyway)
        parent_parsed_items = {i.item_type: i.quantity for i in order.items.all()}
        parent_new_total, parent_item_details = calculate_quote(
            parent_parsed_items, corp_info
        )

        order.total_price = parent_new_total
        order.save(update_fields=["total_price"])

        for detail in parent_item_details:
            i = order.items.filter(item_type=detail["eve_type"]).first()
            if i:
                i.price_per_unit = detail["final_price_per_unit"]
                i.discount_applied = detail["discount_percent"]
                i.save(update_fields=["price_per_unit", "discount_applied"])

        messages.success(
            request,
            _(
                "Sub-component %(name)s split successfully into Child Order #%(child_id)s."
            )
            % {"name": product_type.name, "child_id": child_order.id},
        )

    return redirect("industry_reforged:view_quote", order_id=order.id)
