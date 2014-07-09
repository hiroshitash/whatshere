# Django settings for whatshere_iphone_server project.
import config
import logging
import sys

DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_PROPAGATE_EXCEPTIONS = True

ADMINS = (
    ('Hiroshi Tashiro', 'hiroshitash@gmail.com'),
)

SESSION_COOKIE_SECURE = False
MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django_mongodb_engine', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'my_database',                      # Or path to database file if using sqlite3.
        #'USER': '',                      # Not used with sqlite3.
        #'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': 'ec2-50-18-80-0.us-west-1.compute.amazonaws.com',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '27017',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
#TIME_ZONE = 'America/Chicago'
TIME_ZONE = 'GMT' # same as UTC

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

#SITE_ID = 1
SITE_ID=u'4e1eac30956e0a661700000d'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"

if config.dev:
    APP_DIR = r'/home/ec2-user/whatshere_dev/'
    LOG_DIR = r'/var/log/whatshere_dev/'
    if config.FLAG_INDIVIDUAL_WEBSITE:
        if config.PyDev:
            APP_DIR = r'/Users/hiroshitashiro/Documents/workspace/whatshere_dev/'
            LOG_DIR = r'/Users/hiroshitashiro/Documents/workspace/whatshere_dev/log/'
            MEDIA_ROOT = r'/Users/hiroshitashiro/Documents/workspace/whatshere_dev/media/'
        else:
            MEDIA_ROOT = r'/home/ec2-user/whatshere_dev/media/'
    else:
        MEDIA_ROOT = r'/home/ec2-user/whatshere_dev/media/'
else:
    APP_DIR = r'/home/ec2-user/whatshere_prod/'
    LOG_DIR = r'/var/log/whatshere_prod/'
    if config.FLAG_INDIVIDUAL_WEBSITE:
        MEDIA_ROOT = r'/home/ec2-user/whatshere_prod/media/'
    else:
        MEDIA_ROOT = r'/home/ec2-user/whatshere_prod/media/'
#MEDIA_ROOT = r'/Users/hiroshitashiro/Documents/workspace/whatshere_iphone_server_dev/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = r'/lmedia/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'x5v#2k7@!vfo9(&%eh*a7j#*y1-tr)=esi9t!tly!rvnlj9v%k'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
#    'django.middleware.csrf.CsrfViewMiddleware',
#    'django.middleware.csrf.CsrfResponseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
#    'socialregistration.middleware.FacebookMiddleware'
)

if config.dev:
    if config.FLAG_INDIVIDUAL_WEBSITE:
        ROOT_URLCONF = 'whatshere_dev.urls'
        if config.PyDev:
            TEMPLATE_DIRS = (
            # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
            # Always use forward slashes, even on Windows.
            # Don't forget to use absolute paths, not relative paths.
            #"/home/ec2-user/whatshere_dev/templates",
            "/Users/hiroshitashiro/Documents/workspace/whatshere_dev/templates",
            )
        else:
            TEMPLATE_DIRS = (
            # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
            # Always use forward slashes, even on Windows.
            # Don't forget to use absolute paths, not relative paths.
            "/home/ec2-user/whatshere_dev/templates",
            #    "/Users/hiroshitashiro/Documents/workspace/whatshere_dev/templates",
            )
    else:
        ROOT_URLCONF = 'whatshere_dev.urls'
        TEMPLATE_DIRS = (
            # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
            # Always use forward slashes, even on Windows.
            # Don't forget to use absolute paths, not relative paths.
            "/home/ec2-user/whatshere_dev/templates",
            #    "/Users/hiroshitashiro/Documents/workspace/whatshere_dev/templates",
            )
else:
    if config.FLAG_INDIVIDUAL_WEBSITE:
        ROOT_URLCONF = 'whatshere_prod.urls'
        TEMPLATE_DIRS = (
            # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
            # Always use forward slashes, even on Windows.
            # Don't forget to use absolute paths, not relative paths.
            "/home/ec2-user/whatshere_prod/templates",
            #    "/Users/hiroshitashiro/Documents/workspace/whatshere/templates",
            )
    else:
        ROOT_URLCONF = 'whatshere_prod.urls'
        TEMPLATE_DIRS = (
            # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
            # Always use forward slashes, even on Windows.
            # Don't forget to use absolute paths, not relative paths.
            "/home/ec2-user/whatshere_prod/templates",
            #    "/Users/hiroshitashiro/Documents/workspace/whatshere/templates",
            )

INSTALLED_APPS = (
    'django_mongodb_engine',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
#    'posts',
#    'polls',
#    'socialregistration',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
if not config.PyDev:
    LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '[%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d] %(message)s'
        },
        'simple': {
            'format': '[%(levelname)s] %(asctime)s %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'DEBUG',
#            'class':'logging.handlers.RotatingFileHandler',
            'class':'cloghandler.ConcurrentRotatingFileHandler',
            'filename': "%s/django.log" % LOG_DIR,
            'maxBytes': 1024 * 1024 * 5, # 5 MB
            'backupCount': 5,
            'formatter':'standard',
        },
        'request_handler': {
                'level':'DEBUG',
                'class':'logging.handlers.RotatingFileHandler',
                'filename': "%s/request.log" % LOG_DIR,
                'maxBytes': 1024 * 1024 * 5, # 5 MB
                'backupCount': 5,
                'formatter':'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
#        'django.request': { # Stop SQL debug from logging to main logger
#            'handlers': ['request_handler'],
#            'level': 'DEBUG',
#            'propagate': False
#        },
    }
    }
else:
    LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d] %(message)s'
        },
        'simple': {
            'format': '[%(levelname)s] %(message)s'
        },
    },
    'handlers': {
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'whatshere_dev': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
    }

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages"
)

FACEBOOK_APP_ID = '178504128874319'
FACEBOOK_API_KEY = '178504128874319'
FACEBOOK_SECRET_KEY = '1947d6668bc2e9dc7c5ca25002dd7fde'

AUTHENTICATION_BACKENDS = (
#    'socialregistration.auth.FacebookAuth',
    'django.contrib.auth.backends.ModelBackend'
)

#FACEBOOK_REQUEST_PERMISSIONS = 'email,user_about_me,offline_access,read_stream'
FACEBOOK_REQUEST_PERMISSIONS = 'user_interests,user_likes,user_checkins,user_events,user_status,friends_checkins,friends_status'

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

