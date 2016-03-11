#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ImproperlyConfigured(Exception):
    """Django is somehow improperly configured"""
    pass


class SuspiciousOperation(Exception):
    """The user did something suspicious"""


class SuspiciousFileOperation(SuspiciousOperation):
    """A Suspicious filesystem operation was attempted"""
    pass

class RemovedInDjango110Warning(DeprecationWarning):
    pass
