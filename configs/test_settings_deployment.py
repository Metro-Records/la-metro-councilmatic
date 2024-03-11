# These are all the settings that are specific to a deployment
import os
import sys

import dj_database_url


ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "testing secrets"

# SECURITY WARNING: don't run with debug turned on in production!
# Set this to True while you are developing
DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
if os.getenv("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(default=os.environ["DATABASE_URL"]),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": "lametro",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "localhost",
            "PORT": 5432,
        },
    }

HAYSTACK_CONNECTIONS = {
    "default": {
        "ENGINE": "haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine",
        "URL": "http://elasticsearch:9200",
        "INDEX_NAME": "lametro",
        "SILENTLY_FAIL": False,
        "BATCH_SIZE": 10,
    }
}
HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.RealtimeSignalProcessor"
HAYSTACK_IDENTIFIER_METHOD = "lametro.utils.get_identifier"

# Remember to run python manage.py createcachetable so this will work!
# developers, set your BACKEND to 'django.core.cache.backends.dummy.DummyCache'
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "councilmatic_cache",
    }
}

MEDIA_ROOT = "/media"

# Set this to flush the cache at /flush-cache/{FLUSH_KEY}
FLUSH_KEY = "super secret junk"
API_KEY = "test api key"

# Set this to allow Disqus comments to render
DISQUS_SHORTNAME = None

HEADSHOT_PATH = os.path.join(os.path.dirname(__file__), ".." "/lametro/static/images/")

SHOW_TEST_EVENTS = False

AWS_STORAGE_BUCKET_NAME = "la-metro-headshots-staging"

SMART_LOGIC_KEY = "smartlogic api key"
SMART_LOGIC_ENVIRONMENT = "0ef5d755-1f43-4a7e-8b06-7591bed8d453"

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
