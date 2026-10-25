# Python
# Standard Library
from decimal import Decimal
from unittest.mock import patch

# Django
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth
from allianceauth.framework.staticfiles.storage import AaManifestStaticFilesStorage
from allianceauth.tests.auth_utils import AuthUtils

# AA Industry App
from industry_reforged.forms import (
    BuybackProgramForm,
    CorpItemConfigForm,
    CorpPricingConfigForm,
)
from industry_reforged.models import CorpPricingConfig
from industry_reforged.tests.factories import (
    EveCharacterFactory,
    EveCorporationInfoFactory,
)
from industry_reforged.views.director import (
    director_config,
    director_config_pricing_edit,
)


class TestDirectorConfigIskFormatting(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = AuthUtils.create_user("director_isk_tester")
        cls.user.is_superuser = True
        cls.corp = EveCorporationInfoFactory(corporation_id=98000101)
        cls.char = EveCharacterFactory(
            character_id=91000101,
            corporation_id=cls.corp.corporation_id,
            corporation_name=cls.corp.corporation_name,
        )
        cls.user.profile.main_character = cls.char
        cls.user.profile.save()
        cls.user.save()

        cls.pricing = CorpPricingConfig.objects.create(
            corporation=cls.corp,
            builder_base_fee=Decimal("1500000.00"),
            builder_hourly_rate=Decimal("800000.00"),
            builder_reward_percent=1.0,
            builder_min_reward=Decimal("3000000.00"),
            builder_max_reward=Decimal("85000000.00"),
        )
        cls.factory = RequestFactory()

    def _prepare_request(self, request):
        request.user = self.user
        SessionMiddleware(lambda req: None).process_request(request)
        MessageMiddleware(lambda req: None).process_request(request)
        return request

    def test_form_widgets_have_isk_input_class(self):
        """Verify that ISK configuration fields have the .isk-input CSS class for live formatting."""
        pricing_form = CorpPricingConfigForm()
        for field_name in [
            "builder_base_fee",
            "builder_hourly_rate",
            "builder_min_reward",
            "builder_max_reward",
        ]:
            widget_class = pricing_form.fields[field_name].widget.attrs.get("class", "")
            self.assertIn(
                "isk-input",
                widget_class,
                f"Field {field_name} widget should have 'isk-input' class",
            )

        item_form = CorpItemConfigForm()
        self.assertIn(
            "isk-input",
            item_form.fields["manual_price"].widget.attrs.get("class", ""),
        )

        buyback_form = BuybackProgramForm()
        self.assertIn(
            "isk-input",
            buyback_form.fields["price_density_threshold"].widget.attrs.get(
                "class", ""
            ),
        )

    @patch.object(
        AaManifestStaticFilesStorage, "stored_name", side_effect=lambda name: name
    )
    def test_director_config_form_renders_live_preview_script(self, mock_stored_name):
        """Ensure director_config_form.html contains the extra_javascript block and ISK preview helper."""
        request = self.factory.get(
            reverse(
                "industry_reforged:director_config_pricing_edit", args=[self.pricing.id]
            )
        )
        self._prepare_request(request)

        response = director_config_pricing_edit(request, config_id=self.pricing.id)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        self.assertIn("formatIskDisplay", content)
        self.assertIn("isk-preview-wrapper", content)
        self.assertIn("id_builder_base_fee", content)
        self.assertIn("id_builder_max_reward", content)

    @patch.object(
        AaManifestStaticFilesStorage, "stored_name", side_effect=lambda name: name
    )
    def test_director_config_overview_renders_builder_pricing_tab(
        self, mock_stored_name
    ):
        """Ensure director_config.html displays dedicated Builder Pricing tab and Floor reward."""
        request = self.factory.get(reverse("industry_reforged:director_config"))
        self._prepare_request(request)

        response = director_config(request)
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")
        self.assertIn("builder-pricing", content)
        self.assertIn("Builder Pricing", content)
        self.assertIn("Base Fee", content)
        self.assertIn("Floor:", content)
        self.assertIn("Cap:", content)

    def test_director_config_pricing_edit_redirects_to_builder_pricing_tab(self):
        """Ensure submitting builder pricing redirects back to the #builder-pricing tab."""
        request = self.factory.post(
            reverse(
                "industry_reforged:director_config_pricing_edit", args=[self.pricing.id]
            ),
            data={
                "corporation": self.corp.id,
                "default_discount_percent": "5.0",
                "builder_base_fee": "2000000.00",
                "builder_hourly_rate": "1000000.00",
                "builder_reward_percent": "0.5",
                "builder_min_reward": "2500000.00",
                "builder_max_reward": "80000000.00",
                "builder_urgent_multiplier": "1.5",
                "builder_high_multiplier": "1.25",
                "builder_low_multiplier": "0.8",
                "default_t1_me": "10",
                "default_t2_me": "2",
            },
        )
        self._prepare_request(request)

        response = director_config_pricing_edit(request, config_id=self.pricing.id)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("#builder-pricing"))
