# news_project/settings.py
"""
Django settings configuration module for the news_project web platform ecosystem.

Manages application security parameters, dynamic routing variables, 
database connections, third-party authentication configurations, and user model tracking.
"""

from pathlib import Path
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the .env file located at the project root
load_dotenv(os.path.join(BASE_DIR, '.env'))

# --- 🚀 Dynamic Environment Allocations ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-unsafe-secret-key-for-dev')

# Cast strings safely to Boolean flags
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

# Split comma-separated string variables into an array list safely
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# ==========================================
# APPLICATION PIPELINES & USER STRUCTURES
# ==========================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party extensions
    'rest_framework',
    'rest_framework_simplejwt',
    
    # Core multi-tenant application layer
    'news_api',
]

# Explicitly maps authentication routines to your custom role-based User model
AUTH_USER_MODEL = 'news_api.CustomUser'


# ==========================================
# MIDDLEWARE & SECURITY DISPATCH MATRICES
# ==========================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'news_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Explicit search path targets ensure multi-tenant dashboard templates are located efficiently
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

WSGI_APPLICATION = 'news_project.wsgi.application'


# ==========================================
# DATABASE STORAGE STORAGE MANAGEMENT
# ==========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'news_portal_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}


# ==========================================
# THIRD-PARTY FRAMEWORK AUTH DEFINITIONS
# ==========================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}


# ==========================================
# LOCAL SESSION AND SECURITY OVERRIDES
# ==========================================

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'


# ==========================================
# ROLE-BASED WORKSPACE REDIRECTION TARGETS
# ==========================================

# Route path where unauthenticated browser threads are sent to authenticate
LOGIN_URL = 'news_api:login'

# router view. This breaks the hard-cached browser '?next=' login loops natively.
LOGIN_REDIRECT_URL = 'news_api:dashboard_redirect'

# Fallback path routing user sessions immediately upon active session logouts
LOGOUT_REDIRECT_URL = 'news_api:system_landing_page'


# ==========================================
# STATIC GRAPHICS & HARDWARE STORAGE RULES
# ==========================================

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
