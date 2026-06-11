import os


SECRET_KEY = os.environ.get("AFRIRIDE_DJANGO_SECRET_KEY", "local-dev-only-not-for-production")

DEBUG = os.environ.get("AFRIRIDE_DJANGO_DEBUG", "0") == "1"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",

    # ✅ Your modules
    "afritech.apps.AfriTechConfig",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}

USE_TZ = True
TIME_ZONE = "UTC"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
