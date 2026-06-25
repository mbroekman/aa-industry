code = """

@login_required
@permission_required("industry_reforged.corp_access")
def director_wallets(request: WSGIRequest) -> HttpResponse:
    \"\"\"Corporate Wallets and Transactions\"\"\"
    from .models import CorpWalletDivision, CorpWalletJournal

    # We show wallets for the first configured corp for simplicity, or all user corps
    user_corps = request.user.character_ownerships.all().values_list(
        "character__corporation_id", flat=True
    )

    divisions = CorpWalletDivision.objects.filter(
        corporation__corporation_id__in=user_corps
    ).order_by("division")

    # Filter journals (default to first division if any)
    selected_division_id = request.GET.get("division")
    if selected_division_id:
        journals = CorpWalletJournal.objects.filter(division_id=selected_division_id).order_by("-date")[:500]
    else:
        # Just show the first division's journals by default
        first_div = divisions.first()
        if first_div:
            journals = CorpWalletJournal.objects.filter(division=first_div).order_by("-date")[:500]
            selected_division_id = first_div.id
        else:
            journals = []

    context = {
        "title": "Corporate Wallets",
        "divisions": divisions,
        "journals": journals,
        "selected_division_id": int(selected_division_id) if selected_division_id else None,
    }
    return render(request, "industry_reforged/director_wallets.html", context)


@login_required
@permission_required("industry_reforged.corp_access")
def trigger_wallet_sync(request: WSGIRequest) -> HttpResponse:
    \"\"\"Manually trigger Wallet sync\"\"\"
    from .tasks import task_sync_corp_wallets

    task_sync_corp_wallets.delay()
    messages.success(
        request,
        "Corporate Wallet sync has been queued in the background. Please refresh in a few minutes.",
    )
    return redirect("industry_reforged:director_wallets")
"""

filepath = (
    "/home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/views.py"
)
with open(filepath, "a") as f:
    f.write(code)

print("Appended director_wallets view successfully.")
