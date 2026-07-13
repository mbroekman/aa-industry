# Django
from django.core.management.base import BaseCommand

# AA Industry App
from industry_reforged.models import IndustryRig


class Command(BaseCommand):
    help = "Seeds common Industry Rigs into the database for testing and usage."

    def handle(self, *args, **options):
        rigs = [
            {
                "type_id": 37473,
                "name": "Standup M-Set Equipment Manufacturing Material Efficiency I",
                "me_bonus": 2.0,
                "te_bonus": 20.0,
                "applies_to_categories": "65",  # Structure modules
            },
            {
                "type_id": 37474,
                "name": "Standup M-Set Equipment Manufacturing Material Efficiency II",
                "me_bonus": 2.4,
                "te_bonus": 24.0,
                "applies_to_categories": "65",
            },
            {
                "type_id": 37172,
                "name": "Standup L-Set Ship Manufacturing Material Efficiency I",
                "me_bonus": 2.0,
                "te_bonus": 20.0,
                "applies_to_categories": "6",  # Ships
            },
            {
                "type_id": 37173,
                "name": "Standup L-Set Ship Manufacturing Material Efficiency II",
                "me_bonus": 2.4,
                "te_bonus": 24.0,
                "applies_to_categories": "6",
            },
            {
                "type_id": 37180,
                "name": "Standup L-Set Equipment Manufacturing Material Efficiency I",
                "me_bonus": 2.0,
                "te_bonus": 20.0,
                "applies_to_categories": "65",
            },
            {
                "type_id": 37181,
                "name": "Standup L-Set Equipment Manufacturing Material Efficiency II",
                "me_bonus": 2.4,
                "te_bonus": 24.0,
                "applies_to_categories": "65",
            },
            {
                "type_id": 37260,
                "name": "Standup XL-Set Ship Manufacturing Material Efficiency I",
                "me_bonus": 2.0,
                "te_bonus": 20.0,
                "applies_to_categories": "6",
            },
            {
                "type_id": 37261,
                "name": "Standup XL-Set Ship Manufacturing Material Efficiency II",
                "me_bonus": 2.4,
                "te_bonus": 24.0,
                "applies_to_categories": "6",
            },
        ]

        count = 0
        for rig_data in rigs:
            rig, created = IndustryRig.objects.update_or_create(
                type_id=rig_data["type_id"],
                defaults={
                    "name": rig_data["name"],
                    "me_bonus": rig_data["me_bonus"],
                    "te_bonus": rig_data["te_bonus"],
                    "applies_to_categories": rig_data.get("applies_to_categories", ""),
                    "applies_to_groups": rig_data.get("applies_to_groups", ""),
                },
            )
            if created:
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {count} new Industry Rigs.")
        )
