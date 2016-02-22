#!/usr/bin/env python
# -*- coding: utf-8 -*-
from guoku_crawler.common.storage.encoding import Promise, force_text


def smart_text(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Returns a text object representing 's' -- unicode on Python 2 and str on
    Python 3. Treats bytestrings using the 'encoding' codec.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if isinstance(s, Promise):
        # The input is the result of a gettext_lazy() call.
        return s
    return force_text(s, encoding, strings_only, errors)


def queryset_iterator(queryset, chunk_size=100):
    """
    Iterate over a Django Queryset ordered by the primary key
    This method loads a maximum of chunk size (default: 100) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not pre_load all the
    classes.
    Note that the implementation of the iterator does not support ordered query
    sets.
    :param chunk_size: maximum of chunk
    :param queryset: query that want to query
    """
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunk_size]:
            pk = row.pk
            yield row
        gc.collect()
