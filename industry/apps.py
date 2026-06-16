"""App Configuration"""

# Django
from django.apps import AppConfig

# AA Industry App
from industry import __version__


class IndustryConfig(AppConfig):
    """App Config"""

    name = "industry"
    label = "industry"
    verbose_name = f"Industry App v{__version__}"
