#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import errno
from guoku_crawler import config
import pymogile
import datetime

from asyncio import locks
from os.path import abspath
from urllib.parse import urljoin

from guoku_crawler.common.storage import Storage, File
from guoku_crawler.common.storage._os import safe_join
from guoku_crawler.common.storage.move import file_move_safe
from guoku_crawler.common.storage.encoding import force_text, filepath_to_uri
from guoku_crawler.common.storage.exceptions import (ImproperlyConfigured,
                                                     SuspiciousFileOperation)


class FileSystemStorage(Storage):
    """
    Standard filesystem storage
    """

    def __init__(self, location=None, base_url=None):
        if location is None:
            location = config.MEDIA_ROOT
        self.base_location = location
        self.location = abspath(self.base_location)
        if base_url is None:
            base_url = config.MEDIA_URL
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        return File(open(self.path(name), mode))

    def _save(self, name, content):
        full_path = self.path(name)

        # Create any intermediate directories that do not exist.
        # Note that there is a race between os.path.exists and os.makedirs:
        # if os.makedirs fails with EEXIST, the directory was created
        # concurrently, and we can continue normally. Refs #16082.
        directory = os.path.dirname(full_path)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
        if not os.path.isdir(directory):
            raise IOError("%s exists and is not a directory." % directory)

        # There's a potential race condition between get_available_name and
        # saving the file; it's possible that two threads might return the
        # same name, at which point all sorts of fun happens. So we need to
        # try to create the file, but if it already exists we have to go back
        # to get_available_name() and try again.

        while True:
            try:
                # This file has a file path that we can move.
                if hasattr(content, 'temporary_file_path'):
                    file_move_safe(content.temporary_file_path(), full_path)
                    content.close()

                # This is a normal uploadedfile that we can stream.
                else:
                    # This fun binary flag incantation makes os.open throw an
                    # OSError if the file already exists before we open it.
                    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             getattr(os, 'O_BINARY', 0))
                    # The current umask value is masked out by os.open!
                    fd = os.open(full_path, flags, 0o666)
                    _file = None
                    try:
                        locks.lock(fd, locks.LOCK_EX)
                        for chunk in content.chunks():
                            if _file is None:
                                mode = 'wb' if isinstance(chunk,
                                                          bytes) else 'wt'
                                _file = os.fdopen(fd, mode)
                            _file.write(chunk)
                    finally:
                        locks.unlock(fd)
                        if _file is not None:
                            _file.close()
                        else:
                            os.close(fd)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    # Ooops, the file exists. We need a new file name.
                    name = self.get_available_name(name)
                    full_path = self.path(name)
                else:
                    raise
            else:
                # OK, the file save worked. Break out of the loop.
                break

        if config.FILE_UPLOAD_PERMISSIONS is not None:
            os.chmod(full_path, config.FILE_UPLOAD_PERMISSIONS)

        return name

    def delete(self, name):
        assert name, "The name argument is not allowed to be empty."
        name = self.path(name)
        # If the file exists, delete it from the filesystem.
        # Note that there is a race between os.path.exists and os.remove:
        # if os.remove fails with ENOENT, the file was removed
        # concurrently, and we can continue normally.
        if os.path.exists(name):
            try:
                os.remove(name)
            except OSError as e:
                if e.errno != errno.ENOENT:
                    raise

    def exists(self, name):
        return os.path.exists(self.path(name))

    def listdir(self, path):
        path = self.path(path)
        directories, files = [], []
        for entry in os.listdir(path):
            if os.path.isdir(os.path.join(path, entry)):
                directories.append(entry)
            else:
                files.append(entry)
        return directories, files

    def path(self, name):
        try:
            path = safe_join(self.location, name)
        except ValueError:
            raise SuspiciousFileOperation(
                "Attempted access to '%s' denied." % name)
        return os.path.normpath(path)

    def size(self, name):
        return os.path.getsize(self.path(name))

    def url(self, name):
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        return urljoin(self.base_url, filepath_to_uri(name))

    def accessed_time(self, name):
        return datetime.fromtimestamp(os.path.getatime(self.path(name)))

    def created_time(self, name):
        return datetime.fromtimestamp(os.path.getctime(self.path(name)))

    def modified_time(self, name):
        return datetime.fromtimestamp(os.path.getmtime(self.path(name)))


class MogileFSStorage(Storage):
    """MogileFS filesystem storage"""

    def __init__(self, base_url=config.MEDIA_URL):

        # the MOGILEFS_MEDIA_URL overrides MEDIA_URL
        if hasattr(config, 'MOGILEFS_MEDIA_URL'):
            self.base_url = config.MOGILEFS_MEDIA_URL
        else:
            self.base_url = base_url

        for var in ('MOGILEFS_TRACKERS', 'MOGILEFS_DOMAIN',):
            if not hasattr(config, var):
                raise ImproperlyConfigured(
                    "You must define %s to use the MogileFS backend." % var)

        self.trackers = config.MOGILEFS_TRACKERS
        self.domain = config.MOGILEFS_DOMAIN
        self.client = pymogile.Client(self.domain, self.trackers)

    def get_mogile_paths(self, filename):
        return self.client.get_paths(filename)

        # The following methods define the Backend API

    def filesize(self, filename):
        raise NotImplemented
        # return os.path.getsize(self._get_absolute_path(filename))

    def path(self, filename):
        paths = self.get_mogile_paths(filename)
        if paths:
            return self.get_mogile_paths(filename)[0]
        else:
            return None

    def url(self, filename):
        return urljoin(self.base_url, filename).replace('\\', '/')

        # def open(self, filename, mode='rb'):

        # raise NotImplemented
        # return open(self._get_absolute_path(filename), mode)

    def _open(self, filename, mode='rb'):
        f = self.client.read_file(filename)
        # f.closed = False
        # print f
        return File(file=f, name=filename)
        # return f

    def exists(self, filename):
        return bool(self.client.get_paths(filename))
        # return filename in self.client

    def save(self, filename, raw_contents):
        filename = self.get_available_name(filename)

        if not hasattr(self, 'mogile_class'):
            self.mogile_class = None

        # Write the file to mogile
        success = self.client.store_file(filename, raw_contents,
                                         cls=self.mogile_class)
        if success:
            print("Wrote file to key %s, %s@%s" % (
            filename, self.domain, self.trackers[0]))
        else:
            print("FAILURE writing file %s" % (filename))

        return force_text(filename.replace('\\', '/'))

    def delete(self, filename):
        print(filename)
        return self.client.delete(filename)
