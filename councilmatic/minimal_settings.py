"""
As part of our build process, we need to run collectstatic from within the
Dockerfile. This is a minimal settings file to enable that one management command
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

INSTALLED_APPS = (
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "opencivicdata.core",
    "opencivicdata.legislative",
    "lametro",
    "councilmatic_core",
    "debug_toolbar",
    "captcha",
)
