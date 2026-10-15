"""App Tasks"""

# Standard Library
import logging

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


def _send_contract_notifications(contract, result, is_new_flag: bool):
    """Discord webhook for the director channel on a new flagged/matched
    contract, plus a per-member DM on the status change."""
    from ..models import CorporationWebhookConfig

    if result.status == "FLAGGED":
        webhook_config = CorporationWebhookConfig.objects.filter(
            corporation=contract.program.corporation
        ).first()
        if webhook_config and webhook_config.buyback_webhook:
            from ..utils.discord import send_discord_webhook

            embed = {
                "title": f"Buyback Contract Flagged: {contract.tracking_number}",
                "description": result.notes or "Needs director review.",
                "color": 15158332,  # Red
            }
            send_discord_webhook(webhook_config.buyback_webhook, embed)

    if is_new_flag and contract.character:
        if result.status == "FLAGGED":
            notify_discord_user(
                contract.character,
                f"Your buyback contract {contract.tracking_number} needs review: {result.notes}",
            )
        elif result.status == "MATCHED":
            notify_discord_user(
                contract.character,
                f"Your buyback contract {contract.tracking_number} was matched successfully.",
            )


@shared_task(name="industry_reforged.tasks.buyback_poll_contracts")
@log_task_execution("Buyback Poll Contracts")
def buyback_poll_contracts():
    """
    Poll ESI corp contracts for every active BuybackProgram, match by tracking
    number, update BuybackContract rows, fire notifications.

    Idempotency is structural: esi_contract_id is DB-unique and every write is
    scoped per-row via .update(), so two overlapping runs can't duplicate or
    corrupt state - the lock below only avoids redundant ESI calls, and self-
    heals within 5 minutes if a worker dies mid-run (not the source project's
    unbounded, manually-flushed lock).
    """
    from ..models import BuybackContract, BuybackProgram, CorporationSyncConfig

    programs = BuybackProgram.objects.filter(is_active=True).select_related("corporation")

    for program in programs:
        lock_key = f"buyback_poll_lock_{program.corporation_id}"
        if not cache.add(lock_key, 1, timeout=300):
            continue

        try:
            sync_config = CorporationSyncConfig.objects.filter(
                corporation=program.corporation
            ).select_related("sync_character").first()
            if not sync_config:
                logger.warning(f"No sync config for corporation {program.corporation_id}")
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
            except Exception as e:
                logger.error(f"Failed to fetch contracts for {program.corporation_id}: {e}")
                continue

            for esi_contract in contracts:
                contract_type = getattr(esi_contract, "type", None)
                if contract_type != "item_exchange":
                    continue

                title = getattr(esi_contract, "title", "") or ""
                tracking_number = extract_tracking_number(title)
                if not tracking_number:
                    continue

                contract = BuybackContract.objects.filter(
                    tracking_number=tracking_number, program=program
                ).exclude(status__in=TERMINAL_STATUSES).first()
                if not contract:
                    continue

                esi_contract_id = getattr(esi_contract, "contract_id")
                was_pending = contract.status == "PENDING"

                try:
                    items = esi.client.Contracts.GetCorporationsCorporationIdContractsContractIdItems(
                        corporation_id=program.corporation.corporation_id,
                        contract_id=esi_contract_id,
                        token=token,
                    ).result()
                except Exception as e:
                    logger.error(f"Failed to fetch items for contract {esi_contract_id}: {e}")
                    continue

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

                BuybackContract.objects.filter(pk=contract.pk).update(
                    esi_contract_id=esi_contract_id,
                    esi_issuer_character_id=getattr(esi_contract, "issuer_id", None),
                    esi_acceptor_character_id=getattr(esi_contract, "acceptor_id", None),
                    contract_price=getattr(esi_contract, "price", None),
                    contract_title=title,
                    status=result.status,
                    flag_item_mismatch=result.item_mismatch,
                    flag_price_mismatch=result.price_mismatch,
                    flag_structure_mismatch=result.structure_mismatch,
                    flag_receiver_mismatch=result.receiver_mismatch,
                    flag_title_tampered=result.title_tampered,
                    flag_no_tracking=result.no_tracking,
                    flag_notes=result.notes,
                )

                contract.refresh_from_db()
                _send_contract_notifications(contract, result, is_new_flag=was_pending)
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
        deadline = contract.created_at + timezone.timedelta(days=contract.program.contract_expiry_days)
        if timezone.now() > deadline:
            contract.status = "EXPIRED"
            contract.save(update_fields=["status"])
            if contract.character:
                notify_discord_user(
                    contract.character,
                    f"Your buyback contract {contract.tracking_number} expired - no matching contract was seen in time.",
                )
