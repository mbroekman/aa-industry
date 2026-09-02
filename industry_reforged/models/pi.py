# pylint: disable=attribute-defined-outside-init
"""
App Models
"""

# Standard Library
import datetime

# Third Party
from eveuniverse.models import EveType

# Django
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter


class UserPIConfig(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="industry_pi_config"
    )
    storage_warning_threshold = models.IntegerField(default=75)
    extraction_deficit_threshold_percent = models.IntegerField(
        default=100,
        help_text=_("Warn if extraction is below this percentage of consumption"),
    )

    class Meta:
        verbose_name = _("User PI Config")
        verbose_name_plural = _("User PI Configs")

    def __str__(self):
        return f"{self.user.username} PI Config"


class CharacterPlanet(models.Model):
    character = models.ForeignKey(
        EveCharacter, on_delete=models.CASCADE, related_name="planets"
    )
    planet_id = models.IntegerField()
    system_id = models.IntegerField()
    eve_system = models.ForeignKey(
        "eveuniverse.EveSolarSystem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    eve_planet = models.ForeignKey(
        "eveuniverse.EvePlanet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    planet_type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    upgrade_level = models.IntegerField(default=0)
    num_pins = models.IntegerField(default=0)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Character Planet")
        verbose_name_plural = _("Character Planets")
        unique_together = (("character", "planet_id"),)

    def __str__(self):
        return f"{self.character.character_name} - Planet {self.planet_id}"

    @property
    def has_expired_extractors(self):
        return any(pin.is_extractor and pin.is_expired for pin in self.pins.all())

    @property
    def has_full_storage(self):
        threshold = 75
        try:
            if hasattr(self.character.character_ownership.user, "industry_pi_config"):
                threshold = (
                    self.character.character_ownership.user.industry_pi_config.storage_warning_threshold
                )
        except Exception:
            pass
        return any(pin.utilization_pct >= threshold for pin in self.storage_pins)

    @property
    def factory_summary(self):
        factories = [pin for pin in self.pins.all() if pin.is_factory]
        summary = {}
        for f in factories:
            key = (f.type, f.product_type)
            if key not in summary:
                summary[key] = {
                    "type": f.type,
                    "product_type": f.product_type,
                    "count": 0,
                }
            summary[key]["count"] += 1
        return summary.values()

    @property
    def end_products(self):
        """Returns a list of EveType objects representing the highest tier products produced on this planet."""
        high_tech = self.high_tech_factories
        if high_tech:
            return list({f.product_type for f in high_tech if f.product_type})
        advanced = self.advanced_factories
        if advanced:
            return list({f.product_type for f in advanced if f.product_type})
        basic = self.basic_factories
        if basic:
            return list({f.product_type for f in basic if f.product_type})

        # Fallback to raw materials from extractors if this is an extraction-only planet
        extractors = self.extractors
        if extractors:
            return list({e.product_type for e in extractors if e.product_type})

        return []

    @property
    def extractors(self):
        return [p for p in self.pins.all() if p.is_extractor]

    @property
    def basic_factories(self):
        return [p for p in self.pins.all() if p.is_basic_factory]

    @property
    def advanced_factories(self):
        return [p for p in self.pins.all() if p.is_advanced_factory]

    @property
    def high_tech_factories(self):
        return [p for p in self.pins.all() if p.is_high_tech_factory]

    @property
    def storage_pins(self):
        return [p for p in self.pins.all() if p.is_storage_facility or p.is_launchpad]

    @property
    def command_centers(self):
        return [p for p in self.pins.all() if p.is_command_center]

    @property
    def schematic_cycle_times(self):
        if not hasattr(self, "_schematic_cycle_times"):
            # AA Industry App

            factory_schematics = [
                p.schematic_id
                for p in self.pins.all()
                if p.is_factory and p.schematic_id
            ]
            schematics = PISchematic.objects.filter(schematic_id__in=factory_schematics)
            self._schematic_cycle_times = {
                s.schematic_id: s.cycle_time for s in schematics
            }
        return self._schematic_cycle_times

    @property
    def grouped_factories(self):
        groups = {"basic": {}, "advanced": {}, "high_tech": {}}

        for p in self.pins.all():
            if not p.is_factory:
                continue

            group_key = None
            if p.is_basic_factory:
                group_key = "basic"
            elif p.is_advanced_factory:
                group_key = "advanced"
            elif p.is_high_tech_factory:
                group_key = "high_tech"

            if group_key:
                product_id = p.product_type.id if p.product_type else 0
                product_name = p.product_type.name if p.product_type else "No Schematic"

                # Format a nice string for cycle time, like "1h", "30m", etc.
                cycle_time_sec = self.schematic_cycle_times.get(p.schematic_id, 0)
                cycle_str = ""
                if cycle_time_sec > 0:
                    if cycle_time_sec >= 3600:
                        cycle_str = f"{int(cycle_time_sec / 3600)}h"
                    else:
                        cycle_str = f"{int(cycle_time_sec / 60)}m"

                key = (product_id, p.schematic_id)
                if key not in groups[group_key]:
                    groups[group_key][key] = {
                        "count": 1,
                        "product_type": p.product_type,
                        "product_name": product_name,
                        "cycle_time_sec": cycle_time_sec,
                        "cycle_str": cycle_str,
                        "status_label": p.status_label,
                        "is_idle": p.status_label == "Idle",
                    }
                else:
                    groups[group_key][key]["count"] += 1
                    # If any factory is idle, we might want to flag the group, but let's keep it simple
                    if p.status_label == "Idle":
                        groups[group_key][key]["is_idle"] = True
                        groups[group_key][key]["status_label"] = "Some Idle"

        return {
            "basic": list(groups["basic"].values()),
            "advanced": list(groups["advanced"].values()),
            "high_tech": list(groups["high_tech"].values()),
        }

    @property
    def earliest_extractor_expiry(self):
        extractors = self.extractors
        if not extractors:
            return None
        valid_expiries = [e.expiry_time for e in extractors if e.expiry_time]
        if not valid_expiries:
            return None
        return min(valid_expiries)

    @property
    def hourly_consumption_rates(self):
        if not hasattr(self, "_hourly_consumption_rates"):
            # AA Industry App

            factories = [p for p in self.pins.all() if p.is_factory and p.schematic_id]
            rates = {}
            for f in factories:
                try:
                    schematic = PISchematic.objects.get(schematic_id=f.schematic_id)
                    if schematic.cycle_time:
                        cycles_per_hour = 3600.0 / schematic.cycle_time
                        for inp in schematic.inputs.all():
                            rates[inp.type_id] = rates.get(inp.type_id, 0) + (
                                inp.quantity * cycles_per_hour
                            )
                except PISchematic.DoesNotExist:
                    continue
            self._hourly_consumption_rates = rates
        return self._hourly_consumption_rates

    @property
    def hourly_extraction_rates(self):
        # Django

        rates = {}
        for ext in self.extractors:
            if (
                ext.product_type_id
                and ext.expiry_time
                and ext.expiry_time > timezone.now()
            ):
                if (
                    getattr(ext, "cycle_time", 0) > 0
                    and getattr(ext, "extraction_yield", 0) > 0
                ):
                    rate = (3600.0 / ext.cycle_time) * ext.extraction_yield
                    rates[ext.product_type_id] = (
                        rates.get(ext.product_type_id, 0) + rate
                    )
        return rates

    @property
    def hourly_production_rates(self):
        if not hasattr(self, "_hourly_production_rates"):
            # AA Industry App

            factories = [p for p in self.pins.all() if p.is_factory and p.schematic_id]
            rates = {}
            for f in factories:
                try:
                    schematic = PISchematic.objects.get(schematic_id=f.schematic_id)
                    if schematic.cycle_time:
                        cycles_per_hour = 3600.0 / schematic.cycle_time
                        for out in schematic.outputs.all():
                            rates[out.type_id] = rates.get(out.type_id, 0) + (
                                out.quantity * cycles_per_hour
                            )
                except PISchematic.DoesNotExist:
                    continue
            self._hourly_production_rates = rates
        return self._hourly_production_rates

    @property
    def has_extraction_deficit(self):
        consumption = self.hourly_consumption_rates
        extraction = self.hourly_extraction_rates
        production = self.hourly_production_rates

        threshold_pct = 100
        try:
            if hasattr(self.character.character_ownership.user, "industry_pi_config"):
                threshold_pct = (
                    self.character.character_ownership.user.industry_pi_config.extraction_deficit_threshold_percent
                )
        except Exception:
            pass

        for type_id, cons_rate in consumption.items():
            supply = extraction.get(type_id, 0) + production.get(type_id, 0)
            if supply < (cons_rate * (threshold_pct / 100.0)):
                return True
        return False

    @property
    def deficit_graph_data(self):
        consumption = self.hourly_consumption_rates
        extraction = self.hourly_extraction_rates
        production = self.hourly_production_rates

        data = []
        for type_id, cons_rate in consumption.items():
            if cons_rate > 0:
                supply = extraction.get(type_id, 0) + production.get(type_id, 0)
                deficit = max(0, cons_rate - supply)
                extraction_pct = (
                    min(100.0, (supply / cons_rate) * 100.0) if cons_rate > 0 else 100.0
                )

                # Fetch EveType for name (caching handled by ORM if possible)
                # Third Party
                from eveuniverse.models import EveType

                try:
                    eve_type = EveType.objects.get(id=type_id)
                    name = eve_type.name
                except EveType.DoesNotExist:
                    name = f"Type {type_id}"

                data.append(
                    {
                        "type_id": type_id,
                        "name": name,
                        "consumption": cons_rate,
                        "extraction": supply,
                        "deficit": deficit,
                        "extraction_pct": extraction_pct,
                    }
                )
        return data

    @property
    def factory_depletion_time(self):
        factories = [p for p in self.pins.all() if p.is_factory and p.schematic_id]
        if not factories:
            return None

        # 1. Sum available quantity of all inputs in all storage pins
        consumption_per_hour = self.hourly_consumption_rates
        if not consumption_per_hour:
            return None

        available_qty = {t_id: 0 for t_id in consumption_per_hour}
        for p in self.storage_pins:
            for item_name, item_data in p.contents.items():
                t_id = item_data.get("type_id")
                if t_id in available_qty:
                    available_qty[t_id] += item_data.get("amount", 0)

        # 2. Use extraction_deficit_info to find actual deficits
        deficit_info = self.extraction_deficit_info
        if not deficit_info:
            return None

        min_hours_remaining = float("inf")
        for info in deficit_info:
            deficit = info["deficit"]
            if deficit > 0:
                t_id = info["type_id"]
                hours_left = available_qty.get(t_id, 0) / deficit
                min_hours_remaining = min(min_hours_remaining, hours_left)

        if min_hours_remaining == float("inf"):
            return None

        return self.last_update + datetime.timedelta(hours=min_hours_remaining)


class PlanetPin(models.Model):
    planet = models.ForeignKey(
        "CharacterPlanet", on_delete=models.CASCADE, related_name="pins"
    )
    pin_id = models.BigIntegerField()
    type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, related_name="+"
    )

    # For extractors
    install_time = models.DateTimeField(null=True, blank=True)
    expiry_time = models.DateTimeField(null=True, blank=True)
    cycle_time = models.IntegerField(null=True, blank=True)
    extraction_yield = models.FloatField(null=True, blank=True)
    product_type = models.ForeignKey(
        EveType, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    # For factories
    schematic_id = models.IntegerField(null=True, blank=True)
    last_cycle_start = models.DateTimeField(null=True, blank=True)

    # For storage & infrastructure
    contents_volume = models.FloatField(default=0.0)
    capacity = models.FloatField(default=0.0)
    contents = models.JSONField(default=dict, blank=True)

    # Notifications
    notification_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Planet Pin")
        verbose_name_plural = _("Planet Pins")
        unique_together = (("planet", "pin_id"),)

    def __str__(self):
        return f"Pin {self.pin_id} on {self.planet}"

    @property
    def categorized_contents(self):
        end_products = self.planet.end_products
        end_product_names = [p.name for p in end_products]

        produced = []
        resources = []

        # Calculate simulated production for the planet
        # Standard Library

        # Django

        now = timezone.now()

        simulated_amounts = {}
        # Only add simulation if this pin is a storage/launchpad
        if self.is_storage:
            depletion_time = self.planet.factory_depletion_time
            elapsed_seconds = (now - self.planet.last_update).total_seconds()

            if depletion_time and now > depletion_time:
                elapsed_seconds = (
                    depletion_time - self.planet.last_update
                ).total_seconds()

            if elapsed_seconds > 0:
                for f in self.planet.pins.all():
                    if f.is_factory and f.schematic_id:
                        try:
                            # AA Industry App

                            schematic = PISchematic.objects.get(
                                schematic_id=f.schematic_id
                            )
                            if schematic.cycle_time:
                                cycles = int(elapsed_seconds / schematic.cycle_time)
                                if cycles > 0:
                                    for out in schematic.outputs.all():
                                        if out.type_id not in simulated_amounts:
                                            simulated_amounts[out.type_id] = 0
                                        storage_pins = self.planet.storage_pins
                                        best_pin = None
                                        for sp in storage_pins:
                                            if sp.is_launchpad:
                                                best_pin = sp
                                                break
                                        if not best_pin and storage_pins:
                                            best_pin = storage_pins[0]

                                        if best_pin and self.pin_id == best_pin.pin_id:
                                            simulated_amounts[out.type_id] += (
                                                out.quantity * cycles
                                            )
                        except PISchematic.DoesNotExist:
                            continue

        for ep in end_products:
            amount = 0
            vol = 0
            if self.contents and ep.name in self.contents:
                amount = self.contents[ep.name].get("amount", 0)
                vol = self.contents[ep.name].get("volume", 0)

            # Add simulated amount
            sim_added = int(simulated_amounts.get(ep.id, 0))
            amount += sim_added

            if amount > 0:
                produced.append(
                    {
                        "name": ep.name,
                        "type_id": ep.id,
                        "amount": amount,
                        "volume": vol + (sim_added * float(ep.volume or 0)),
                    }
                )

        if self.contents:
            for name, item in self.contents.items():
                if name not in end_product_names:
                    # Subtract simulated consumption? Let's just focus on production for now as requested.
                    amount = item.get("amount", 0)
                    resources.append(
                        {
                            "name": name,
                            "type_id": item.get("type_id"),
                            "amount": amount,
                            "volume": item.get("volume", 0),
                        }
                    )

        return {"produced": produced, "resources": resources}

    @property
    def utilization_pct(self):
        if self.capacity and self.capacity > 0:
            return min(100.0, (self.contents_volume / self.capacity) * 100.0)
        return 0.0

    @property
    def is_extractor(self):
        return self.type and "Extractor" in self.type.name

    @property
    def extraction_deficit_info(self):
        if not self.is_extractor or not self.product_type_id:
            return None

        consumption = self.planet.hourly_consumption_rates.get(self.product_type_id, 0)
        if consumption == 0:
            return None

        extraction = self.planet.hourly_extraction_rates.get(self.product_type_id, 0)
        production = self.planet.hourly_production_rates.get(self.product_type_id, 0)
        supply = extraction + production

        threshold_pct = 100
        try:
            if hasattr(
                self.planet.character.character_ownership.user, "industry_pi_config"
            ):
                threshold_pct = (
                    self.planet.character.character_ownership.user.industry_pi_config.extraction_deficit_threshold_percent
                )
        except Exception:
            pass

        if supply < (consumption * (threshold_pct / 100.0)):
            return {
                "deficit_per_hour": consumption - supply,
                "consumption_per_hour": consumption,
                "extraction_per_hour": supply,
            }
        return None

    @property
    def is_factory(self):
        return (
            self.type
            and ("Facility" in self.type.name or "Plant" in self.type.name)
            and "Storage" not in self.type.name
        )

    @property
    def is_basic_factory(self):
        return self.type and "Basic Industry Facility" in self.type.name

    @property
    def is_advanced_factory(self):
        return self.type and "Advanced Industry Facility" in self.type.name

    @property
    def is_high_tech_factory(self):
        return self.type and "High Tech Production Plant" in self.type.name

    @property
    def is_launchpad(self):
        return self.type and "Launchpad" in self.type.name

    @property
    def is_storage_facility(self):
        return self.type and "Storage Facility" in self.type.name

    @property
    def is_command_center(self):
        return self.type and "Command Center" in self.type.name

    @property
    def is_storage(self):
        return self.is_launchpad or self.is_storage_facility or self.is_command_center

    @property
    def status_label(self):
        if self.is_extractor:
            return "Expired" if self.is_expired else "Running"
        if self.is_factory:
            if self.schematic_id:
                return "Configured"
            return "Idle"
        return "Online"

    @property
    def progress_percent(self):
        if not self.install_time or not self.expiry_time:
            return 0
        # Django

        now = timezone.now()
        if now >= self.expiry_time:
            return 100
        if now <= self.install_time:
            return 0
        total_duration = (self.expiry_time - self.install_time).total_seconds()
        elapsed = (now - self.install_time).total_seconds()
        if total_duration <= 0:
            return 100
        return int((elapsed / total_duration) * 100)

    @property
    def is_expired(self):
        if not self.expiry_time:
            return False
        # Django

        return timezone.now() >= self.expiry_time


class PISchematic(models.Model):
    schematic_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    cycle_time = models.IntegerField(help_text=_("Cycle time in seconds"))

    class Meta:
        verbose_name = _("PI Schematic")
        verbose_name_plural = _("PI Schematics")

    def __str__(self):
        return self.name


class PISchematicInput(models.Model):
    schematic = models.ForeignKey(
        PISchematic, on_delete=models.CASCADE, related_name="inputs"
    )
    type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.IntegerField()


class PISchematicOutput(models.Model):
    schematic = models.ForeignKey(
        PISchematic, on_delete=models.CASCADE, related_name="outputs"
    )
    type = models.ForeignKey(EveType, on_delete=models.CASCADE, related_name="+")
    quantity = models.IntegerField()
