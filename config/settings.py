import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _social_app_from_env(prefix, default_name):
    client_id = os.getenv(f"{prefix}_CLIENT_ID", "").strip()
    secret = os.getenv(f"{prefix}_CLIENT_SECRET", "").strip()
    if not client_id or not secret:
        return None
    # Hidden apps act as a safe fallback when a DB-backed SocialApp also exists.
    return {
        "name": default_name,
        "client_id": client_id,
        "secret": secret,
        "settings": {
            "hidden": True,
        },
    }

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-r-ml_40k$rtu)3=$2^y$uo+tl^o5=84a*7#7oy#s@ax3dkpf5k",
)
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
SOCIAL_LOGIN_ENABLED = (
    os.getenv(
        "DJANGO_ENABLE_SOCIAL_LOGIN",
        os.getenv("DJANGO_ENABLE_GOOGLE_LOGIN", "False"),
    ).lower()
    == "true"
)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost,.pythonanywhere.com",
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "hangarin",
    "pwa",
]

if SOCIAL_LOGIN_ENABLED:
    INSTALLED_APPS += [
        "django.contrib.sites",
        "allauth",
        "allauth.account",
        "allauth.socialaccount",
        "allauth.socialaccount.providers.google",
        "allauth.socialaccount.providers.github",
    ]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

if SOCIAL_LOGIN_ENABLED:
    MIDDLEWARE.insert(-1, "allauth.account.middleware.AccountMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "hangarin" / "templates",
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Manila"

USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "hangarin" / "static",
    BASE_DIR / "static",
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

if SOCIAL_LOGIN_ENABLED:
    google_app = _social_app_from_env("GOOGLE", "Hangarin Google")
    github_app = _social_app_from_env("GITHUB", "Hangarin GitHub")
    SITE_ID = int(os.getenv("DJANGO_SITE_ID", "1"))
    AUTHENTICATION_BACKENDS.append(
        "allauth.account.auth_backends.AuthenticationBackend"
    )
    ACCOUNT_EMAIL_VERIFICATION = "none"
    ACCOUNT_LOGIN_METHODS = {"email", "username"}
    SOCIALACCOUNT_PROVIDERS = {
        "google": {
            "SCOPE": [
                "profile",
                "email",
            ],
            "AUTH_PARAMS": {
                "access_type": "online",
            },
            "OAUTH_PKCE_ENABLED": True,
        },
        # Inference: requesting email scope helps ensure GitHub returns a usable email.
        "github": {
            "SCOPE": [
                "user:email",
            ],
        },
    }
    if google_app:
        SOCIALACCOUNT_PROVIDERS["google"]["APPS"] = [google_app]
    if github_app:
        SOCIALACCOUNT_PROVIDERS["github"]["APPS"] = [github_app]

# PWA Settings (Strictly following Tutorial Screenshots)
PWA_APP_NAME = 'ProjectSite'
PWA_APP_SHORT_NAME = 'ProjectSite'
PWA_APP_DESCRIPTION = 'A Progressive Web App version of ProjectSite'
PWA_APP_THEME_COLOR = '#0A0A0A'
PWA_APP_BACKGROUND_COLOR = '#FFFFFF'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'portrait'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {
        'src': '/static/hangarin/img/icon-192.png',
        'sizes': '192x192'
    },
    {
        'src': '/static/hangarin/img/icon-512.png',
        'sizes': '512x512'
    }
]
PWA_APP_ICONS_APPLE = PWA_APP_ICONS
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static', 'js', 'serviceworker.js')
