#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime

from sqlalchemy import or_

from guoku_crawler.db import session
from guoku_crawler.celery import RequestsTask, app
from guoku_crawler.article.rss import crawl_rss_list
from guoku_crawler.article.weixin import crawl_weixin_list, prepare_sogou_cookies
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

def get_auth_users():
    users = session.query(CoreGkuser).filter(
        CoreGkuser.authorized_profile.any(or_(
            Profile.weixin_id.isnot(None), Profile.rss_url.isnot(None))),
        CoreGkuser.groups.any(AuthGroup.name == 'Author')
    ).all()
    return users

AUTH_USER_LIST = get_auth_users()


@app.task(base=RequestsTask, name='crawl_articles')
def crawl_articles():

    global AUTH_USER_LIST
    if not AUTH_USER_LIST:
        AUTH_USER_LIST = get_auth_users()
    crawl_user_articles(AUTH_USER_LIST.pop().profile.id)



def crawl_user_articles(authorized_user_id):
    # crawl rss article if user has rss url,
    # else crawl weixin article from sogou.
    authorized_user = session.query(Profile).get(authorized_user_id)

    if authorized_user.rss_url:
        crawl_rss_list.delay(authorized_user_id)
    else:
        crawl_weixin_list.delay(authorized_user_id)





if __name__ == '__main__':
    # prepare_sogou_cookies()
    # crawl_user_articles(25)
    for i in range(10):
        crawl_articles()
    print '*'*100




