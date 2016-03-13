#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from celery import Celery
from celery import Task
from guoku_crawler import config

import requests

app = Celery('guoku_crawler')
app.config_from_object(config)


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

if __name__ == '__main__':
    app.start()
