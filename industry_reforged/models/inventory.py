"""
App Models
"""

# Third Party
from eveuniverse.models import EveType

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCorporationInfo


class CorpInventory(models.Model):
    corporation = models.ForeignKey(
        EveCorporationInfo, on_delete=models.CASCADE, related_name="inventory"
    )
    item_type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.BigIntegerField(default=0)

    location_id = models.BigIntegerField()

    manual_override = models.BooleanField(
        default=False, help_text="If true, ESI sync will not overwrite this quantity"
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Corp Inventory")
        verbose_name_plural = _("Corp Inventories")
        unique_together = (("corporation", "item_type", "location_id"),)

    def __str__(self):
        return f"{self.quantity}x {self.item_type.name} in {self.corporation.corporation_ticker}"
