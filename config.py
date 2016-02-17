#!/usr/bin/env python
# -*- coding: utf-8 -*-


DATABASES = {
    'DB_NAME': 'core',
    'USER': 'root',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': '3306',
}
echo = ''
CONNECTION_POOL = ''

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}?charset=utf8'.format_map(DATABASES)

