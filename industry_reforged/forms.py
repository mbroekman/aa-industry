# Third Party
import requests
from eveuniverse.models import EveType

# Django
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from .models import (
    Basket,
    BasketItem,
    CorpItemConfig,
    CorporationPricingConfig,
    CorpPricingConfig,
    CorpTypeDiscount,
    IndustryFacility,
    IndustryFacilityRig,
    IndustryRig,
    TaxConfig,
    UserPIConfig,
)


def resolve_eve_type(item_name: str) -> EveType:
    """Helper to resolve an item name to an EveType."""
    if not item_name:
        raise ValidationError(_("Item name cannot be empty."))

    item_name = item_name.strip()

    # 1. Check local DB (case-insensitive)
    eve_type = EveType.objects.filter(name__iexact=item_name).first()
    if eve_type:
        return eve_type

    # 2. Try ESI
    try:
        res = requests.post(
            "https://esi.evetech.net/latest/universe/ids/",
            json=[item_name],
            timeout=5,
        )
        if res.status_code == 200:
            data = res.json()
            if "inventory_types" in data and len(data["inventory_types"]) > 0:
                type_id = data["inventory_types"][0]["id"]
                eve_type, created = EveType.objects.get_or_create_esi(id=type_id)
                return eve_type
    except Exception:
        pass

    raise ValidationError(
        _("Could not resolve '%(name)s' to a valid EVE item."),
        params={"name": item_name},
    )


class CorpItemConfigForm(forms.ModelForm):
    item_name = forms.CharField(
        max_length=100,
        help_text=_("Exact name of the item (e.g. Aeon)"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Tritanium"}
        ),
    )

    class Meta:
        model = CorpItemConfig
        fields = [
            "corporation",
            "item_name",
            "manual_me",
            "manual_te",
            "max_runs",
            "manual_price",
            "target_threshold",
            "auto_produce",
            "build_or_buy",
            "exclude_from_orders",
            "exclude_warning_message",
        ]
        widgets = {
            "corporation": forms.Select(attrs={"class": "form-select"}),
            "manual_me": forms.NumberInput(attrs={"class": "form-control"}),
            "manual_te": forms.NumberInput(attrs={"class": "form-control"}),
            "max_runs": forms.NumberInput(attrs={"class": "form-control"}),
            "manual_price": forms.NumberInput(attrs={"class": "form-control"}),
            "target_threshold": forms.NumberInput(attrs={"class": "form-control"}),
            "auto_produce": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "build_or_buy": forms.Select(attrs={"class": "form-select"}),
            "exclude_from_orders": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "exclude_warning_message": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "E.g. Get deadspace items yourself",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["corporation"].disabled = True
            if self.instance.item_type:
                self.fields["item_name"].initial = self.instance.item_type.name

    def clean(self):
        cleaned_data = super().clean()
        item_name = cleaned_data.get("item_name")
        if item_name:
            eve_type = resolve_eve_type(item_name)

            corp = cleaned_data.get("corporation")
            if not corp:
                return cleaned_data

            qs = CorpItemConfig.objects.filter(corporation=corp, item_type=eve_type)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "item_name", _("A configuration for this item already exists.")
                )

            self.instance.item_type = eve_type
        return cleaned_data


