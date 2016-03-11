#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from wand.image import Image as WandImage
from hashlib import md5

from guoku_crawler import config
from guoku_crawler.common.file import ContentFile
from guoku_crawler.common.storage.storage import FileSystemStorage, MogileFSStorage

image_path = getattr(config, 'MOGILEFS_MEDIA_URL', 'images/')


def get_storage_class():
    if config.LOCAL_FILE_STORAGE:
        return FileSystemStorage()
    return MogileFSStorage()
default_storage = get_storage_class()


class HandleImage(object):
    path = image_path

    def __init__(self, file):
        self.content_type = self.get_content_type(file)
        self._name = None
        if hasattr(file, 'chunks'):
            self._image_data = ''.join(chuck for chuck in file.chunks())
        else:
            self._image_data = file.read()
        self.ext_name = self.get_ext_name()
        file.close()
        logging.info('init HandleImage obj.')
        try:
            self.img = WandImage(blob=self._image_data)
        except BaseException as e:
            logging.error(e)
            self.img = WandImage(file=file)

    @property
    def image_data(self):
        return self._image_data

    @property
    def name(self):
        self._name = md5(self.image_data).hexdigest()
        return self._name

    @staticmethod
    def get_content_type(file):
        try:
            content_type = file.content_type
        except AttributeError:
            content_type = None
        if content_type is None:
            return None

        if content_type == 'image/png':
            content_type = 'image/jpeg'
        return content_type

    def get_ext_name(self):
        ext = 'jpg'
        try:
            ext = self.content_type.split('/')[1]
        except Exception as e:
            logging.error(e)
            pass

        return ext

    def crop_square(self):
        _img = WandImage(blob=self._image_data)
        _delta = _img.width - _img.height
        if _delta > 0:
            _img.crop(_delta / 2, 0, width=_img.height, height=_img.height)
        elif _delta < 0:
            _img.crop(0, -_delta / 2, width=_img.width, height=_img.width)

        self._image_data = _img.make_blob()

    def save(self, path='', square=False):
        if self.ext_name == 'png':
            self._image_data = self.img.make_blob(format='jpeg')
            self.ext_name = 'jpg'

        if square and (self.ext_name == 'jpg'):
            self.crop_square()

        if path:
            self.path = path

        file_name = self.path + self.name + '.' + self.ext_name
        if not default_storage.exists(file_name=file_name):
            # try:
            file_name = default_storage.save(file_name,
                                             ContentFile(self.image_data))
            # except Exception as e:
            #     logging.info(e)
        else:
            pass

        return file_name
