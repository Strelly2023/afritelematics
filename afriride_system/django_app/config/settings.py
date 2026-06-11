import os


SECRET_KEY = os.environ.get("AFRIRIDE_DJANGO_SECRET_KEY", "local-dev-only-not-for-production")

DEBUG = os.environ.get("AFRIRIDE_DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = ['*']  # ✅ 
ROOT_URLCONF = "config.urls"
AUDIT_API_KEY = os.environ.get("AFRIRIDE_AUDIT_API_KEY", "local-audit-key-not-for-production")

MIDDLEWARE = [
    "config.middleware.DevelopmentCorsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [],
        "OPTIONS": {},
    }
]


INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
    "django.contrib.auth",
    "django.contrib.staticfiles",

    # ✅ Your app
    "afritech",
    "blockchain",
]

STATIC_URL = "/static/"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}

USE_TZ = True
TIME_ZONE = "UTC"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
