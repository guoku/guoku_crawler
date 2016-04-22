#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import requests

from time import sleep
from faker import Faker
from urlparse import urljoin

from guoku_crawler.config import logger
from requests.exceptions import ReadTimeout
from requests.exceptions import ConnectionError

from guoku_crawler.db import r
from guoku_crawler import config
from guoku_crawler.celery import RequestsTask, app
from guoku_crawler.exceptions import TooManyRequests, Expired, Retry


faker = Faker()


class BaseClient(requests.Session):
    def request(self, method, url,
                params=None,
                data=None,
                headers=None,
                cookies=None,
                files=None,
                auth=None,
                timeout=None,
                allow_redirects=True,
                proxies=None,
                hooks=None,
                stream=None,
                verify=None,
                cert=None,
                json=None):
        resp = None
        try:
            resp = super(BaseClient, self).request(method, url, params, data,
                                                   headers, cookies, files,
                                                   auth, timeout,
                                                   allow_redirects, proxies,
                                                   hooks, stream, verify,
                                                   cert, json)

        except ConnectionError as e:
            raise Retry(message=u'ConnectionError. %s' % e)
        except ReadTimeout as e:
            raise Retry(message=u'ReadTimeout. %s' % e)
        except BaseException as e:
            logger.error(e)
        if stream:
            return resp
        resp.utf8_content = resp.content.decode('utf-8')
        resp.utf8_content = resp.utf8_content.rstrip('\n')
        sleep(config.REQUEST_INTERVAL)
        return resp


class RSSClient(BaseClient):
    pass


class WeiXinClient(BaseClient):
    def __init__(self):
        super(WeiXinClient, self).__init__()
        self._sg_user = None

    @property
    def sg_user(self):
        return self._sg_user

    def request(self, method, url,
                params=None,
                data=None,
                headers=None,
                cookies=None,
                files=None,
                auth=None,
                timeout=None,
                allow_redirects=True,
                proxies=None,
                hooks=None,
                stream=None,
                verify=None,
                cert=None,
                json=None,
                jsonp_callback=None):

        resp = super(WeiXinClient, self).request(method, url, params, data,
                                                 headers, cookies, files,
                                                 auth, timeout,
                                                 allow_redirects, proxies,
                                                 hooks, stream, verify,
                                                 cert, json)
        logger.info('WeiXinClient().request: request url: %s, user: %s' % (url, self.sg_user))
        logger.info(resp.request.headers)
        if stream:
            return resp

        # catch exceptions
        if resp.utf8_content.find(u'您的访问过于频繁') >= 0:
            message = u'您的访问过于频繁,需要输入验证码. user: %s, url: %s' % (
                self.sg_user, url)
            # logger.warning(message)
            logger.warning(u'访问过于频繁, cookie: %s' % resp.request.headers)
            raise TooManyRequests(message)
        if resp.utf8_content.find(u'当前请求已过期') >= 0:
            message = u'当前请求已过期: %s' % url
            # logger.warning(message)
            raise Expired(message)

        if jsonp_callback:
            resp.jsonp = self.parse_jsonp(resp.utf8_content, jsonp_callback)
            if resp.status_code > 400:
                # raise Exception('404')
                return resp
            if resp.jsonp.get('code') == 'needlogin':
                self.refresh_cookies()
                raise Retry(message=u'need login with %s.' % self.sg_user)
        sleep(config.REQUEST_INTERVAL)
        return resp

    def refresh_cookies(self, update=False):
        self.cookies.clear()
        if update:
            update_sogou_cookie.delay(self.sg_user)
            logger.info('WeiXinClient().refresh_cookies: call update_sogou_cookie.delay for user: %s' % self.sg_user)

        sg_users = list(config.SOGOU_USERS)
        if self.sg_user:
            sg_users.remove(self.sg_user)

        sg_user = random.choice(sg_users)
        sg_cookie = r.get('sogou.cookie.%s' % sg_user)
        if not sg_cookie:
            update_sogou_cookie.delay(sg_user)
            logger.info('WeiXinClient().refresh_cookies while loop: call update_sogou_cookie.delay for user: %s' % sg_user)
            # sg_user = random.choice(sg_users)
            try:
                for sg_user in sg_users:
                    try:
                        sg_cookie = r.get('sogou.cookie.%s' % sg_user).decode()
                        logger.info('WeiXinClient().refresh_cookies while loop: got cookie from redis, user: %s' % sg_user)
                        break
                    except:
                        pass
            except:
                sg_user = random.choice(sg_users)
                update_sogou_cookie(sg_user)


            # except Exception as e:
            #     logger.error('WeiXinClient().refresh_cookies while loop: %s' % e)
            #     sleep(10)
            #     pass

        self._sg_user = sg_user
        self.headers['Cookie'] = sg_cookie
        self.headers['User-Agent'] = faker.user_agent()
        # logger.info("have updated cookies for %s" % self.sg_user)
        logger.info("weixin_client.Cookie: %s" % self.headers['Cookie'])

    @classmethod
    def parse_jsonp(cls, utf8_content, callback):
        if utf8_content.startswith(callback):
            try:
                # utf8 content is a jsonp
                # here we extract the json part
                # for example, "cb({"a": 1})", where callback is "cb"
                return json.loads(utf8_content[len(callback) + 1:-1])
            except ValueError:
                logger.error("Json decode error %s", utf8_content)
                raise


@app.task(base=RequestsTask, name='weixin.update_sogou_cookie')
def update_sogou_cookie(sg_user):
    if not sg_user:
        return
    get_url = urljoin(config.PHANTOM_SERVER, '_sg_cookie')
    resp = requests.post(get_url, data={'email': sg_user})
    cookie = resp.json()['sg_cookie']
    key = 'sogou.cookie.%s' % sg_user
    r.set(key, cookie)
    logger.info('update_sogou_cookie: update cookie SUCCESS for %s: , cookie: %s, have saved to redis.' % (sg_user, cookie))


def get_user_profile_link(weixin_id):
    get_url = urljoin(config.PHANTOM_SERVER, 'userlink')
    params = dict(type='1', ie='utf8', query=weixin_id)
    resp = requests.post(get_url, params=params)
    return resp
