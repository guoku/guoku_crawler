#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import logging
import requests

from time import sleep
from faker import Faker
from requests.exceptions import ReadTimeout
from requests.exceptions import ConnectionError

from guoku_crawler import config, r
from guoku_crawler.exceptions import ToManyRequests, Expired, Retry
from guoku_crawler.article.tasks import update_user_cookie


faker = Faker()


class WeiXinClient(requests.Session):
    def __init__(self):
        super(WeiXinClient, self).__init__()
        self._sg_user = None
        self.refresh_cookies()

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
                jsonp_callback=None):
        try:
            resp = super(WeiXinClient, self).request(method, url, params, data,
                                                     headers, cookies, files,
                                                     auth, timeout, proxies,
                                                     allow_redirects, hooks,
                                                     stream, verify, cert)
        except ConnectionError as e:
            raise Retry(message=u'ConnectionError. %s' % e)
        except ReadTimeout as e:
            raise Retry(message=u'ReadTimeout. %s' % e)
        except BaseException as e:
            print(e)
            logging.ERROR(e)
        if stream:
            return resp

        resp.utf8_content = resp.content.decode('utf-8')
        resp.utf8_content = resp.utf8_content.rstrip('\n')

        # catch exceptions
        if resp.utf8_content.find(u'您的访问过于频繁') >= 0:
            logging.warning(u'访问的过于频繁. 用户: %s, url: %s', self.sg_user, url)
            raise ToManyRequests(
                message=u'too many requests with %s.' % self.sg_user
            )
        if resp.utf8_content.find(u'当前请求已过期') >= 0:
            logging.warning(u'当前请求已过期. url: %s', url)
            raise Expired('link expired: %s' % url)

        if jsonp_callback:
            resp.jsonp = self.parse_jsonp(resp.utf8_content, jsonp_callback)
            if resp.jsonp.get('code') == 'needlogin':
                self.refresh_cookies()
                raise Retry(message=u'need login with %s.' % self.sg_user)
        sleep(config.REQUEST_INTERVAL)
        return resp

    def refresh_cookies(self, update=False):
        self.cookies.clear()
        if update:
            update_user_cookie(self.sg_user)

        sg_users = list(config.SOGOU_USERS)
        if self.sg_user:
            sg_users.remove(self.sg_user)
        sg_user = random.choice(sg_users)
        sg_cookie = r.get('sogou.cookie.%s' % sg_user)
        if not sg_cookie:
            update_user_cookie(sg_user)
            sg_cookie = r.get('sogou.cookie.%s' % sg_user)
        self._sg_user = sg_user
        self.headers['Cookie'] = sg_cookie
        self.headers['User-Agent'] = faker.user_agent()

    @classmethod
    def parse_jsonp(cls, utf8_content, callback):
        if utf8_content.startswith(callback):
            try:
                # utf8 content is a jsonp
                # here we extract the json part
                # for example, "cb({"a": 1})", where callback is "cb"
                return json.loads(utf8_content[len(callback) + 1:-1])
            except ValueError:
                logging.error("Json decode error %s", utf8_content)
                raise
