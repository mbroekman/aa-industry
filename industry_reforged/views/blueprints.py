"""App Views for Blueprint Request System"""

# Standard Library
import logging

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

# App
from ..models import (
    BlueprintRequest,
    CorpBlueprint,
    CorporationWebhookConfig,
    ProductionTask,
)
from ..tasks.utils import notify_discord_user
from ..utils.discord import send_discord_webhook

logger = logging.getLogger(__name__)


@login_required
@permission_required("industry_reforged.basic_access")
def blueprint_library(request: WSGIRequest) -> HttpResponse:
    """View to display available corp blueprints for members."""
    # Simple search handling
    query = request.GET.get("q", "")

    # Get distinct blueprint groups for filtering
    # Third Party
    from eveuniverse.models import EveGroup

    group_ids = CorpBlueprint.objects.values_list(
        "eve_type__eve_group_id", flat=True
    ).distinct()
    bp_groups = EveGroup.objects.filter(id__in=group_ids).order_by("name")

    context = {
        "query": query,
        "bp_groups": bp_groups,
    }
    return render(request, "industry_reforged/blueprints/library.html", context)


@login_required
@permission_required("industry_reforged.basic_access")
def request_blueprint(request: WSGIRequest, item_id: int) -> HttpResponse:
    """Endpoint to submit a blueprint request."""
    if request.method == "POST":
        blueprint = get_object_or_404(CorpBlueprint, item_id=item_id)

        try:
            requested_quantity = int(request.POST.get("requested_quantity", 1))
            requested_runs = int(request.POST.get("requested_runs", 1))
            notes = request.POST.get("notes", "")

            if requested_quantity < 1 or requested_runs < 1:
                messages.error(request, _("Quantity and Runs must be at least 1."))
                return redirect("industry_reforged:blueprint_library")

            BlueprintRequest.objects.create(
                requester=request.user,
                blueprint=blueprint,
                requested_quantity=requested_quantity,
                requested_runs=requested_runs,
                notes=notes,
            )

            # Send discord webhook notification
            webhook_configs = CorporationWebhookConfig.objects.all()
            for config in webhook_configs:
                if config.blueprint_requests_webhook:
                    embed = {
                        "title": "New Blueprint Request",
                        "description": f"**{request.user.username}** has requested copies of **{blueprint.eve_type.name}**.",
                        "color": 3447003,  # Blue
                        "fields": [
                            {
                                "name": "Quantity",
                                "value": str(requested_quantity),
                                "inline": True,
                            },
                            {
                                "name": "Runs",
                                "value": str(requested_runs),
                                "inline": True,
                            },
                            {
                                "name": "Notes",
                                "value": notes if notes else "None",
                                "inline": False,
                            },
                        ],
                    }
                    send_discord_webhook(config.blueprint_requests_webhook, embed)

            messages.success(
                request,
                _(f"Request for {blueprint.eve_type.name} submitted successfully."),
            )
        except ValueError:
            messages.error(request, _("Invalid input for quantity or runs."))

    return redirect("industry_reforged:blueprint_library")


@login_required
@permission_required("industry_reforged.corp_access")
def update_request_status(request: WSGIRequest, request_id: int) -> HttpResponse:
    """Endpoint for directors to accept/reject/process a request."""
    if request.method == "POST":
        bp_req = get_object_or_404(BlueprintRequest, id=request_id)
        new_status = request.POST.get("status")

        if new_status in dict(BlueprintRequest.STATUS_CHOICES):
            bp_req.status = new_status
            bp_req.processed_by = request.user
            bp_req.save()

            messages.success(
                request, _(f"Request #{bp_req.id} updated to {new_status}.")
            )

            # If accepted, spawn a ProductionTask for copying (activity_id 5 is copying usually, assuming 5 based on EVE)
            if new_status == "ACCEPTED":
                # Create a job for industrialists
                ProductionTask.objects.create(
                    item_type=bp_req.blueprint.eve_type,
                    quantity=bp_req.requested_quantity,
                    activity_id=5,  # Copying
                    created_from_blueprint_request=bp_req,
                    priority="NORMAL",
                )

            # Send DM to requester
            try:
                if (
                    hasattr(bp_req.requester, "profile")
                    and bp_req.requester.profile.main_character
                ):
                    main_char = bp_req.requester.profile.main_character
                    msg = f"Your Blueprint Request for **{bp_req.blueprint.eve_type.name}** has been marked as **{new_status}** by {request.user.username}."
                    notify_discord_user(main_char, msg)
            except Exception as e:
                logger.error(
                    f"Failed to send DM for blueprint request {bp_req.id}: {e}"
                )

        else:
            messages.error(request, _("Invalid status update."))

    # Redirect back to where they came from
    referer = request.headers.get("referer")
    if referer:
        return HttpResponseRedirect(referer)
    return redirect("/director/?tab=blueprint-requests")
