#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import os

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

# System
DEBUG = True
CONNECTION_POOL = ''


def load_config():
    env_config = config_from_env('GK_')
    for k, v in env_config.items():
        setattr(sys.modules[__name__], k, v)
