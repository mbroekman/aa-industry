# Standard Library
from decimal import Decimal

# Third Party
import pytest

# Django
from django.utils import timezone

# AA Industry App
from industry_reforged.models import (
    CorpMOTD,
    CorporationSyncConfig,
    CorporationWebhookConfig,
    CorpWalletJournal,
    TaxConfig,
    WalletJournalSyncState,
)

from .factories import (
    CorpWalletDivisionFactory,
    EveCharacterFactory,
    EveCorporationInfoFactory,
)


@pytest.mark.django_db
class TestMoreModels:
    def test_corp_wallet_division_str(self):
        div = CorpWalletDivisionFactory(division=2, name="Operations")
        assert "Operations" in str(div)
        assert "Div 2" in str(div)

    def test_corporation_sync_config_str(self):
        corp = EveCorporationInfoFactory(corporation_name="Test Corp")
        char = EveCharacterFactory()
        config = CorporationSyncConfig.objects.create(
            corporation=corp, sync_character=char
        )
        assert str(config) == "Test Corp Sync Config"

    def test_corporation_webhook_config_str(self):
        corp = EveCorporationInfoFactory(corporation_name="Webhook Corp")
        config = CorporationWebhookConfig.objects.create(corporation=corp)
        assert str(config) == "Webhook Corp Webhooks"

    def test_corp_motd_str(self):
        corp = EveCorporationInfoFactory(corporation_name="MOTD Corp")
        motd = CorpMOTD.objects.create(corporation=corp, message="Hello")
        assert "MOTD for MOTD Corp" in str(motd)

    def test_tax_config_str(self):
        corp = EveCorporationInfoFactory(corporation_ticker="TICK")
        tax = TaxConfig.objects.create(corporation=corp)
        assert "TICK Tax Config" in str(tax)

    def test_wallet_journal_sync_state_str(self):
        corp = EveCorporationInfoFactory(corporation_ticker="TICK2")
        state = WalletJournalSyncState.objects.create(
            corporation=corp, last_journal_id=123
        )
        assert "TICK2" in str(state)
        assert "123" in str(state)

    def test_corp_wallet_journal_str(self):
        div = CorpWalletDivisionFactory(division=1, name="Master")
        journal = CorpWalletJournal.objects.create(
            division=div,
            journal_id=999,
            date=timezone.now(),
            ref_type="player_donation",
            amount=Decimal("100.00"),
            balance=Decimal("100.00"),
        )
        assert "Journal 999" in str(journal)
        assert "player_donation" in str(journal)
