#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from guoku_crawler.config import DATABASES


SQLALCHEMY_DATABASE_URI = ('mysql+pymysql://{USER}:{PASSWORD}@'
                           '{HOST}:{PORT}/{DB_NAME}?charset=utf8'.
                           format_map(DATABASES))
engine = create_engine(
    SQLALCHEMY_DATABASE_URI)

session = Session(engine)
