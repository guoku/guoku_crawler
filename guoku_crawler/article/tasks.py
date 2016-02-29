#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

import requests

from urllib.parse import urljoin

from guoku_crawler import config, r
from guoku_crawler.celery import RequestsTask, app


def update_user_cookie(sg_user):
    if not sg_user:
        return
    get_url = urljoin(config.PHANTOM_SERVER, '_sg_cookie')
    resp = requests.post(get_url, data={'email': sg_user})
    cookie = resp.json()['sg_cookie']
    print('-'*80, '\r\n')
    print('got cookie for %s: ', sg_user)
    print(cookie)
    print('-'*80, '\r\n')
    key = 'sogou.cookie.%s' % sg_user
    r.set(key, cookie)


def prepare_cookies():
    check_url = urljoin(config.PHANTOM_SERVER, '_health')
    resp = requests.get(check_url)
    ready = resp.status_code == 200
    if ready:
        emails = config.SOGOU_USERS
        for sg_email in emails:
            update_user_cookie(sg_user=sg_email)
    else:
        logging.error("phantom web server is unavailable!")


if __name__ == '__main__':
    prepare_cookies()
