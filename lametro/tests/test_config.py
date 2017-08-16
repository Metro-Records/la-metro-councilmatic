SECRET_KEY = 'sweet bird most musical most melancholy'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'haystack',
    'lametro',
    'councilmatic_core',
    'adv_cache_tag',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lametro',
        'USER': '',
        'PASSWORD': '',
        'PORT': 5432,
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8983/solr',
    },
}

OCD_CITY_COUNCIL_ID = 'ocd-organization/42e23f04-de78-436a-bec5-ab240c1b977c'

CITY_COUNCIL_NAME = 'Metro'

APP_NAME = 'lametro'