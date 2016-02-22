#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import redis
import requests

from celery.task import task
from urllib.parse import urljoin

from guoku_crawler import config
from guoku_crawler.celery import RequestsTask


r = redis.Redis(host=config.CONFIG_REDIS_HOST,
                port=config.CONFIG_REDIS_PORT,
                db=config.CONFIG_REDIS_DB)


@task(base=RequestsTask, name="sogou.update_user_cookie")
def update_user_cookie(sg_user):
    if not sg_user:
        return
    get_url = urljoin(config.PHANTOM_SERVER, '_sg_cookie')
    resp = requests.post(get_url, data={'email': sg_user})
    cookie = resp.json()['sg_cookie']
    print('-'*80)
    print(cookie)
    print('-'*80)
    key = 'sogou.cookie.%s' % sg_user
    r.set(key, cookie)


@task(base=RequestsTask, name="sogou.prepare_cookies")
def prepare_cookies():
    check_url = urljoin(config.PHANTOM_SERVER, '_health')
    resp = requests.get(check_url)
    ready = resp.status_code == 200
    if ready:
        emails = config.SOGOU_USERS
        for sg_email in emails:
            update_user_cookie.delay(sg_user=sg_email)
    else:
        logging.error("phantom web server is unavailable!")


if __name__ == '__main__':
    prepare_cookies.delay()
    print('hahahah')
