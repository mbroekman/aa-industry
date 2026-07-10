# Third Party
import requests
from eveuniverse.models import EveType

# Django
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from .models import (
    CorpItemConfig,
    CorpPricingConfig,
    CorpTypeDiscount,
    IndustryFacility,
    IndustryFacilityRig,
    IndustryRig,
    TaxConfig,
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
            "item_name",
            "manual_me",
            "manual_te",
            "manual_price",
            "target_threshold",
            "auto_produce",
            "build_or_buy",
            "bom_source",
            "exclude_from_orders",
            "exclude_warning_message",
        ]
        widgets = {
            "manual_me": forms.NumberInput(attrs={"class": "form-control"}),
            "manual_te": forms.NumberInput(attrs={"class": "form-control"}),
            "manual_price": forms.NumberInput(attrs={"class": "form-control"}),
            "target_threshold": forms.NumberInput(attrs={"class": "form-control"}),
            "auto_produce": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "build_or_buy": forms.Select(attrs={"class": "form-select"}),
            "bom_source": forms.Select(attrs={"class": "form-select"}),
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
        if self.instance and self.instance.pk and self.instance.item_type:
            self.fields["item_name"].initial = self.instance.item_type.name

    def clean(self):
        cleaned_data = super().clean()
        item_name = cleaned_data.get("item_name")
        if item_name:
            eve_type = resolve_eve_type(item_name)

            qs = CorpItemConfig.objects.filter(
                corporation=self.instance.corporation, item_type=eve_type
            )
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
        fields = ["default_discount_percent", "builder_reward_percent"]
        widgets = {
            "default_discount_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
            "builder_reward_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
        }


class TaxConfigForm(forms.ModelForm):
    class Meta:
        model = TaxConfig
        fields = ["industry_tax_rate", "broker_fee_rate"]
        widgets = {
            "industry_tax_rate": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
            "broker_fee_rate": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
        }


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
        fields = ["item_name", "discount_percent"]
        widgets = {
            "discount_percent": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.eve_type:
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
        (35833, "Tatara"),
        (35835, "Astrahus"),
        (35836, "Fortizar"),
        (35834, "Keepstar"),
    ]

    type_id = forms.ChoiceField(
        choices=FACILITY_TYPE_CHOICES,
        required=True,
        help_text=_("The type of Upwell structure"),
    )

    class Meta:
        model = IndustryFacility
        fields = ["facility_id", "name", "type_id", "solar_system_id"]
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
