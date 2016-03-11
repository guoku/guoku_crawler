#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urlparse import urljoin

from guoku_crawler.celery import RequestsTask, app
from guoku_crawler.db import session
from guoku_crawler.models import CoreAuthorizedUserProfile as Profile


@app.task(base=RequestsTask, name='sogou.weixin.crawl_list')
def crawl_rss_list(authorized_user_id):
    authorized_user = session.query(Profile).get(authorized_user_id)
    blog_address = authorized_user.rss_url
    rss_url = urljoin(blog_address, '?feed=rss2')


