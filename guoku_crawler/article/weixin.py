#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import random
import requests
import json

from datetime import datetime
from urlparse import urljoin
from bs4 import BeautifulSoup
from celery import current_task
from pymysql.err import InternalError, DatabaseError

from guoku_crawler.config import logger
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from guoku_crawler import config
from guoku_crawler.article.client import WeiXinClient, update_sogou_cookie, get_user_profile_link
from guoku_crawler.celery import RequestsTask, app
from guoku_crawler.common.image import fetch_image
from guoku_crawler.common.parse import clean_xml
from guoku_crawler.db import session, r
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
def crawl_weixin_list(authorized_user_id, page=1, update_cookie=False):
    authorized_user = session.query(Profile).get(authorized_user_id)
    logger.info('start crawl_weixin_list %s, authorized_user_id: %d' % (authorized_user.weixin_id, authorized_user_id))
    try:
        open_id, sg_cookie, user_link= get_sogou_tokens(
            weixin_id=authorized_user.weixin_id,
            update_cookie=update_cookie)
    except (TooManyRequests, Expired) as e:
        # if too frequent error, re-crawl the page the current article is on
        update_cookie = True
        logger.warning('failed to get_sogou_tokens')
        logger.warning("crawl_weixin_list: too many requests or request expired. %s", e.message)
        weixin_client.refresh_cookies(update_cookie)
        # raise current_task.retry(exc=e)
        raise TooManyRequests

    # if not open_id:
    #     logger.warning("skip user %s: cannot find open_id. "
    #                    "Is weixin_id correct?",
    #                    authorized_user.weixin_id)
    #     return
    if not authorized_user.weixin_openid:
        # save open_id if it's not set already
        authorized_user.weixin_openid = open_id
        session.commit()

    # go_next = True
    # jsonp_callback = 'sogou.weixin_gzhcb'
    # params = {
    #     'openid': open_id,
    #     'ext': ext,
    #     'page': page,
    #     'cb': jsonp_callback,
    #     'type': 1,
    # }
    # response = weixin_client.get(ARTICLE_LIST_API,
    #                              params=params,
    #                              jsonp_callback=jsonp_callback,
    #                              headers={'Cookie': sg_cookie})

    new_response = weixin_client.get(user_link, headers={'Cookie': sg_cookie})
    new_response.utf8_content = new_response.utf8_content.replace('&quot;', '').replace('amp;', '')
    new_response = BeautifulSoup(new_response.utf8_content, 'lxml')

    scripts = new_response.find_all('script', type='text/javascript')[-1]
    test = BeautifulSoup(scripts.text, 'xml')

    # ha = re.split('content_url:\\\\\\\\', new_response.utf8_content)
    items = re.split('title:', scripts.text)

    # l = scripts.text.split(';\r\n')
    # jsonValue = '{%s}' % (l[3].split('{', 1)[1].rsplit('}', 1)[0],)
    # jsonValue = jsonValue.replace('&quot;', '')
    # r = re.split('app_msg_ext_info:', jsonValue)
    # for i in r:
    #     o = re.split('content_url:', i)
    #     for x in o:
    #         print x
    article_list = []
    # t = re.split('content_url:\\\\\\\\', jsonValue)
    for item in items[1:]:
            item = item.replace('\\', '')
            try:
                cover = re.findall(r'cover:(.*(wx_fmt=(jpeg|png))),(subtype|author)', item)[0][0]
            except:
                cover = ''
            fileid = re.findall(r'fileid:(\d+)', item)[0]
            # title = re.findall(r'(.*),digest', item)[0]
            article_url = u'http://mp.weixin.qq.com' + re.findall(r'content_url:(.*),source_url', item)[0]
            article_list.append((cover, article_url, fileid))
    try:
        for article in article_list:
            try:
                crawl_weixin_article.delay(article, authorized_user_id, sg_cookie)
            except Exception as e:
                logger.error(e)
                logger.error('crawl_weixin_list: article %s failed' % article[1])
    except Exception as e:
        logger.info(str(authorized_user_id) + 'failed')
        logger.error(e)
            # print  cover
            # print article_url




    # for link in article_list:
    # response = weixin_client.get(article_list[-1])
    # new_crawl_article(article_list[0], authorized_user_id, sg_cookie)
    return article_list

    # oj = json.loads(jsonValue)
    # jsonValue.replace('&quot;', '')

    # item_dict = {}
    # for article_item in response.jsonp['items']:
    #     article_item_xml = clean_xml(article_item)
    #     article_item_xml = BeautifulSoup(article_item_xml, 'xml')
    #     identity_code = article_item_xml.item.display.docid.text
    #     item_dict[identity_code] = article_item_xml
    #
    # existed = []
    # for item in item_dict.keys():
    #     article = session.query(CoreArticle.title).filter(
    #         and_(
    #             CoreArticle.creator_id == authorized_user.user.id,
    #             CoreArticle.identity_code == item
    #         )
    #     )
    #     if article.all():
    #         existed.append(item)
    #
    # article_list = {key: value for key, value
    #                 in item_dict.items() if key not in existed}
    #
    # if existed:
    #     logger.info('some articles are existed, no need to go to next page.')
    #     go_next = False


    # if article_list:
    #     for identity_code, article_item in article_list.items():
    #         crawl_weixin_article.delay(
    #             article_link=article_item.url.string,
    #             authorized_user_id=authorized_user.id,
    #             article_data=dict(cover=article_item.imglink.string,
    #                               identity_code=identity_code),
    #             sg_cookie=sg_cookie,
    #             page=page,
    #         )

    # page += 1
    # if int(response.jsonp['totalPages']) < page:
    #     logger.info('some articles are existed, no need to go to next page.Next will crawl user %s %d articles.' % (
    #                         authorized_user.weixin_id, len(article_list)))
    #     go_next = False

    # if go_next:
    #     logger.info('prepare to get next page: %d', page)
    #     crawl_weixin_list.delay(authorized_user_id=authorized_user.id,
    #                             page=page)
