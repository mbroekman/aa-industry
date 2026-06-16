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
