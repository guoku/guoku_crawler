#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sqlalchemy import BigInteger, Column, Date, DateTime, Float, ForeignKey, Index, Integer, Numeric, SmallInteger, String, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class AuthGroup(Base):
    __tablename__ = 'auth_group'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False, unique=True)


class AuthGroupPermission(Base):
    __tablename__ = 'auth_group_permissions'
    __table_args__ = (
        Index('group_id', 'group_id', 'permission_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    group_id = Column(ForeignKey('auth_group.id'), nullable=False, index=True)
    permission_id = Column(ForeignKey('auth_permission.id'), nullable=False, index=True)

    group = relationship('AuthGroup')
    permission = relationship('AuthPermission')


class AuthPermission(Base):
    __tablename__ = 'auth_permission'
    __table_args__ = (
        Index('content_type_id', 'content_type_id', 'codename', unique=True),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    content_type_id = Column(ForeignKey('django_content_type.id'), nullable=False, index=True)
    codename = Column(String(100), nullable=False)

    content_type = relationship('DjangoContentType')


class CaptchaCaptchastore(Base):
    __tablename__ = 'captcha_captchastore'

    id = Column(Integer, primary_key=True)
    challenge = Column(String(32), nullable=False)
    response = Column(String(32), nullable=False)
    hashkey = Column(String(40), nullable=False, unique=True)
    expiration = Column(DateTime, nullable=False)


class CeleryTaskmeta(Base):
    __tablename__ = 'celery_taskmeta'

    id = Column(Integer, primary_key=True)
    task_id = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False)
    result = Column(String)
    date_done = Column(DateTime, nullable=False)
    traceback = Column(String)
    hidden = Column(Integer, nullable=False, index=True)
    meta = Column(String)


class CeleryTasksetmeta(Base):
    __tablename__ = 'celery_tasksetmeta'

    id = Column(Integer, primary_key=True)
    taskset_id = Column(String(255), nullable=False, unique=True)
    result = Column(String, nullable=False)
    date_done = Column(DateTime, nullable=False)
    hidden = Column(Integer, nullable=False, index=True)


class CoreArticle(Base):
    __tablename__ = 'core_article'

    id = Column(Integer, primary_key=True)
    creator_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String, nullable=False)
    publish = Column(Integer, nullable=False)
    created_datetime = Column(DateTime, index=True)
    updated_datetime = Column(DateTime, index=True)
    cover = Column(String(255), nullable=False)
    showcover = Column(Integer, server_default=text("'0'"))
    read_count = Column(Integer, server_default=text("'0000000000'"))
    feed_read_count = Column(Integer, server_default=text("'0000000000'"))
    cleaned_title = Column(String(255))

    creator = relationship('CoreGkuser')


class CoreArticleDig(Base):
    __tablename__ = 'core_article_dig'
    __table_args__ = (
        Index('article_id', 'article_id', 'user_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    created_time = Column(DateTime, nullable=False, index=True)


class CoreArticleRelatedEntity(Base):
    __tablename__ = 'core_article_related_entities'
    __table_args__ = (
        Index('article_id', 'article_id', 'entity_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, nullable=False)
    entity_id = Column(Integer, nullable=False, index=True)


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

    user = relationship('CoreGkuser')


class CoreBanner(Base):
    __tablename__ = 'core_banner'

    id = Column(Integer, primary_key=True)
    content_type = Column(String(64), nullable=False)
    key = Column(String(1024), nullable=False)
    image = Column(String(64), nullable=False)
    created_time = Column(DateTime, nullable=False, index=True)
    updated_time = Column(DateTime, nullable=False, index=True)


class CoreBrand(Base):
    __tablename__ = 'core_brand'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    alias = Column(String(100))
    icon = Column(String(255))
    company = Column(String(100))
    website = Column(String(255))
    national = Column(String(100))
    intro = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    created_date = Column(DateTime, nullable=False, index=True)
    tmall_link = Column(String(255))


class CoreBuyLink(Base):
    __tablename__ = 'core_buy_link'

    id = Column(Integer, primary_key=True)
    entity_id = Column(ForeignKey('core_entity.id'), nullable=False, index=True)
    origin_id = Column(String(100), nullable=False)
    origin_source = Column(String(255), nullable=False)
    cid = Column(String(255))
    link = Column(String(255), nullable=False)
    price = Column(Numeric(20, 2), nullable=False)
    volume = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)
    default = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
    shop_link = Column(String(255))
    seller = Column(String(255))
    foreign_price = Column(Numeric(20, 2))

    entity = relationship('CoreEntity')


class CoreCategory(Base):
    __tablename__ = 'core_category'

    id = Column(Integer, primary_key=True)
    title = Column(String(128), nullable=False, index=True)
    status = Column(Integer, nullable=False, index=True)
    cover = Column(String(255), nullable=False)


class CoreEditorRecommendation(Base):
    __tablename__ = 'core_editor_recommendation'

    id = Column(Integer, primary_key=True)
    image = Column(String(255), nullable=False)
    link = Column(String(255), nullable=False)
    created_time = Column(DateTime, nullable=False, index=True)
    updated_time = Column(DateTime, nullable=False, index=True)


class CoreEdm(Base):
    __tablename__ = 'core_edm'

    id = Column(Integer, primary_key=True)
    title = Column(String(255, 'utf8mb4_unicode_ci'), nullable=False)
    created = Column(DateTime, nullable=False)
    modified = Column(DateTime, nullable=False)
    status = Column(Integer, nullable=False)
    publish_time = Column(DateTime, nullable=False)
    cover_image = Column(String(255, 'utf8mb4_unicode_ci'), nullable=False)
    cover_hype_link = Column(String(255, 'utf8mb4_unicode_ci'), nullable=False)
    cover_description = Column(String(collation='utf8mb4_unicode_ci'), nullable=False)
    sd_template_invoke_name = Column(String(255, 'utf8mb4_unicode_ci'))
    display = Column(Integer, nullable=False)
    sd_task_id = Column(String(45, 'utf8mb4_unicode_ci'))


class CoreEdmSelectionArticle(Base):
    __tablename__ = 'core_edm_selection_articles'
    __table_args__ = (
        Index('edm_id', 'edm_id', 'selection_article_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    edm_id = Column(Integer, nullable=False, index=True)
    selection_article_id = Column(Integer, nullable=False, index=True)


class CoreEntity(Base):
    __tablename__ = 'core_entity'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), index=True)
    entity_hash = Column(String(32), nullable=False, unique=True)
    category_id = Column(ForeignKey('core_sub_category.id'), nullable=False, index=True)
    brand = Column(String(256), nullable=False)
    title = Column(String(256), nullable=False)
    intro = Column(String, nullable=False)
    rate = Column(Numeric(3, 2), nullable=False)
    price = Column(Numeric(20, 2), nullable=False, index=True)
    mark = Column(Integer, nullable=False, index=True)
    images = Column(String, nullable=False)
    created_time = Column(DateTime, nullable=False, index=True)
    updated_time = Column(DateTime, nullable=False, index=True)
    status = Column(Integer, nullable=False)

    category = relationship('CoreSubCategory')
    user = relationship('CoreGkuser')


class CoreEntityLike(Base):
    __tablename__ = 'core_entity_like'
    __table_args__ = (
        Index('entity_id', 'entity_id', 'user_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    entity_id = Column(ForeignKey('core_entity.id'), nullable=False, index=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    created_time = Column(DateTime, nullable=False, index=True)

    entity = relationship('CoreEntity')
    user = relationship('CoreGkuser')


class CoreEntityTag(Base):
    __tablename__ = 'core_entity_tag'
    __table_args__ = (
        Index('entity_id', 'entity_id', 'user_id', 'tag_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    entity_id = Column(ForeignKey('core_entity.id'), nullable=False, index=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    tag_id = Column(ForeignKey('core_tag.id'), nullable=False, index=True)
    created_time = Column(DateTime, nullable=False, index=True)
    last_tagged_time = Column(DateTime, nullable=False, index=True)

    entity = relationship('CoreEntity')
    tag = relationship('CoreTag')
    user = relationship('CoreGkuser')


class CoreEvent(Base):
    __tablename__ = 'core_event'

    id = Column(Integer, primary_key=True)
    title = Column(String(30), nullable=False)
    tag = Column(String(30), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    status = Column(Integer, nullable=False)
    created_datetime = Column(DateTime, nullable=False, index=True)
    toptag = Column(String(30), nullable=False)


class CoreEventStatu(CoreEvent):
    __tablename__ = 'core_event_status'

    event_id = Column(ForeignKey('core_event.id'), primary_key=True)
    is_published = Column(Integer, nullable=False)
    is_top = Column(Integer, nullable=False)


class CoreEventBanner(Base):
    __tablename__ = 'core_event_banner'

    id = Column(Integer, primary_key=True)
    image = Column(String(255), nullable=False)
    banner_type = Column(Integer, nullable=False)
    user_id = Column(String(30))
    link = Column(String(255))
    created_time = Column(DateTime, nullable=False, index=True)
    updated_time = Column(DateTime, nullable=False, index=True)
    background_image = Column(String(255))
    background_color = Column(String(14), server_default=text("'fff'"))


class CoreEventRelatedArticle(Base):
    __tablename__ = 'core_event_related_articles'
    __table_args__ = (
        Index('event_id', 'event_id', 'article_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, nullable=False)
    article_id = Column(Integer, nullable=False, index=True)


class CoreFriendlyLink(Base):
    __tablename__ = 'core_friendly_link'

    id = Column(Integer, primary_key=True)
    name = Column(String(64, 'utf8mb4_unicode_ci'), nullable=False)
    link = Column(String(255, 'utf8mb4_unicode_ci'), nullable=False)
    link_category = Column(String(64, 'utf8mb4_unicode_ci'), nullable=False)
    position = Column(Integer)
    logo = Column(String(255, 'utf8mb4_unicode_ci'))
    status = Column(Integer, nullable=False)


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


class CoreGkuserGroup(Base):
    __tablename__ = 'core_gkuser_groups'
    __table_args__ = (
        Index('gkuser_id', 'gkuser_id', 'group_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    gkuser_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    group_id = Column(ForeignKey('auth_group.id'), nullable=False, index=True)

    gkuser = relationship('CoreGkuser')
    group = relationship('AuthGroup')


class CoreGkuserUserPermission(Base):
    __tablename__ = 'core_gkuser_user_permissions'
    __table_args__ = (
        Index('gkuser_id', 'gkuser_id', 'permission_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    gkuser_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    permission_id = Column(ForeignKey('auth_permission.id'), nullable=False, index=True)

    gkuser = relationship('CoreGkuser')
    permission = relationship('AuthPermission')


class CoreMedia(Base):
    __tablename__ = 'core_media'

    id = Column(Integer, primary_key=True)
    file_path = Column(String(200), nullable=False)
    content_type = Column(String(30), nullable=False)
    upload_datetime = Column(DateTime, index=True)
    creator_id = Column(Integer)


class CoreNote(Base):
    __tablename__ = 'core_note'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    entity_id = Column(ForeignKey('core_entity.id'), nullable=False, index=True)
    note = Column(String)
    post_time = Column(DateTime, nullable=False, index=True)
    updated_time = Column(DateTime, nullable=False, index=True)
    status = Column(Integer, nullable=False)

    entity = relationship('CoreEntity')
    user = relationship('CoreGkuser')


class CoreNoteComment(Base):
    __tablename__ = 'core_note_comment'

    id = Column(Integer, primary_key=True)
    note_id = Column(ForeignKey('core_note.id'), nullable=False, index=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    content = Column(String, nullable=False)
    replied_comment_id = Column(Integer)
    replied_user_id = Column(Integer)
    post_time = Column(DateTime, nullable=False, index=True)

    note = relationship('CoreNote')
    user = relationship('CoreGkuser')


class CoreNotePoke(Base):
    __tablename__ = 'core_note_poke'
    __table_args__ = (
        Index('note_id', 'note_id', 'user_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    note_id = Column(ForeignKey('core_note.id'), nullable=False, index=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    created_time = Column(DateTime, nullable=False, index=True)

    note = relationship('CoreNote')
    user = relationship('CoreGkuser')


class CoreSdAddressList(Base):
    __tablename__ = 'core_sd_address_list'

    id = Column(Integer, primary_key=True)
    address = Column(String(45), nullable=False, unique=True)
    name = Column(String(45), nullable=False)
    description = Column(String(45), nullable=False)
    created = Column(DateTime, nullable=False)
    members_count = Column(Integer, nullable=False)


class CoreSearchHistory(Base):
    __tablename__ = 'core_search_history'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), index=True)
    key_words = Column(String(255), nullable=False)
    search_time = Column(DateTime)
    ip = Column(String(45))
    agent = Column(String(255))

    user = relationship('CoreGkuser')


class CoreSelectionArticle(Base):
    __tablename__ = 'core_selection_article'

    id = Column(Integer, primary_key=True)
    article_id = Column(ForeignKey('core_article.id'), nullable=False, index=True)
    is_published = Column(Integer, nullable=False)
    pub_time = Column(DateTime, index=True)
    create_time = Column(DateTime, nullable=False, index=True)

    article = relationship('CoreArticle')


class CoreSelectionEntity(Base):
    __tablename__ = 'core_selection_entity'

    id = Column(Integer, primary_key=True)
    entity_id = Column(ForeignKey('core_entity.id'), nullable=False, unique=True)
    is_published = Column(Integer, nullable=False)
    pub_time = Column(DateTime, nullable=False, index=True)

    entity = relationship('CoreEntity')


class CoreShowBanner(Base):
    __tablename__ = 'core_show_banner'

    id = Column(Integer, primary_key=True)
    banner_id = Column(ForeignKey('core_banner.id'), nullable=False, unique=True)
    created_time = Column(DateTime, nullable=False, index=True)

    banner = relationship('CoreBanner')


class CoreShowEditorRecommendation(Base):
    __tablename__ = 'core_show_editor_recommendation'

    id = Column(Integer, primary_key=True)
    recommendation_id = Column(ForeignKey('core_editor_recommendation.id'), nullable=False, unique=True)
    event_id = Column(ForeignKey('core_event.id'), index=True)
    position = Column(Integer, nullable=False)
    created_time = Column(DateTime, nullable=False, index=True)
    section = Column(String(64), nullable=False, server_default=text("'entity'"))

    event = relationship('CoreEvent')
    recommendation = relationship('CoreEditorRecommendation')


class CoreShowEventBanner(Base):
    __tablename__ = 'core_show_event_banner'

    id = Column(Integer, primary_key=True)
    banner_id = Column(ForeignKey('core_event_banner.id'), nullable=False, unique=True)
    event_id = Column(ForeignKey('core_event.id'), index=True)
    position = Column(Integer, nullable=False)
    created_time = Column(DateTime, nullable=False, index=True)

    banner = relationship('CoreEventBanner')
    event = relationship('CoreEvent')


class CoreSidebarBanner(Base):
    __tablename__ = 'core_sidebar_banner'

    id = Column(Integer, primary_key=True)
    image = Column(String(255, 'utf8mb4_unicode_ci'), nullable=False)
    created_time = Column(DateTime, nullable=False, index=True)
    updated_time = Column(DateTime, nullable=False, index=True)
    link = Column(String(255, 'utf8mb4_unicode_ci'), nullable=False)
    position = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)


class CoreSinaToken(Base):
    __tablename__ = 'core_sina_token'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, unique=True)
    sina_id = Column(String(64), index=True)
    screen_name = Column(String(64), index=True)
    access_token = Column(String(255), index=True)
    create_time = Column(DateTime, nullable=False)
    expires_in = Column(Integer, nullable=False)
    updated_time = Column(DateTime)

    user = relationship('CoreGkuser')


class CoreSubCategory(Base):
    __tablename__ = 'core_sub_category'

    id = Column(Integer, primary_key=True)
    group_id = Column(ForeignKey('core_category.id'), nullable=False, index=True)
    title = Column(String(128), nullable=False, index=True)
    alias = Column(String(128), nullable=False)
    icon = Column(String(64), index=True)
    status = Column(Integer, nullable=False, index=True)

    group = relationship('CoreCategory')


class CoreTag(Base):
    __tablename__ = 'core_tag'
    __table_args__ = (
        Index('creator_id', 'creator_id', 'tag', unique=True),
    )

    id = Column(Integer, primary_key=True)
    tag = Column(String(128), nullable=False, unique=True)
    tag_hash = Column(String(32), nullable=False, unique=True)
    status = Column(Integer, nullable=False, index=True)
    creator_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    created_time = Column(DateTime, nullable=False, index=True)
    updated_time = Column(DateTime, nullable=False, index=True)

    creator = relationship('CoreGkuser')


class CoreTaobaoToken(Base):
    __tablename__ = 'core_taobao_token'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, unique=True)
    taobao_id = Column(String(64), index=True)
    screen_name = Column(String(64), index=True)
    access_token = Column(String(255), index=True)
    refresh_token = Column(String(255), index=True)
    create_time = Column(DateTime, nullable=False)
    expires_in = Column(Integer, nullable=False)
    re_expires_in = Column(Integer, nullable=False)
    updated_time = Column(DateTime)
    open_uid = Column(String(64))
    isv_uid = Column(String(64))

    user = relationship('CoreGkuser')


class CoreTestEventBanner(Base):
    __tablename__ = 'core_test_event_banner'

    id = Column(Integer, primary_key=True)
    image = Column(String(255), nullable=False)
    banner_type = Column(Integer, nullable=False)
    user_id = Column(String(30))
    link = Column(String(255))
    background_image = Column(String(255))
    background_color = Column(String(14))
    created_time = Column(DateTime, nullable=False, index=True)
    updated_time = Column(DateTime, nullable=False, index=True)


class CoreUserFollow(Base):
    __tablename__ = 'core_user_follow'
    __table_args__ = (
        Index('follower_id', 'follower_id', 'followee_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    follower_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    followee_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    followed_time = Column(DateTime, nullable=False, index=True)

    followee = relationship('CoreGkuser', primaryjoin='CoreUserFollow.followee_id == CoreGkuser.id')
    follower = relationship('CoreGkuser', primaryjoin='CoreUserFollow.follower_id == CoreGkuser.id')


class CoreUserProfile(Base):
    __tablename__ = 'core_user_profile'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, unique=True)
    nickname = Column(String(64), nullable=False, index=True)
    location = Column(String(32))
    city = Column(String(32))
    gender = Column(String(2), nullable=False)
    bio = Column(String(1024))
    website = Column(String(1024))
    avatar = Column(String(255), nullable=False)
    email_verified = Column(Integer, nullable=False)
    weixin_id = Column(String(255))
    weixin_nick = Column(String(255))
    weixin_qrcode_img = Column(String(255))
    author_website = Column(String(1024))
    weibo_id = Column(String(255))
    weibo_nick = Column(String(255))

    user = relationship('CoreGkuser')


class CoreWechatToken(Base):
    __tablename__ = 'core_wechat_token'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True)
    unionid = Column(String(255), nullable=False, index=True)
    nickname = Column(String(255), nullable=False)
    updated_time = Column(DateTime)


class DjangoContentType(Base):
    __tablename__ = 'django_content_type'
    __table_args__ = (
        Index('app_label', 'app_label', 'model', unique=True),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    app_label = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)


class DjangoMigration(Base):
    __tablename__ = 'django_migrations'

    id = Column(Integer, primary_key=True)
    app = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    applied = Column(DateTime, nullable=False)


class DjceleryCrontabschedule(Base):
    __tablename__ = 'djcelery_crontabschedule'

    id = Column(Integer, primary_key=True)
    minute = Column(String(64), nullable=False)
    hour = Column(String(64), nullable=False)
    day_of_week = Column(String(64), nullable=False)
    day_of_month = Column(String(64), nullable=False)
    month_of_year = Column(String(64), nullable=False)


class DjceleryIntervalschedule(Base):
    __tablename__ = 'djcelery_intervalschedule'

    id = Column(Integer, primary_key=True)
    every = Column(Integer, nullable=False)
    period = Column(String(24), nullable=False)


class DjceleryPeriodictask(Base):
    __tablename__ = 'djcelery_periodictask'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    task = Column(String(200), nullable=False)
    interval_id = Column(ForeignKey('djcelery_intervalschedule.id'), index=True)
    crontab_id = Column(ForeignKey('djcelery_crontabschedule.id'), index=True)
    args = Column(String, nullable=False)
    kwargs = Column(String, nullable=False)
    queue = Column(String(200))
    exchange = Column(String(200))
    routing_key = Column(String(200))
    expires = Column(DateTime)
    enabled = Column(Integer, nullable=False)
    last_run_at = Column(DateTime)
    total_run_count = Column(Integer, nullable=False)
    date_changed = Column(DateTime, nullable=False)
    description = Column(String, nullable=False)

    crontab = relationship('DjceleryCrontabschedule')
    interval = relationship('DjceleryIntervalschedule')


class DjceleryPeriodictask(Base):
    __tablename__ = 'djcelery_periodictasks'

    ident = Column(SmallInteger, primary_key=True)
    last_update = Column(DateTime, nullable=False)


class DjceleryTaskstate(Base):
    __tablename__ = 'djcelery_taskstate'

    id = Column(Integer, primary_key=True)
    state = Column(String(64), nullable=False, index=True)
    task_id = Column(String(36), nullable=False, unique=True)
    name = Column(String(200), index=True)
    tstamp = Column(DateTime, nullable=False, index=True)
    args = Column(String)
    kwargs = Column(String)
    eta = Column(DateTime)
    expires = Column(DateTime)
    result = Column(String)
    traceback = Column(String)
    runtime = Column(Float(asdecimal=True))
    retries = Column(Integer, nullable=False)
    worker_id = Column(ForeignKey('djcelery_workerstate.id'), index=True)
    hidden = Column(Integer, nullable=False, index=True)

    worker = relationship('DjceleryWorkerstate')


class DjceleryWorkerstate(Base):
    __tablename__ = 'djcelery_workerstate'

    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), nullable=False, unique=True)
    last_heartbeat = Column(DateTime, index=True)


class FetchSogoucooky(Base):
    __tablename__ = 'fetch_sogoucookies'

    id = Column(Integer, primary_key=True)
    cookie_string = Column(String, nullable=False)
    created_time = Column(DateTime, nullable=False)


class MobileApp(Base):
    __tablename__ = 'mobile_apps'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    app_name = Column(String(30), nullable=False, unique=True)
    desc = Column(String, nullable=False)
    api_key = Column(String(64), nullable=False)
    api_secret = Column(String(32), nullable=False)
    created_time = Column(DateTime, nullable=False)

    user = relationship('CoreGkuser')


class MobileLaunchboard(Base):
    __tablename__ = 'mobile_launchboard'

    id = Column(Integer, primary_key=True)
    launchImage = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=False)
    status = Column(Integer, nullable=False)
    action = Column(String(255), nullable=False)
    created_datetime = Column(DateTime, nullable=False, index=True)


class MobileSessionKey(Base):
    __tablename__ = 'mobile_session_key'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    app_id = Column(ForeignKey('mobile_apps.id'), nullable=False, index=True)
    session_key = Column(String(64), nullable=False, unique=True)
    create_time = Column(DateTime, nullable=False)

    app = relationship('MobileApp')
    user = relationship('CoreGkuser')


class NotificationsJpushtoken(Base):
    __tablename__ = 'notifications_jpushtoken'

    id = Column(Integer, primary_key=True)
    rid = Column(String(128), nullable=False)
    user_id = Column(ForeignKey('core_gkuser.id'), index=True)
    model = Column(String(100), nullable=False)
    version = Column(String(10), nullable=False)
    updated_time = Column(DateTime, nullable=False)

    user = relationship('CoreGkuser')


class NotificationsNotification(Base):
    __tablename__ = 'notifications_notification'

    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)
    recipient_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    unread = Column(Integer, nullable=False)
    actor_content_type_id = Column(ForeignKey('django_content_type.id'), nullable=False, index=True)
    actor_object_id = Column(String(255), nullable=False, index=True)
    verb = Column(String(255), nullable=False)
    description = Column(String)
    target_content_type_id = Column(ForeignKey('django_content_type.id'), index=True)
    target_object_id = Column(String(255))
    action_object_content_type_id = Column(ForeignKey('django_content_type.id'), index=True)
    action_object_object_id = Column(String(255))
    timestamp = Column(DateTime, nullable=False, index=True)
    public = Column(Integer, nullable=False)

    action_object_content_type = relationship('DjangoContentType', primaryjoin='NotificationsNotification.action_object_content_type_id == DjangoContentType.id')
    actor_content_type = relationship('DjangoContentType', primaryjoin='NotificationsNotification.actor_content_type_id == DjangoContentType.id')
    recipient = relationship('CoreGkuser')
    target_content_type = relationship('DjangoContentType', primaryjoin='NotificationsNotification.target_content_type_id == DjangoContentType.id')


class ReportReport(Base):
    __tablename__ = 'report_report'

    id = Column(Integer, primary_key=True)
    reporter_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    comment = Column(String, nullable=False)
    content_type_id = Column(ForeignKey('django_content_type.id'), nullable=False, index=True)
    object_id = Column(Integer, nullable=False)
    created_datetime = Column(DateTime, nullable=False, index=True)
    type = Column(SmallInteger, nullable=False)
    progress = Column(SmallInteger, nullable=False, server_default=text("'2'"))

    content_type = relationship('DjangoContentType')
    reporter = relationship('CoreGkuser')


class ReportSelection(Base):
    __tablename__ = 'report_selection'

    id = Column(Integer, primary_key=True)
    selected_total = Column(Integer, nullable=False)
    pub_date = Column(Date, nullable=False, index=True)
    like_total = Column(Integer, server_default=text("'0'"))


class SellerSellerProfile(Base):
    __tablename__ = 'seller_seller_profile'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), unique=True)
    shop_title = Column(String(255), nullable=False, index=True)
    shop_link = Column(String(255), nullable=False)
    seller_name = Column(String(255), nullable=False, index=True)
    shop_desc = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    logo = Column(String(255), nullable=False)
    category_logo = Column(String(255), nullable=False)
    business_section = Column(Integer, nullable=False)
    gk_stars = Column(Integer, nullable=False)
    related_article_id = Column(ForeignKey('core_article.id'), unique=True)

    related_article = relationship('CoreArticle')
    user = relationship('CoreGkuser')


class TagContentTag(Base):
    __tablename__ = 'tag_content_tags'
    __table_args__ = (
        Index('tag_id', 'tag_id', 'creator_id', 'target_content_type_id', 'target_object_id', unique=True),
    )

    id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, nullable=False, index=True)
    creator_id = Column(Integer, nullable=False, index=True)
    target_content_type_id = Column(Integer, index=True)
    target_object_id = Column(BigInteger)
    created_datetime = Column(DateTime, nullable=False, index=True)


class TagTag(Base):
    __tablename__ = 'tag_tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(100, 'utf8mb4_unicode_ci'), nullable=False, unique=True)
    hash = Column(String(32, 'utf8mb4_unicode_ci'), nullable=False, unique=True)
    status = Column(Integer, nullable=False)
    image = Column(String(255, 'utf8mb4_unicode_ci'))
    isTopArticleTag = Column(Integer, nullable=False, server_default=text("'0'"))


class WechatRobot(Base):
    __tablename__ = 'wechat_robots'

    id = Column(Integer, primary_key=True)
    accept = Column(String(255), nullable=False, unique=True)
    type = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    created_datetime = Column(DateTime, nullable=False, index=True)


class WechatToken(Base):
    __tablename__ = 'wechat_token'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('core_gkuser.id'), nullable=False, index=True)
    open_id = Column(String(255), nullable=False)
    joined_datetime = Column(DateTime, nullable=False, index=True)

    user = relationship('CoreGkuser')
