"""

Google Auth Codes:

Client ID: 825158876282-u0pr92c0l72r3s0i6vn86ti1koa2m48m.apps.googleusercontent.com
Secret: aO1icaDW0LHIjmaZItMdYFNk

Django settings for BidCentral project.

Generated by 'django-admin startproject' using Django 2.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""
import os
from dotenv import load_dotenv

load_dotenv(".env")

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '3r%!0f-_l2vmx#g9r0*^*193$gks6flg2+ria)3sh4n82y6c17'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1"]


# Application definition

INSTALLED_APPS = [
    ## Admin backend
    'jazzmin',
    
    ## Django defaults
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tables2',
    'django.contrib.sites',
    
    # Cool looking "ago" type human dates
    'django.contrib.humanize',

    # ## Main app
    'project.apps.bidinterpreter',

    # ## Addon allauth module
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # ## Custom profiles app
    'project.apps.profile',

    # ## Custom invite app
    'project.apps.invite',

    # Nicer looking django forms, pip install django-bootstrap-form
    'bootstrapform',

    # For better phone numbers in forms, pip install django-phonenumber-field[phonenumbers]
    'phonenumber_field',

    # Debug toolbar -- great for inspecting django objects, pip install django-debug-toolbar
    'debug_toolbar',

    # pip install django-debug-permissions
    'debug_permissions',

    # pip install django-formtools
    'formtools',
    
    # pip install django-compressor-toolkit
    'compressor',
    'sass_processor',

    ## testing kafka replacement
    # pip install django-background-tasks 
    'background_task',

    ## pip install django-admin-json-editor
    # 'django_admin_json_editor',
    ## pip install django-json-widget
    'django_json_widget',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'project.apps.bidinterpreter.basic_http_auth.BasicAuthMiddleware'
]

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ]
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_DIR, 'project/templates'), os.path.join(PROJECT_DIR, 'project/templates/allauth')],
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

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql_psycopg2',
        'NAME':     os.environ['pgsql_db'],
        'USER':     os.environ['pgsql_user'],
        'PASSWORD': os.environ['pgsql_password'],
        'HOST':     os.environ['pgsql_host'],
        'PORT':     os.environ['pgsql_port'],
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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

# File Upload - You can change it yourself
DRF_FILE_UPLOAD_PATH = os.path.join(BASE_DIR, 'uploads')

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, "static")
# ]

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
COMPRESS_ROOT = BASE_DIR + "/static"

STATICFILES_FINDERS = (
    #'django_tenants.staticfiles.finders.TenantFileSystemFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
    'sass_processor.finders.CssFinder',
)

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
    'compressor.filters.template.TemplateFilter'
]

COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]
# COMPRESS_PRECOMPILERS = (
#     ('module', 'compressor_toolkit.precompilers.ES6Compiler'),
# )
COMPRESS_ENABLED = True

# STATIC_ROOT = os.path.join(BASE_DIR, 'uploads')
MEDIA_ROOT = BASE_DIR + '/uploads'
MEDIA_URL = '/uploads/'

SITE_ID = 1

# ACCOUNT_EMAIL_VERIFICATION = 'none'
# LOGIN_REDIRECT_URL = 'home'

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        'SCOPE': [
            'profile',
            'email',
        ],
        # 'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

INTERNAL_IPS = [
    '127.0.0.1',
]

#DataFlair
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = "loihub.invites@gmail.com"
EMAIL_HOST_PASSWORD = "b3st p@ssw0rd ev@r"

#ACCOUNT_CONFIRM_EMAIL_ON_GET = True
#ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
#ACCOUNT_EMAIL_REQUIRED = True
#ACCOUNT_AUTHENTICATION_METHOD = "username_email"
#ACCOUNT_CONFIRM_EMAIL_ON_GET = True
#ACCOUNT_EMAIL_REQUIRED = True
#ACCOUNT_EMAIL_VERIFICATION = "mandatory"
#ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
#ACCOUNT_LOGOUT_ON_GET = True
#ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_SESSION_REMEMBER = True

## Social Account Settings
# SOCIALACCOUNT_EMAIL_VERIFICATION = ACCOUNT_EMAIL_VERIFICATION

## This appears depricated but not in the documentation -- so annoying https://github.com/pennersr/django-allauth/issues/2039
# ACCOUNT_SIGNUP_FORM_CLASS = "signup.forms.SignupForm"
# New method:
# ACCOUNT_FORMS = {'signup': 'profile.forms.UserProfile'}
#ACCOUNT_SIGNUP_FORM_CLASS = 'signup.forms.SignupForm'

ACCOUNT_LOGOUT_REDIRECT_URL ='/bidinterpreter'
LOGIN_REDIRECT_URL = "/bidinterpreter"
ACCOUNT_LOGOUT_ON_GET = True

# Google Development Credentials - Allauth - (double check not logged in as admin account!)
# client id: 773667739422-4r7tp65kdv3k0tmnc1udg5j939am77em.apps.googleusercontent.com
# secret key: L97r1-U8StgaLVDGvlcN5-jR

# For phone number validation
PHONENUMBER_DEFAULT_REGION = 'US'

# Basic HTTP Auth
BASICAUTH_USERNAME = "always"
BASICAUTH_PASSWORD = "be closing"

# Background processing configuration
BACKGROUND_TASK_RUN_ASYNC = True
MAX_ATTEMPTS = 1


X_FRAME_OPTIONS='SAMEORIGIN'
XS_SHARING_ALLOWED_METHODS = ['POST','GET','OPTIONS', 'PUT', 'DELETE']

JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    # "site_title": "Library Admin",
    "site_header": "LOIHub Dashboard",
}

## Show toolbar only in speicifc routes matching condition
def show_toolbar(request):
    return "download" not in request.build_absolute_uri()

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'project.settings.show_toolbar',
    # Rest of config
}