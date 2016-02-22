#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import requests
import logging

from time import sleep
from faker import Faker
from requests.exceptions import ReadTimeout
from requests.exceptions import ConnectionError

from guoku_crawler.exceptions import ToManyRequests, Expired, Retry


faker = Faker()


class WeiXinClient(requests.Session):
    def __init__(self):
        super(WeiXinClient, self).__init__()
        self.refresh_cookies()

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
        if stream:
            return resp

        cookie_user = sogou_cookies.get(self.headers['Cookie'])
        resp.utf8_content = resp.content.decode('utf-8')
        resp.utf8_content = resp.utf8_content.rstrip('\n')
        if resp.utf8_content.find(u'您的访问过于频繁') >= 0:
            logging.warning(u'访问的过于频繁. 用户: %s, url: %s', cookie_user, url)
            raise ToManyRequests(message=u'too many requests.')
        if resp.utf8_content.find(u'当前请求已过期') >= 0:
            logging.warning(u'当前请求已过期. url: %s', url)
            raise Expired('link expired: %s' % url)
        if jsonp_callback:
            resp.jsonp = self.parse_jsonp(resp.utf8_content, jsonp_callback)
            if resp.jsonp.get('code') == 'needlogin':
                self.refresh_cookies()
                raise Retry(message=u'need login.')
        sleep(60)
        return resp

    def refresh_cookies(self):
        self.cookies.clear()
        self.headers['Cookie'] = random.choice(sogou_cookies.keys())
        self.headers['User-Agent'] = faker.user_agent()
        return self.headers['Cookie']

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
