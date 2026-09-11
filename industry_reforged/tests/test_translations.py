import gettext
from pathlib import Path
import pytest
from django.utils.translation import activate, deactivate, gettext as _


class TestDutchTranslations:
    """Test suite to ensure Dutch translations exist, load, and cover key domain concepts."""

    @classmethod
    def setup_class(cls):
        cls.locale_dir = (
            Path(__file__).resolve().parent.parent / "locale" / "nl" / "LC_MESSAGES"
        )
        cls.mo_file = cls.locale_dir / "django.mo"
        cls.po_file = cls.locale_dir / "django.po"

    def test_mo_file_exists_and_is_valid(self):
        """Verify that django.mo exists and can be loaded as GNUTranslations."""
        assert self.mo_file.exists(), f"Missing compiled binary: {self.mo_file}"
        assert self.mo_file.stat().st_size > 10000, "MO file appears truncated or empty"

        with open(self.mo_file, "rb") as f:
            catalog = gettext.GNUTranslations(f)
        assert catalog is not None

    def test_key_translations_via_gnu_translations(self):
        """Verify that crucial domain terms translate accurately in GNUTranslations."""
        with open(self.mo_file, "rb") as f:
            catalog = gettext.GNUTranslations(f)

        expected = {
            "AI Market Manager": "AI Marktbeheerder",
            "Target Hub (Structure ID)": "Doelhub (Structuur ID)",
            "Target Region": "Doelregio",
            "Opportunity Scanner": "Opportuniteitsscanner",
            "Basket": "Winkelmand",
            "Ledger Transaction": "Grootboektransactie",
            "Sync Corp Blueprints": "Synchroniseer Bedrijfsblauwdrukken",
            "Industry Leaderboard": "Industrie Ranglijst",
            "Are you sure you want to delete this Opportunity Scanner?": "Weet je zeker dat je deze Opportuniteitsscanner wilt verwijderen?",
            "Production Task for %(item_name)s deleted.": "Productietaak voor %(item_name)s verwijderd.",
        }

        for msgid, expected_msgstr in expected.items():
            translated = catalog.gettext(msgid)
            assert (
                translated == expected_msgstr
            ), f"Expected '{msgid}' -> '{expected_msgstr}', got '{translated}'"

    def test_translation_activation_in_django(self):
        """Verify that Django's translation activator correctly uses the Dutch translations."""
        activate("nl")
        try:
            assert _("AI Market Manager") == "AI Marktbeheerder"
            assert _("Opportunity Scanner") == "Opportuniteitsscanner"
            assert _("Basket") == "Winkelmand"
            assert _("Industry Leaderboard") == "Industrie Ranglijst"
        finally:
            deactivate()
