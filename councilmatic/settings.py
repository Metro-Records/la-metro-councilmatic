import os
import sys

import dj_database_url
import environ

from .settings_jurisdiction import *  # noqa

env = environ.Env(
    # Set default values
    DJANGO_DEBUG=(bool, False),
    LOCAL_DOCKER=(bool, False),
)

# Core Django Settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Take missing environment variables from .env.local file
environ.Env.read_env(os.path.join(BASE_DIR, ".env.local"))

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG")
SHOW_TEST_EVENTS = env.bool("SHOW_TEST_EVENTS")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

if env("LOCAL_DOCKER"):
    import socket

    # Add dynamically generated Docker IP
    # Don't do this in production!
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[:-1] + "1" for ip in ips] + ["127.0.0.1"]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

DATABASES = {}

DATABASES["default"] = dj_database_url.parse(
    env("DATABASE_URL"),
    conn_max_age=600,
    engine="django.contrib.gis.db.backends.postgis",
    ssl_require=True if os.getenv("POSTGRES_REQUIRE_SSL") else False,
)

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine",
        "URL": env("SEARCH_URL"),
        "INDEX_NAME": "lametro",
        "SILENTLY_FAIL": False,
        "BATCH_SIZE": 10,
    }
}
HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"
HAYSTACK_IDENTIFIER_METHOD = "lametro.utils.get_identifier"

cache_backend = "dummy.DummyCache" if DEBUG is True else "db.DatabaseCache"
CACHES = {
    "default": {
        "BACKEND": f"django.core.cache.backends.{cache_backend}",
        "LOCATION": "site_cache",
    }
}
ADV_CACHE_INCLUDE_PK = True

# Django Debug Toolbar Panel Settings
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.sql.SQLPanel",
    "debug_toolbar.panels.cache.CachePanel",
]


# Application definition
INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "haystack",
    "opencivicdata.core",
    "opencivicdata.legislative",
    "lametro",
    "councilmatic_core",
    "adv_cache_tag",
    "debug_toolbar",
    "captcha",
    "markdownify.apps.MarkdownifyConfig",
)

try:
    INSTALLED_APPS += EXTRA_APPS  # noqa
except NameError:
    pass

MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

ROOT_URLCONF = "councilmatic.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "lametro/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "councilmatic_core.views.city_context",
                "lametro.context_processors.recaptcha_public_key",
            ],
        },
    },
]


WSGI_APPLICATION = "councilmatic.wsgi.application"


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/Los_Angeles"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Third Party Keys
RECAPTCHA_PUBLIC_KEY = env("RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = env("RECAPTCHA_PRIVATE_KEY")
if not (RECAPTCHA_PUBLIC_KEY and RECAPTCHA_PRIVATE_KEY):
    SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]

SMART_LOGIC_KEY = env("SMART_LOGIC_KEY")
SMART_LOGIC_ENVIRONMENT = env("SMART_LOGIC_ENVIRONMENT")

MERGE_HOST = env("MERGE_HOST")
MERGE_ENDPOINT = env("MERGE_ENDPOINT")

# Third Party Services

# - Document caching service
PIC_BASE_URL = "https://pic.datamade.us/lametro/document/"
FLUSH_KEY = env("FLUSH_KEY")
REFRESH_KEY = env("REFRESH_KEY")
API_KEY = env("API_KEY")

# - Analytics
ANALYTICS_TRACKING_CODE = env("ANALYTICS_TRACKING_CODE")
SERVICE_ACCOUNT_KEY_PATH = "configs/lametro_service_acct_key.json"
# Service account key should be a valid JSON string
GOOGLE_SERVICE_ACCT_API_KEY = env("GOOGLE_SERVICE_ACCT_API_KEY")
REMOTE_ANALYTICS_FOLDER = env("REMOTE_ANALYTICS_FOLDER")

# - Set this to allow Disqus comments to render.
DISQUS_SHORTNAME = None

# - Google Maps
GOOGLE_API_KEY = env("GOOGLE_API_KEY")

# - AWS
AWS_S3_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID")
AWS_S3_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")

if AWS_S3_ACCESS_KEY_ID and AWS_S3_SECRET_ACCESS_KEY:
    print(
        f"AWS configured. Uploading and retrieving headshots from {AWS_STORAGE_BUCKET_NAME}..."
    )
    from django.core.files.storage import get_storage_class

    S3Storage = get_storage_class("storages.backends.s3boto3.S3Boto3Storage")

    AWS_QUERYSTRING_AUTH = False
    COUNCILMATIC_HEADSHOT_STORAGE_BACKEND = S3Storage()

else:
    print("AWS not configured. Defaulting to local storage...")

# LOGGING
SENTRY_DSN = env("SENTRY_DSN")

if SENTRY_DSN:
    import logging

    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    from councilmatic.logging import before_send

    def custom_sampler(ctx):
        if "wsgi_environ" in ctx:
            path = ctx["wsgi_environ"].get("PATH_INFO", "")
            # Don't trace performance of static assets
            if path.startswith("/static/"):
                return 0

        # Sample other pages at 5% rate
        return 0.05

    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.WARNING,  # Send warnings and above as events
    )

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), sentry_logging],
        before_send=before_send,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
        release=f"{os.environ['HEROKU_RELEASE_VERSION']}-{os.environ['HEROKU_APP_NAME']}",
        enable_tracing=True,
        traces_sampler=custom_sampler,
        profiles_sample_rate=0.05,
    )

# Use standard logging module to catch errors in import_data (which uses a 'logger')
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "[%(asctime)s][%(levelname)s] %(name)s "
            "%(filename)s:%(funcName)s:%(lineno)d | %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console",
            "stream": sys.stdout,
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "lametro": {
            "handlers": ["console"],
            "propagate": True,
        },
    },
}


# Allow some html tags to render in markdown. Mainly for alerts
MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": [
            "br",
            "strong",
            "em",
            "a",
        ]
    }
}

# Hard time limit on HTTP requests
REQUEST_TIMEOUT = 5
