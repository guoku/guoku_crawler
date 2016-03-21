#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import csv

from sqlalchemy import or_

from guoku_crawler.db import session
from guoku_crawler.config import NICKNAME_DICT
from guoku_crawler.celery import RequestsTask, app
from guoku_crawler.article.rss import crawl_rss_list
from guoku_crawler.article.weixin import crawl_weixin_list
from guoku_crawler.models import CoreGkuser, AuthGroup, CoreArticle
from guoku_crawler.models import CoreAuthorizedUserProfile as Profile


yesterday_start = datetime.datetime.combine(
    datetime.date.today() - datetime.timedelta(days=1),
    datetime.time.min
)
today_start = datetime.datetime.combine(
    datetime.date.today(),
    datetime.time.min
)


@app.task(base=RequestsTask, name='crawl_articles')
def crawl_articles():
    users = get_auth_users()
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


def get_auth_users():
    users = session.query(CoreGkuser).filter(
        CoreGkuser.authorized_profile.any(or_(
            Profile.weixin_id.isnot(None), Profile.rss_url.isnot(None))),
        CoreGkuser.groups.any(AuthGroup.name == 'Author')
    ).all()
    return users


def get_user_update_num(user):
    authorized_user = session.query(Profile).get(user.profile.id)
    yesterday_finish = len(session.query(CoreArticle).filter(
        CoreArticle.updated_datetime >= yesterday_start,
        CoreArticle.updated_datetime < today_start,
        CoreArticle.creator_id == authorized_user.user.id).all())
    return yesterday_finish


@app.task(base=RequestsTask, name='crawl_result_analysis')
def get_yesterday_detail():
    users = get_auth_users()
    yesterday_detail = {}
    for user in users:
        yesterday_detail[NICKNAME_DICT[
            user.profile.personal_domain_name]] = get_user_update_num(user)
    yesterday_detail['all'] = sum(yesterday_detail.values())
    with open('logs/crawlResults.csv', 'a') as f:
        f = csv.writer(f)
        f.writerow(('起始时间', '结束时间'))
        f.writerow((str(yesterday_start), str(today_start)))
        f.writerow(('作者', '文章数'))
        f.writerows(yesterday_detail.items())
        f.writerow(('', ''))
    return yesterday_detail
