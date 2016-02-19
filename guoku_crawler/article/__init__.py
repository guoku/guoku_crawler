#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
from time import sleep

import requests

from faker import Faker
from celery import Task
from requests.exceptions import ReadTimeout
from requests.exceptions import ConnectionError


faker = Faker()
search_api = 'http://weixin.sogou.com/weixinjs'
login_url = 'https://account.sogou.com/web/login'
log = getLogger('django')


class Retry(Exception):
    def __init__(self, countdown=5, message=u''):
        self.countdown = countdown
        self.message = 'Fetch error, need to login or get new token.' + message


class Expired(Exception):
    def __init__(self, message=u''):
        self.message = message


class ToManyRequests(Exception):
    def __init__(self, message=u''):
        self.message = message


class RequestsTask(Task):
    abstract = True
    compression = 'gzip'
    default_retry_delay = 5
    send_error_emails = True
    max_retries = 3

    def __call__(self, *args, **kwargs):
        try:
            return super(RequestsTask, self).__call__(*args, **kwargs)
        except (requests.Timeout, requests.ConnectionError) as e:
            raise self.retry(exc=e)


class WeiXinClient(requests.Session):
    def __init__(self):
        super(WeiXinClient, self).__init__()
        self.login_url = 'https://account.sogou.com/web/login'
        self.search_api_url = 'http://weixin.sogou.com/weixinjs'
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
                json=None,
                jsonp_callback=None):
        try:
            resp = super(WeiXinClient, self).request(method, url, params, data,
                                                     headers, cookies, files, auth,
                                                     timeout, allow_redirects,
                                                     proxies, hooks, stream, verify,
                                                     cert, json)
        except ConnectionError as e:
            raise Retry(message=u'ConnectionError. %s' % e.message)
        except ReadTimeout as e:
            raise Retry(message=u'ReadTimeout. %s' % e.message)
        if stream:
            return resp

        cookie_user = sogou_cookies.get(self.headers['Cookie'])
        resp.utf8_content = resp.content.decode('utf-8')
        resp.utf8_content = resp.utf8_content.rstrip('\n')
        if resp.utf8_content.find(u'您的访问过于频繁') >= 0:
            log.warning(u'访问的过于频繁. 用户: %s, url: %s', cookie_user, url)
            raise ToManyRequests(message=u'too many requests.')
        if resp.utf8_content.find(u'当前请求已过期') >= 0:
            log.warning(u'当前请求已过期. url: %s', url)
            raise Expired('link expired: %s' % url)
        if jsonp_callback:
            resp.jsonp = self.parse_jsonp(resp.utf8_content, jsonp_callback)
            if resp.jsonp.get('code') == 'needlogin':
                self.refresh_cookies()
                raise Retry(message=u'need login.')
        sleep(60)
        return resp

    def login(self):
        username = random.choice(settings.SOGOU_USERS)
        password = settings.SOGOU_PASSWORD
        headers = {
            'Referer': 'http://news.sogou.com/?p=40030300&kw=',
            'Origin': 'http://news.sogou.com',
            'Host': 'account.sogou.com',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'RA-Sid': '77094B42-20140626-080311-ac7a24-cf2748',
            'RA-Ver': '3.0.7',
            'Upgrade-Insecure-Requests': 1,
            'UserAgent': faker.user_agent(),
        }
        data = dict(username=username,
                    password=password,
                    autoLogin=1,
                    client_id='2006',
                    xd='http://news.sogou.com/jump.htm',
                    )
        self.request('POST',
                     self.login_url, data=data, headers=headers)

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
                log.error("Json decode error %s", utf8_content)
                raise


