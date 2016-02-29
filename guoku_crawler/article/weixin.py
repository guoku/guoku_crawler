#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from wand.exceptions import WandException

from guoku_crawler import config
from guoku_crawler.article import Expired
from guoku_crawler.article import WeiXinClient, ToManyRequests
from guoku_crawler.celery import RequestsTask, app
from guoku_crawler.common.parse import clean_xml, clean_title
from guoku_crawler.common.utils import get_or_create
from guoku_crawler.db import session
from guoku_crawler.models import CoreArticle, CoreMedia, CoreGkuser, AuthGroup
from guoku_crawler.models import CoreAuthorizedUserProfile as Profile


SEARCH_API = 'http://weixin.sogou.com/weixinjs'
ARTICLE_LIST_API = 'http://weixin.sogou.com/gzhjs'
weixin_client = WeiXinClient()
qr_code_patterns = (re.compile('biz\s*=\s*"(?P<qr_url>[^"]*)'),
                    re.compile('fakeid\s*=\s*"(?P<qr_url>[^"]*)'),
                    re.compile('appuin\s*=\s*"(?P<qr_url>[^"]*)'))
image_host = getattr(config, 'IMAGE_HOST', None)


# @app.task(base=RequestsTask, name='sogou.crawl_articles')
def crawl_articles():
    users = session.query(CoreGkuser).filter(
        CoreGkuser.authorized_profile.any(Profile.weixin_id.isnot(None)),
        CoreGkuser.groups.any(AuthGroup.name == 'Author')
    ).all()
    for user in users:
        print(user)
        crawl_user_articles(user.profile.id)


# @app.task(base=RequestsTask, name='sogou.crawl_user_articles')
def crawl_user_articles(authorized_user_id, page=1):
    authorized_user = session.query(Profile).get(authorized_user_id)
    print('>> authorized: ', authorized_user)
    open_id, ext, sg_cookie = get_tokens(authorized_user.weixin_id)
    if not open_id:
        logging.warning("skip user %s: cannot find open_id. "
                        "Is weixin_id correct?",
                        authorized_user.weixin_id)
        return
    if not authorized_user.weixin_openid:
        # save open_id if it's not set already
        authorized_user.weixin_openid = open_id
        authorized_user.save()

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
        title = clean_title(article_item_xml.title1.text)
        item_dict[title] = article_item_xml

    existed = []
    for item in item_dict.keys():
        article = session.query(CoreArticle.title).filter(
            CoreArticle.creator == authorized_user.user,
            CoreArticle.cleaned_title.like('{item}%'.format_map(item_dict))
        )
        logging.info("filter sql is: %s", article.query)
        if article:
            existed.append(item)

    logging.info("those articles are existed: %s", existed)
    if existed:
        logging.info('some items on the page already exists in db; '
                     'no need to go to next page')
        go_next = False
    item_dict = {key: value for key, value
                 in item_dict.items() if key not in existed}
    for cleaned_title, article_item in item_dict.items():
        crawl_article(
            article_link=article_item.url.string,
            authorized_user_id=authorized_user.id,
            article_data=dict(cover=article_item.imglink.string),
            sg_cookie=sg_cookie,
            page=page,
        )

    page += 1
    if int(response.jsonp['totalPages']) < page:
        logging.info('current page is the last page; will not go next page')
        go_next = False

    if go_next:
        logging.info('prepare to get next page: %d', page)
        crawl_user_articles(authorized_user_id=authorized_user.id,
                                  page=page)


# @app.task(base=RequestsTask, name='sogou.crawl_article')
def crawl_article(article_link, authorized_user_id, article_data, sg_cookie,
                  page):
    url = urljoin('http://weixin.sogou.com/', article_link)
    authorized_user = session.query(Profile).get(authorized_user_id)

    try:
        resp = weixin_client.get(
            url=url, headers={'Cookie': sg_cookie})
    except (ToManyRequests, Expired) as e:
        # if too frequent error, re-crawl the page the current article is on
        logging.warning("too many requests or request expired. %s", e.message)
        crawl_user_articles(authorized_user_id=authorized_user.id,
                                  page=page)
        return

    article_soup = BeautifulSoup(resp.utf8_content, from_encoding='utf8')
    if not authorized_user.weixin_qrcode_img:
        get_qr_code(authorized_user.id, parse_qr_code_url(article_soup))

    title = article_soup.select('h2.rich_media_title')[0].text
    published_time = article_soup.select('em#post-date')[0].text
    published_time = datetime.strptime(published_time, '%Y-%m-%d')
    content = article_soup.find('div', id='js_content')
    creator = authorized_user.user
    cleaned_title = clean_title(title)

    article, created = get_or_create(CoreArticle, **dict(
        cleaned_title=cleaned_title,
        creator=creator,
    ))
    logging.info("created article id: %s. title: %s. cleaned_title: %s",
                 article.id, title, cleaned_title)

    if created:
        article_info = dict(
            title=title,
            content=content.decode_contents(formatter="html"),
            created_datetime=published_time,
            publish=CoreArticle.published,
        )
        article_info.update(article_data)
        for (key, value) in article_info.items():
            setattr(article, key, value)
        article.save()
        logging.info('insert article. %s', title)

    cover = fetch_image(article.cover)
    if cover:
        article.cover = cover
        article.save()

    article_soup = BeautifulSoup(article.content)
    image_tags = article_soup.find_all('img')
    if image_tags:
        for i, image_tag in enumerate(image_tags):
            img_src = (
                image_tag.attrs.get('src') or image_tag.attrs.get('data-src')
            )
            if img_src:
                logging.info('fetch_image for article %d: %s', article.id,
                             img_src)
                gk_img_rc = fetch_image(img_src, full=False)
                if gk_img_rc:
                    full_path = "%s%s" % (image_host, gk_img_rc)
                    image_tag['src'] = full_path
                    image_tag['data-src'] = full_path
                    if not cover and not article.cover and i == 0:
                        article.cover = gk_img_rc
            content_html = article_soup.decode_contents(formatter="html")
            article.content = content_html
            article.save()
    logging.info('article %s finished.', article.id)
    print('-' * 80)


def get_tokens(weixin_id):
    logging.info('get open_id for %s', weixin_id)
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
        logging.warning('cannot find open_id for weixin_id: %s.', weixin_id)
        return None, None, None


def fetch_image(image_url, full=True):
    logging.info('fetch_image %s', image_url)
    if not image_url:
        logging.info('empty image url; skip')
        return
    if (not image_url.find('mmbiz.qpic.cn') >= 0 and
            not image_url.find('mp.weixin.qq.com') >= 0):
        logging.info('image url is not from mmbiz.qpic.cn; skip: %s', image_url)
        return
    from guoku_crawler.common.image import HandleImage
    r = weixin_client.get(url=image_url, stream=True)
    try:
        try:
            content_type = r.headers['Content-Type']
        except KeyError:
            content_type = 'image/jpeg'
        image = HandleImage(r.raw)
        image_name = image.save()
        media = CoreMedia(file_path=image_name, content_type=content_type)
        session.add(media)
        session.commit()
        if full:
            return "%s%s" % (image_host, image_name)
        return image_name

    except (AttributeError, WandException) as e:
        logging.error('handle image(%s) Error: %s', image_url, e.message)


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
        qr_code_image = fetch_image(qr_code_url)
        authorized_user.weixin_qrcode_img = qr_code_image
        authorized_user.save()


if __name__ == '__main__':
    crawl_articles()
    print('hhhhhh')
