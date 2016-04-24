#!/usr/bin/env python
# -*- coding: utf-8 -*-

class CrawlerBaseException(Exception):
    def __init__(self, message=u''):
        self.message = message


class Retry(Exception):
    def __init__(self, countdown=5, message=u''):
        self.countdown = countdown
        self.message = 'Fetch error, need to login or get new token.' + message


class Expired(Exception):
    def __init__(self, message=u''):
        self.message = message


class TooManyRequests(Exception):
    def __init__(self, message=u''):
        self.message = message


class CanNotFindWeixinInSogouException(CrawlerBaseException):
    pass


