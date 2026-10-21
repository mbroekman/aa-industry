"""
Unit tests for Hybrid Builder Reward Model 2 (TASK-249).
"""

# Standard Library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo

# Django
from django.test import TestCase

# AA Industry App
from industry_reforged.forms import CorpPricingConfigForm
from industry_reforged.models import CorpPricingConfig
from industry_reforged.templatetags.industry_tags import format_duration
from industry_reforged.utils.pricing_engine import (
    calculate_task_builder_reward,
    get_item_production_details,
)


class TestHybridBuilderRewards(TestCase):
    def setUp(self):
        self.corp = EveCorporationInfo.objects.create(
            corporation_id=98765432,
            corporation_name="Test Industrial Corp",
            corporation_ticker="TIC",
        )
        self.config = CorpPricingConfig.objects.create(
            corporation=self.corp,
            builder_base_fee=Decimal("1000000.00"),
            builder_hourly_rate=Decimal("750000.00"),
            builder_reward_percent=0.5,
            builder_min_reward=Decimal("2500000.00"),
            builder_max_reward=Decimal("75000000.00"),
            builder_urgent_multiplier=1.5,
            builder_high_multiplier=1.25,
            builder_low_multiplier=0.8,
        )

    def test_format_duration_templatetag(self):
        self.assertEqual(format_duration(600), "10m")
        self.assertEqual(format_duration(3600), "1h")
        self.assertEqual(format_duration(12000), "3h 20m")
        self.assertEqual(format_duration(90000), "1d 1h")
        self.assertEqual(format_duration(9000000), "104d 4h")
        self.assertEqual(format_duration(0), "")
        self.assertEqual(format_duration(None), "")
        self.assertEqual(format_duration("invalid"), "")

    def test_get_item_production_details_fallback(self):
        dur, portion = get_item_production_details(99999999, activity_id=1)
        self.assertEqual(dur, 0)
        self.assertEqual(portion, 1)

    @patch("industry_reforged.utils.pricing_engine.get_item_production_details")
    def test_calculate_task_builder_reward_standard(self, mock_details):
        # 4 hours base duration, 1 portion_size, 1 unit
        # TE 0.75 -> 4h * 0.75 = 3 hours
        mock_details.return_value = (14400, 1)

        fake_eve_type = MagicMock()
        fake_eve_type.id = 624  # Caracal

        reward, est_sec = calculate_task_builder_reward(
            eve_type=fake_eve_type,
            quantity=1,
            activity_id=1,
            priority="NORMAL",
            pricing_config=self.config,
            line_total_value=15000000.0,  # 15M ISK
        )

        # Expected:
        # Duration: 14400 * 1 * 0.75 = 10800s = 3.0h
        # Base fee: 1.0M
        # Slot cost: 3.0 * 750k = 2.25M
        # Value incentive: 15M * 0.5% = 75k
        # Raw: 1.0M + 2.25M + 75k = 3.325M ISK
        # Within bounds [2.5M, 75M] -> 3,325,000.00 ISK
        self.assertEqual(est_sec, 10800)
        self.assertEqual(reward, Decimal("3325000.00"))

    @patch("industry_reforged.utils.pricing_engine.get_item_production_details")
    def test_calculate_task_builder_reward_minimum_floor(self, mock_details):
        # Very short duration (10 min = 600s), portion size 100, 100 units (1 run)
        mock_details.return_value = (600, 100)

        fake_eve_type = MagicMock()
        fake_eve_type.id = 219  # Antimatter Charge M

        reward, _est_sec = calculate_task_builder_reward(
            eve_type=fake_eve_type,
            quantity=100,
            activity_id=1,
            priority="NORMAL",
            pricing_config=self.config,
            line_total_value=50000.0,  # 50k ISK
        )

        # Raw would be: 1M base + ~0.09h * 750k (~70k) + 250 ISK = ~1.07M ISK
        # Clamped to minimum floor: 2,500,000.00 ISK
        self.assertEqual(reward, Decimal("2500000.00"))

    @patch("industry_reforged.utils.pricing_engine.get_item_production_details")
    def test_calculate_task_builder_reward_maximum_cap(self, mock_details):
        # Massive job: Erebus (9,000,000s = 2500h base), value 95B ISK
        mock_details.return_value = (9000000, 1)

        fake_eve_type = MagicMock()
        fake_eve_type.id = 670  # Erebus

        reward, _est_sec = calculate_task_builder_reward(
            eve_type=fake_eve_type,
            quantity=1,
            activity_id=1,
            priority="NORMAL",
            pricing_config=self.config,
            line_total_value=95000000000.0,  # 95 Billion ISK
        )

        # Uncapped raw would be > 1.8 Billion ISK
        # Clamped to maximum cap: 75,000,000.00 ISK
        self.assertEqual(reward, Decimal("75000000.00"))

    @patch("industry_reforged.utils.pricing_engine.get_item_production_details")
    def test_calculate_task_builder_reward_priority_multipliers(self, mock_details):
        # Standard job clamped to minimum floor (2.5M)
        mock_details.return_value = (600, 100)
        fake_eve_type = MagicMock(id=219)

        # Normal: 2.5M
        normal_rew, _ = calculate_task_builder_reward(
            fake_eve_type, 100, 1, "NORMAL", self.config, 50000.0
        )
        self.assertEqual(normal_rew, Decimal("2500000.00"))

        # Urgent (1.5x): 2.5M * 1.5 = 3.75M
        urgent_rew, _ = calculate_task_builder_reward(
            fake_eve_type, 100, 1, "URGENT", self.config, 50000.0
        )
        self.assertEqual(urgent_rew, Decimal("3750000.00"))

        # High (1.25x): 2.5M * 1.25 = 3.125M
        high_rew, _ = calculate_task_builder_reward(
            fake_eve_type, 100, 1, "HIGH", self.config, 50000.0
        )
        self.assertEqual(high_rew, Decimal("3125000.00"))

        # Low (0.8x): 2.5M * 0.8 = 2.0M
        low_rew, _ = calculate_task_builder_reward(
            fake_eve_type, 100, 1, "LOW", self.config, 50000.0
        )
        self.assertEqual(low_rew, Decimal("2000000.00"))

    def test_corp_pricing_config_form_validation(self):
        # Invalid: min_reward > max_reward
        form_data = {
            "corporation": self.corp.id,
            "default_discount_percent": 5.0,
            "builder_base_fee": 1000000.0,
            "builder_hourly_rate": 750000.0,
            "builder_reward_percent": 0.5,
            "builder_min_reward": 80000000.0,  # 80M > 50M
            "builder_max_reward": 50000000.0,
            "builder_urgent_multiplier": 1.5,
            "builder_high_multiplier": 1.25,
            "builder_low_multiplier": 0.8,
            "default_t1_me": 10,
            "default_t2_me": 2,
        }
        form = CorpPricingConfigForm(data=form_data, instance=self.config)
        self.assertFalse(form.is_valid())
        self.assertIn("builder_min_reward", form.errors)

        # Valid: min_reward <= max_reward
        form_data["builder_min_reward"] = 2500000.0
        form = CorpPricingConfigForm(data=form_data, instance=self.config)
        self.assertTrue(form.is_valid())
