#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
From django.
"""

from io import BytesIO, StringIO

from guoku_crawler.storage.file import File


class ContentFile(File):
    """
    A File-like object that takes just raw content, rather than an actual file.
    """

    def __init__(self, content, name=None):
        stream_class = StringIO if isinstance(content,
                                              str) else BytesIO
        super(ContentFile, self).__init__(stream_class(content), name=name)
        self.size = len(content)

    def __str__(self):
        return 'Raw content'

    def __bool__(self):
        return True

    def __nonzero__(self):  # Python 2 compatibility
        return type(self).__bool__(self)

    def open(self, mode=None):
        self.seek(0)

    def close(self):
        pass
