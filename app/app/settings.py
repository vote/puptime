"""
Django settings for app project.

Generated by 'django-admin startproject' using Django 3.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
from pathlib import Path
from typing import Dict, Optional

import environs
import sentry_sdk
from celery.schedules import crontab
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

env = environs.Env()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ENV = env.str("ENV", default="dev")

SECRET_KEY = env.str("SECRET_KEY", default="SET_THIS_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default="localhost")
PRIMARY_ORIGIN = env.str("PRIMARY_ORIGIN", default="http://localhost:9901")

# Useful analytics and tracking tags
CLOUD_DETAIL = env.str("CLOUD_DETAIL", default="")
SERVER_GROUP = env.str("SERVER_GROUP", default="")
CLOUD_STACK = env.str("CLOUD_STACK", default="local")
ENV = env.str("ENV", default=CLOUD_STACK)
TAG = env.str("TAG", default="")
BUILD = env.str("BUILD", default="0")


### CELERY #########################

CELERY_BROKER_URL = env.str("REDIS_URL", default="redis://redis:6379")
CELERY_RESULT_BACKEND = "django-db"
CELERY_WORKER_CONCURRENCY = env.int("CELERY_WORKER_CONCURRENCY", default=8)
CELERY_TASK_SERIALIZER = "json"

# specify a max_loop_interval AND lock timeout that ensure we don't
# pause too long during/after a redeploy
CELERY_BEAT_MAX_LOOP_INTERVAL = 5
CELERY_REDBEAT_LOCK_TIMEOUT = 30

CELERY_TASK_DEFAULT_QUEUE = "default"

CELERY_BEAT_SCHEDULE = {
    "test": {"task": "uptime.tasks.tick", "schedule": crontab(minute=f"*/1"),},
}

if env.bool("PROXIES", default=True):
    CELERY_BEAT_SCHEDULE["check-proxies"] = {
        "task": "uptime.tasks.check_proxies",
        "schedule": crontab(minute=f"*/15"),
    }
    CELERY_BEAT_SCHEDULE["check-all"] = {
        "task": "uptime.tasks.check_all",
        "schedule": crontab(minute=f"*/5"),
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
        "DIRS": ["templates",],
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
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
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

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_PATH, "static")

## logging

handler = "console" if DEBUG else "json"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler",},
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
        # "ddtrace": {
        #     "handlers": [handler],
        #     "level": env.str("DJANGO_LOGGING_LEVEL", default="INFO"),
        # },
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

SELENIUM_URL = env.str("SELENIUM_URL", "http://127.0.0.1:4444/wd/hub")
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

MAX_PROXY_AGE_HOURS = env.int("MAX_PROXY_AGE_HOURS", default=2)

#### END PROXY_CONFIGURATION


#### DJANGO-ALIVE CONFIGURATION

ALIVE_CHECKS: Dict[str, Dict[Optional[str], Optional[str]]] = {
    "django_alive.checks.check_migrations": {},
}

#### END ALIVE CONFIGURATION


#### DATADOG CONFIGURATION

# ddtrace.tracer.set_tags({"build": BUILD})

#### END DATADOG CONFIGURATION


#### STATSD CONFIGURATION

STATSD_TAGS = [
    f"env:{ENV}",
    f"spinnaker_detail:{CLOUD_DETAIL}",
    f"spinnaker_servergroup:{SERVER_GROUP}",
    f"spinnaker_stack:{CLOUD_STACK}",
    f"image_tag:{TAG}",
    f"build:{BUILD}",
]

#### END STATSD CONFIGURATION


#### SENTRY CONFIGURATION

SENTRY_DSN = env.str("SENTRY_DSN", default="")
if TAG and SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), RedisIntegration(), CeleryIntegration()],
        send_default_pii=True,
        release=f"puptime@{TAG}",
        environment=ENV,
    )

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("SERVER_GROUP", SERVER_GROUP)
        scope.set_tag("CLOUD_DETAIL", CLOUD_DETAIL)
        scope.set_tag("CLOUD_STACK", CLOUD_STACK)
        scope.set_tag("build", BUILD)
        scope.set_tag("tag", TAG)
        scope.set_extra("allowed_hosts", ALLOWED_HOSTS)

#### END SENTRY CONFIGURATION
