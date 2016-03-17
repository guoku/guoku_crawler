#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import random
import requests

from datetime import datetime
from urlparse import urljoin
from bs4 import BeautifulSoup
from celery import current_task
from guoku_crawler.config import logger
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from guoku_crawler import config
from guoku_crawler.article.client import WeiXinClient, update_sogou_cookie
from guoku_crawler.celery import RequestsTask, app
from guoku_crawler.common.image import fetch_image
from guoku_crawler.common.parse import clean_xml
from guoku_crawler.db import session
from guoku_crawler.exceptions import TooManyRequests, Expired
from guoku_crawler.models import CoreArticle
from guoku_crawler.models import CoreAuthorizedUserProfile as Profile

SEARCH_API = 'http://weixin.sogou.com/weixinjs'
ARTICLE_LIST_API = 'http://weixin.sogou.com/gzhjs'
weixin_client = WeiXinClient()
qr_code_patterns = (re.compile('biz\s*=\s*"(?P<qr_url>[^"]*)'),
                    re.compile('fakeid\s*=\s*"(?P<qr_url>[^"]*)'),
                    re.compile('appuin\s*=\s*"(?P<qr_url>[^"]*)'))
image_host = getattr(config, 'IMAGE_HOST', None)


@app.task(base=RequestsTask, name='weixin.crawl_list')
def crawl_weixin_list(authorized_user_id, page=1):
    authorized_user = session.query(Profile).get(authorized_user_id)
    try:
        open_id, ext, sg_cookie = get_sogou_tokens(authorized_user.weixin_id)
    except (TooManyRequests, Expired) as e:
        # if too frequent error, re-crawl the page the current article is on
        logger.warning("too many requests or request expired. %s", e.message)
        weixin_client.refresh_cookies(True)
        raise current_task.retry(exc=e)

    if not open_id:
        logger.warning("skip user %s: cannot find open_id. "
                        "Is weixin_id correct?",
                        authorized_user.weixin_id)
        return
    if not authorized_user.weixin_openid:
        # save open_id if it's not set already
        authorized_user.weixin_openid = open_id
        session.commit()

    go_next = True
    jsonp_callback = 'sogou.weixin_gzhcb'
    params = {
        'openid': open_id,
        'ext': ext,
        'page': page,
        'cb': jsonp_callback,
        'type': 1,
    }
    response = weixin_client.get(ARTICLE_LIST_API,
                                 params=params,
                                 jsonp_callback=jsonp_callback,
                                 headers={'Cookie': sg_cookie})

    item_dict = {}
    for article_item in response.jsonp['items']:
        article_item_xml = clean_xml(article_item)
        article_item_xml = BeautifulSoup(article_item_xml, 'xml')
        identity_code = article_item_xml.item.display.docid.text
        item_dict[identity_code] = article_item_xml

    existed = []
    for item in item_dict.keys():
        article = session.query(CoreArticle.title).filter(
            and_(
                CoreArticle.creator_id == authorized_user.user.id,
                CoreArticle.identity_code == item
            )
        )
        logger.info("filter sql is: %s", article)
        if article.all():
            existed.append(item)

    logger.info("those articles are existed: %s", existed)
    if existed:
        logger.info('some items on the page already exists in db; '
                     'no need to go to next page')
        go_next = False

    item_dict = {key: value for key, value
                 in item_dict.items() if key not in existed}
    for identity_code, article_item in item_dict.items():
        crawl_weixin_article.delay(
            article_link=article_item.url.string,
            authorized_user_id=authorized_user.id,
            article_data=dict(cover=article_item.imglink.string,
                              identity_code=identity_code),
            sg_cookie=sg_cookie,
            page=page,
        )

    page += 1
    if int(response.jsonp['totalPages']) < page:
        logger.info('current page is the last page; will not go next page')
        go_next = False

    if go_next:
        logger.info('prepare to get next page: %d', page)
        crawl_weixin_list.delay(authorized_user_id=authorized_user.id,
                                page=page)


