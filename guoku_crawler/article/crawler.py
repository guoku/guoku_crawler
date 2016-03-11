#!/usr/bin/env python
# -*- coding: utf-8 -*-
from guoku_crawler.celery import RequestsTask, app
from guoku_crawler.db import session
from guoku_crawler.model_back import AuthGroup
from guoku_crawler.models import CoreGkuser
from guoku_crawler.models import CoreAuthorizedUserProfile as Profile
from guoku_crawler.article.weixin import crawl_weixin_list
from guoku_crawler.article.rss import crawl_rss_list


@app.task(base=RequestsTask, name='sogou.crawl_articles')
def crawl_articles():
    users = session.query(CoreGkuser).filter(
        CoreGkuser.authorized_profile.any(
            Profile.weixin_id.isnot(None) or Profile.rss_url.isnot(None)),
        CoreGkuser.groups.any(AuthGroup.name == 'Author')
    ).all()
    for user in users:
        crawl_user_articles(user.profile.id)


def crawl_user_articles(authorized_user_id):
    # crawl rss article if user has rss url,
    # else crawl weixin article from sogou.
    authorized_user = session.query(Profile).get(authorized_user_id)

    if authorized_user.rss_url:
        crawl_rss_list.delay(authorized_user_id)
    else:
        crawl_weixin_list.delay(authorized_user_id)
