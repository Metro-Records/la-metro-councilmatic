# These are all the settings that are specific to a deployment

import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'testing secrets'

# SECURITY WARNING: don't run with debug turned on in production!
# Set this to True while you are developing
DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'travis',
        'USER': 'travis',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        #'URL': 'http://127.0.0.1:8983/solr'
        # ...or for multicore...
        'URL': 'http://127.0.0.1:8983/solr/lametro',
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

# Set this to allow Disqus comments to render
DISQUS_SHORTNAME = None

# analytics tracking code
ANALYTICS_TRACKING_CODE = ''

HEADSHOT_PATH = os.path.join(os.path.dirname(__file__), '..'
                             '/lametro/static/images/')

EXTRA_APPS = ('raven.contrib.django.raven_compat',)

RAVEN_CONFIG = {
    'dsn': 'https://4a1f7af075cd4fd4bedebe4db50d9c3d:f49e4e9b89ed41e889f69be65b4f6f21@sentry.io/107858',
}
