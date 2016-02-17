#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session

from config import SQLALCHEMY_DATABASE_URI
from sqlalchemy import create_engine


engine = create_engine(
    SQLALCHEMY_DATABASE_URI)
session = Session(engine)
