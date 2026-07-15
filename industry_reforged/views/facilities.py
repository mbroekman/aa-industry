"""App Views"""

# Django
from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


def get_corporate_structures_for_dropdown(corporation):
    # Third Party
    import requests

    # Alliance Auth
    from esi.models import Token

    from ..models import CorporationSyncConfig

    if not corporation:
        return []

    sync_config = CorporationSyncConfig.objects.filter(corporation=corporation).first()
    if not sync_config:
        return []

    token = Token.objects.filter(
        character_id=sync_config.sync_character.character_id,
        scopes__name="esi-corporations.read_structures.v1",
    ).first()

    if not token:
        return []

    url = f"https://esi.evetech.net/latest/corporations/{corporation.corporation_id}/structures/?datasource=tranquility"
    headers = {
        "Authorization": f"Bearer {token.valid_access_token()}",
        "Accept": "application/json",
    }
    from ..models import IndustryFacility

    structures = []

    production_facility_ids = set(
        IndustryFacility.objects.filter(is_production_facility=True).values_list(
            "facility_id", flat=True
        )
    )

    # First, fetch from ESI (which gives us structures the corp actually owns/rents)
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            valid_types = {35825, 35826, 35827, 35832, 35833, 35835, 35836, 35834}
            for st in resp.json():
                if (
                    st.get("type_id") in valid_types
                    and st["structure_id"] not in production_facility_ids
                ):
                    structures.append(
                        {
                            "id": st["structure_id"],
                            "name": st["name"],
                            "type_id": st["type_id"],
                            "system_id": st["system_id"],
                        }
                    )
    except Exception:
        pass

    # Second, include any discovered non-production facilities
    known_facility_ids = {s["id"] for s in structures}
    for fac in IndustryFacility.objects.filter(is_production_facility=False):
        if fac.facility_id not in known_facility_ids:
            structures.append(
                {
                    "id": fac.facility_id,
                    "name": fac.name,
                    "type_id": fac.type_id or "",
                    "system_id": fac.solar_system_id or "",
                }
            )
            known_facility_ids.add(fac.facility_id)

    return structures


def add_facility(request: WSGIRequest) -> HttpResponse:
    from ..forms import IndustryFacilityForm, IndustryFacilityRigFormSet

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None
    corp_structures = get_corporate_structures_for_dropdown(corporation)

    if request.method == "POST":
        # Check if the facility already exists in the database
        facility_id = request.POST.get("facility_id")
        instance = None
        if facility_id:
            from ..models import IndustryFacility

            try:
                existing_facility = IndustryFacility.objects.get(pk=facility_id)
                # Only use the instance if it's NOT already a production facility
                if not existing_facility.is_production_facility:
                    instance = existing_facility
            except IndustryFacility.DoesNotExist:
                pass

        form = IndustryFacilityForm(request.POST, instance=instance)
        if form.is_valid():
            facility = form.save()
            formset = IndustryFacilityRigFormSet(request.POST, instance=facility)
            if formset.is_valid():
                formset.save()
                messages.success(request, _("Facility added successfully."))

                # Automatically sync rigs in the background
                from ..tasks.facilities import sync_facility_rigs

                sync_facility_rigs.delay()

                return redirect(
                    reverse("industry_reforged:director_config") + "#facilities"
                )
            else:
                # If it was a pre-existing facility that we were updating, revert the flag.
                # If it was a completely new facility, delete it.
                if instance:
                    facility.is_production_facility = False
                    facility.save()
                else:
                    facility.delete()
        else:
            formset = IndustryFacilityRigFormSet(request.POST)
    else:
        form = IndustryFacilityForm()
        formset = IndustryFacilityRigFormSet()

    return render(
        request,
        "industry_reforged/manage_facility.html",
        {
            "form": form,
            "formset": formset,
            "corp_structures": corp_structures,
            "title": _("Add Production Facility"),
        },
    )


def edit_facility(request: WSGIRequest, facility_id: int) -> HttpResponse:
    from ..forms import IndustryFacilityForm, IndustryFacilityRigFormSet
    from ..models import IndustryFacility

    main_char = request.user.profile.main_character
    corporation = main_char.corporation if main_char else None
    corp_structures = get_corporate_structures_for_dropdown(corporation)

    facility = get_object_or_404(IndustryFacility, pk=facility_id)
    if request.method == "POST":
        form = IndustryFacilityForm(request.POST, instance=facility)
        formset = IndustryFacilityRigFormSet(request.POST, instance=facility)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, _("Facility updated successfully."))

            # Automatically sync rigs in the background
            from ..tasks.facilities import sync_facility_rigs

            sync_facility_rigs.delay()

            return redirect(
                reverse("industry_reforged:director_config") + "#facilities"
            )
    else:
        form = IndustryFacilityForm(instance=facility)
        formset = IndustryFacilityRigFormSet(instance=facility)

    return render(
        request,
        "industry_reforged/manage_facility.html",
        {
            "form": form,
            "formset": formset,
            "facility": facility,
            "corp_structures": corp_structures,
            "title": _("Edit Production Facility"),
        },
    )


def delete_facility(request: WSGIRequest, facility_id: int) -> HttpResponse:
    from ..models import IndustryFacility

    if request.method == "POST":
        facility = get_object_or_404(IndustryFacility, pk=facility_id)
        facility.delete()
        messages.success(request, _("Facility deleted successfully."))
    return redirect(reverse("industry_reforged:director_config") + "#facilities")
