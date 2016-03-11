#!/usr/bin/env python
# -*- coding: utf-8 -*-
import redis
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from guoku_crawler import config
from guoku_crawler.config import DATABASES


SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://{USER}:{PASSWORD}@'
                           '{HOST}:{PORT}/{DB_NAME}?charset=utf8'.
                           format(**DATABASES))
engine = create_engine(
    SQLALCHEMY_DATABASE_URI)

session = Session(engine)

r = redis.Redis(host=config.CONFIG_REDIS_HOST,
                port=config.CONFIG_REDIS_PORT,
                db=config.CONFIG_REDIS_DB)
