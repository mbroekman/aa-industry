"""App Tasks"""

# Standard Library
import datetime
import logging

# Third Party
from celery import shared_task

# Django
from django.utils import timezone

# Alliance Auth
from esi.exceptions import HTTPNotModified
from esi.models import Token

from .utils import esi, log_task_execution

logger = logging.getLogger(__name__)


@shared_task(name="industry_reforged.tasks.task_sync_corp_wallets")
@log_task_execution("Task Sync Corp Wallets")
def task_sync_corp_wallets():
    """Fetch corporate wallets and journals from ESI."""
    from ..models import CorporationSyncConfig, CorpWalletDivision, CorpWalletJournal

    configs = CorporationSyncConfig.objects.select_related(
        "sync_character", "corporation"
    )

    for config in configs:
        token = Token.objects.filter(
            character_id=config.sync_character.character_id,
            scopes__name="esi-wallet.read_corporation_wallets.v1",
        ).first()

        if not token:
            logger.warning(
                f"No corporate wallet token found for {config.sync_character.character_name}"
            )
            continue

        # Try to fetch actual division names
        div_token = Token.objects.filter(
            character_id=config.sync_character.character_id,
            scopes__name="esi-corporations.read_divisions.v1",
        ).first()

        division_names = {}
        if div_token:
            try:
                divisions = (
                    esi.client.Corporation.GetCorporationsCorporationIdDivisions(
                        corporation_id=config.corporation.corporation_id,
                        token=div_token,
                    ).result()
                )
                if hasattr(divisions, "wallet") and divisions.wallet:
                    for d in divisions.wallet:
                        div_name = d.name
                        if not div_name:
                            div_name = (
                                "Master Wallet"
                                if d.division == 1
                                else f"Division {d.division}"
                            )
                        division_names[d.division] = div_name
                        logger.info(
                            f"Fetched division {div_name} ({d.division}) for {config.corporation}"
                        )
            except Exception as e:
                logger.warning(
                    f"Could not fetch division names for {config.corporation}: {e}"
                )

        try:
            # 1. Fetch division balances
            wallets = esi.client.Wallet.GetCorporationsCorporationIdWallets(
                corporation_id=config.corporation.corporation_id, token=token
            ).result()

            divisions_map = {}
            if wallets:
                for w in wallets:
                    division_id = getattr(w, "division")
                    balance = getattr(w, "balance")
                    div, created = CorpWalletDivision.objects.update_or_create(
                        corporation=config.corporation,
                        division=division_id,
                        defaults={"balance": balance},
                    )

                    if division_names and division_id in division_names:
                        div.name = division_names[division_id]
                        div.save(update_fields=["name"])
                    elif not div.name:
                        div.name = f"Division {division_id}"
                        if division_id == 1:
                            div.name = "Master Wallet"
                        div.save(update_fields=["name"])

                    divisions_map[division_id] = div

                    from ..models import CorporationWebhookConfig

                    now = timezone.now()

                    webhook_config = CorporationWebhookConfig.objects.filter(
                        corporation=config.corporation
                    ).first()
                    threshold = div.warning_threshold

                    if balance < threshold:
                        if not div.last_warning or (
                            now - div.last_warning
                        ) > datetime.timedelta(days=1):
                            if webhook_config and webhook_config.wallets_webhook:
                                from ..utils.discord import send_discord_webhook

                                embed = {
                                    "title": f"Low Wallet Balance: {div.name}",
                                    "description": f"Balance is **{balance:,.2f} ISK**, which is below the threshold of **{threshold:,.2f} ISK**.",
                                    "color": 15158332,  # Red
                                }
                                send_discord_webhook(
                                    webhook_config.wallets_webhook, embed
                                )
                            div.last_warning = now
                            div.save()

            # 2. Fetch journal entries for each division
            for division_id, div_obj in divisions_map.items():
                try:
                    journal_entries = esi.client.Wallet.GetCorporationsCorporationIdWalletsDivisionJournal(
                        corporation_id=config.corporation.corporation_id,
                        division=division_id,
                        token=token,
                    ).result()

                    if journal_entries:
                        journal_objects = []
                        seen_j_ids = set()
                        for entry in journal_entries:
                            j_id = getattr(entry, "id")
                            if j_id in seen_j_ids:
                                continue
                            seen_j_ids.add(j_id)

                            # Check if exists to avoid bulk_create collisions (if we weren't ignoring conflicts)
                            if not CorpWalletJournal.objects.filter(
                                division=div_obj, journal_id=j_id
                            ).exists():
                                journal_objects.append(
                                    CorpWalletJournal(
                                        division=div_obj,
                                        journal_id=j_id,
                                        date=getattr(entry, "date"),
                                        ref_type=getattr(entry, "ref_type"),
                                        amount=getattr(entry, "amount", None),
                                        balance=getattr(entry, "balance", None),
                                        reason=str(getattr(entry, "reason", ""))[:250],
                                        description=str(
                                            getattr(entry, "description", "")
                                        )[:250],
                                        first_party_id=getattr(
                                            entry, "first_party_id", None
                                        ),
                                        second_party_id=getattr(
                                            entry, "second_party_id", None
                                        ),
                                        tax=getattr(entry, "tax", None),
                                        tax_receiver_id=getattr(
                                            entry, "tax_receiver_id", None
                                        ),
                                    )
                                )
                        if journal_objects:
                            CorpWalletJournal.objects.bulk_create(
                                journal_objects, ignore_conflicts=True
                            )

                except HTTPNotModified:
                    continue
                except Exception as e:
                    logger.error(
                        f"Failed to fetch journal for div {division_id} (corp {config.corporation.corporation_id}): {e}"
                    )

        except HTTPNotModified:
            continue
        except Exception as e:
            logger.error(
                f"Failed to fetch wallets for corp {config.corporation.corporation_id}: {e}"
            )

    # After syncing wallets, check for any payments that match pending payouts or orders
    task_process_wallet_payments.delay()


