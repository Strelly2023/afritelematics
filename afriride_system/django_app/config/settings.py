SECRET_KEY = "dev-key"

DEBUG = True
ALLOWED_HOSTS = ['*']  # ✅ ADD THIS
ROOT_URLCONF = "config.urls"
AUDIT_API_KEY = "super-secret-key-123"

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
