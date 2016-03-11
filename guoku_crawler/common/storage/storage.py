#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import errno
import warnings

import itertools
import pymogile

from datetime import datetime
from os.path import abspath
from urlparse import urljoin

from guoku_crawler import config
from guoku_crawler.common.storage import locks
from guoku_crawler.common.storage.file import File
from guoku_crawler.common.storage._os import safe_join
from guoku_crawler.common.storage.move import file_move_safe
from guoku_crawler.common.storage.encoding import filepath_to_uri, force_unicode
from guoku_crawler.common.storage.exceptions import (SuspiciousFileOperation,
                                                     RemovedInDjango110Warning,
                                                     ImproperlyConfigured)
from guoku_crawler.common.storage.encoding import get_valid_filename, force_unicode, \
    force_unicode


class Storage(object):
    """
    A base storage class, providing some default behaviors that all other
    storage systems can inherit or override, as necessary.
    """

    # The following methods represent a public interface to private methods.
    # These shouldn't be overridden by subclasses unless absolutely necessary.

    def open(self, name, mode='rb'):
        """
        Retrieves the specified file from storage.
        """
        return self._open(name, mode)

    def save(self, name, content):
        """
        Saves new content to the file specified by name. The content should be
        a proper File object or any python file-like object, ready to be read
        from the beginning.
        """
        # Get the proper name for the file, as it will actually be saved.
        if name is None:
            name = content.name

        if not hasattr(content, 'chunks'):
            content = File(content)

        name = self.get_available_name(name)
        name = self._save(name, content)

        # Store filenames with forward slashes, even on Windows
        return force_unicode(name.replace('\\', '/'))

    # These methods are part of the public API, with default implementations.

    def get_valid_name(self, name):
        """
        Returns a filename, based on the provided filename, that's suitable for
        use in the target storage system.
        """
        return get_valid_filename(name)

    def get_available_name(self, name):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        # If the filename already exists, add an underscore and a number (before
        # the file extension, if one exists) to the filename until the generated
        # filename doesn't exist.
        count = itertools.count(1)
        while self.exists(name):
            # file_ext includes the dot.
            name = os.path.join(dir_name, "%s_%s%s" % (file_root, next(count), file_ext))

        return name

    def path(self, name):
        """
        Returns a local filesystem path where the file can be retrieved using
        Python's built-in open() function. Storage systems that can't be
        accessed using open() should *not* implement this method.
        """
        raise NotImplementedError("This backend doesn't support absolute paths.")

    # The following methods form the public API for storage systems, but with
    # no default implementations. Subclasses must implement *all* of these.

    def delete(self, name):
        """
        Deletes the specified file from the storage system.
        """
        raise NotImplementedError()

    def exists(self, name):
        """
        Returns True if a file referened by the given name already exists in the
        storage system, or False if the name is available for a new file.
        """
        raise NotImplementedError()

    def listdir(self, path):
        """
        Lists the contents of the specified path, returning a 2-tuple of lists;
        the first item being directories, the second item being files.
        """
        raise NotImplementedError()

    def size(self, name):
        """
        Returns the total size, in bytes, of the file specified by name.
        """
        raise NotImplementedError()

    def url(self, name):
        """
        Returns an absolute URL where the file's contents can be accessed
        directly by a Web browser.
        """
        raise NotImplementedError()

    def accessed_time(self, name):
        """
        Returns the last accessed time (as datetime object) of the file
        specified by name.
        """
        raise NotImplementedError()

    def created_time(self, name):
        """
        Returns the creation time (as datetime object) of the file
        specified by name.
        """
        raise NotImplementedError()

    def modified_time(self, name):
        """
        Returns the last modified time (as datetime object) of the file
        specified by name.
        """
        raise NotImplementedError()