@shared_task(name="industry_reforged.tasks.task_process_wallet_payments")
@log_task_execution("Task Process Wallet Payments")
def task_process_wallet_payments():
    """Process new wallet journal entries and match them to Orders and Payouts."""
    from ..models import (
        BuilderPayoutBatch,
        CorpWalletJournal,
        EveCorporationInfo,
        MemberOrder,
        WalletJournalSyncState,
    )

    # Ensure all corps have a sync state
    for corp in EveCorporationInfo.objects.all():
        WalletJournalSyncState.objects.get_or_create(corporation=corp)

    states = WalletJournalSyncState.objects.all()

    # Pre-fetch pending payments
    unpaid_orders = {
        order.payment_reference: order
        for order in MemberOrder.objects.filter(is_paid=False)
        .exclude(payment_reference__isnull=True)
        .exclude(payment_reference="")
    }
    pending_batches = {
        batch.payment_reference: batch
        for batch in BuilderPayoutBatch.objects.filter(status="PENDING")
    }

    if not unpaid_orders and not pending_batches:
        return  # Nothing to look for

    for state in states:
        entries = CorpWalletJournal.objects.filter(
            division__corporation=state.corporation,
            journal_id__gt=state.last_journal_id,
        ).order_by("journal_id")

        if not entries.exists():
            continue

        highest_id = state.last_journal_id

        for entry in entries:
            highest_id = max(highest_id, entry.journal_id)
            reason = entry.reason or ""

            # Incoming payment (Client -> Corp)
            if entry.amount is not None and entry.amount > 0:
                # Iterate over a list of items so we can safely modify/pop the dict if needed
                for ref, order in list(unpaid_orders.items()):
                    if ref in reason:
                        order.amount_paid += entry.amount
                        note = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Auto Sync: Received payment of {entry.amount:,.2f} ISK."
                        if order.notes:
                            order.notes += f"\n{note}"
                        else:
                            order.notes = note

                        if order.amount_paid >= order.total_price:
                            order.is_paid = True
                            unpaid_orders.pop(ref, None)

                        order.save()
                        break

            # Outgoing payment (Corp -> Builder)
            elif entry.amount is not None and entry.amount < 0:
                for ref, batch in pending_batches.items():
                    if ref in reason and abs(entry.amount) >= batch.total_amount:
                        batch.status = "PAID"
                        batch.paid_at = timezone.now()
                        batch.save()
                        pending_batches.pop(ref, None)
                        break

        # Save highest processed ID
        state.last_journal_id = highest_id
        state.save()
