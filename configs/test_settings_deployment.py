# These are all the settings that are specific to a deployment
import os
import sys

import dj_database_url


ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'testing secrets'

# SECURITY WARNING: don't run with debug turned on in production!
# Set this to True while you are developing
DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(default=os.environ['DATABASE_URL']),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': 'lametro',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'localhost',
            'PORT': 5432,
        },
    }

if os.getenv('SOLR_URL'):
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
            #'URL': 'http://127.0.0.1:8983/solr'
            # ...or for multicore...
            'URL': os.environ['SOLR_URL'],
        },
    }
else:
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine'
        },
    }

# Remember to run python manage.py createcachetable so this will work!
# developers, set your BACKEND to 'django.core.cache.backends.dummy.DummyCache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'councilmatic_cache',
    }
}

# Set this to flush the cache at /flush-cache/{FLUSH_KEY}
FLUSH_KEY = 'super secret junk'
API_KEY = 'test api key'

# Set this to allow Disqus comments to render
DISQUS_SHORTNAME = None

# analytics tracking code
ANALYTICS_TRACKING_CODE = ''

HEADSHOT_PATH = os.path.join(os.path.dirname(__file__), '..'
                             '/lametro/static/images/')

SHOW_TEST_EVENTS = False

BUCKET_NAME = 'la-metro-headshots-staging'
print("from test_settings.deployment:", BUCKET_NAME)

SMART_LOGIC_KEY = 'smartlogic api key'
SMART_LOGIC_ENVIRONMENT = '0ef5d755-1f43-4a7e-8b06-7591bed8d453'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '[%(asctime)s][%(levelname)s] %(name)s '
                      '%(filename)s:%(funcName)s:%(lineno)d | %(message)s',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'stream': sys.stdout
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    },
    'loggers': {
        'lametro': {
            'handlers': ['console'],
            'propagate': True,
        },
    }
}
