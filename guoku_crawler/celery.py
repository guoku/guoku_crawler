#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

from celery import Celery
from celery import Task

from guoku_crawler import config


BROKER_URL = 'redis://localhost:6379/0'
app = Celery('tasks', broker=config.BROKER_URL)


class RequestsTask(Task):
    def run(self, *args, **kwargs):
        pass

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


from guoku_crawler.article.tasks import prepare_cookies
from guoku_crawler.article.tasks import update_user_cookie


__all__ = [prepare_cookies, update_user_cookie, RequestsTask]
