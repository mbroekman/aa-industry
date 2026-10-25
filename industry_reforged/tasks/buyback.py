"""App Tasks"""

# Standard Library
import logging
from collections import Counter
from datetime import datetime

# Third Party
from celery import shared_task

# Django
from django.core.cache import cache
from django.utils import timezone

# Alliance Auth
from esi.models import Token

from ..utils.buyback_matching import (
    BuybackContractExpectation,
    ExpectedItem,
    extract_tracking_number,
    match_contract,
)
from .utils import esi, log_task_execution, notify_discord_user

logger = logging.getLogger(__name__)

CONTRACTS_SCOPE = "esi-contracts.read_corporation_contracts.v1"
TERMINAL_STATUSES = ("PAID", "REJECTED", "CANCELLED", "EXPIRED")

# ESI contract statuses. "finished*" means the receiver accepted it in-game, so
# the seller has been paid; "deleted"/"cancelled" means the seller withdrew it
# and may still create a corrected one before the program's expiry.
ESI_FINISHED = ("finished", "finished_issuer", "finished_contractor")
ESI_REJECTED = ("rejected",)
ESI_WITHDRAWN = ("deleted", "cancelled")


def _build_expectation(contract) -> BuybackContractExpectation:
    program = contract.program
    location_id = None
    if program.facility_id:
        location_id = program.facility_id
    elif program.known_location_id:
        location_id = program.known_location_id

    expected_items = [
        ExpectedItem(type_id=item.eve_type_id, quantity=item.quantity)
        for item in contract.items.all()
    ]

    return BuybackContractExpectation(
        tracking_number=contract.tracking_number,
        expected_items=expected_items,
        expected_price=float(contract.quoted_price),
        expected_location_id=location_id,
        expected_receiver_id=program.corporation.corporation_id,
    )


def watchlist_flag_notes(program, type_ids) -> list[str]:
    """One note per watchlist entry in flag mode (not blocking) that matches."""
    from ..models import BuybackWatchlistItem

    hits = BuybackWatchlistItem.objects.filter(
        program=program, blocks_submission=False, eve_type_id__in=type_ids
    ).select_related("eve_type")
    return [
        f"Watchlisted item: {hit.eve_type.name}" + (f" ({hit.reason})" if hit.reason else "")
        for hit in hits
    ]


def _notify_member(contract, message: str):
    if contract.character:
        notify_discord_user(contract.character, message)


def _send_match_notifications(contract):
    """Fired once, on the PENDING -> MATCHED/FLAGGED transition."""
    from ..models import CorporationWebhookConfig

    if contract.status == "FLAGGED":
        webhook_config = CorporationWebhookConfig.objects.filter(
            corporation=contract.program.corporation
        ).first()
        if webhook_config and webhook_config.buyback_webhook:
            from ..utils.discord import send_discord_webhook

            embed = {
                "title": f"Buyback Contract Flagged: {contract.tracking_number}",
                "description": contract.flag_notes or "Needs director review.",
                "color": 15158332,  # Red
            }
            send_discord_webhook(webhook_config.buyback_webhook, embed)
        _notify_member(
            contract,
            f"Your buyback contract {contract.tracking_number} needs review: {contract.flag_notes}",
        )
    elif contract.status == "MATCHED":
        _notify_member(
            contract,
            f"Your buyback contract {contract.tracking_number} was matched successfully.",
        )


def _match(contract, esi_contract, program, token) -> bool:
    """Compare the in-game contract against the appraisal and store the result.
    Returns False if the contract items couldn't be fetched (retry next poll)."""
    from ..models import BuybackContract

    esi_contract_id = getattr(esi_contract, "contract_id")
    try:
        items = esi.client.Contracts.GetCorporationsCorporationIdContractsContractIdItems(
            corporation_id=program.corporation.corporation_id,
            contract_id=esi_contract_id,
            token=token,
        ).result()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to fetch items for contract {esi_contract_id}: {e}")
        return False

    title = getattr(esi_contract, "title", "") or ""
    esi_contract_dict = {
        "title": title,
        "price": getattr(esi_contract, "price", 0.0),
        "start_location_id": getattr(esi_contract, "start_location_id", None),
        "acceptor_id": getattr(esi_contract, "acceptor_id", None),
        "assignee_id": getattr(esi_contract, "assignee_id", None),
    }
    esi_items = [
        {
            "type_id": getattr(i, "type_id", None),
            "quantity": getattr(i, "quantity", 0),
        }
        for i in items
    ]

    result = match_contract(_build_expectation(contract), esi_contract_dict, esi_items)

    # Watchlist "flag" items send the contract to review even when the in-game
    # contract itself is clean.
    watchlist_notes = watchlist_flag_notes(
        program, [item.eve_type_id for item in contract.items.all()]
    )
    status = "FLAGGED" if watchlist_notes else result.status
    notes = "\n".join(watchlist_notes + ([result.notes] if result.notes else []))

    BuybackContract.objects.filter(pk=contract.pk).update(
        esi_contract_id=esi_contract_id,
        esi_issuer_character_id=getattr(esi_contract, "issuer_id", None),
        esi_acceptor_character_id=getattr(esi_contract, "acceptor_id", None),
        contract_price=getattr(esi_contract, "price", None),
        contract_title=title,
        status=status,
        flag_item_mismatch=result.item_mismatch,
        flag_price_mismatch=result.price_mismatch,
        flag_structure_mismatch=result.structure_mismatch,
        flag_receiver_mismatch=result.receiver_mismatch,
        flag_title_tampered=result.title_tampered,
        flag_no_tracking=result.no_tracking,
        flag_watchlist=bool(watchlist_notes),
        flag_notes=notes,
        updated_at=timezone.now(),
    )

    esi_totals = Counter()
    for item in esi_items:
        esi_totals[item["type_id"]] += item["quantity"]
    for item in contract.items.all():
        verified = esi_totals.get(item.eve_type_id, 0) == item.quantity
        if item.is_esi_verified != verified:
            item.is_esi_verified = verified
            item.save(update_fields=["is_esi_verified"])

    contract.refresh_from_db()
    _send_match_notifications(contract)
    return True


