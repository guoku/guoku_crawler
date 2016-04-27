#!/usr/bin/env python
# -*- coding: utf-8 -*-
from hashlib import md5

import datetime
from bs4 import BeautifulSoup
from dateutil import parser
from guoku_crawler.article.weixin import caculate_identity_code
from sqlalchemy.orm.exc import NoResultFound

from guoku_crawler import config
from guoku_crawler.article.client import RSSClient
from guoku_crawler.celery import RequestsTask, app
from guoku_crawler.common.image import fetch_image
from guoku_crawler.db import session
from guoku_crawler.models import CoreArticle
from guoku_crawler.models import CoreAuthorizedUserProfile as Profile
from guoku_crawler.config import logger


rss_client = RSSClient()
image_host = getattr(config, 'IMAGE_HOST', None)


@app.task(base=RequestsTask, name='rss.crawl_list')
def crawl_rss_list(authorized_user_id, page=1):
    authorized_user = session.query(Profile).get(authorized_user_id)
    blog_address = authorized_user.rss_url
    params = {
        'feed': 'rss2',
        'paged': page
    }

    go_next = True
    response = rss_client.get(blog_address,
                              params=params
                              )
    xml_content = BeautifulSoup(response.utf8_content, 'xml')
    # REFACTOR HERE
    # TODO :  parser
    item_list = xml_content.find_all('item')
    for item in item_list:
        title = item.title.text
        created_datetime = parser.parse(item.pubDate.text)
        created_datetime = datetime.datetime.strptime(str(created_datetime.date()), '%Y-%m-%d')
        identity_code = caculate_identity_code(title, created_datetime, authorized_user.user.id)
        try:
            article = session.query(CoreArticle).filter_by(
                identity_code=identity_code,
                creator=authorized_user.user
            ).one()
            go_next = False
            logger.info('some items on the page already exists in db; '
                         'no need to go to next page')
        except NoResultFound:

            article = CoreArticle(
                creator=authorized_user.user,
                identity_code=identity_code,
                title=title,
                content=item.encoded.string if item.encoded else item.description.text,
                updated_datetime=datetime.datetime.now(),
                created_datetime=parser.parse(item.pubDate.text),
                publish=CoreArticle.published,
                cover=config.DEFAULT_ARTICLE_COVER
            )
            session.add(article)
            session.commit()
            crawl_rss_images.delay(article.content, article.id)

        logger.info('article %s finished.', article.id)

    if len(item_list) < 10:
        go_next = False
        logger.info('current page is the last page; will not go next page')

    page += 1
    if go_next:
        logger.info('prepare to get next page: %d', page)
        crawl_rss_list.delay(authorized_user_id=authorized_user.id,
                             page=page)


@app.task(base=RequestsTask, name='rss.crawl_rss_images')
def crawl_rss_images(content_string, article_id):
    if not content_string:
        return
    article = session.query(CoreArticle).get(article_id)
    article_soup = BeautifulSoup(content_string)
    image_tags = article_soup.find_all('img')
    if image_tags:
        for i, image_tag in enumerate(image_tags):
            img_src = (
                image_tag.attrs.get('src') or image_tag.attrs.get('data-src')
            )
            if img_src:
                logger.info('fetch_image for article %d: %s', article.id,
                             img_src)
                gk_img_rc = fetch_image(img_src, rss_client, full=False)
                if gk_img_rc:
                    full_path = "%s%s" % (image_host, gk_img_rc)
                    image_tag['src'] = full_path
                    image_tag['data-src'] = full_path
                    if i == 0:
                        article.cover = full_path
            content_html = article_soup.decode_contents(formatter="html")
            article.content = content_html
            session.commit()
