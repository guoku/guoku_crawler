#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
from celery.schedules import crontab
from guoku_crawler.utils import config_from_env
from guoku_crawler.logging_conf import LOGGING
import logging.config
import logging


logging.config.dictConfig(LOGGING)
logger = logging.getLogger("request")

# Database
DATABASES = {
    'DB_NAME': 'core',
    'USER': 'guoku',
    'PASSWORD': 'guoku!@#',
    'HOST': '10.0.2.90',
    'PORT': '3306',
}

# Image
IMAGE_HOST = 'http://imgcdn.guoku.com/'
IMAGE_PATH = 'images/'
LOCAL_FILE_STORAGE = False
MEDIA_ROOT = ''
MOGILEFS_DOMAIN = 'prod'
MOGILEFS_TRACKERS = ['10.0.2.50:7001']
MOGILEFS_MEDIA_URL = 'images/'
FILE_UPLOAD_DIRECTORY_PERMISSIONS = ''
FILE_UPLOAD_PERMISSIONS = ''
MEDIA_URL = 'images/'
STATIC_URL = 'http://static.guoku.com/static/v4/dafb5059ae45f18b0eff711a38de3d59b95bad4c/'
DEFAULT_ARTICLE_COVER = "%s%s" % (
    STATIC_URL, 'images/article/default_cover.jpg'
)

# System
DEBUG = True
CONNECTION_POOL = ''
PHANTOM_SERVER = 'http://10.0.2.49:5000/'

# Celery
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERYD_CONCURRENCY = 2
CELERY_DISABLE_RATE_LIMITS = False
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_ALWAYS_EAGER = False
CELERY_ENABLE_UTC = False
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_IMPORTS = (
    'guoku_crawler.article',
)
CELERY_ROUTES = {
    'weixin.update_sogou_cookie':
        {
            'queue': 'cookies'
        }
}
CELERY_ANNOTATIONS = {
    'crawl_articles': {
        'rate_limit': '1/m',
    },
    'rss.crawl_list': {
        'rate_limit': '3/m',
    },
    'weixin.crawl_list': {
        'rate_limit': '1/m',
    },
    'weixin.crawl_weixin_article': {
        'rate_limit': '1/m',
    },
    'weixin.prepare_sogou_cookies': {
        'rate_limit': '1/m',
    },
    'weixin.update_sogou_cookie': {
        'rate_limit': '1/m',
    },
}
REQUEST_INTERVAL = 20
CELERYBEAT_SCHEDULE = {
    'crawl_all_articles': {
        'task': 'crawl_articles',
        'schedule': crontab(minute='*/10')
    },
}

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
    'drind1977@jourrapide.com',
    'duad1937@jourrapide.com',
    'alat1981@jourrapide.com',
    'paboy1973@superrito.com',
    'fuly1964@cuvox.de',
    'nelf1946@cuvox.de',
    'offam1939@cuvox.de',
    'norne1981@dayrep.com',
    'monce1934@teleworm.us',
    'overniseents93@einrot.com',
    'gavis1978@einrot.com',
    'harmuden1974@superrito.com',

    # local
    # 'saind1974@gustr.com',
    # 'forry1978@superrito.com',
    # 'wassiriour49@teleworm.us',

]
SOGOU_PASSWORD = 'guoku1@#'



def load_config():
    env_config = config_from_env('GK_')
    for k, v in env_config.items():
        setattr(sys.modules[__name__], k, v)


load_config()
