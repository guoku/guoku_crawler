#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import orm, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, mapper
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, text,
                        Index)

from guoku_crawler.db import session


Base = declarative_base()


core_gkuser_groups = Table(
    'core_gkuser_groups', Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('group_id', Integer, ForeignKey('auth_group.id')),
    Column('gkuser_id', Integer, ForeignKey('core_gkuser.id'))
)


class AuthGroup(Base):
    __tablename__ = 'auth_group'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False, unique=True)
    users = relationship('CoreGkuser',
                         secondary=core_gkuser_groups,
                         backref='gk_groups')


class CoreGkuser(Base):
    __tablename__ = 'core_gkuser'

    id = Column(Integer, primary_key=True)
    password = Column(String(128), nullable=False)
    last_login = Column(DateTime, nullable=False)
    is_superuser = Column(Integer, nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    is_active = Column(Integer, nullable=False)
    is_admin = Column(Integer, nullable=False)
    date_joined = Column(DateTime, nullable=False)
    groups = relationship('AuthGroup',
                          secondary=core_gkuser_groups,
                          backref='gk_users'
                          )
    authorized_profile = relationship('CoreAuthorizedUserProfile',
                           backref=backref('user', uselist=False))


class CoreAuthorizedUserProfile(Base):
    __tablename__ = 'core_authorized_user_profile'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, unique=True)
    weixin_id = Column(String(255))
    weixin_nick = Column(String(255))
    weixin_qrcode_img = Column(String(255))
    author_website = Column(String(1024))
    weibo_id = Column(String(255))
    weibo_nick = Column(String(255))
    personal_domain_name = Column(String(64))
    weixin_openid = Column(String(255))
    rss_url = Column(String(255), nullable=True)
    gk_user = relationship('CoreGkuser',
                           backref=backref('profile', uselist=False))


class CoreArticle(Base):
    __tablename__ = 'core_article'
    (remove, draft, published) = range(3)

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(String, nullable=False)
    publish = Column(Integer, nullable=False)
    created_datetime = Column(DateTime, index=True)
    updated_datetime = Column(DateTime, index=True)
    cover = Column(String(255), nullable=True)
    showcover = Column(Integer, server_default=text("'0'"))
    read_count = Column(Integer, server_default=text("'0000000000'"))
    feed_read_count = Column(Integer, server_default=text("'0000000000'"))
    identity_code = Column(String(255))
    origin_url = Column(String(255)) #add by an
    source =Column(Integer,nullable=True, server_default=text("'0")) #add by an
    creator_id = Column(ForeignKey('core_gkuser.id'),
                        nullable=False, index=True)

    creator = relationship('CoreGkuser')


class CoreMedia(Base):
    __tablename__ = 'core_media'

    id = Column(Integer, primary_key=True)
    file_path = Column(String(200), nullable=False)
    content_type = Column(String(30), nullable=False)
    upload_datetime = Column(DateTime, index=True)
    creator_id = Column(Integer)
