"""
As part of our build process, we need to run collectstatic from within the
Dockerfile. This is a minimal settings file to enable that one management command
"""

import os

SECRET_KEY = "really super secret"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "opencivicdata.core",
    "opencivicdata.legislative",
    "lametro",
    "councilmatic_core",
    "wagtail.admin",
    "wagtail.contrib.typed_table_block",
    "wagtail",
    "debug_toolbar",
    "captcha",
)

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine",
        "URL": "http://elasticsearch:9200",
        "INDEX_NAME": "lametro",
        "SILENTLY_FAIL": False,
        "BATCH_SIZE": 10,
    }
}