@app.task(base=RequestsTask, name='weixin.crawl_weixin_article')
def crawl_weixin_article(article_info, authorized_user_id, cookie):
    try:
        resp = weixin_client.get(
            url=article_info[1], headers={'Cookie': cookie})
    except:
        pass
    article_soup = BeautifulSoup(resp.utf8_content, from_encoding='utf8',
                                 isHTML=True)

    authorized_user = session.query(Profile).get(authorized_user_id)
    identity_code = article_info[2]
    creator = authorized_user.user
    title = article_soup.select('h2.rich_media_title')[0].text
    content = article_soup.find('div', id='js_content')
    published_time = article_soup.select('em#post-date')[0].text
    published_time = datetime.strptime(published_time, '%Y-%m-%d')
    cover = article_info[0]
    if not cover:
        # cover = article_soup.select('img#js_cover.rich_media_thumb')
        cover = ''  #Todo
        pass



    try:
        article = session.query(CoreArticle).filter_by(
            identity_code=identity_code,
            creator_id=creator.id
        ).one()
        logger.info('this article alreadey in the database.')
    except NoResultFound:
        article = CoreArticle(
            creator=creator,
            identity_code=identity_code,
            title=title,
            content=content.decode_contents(formatter="html"),
            created_datetime=published_time,
            updated_datetime=datetime.now(),
            publish=CoreArticle.published,
            cover=cover,
        )
        session.add(article)
        session.commit()
        logger.info("created article id: %s. title: %s. identity_code: %s",
                    article.id, title, identity_code)
        try:
            crawl_image(article)
        except Exception  as e:
            logger.error(e)
        # logger.info('-'*100)
        # cover = fetch_image(article.cover, weixin_client)
        # if cover:
        #     article.cover = cover
        #     session.commit()
        #
        # article_soup = BeautifulSoup(article.content)
        # image_tags = article_soup.find_all('img')
        # if image_tags:
        #     for i, image_tag in enumerate(image_tags):
        #         img_src = (
        #             image_tag.attrs.get('src') or image_tag.attrs.get('data-src')
        #         )
        #         if img_src:
        #             logger.info('fetch_image for article %d: %s', article.id,
        #                         img_src)
        #             gk_img_rc = fetch_image(img_src, weixin_client, full=False)
        #             if gk_img_rc:
        #                 full_path = "%s%s" % (image_host, gk_img_rc)
        #                 image_tag['src'] = full_path
        #                 image_tag['data-src'] = full_path
        #                 if not cover and not article.cover and i == 0:
        #                     article.cover = gk_img_rc
        #         content_html = article_soup.decode_contents(formatter="html")
        #         article.content = content_html
        #         session.commit()
        # logger.info('article %s finished.', article.id)
        # logger.info('-' * 120)

def crawl_image(article):
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
    logger.info('-' * 120)


