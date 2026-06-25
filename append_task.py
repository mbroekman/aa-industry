code = """
@shared_task
def task_sync_corp_wallets():
    \"\"\"Fetch corporate wallets and journals from ESI.\"\"\"
    from .models import CorpWalletDivision, CorpWalletJournal, CorporationSyncConfig
    # Third Party
    from dateutil.parser import parse

    configs = CorporationSyncConfig.objects.select_related("sync_character", "corporation")

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
                        defaults={"balance": balance}
                    )
                    # We might not know the name initially, default to Division X
                    if not div.name:
                        div.name = f"Division {division_id}"
                        div.save()
                    divisions_map[division_id] = div

            # 2. Fetch journal entries for each division
            for division_id, div_obj in divisions_map.items():
                try:
                    journal_entries = esi.client.Wallet.GetCorporationsCorporationIdWalletsDivisionJournal(
                        corporation_id=config.corporation.corporation_id,
                        division=division_id,
                        token=token
                    ).result()

                    if journal_entries:
                        journal_objects = []
                        for entry in journal_entries:
                            j_id = getattr(entry, "id")
                            # Check if exists to avoid bulk_create collisions
                            if not CorpWalletJournal.objects.filter(division=div_obj, journal_id=j_id).exists():
                                journal_objects.append(
                                    CorpWalletJournal(
                                        division=div_obj,
                                        journal_id=j_id,
                                        date=getattr(entry, "date"),
                                        ref_type=getattr(entry, "ref_type"),
                                        amount=getattr(entry, "amount", None),
                                        balance=getattr(entry, "balance", None),
                                        reason=getattr(entry, "reason", None),
                                        description=getattr(entry, "description", None),
                                        first_party_id=getattr(entry, "first_party_id", None),
                                        second_party_id=getattr(entry, "second_party_id", None),
                                        tax=getattr(entry, "tax", None),
                                        tax_receiver_id=getattr(entry, "tax_receiver_id", None),
                                    )
                                )
                        if journal_objects:
                            CorpWalletJournal.objects.bulk_create(journal_objects)

                except HTTPNotModified:
                    continue
                except Exception as e:
                    logger.error(f"Failed to fetch journal for div {division_id} (corp {config.corporation.corporation_id}): {e}")

        except HTTPNotModified:
            continue
        except Exception as e:
            logger.error(
                f"Failed to fetch wallets for corp {config.corporation.corporation_id}: {e}"
            )
"""

filepath = (
    "/home/mbroekman/Development/aa-dev/working/aa-industry/industry_reforged/tasks.py"
)
with open(filepath, "a") as f:
    f.write(code)

print("Appended task_sync_corp_wallets successfully.")
