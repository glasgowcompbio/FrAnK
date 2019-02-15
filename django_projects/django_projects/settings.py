"""
Django settings for django_projects project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import djcelery
import logging
from support import logging_support


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'q2wm(xhfj@6k+))@sk^4vm(t%1i3rqoqh*^y$!+g5d@538d!)t'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(BASE_DIR), 'mytemplates'),
    os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'python_support'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.static',
)

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_spaghetti',
    'registration',
    'frank'
)

SPAGHETTI_SAUCE = {
  'apps':[
    'frank'
  ],
  'show_fields': False,
}


MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'django_projects.urls'

WSGI_APPLICATION = 'django_projects.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
# MEDIA_ROOT = os.path.abspath(os.path.dirname(__file__)) + '/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'pimp_data')
os.environ['PIMP_MEDIA_ROOT'] = MEDIA_ROOT

#MEDIA_ROOT = '/opt/django/data/pimp_data/'
#MEDIA_ROOT = '/Users/yoanngloaguen/Documents/ideomWebSite/media/'
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) + '/static/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    # '/Users/yoanngloaguen/Documents/django_projects/pimp/static/',
    os.path.join(os.path.dirname(__file__), 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Other setting files

CELERYD_LOG_COLOR = False
CELERYD_MAX_TASKS_PER_CHILD=1
DJANGO_LOG_LEVEL = 'WARNING'
os.environ['DJANGO_LOG_LEVEL'] = DJANGO_LOG_LEVEL

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
logging.setLoggerClass(logging_support.FineLogger)
CELERYD_HIJACK_ROOT_LOGGER = False
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'context_filter': {
            '()': 'support.logging_support.ContextFilter',
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(filename)s:%(lineno)d %(user)s %(project)s %(analysis)s | %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(filename)s:%(lineno)d | %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': os.getenv('DJANGO_LOG_LEVEL', 'WARNING'),
            'formatter': 'verbose',
            'filters': ['context_filter'],
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        '': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'WARN',
            'propagate': False,
        },
        'celery.task': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': False,
        },
    }
}
from celery.signals import setup_logging
@setup_logging.connect
def configure_celery_logging(**kwargs):
    pass

NOTEBOOK_ARGUMENTS = [
    '--ip', '0.0.0.0',
]

MSPEPSEARCH_IMAGE = 'nist-image'
INTERNAL_NIST_QUERY_DIR = os.path.join(os.path.dirname(BASE_DIR), 'pimp', 'frank', 'NISTQueryFiles')
EXTERNAL_NIST_QUERY_DIR = INTERNAL_NIST_QUERY_DIR
INTERNAL_MAGMA_QUERY_DIR = os.path.join(os.path.dirname(BASE_DIR), 'pimp', 'frank', 'MAGMAQueryFiles')
EXTERNAL_MAGMA_QUERY_DIR = INTERNAL_MAGMA_QUERY_DIR