# @app.task(base=RequestsTask, name='weixin.crawl_weixin_article')
# def crawl_weixin_article(article_link, authorized_user_id, article_data,
#                          sg_cookie,
#                          page):
#     identity_code = article_data.get('identity_code')
#     cover = article_data.get('cover')
#     url = urljoin('http://weixin.sogou.com/', article_link)
#     authorized_user = session.query(Profile).get(authorized_user_id)
#
#     try:
#         resp = weixin_client.get(
#             url=url, headers={'Cookie': sg_cookie})
#     except (TooManyRequests, Expired):
#         # if too frequent error, re-crawl the page the current article is on
#         crawl_weixin_list.delay(authorized_user_id=authorized_user.id,
#                                 page=page, update_cookie=True)
#         return
#
#     article_soup = BeautifulSoup(resp.utf8_content, from_encoding='utf8',
#                                  isHTML=True)
#     if not authorized_user.weixin_qrcode_img:
#         get_qr_code(authorized_user.id, parse_qr_code_url(article_soup))
#
#     title = article_soup.select('h2.rich_media_title')[0].text
#     published_time = article_soup.select('em#post-date')[0].text
#     published_time = datetime.strptime(published_time, '%Y-%m-%d')
#     content = article_soup.find('div', id='js_content')
#     creator = authorized_user.user
#
#     try:
#         existed_article = session.query(CoreArticle).filter_by(
#             title=title,
#             creator_id=creator.id
#         ).all()
#     except BaseException as e:
#         logger.error(e.message)
#         return
#
#     if existed_article:
#         existed_article[0].identity_code = identity_code
#         session.commit()
#         return
#
#     if session.query(CoreArticle).filter_by(
#         identity_code=identity_code,
#         creator_id=creator.id
#     ).all():
#         return
#
#     try:
#         article = session.query(CoreArticle).filter_by(
#             identity_code=identity_code,
#             creator_id=creator.id
#         ).one()
#     except NoResultFound:
#         article = CoreArticle(
#             creator=creator,
#             identity_code=identity_code,
#             title=title,
#             content=content.decode_contents(formatter="html"),
#             created_datetime=published_time,
#             updated_datetime=datetime.now(),
#             publish=CoreArticle.published,
#             cover=cover,
#         )
#         session.add(article)
#         session.commit()
#         logger.info("created article id: %s. title: %s. identity_code: %s",
#                 article.id, title, identity_code)
#
#     cover = fetch_image(article.cover, weixin_client)
#     if cover:
#         article.cover = cover
#         session.commit()
#
#     article_soup = BeautifulSoup(article.content)
#     image_tags = article_soup.find_all('img')
#     if image_tags:
#         for i, image_tag in enumerate(image_tags):
#             img_src = (
#                 image_tag.attrs.get('src') or image_tag.attrs.get('data-src')
#             )
#             if img_src:
#                 logger.info('fetch_image for article %d: %s', article.id,
#                             img_src)
#                 gk_img_rc = fetch_image(img_src, weixin_client, full=False)
#                 if gk_img_rc:
#                     full_path = "%s%s" % (image_host, gk_img_rc)
#                     image_tag['src'] = full_path
#                     image_tag['data-src'] = full_path
#                     if not cover and not article.cover and i == 0:
#                         article.cover = gk_img_rc
#             content_html = article_soup.decode_contents(formatter="html")
#             article.content = content_html
#             session.commit()
#     logger.info('article %s finished.', article.id)
#     logger.info('-' * 120)


def get_sogou_tokens(weixin_id, update_cookie=False):

    weixin_id = weixin_id.strip()
    logger.info('getting open_id for %s', weixin_id)
    # open_id = None
    # ext = None
    user_link = None
    params = dict(type='1', ie='utf8', query=weixin_id)
    # weixin_client.refresh_cookies(update_cookie)
    # sg_cookie = weixin_client.headers.get('Cookie')
    # sg_cookie = cookie_to_dict(sg_cookie)
    #Todo
    # if not sg_cookie:
    #     for user in list(config.SOGOU_USERS):
    #         sg_cookie = r.get('sogou.cookie.%s' % user)
    #         if sg_cookie:
    #             break
    # sg_cookie['SNUID'] = 'B96B3A33BABC88B748F2CD31BAAFA909'

    # logger.info('get_sogou_tokens: request headers cookie: %s' % sg_cookie)
    try:
        response = get_user_profile_link(weixin_id)
        user_link = json.loads(response.content).get('user_link')
        return '', '', user_link
    except Exception as e:
        logger.error(e)

    # response = weixin_client.get(url=SEARCH_API,
    #                              params=params,
    #                              jsonp_callback='weixin',
    #                              headers={'Cookie': sg_cookie},
    #                              cookies=sg_cookie
    #                              )
    #
    # for item in response.jsonp['items']:
    #     item_xml = clean_xml(item)
    #     item_xml = BeautifulSoup(item_xml, 'xml')
    #     if item_xml.weixinhao.string.lower() == weixin_id.lower():
    #         open_id = item_xml.id.string
    #         # ext = item_xml.ext
    #         user_link = item_xml.encGzhUrl.string
    #
    #         break
    #
    # if open_id:
    #     logger.info('got open_id and user profile link...')
    #     return open_id,  sg_cookie, user_link
    # else:
    #     logger.warning('cannot find open_id for weixin_id: %s.', weixin_id)
    #     return None, None, None
# def cookie_to_dict(cookies):
#     cookies_dict = {}
#     items = cookies.split(';')
#     for item in items:
#         k, v = item.split('=')
#         cookies_dict[k.strip()] = v
#     return cookies_dict




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
    logger.info('start to prepare cookies for all the users')
    check_url = urljoin(config.PHANTOM_SERVER, '_health')
    resp = requests.get(check_url)
    ready = resp.status_code == 200
    if ready:
        emails = config.SOGOU_USERS
        for sg_email in emails:
            update_sogou_cookie.delay(sg_user=sg_email)
            logger.info('prepare_sogou_cookie: call update_sogou_cookie.delay for user: %s' % sg_email)
            # result.get()
    else:
        logger.error("phantom web server is unavailable!")
