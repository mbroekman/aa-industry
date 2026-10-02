# Every setting in base.py can be overloaded by redefining it here.
from .base import *
from urllib.parse import urlparse

# These are required for Django to function properly. Don't touch.
ROOT_URLCONF = 'myauth.urls'
WSGI_APPLICATION = 'myauth.wsgi.application'
SECRET_KEY = 'django-insecure-8(-oo4(@zoo^36tpfvs+oi%v-cf@4zh@59%5u18pb%(18p3ja+'

# This is where css/images will be placed for your webserver to read
STATIC_ROOT = "/var/www/myauth/static/"

# Change this to change the name of the auth site displayed
# in page titles and the site header.
SITE_NAME = 'myauth'

# This is your websites URL, set it accordingly
# Make sure this URL is WITHOUT a trailing slash
SITE_URL = "https://example.com"

# Django security
ALLOWED_HOSTS = [urlparse(SITE_URL).hostname]
CSRF_TRUSTED_ORIGINS = [SITE_URL]

# Change this to enable/disable debug mode, which displays
# useful error messages but can leak sensitive data.
DEBUG = False

# Add any additional apps to this list.
INSTALLED_APPS += [
    #'allianceauth.theme.bootstrap',
]

# To change the logging level for extensions, uncomment the following line.
# LOGGING['handlers']['extension_file']['level'] = 'DEBUG'

# By default, apps are prevented from having public views for security reasons.
# To allow specific apps to have public views, add them to APPS_WITH_PUBLIC_VIEWS
#   » The format is the same as in INSTALLED_APPS
#   » The app developer must also explicitly allow public views for their app
APPS_WITH_PUBLIC_VIEWS = [

]

# Enter credentials to use MySQL/MariaDB. Comment out to use sqlite3
DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'alliance_auth',
    'USER': '',
    'PASSWORD': '',
    'HOST': '127.0.0.1',
    'PORT': '3306',
    'OPTIONS': {'charset': 'utf8mb4'},
}

# Register an application at https://developers.eveonline.com for Authentication
# & API Access and fill out these settings. Be sure to set the callback URL
# to https://example.com/sso/callback substituting your domain for example.com in
# CCP's developer portal
# Logging in to auth requires the publicData scope (can be overridden through the
# LOGIN_TOKEN_SCOPES setting). Other apps may require more (see their docs).
ESI_SSO_CALLBACK_URL = f"{SITE_URL}/sso/callback"  # Do NOT change this line!
ESI_SSO_CLIENT_ID = ''
ESI_SSO_CLIENT_SECRET = ''
ESI_USER_CONTACT_EMAIL = ''  # A server maintainer that CCP can contact in case of issues.

# By default, emails are validated before new users can log in.
# It's recommended to use a free service like SparkPost or Elastic Email to send email.
# https://www.sparkpost.com/docs/integrations/django/
# https://elasticemail.com/resources/settings/smtp-api/
# Set the default from email to something like 'noreply@example.com'
# Email validation can be turned off by uncommenting the line below. This can break some services.
# REGISTRATION_VERIFY_EMAIL = False
EMAIL_HOST = ''
EMAIL_PORT = 587
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = ''

# Cache compression can help on bigger auths where ram starts to become an issue.
# Uncomment the following 3 lines to enable.

#CACHES["default"]["OPTIONS"] = {
#    "COMPRESSOR": "django_redis.compressors.lzma.LzmaCompressor",
#}

#######################################
# Add any custom settings below here. #
#######################################
ESI_USER_CONTACT_EMAIL = "test@test.com"
