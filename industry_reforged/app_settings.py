"""App Settings"""

# Django
from django.conf import settings

# put your app settings here


INDUSTRY_SETTING_ONE = getattr(settings, "INDUSTRY_SETTING_ONE", None)
