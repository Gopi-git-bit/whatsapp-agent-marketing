"""
Django settings for the backend project.

This configuration reads values from environment variables where possible to
facilitate deployment to different environments (development, staging,
production).  When a variable is not defined, a sensible default is used.

Key technologies configured in this file:

* **Django REST Framework** with JWT authentication
* **Celery** and **Redis** for asynchronous tasks
* **Django Channels** for WebSocket support
* **PostgreSQL** for persistent storage
* **Sentry** for error tracking
* A custom middleware that records request durations for simple SLA monitoring
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from a `.env` file if present.  This allows
# development environments to define secrets and connection strings without
# committing them to version control.  In a production setting you should
# configure your environment variables via your process manager.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

#############################
# Core Django configuration #
#############################

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ['true', '1', 'yes']

ALLOWED_HOSTS: list[str] = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third‑party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'channels',
    # Local apps
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middleware to measure response times
    'backend.middleware.SLAMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION = 'backend.asgi.application'


#################################
# Database configuration         #
#################################

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DJANGO_DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DJANGO_DB_NAME', 'backend'),
        'USER': os.getenv('DJANGO_DB_USER', 'backend'),
        'PASSWORD': os.getenv('DJANGO_DB_PASSWORD', 'backend'),
        'HOST': os.getenv('DJANGO_DB_HOST', 'localhost'),
        'PORT': os.getenv('DJANGO_DB_PORT', '5432'),
    }
}


#################################
# Password validation            #
#################################

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


#################################
# Internationalization          #
#################################

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('DJANGO_TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True


#################################
# Static files (CSS, JavaScript) #
#################################

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


#######################
# REST Framework       #
#######################

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'quote_calculator': '100/hour',
    },
}

from datetime import timedelta

# Configure JSON Web Token behavior
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_MINUTES', '15'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'SIGNING_KEY': SECRET_KEY,
}


#######################
# Channels             #
#######################

# Configure the channel layer to use Redis.  The channel layer is used by
# Django Channels to coordinate WebSocket connections.  You can specify
# multiple hosts in production to scale out horizontally.
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.getenv('CHANNELS_REDIS_URL', 'redis://localhost:6379/2')],
        },
    },
}


#######################
# Celery              #
#######################

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE


#######################
# Sentry              #
#######################

# Configure Sentry if a DSN is provided.  Sentry will capture unhandled
# exceptions and send them to your Sentry project.  See https://docs.sentry.io/
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk  # type: ignore
    from sentry_sdk.integrations.django import DjangoIntegration  # type: ignore

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.0')),
        send_default_pii=True,
        environment=os.getenv('SENTRY_ENVIRONMENT', 'development'),
    )


#################################
# Custom Settings              #
#################################

# SLA threshold in seconds.  Requests exceeding this duration will be logged
# by the custom middleware.  You can adjust this via environment variable.
SLA_THRESHOLD_SECONDS = float(os.getenv('SLA_THRESHOLD_SECONDS', '0.5'))


############################
# Default primary key field #
############################

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'
