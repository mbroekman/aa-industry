"""Admin models"""

# Django
from django.contrib import admin

from .models import (
    CharacterIndustryJob,
    CorpHangarConfig,
    CorpInventory,
    CorpItemConfig,
    CorpMOTD,
    CorporationIndustryJob,
    CorporationSyncConfig,
    CorpPricingConfig,
    CorpTypeDiscount,
    MemberOrder,
    OrderFit,
    OrderItem,
    ProductionTask,
    TaxConfig,
)


@admin.register(CharacterIndustryJob)
class CharacterIndustryJobAdmin(admin.ModelAdmin):
    list_display = ("job_id", "character", "status", "start_date", "end_date")
    search_fields = ("character__character_name",)


@admin.register(CorporationIndustryJob)
class CorporationIndustryJobAdmin(admin.ModelAdmin):
    list_display = (
        "job_id",
        "corporation",
        "installer",
        "status",
        "start_date",
        "end_date",
    )
    search_fields = ("corporation__corporation_name", "installer__character_name")


@admin.register(CorporationSyncConfig)
class CorporationSyncConfigAdmin(admin.ModelAdmin):
    list_display = ("corporation", "sync_character")


@admin.register(CorpPricingConfig)
class CorpPricingConfigAdmin(admin.ModelAdmin):
    list_display = ("corporation", "default_discount_percent")


@admin.register(CorpTypeDiscount)
class CorpTypeDiscountAdmin(admin.ModelAdmin):
    list_display = ("config", "eve_type", "discount_percent")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class OrderFitInline(admin.StackedInline):
    model = OrderFit


@admin.register(MemberOrder)
class MemberOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "character", "status", "total_price", "created_at")
    list_filter = ("status",)
    search_fields = ("character__character_name",)
    inlines = [OrderItemInline, OrderFitInline]


@admin.register(CorpMOTD)
class CorpMOTDAdmin(admin.ModelAdmin):
    list_display = ("corporation", "updated_at", "updated_by")


@admin.register(ProductionTask)
class ProductionTaskAdmin(admin.ModelAdmin):
    list_display = ("item_type", "quantity", "status", "assigned_to", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("assigned_to__character_name", "item_type__name")


@admin.register(CorpItemConfig)
class CorpItemConfigAdmin(admin.ModelAdmin):
    list_display = (
        "corporation",
        "item_type",
        "build_or_buy",
        "bom_source",
        "target_threshold",
        "auto_produce",
    )
    list_filter = ("build_or_buy", "bom_source", "auto_produce")
    search_fields = ("item_type__name", "corporation__corporation_name")


@admin.register(CorpHangarConfig)
class CorpHangarConfigAdmin(admin.ModelAdmin):
    list_display = ("corporation", "location_id", "flag_id", "description")


@admin.register(CorpInventory)
class CorpInventoryAdmin(admin.ModelAdmin):
    list_display = (
        "corporation",
        "item_type",
        "quantity",
        "location_id",
        "flag_id",
        "manual_override",
    )
    list_filter = ("manual_override", "corporation")
    search_fields = ("item_type__name",)


@admin.register(TaxConfig)
class TaxConfigAdmin(admin.ModelAdmin):
    list_display = ("corporation", "industry_tax_rate", "broker_fee_rate")
