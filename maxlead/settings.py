"""
Django settings for maxlead project.

Generated by 'django-admin startproject' using Django 1.11.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '2(hp2_0t2&yo^bg@i7ih*wwl22p+mq#uk6y--j4f5&=^+(c3pi'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'suit',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_crontab',
    'django_object_actions',
    'maxlead_site',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'maxlead.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'maxlead.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # }

    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'maxlead',
        'USER': 'odoo',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

SPIDER_URL = 'D:/maxlead/bots/maxlead_scrapy'

DOWNLOAD_URL = 'D:/maxlead/download'

REVIEW_TIME = 604800

# django-suit config
SUIT_CONFIG = {
    'ADMIN_NAME': 'Maxlead信息管理系统',
    'HEADER_DATE_FORMAT': '',
    'HEADER_TIME_FORMAT': 'H:i',
    'SHOW_REQUIRED_ASTERISK': True,
    'CONFIRM_UNSAVED_CHANGES': True,
    'LIST_PER_PAGE': 20,
    'MENU_OPEN_FIRST_CHILD': True,
    'MENU': (
        # sites是默认原先的app和models
        'maxlead_site',
        # '-',
        # {'app': 'Maxlead_Site', 'label': u'爬虫', 'icon': 'icon-user'},
        # '-',
        # {'app': 'duser', 'label': u'平台用户', 'icon': 'icon-user'},
        # '-',
        # {'app': 'dtheme', 'label': u'主题管理', 'icon': 'icon-tags'},
        # '-',
        # {'app': 'dpost', 'label': u'文章管理', 'icon': 'icon-edit'},
        '-',
        # 如果使用http这种绝对路径的话，菜单不会展开，且不会标记为active状态
        # {'url': '/admin/warehouse/test', 'label': u'这是一个测试', 'icon': 'icon-lock'},
        # '-',
        # {'label': u'运行爬虫', 'icon': 'icon-tags', 'models': (
        #     {'url': '/admin/warehouse/spiders', 'label': u'运行爬虫'},
        #     {'url': '/admin/warehouse/spiders2', 'label': u'运行爬虫2'},
        # )}
    )
}

CRONJOBS = [
    ('*/5 * * * *', "maxlead_site.cron.RunReview")
]
