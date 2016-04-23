#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import random
import requests
import json
import hashlib

from datetime import datetime
from urlparse import urljoin
from bs4 import BeautifulSoup
from celery import current_task
from pymysql.err import InternalError, DatabaseError

from guoku_crawler.config import logger
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from guoku_crawler.utils import pick
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


def parse_link_list_for_weixinid(response , weixin_id):
    link = None
    for item in response.jsonp['items']:
        item_xml = clean_xml(item)
        item_xml = BeautifulSoup(item_xml, 'xml')
        if item_xml.weixinhao.string.lower() == weixin_id.lower():
            link = item_xml.encGzhUrl.string
            break
    return  link


def get_msg_obj(msg):
    msgObj = None
    try :
        msg = msg.replace('&quot;', '"')
        msg = msg.replace('&amp;amp;','&')
        msg = msg.replace('\\\/','/')
        msgObj = json.loads(msg)
    except Exception as e :
        logger.warning('can not get msg obj')

    return msgObj


def parse_msg_object(msgObj):
    article_mission_list = []
    keys = ['content_url', 'cover', 'is_multi', 'source_url', 'title', 'source_url', 'author']
    try:
        for article_item in msgObj['list']:
            article_info = article_item['app_msg_ext_info']
            article = pick(article_info,keys)
            article_mission_list.append(article)
            if  'multi_app_msg_item_list' in article_info :
                for child_article in article_info['multi_app_msg_item_list']:
                    c_article =  pick(child_article, keys)
                    article_mission_list.append(c_article)

    except Exception as e:
        logger.warning('can not fetch article mission list %s' % str(e))
        article_mission_list = None

    return article_mission_list



def parse_msg_list(msg):
    # quote = re.compile(r'&quot;')
    msgObj = get_msg_obj(msg)
    if msgObj is None:
        logger.warning('parse message list fail')
        return None

    article_mission_list = parse_msg_object(msgObj)
    return article_mission_list


def parse_article_url_list(response):
    url_list = None

    matchObj = re.compile(r'msgList = \'(.*)\'', re.M|re.I)
    result = matchObj.search(response.text)

    if (result is None) \
            or (result.group() is None) \
            or (result.group(1) is None) :

        logger.warning('can not parse article url list')
        return None

    msgListString = result.group(1)
    article_mission_list =  parse_msg_list(msgListString)
    if article_mission_list is None:
        logger.warning('can not parse msg list in page')
        return None

    return article_mission_list


    #         TODO : parse object




def get_link_list_url(weixin_id, update_cookie=False):
    params = dict(type='1', ie='utf8', query=weixin_id)
    sg_cookie = weixin_client.headers.get('Cookie')
    logger.info('get weixin list for %s ', weixin_id)
    response = weixin_client.get(url=SEARCH_API,
                                 params=params,
                                 jsonp_callback='weixin',
                                 headers={'Cookie': sg_cookie})
    list_link_url = parse_link_list_for_weixinid(response, weixin_id);
    return list_link_url


def get_link_list_by_url(url):
    sg_cookie = weixin_client.headers.get('Cookie')
    response = weixin_client.get(url=url, headers={'Cookie':sg_cookie})
    article_url_list = parse_article_url_list(response)
    return article_url_list



def get_user_weixin_list(weixin_id, update_cookie=False ):
    link_list_url =  get_link_list_url(weixin_id, update_cookie)
    if link_list_url is None:
        logger.warning('can not find link_list_url for weixin_id : ' % weixin_id)
        return
    else:
        logger.info('link list url for %s is %s' %(weixin_id,link_list_url))

    link_list = get_link_list_by_url(link_list_url)
    return link_list

def get_weixin_id_by_authorized_user_id(userid):
    # TODO : test  no weixin id Profile
    return session.query(Profile).get(userid)\
                                 .weixin_id\
                                 .strip()

def get_user_by_authorized_user_id(userid):
    return session.query(Profile).get(userid)




def is_mission_done(mission):
    '''

    :param mission:
        article crawl mission
    :return:
        if the mission has been finished
    '''
    return False


def get_request_cookie():
    return weixin_client.headers.get('Cookie')

@app.task(base=RequestsTask, name='weixin.crawl_weixin_single_article_mission')
def crawl_weixin_single_article_mission(mission, authorized_user_id=None):
    '''
    :param mission:
        {
            'author':
            'title':
            'cover':
            'is_multi':
            'source_url':
            'content_url':
        }
    :param authorized_user_id:

    :return: none

    '''

    if authorized_user_id is None:
        logger.warning('need authorized user id to go on')
        raise Exception #need Exception handle

    if  isArticleExist(mission):

        return

    response = None
    try :
        response = get_mission_page_content(mission)
    except (TooManyRequests, Expired) as e  :
        logger.warning('Too many request for mission %s ' % mission['content_url'])
        # TODO exception handle
        return

    if (response is None) or (response.status_code != 200):
        # TODO : Exception raise and handle
        logger.warning('response of the mission status wrong' % getattr(mission, 'content_url'))

    else:
        article_dic = parse_article_page(response,authorized_user_id)
        article_dic.update(mission)

        try :
            article = createArticle(article_dic)
            fetch_article_cover(article)
            fetch_article_image(article)
        except Exception as e :
            logger.warning('create Article fail ')