class FileSystemStorage(Storage):
    """
    Standard filesystem storage
    """

    def __init__(self, location=None, base_url=None, file_permissions_mode=None,
                 directory_permissions_mode=None):
        if location is None:
            location = config.MEDIA_ROOT
        self.base_location = location
        self.location = abspath(self.base_location)
        if base_url is None:
            base_url = config.MEDIA_URL
        elif not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url
        self.file_permissions_mode = (
            file_permissions_mode if file_permissions_mode is not None
            else config.FILE_UPLOAD_PERMISSIONS
        )
        self.directory_permissions_mode = (
            directory_permissions_mode if directory_permissions_mode is not None
            else config.FILE_UPLOAD_DIRECTORY_PERMISSIONS
        )

    def _open(self, name, mode='rb'):
        return File(open(self.path(name), mode))

    def save(self, name, content):
        full_path = self.path(name)

        # Create any intermediate directories that do not exist.
        # Note that there is a race between os.path.exists and os.makedirs:
        # if os.makedirs fails with EEXIST, the directory was created
        # concurrently, and we can continue normally. Refs #16082.
        directory = os.path.dirname(full_path)
        if not os.path.exists(directory):
            try:
                if self.directory_permissions_mode is not None:
                    # os.makedirs applies the global umask, so we reset it,
                    # for consistency with file_permissions_mode behavior.
                    old_umask = os.umask(0)
                    try:
                        os.makedirs(directory, self.directory_permissions_mode)
                    finally:
                        os.umask(old_umask)
                else:
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

        if self.file_permissions_mode is not None:
            os.chmod(full_path, self.file_permissions_mode)

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

    def exists(self, file_name):
        return os.path.exists(self.path(file_name))

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
        return safe_join(self.location, name)

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
                raise ImproperlyConfigured, "You must define %s to use the MogileFS backend." % var

        self.trackers = config.MOGILEFS_TRACKERS
        self.domain = config.MOGILEFS_DOMAIN
        self.client = pymogile.Client(self.domain, self.trackers)

    def get_mogile_paths(self, file_name):
        return self.client.get_paths(file_name)

        # The following methods define the Backend API

    def filesize(self, file_name):
        raise NotImplemented
        #return os.path.getsize(self._get_absolute_path(file_name))

    def path(self, file_name):
        paths = self.get_mogile_paths(file_name)
        if paths:
            return self.get_mogile_paths(file_name)[0]
        else:
            return None

    def url(self, file_name):
        return urljoin(self.base_url, file_name).replace('\\', '/')

        # def open(self, file_name, mode='rb'):

        # raise NotImplemented
        #return open(self._get_absolute_path(file_name), mode)
    def _open(self, file_name, mode='rb'):
        f = self.client.read_file(file_name)
        # f.closed = False
        # print f
        return File(file=f, name=file_name)
        # return f

    def exists(self, file_name):
        return bool(self.client.get_paths(file_name))
        # return file_name in self.client

    def save(self, file_name, raw_contents):
        file_name = self.get_available_name(file_name)

        if not hasattr(self, 'mogile_class'):
            self.mogile_class = None

        # Write the file to mogile
        success = self.client.store_file(file_name, raw_contents, cls=self.mogile_class)
        if success:
            print "Wrote file to key %s, %s@%s" % (file_name, self.domain, self.trackers[0])
        else:
            print "FAILURE writing file %s" % (file_name)

        return force_unicode(file_name.replace('\\', '/'))

    def delete(self, file_name):
        print file_name
        return self.client.delete(file_name)

#
# def serve_mogilefs_file(request, key=None):
#     """
#     Called when a user requests an image.
#     Either reproxy the path to perlbal, or serve the image outright
#     """
#     # not the best way to do this, since we create a client each time
#     mimetype = mimetypes.guess_type(key)[0] or "application/x-octet-stream"
#     client = pymogile.Client(config.MOGILEFS_DOMAIN, config.MOGILEFS_TRACKERS)
#     if hasattr(config, "SERVE_WITH_PERLBAL") and config.SERVE_WITH_PERLBAL:
#         # we're reproxying with perlbal
#
#         # check the path cache
#
#         path = cache.get(key)
#
#         if not path:
#             path = client.get_paths(key)
#             cache.set(key, path, 60)
#
#         if path:
#             response = HttpResponse(content_type=mimetype)
#             response['X-REPROXY-URL'] = path[0]
#         else:
#             response = HttpResponseNotFound()
#
#     else:
#         # we don't have perlbal, let's just serve the image via django
#         file_data = client[key]
#         if file_data:
#             response = HttpResponse(file_data, mimetype=mimetype)
#         else:
#             response = HttpResponseNotFound()
#
#     return response
