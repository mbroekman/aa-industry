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
    CorporationWebhookConfig,
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


@admin.register(CorporationWebhookConfig)
class CorporationWebhookConfigAdmin(admin.ModelAdmin):
    list_display = (
        "corporation",
        "orders_webhook",
        "jobs_webhook",
        "wallets_webhook",
        "inventory_webhook",
    )


class CorpTypeDiscountInline(admin.TabularInline):
    model = CorpTypeDiscount
    extra = 1
    raw_id_fields = ("eve_type",)


@admin.register(CorpPricingConfig)
class CorpPricingConfigAdmin(admin.ModelAdmin):
    list_display = ("corporation", "default_discount_percent", "builder_reward_percent")
    search_fields = ("corporation__corporation_name",)
    raw_id_fields = ("corporation",)
    inlines = [CorpTypeDiscountInline]


@admin.register(TaxConfig)
class TaxConfigAdmin(admin.ModelAdmin):
    list_display = ("corporation", "industry_tax_rate", "broker_fee_rate")
    search_fields = ("corporation__corporation_name",)
    raw_id_fields = ("corporation",)


@admin.register(CorpItemConfig)
class CorpItemConfigAdmin(admin.ModelAdmin):
    list_display = ("corporation", "item_type", "manual_price")
    search_fields = ("corporation__corporation_name", "item_type__name")
    raw_id_fields = ("corporation", "item_type")