def fetch_article_cover(article):
    if article.cover is None:
        return
    try :
        cover = fetch_image(article.cover, weixin_client)
        article.cover = cover
        session.commit()
    except Exception as e :
        logger.warning('get cover fail for article : %s ' % article.title)


def fetch_article_image(article):
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
                    if not article.cover and i == 0:
                        article.cover = gk_img_rc
            content_html = article_soup.decode_contents(formatter="html")
            article.content = content_html
            session.commit()
    logger.info('article %s finished.', article.id)
    print('-' * 80)



def isArticleExist(article_dic):

    return False


def createArticle(article_dic):
    keys = ['creator','title','content', 'created_datetime', 'cover', 'identity_code']

    article = CoreArticle(
            creator=article_dic['creator'],
            identity_code=article_dic['identity_code'],
            title=article_dic['title'],
            content=article_dic['content'].prettify().encode('utf-8'),
            created_datetime=article_dic['created_datetime'],
            updated_datetime=datetime.now(),
            publish=CoreArticle.published,
            cover=article_dic['cover'],
        )
    session.add(article)
    session.commit()
    return article

    article_dic  = pick(article_dic, keys)
    article = CoreArticle(**article_dic)
    session.add(article)
    try :
        session.commit()
        return article
    except Exception as e :
        logger.info('save article fail, for  for article : %s ' %article.title)
        #TODO : raise Exception here
        return None



def get_identity_code(article_dic, authorized_user_id):
    user_id = get_user_by_authorized_user_id(authorized_user_id).id
    title_hash =  hashlib.sha1(article_dic['title'].encode('utf-8')).hexdigest()
    return '%s_%s_%s ' % (user_id,title_hash,article_dic['created_datetime'])

def parse_article_page(response, user_id):
    article_soup = BeautifulSoup(response.utf8_content, from_encoding='utf8', isHTML=True)
    title = article_soup.select('h2.rich_media_title')[0].text
    published_time = article_soup.select('em#post-date')[0].text
    published_time = datetime.strptime(published_time, '%Y-%m-%d')
    content = article_soup.find('div', id='js_content')
    article_dic = dict(
        title=title,
        created_datetime=published_time,
        content=content)
    article_dic['creator'] = get_user_by_authorized_user_id(user_id).user
    article_dic['updated_datetime'] = datetime.now()
    article_dic['publish'] = CoreArticle.published
    article_dic['identity_code'] = get_identity_code(article_dic, user_id)

    return article_dic




def get_mission_page_content(mission):
    cookie  = get_request_cookie()
    url = convert_article_url(mission['content_url'])
    response = weixin_client.get( url, headers={'Cookie': cookie})
    return response

def convert_article_url(uri):
    url = 'http://mp.weixin.qq.com%s' % uri
    return url




@app.task(base=RequestsTask, name='weixin.crawl_list')
def crawl_weixin_articles(authorized_user_id, update_cookie=False):

    logger.info('weixin articles  for authorized author id : %s' % authorized_user_id)

    weixin_id = get_weixin_id_by_authorized_user_id(authorized_user_id)

    user_article_mission_list = get_user_weixin_list(weixin_id, update_cookie=False)

    for article_mission in user_article_mission_list:
        print article_mission
        crawl_weixin_single_article_mission(article_mission, authorized_user_id)
    return

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
        if article.all():
            existed.append(item)

    if existed:
        logger.info('some articles are existed, no need to go to next page.')
        go_next = False

    article_list = {key: value for key, value
                    in item_dict.items() if key not in existed}
    if article_list:
        for identity_code, article_item in article_list.items():
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
    except (TooManyRequests, Expired):
        # if too frequent error, re-crawl the page the current article is on
        crawl_weixin_article.delay(authorized_user_id=authorized_user.id,
                                page=page, update_cookie=True)
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

    try:
        existed_article = session.query(CoreArticle).filter_by(
            title=title,
            creator_id=creator.id
        ).all()
    except BaseException as e:
        logger.error(e.message)
        return

    if existed_article:
        existed_article[0].identity_code = identity_code
        session.commit()
        return

    if session.query(CoreArticle).filter_by(
        identity_code=identity_code,
        creator_id=creator.id
    ).all():
        return

    try:
        article = session.query(CoreArticle).filter_by(
            identity_code=identity_code,
            creator_id=creator.id
        ).one()

    except NoResultFound:
        article = CoreArticle(
            creator=creator,
            identity_code=identity_code,
            title=title,
            content=content.prettify().encode('utf-8'),
            created_datetime=published_time,
            updated_datetime=datetime.now(),
            publish=CoreArticle.published,
            cover=cover,
        )
        session.add(article)

        try:
            session.commit()
        except Exception as e :
            logger.info('save article fail , for article  : %s' %article.title )


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


def get_sogou_tokens(weixin_id, update_cookie=False):
    weixin_id = weixin_id.strip()
    logger.info('get open_id for %s', weixin_id)
    open_id = None
    ext = None
    params = dict(type='1', ie='utf8', query=weixin_id)
    weixin_client.refresh_cookies(update_cookie)
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
            result = update_sogou_cookie.delay(sg_user=sg_email)
            result.get()
    else:
        logger.error("phantom web server is unavailable!")