def _follow_esi_status(contract, esi_contract):
    """Apply what happened to the matched contract in-game."""
    from ..models import BuybackContract

    esi_status = getattr(esi_contract, "status", None)
    if not isinstance(esi_status, str):
        esi_status = "outstanding"

    if esi_status in ESI_FINISHED:
        if contract.mark_paid(notes="Buyback payout (contract accepted in-game)"):
            _notify_member(
                contract,
                f"Your buyback contract {contract.tracking_number} was accepted and paid.",
            )
    elif esi_status in ESI_REJECTED:
        contract.status = "REJECTED"
        contract.save(update_fields=["status", "updated_at"])
        _notify_member(
            contract,
            f"Your buyback contract {contract.tracking_number} was rejected in-game.",
        )
    elif esi_status in ESI_WITHDRAWN:
        # The seller withdrew it - typically to fix it. Go back to PENDING so a
        # corrected contract with the same tracking number can still match.
        BuybackContract.objects.filter(pk=contract.pk).update(
            status="PENDING",
            esi_contract_id=None,
            contract_price=None,
            contract_title="",
            updated_at=timezone.now(),
        )
    else:
        date_expired = getattr(esi_contract, "date_expired", None)
        if isinstance(date_expired, datetime) and date_expired < timezone.now():
            contract.status = "EXPIRED"
            contract.save(update_fields=["status", "updated_at"])
            _notify_member(
                contract,
                f"Your buyback contract {contract.tracking_number} expired in-game without being accepted.",
            )


@shared_task(name="industry_reforged.tasks.buyback_poll_contracts")
@log_task_execution("Buyback Poll Contracts")
def buyback_poll_contracts():
    """
    Poll ESI corp contracts for every active BuybackProgram. A contract is
    matched (items compared, flags set, notifications sent) once, when first
    seen; after that only its in-game status is followed (paid, rejected,
    withdrawn, expired).

    Idempotency is structural: esi_contract_id is DB-unique, the payout goes
    through BuybackContract.mark_paid() (records once), and notifications only
    fire on status transitions. The lock below only avoids redundant ESI calls
    and self-heals within 5 minutes if a worker dies mid-run.
    """
    from ..models import BuybackContract, BuybackProgram, CorporationSyncConfig

    programs = BuybackProgram.objects.filter(is_active=True).select_related(
        "corporation"
    )

    for program in programs:
        lock_key = f"buyback_poll_lock_{program.corporation_id}"
        if not cache.add(lock_key, 1, timeout=300):
            continue

        try:
            sync_config = (
                CorporationSyncConfig.objects.filter(corporation=program.corporation)
                .select_related("sync_character")
                .first()
            )
            if not sync_config:
                logger.warning(
                    f"No sync config for corporation {program.corporation_id}"
                )
                continue

            token = Token.objects.filter(
                character_id=sync_config.sync_character.character_id,
                scopes__name=CONTRACTS_SCOPE,
            ).first()
            if not token:
                logger.warning(
                    f"No contracts-scope token for {sync_config.sync_character.character_name}"
                )
                continue

            try:
                contracts = esi.client.Contracts.GetCorporationsCorporationIdContracts(
                    corporation_id=program.corporation.corporation_id, token=token
                ).results()
            except Exception as e:  # noqa: BLE001
                logger.error(
                    f"Failed to fetch contracts for {program.corporation_id}: {e}"
                )
                continue

            for esi_contract in contracts:
                if getattr(esi_contract, "type", None) != "item_exchange":
                    continue

                tracking_number = extract_tracking_number(
                    getattr(esi_contract, "title", "") or ""
                )
                if not tracking_number:
                    continue

                contract = (
                    BuybackContract.objects.filter(
                        tracking_number=tracking_number, program=program
                    )
                    .exclude(status__in=TERMINAL_STATUSES)
                    .first()
                )
                if not contract:
                    continue

                esi_contract_id = getattr(esi_contract, "contract_id")
                if contract.esi_contract_id is None:
                    if not _match(contract, esi_contract, program, token):
                        continue
                elif contract.esi_contract_id != esi_contract_id:
                    # A second in-game contract with the same tracking number;
                    # the first one stays authoritative until it's withdrawn.
                    continue

                _follow_esi_status(contract, esi_contract)
        finally:
            cache.delete(lock_key)


@shared_task(name="industry_reforged.tasks.buyback_purge_stale_contracts")
@log_task_execution("Buyback Purge Stale Contracts")
def buyback_purge_stale_contracts():
    """Expire PENDING contracts older than program.contract_expiry_days with
    no matching ESI contract ever seen."""
    from ..models import BuybackContract

    pending = BuybackContract.objects.filter(status="PENDING").select_related("program")

    for contract in pending:
        deadline = contract.created_at + timezone.timedelta(
            days=contract.program.contract_expiry_days
        )
        if timezone.now() > deadline:
            contract.status = "EXPIRED"
            contract.save(update_fields=["status", "updated_at"])
            _notify_member(
                contract,
                f"Your buyback contract {contract.tracking_number} expired - no matching contract was seen in time.",
            )