#############  Cookies  #############
sogou_cookies = {'IPLOC=CN1100; SUV=00952CF17C7F4BB756C28AD8AC45E050; SUID=B74B7F7C543A900A0000000056C28AD8; CXID=5E6A70781A0DC6BF80598F1FE7FBA228; ppinf=5|1455590122|1456799722|Y2xpZW50aWQ6NDoyMDA2fGNydDoxMDoxNDU1NTkwMTIyfHJlZm5pY2s6MDp8dHJ1c3Q6MToxfHVzZXJpZDoyMzpzaG9lbWFoNTVAc3VwZXJyaXRvLmNvbXx1bmlxbmFtZTowOnw; pprdig=ESNu7c-bdrmSAMER4UcHZ-s7kT-5Y-Ca698dnsv1auno00G1s3WMcdKcQPUFzOYt9pfxm8oGv0x5616IPlReO-RwzA6kJxoic3A9eWV8B5ERVazJlZFpk8A6VCL1WKMrmaEvyGT21EjzfxbbxcnFCwahzHPiVU2TYmTIRYSJaCQ; ad=0YENYlllll2QZorYlllllVbjAm1lllllK4daHZlllxwlllll94Dll5@@@@@@@@@@; ABTEST=0|1455590133|v1; SNUID=E61A2E2D51547A8BAD85F95E523601B8; ppmdig=1455590133000000269a9b3432737f4ef0658be46bdc6109'
                 : 'shoemah55@superrito.com',

                 'ABTEST=0|1455467345|v1; SNUID=2AF52779787D52C51F6D3AF479BB4232; IPLOC=CN1100; SUID=528C5F01E518920A0000000056C0AB51; SUID=528C5F015FC00D0A0000000056C0AB51; SUV=1455467346777522; CXID=1C4DB0247E61BE4B99EF357907DF0373; ppinf=5|1455467390|1456676990|Y2xpZW50aWQ6NDoyMDA2fGNydDoxMDoxNDU1NDY3MzkwfHJlZm5pY2s6MDp8dHJ1c3Q6MToxfHVzZXJpZDoyMzpkdWFkMTkzN0Bqb3VycmFwaWRlLmNvbXx1bmlxbmFtZTowOnw; pprdig=A1WnwjctQ9O73thzbyR9XQ8acB0e9amPBDh048LvZv1-XwuVVfEmjO3P6QsdarONGNGzi96LUCijT6WnYUTjlCxhSNuX3GdpF1sAdf_jKXZC1Zy8fOgv-5TEIAvZeDPPXzqAsatV-uAyVx_s1azCkUaSz6OR_69PVaSopMVw2q0; ad=3afdDkllll2QZ3HqlllllVbl$cwllllllqMGUklllxGlllllRXDll5@@@@@@@@@@; ppmdig=1455467399000000aaed2e767ad590332462fdcd9a7299a3'
                 : 'duad1937@jourrapide.com',

                 'ABTEST=0|1455467345|v1; SUID=528C5F01E518920A0000000056C0AB51; SUV=00942CF03BBCFCA456C16869FDFAD356; SUID=A4FCBC3B543A900A0000000056C16869; CXID=64F75D7609434253F8BB56382BC92D7D; ppinf=5|1455515823|1456725423|Y2xpZW50aWQ6NDoyMDA2fGNydDoxMDoxNDU1NTE1ODIzfHJlZm5pY2s6MDp8dHJ1c3Q6MToxfHVzZXJpZDoyNjpvYnNvbWVkMTk3N0Bqb3VycmFwaWRlLmNvbXx1bmlxbmFtZTowOnw; pprdig=WyJT08C7ZYeWGQ1MZrZg8bjdhOnOv5PXSC41ntesRNRz3eLs5UAr8jrXSCD8QqRu0Vg4awRr58VilI0ty17aOUz7lB9rh3cj1jnyv1YmAbftNuKd_xw0LRgp_05L0OWF-8Tlmw9CZgv1JB_4P7aNBiU76BCFB5MFbfTKR1_Vsic; ad=$rfdvkllll2QZQP7lllllVbxzaUlllllnE8DIlllllZlllllRTDll5@@@@@@@@@@; weixinIndexVisited=1; SNUID=237B34BC8882A34F367D6FF6885B2AEF; ppmdig=14555897510000008048b6bb7e0414f2cb91c581dd7c224c; IPLOC=CN1100; sct=6; LSTMV=1017%2C255; LCLKINT=30112'
                 : 'obsomed1977@jourrapide.com',

                 'SUV=00DF64037C7F4BB756C28B1FCE2DF205; IPLOC=CN1100; SUID=B74B7F7C543A900A0000000056C28B1F; CXID=1D8132CF46F1FF3ED5BBB39DAD4D63C4; ABTEST=0|1455590177|v1; SNUID=38C5F1F28E8AA55670F5583C8FCA85E7; ppinf=5|1455590185|1456799785|Y2xpZW50aWQ6NDoyMDA2fGNydDoxMDoxNDU1NTkwMTg1fHJlZm5pY2s6MDp8dHJ1c3Q6MToxfHVzZXJpZDoyMzpkdWFkMTkzN0Bqb3VycmFwaWRlLmNvbXx1bmlxbmFtZTowOnw; pprdig=Vfh7mP-24IWzcjGbHpuwsH5D254w4cUtFcgFiNQJf6LlIxf9xUXpBeunNMGqsd0fAqBSQzkLxxINidav911o8sDtE6ani61-e4D7F1dJnvNkzogOEa_KWZefwdamXTCzNBoUqGYkX_4dJvor7C_K9e6ffwewKEE-r0ys-pLxDXY; ad=xcEN3lllll2QZo7klllllVbjAh7lllllK4daHZlllxwlllll94Dll5@@@@@@@@@@; ppmdig=145559019100000067801a980ef600f55b19f2d36d78bcde'
                 : 'duad1937@jourrapide.com'
                 }


sogou_referers = ('http://weixin.sogou.com/',
                  'http://mp.weixin.qq.com/s?__biz=MTI0MDU3NDYwMQ==&mid=406976557&idx=3&sn=e2749cff6e7fbf1379f4d7ee5829a5aa&3rd=MzA3MDU4NTYzMw==&scene=6#rd',
                  'http://weixin.sogou.com/weixin?type=1&query=a&ie=utf8'
                  )

# @task(base=RequestsTask, name="sogou.update_user_cookie")
# def update_user_cookie(sg_user):
#     if not sg_user:
#         return
#     get_url = urljoin(settings.PHANTOM_SERVER, '_sg_cookie')
#     resp = requests.post(get_url, data={'email': sg_user})
#     cookie = resp.json()['sg_cookie']
#     key = 'sogou.cookie.%s' % sg_user
#     r.set(key, cookie)