@app.task(base=RequestsTask, name='weixin.crawl_weixin_article')
def crawl_weixin_article(article_link, authorized_user_id, article_data,
                         sg_cookie,
                         page):
    identity_code = article_data.get('identity_code')
    cover = article_data.get('cover')
    url = urljoin('http://weixin.sogou.com/', article_link)
    authorized_user = session.query(Profile).get(authorized_user_id)

    try:
        resp = weixin_client.get(
            url=url, headers={'Cookie': sg_cookie})
    except (TooManyRequests, Expired) as e:
        # if too frequent error, re-crawl the page the current article is on
        logger.warning("too many requests or request expired. %s", e.message)
        crawl_weixin_list.delay(authorized_user_id=authorized_user.id,
                                page=page)
        return

    article_soup = BeautifulSoup(resp.utf8_content, from_encoding='utf8',
                                 isHTML=True)
    if not authorized_user.weixin_qrcode_img:
        get_qr_code(authorized_user.id, parse_qr_code_url(article_soup))

    title = article_soup.select('h2.rich_media_title')[0].text
    published_time = article_soup.select('em#post-date')[0].text
    published_time = datetime.strptime(published_time, '%Y-%m-%d')
    content = article_soup.find('div', id='js_content')
    creator = authorized_user.user

    ##
    existed_article = session.query(CoreArticle).filter_by(
        title=title,
        creator=creator
    )
    if existed_article.all():
        article = existed_article.all()[0]
        article.identity_code = identity_code
        session.commit()
        return
    ##


    try:
        article = session.query(CoreArticle).filter_by(
            identity_code=identity_code,
        ).one()
    except NoResultFound:
        article = CoreArticle(
            creator=creator,
            identity_code=identity_code,
            title=title,
            content=content.decode_contents(formatter="html"),
            created_datetime=published_time,
            publish=CoreArticle.published,
            cover=cover,
        )
        session.add(article)
        session.commit()
    logger.info("created article id: %s. title: %s. identity_code: %s",
                 article.id, title, identity_code)

    cover = fetch_image(article.cover, weixin_client)
    if cover:
        article.cover = cover
        session.commit()

    article_soup = BeautifulSoup(article.content)
    image_tags = article_soup.find_all('img')
    if image_tags:
        for i, image_tag in enumerate(image_tags):
            img_src = (
                image_tag.attrs.get('src') or image_tag.attrs.get('data-src')
            )
            if img_src:
                logger.info('fetch_image for article %d: %s', article.id,
                             img_src)
                gk_img_rc = fetch_image(img_src, weixin_client, full=False)
                if gk_img_rc:
                    full_path = "%s%s" % (image_host, gk_img_rc)
                    image_tag['src'] = full_path
                    image_tag['data-src'] = full_path
                    if not cover and not article.cover and i == 0:
                        article.cover = gk_img_rc
            content_html = article_soup.decode_contents(formatter="html")
            article.content = content_html
            session.commit()
    logger.info('article %s finished.', article.id)
    print('-' * 80)


def get_sogou_tokens(weixin_id):
    weixin_id = weixin_id.strip()
    logger.info('get open_id for %s', weixin_id)
    open_id = None
    ext = None
    params = dict(type='1', ie='utf8', query=weixin_id)
    weixin_client.refresh_cookies()
    sg_cookie = weixin_client.headers.get('Cookie')
    response = weixin_client.get(url=SEARCH_API,
                                 params=params,
                                 jsonp_callback='weixin',
                                 headers={'Cookie': sg_cookie})

    for item in response.jsonp['items']:
        item_xml = clean_xml(item)
        item_xml = BeautifulSoup(item_xml, 'xml')
        if item_xml.weixinhao.string.lower() == weixin_id.lower():
            open_id = item_xml.id.string
            ext = item_xml.ext.string
            break

    if open_id:
        return open_id, ext, sg_cookie
    else:
        logger.warning('cannot find open_id for weixin_id: %s.', weixin_id)
        return None, None, None


def parse_qr_code_url(article_soup):
    scripts = article_soup.select('script')
    biz = ''
    for script in scripts:
        found = False
        for pattern in qr_code_patterns:
            biz_tag = pattern.findall(script.text)
            if biz_tag:
                biz = biz_tag[0]
                found = True
        if found:
            break

    scene = random.randrange(10000001, 10000007)
    return 'http://mp.weixin.qq.com/mp/qrcode?scene=%s&__biz=%s' % (scene, biz)


def get_qr_code(authorized_user_id, qr_code_url):
    authorized_user = session.query(Profile).get(authorized_user_id)
    if not authorized_user.weixin_qrcode_img:
        qr_code_image = fetch_image(qr_code_url, weixin_client)
        authorized_user.weixin_qrcode_img = qr_code_image
        session.commit()


@app.task(base=RequestsTask, name='weixin.prepare_sogou_cookies')
def prepare_sogou_cookies():
    check_url = urljoin(config.PHANTOM_SERVER, '_health')
    resp = requests.get(check_url)
    ready = resp.status_code == 200
    if ready:
        emails = config.SOGOU_USERS
        for sg_email in emails:
            update_sogou_cookie.delay(sg_user=sg_email)
    else:
        logger.error("phantom web server is unavailable!")


if __name__ == '__main__':
    prepare_sogou_cookies.delay()
