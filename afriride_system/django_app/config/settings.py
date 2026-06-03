SECRET_KEY = "dev-key"

DEBUG = True
ROOT_URLCONF = "config.urls"
AUDIT_API_KEY = "super-secret-key-123"


INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
    "django.contrib.auth",

    # ✅ Your app
    "afritech",
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
