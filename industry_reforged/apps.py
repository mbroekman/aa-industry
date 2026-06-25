"""App Configuration"""

# Django
from django.apps import AppConfig

# AA Industry App
from industry_reforged import __version__


class IndustryConfig(AppConfig):
    """App Config"""

    name = "industry_reforged"
    label = "industry_reforged"
    verbose_name = f"Industry App v{__version__}"
