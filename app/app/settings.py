"""
Django settings for app project.

Generated by 'django-admin startproject' using Django 3.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path

import environs
from celery.schedules import crontab

env = environs.Env()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ENV = env.str("ENV", default="dev")

SECRET_KEY = env.str("SECRET_KEY", default="SET_THIS_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default="localhost")
PRIMARY_ORIGIN = env.str("PRIMARY_ORIGIN", default="http://localhost")


### CELERY #########################

CELERY_BROKER_URL = env.str("REDIS_URL", default="redis://redis:6379")
CELERY_RESULT_BACKEND = "django-db"
CELERY_WORKER_CONCURRENCY = env.int("CELERY_WORKER_CONCURRENCY", default=8)
CELERY_TASK_SERIALIZER = "json"

CELERY_TASK_DEFAULT_QUEUE = "default"

CELERY_BEAT_SCHEDULE = {
    "test": {
        "task": "uptime.tasks.tick",
        "schedule": crontab(minute=f"*/1"),
    },
    "check-proxies": {
        "task": "uptime.tasks.check_proxies",
        "schedule": crontab(minute=f"*/15"),
    },
    "check-all": {
        "task": "uptime.tasks.check_all",
        #        "schedule": crontab(minute=f"*/5"),
        "schedule": crontab(minute=0, hour="*"),
    },
}

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "django_celery_results",
    "django_tables2",
    "uptime",
    "django_alive",
]

MIDDLEWARE = [
    "django_alive.middleware.healthcheck_bypass_host_check",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL", default="postgres://postgres:uptime@postgres:5432/uptime"
    ),
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = "/static/"


## logging

handler = "console" if DEBUG else "json"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "json": {"class": "logging.StreamHandler", "formatter": "json"},
    },
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(name) %(message)s %(levelname) %(module) %(filename) %(funcName) %(lineno)",
        }
    },
    "loggers": {
        "django": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
        },
        "ddtrace": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
        },
        "common": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
            "propagate": False,
        },
        "uptime": {
            "handlers": [handler],
            "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
        },
    },
}


##

SELENIUM_URL = env.str("SELENIUM_URL", "http://selenium:4444/wd/hub")
SELENIUM_DRIVER_TIMEOUT = env.int("SELENIUM_DRIVER_TIMEOUT", 30)


#### AWS CONFIGURATION

AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", default="")
AWS_DEFAULT_REGION = env.str("AWS_DEFAULT_REGION", default="us-west-2")

AWS_PROXY_ROLE_ARN = env.str("AWS_PROXY_ROLE_ARN", default=None)
AWS_PROXY_ROLE_SESSION_NAME = env.str("AWS_PROXY_ROLE_SESSION_NAME", default=None)

SNAPSHOT_BUCKET = env.str("SNAPSHOT_BUCKET", default=None)

AWS_PROXY_KEY_NAME = env.str("AWS_PROXY_KEY_NAME", default="uptime-proxy")

#### END AWS CONFIGURATION


#### PROXY CONFIGURATION

PROXY_SSH_KEY = (
    env.str("PROXY_SSH_KEY", default="").replace("\\n", "\n").encode("utf-8")
)
PROXY_SSH_KEY_ID = env.str("PROXY_SSH_KEY_ID", default=None)
DIGITALOCEAN_KEY = env.str("DIGITALOCEAN_KEY", default=None)

PROXY_TAG = env.str("PROXY_TAG", default=ENV)

#### END PROXY_CONFIGURATION


#### DJANGO-ALIVE CONFIGURATION

ALIVE_CHECKS = {
    "django_alive.checks.check_migrations": {},
}

#### END ALIVE CONFIGURATION
