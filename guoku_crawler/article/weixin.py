#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import random
import requests
import json
import hashlib
import time

from datetime import datetime
from urlparse import urljoin
from bs4 import BeautifulSoup
from celery import current_task
from pymysql.err import InternalError, DatabaseError

from guoku_crawler.config import logger
from sqlalchemy import and_
from sqlalchemy.orm.exc import NoResultFound

from guoku_crawler.utils import pick, stripHtmlText
from guoku_crawler import config
from guoku_crawler.article.client import WeiXinClient, update_sogou_cookie
from guoku_crawler.tasks import RequestsTask, app
from guoku_crawler.common.image import fetch_image
from guoku_crawler.common.parse import clean_xml
from guoku_crawler.db import session
from guoku_crawler.exceptions import TooManyRequests, Expired, CanNotFindWeixinInSogouException
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
            article_common_info = article_item['comm_msg_info']
            # get create date
            created_datetime_number = article_common_info['datetime']

            #created_datetime must strip time , set to 00:00:00
            #for compatiable with old data
            created_date = datetime.fromtimestamp(created_datetime_number)\
                                    .replace(hour=0, minute=0,second=0)

            article = pick(article_info,keys)
            article['title'] = stripHtmlText(article['title'])
            article['created_datetime'] = created_date
            article_mission_list.append(article)
            if  'multi_app_msg_item_list' in article_info :
                for child_article in article_info['multi_app_msg_item_list']:
                    # c for child article
                    c_article =  pick(child_article, keys)
                    c_article['title'] = stripHtmlText(c_article['title'])
                    c_article['created_datetime'] = created_date
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
    logger.info('get weixin list for %s ', weixin_id)

    weixin_client.refresh_cookies(update_cookie)
    sg_cookie = weixin_client.headers.get('Cookie')

    response = weixin_client.get(url=SEARCH_API,
                                 params=params,
                                 jsonp_callback='weixin',
                                 headers={'Cookie': sg_cookie})
    #debug here
    # raise TooManyRequests()
    # return

    list_link_url = parse_link_list_for_weixinid(response, weixin_id);
    return list_link_url


def get_link_list_by_url(url):
    sg_cookie = weixin_client.headers.get('Cookie')
    response = weixin_client.get(url=url, headers={'Cookie':sg_cookie})
    article_url_list = parse_article_url_list(response)
    return article_url_list



def get_user_article_mission_list(weixin_id, update_cookie=False):
    link_list_url =  get_link_list_url(weixin_id, update_cookie)
    if link_list_url is None:
        logger.warning('can not find link_list_url for weixin_id : %s' % weixin_id)
        raise  CanNotFindWeixinInSogouException(message='can not find weixin in sogou for wx id : %s ' % weixin_id)
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
    return session.query(Profile).get(userid).user




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
def crawl_weixin_single_article_mission(mission, authorized_user_id=None, update_cookie=False):
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
    weixin_client.refresh_cookies(update_cookie)

    if authorized_user_id is None:
        logger.warning('need authorized user id to go on')
        raise Exception #need Exception handle
    user = get_user_by_authorized_user_id(authorized_user_id)

    mission['identity_code'] = caculate_identity_code(mission['title'], mission['created_datetime'],user.id )
    if  is_article_exist(mission, user):
            logger.info('article exist : %s', mission['title'])
            return

    response = None
    try :
        response = get_mission_page_content(mission)
    except (TooManyRequests, Expired) as e  :
        logger.warning('Too many request for single mission %s ' % mission['content_url'])
        crawl_weixin_single_article_mission.delay(mission,authorized_user_id,update_cookie=True)

    if (response is None) or (response.status_code != 200):
        # TODO : Exception raise and handle
        logger.warning('response of the mission status wrong' % getattr(mission, 'content_url'))

    else:
        article_dic = parse_article_page(response,authorized_user_id)
        article_dic.update(mission)
        #check again , for other
        if  is_article_exist(article_dic, user):
            logger.info('article exist : %s', article_dic['title'])
            return
        try :
            article = createArticle(article_dic)
            fetch_article_cover(article)
            fetch_article_image(article)
            fetch_user_qrcode_img_for_user(authorized_user_id)
        #     TODO : qrcode
        except Exception as e :
            logger.warning('create Article fail ')

def fetch_user_qrcode_img_for_user(authorized_user_id):
    #TODO implement
    # old code here

    # if not authorized_user.weixin_qrcode_img:
    #     get_qr_code(authorized_user.id, parse_qr_code_url(article_soup))

    pass

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
                # logger.info('fetch_image for article %d: %s', article.id,img_src)
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



def is_article_exist(article_dic, user):
    #TODO : implement

    try:
        existed_article = session.query(CoreArticle).filter_by(
            identity_code=article_dic['identity_code'],
        ).all()
    except BaseException as e:
        logger.error(e.message)
        return False

    if existed_article:
        logger.info('article existed : %s' % article_dic['title'])
        return True

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

# important this method must be same with
#       nut:Article model's calulate_identity_code  !!!
def caculate_identity_code(title, created_datetime,user_id):
    title_hash =  hashlib.sha1(title.encode('utf-8')).hexdigest()
    return '%s_%s_%s ' % (user_id,title_hash,created_datetime)



def get_identity_code(article_dic, authorized_user_id):
    user_id = get_user_by_authorized_user_id(authorized_user_id).id
    title = article_dic['title']
    created_datetime = article_dic['created_datetime']
    return caculate_identity_code(title,created_datetime, user_id)

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
    article_dic['creator'] = get_user_by_authorized_user_id(user_id)
    article_dic['updated_datetime'] = datetime.now()
    article_dic['publish'] = CoreArticle.published
    article_dic['identity_code'] = get_identity_code(article_dic, user_id)
    return article_dic


def get_mission_page_content(mission):
    cookie  = get_request_cookie()
    url = convert_article_url(mission['content_url'])
    # #debug
    # raise TooManyRequests()
    response = weixin_client.get( url, headers={'Cookie': cookie})
    return response

def convert_article_url(uri):
    url = 'http://mp.weixin.qq.com%s' % uri
    return url

@app.task(base=RequestsTask, name='weixin.crawl_list')
def crawl_user_weixin_articles_by_authorized_user_id(authorized_user_id, update_cookie=False):
    logger.info('weixin articles  for authorized author id : %s' % authorized_user_id)
    weixin_id = get_weixin_id_by_authorized_user_id(authorized_user_id)
    try:
        user_article_mission_list = get_user_article_mission_list(weixin_id, update_cookie=update_cookie)

        for article_mission in user_article_mission_list:
            print article_mission
            crawl_weixin_single_article_mission.delay(article_mission, authorized_user_id, update_cookie=False)
        return

    except CanNotFindWeixinInSogouException as e :
        logger.error('Fatal mission fail : %s ' %e.message )
        #todo : mail to admin
    except TooManyRequests as e :
        update_cookie = True
        logger.warning("too many requests or request expired. %s", e.message)
        crawl_user_weixin_articles_by_authorized_user_id.delay(authorized_user_id, update_cookie=update_cookie)
        #TODO : use retry instead of delay .



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
