"""Admin models"""

# Django
from django.contrib import admin

from .models import (
    AIMarketLog,
    Basket,
    BasketItem,
    CharacterIndustryJob,
    CorpInventory,
    CorpMOTD,
    CorporationIndustryJob,
    CorporationSyncConfig,
    CorporationWebhookConfig,
    MemberOrder,
    OrderFit,
    OrderItem,
    ProductionTask,
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


@admin.register(CorpInventory)
class CorpInventoryAdmin(admin.ModelAdmin):
    list_display = (
        "corporation",
        "item_type",
        "quantity",
        "location_id",
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
        "ai_jobs_webhook",
    )


class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 1


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "corporation",
        "is_active",
        "target_region_id",
        "min_profit_margin",
    )
    list_filter = ("is_active", "corporation")
    search_fields = ("name", "corporation__corporation_name")
    inlines = [BasketItemInline]


@admin.register(AIMarketLog)
class AIMarketLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "basket_item", "action_taken", "margin", "stock_level")
    list_filter = ("action_taken",)
    search_fields = ("reason", "basket_item__eve_type__name")
    readonly_fields = (
        "timestamp",
        "basket_item",
        "action_taken",
        "margin",
        "stock_level",
        "reason",
    )
