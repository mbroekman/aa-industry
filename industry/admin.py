"""Admin models"""

# Django
from django.contrib import admin

from .models import CharacterIndustryJob, CorporationIndustryJob, CorporationSyncConfig


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


from .models import (
    CorpPricingConfig,
    CorpTypeDiscount,
    MemberOrder,
    OrderFit,
    OrderItem,
)


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
