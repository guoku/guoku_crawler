#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from guoku_crawler.utils import config_from_env


# Database
DATABASES = {
    'DB_NAME': 'core',
    'USER': 'root',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': '3306',
}

# Image
# IMAGE_LOCAL = False
# IMAGE_HOST = 'http://imgcdn.guoku.com/'
IMAGE_LOCAL = True
IMAGE_HOST = 'http://imgcdn.guoku.com/'
IMAGE_PATH = 'images/'
LOCAL_FILE_STORAGE = True
MEDIA_ROOT = ''

# System
DEBUG = True
CONNECTION_POOL = ''
PHANTOM_SERVER = 'http://192.168.99.100:5000/'

# Celery
CELERY = dict(
    BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0',
    CELERYD_CONCURRENCY=3,
    CELERY_DISABLE_RATE_LIMITS=False,
    CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    CELERY_ALWAYS_EAGER=True,
    CELERY_IMPORTS=(
        # 'guoku_crawler.article.tasks',
        # 'guoku_crawler.article.weixin',
                    ),
)
REQUEST_INTERVAL = 60

# Redis
CONFIG_REDIS_HOST = 'localhost'
CONFIG_REDIS_PORT = 6379
CONFIG_REDIS_DB = 0

# Sogou
SOGOU_USERS = [
    'waser1959@gustr.com',
    'asortafairytale@fleckens.hu',
    'adisaid@jourrapide.com',
    'rathe1981@rhyta.com',
    'andurn@fleckens.hu',
    'sanyuanmilk@fleckens.hu',
    'yundaexpress@rhyta.com',
    'sunstarorabreathfine@jourrapide.com',
    'indonesiamandheling@einrot.com',
    'charlottewalkforshame@dayrep.com',
    'shoemah55@superrito.com',
    'monan1977@fleckens.hu',
    'obsomed1977@jourrapide.com',
    'finighboy78@superrito.com',
    'artimessill1959@einrot.com',
    'suildrued41@dayrep.com',
    'ater1954@teleworm.us',
    'duad1937@jourrapide.com',
    'drecur44@superrito.com',
    'paboy1973@superrito.com',
]
SOGOU_PASSWORD = 'guoku1@#'


def load_config():
    env_config = config_from_env('GK_')
    for k, v in env_config.items():
        setattr(sys.modules[__name__], k, v)