class CorpPricingConfigForm(forms.ModelForm):
    class Meta:
        model = CorpPricingConfig
        fields = [
            "corporation",
            "default_discount_percent",
            "builder_reward_percent",
            "default_t1_me",
            "default_t2_me",
        ]
        widgets = {
            "corporation": forms.Select(attrs={"class": "form-select"}),
            "default_discount_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
            "builder_reward_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
            "default_t1_me": forms.NumberInput(
                attrs={"class": "form-control", "step": "1", "min": "0", "max": "10"}
            ),
            "default_t2_me": forms.NumberInput(
                attrs={"class": "form-control", "step": "1", "min": "0", "max": "10"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["corporation"].disabled = True


class TaxConfigForm(forms.ModelForm):
    class Meta:
        model = TaxConfig
        fields = ["corporation", "industry_tax_rate", "broker_fee_rate"]
        widgets = {
            "corporation": forms.Select(attrs={"class": "form-select"}),
            "industry_tax_rate": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
            "broker_fee_rate": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["corporation"].disabled = True


class CorpTypeDiscountForm(forms.ModelForm):
    item_name = forms.CharField(
        max_length=100,
        help_text=_("Exact name of the item to discount (e.g. Paladin)"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Paladin"}
        ),
    )

    class Meta:
        model = CorpTypeDiscount
        fields = ["config", "item_name", "discount_percent"]
        widgets = {
            "config": forms.Select(attrs={"class": "form-select"}),
            "discount_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Display the corporation name for the config instead of "CorpPricingConfig object"
        self.fields["config"].label_from_instance = (
            lambda obj: obj.corporation.corporation_name
        )
        if self.instance and self.instance.pk:
            self.fields["config"].disabled = True
            if self.instance.eve_type:
                self.fields["item_name"].initial = self.instance.eve_type.name

    def clean(self):
        cleaned_data = super().clean()
        item_name = cleaned_data.get("item_name")
        if item_name:
            eve_type = resolve_eve_type(item_name)

            qs = CorpTypeDiscount.objects.filter(
                config=self.instance.config, eve_type=eve_type
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "item_name", _("A discount rule for this item already exists.")
                )

            self.instance.eve_type = eve_type
        return cleaned_data


class IndustryFacilityForm(forms.ModelForm):
    FACILITY_TYPE_CHOICES = [
        ("", "Select a facility type..."),
        (35825, "Raitaru"),
        (35826, "Azbel"),
        (35827, "Sotiyo"),
        (35832, "Athanor"),
        (35833, "Fortizar"),
        (35835, "Astrahus"),
        (35836, "Tatara"),
        (35834, "Keepstar"),
    ]

    type_id = forms.ChoiceField(
        choices=FACILITY_TYPE_CHOICES,
        required=True,
        help_text=_("The type of Upwell structure"),
    )

    class Meta:
        model = IndustryFacility
        fields = ["facility_id", "name", "type_id", "solar_system_id", "is_default"]
        help_texts = {
            "facility_id": _("The exact EVE Structure ID. Type manually."),
            "name": _("A friendly name for this facility."),
            "solar_system_id": _("Optional: EVE Solar System ID"),
        }

    def clean_type_id(self):
        return int(self.cleaned_data["type_id"])

    def clean(self):
        cleaned_data = super().clean()
        solar_system_id = cleaned_data.get("solar_system_id")
        if solar_system_id:
            # Third Party
            import requests

            try:
                resp = requests.get(
                    f"https://esi.evetech.net/latest/universe/systems/{solar_system_id}/?datasource=tranquility",
                    timeout=5,
                )
                if resp.status_code == 200:
                    sec = resp.json().get("security_status", 1.0)
                    if sec >= 0.45:
                        self.instance.security_space = "HIGHSEC"
                        cleaned_data["security_space"] = "HIGHSEC"
                    elif sec > 0.0:
                        self.instance.security_space = "LOWSEC"
                        cleaned_data["security_space"] = "LOWSEC"
                    else:
                        self.instance.security_space = "NULLSEC_WH"
                        cleaned_data["security_space"] = "NULLSEC_WH"
            except Exception:
                pass

        self.instance.is_production_facility = True
        return cleaned_data


class IndustryFacilityRigForm(forms.ModelForm):
    class Meta:
        model = IndustryFacilityRig
        fields = ["rig"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rig"].queryset = IndustryRig.objects.all().order_by("name")


IndustryFacilityRigFormSet = inlineformset_factory(
    IndustryFacility,
    IndustryFacilityRig,
    form=IndustryFacilityRigForm,
    extra=1,
    can_delete=True,
)


class UserPIConfigForm(forms.ModelForm):
    class Meta:
        model = UserPIConfig
        fields = ["storage_warning_threshold", "extraction_deficit_threshold_percent"]
        widgets = {
            "storage_warning_threshold": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "1",
                    "min": "1",
                    "max": "100",
                }
            ),
            "extraction_deficit_threshold_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "1",
                    "min": "0",
                    "max": "1000",
                }
            ),
        }
        labels = {
            "storage_warning_threshold": _("Storage Warning Threshold (%)"),
            "extraction_deficit_threshold_percent": _("Deficit Warning Threshold (%)"),
        }


class CorporationPricingConfigForm(forms.ModelForm):
    class Meta:
        model = CorporationPricingConfig
        fields = [
            "corporation",
            "material_valuation_method",
            "minimum_margin_floor",
        ]
        widgets = {
            "corporation": forms.Select(attrs={"class": "form-select"}),
            "material_valuation_method": forms.Select(attrs={"class": "form-select"}),
            "minimum_margin_floor": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["corporation"].disabled = True


def get_target_hub_choices(user_corps=None, current_target_hub=None):
    """
    Populates target_hub_id choices for BasketForm and OpportunityScannerForm.
    Combines configured IndustryFacility records and KnownLocation records.
    """
    # Django
    from django.db.models import Q

    # Alliance Auth
    from allianceauth.eveonline.models import EveCorporationInfo

    from .models.facilities import IndustryFacility, KnownLocation

    choices = [("", "---------")]
    hub_map = {}

    # 1. Fetch configured IndustryFacility records
    facility_qs = IndustryFacility.objects.all()
    if user_corps is not None and user_corps.exists():
        corp_ids = list(user_corps.values_list("corporation_id", flat=True))
        alliance_ids = list(
            user_corps.exclude(alliance__isnull=True).values_list(
                "alliance__alliance_id", flat=True
            )
        )
        alliance_corp_ids = []
        if alliance_ids:
            alliance_corp_ids = list(
                EveCorporationInfo.objects.filter(
                    alliance__alliance_id__in=alliance_ids
                ).values_list("corporation_id", flat=True)
            )

        allowed_owners = set(corp_ids + alliance_corp_ids)
        filtered_qs = facility_qs.filter(
            Q(owner_id__in=allowed_owners)
            | Q(owner_id__isnull=True)
            | Q(owner_id__lt=100000000)  # NPC stations / corporations
            | Q(is_production_facility=True)
        )
        if filtered_qs.exists():
            facility_qs = filtered_qs

    for fac in facility_qs:
        name = fac.name if fac.name else f"Facility ({fac.facility_id})"
        hub_map[fac.facility_id] = name

    # 2. Fetch KnownLocation records (asset locations)
    if user_corps is not None and user_corps.exists():
        loc_qs = KnownLocation.objects.filter(corporations__in=user_corps).distinct()
    else:
        loc_qs = KnownLocation.objects.all()

    for loc in loc_qs:
        if loc.location_id not in hub_map:
            name = (
                loc.name
                if loc.name
                else f"Unknown Structure/Station ({loc.location_id})"
            )
            hub_map[loc.location_id] = name

    # 3. Ensure current_target_hub is present if passed
    if current_target_hub:
        fac_id = getattr(current_target_hub, "facility_id", None) or getattr(
            current_target_hub, "pk", None
        )
        if fac_id and fac_id not in hub_map:
            name = (
                current_target_hub.name
                if getattr(current_target_hub, "name", None)
                else f"Unknown ({fac_id})"
            )
            hub_map[fac_id] = name

    sorted_hubs = sorted(hub_map.items(), key=lambda x: str(x[1]).lower())
    for fac_id, name in sorted_hubs:
        choices.append((fac_id, name))

    return choices


class BasketForm(forms.ModelForm):
    target_hub_id = forms.ChoiceField(
        required=False,
        label=_("Target Hub (Structure ID)"),
        help_text=_("Select a structure where your corporation has assets"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Basket
        fields = [
            "name",
            "corporation",
            "is_active",
            "target_region_id",
            "min_profit_margin",
            "run_interval_hours",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "corporation": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "target_region_id": forms.NumberInput(attrs={"class": "form-control"}),
            "min_profit_margin": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
            "run_interval_hours": forms.NumberInput(
                attrs={"class": "form-control", "min": "1"}
            ),
        }

    def __init__(self, *args, **kwargs):
        user_corps = kwargs.pop("user_corps", None)
        super().__init__(*args, **kwargs)
        if user_corps is not None:
            self.fields["corporation"].queryset = user_corps

        self.fields["target_hub_id"].choices = get_target_hub_choices(
            user_corps=user_corps,
            current_target_hub=getattr(self.instance, "target_hub", None),
        )

        if self.instance and self.instance.pk and self.instance.target_hub_id:
            self.fields["target_hub_id"].initial = self.instance.target_hub_id

    def clean(self):
        cleaned_data = super().clean()
        target_hub_id = cleaned_data.get("target_hub_id")

        if target_hub_id:
            try:
                target_hub_id = int(target_hub_id)
            except (ValueError, TypeError):
                target_hub_id = None

        if target_hub_id:
            # Third Party
            import requests

            from .models.facilities import IndustryFacility

            facility = IndustryFacility.objects.filter(
                facility_id=target_hub_id
            ).first()
            if not facility:
                # Try to fetch from ESI or KnownLocations
                name = f"Unknown Facility ({target_hub_id})"

                from .models.facilities import KnownLocation

                known_loc = KnownLocation.objects.filter(
                    location_id=target_hub_id
                ).first()
                if known_loc and known_loc.name:
                    name = known_loc.name

                type_id = None
                solar_system_id = None

                if target_hub_id < 100000000:
                    # It's a station
                    try:
                        resp = requests.get(
                            f"https://esi.evetech.net/latest/universe/stations/{target_hub_id}/?datasource=tranquility",
                            timeout=5,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            name = data.get("name", name)
                            type_id = data.get("type_id")
                            solar_system_id = data.get("system_id")
                    except Exception:
                        pass
                else:
                    # It's a structure
                    try:
                        resp = requests.get(
                            f"https://esi.evetech.net/latest/universe/structures/{target_hub_id}/?datasource=tranquility",
                            timeout=5,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            name = data.get("name", name)
                            type_id = data.get("type_id")
                            solar_system_id = data.get("solar_system_id")
                    except Exception:
                        pass

                facility = IndustryFacility.objects.create(
                    facility_id=target_hub_id,
                    name=name,
                    type_id=type_id,
                    solar_system_id=solar_system_id,
                )

            self.instance.target_hub = facility
        else:
            self.instance.target_hub = None

        return cleaned_data


class BasketItemForm(forms.ModelForm):
    item_name = forms.CharField(
        max_length=100,
        help_text=_("Exact name of the item (e.g. Tritanium)"),
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Tritanium"}
        ),
        required=True,
    )

    class Meta:
        model = BasketItem
        fields = ["eve_type", "item_name", "target_stock_level", "batch_size"]
        widgets = {
            "eve_type": forms.HiddenInput(),
            "target_stock_level": forms.NumberInput(attrs={"class": "form-control"}),
            "batch_size": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If we already have an eve_type, populate the item_name field
        if self.instance and self.instance.pk and self.instance.eve_type_id:
            self.initial["item_name"] = self.instance.eve_type.name

        # eve_type is hidden, it will be resolved from item_name in clean()
        self.fields["eve_type"].required = False

    def clean(self):
        cleaned_data = super().clean()
        item_name = cleaned_data.get("item_name")
        if item_name and not cleaned_data.get("DELETE"):
            try:
                eve_type = resolve_eve_type(item_name)
                cleaned_data["eve_type"] = eve_type
            except ValidationError as e:
                self.add_error("item_name", e)
        return cleaned_data


BasketItemFormSet = inlineformset_factory(
    Basket,
    BasketItem,
    form=BasketItemForm,
    extra=1,
    can_delete=True,
)


class OpportunityScannerForm(forms.ModelForm):
    COMMON_REGIONS = [
        ("", "---------"),
        (10000002, "The Forge (Jita)"),
        (10000043, "Domain (Amarr)"),
        (10000032, "Sinq Laison (Dodixie)"),
        (10000030, "Heimatar (Rens)"),
        (10000042, "Metropolis (Hek)"),
        (10000060, "Delve"),
    ]

    CATEGORY_CHOICES = [
        (6, "Ships"),
        (7, "Modules"),
        (8, "Charges"),
        (18, "Drones"),
        (22, "Deployables"),
        (66, "Rigs"),
        (87, "Fighters"),
        (32, "Subsystems"),
        (20, "Implants"),
        (16, "Skills"),
        (43, "Missions"),
        (17, "Commodities"),
    ]

    region_id = forms.ChoiceField(
        required=False,
        choices=COMMON_REGIONS,
        label=_("Target Region"),
        help_text=_("Select a region if you want to scan a specific region's market."),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    target_hub_id = forms.ChoiceField(
        required=False,
        label=_("Target Hub (Structure ID)"),
        help_text=_("Select a structure where your corporation has assets"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    categories = forms.MultipleChoiceField(
        choices=CATEGORY_CHOICES,
        required=True,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "8"}),
        help_text=_("Hold Ctrl (Windows) or Cmd (Mac) to select multiple categories."),
    )

    class Meta:
        from .models.ai_manager import OpportunityScanner

        model = OpportunityScanner
        fields = [
            "name",
            "corporation",
            "is_active",
            "min_profit_margin",
            "min_velocity",
            "auto_add_basket",
            "target_stock_days",
            "run_interval_hours",
            "scan_missing_blueprints",
        ]
        widgets = {
            "scan_missing_blueprints": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "run_interval_hours": forms.NumberInput(
                attrs={"class": "form-control", "min": "1"}
            ),
            "auto_add_basket": forms.Select(attrs={"class": "form-select"}),
            "target_stock_days": forms.NumberInput(
                attrs={"class": "form-control", "min": "1"}
            ),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "corporation": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "min_profit_margin": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
            "min_velocity": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
        }

    def __init__(self, *args, **kwargs):
        user_corps = kwargs.pop("user_corps", None)
        super().__init__(*args, **kwargs)
        if user_corps is not None:
            self.fields["corporation"].queryset = user_corps

            # Filter auto_add_basket
            from .models.ai_manager import Basket

            self.fields["auto_add_basket"].queryset = Basket.objects.filter(
                corporation__in=user_corps
            )

        self.fields["target_hub_id"].choices = get_target_hub_choices(
            user_corps=user_corps,
            current_target_hub=getattr(self.instance, "target_hub", None),
        )

        if self.instance and self.instance.pk:
            if self.instance.target_hub_id:
                self.fields["target_hub_id"].initial = self.instance.target_hub_id
            if self.instance.target_region_id:
                self.fields["region_id"].initial = self.instance.target_region_id
            if self.instance.categories:
                self.fields["categories"].initial = self.instance.categories

    def clean(self):
        cleaned_data = super().clean()

        region_id = cleaned_data.get("region_id")
        target_hub_id = cleaned_data.get("target_hub_id")

        if not region_id and not target_hub_id:
            raise ValidationError(
                _("You must select either a Target Region or a Target Hub.")
            )

        if region_id:
            try:
                region_id = int(region_id)
            except (ValueError, TypeError):
                self.add_error("region_id", _("Invalid region ID."))

        if target_hub_id:
            try:
                target_hub_id = int(target_hub_id)
            except (ValueError, TypeError):
                target_hub_id = None

        if target_hub_id:
            # Third Party
            import requests

            from .models.facilities import IndustryFacility

            facility = IndustryFacility.objects.filter(
                facility_id=target_hub_id
            ).first()
            if not facility:
                name = f"Unknown Facility ({target_hub_id})"
                from .models.facilities import KnownLocation

                known_loc = KnownLocation.objects.filter(
                    location_id=target_hub_id
                ).first()
                if known_loc and known_loc.name:
                    name = known_loc.name

                type_id = None
                solar_system_id = None
                if target_hub_id < 100000000:
                    try:
                        resp = requests.get(
                            f"https://esi.evetech.net/latest/universe/stations/{target_hub_id}/?datasource=tranquility",
                            timeout=5,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            name = data.get("name", name)
                            type_id = data.get("type_id")
                            solar_system_id = data.get("system_id")
                    except Exception:
                        pass

                corporation = cleaned_data.get("corporation")
                facility = IndustryFacility.objects.create(
                    facility_id=target_hub_id,
                    name=name,
                    corporation=corporation,
                    type_id=type_id,
                    solar_system_id=solar_system_id,
                )

            cleaned_data["target_hub_id"] = target_hub_id
            self.instance.target_hub = facility
        else:
            self.instance.target_hub = None

        if region_id:
            self.instance.target_region_id = region_id
        else:
            self.instance.target_region_id = None

        categories = cleaned_data.get("categories")
        if categories:
            self.instance.categories = [int(c) for c in categories]

        return cleaned_data
